"""Repository-wide implementation claims and bounded durable review ownership.

Actor IDs identify cooperating agent runs, not authenticated GitHub accounts.
Every reservation uses the shared file's SHA compare-and-swap. Failed/uncertain
external writes retain ownership until the same run resumes or is stopped.
"""
import copy
import hashlib
import json
import re
import uuid
from pathlib import Path
from . import delivery_policy as rules, identifiers, pr_checks, workflow
from .model import names, tasks_from_issues
from .sync import now


def actor(value, role):
    if not isinstance(value, str) or not re.fullmatch(role + r'-[A-Za-z0-9]{4,32}', value):
        raise ValueError('Use a neutral ' + role + '-<opaque ID> identity')
    return value


def credentials(args, role):
    identity = actor(getattr(args, 'actor', None), role)
    session = getattr(args, 'session', None)
    if not isinstance(session, str) or not re.fullmatch(r'[A-Za-z0-9_-]{4,100}', session):
        raise ValueError('Supply a stable opaque --session for this actual agent run')
    return identity, session


def register(section, identity, session, role):
    old = section['actors'].get(identity)
    if old and old != {'session': session, 'role': role}:
        raise ValueError('Actor identity already belongs to another run or role')
    if any(k != identity and v['session'] == session for k, v in section['actors'].items()):
        raise ValueError('One actual agent run cannot acquire a second actor identity')
    section['actors'][identity] = {'session': session, 'role': role}


def read(store, config):
    state, sha = store.read(optional=True)
    section = rules.execution_state(state, config)
    if section is None:
        raise ValueError('This project has not adopted execution_policy')
    return state, sha, section


def owned(row, args, role='Worker'):
    identity, session = credentials(args, role)
    if not row or (row.get('id'), row.get('actor'), row.get('session')) != (getattr(args, 'claim', None), identity, session):
        raise ValueError('Stale or foreign claim; inspect execution show and resume the owning run')
    return row


def audit(section, event, **fields):
    section['history'].append(dict(event=event, at=now(), **fields))


def put_review(section, lane):
    if section['policy']['schema_version'] == 3 and not lane.get('batch_id'):
        # A kept source lane can move to a fresh PR after author fixes.
        for key, old in list(section['source_reviews'].items()):
            if old['id'] == lane['id']:
                del section['source_reviews'][key]
        section['source_reviews'][str(lane['pr'])] = lane
    else:
        section['review'] = lane


def remove_review(section, lane):
    if section['policy']['schema_version'] == 3 and not lane.get('batch_id'):
        del section['source_reviews'][str(lane['pr'])]
    else:
        section['review'] = None


def independent_slot(section, identity, session):
    if any(lane['actor'] == identity or lane['session'] == session for lane in rules.review_lanes(section)):
        raise ValueError('Each concurrent review needs a distinct actual reviewer run')


def migrate(api, config, store, apply=False, preserve_review_queue=False, preserve_closed_review_handoffs=False,
            maintenance_args=None):
    if preserve_closed_review_handoffs and not preserve_review_queue:
        raise ValueError('--preserve-closed-review-handoffs requires --preserve-review-queue')
    value = rules.execution_policy(config)
    if not value:
        raise ValueError('Commit the explicit execution_policy adoption before migrating shared state')
    state, sha = store.read(optional=True)
    if state.get('maintenance') and apply:
        from .maintenance import owned
        owned(state, maintenance_args)
    old = state.get('execution')
    context = rules.context_module().policy(config) if 'task_context_policy' in config else None
    if old and state.get('task_context', {}).get('policy') != context:
        raise ValueError('Adopt task context separately under owned idle maintenance')
    if old and (old.get('delivery_policy', rules.fingerprint(config)) != rules.fingerprint(config)
                or old.get('policy', {}).get('schema_version') in (2, 3)
                and 'delivery_policy' not in old and not rules.policy(config)['staging']['enabled']):
        raise ValueError('Execution migration cannot change delivery policy; use the inspected delivery-policy migrate transition')
    if rules.state_schema(state) == 2 and old and old.get('policy') == value:
        rules.execution_state(state, config)
        return {'applied': False, 'already_adopted': True, 'policy': value}
    from .maintenance import busy
    if busy(state):
        raise ValueError('Finish existing execution, batch, review and stage work before adoption; drain pending operations too')
    candidate = state.get('delivery_workflow', {}).get('stage', {})
    previous_version = old.get('policy', {}).get('schema_version') if old else None
    pool_adoption = bool(previous_version == 2 and value['schema_version'] == 3
                         and all(old['policy'].get(k) == value[k] for k in ('implementation_limit', 'batch_limit')))
    preserve = bool(preserve_review_queue and rules.state_schema(state) == 2 and old
                    and (previous_version == 1 and value['schema_version'] == 2
                         and all(old['policy'].get(k) == value[k] for k in ('implementation_limit', 'review_limit'))
                         or pool_adoption))
    if preserve_review_queue and not preserve:
        raise ValueError('Queue preservation supports unchanged-capacity schema 1 -> 2 or schema 2 -> 3 with unchanged implementation/batch limits')
    approved = {int(n) for n, row in old.get('tasks', {}).items() if row.get('state') == 'approved'} if old else set()
    if (state.get('active') or state.get('run', {}) and state['run'].get('state') == 'running'
            or candidate and candidate.get('state') != 'promoted'
            or old and (old.get('claims') or rules.review_lanes(old) or old.get('review_queue') and not preserve or old.get('integration')
                        or old.get('intake', {}) and old['intake'].get('state') == 'running'
                        or approved and not (preserve and pool_adoption))):
        raise ValueError('Finish existing execution, batch, review and stage work before adoption')
    tasks = tasks_from_issues(api.issues(), config)
    queued = set(old.get('review_queue', [])) if preserve else set()
    closed_handoffs = []
    if preserve:
        active_reviews = {t['number'] for t in tasks if not t['archive'] and t['phase'] == 'review'}
        if active_reviews != queued or len(queued) != len(old['review_queue']):
            raise ValueError('Preserved queue must exactly match all current Review tasks')
        previous_config = dict(config, execution_policy=old['policy'])
        rules.execution_state(state, previous_config)
        active_approved = {t['number'] for t in tasks if not t['archive'] and t['phase'] == 'approved'}
        if active_approved != approved:
            raise ValueError('Preserved Approved tasks must exactly match durable task records')
        if pool_adoption:
            from . import batch_policy
            baseline = api.request(api.root + '/git/ref/heads/' + config['project']['base_branch'])['object']['sha']
            for n in approved:
                approval = old['approvals'].get(str(n))
                if not approval or approval.get('issue') != n:
                    raise ValueError('Preserved Approved task requires its durable source approval')
                batch_policy.source(api.request, previous_config, approval, baseline)
        for n in queued:
            record = old['tasks'].get(str(n), {})
            handoff = record.get('handoff', {})
            if record.get('state') != 'queued' or not handoff or record.get('pr') != handoff.get('pr'):
                raise ValueError('Only durable queued Worker handoffs can be preserved')
            pr = api.request(api.root + f'/pulls/{record["pr"]}')
            linked = pr_checks.check(api.request, previous_config, record['pr'])
            closed = bool(preserve_closed_review_handoffs and pr.get('state') == 'closed'
                          and pr.get('merged') is False and pr.get('draft') is False)
            if (pr.get('merged') or pr.get('draft') or pr.get('state') != 'open' and not closed
                    or rules.route(previous_config, pr, api.request) not in (('approval', 'process') if pool_adoption else ('stage',)) or linked['issues'] != [n]
                    or pr['head']['ref'] != handoff.get('branch')
                    or pr['head'].get('repo', {}).get('full_name', '').lower() != api.repository.lower()
                    or not record.get('implementers')):
                raise ValueError('Preserved handoff needs its original ready per-task source PR')
            if closed:
                implementer = {'actor': handoff.get('actor'), 'session': handoff.get('session')}
                if (pr['base'].get('repo', {}).get('full_name', '').lower() != api.repository.lower()
                        or handoff.get('issue') != n or record.get('worker') != implementer['actor']
                        or implementer not in record['implementers']
                        or old.get('actors', {}).get(implementer['actor']) != {'session': implementer['session'], 'role': 'Worker'}):
                    raise ValueError('Closed handoff needs its original repository and recorded Worker evidence')
                closed_handoffs.append({'issue': n, 'pr': record['pr']})
    if any(not t['archive'] and t['phase'] in ('in_progress', 'review', 'approved', 'stage')
           and not (preserve and (t['phase'] == 'review' and t['number'] in queued
                                or pool_adoption and t['phase'] == 'approved' and t['number'] in approved)) for t in tasks):
        raise ValueError('Resolve all In Progress, Review and Stage tasks before adoption')
    rules.set_state_schema(state, 2)
    section = state.setdefault('execution', {'claims': {}, 'tasks': {}, 'actors': {},
                                            'completed': {}, 'review_queue': [], 'review': None, 'history': []})
    section['policy'] = copy.deepcopy(value)
    section['delivery_policy'] = rules.fingerprint(config)
    if context and not old:
        ref = api.request(api.root + '/git/ref/heads/' + config['project']['base_branch'])['object']['sha']
        row = api.request(api.root + '/contents/tracker/config.json?ref=' + ref)
        if json.loads(rules.file_bytes(api.request, api.root, row)) != config:
            raise ValueError('Initial task context adoption requires official current-main config')
        state['task_context'] = {'policy': copy.deepcopy(context), 'base_schema_version': 2, 'readiness': {},
                                 'history': [{'event': 'initialized', 'main_sha': ref}]}
        if state.get('maintenance'):
            state['maintenance']['base_schema_version'] = 4
        else:
            state['schema_version'] = 4
    if value['schema_version'] in (2, 3):
        section.setdefault('approvals', {})
        section.setdefault('batches', {})
        section.setdefault('integration', None)
        section.setdefault('intake', None)
    if value['schema_version'] == 3:
        section['source_reviews'] = {}
    evidence = {'preserved_closed_review_handoffs': sorted(closed_handoffs, key=lambda row: row['issue'])} if preserve_closed_review_handoffs else {}
    if pool_adoption and preserve:
        evidence['preserved_approved'] = sorted(approved)
    audit(section, 'policy-adopted', policy=value, preserved_review_queue=sorted(queued), **evidence)
    rules.execution_state(state, config)
    if apply:
        store.write(state, sha)
    return {'applied': apply, 'policy': value, 'schema_version': state['schema_version'], 'preserved_review_queue': sorted(queued), **evidence,
            'instruction': 'All writers and the snapshot service must use the compatible engine before --apply.'}


def worker_fields(args):
    identity, session = credentials(args, 'Worker')
    coordinator = actor(getattr(args, 'coordinator', None), 'Coordinator')
    branch, directory = getattr(args, 'branch', None), getattr(args, 'worktree', None)
    if not rules.valid_branch(branch) or not isinstance(directory, str) or not Path(directory).is_absolute():
        raise ValueError('Supply the dedicated --branch and absolute --worktree for this task')
    return {'actor': identity, 'session': session, 'coordinator': coordinator, 'branch': branch,
            'worktree': str(Path(directory).resolve())}


def available(section, fields, number):
    if len(section['claims']) >= section['policy']['implementation_limit']:
        raise ValueError('All implementation slots are occupied; wait for a handoff')
    for claim in section['claims'].values():
        if any(claim[k] == fields[k] for k in ('session', 'branch', 'worktree')):
            raise ValueError('Each concurrent task needs its own agent run, branch and worktree')
    for key, record in section['tasks'].items():
        handoff = record.get('handoff', {})
        if key != str(number) and record['state'] not in ('merged', 'archived') and any(
                handoff.get(k) == fields[k] for k in ('branch', 'worktree')):
            raise ValueError('A pending task retains its branch and worktree through review/integration')
    lane = rules.review_lane(section, issue=number)
    if lane and lane['state'] != 'fixing':
        raise ValueError('Return the review to implementation before reclaiming this task')


def eligible(api, config, state, number, recover_from=None):
    from .queue import dependency_problems
    tasks = tasks_from_issues(api.issues(), config, state.get('delivery_workflow', {}).get('tasks', {}))
    issue = api.issue(number)
    candidate = issue
    statuses = {x for x in names(issue) if x.startswith('status:')}
    intended = 'status:' + workflow.target(config, 'in_progress')
    if recover_from and recover_from != intended and statuses == {recover_from, intended}:
        # The claimed start added its target but the old-label DELETE failed.
        # Validate every other field normally; the owner retries that exact write.
        candidate = dict(issue, labels=[{'name': x} for x in names(issue) if x != recover_from])
    task = tasks_from_issues([candidate], config, state.get('delivery_workflow', {}).get('tasks', {}))[0]
    if (issue.get('state') != 'open' or task['archive'] or task['initiative'] or task['phase'] in ('merged', 'review', 'approved', 'stage')
            or task['blocked'] or task['warnings'] or not task['module'] or not task['type']
            or dependency_problems(task, tasks)):
        raise ValueError('Choose an open classified unfinished task with no blockers or unfinished dependencies')
    return issue, task


def start(api, config, store, number, args):
    state, sha, section = read(store, config)
    fields = worker_fields(args)
    rules.context_module().require_ready(api, config, state, number, fields)
    current = section['claims'].get(str(number))
    if not getattr(args, 'resume', False):
        rules.admission_open(state)
    if getattr(args, 'resume', False):
        owned(current, args)
    issue, task = eligible(api, config, state, number, current.get('from_status') if getattr(args, 'resume', False) else None)
    record = section['tasks'].get(str(number), {})
    if record.get('state') == 'archiving':
        raise ValueError('Finish the pending archive before starting this task')
    if record.get('handoff', {}).get('pr') and record['state'] not in ('merged', 'archived') and record['handoff']['branch'] != fields['branch']:
        raise ValueError('Preserve the working branch through review and stage fixes')
    if getattr(args, 'resume', False):
        owned(current, args)
        if any(current[k] != v for k, v in fields.items()) or current['state'] != 'implementing':
            raise ValueError('Resume the recorded branch/worktree and pending operation before implementation')
    else:
        if current or str(number) in section['tasks'] and section['tasks'][str(number)]['state'] == 'queued':
            raise ValueError('This task already has an owner or review handoff')
        if task['phase'] == 'in_progress':
            raise ValueError('Unclaimed In Progress task; reconcile its previous execution before starting')
        available(section, fields, number)
        register(section, fields['actor'], fields['session'], 'Worker')
        current = dict(fields, id=uuid.uuid4().hex, issue=number, state='implementing', started_at=now(),
                       from_status=next(x for x in names(issue) if x.startswith('status:')))
        section['claims'][str(number)] = current
        record = section['tasks'].setdefault(str(number), {'implementers': []})
        record.update(state='implementing', worker=fields['actor'], coordinator=fields['coordinator'])
        record.pop('return', None)
        record.pop('reviewer', None)
        record['implementers'].append({'actor': fields['actor'], 'session': fields['session']})
        audit(section, 'claimed', issue=number, claim=current['id'], actor=fields['actor'])
        if str(number) in config.get('historical_completion', {}).get('tasks', {}):
            state.setdefault('delivery_workflow', {}).setdefault('tasks', {}).setdefault(str(number), {})['historical_revoked'] = True
        store.write(state, sha)
    # The reservation survives uncertain label writes. Resume uses the same claim.
    issue, _ = eligible(api, config, state, number, current.get('from_status'))
    rules.context_module().require_ready(api, config, state, number, fields)
    api.labels(number, {'status:' + workflow.target(config, 'in_progress')}, {x for x in names(issue) if x.startswith('status:')})
    return {'issue': number, 'id': identifiers.task_id(issue, config), 'claim': current,
            'instruction': 'In Progress verified; only this run may implement in its dedicated worktree.'}


def takeover(api, config, store, number, args):
    state, sha, section = read(store, config)
    old = section['claims'].get(str(number))
    if not old or old['id'] != args.previous_claim or old['state'] != 'implementing':
        raise ValueError('Takeover requires the current implementing claim; finish any pending handoff first')
    if not args.stopped or not args.reason or not args.reason.strip():
        raise ValueError('Verify the previous agent has stopped, then supply --stopped and a handoff --reason')
    fields = worker_fields(args)
    if fields['branch'] != old['branch']:
        raise ValueError('Takeover must preserve the recorded working branch')
    if fields['session'] == old['session']:
        raise ValueError('Use resume for the same agent run')
    rules.context_module().require_ready(api, config, state, number, fields)
    eligible(api, config, state, number, old.get('from_status'))
    del section['claims'][str(number)]
    available(section, fields, number)
    register(section, fields['actor'], fields['session'], 'Worker')
    claim = dict(fields, id=uuid.uuid4().hex, issue=number, state='implementing', started_at=now(), from_status=old.get('from_status'))
    section['claims'][str(number)] = claim
    record = section['tasks'][str(number)]
    record.update(worker=fields['actor'], coordinator=fields['coordinator'])
    record['implementers'].append({'actor': fields['actor'], 'session': fields['session']})
    audit(section, 'takeover', issue=number, previous=old, claim=claim['id'], reason=args.reason.strip())
    store.write(state, sha)
    return {'issue': number, 'claim': claim, 'instruction': 'Ownership transferred; inspect previous work before resuming.'}


def report(args):
    text = args.report_file.read_text(encoding='utf-8').strip()
    if not text:
        raise ValueError('Handoff needs actual checks, results, remaining risks and a durable work reference')
    return text


def handoff(api, config, store, number, args):
    state, sha, section = read(store, config)
    record = section['tasks'].get(str(number), {})
    current = section['claims'].get(str(number))
    if not current and record.get('state') in ('queued', 'reviewing'):
        owned(record.get('handoff'), args)
        if record['handoff']['pr'] != args.pr:
            raise ValueError('Handoff already refers to another PR')
        return {'issue': number, 'state': 'queued', 'already_applied': True}
    current = owned(current, args)
    if current['state'] not in ('implementing', 'handoff'):
        raise ValueError('Finish the pending claim operation first')
    pr = api.request(api.root + f'/pulls/{args.pr}')
    if (pr.get('state') != 'open' or pr.get('merged') or pr.get('draft')
            or pr['head']['ref'] != current['branch']
            or pr['head'].get('repo', {}).get('full_name', '').lower() != api.repository.lower()
            or pr_checks.linked_numbers(pr.get('body'), config) != [number]
            or rules.route(config, pr, api.request) == 'promotion'):
        raise ValueError('Handoff requires one ready source PR for this task in its recorded repository branch')
    rules.naming(config, pr, [number], api.request)
    body = report(args)
    if current['state'] == 'handoff' and (current['pr'] != args.pr or current['report'] != body):
        raise ValueError('Resume the same pending handoff without changing its PR or report')
    if current['state'] == 'implementing':
        current.update(state='handoff', pr=args.pr, report=body)
        store.write(state, sha)
    issue = api.issue(number)
    api.labels(number, {'status:' + workflow.target(config, 'review')}, {x for x in names(issue) if x.startswith('status:')})
    pr_checks.check(api.request, config, args.pr)
    state, sha, section = read(store, config)
    current = owned(section['claims'].get(str(number)), args)
    record = section['tasks'][str(number)]
    record.update(state='queued', handoff=copy.deepcopy(current), pr=args.pr, queued_at=now())
    del section['claims'][str(number)]
    lane = rules.review_lane(section, issue=number)
    if lane:
        if lane['state'] != 'fixing':
            raise ValueError('Review lane changed during the fix handoff')
        if rules.route(config, pr, api.request) == 'process' and not rules.process_module().idle(state, config):
            raise ValueError('Process fix handoff requires idle stage/intake/integration')
        lane.update(pr=args.pr, state='reviewing', started_at=now())
        audit(section, 'review-resumed', pr=args.pr, issues=[number])
        lane.pop('route', None)
        if rules.route(config, pr, api.request) == 'process':
            lane['route'] = 'process'
        record.update(state='reviewing', reviewer=lane['actor'])
        put_review(section, lane)
    elif number not in section['review_queue']:
        section['review_queue'].append(number)
    audit(section, 'handed-off', issue=number, pr=args.pr, actor=current['actor'])
    store.write(state, sha)
    return {'issue': number, 'state': record['state'], 'instruction': 'Implementation slot released; independent review may resume.'}


def stop(api, config, store, number, args):
    state, sha, section = read(store, config)
    current = owned(section['claims'].get(str(number)), args)
    if current['state'] not in ('implementing', 'stopping'):
        raise ValueError('Finish the pending handoff first')
    body = report(args)
    if current['state'] == 'stopping' and current['report'] != body:
        raise ValueError('Resume the same stop report')
    current.update(state='stopping', report=body)
    store.write(state, sha)
    issue = api.issue(number)
    api.labels(number, {'status:' + workflow.target(config, 'todo'), 'flag:blocked'}, {x for x in names(issue) if x.startswith('status:')})
    state, sha, section = read(store, config)
    current = owned(section['claims'].get(str(number)), args)
    section['tasks'][str(number)].update(state='stopped', handoff=copy.deepcopy(current))
    del section['claims'][str(number)]
    audit(section, 'stopped', issue=number, actor=current['actor'], report=body)
    store.write(state, sha)
    return {'issue': number, 'state': 'stopped', 'instruction': 'Unblock only after resolving the recorded handoff.'}


def acquire_review(api, config, store, args):
    state, sha, section = read(store, config)
    identity, session = credentials(args, 'Reviewer')
    coordinator = actor(args.coordinator, 'Coordinator')
    pool = section['policy']['schema_version'] == 3
    existing = rules.review_lane(section, pr=args.pr) if pool else section['review']
    if existing:
        if existing.get('route') == 'process' and not rules.process_module().idle(state, config):
            raise ValueError('Process review requires idle stage/intake/integration')
        owned(existing, args, 'Reviewer')
        if existing['pr'] != args.pr:
            raise ValueError('Another PR owns the review lane')
        return {'review': existing, 'resumed': True}
    rules.admission_open(state)
    if pool:
        if len(section['source_reviews']) >= section['policy']['review_limit']:
            raise ValueError('All source review slots are occupied; wait for approval or return')
        independent_slot(section, identity, session)
    linked = pr_checks.check(api.request, config, args.pr)
    pr = api.request(api.root + f'/pulls/{args.pr}')
    if (pr.get('merged') or pr.get('draft') or pr.get('state') != 'open' or rules.route(config, pr, api.request) == 'promotion'
            or rules.batch_mode(config) and rules.route(config, pr, api.request) not in ('approval', 'process')):
        raise ValueError('Review acquisition requires an open ready source PR')
    if len(linked['issues']) != 1:
        raise ValueError('Parallel execution uses one task per source PR')
    number = linked['issues'][0]
    record = section['tasks'].get(str(number), {})
    if number not in section['review_queue'] or record.get('pr') != args.pr or record.get('state') != 'queued':
        raise ValueError('The worker must finish the durable review handoff first')
    if any(i['actor'] == identity or i['session'] == session for i in record['implementers']):
        raise ValueError('The reviewer must not have implemented any work on this task')
    direction = rules.route(config, pr, api.request)
    if direction == 'process' and not rules.process_module().idle(state, config):
        raise ValueError('Process review requires idle stage/intake/integration')
    register(section, identity, session, 'Reviewer')
    lane = {'id': uuid.uuid4().hex, 'pr': args.pr, 'issues': [number], 'actor': identity,
            'session': session, 'coordinator': coordinator, 'started_at': now(), 'state': 'reviewing'}
    if direction == 'process':
        lane['route'] = 'process'
    put_review(section, lane)
    section['review_queue'].remove(number)
    record.update(state='reviewing', reviewer=identity)
    audit(section, 'review-acquired', pr=args.pr, lane=lane['id'], actor=identity)
    store.write(state, sha)
    return {'review': lane, 'instruction': 'Review this PR against current main; hold the lane through integration or return it for fixes.'}


def review_evidence(config, state, number, document, numbers):
    section = rules.execution_state(state, config)
    if section is None:
        return {}
    lane = rules.review_lane(section, pr=number)
    if (not lane or lane['state'] != 'reviewing' or lane['pr'] != number or set(lane['issues']) != set(numbers)
            or document.get('execution_lane') != lane['id'] or document.get('reviewer') != lane['actor']
            or document.get('review_session') != lane['session']):
        raise ValueError('Review evidence must identify the current independent review lane and session')
    for n in numbers:
        record = section['tasks'][str(n)]
        if (not lane.get('batch_id') and document.get('implementer') != record['worker']) or any(
                i['actor'] == lane['actor'] or i['session'] == lane['session'] for i in record['implementers']):
            raise ValueError('Review must identify the recorded worker and be independent of all implementers')
    if lane.get('batch_id'):
        batch = section.get('integration')
        if (not batch or batch['id'] != lane['batch_id'] or document.get('implementer') != batch['actor']
                or document.get('batch_id') != batch['id']
                or document.get('source_heads') != [m['head_sha'] for m in batch['members']]):
            raise ValueError('Integration review must attest the actual Coordinator, batch and exact approved source tips')
    return {'execution_lane': lane['id'], 'review_session': lane['session']}


def return_review(api, config, store, args):
    state, sha, section = read(store, config)
    lane = owned(rules.review_lane(section, claim=args.claim), args, 'Reviewer')
    if lane.get('route') == 'compatibility':
        raise ValueError('Use task-context review-release before the Coordinator returns an Approved source')
    if lane.get('batch_id'):
        raise ValueError('Use batch return for affected member authors; retain Coordinator integration ownership')
    pr = api.request(api.root + f'/pulls/{lane["pr"]}')
    keep = bool(getattr(args, 'keep_lane', False))
    if pr.get('merged') and not keep:
        raise ValueError('A merged source requires --keep-lane through stage fixes and main integration')
    if lane['state'] not in ('reviewing', 'returning'):
        raise ValueError('Finish the current review operation first')
    body = report(args)
    if lane['state'] == 'returning' and (lane['report'] != body or lane['keep_lane'] != keep):
        raise ValueError('Resume the same return report')
    lane.update(state='returning', report=body, keep_lane=keep)
    state.get('delivery_workflow', {}).get('reviews', {}).pop(str(lane['pr']), None)
    store.write(state, sha)
    for n in lane['issues']:
        issue = api.issue(n)
        api.labels(n, {'status:' + workflow.target(config, 'todo')}, {x for x in names(issue) if x.startswith('status:')})
    state, sha, section = read(store, config)
    lane = owned(rules.review_lane(section, claim=args.claim), args, 'Reviewer')
    for n in lane['issues']:
        section['tasks'][str(n)].update(state='changes_requested', review_report=body)
    audit(section, 'review-returned', review=copy.deepcopy(lane))
    if keep:
        lane['state'] = 'fixing'
    else:
        remove_review(section, lane)
    store.write(state, sha)
    return {'state': 'changes_requested', 'issues': lane['issues']}


def takeover_review(api, config, store, args):
    state, sha, section = read(store, config)
    old = rules.review_lane(section, claim=args.previous_claim)
    if not old or old['id'] != args.previous_claim or old['state'] == 'returning':
        raise ValueError('Use the current review claim and finish pending return operations first')
    if not args.stopped or not args.reason or not args.reason.strip():
        raise ValueError('Verify the previous reviewer stopped, then supply --stopped and --reason')
    identity, session = credentials(args, 'Reviewer')
    coordinator = actor(args.coordinator, 'Coordinator')
    if session == old['session']:
        raise ValueError('Resume the same reviewer with its claim')
    independent_slot(section, identity, session)
    for n in old['issues']:
        if any(i['actor'] == identity or i['session'] == session for i in section['tasks'][str(n)]['implementers']):
            raise ValueError('The replacement reviewer must be independent of every implementer')
    register(section, identity, session, 'Reviewer')
    lane = dict(old, id=uuid.uuid4().hex, actor=identity, session=session, coordinator=coordinator)
    if old.get('route') == 'compatibility':
        remove_review(section, old)
        put_review(section, lane)
        audit(section, 'compatibility-transferred', previous=copy.deepcopy(old), review=copy.deepcopy(lane), reason=args.reason)
        store.write(state, sha)
        return {'review': lane, 'instruction': 'Review the retained exact context; the previous owner supplied no new compatibility.'}
    if rules.batch_mode(config) and lane['state'] == 'approving':
        lane['state'] = 'reviewing'
        lane['approval_recovery'] = True
    remove_review(section, old)
    put_review(section, lane)
    # Previous evidence cannot be reused under a new reviewer identity. A source
    # already in stage can be independently reviewed at its actual merge tree.
    state.get('delivery_workflow', {}).get('reviews', {}).pop(str(old['pr']), None)
    if lane.get('batch_id'):
        batch = section.get('integration')
        if not batch or batch['id'] != lane['batch_id'] or coordinator != batch['actor']:
            raise ValueError('Use the current integration Coordinator when replacing its Reviewer')
    else:
        for n in lane['issues']:
            section['tasks'][str(n)]['reviewer'] = identity
    audit(section, 'review-takeover', previous=old, claim=lane['id'], reason=args.reason.strip())
    store.write(state, sha)
    return {'review': lane, 'instruction': 'Previous approval invalidated; independently review current content before integration.'}


def finish(config, store, numbers, prs):
    """Called only after verified main merge, receipt and label writes succeeded."""
    if not rules.execution_policy(config):
        if 'process_instructions' not in config:
            return
        state, sha = store.read(optional=True)
        tasks = state.get('delivery_workflow', {}).get('tasks', {})
        changed = False
        for number in numbers:
            receipt = tasks.get(str(number), {})
            if receipt.get('process') and not receipt.get('completed_at'):
                if ((state.get('active') or {}).get('issue') != number or [x['pr'] for x in receipt.get('sources', [])] != prs
                        or not rules.summary(receipt).get('verified')):
                    raise ValueError('Legacy process completion must retain its actual slot and source')
                receipt['completed_at'] = now()
                changed = True
        if changed:
            store.write(state, sha)
        return
    state, sha, section = read(store, config)
    lane = (rules.review_lane(section, pr=prs[0]) if section['policy']['schema_version'] == 3 and len(prs) == 1
            else section.get('review'))
    if rules.batch_mode(config) and (lane or {}).get('route') != 'process':
        if all(section['completed'].get(str(pr), {}).get('route') == 'process' for pr in prs):
            return
        from . import batches
        return batches.finish(config, store, numbers, prs)
    if all(str(pr) in section['completed'] for pr in prs):
        return
    if not lane or not set(lane['issues']) <= set(numbers):
        raise ValueError('Finish all tasks belonging to the current review lane before releasing it')
    if lane.get('route') == 'process':
        receipt = state.get('delivery_workflow', {}).get('tasks', {}).get(str(lane['issues'][0]), {})
        if (numbers != lane['issues'] or prs != [lane['pr']] or lane['state'] != 'reviewing'
                or not receipt.get('process') or not rules.summary(receipt).get('verified')
                or [x['pr'] for x in receipt.get('sources', [])] != prs):
            raise ValueError('Complete exactly the reviewed process source and its retained merge proof')
    for pr in set(prs) | {lane['pr']}:
        section['completed'][str(pr)] = copy.deepcopy(lane)
    for n in lane['issues']:
        section['tasks'][str(n)]['state'] = 'merged'
    audit(section, 'integrated', review=copy.deepcopy(lane), prs=prs)
    remove_review(section, lane)
    store.write(state, sha)


def public(section, delivery_workflow=None):
    """Exclude private paths, run IDs, claim tokens, reports and actor registry."""
    lane = section.get('review')
    result = {'implementation_limit': section['policy']['implementation_limit'], 'review_limit': section['policy']['review_limit'],
            'active': [{'issue': c['issue'], 'worker': c['actor'], 'coordinator': c['coordinator']}
                       for c in section['claims'].values()],
            'review_queue': section['review_queue'],
            'review': {k: lane[k] for k in ('pr', 'issues', 'actor', 'coordinator', 'state')} if lane else None,
            'tasks': {n: {k: row[k] for k in ('state', 'worker', 'reviewer', 'coordinator', 'pr') if k in row}
                      for n, row in section['tasks'].items()}}
    if section['policy']['schema_version'] == 3:
        result['source_reviews'] = [{k: row[k] for k in ('pr', 'issues', 'actor', 'coordinator', 'state')}
                                    for row in section['source_reviews'].values()]
        result['integration_review_limit'] = 1
    if section['policy']['schema_version'] in (2, 3):
        batch, intake = section.get('integration'), section.get('intake')
        # A batch ID is an ownership claim. Publish a separate, stable display
        # identity and an allowlisted history without changing any writer state.
        history = dict(section.get('batches', {}))
        if batch:
            history[batch['id']] = batch
        # Completed/cancelled entries retain durable insertion order; the active
        # entry follows them. Same-second starts must not renumber older batches.
        ordered = list(history.values())
        displays = {}
        for index, row in enumerate(ordered, 1):
            display = {k: row[k] for k in ('issues', 'actor', 'state', 'pr', 'started_at', 'finished_at') if k in row}
            display.update(id='batch-' + hashlib.sha256(row['id'].encode()).hexdigest()[:16], name=f'Batch {index}')
            from .batch_delivery import project
            display['delivery_evidence'] = project(row, delivery_workflow or {})
            if row.get('review', {}).get('actor'):
                display['reviewer'] = row['review']['actor']
            if batch and row['id'] == batch['id'] and lane and lane.get('batch_id') == batch['id']:
                display['reviewer'] = lane['actor']
            displays[row['id']] = display
        result.update(batch_limit=section['policy']['batch_limit'],
                      approved=[int(n) for n,r in section['tasks'].items() if r.get('state') == 'approved'],
                      integration=displays[batch['id']] if batch else None,
                      batches=list(displays.values()),
                      intake={k: intake[k] for k in ('issues', 'remaining', 'state')} if intake else None)
    return result


def archive(api, config, store, number, reason):
    from . import catalog
    if not reason or not reason.strip():
        raise ValueError('Archiving requires a reason')
    state, sha, section = read(store, config)
    if (str(number) in section['claims'] or number in section['review_queue']
            or rules.review_lane(section, issue=number)
            or section.get('integration') and number in section['integration']['issues']
            or section['tasks'].get(str(number), {}).get('state') == 'approved'
            or section.get('intake') and section['intake'].get('state') == 'running' and number in section['intake']['remaining']):
        raise ValueError('Finish the execution handoff before archiving this task')
    record = section['tasks'].setdefault(str(number), {'implementers': []})
    record['state'] = 'archiving'
    store.write(state, sha)
    result = catalog.archive(api, store, number, reason)
    state, sha, section = read(store, config)
    if section['tasks'][str(number)]['state'] != 'archiving':
        raise ValueError('Archive ownership changed; reconcile before continuing')
    section['tasks'][str(number)]['state'] = 'archived'
    audit(section, 'archived', issue=number, reason=reason)
    store.write(state, sha)
    return result
