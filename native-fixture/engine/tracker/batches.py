"""Owned, resumable approval/intake/batch mutations; never merge or deploy."""
import copy
import re
import uuid
from urllib.parse import quote
from . import batch_policy as proof, delivery_policy as rules, execution, pr_checks, workflow
from .model import names, tasks_from_issues
from .sync import now


def read(store, config):
    if not rules.batch_mode(config):
        raise ValueError('This command requires explicit execution policy schema 2')
    return execution.read(store, config)


def main(api, config):
    return api.request(api.root + '/git/ref/heads/' + quote(config['project']['base_branch'], safe=''))['object']['sha']


def coordinator(section, args):
    identity, session = execution.credentials(args, 'Coordinator')
    execution.register(section, identity, session, 'Coordinator')
    return identity, session


def owned(section, args):
    return execution.owned(section.get('integration'), args, 'Coordinator')


def mark_stage(api, batch, state):
    candidate = state.get('delivery_workflow', {}).get('stage', {})
    if (batch['entered_stage'] or candidate.get('batch_id') == batch['id']
            or batch['pr'] and api.request(api.root + f'/pulls/{batch["pr"]}').get('merged')):
        batch['entered_stage'] = True


def before_main(api, config, batch):
    if (not rules.policy(config)['staging']['enabled'] and batch.get('pr')
            and api.request(api.root + f'/pulls/{batch["pr"]}').get('merged')):
        raise ValueError('Direct-main batch is already merged; finish its retained completion before new task work')


def approve(api, config, store, args):
    state, sha, section = read(store, config)
    lane = rules.review_lane(section, claim=args.claim) if section['policy']['schema_version'] == 3 else section.get('review')
    if not lane:
        matches = [a for a in section['approvals'].values() if a['lane']['id'] == args.claim]
        if len(matches) != 1:
            raise ValueError('No source approval belongs to this review claim')
        execution.owned(matches[0]['lane'], args, 'Reviewer')
        proof.source(api.request, config, matches[0], main(api, config))
        return {'already_applied': True, 'issue': matches[0]['issue'], 'state': 'approved'}
    execution.owned(lane, args, 'Reviewer')
    if lane.get('batch_id') or lane.get('route') == 'compatibility' or lane['state'] not in ('reviewing', 'approving'):
        raise ValueError('Approve one source task, not the integration candidate')
    number = lane['issues'][0]
    pr = api.request(api.root + f'/pulls/{lane["pr"]}')
    if rules.route(config, pr, api.request) != 'approval' or pr.get('merged'):
        raise ValueError('Source approvals require an unmerged approval-only working PR')
    receipt = state.get('delivery_workflow', {}).get('reviews', {}).get(str(lane['pr']), {})
    if (receipt.get('execution_lane') != lane['id'] or receipt.get('reviewer') != lane['actor']
            or receipt.get('review_session') != lane['session']):
        raise ValueError('Record the current independent review before approval')
    baseline = main(api, config)
    scope = proof.scope(api.issue(number), config)
    if receipt.get('issue_scopes') != {str(number): scope}:
        raise ValueError('Task scope changed after review')
    approval = dict(issue=number, pr=lane['pr'], branch=pr['head']['ref'], head_sha=pr['head']['sha'],
                    base_sha=pr['base']['sha'], main_sha=baseline, policy=rules.fingerprint(config),
                    scope=scope, review=copy.deepcopy(receipt), lane=copy.deepcopy(lane), approved_at=now())
    proof.source(api.request, config, approval, baseline, phases=('review', 'approved'), pending=True)
    if lane['state'] == 'reviewing':
        lane.update(state='approving', approval=approval)
        store.write(state, sha)
    elif any(lane['approval'][k] != approval[k] for k in ('pr', 'scope', 'head_sha', 'base_sha', 'main_sha', 'review')):
        raise ValueError('Resume the journaled approval without changing source or scope')
    labels = names(api.issue(number))
    api.labels(number, {'status:' + workflow.target(config, 'approved')}, {x for x in labels if x.startswith('status:')})
    state, sha, section = read(store, config)
    lane = execution.owned(rules.review_lane(section, claim=args.claim), args, 'Reviewer')
    approval = lane['approval']
    proof.source(api.request, config, approval, main(api, config))
    section['approvals'][str(number)] = approval
    section['tasks'][str(number)].update(state='approved')
    execution.audit(section, 'source-approved', issue=number, pr=lane['pr'], review=copy.deepcopy(lane))
    execution.remove_review(section, lane)
    store.write(state, sha)
    return {'issue': number, 'state': 'approved', 'instruction': 'Review slot released; source PR remains unmerged.'}


def eligible(api, config, state, section, number, baseline, tasks=None):
    if (rules.review_lane(section, issue=number) or {}).get('route') == 'compatibility':
        raise ValueError(f'#{number}: finish the owned compatibility review before batch selection')
    approval = section['approvals'].get(str(number))
    if not approval or section['tasks'].get(str(number), {}).get('state') != 'approved':
        raise ValueError(f'#{number}: no completed source approval')
    proof.source(api.request, config, approval, baseline)
    from .queue import dependency_problems
    if tasks is None:
        tasks = tasks_from_issues(api.issues(), config, state.get('delivery_workflow', {}).get('tasks', {}))
    task = next(t for t in tasks if t['number'] == number)
    if task['warnings'] or task['initiative'] or dependency_problems(task, tasks):
        raise ValueError(f'#{number}: dependencies or classification prevent integration')
    return copy.deepcopy(approval)


def intake(api, config, store, args):
    state, sha, section = read(store, config)
    if any(lane.get('route') == 'process' for lane in rules.review_lanes(section)):
        raise ValueError('Finish or return the held process review before freezing an intake')
    identity, session = coordinator(section, args)
    old = section.get('intake')
    if old and old['state'] == 'running':
        execution.owned(old, args, 'Coordinator')
        return {'intake': old, 'resumed': True}
    rules.admission_open(state)
    if section.get('integration'):
        raise ValueError('Finish the active integration batch first')
    if bool(args.all_approved) == bool(args.issues):
        raise ValueError('Select --all-approved or explicit --issues, exactly one')
    numbers = args.issues or [int(n) for n, a in sorted(section['approvals'].items(), key=lambda x: x[1]['approved_at'])
                              if section['tasks'].get(n, {}).get('state') == 'approved']
    if not numbers or len(numbers) != len(set(numbers)):
        raise ValueError('Intake requires a nonempty unique task set')
    baseline = main(api, config)
    tasks = tasks_from_issues(api.issues(), config, state.get('delivery_workflow', {}).get('tasks', {}))
    if args.all_approved:
        by_number = {t['number']: t for t in tasks}
        priorities = {'high': 0, 'medium': 1, 'low': 2}
        numbers.sort(key=lambda n: (priorities.get(by_number[n]['priority'], 1), section['approvals'][str(n)]['approved_at'], n))
    rejected, accepted = {}, []
    for n in numbers:
        try:
            eligible(api, config, state, section, n, baseline, tasks)
            accepted.append(n)
        except ValueError as error:
            rejected[str(n)] = str(error)
    if not accepted:
        return {'applied': False, 'ineligible': rejected, 'instruction': 'Return stale tasks for author fixes and fresh review.'}
    row = dict(id=uuid.uuid4().hex, actor=identity, session=session, state='running', issues=accepted,
               remaining=accepted[:], batches=[], started_at=now(), ineligible=rejected)
    section['intake'] = row
    execution.audit(section, 'intake-frozen', intake=copy.deepcopy(row))
    store.write(state, sha)
    return {'intake': row, 'ineligible': rejected, 'instruction': 'New approvals wait for another intake; begin sequential bounded batches.'}


def begin(api, config, store, args):
    state, sha, section = read(store, config)
    if any(lane.get('route') == 'process' for lane in rules.review_lanes(section)):
        raise ValueError('Finish or return the held process review before beginning a batch')
    identity, session = coordinator(section, args)
    if section.get('integration'):
        batch = owned(section, args)
        if getattr(args, 'deliver', False) and not batch.get('delivery_request'):
            raise ValueError('Existing batch was frozen without delivery authorization; finish or cancel it before a newly authorized batch')
        if getattr(args, 'deliver', False) and any(batch['delivery_request'].get(k) != getattr(args, 'delivery_' + k, None)
                                                 for k in ('workflow', 'job')):
            raise ValueError('Resume the original authorized delivery workflow and job')
        return {'batch': batch, 'resumed': True}
    rules.admission_open(state)
    if rules.pending_delivery(state, config):
        raise ValueError('Finish the previous authorized batch delivery to this target before advancing main')
    snapshot = section.get('intake')
    if not snapshot or snapshot['state'] != 'running':
        raise ValueError('Freeze an explicit intake before beginning a batch')
    # The intake and batch have different claim IDs; supply --intake for selection.
    if (snapshot['id'], snapshot['actor'], snapshot['session']) != (args.intake, identity, session):
        raise ValueError('This Coordinator does not own the frozen intake')
    numbers = args.issues or snapshot['remaining'][:section['policy']['batch_limit']]
    if (not numbers or len(numbers) != len(set(numbers)) or len(numbers) > section['policy']['batch_limit']
            or not set(numbers) <= set(snapshot['remaining'])):
        raise ValueError('Choose remaining intake members within the configured batch limit')
    baseline = main(api, config)
    candidate = state.get('delivery_workflow', {}).get('stage', {})
    stage_sha = (api.request(api.root + '/git/ref/heads/' + quote(rules.policy(config)['staging']['branch'], safe=''))['object']['sha']
                 if rules.policy(config)['staging']['enabled'] else None)
    if (candidate and candidate.get('state') != 'promoted'
            or stage_sha and rules.tree(api.request, api.root, stage_sha) != rules.tree(api.request, api.root, baseline)
            and not ('process_instructions' in config and rules.process_module().stage_base_compatible(api.request, config, stage_sha, baseline, state))):
        raise ValueError('Finish the existing stage candidate and reconcile stage with main first')
    tasks = tasks_from_issues(api.issues(), config, state.get('delivery_workflow', {}).get('tasks', {}))
    members = [eligible(api, config, state, section, n, baseline, tasks) for n in numbers]
    token = uuid.uuid4().hex
    batch = dict(id=token, actor=identity, session=session, state='assembling', issues=numbers,
                 members=members, main_sha=baseline, branch='codex/batch-' + token,
                 intake=snapshot['id'], started_at=now(), pr=None, entered_stage=False, history=[])
    if getattr(args, 'deliver', False):
        producer, job = getattr(args, 'delivery_workflow', None), getattr(args, 'delivery_job', None)
        if (not isinstance(producer, str) or not re.fullmatch(r'\.github/workflows/[A-Za-z0-9][A-Za-z0-9_-]*\.ya?ml', producer)
                or not isinstance(job, str) or not job.strip() or job != job.strip() or len(job) > 200):
            raise ValueError('--deliver requires an explicit --delivery-workflow .github/workflows/NAME.yml and --delivery-job exact native job name')
        batch['delivery_request'] = dict(schema_version=1, state='requested', batch_id=token, issues=numbers[:],
            policy=rules.fingerprint(config), target=rules.policy(config)['delivery_target'],
            workflow=producer, job=job, actor=identity, session=session, requested_at=now())
    section['integration'] = batch
    execution.audit(section, 'batch-frozen', batch=copy.deepcopy(batch))
    store.write(state, sha)
    return {'batch': batch, 'instruction': 'Assemble exact approved tips on this branch, then acquire independent batch review.'}


def acquire_review(api, config, store, args):
    state, sha, section = read(store, config)
    batch = section.get('integration')
    if not batch:
        raise ValueError('No active integration batch')
    if section.get('review'):
        execution.owned(section['review'], args, 'Reviewer')
        if section['review'].get('batch_id') != batch['id'] or section['review']['pr'] != args.pr:
            raise ValueError('Another PR owns the independent review slot')
        return {'review': section['review'], 'resumed': True}
    rules.admission_open(state)
    identity, session = execution.credentials(args, 'Reviewer')
    execution.independent_slot(section, identity, session)
    coordinator_id = execution.actor(args.coordinator, 'Coordinator')
    if coordinator_id != batch['actor'] or session == batch['session']:
        raise ValueError('Review requires an independent run and the actual batch Coordinator')
    linked = pr_checks.check(api.request, config, args.pr)
    pr = api.request(api.root + f'/pulls/{args.pr}')
    expected_route = 'stage' if rules.policy(config)['staging']['enabled'] else 'batch'
    if pr.get('draft') or pr.get('state') != 'open' or rules.route(config, pr, api.request) != expected_route:
        raise ValueError('Batch review requires its open ready integration PR into the configured branch')
    proof.validate_candidate(api.request, config, pr, linked['issues'], batch, state)
    for n in batch['issues']:
        if any(i['actor'] == identity or i['session'] == session for i in section['tasks'][str(n)]['implementers']):
            raise ValueError('Integration reviewer must be independent of every member implementer')
    execution.register(section, identity, session, 'Reviewer')
    lane = dict(id=uuid.uuid4().hex, batch_id=batch['id'], pr=args.pr, issues=batch['issues'][:], actor=identity,
                session=session, coordinator=coordinator_id, state='reviewing', started_at=now())
    batch.update(pr=args.pr, state='reviewing')
    section['review'] = lane
    execution.audit(section, 'batch-review-acquired', review=copy.deepcopy(lane))
    store.write(state, sha)
    return {'review': lane, 'instruction': 'Review exact combined content and source composition; retain the lane through promotion.'}


def return_task(api, config, store, number, args):
    state, sha, section = read(store, config)
    identity, session = coordinator(section, args)
    batch = section.get('integration')
    member = batch and number in batch['issues']
    snapshot = section.get('intake')
    selected = snapshot and snapshot['state'] == 'running' and number in snapshot['remaining']
    if member:
        owned(section, args)
        before_main(api, config, batch)
        mark_stage(api, batch, state)
    elif selected:
        execution.owned(snapshot, args, 'Coordinator')
    record = section['tasks'].get(str(number), {})
    pending = record.get('return') if record.get('state') in ('returning_approval', 'changes_requested') else None
    if record.get('state') == 'changes_requested' and pending:
        if not member and not selected:
            execution.owned(pending, args, 'Coordinator')
        return {'issue': number, 'already_applied': True}
    approval = section['approvals'].get(str(number))
    if not approval or not member and not selected and not pending and approval['lane']['coordinator'] != identity:
        raise ValueError('Only the recorded Coordinator may return this approved task')
    lane = (rules.review_lane(section, issue=number) if section['policy']['schema_version'] == 3
            else section.get('review'))
    if lane and (not member or lane.get('batch_id') != batch['id']):
        raise ValueError('Finish the independent source review operation first')
    text = execution.report(args)
    if pending and (pending['report'] != text or pending['session'] != session):
        raise ValueError('Resume the same pending author return')
    row = pending or dict(id=args.claim or uuid.uuid4().hex, actor=identity, session=session, report=text)
    record.update(state='returning_approval', return_operation=copy.deepcopy(row))
    record['return'] = row
    if member:
        batch['state'] = 'fixing'
        if section.get('review'):
            batch['history'].append({'review': copy.deepcopy(section['review']), 'reason': text})
            state.get('delivery_workflow', {}).get('reviews', {}).pop(str(batch['pr']), None)
            section['review'] = None
        candidate = state.get('delivery_workflow', {}).get('stage', {})
        if candidate.get('batch_id') == batch['id']:
            candidate.update(state='failed', failure_report=text)
    store.write(state, sha)
    labels = names(api.issue(number))
    api.labels(number, {'status:' + workflow.target(config, 'todo')}, {x for x in labels if x.startswith('status:')})
    state, sha, section = read(store, config)
    record = section['tasks'][str(number)]
    if record.get('return') != row or record['state'] != 'returning_approval':
        raise ValueError('Author return ownership changed; reconcile before continuing')
    record.update(state='changes_requested', review_report=text)
    section['approvals'].pop(str(number), None)
    execution.audit(section, 'approval-returned', issue=number, operation=row, batch_id=batch['id'] if member else None)
    store.write(state, sha)
    return {'issue': number, 'state': 'changes_requested', 'claim': row['id'],
            'instruction': 'Author claims the original branch, then checks, handoff and fresh independent approval.'}


def refresh(api, config, store, args):
    state, sha, section = read(store, config)
    batch = owned(section, args)
    before_main(api, config, batch)
    mark_stage(api, batch, state)
    if section.get('review'):
        raise ValueError('Finish or return the current review before rebuilding')
    baseline = main(api, config)
    members = []
    for old in batch['members']:
        new = section['approvals'].get(str(old['issue']))
        if not new:
            raise ValueError('Every returned member needs a fresh approval before rebuilding')
        proof.source(api.request, config, new, baseline, phases=('approved', 'stage'))
        members.append(copy.deepcopy(new))
    proof.dependencies_ready(api.request, config, batch['issues'], state)
    batch['history'].append({'members': copy.deepcopy(batch['members']), 'main_sha': batch['main_sha'], 'pr': batch['pr'], 'at': now()})
    batch.update(members=members, main_sha=baseline, pr=None, state='assembling')
    execution.audit(section, 'batch-refreshed', batch_id=batch['id'])
    store.write(state, sha)
    return {'batch': batch, 'instruction': 'Rebuild the same held member set; preserve already integrated work and independently review the new candidate.'}


def return_candidate(api, config, store, args):
    state, sha, section = read(store, config)
    lane = execution.owned(section.get('review'), args, 'Reviewer')
    batch = section.get('integration')
    if not batch or lane.get('batch_id') != batch['id']:
        raise ValueError('Only the current integration Reviewer can return this candidate')
    before_main(api, config, batch)
    mark_stage(api, batch, state)
    text = execution.report(args)
    batch['history'].append({'review': copy.deepcopy(lane), 'reason': text, 'at': now()})
    batch['state'] = 'fixing'
    state.get('delivery_workflow', {}).get('reviews', {}).pop(str(lane['pr']), None)
    candidate = state.get('delivery_workflow', {}).get('stage', {})
    if candidate.get('batch_id') == batch['id']:
        candidate.update(state='failed', failure_report=text)
    section['review'] = None
    execution.audit(section, 'batch-review-returned', batch_id=batch['id'], report=text)
    store.write(state, sha)
    return {'state': 'fixing', 'instruction': 'Coordinator keeps integration ownership; return affected members or rebuild the reviewed composition.'}


def cancel_intake(api, config, store, args):
    state, sha, section = read(store, config)
    execution.owned(section.get('intake'), args, 'Coordinator')
    if section.get('integration'):
        raise ValueError('Finish the held batch before cancelling its remaining intake')
    text = execution.report(args)
    section['intake'].update(state='cancelled', report=text)
    execution.audit(section, 'intake-cancelled', intake=copy.deepcopy(section['intake']))
    store.write(state, sha)
    return {'state': 'cancelled', 'instruction': 'Unintegrated tasks retain their actual status and approval history.'}


def close_sources(api, config, store, args):
    state, sha, section = read(store, config)
    batch = section['batches'].get(args.batch_id)
    if not batch or batch.get('state') != 'merged':
        raise ValueError('Only a completed admitted batch can close superseded source PRs')
    for number in batch['main_prs']:
        pr_checks.check(api.request, config, number, allow_transition=True, admission=True)
        pr = api.request(api.root + f'/pulls/{number}')
        comparison = api.request(api.root + '/compare/' + pr['merge_commit_sha'] + '...' + quote(config['project']['base_branch'], safe=''))
        if comparison.get('status') not in ('ahead', 'identical'):
            raise ValueError('Batch merge is no longer included in main')
    for member in batch['members']:
        for number in batch['main_prs']:
            pr = api.request(api.root + f'/pulls/{number}')
            proof.source(api.request, config, member, batch['main_sha'], phases=('merged',),
                         completed=True, frozen=True, included_in=pr['merge_commit_sha'])
    # Checklist recovery remains bound to the admitted scope during cleanup too.
    from . import acceptance
    for member in batch['members']:
        item = api.issue(member['issue'])
        if acceptance.criteria(item.get('body')):
            acceptance.verify(api, config, store, item, batch['main_prs'])
    batch['closing_sources'] = True
    store.write(state, sha)
    for member in batch['members']:
        pr = api.request(api.root + f'/pulls/{member["pr"]}')
        if pr['head']['sha'] != member['head_sha']:
            raise ValueError('Source changed while closing; preserve it and reconcile')
        if not pr.get('merged') and pr.get('state') == 'open':
            api.request(api.root + f'/pulls/{member["pr"]}', 'PATCH', {'state': 'closed'})
    state, sha, section = read(store, config)
    section['batches'][args.batch_id].update(closing_sources=False, sources_closed=True)
    execution.audit(section, 'included-sources-closed', batch_id=args.batch_id)
    store.write(state, sha)
    return {'state': 'sources_closed', 'prs': [m['pr'] for m in batch['members']]}


def cancel_delivery(api, config, store, args):
    state, sha, section = read(store, config)
    batch = section['batches'].get(args.batch_id)
    request = batch.get('delivery_request') if batch else None
    if not batch or batch.get('state') != 'merged' or not request:
        raise ValueError('Only an archived merged batch with explicit delivery authorization can cancel delivery')
    identity, session = coordinator(section, args)
    text = execution.report(args)
    previous = request.get('cancelled_by') or {'actor': batch['actor'], 'session': batch['session']}
    if (identity, session) != (previous['actor'], previous['session']):
        if (getattr(args, 'previous_claim', None) != batch['id'] or not getattr(args, 'stopped', False)
                or not getattr(args, 'reason', None) or not args.reason.strip()):
            raise ValueError('Resume the actual Coordinator or explicitly transfer its stopped delivery ownership')
    elif getattr(args, 'claim', None) != batch['id']:
        raise ValueError('Supply the exact archived batch claim for delivery cancellation')
    if request.get('state') == 'cancelled':
        if request.get('cancellation_report') != text:
            raise ValueError('Resume the original cancellation report')
        return {'state': 'cancelled', 'already_applied': True, 'issues': batch['issues']}
    from . import batch_delivery
    projected = copy.deepcopy(batch)
    projected['delivery_evidence'] = batch_delivery.project(batch, state.get('delivery_workflow', {}))
    batch_delivery.finish(projected, config)
    if projected['delivery']['complete']:
        raise ValueError('Verified completed delivery has no pending request to cancel')
    batch['history'].append(dict(delivery_request=copy.deepcopy(request), cancellation_owner=dict(actor=identity, session=session),
                                previous_owner=previous, reason=getattr(args, 'reason', None), at=now()))
    request.update(state='cancelled', cancelled_by=dict(actor=identity, session=session),
                   cancellation_report=text, cancelled_at=now())
    execution.audit(section, 'batch-delivery-cancelled', batch_id=batch['id'], actor=identity, session=session, report=text)
    store.write(state, sha)
    return {'state': 'cancelled', 'issues': batch['issues'],
            'instruction': 'Delivery request cancelled only; task receipts and incomplete delivery remain. New fixes need their own reviewed batch.'}


def cancel(api, config, store, args):
    state, sha, section = read(store, config)
    batch = owned(section, args)
    report = execution.report(args)
    pr = api.request(api.root + f'/pulls/{batch["pr"]}') if batch['pr'] else {}
    if batch['entered_stage'] or pr.get('merged'):
        raise ValueError('A batch that entered stage retains ownership through fixes and promotion')
    if section.get('review') and section['review'].get('batch_id') != batch['id']:
        raise ValueError('Finish the active source review first')
    # Cancellation never approves or rewrites members. Before a real stage merge
    # it can also release a stale/returned candidate, preserving actual author
    # claims/status and allowing a smaller next selection from the fixed intake.
    if section.get('review'):
        state.get('delivery_workflow', {}).get('reviews', {}).pop(str(batch['pr']), None)
        section['review'] = None
    batch.update(state='cancelled', report=report)
    section['batches'][batch['id']] = copy.deepcopy(batch)
    section['integration'] = None
    execution.audit(section, 'batch-cancelled', batch=copy.deepcopy(batch))
    store.write(state, sha)
    return {'state': 'cancelled', 'issues': batch['issues'], 'instruction': 'Unchanged members remain Approved in the frozen intake.'}


def takeover(api, config, store, args):
    state, sha, section = read(store, config)
    if getattr(args, 'issue', None):
        record = section['tasks'].get(str(args.issue), {})
        previous = record.get('return')
        if (section.get('integration') and args.issue in section['integration']['issues']
                or section.get('intake') and section['intake']['state'] == 'running' and args.issue in section['intake']['remaining']
                or record.get('state') != 'returning_approval' or not previous
                or previous['id'] != args.previous_claim or not args.stopped or not args.reason or not args.reason.strip()):
            raise ValueError('Only a stopped standalone pending author-return owner can transfer with --issue')
        identity, session = coordinator(section, args)
        if session == previous['session']:
            raise ValueError('Resume the owning Coordinator with its return claim')
        old = copy.deepcopy(previous)
        previous.update(id=uuid.uuid4().hex, actor=identity, session=session)
        record['return_operation'] = copy.deepcopy(previous)
        execution.audit(section, 'author-return-takeover', issue=args.issue, previous=old, owner=copy.deepcopy(previous), reason=args.reason.strip())
        store.write(state, sha)
        return {'return_claim': previous['id'], 'instruction': 'Resume batch return with this claim and the same report.'}
    old = section.get('integration') or section.get('intake')
    if not old or old['id'] != args.previous_claim or not args.stopped or not args.reason or not args.reason.strip():
        raise ValueError('Inspect the held batch, stop its old Coordinator, and supply current --previous-claim --stopped --reason')
    identity, session = coordinator(section, args)
    if session == old['session']:
        raise ValueError('Resume the owning Coordinator with its claim')
    if not section.get('integration') and old.get('state') != 'running':
        raise ValueError('Only a running intake needs ownership transfer')
    # Frozen identity/member set stays immutable; old actor/session loses ownership.
    previous = copy.deepcopy(old)
    old.update(actor=identity, session=session)
    old.setdefault('history', []).append({'coordinator': previous['actor'], 'session': previous['session'], 'reason': args.reason.strip(), 'at': now()})
    if not section.get('integration'):
        for n in old['remaining']:
            record = section['tasks'][str(n)]
            pending = record.get('return')
            if record.get('state') == 'returning_approval' and pending:
                old['history'].append({'pending_author_return': copy.deepcopy(pending), 'issue': n})
                pending.update(actor=identity, session=session)
                record['return_operation'] = copy.deepcopy(pending)
        execution.audit(section, 'intake-takeover', previous=previous, actor=identity, reason=args.reason.strip())
        store.write(state, sha)
        return {'intake': old, 'instruction': 'Resume the unchanged fixed intake; no tasks were approved or completed.'}
    snapshot = section.get('intake')
    remaining = snapshot['remaining'] if snapshot and snapshot['id'] == old['intake'] else []
    for n in set(old['issues']) | set(remaining):
        record = section['tasks'][str(n)]
        pending = record.get('return')
        if record.get('state') == 'returning_approval' and pending:
            old['history'].append({'pending_author_return': copy.deepcopy(pending), 'issue': n})
            pending.update(actor=identity, session=session)
            record['return_operation'] = copy.deepcopy(pending)
    if snapshot and snapshot['id'] == old['intake']:
        snapshot.update(actor=identity, session=session)
    if section.get('review') and section['review'].get('batch_id') == old['id']:
        section['review']['coordinator'] = identity
    execution.audit(section, 'batch-takeover', previous=previous, actor=identity, reason=args.reason.strip())
    store.write(state, sha)
    return {'batch': old, 'instruction': 'Ownership transferred; preserve the frozen set and existing exact-content evidence.'}


def finish(config, store, numbers, prs):
    state, sha, section = read(store, config)
    if all(str(pr) in section['completed'] for pr in prs):
        return
    batch = section.get('integration')
    lane = section.get('review')
    if not batch or not lane or lane.get('batch_id') != batch['id'] or set(numbers) != set(batch['issues']):
        raise ValueError('Complete every frozen member before releasing integration ownership')
    workflow_state = state.get('delivery_workflow', {})
    if rules.policy(config)['staging']['enabled']:
        candidate = workflow_state.get('stage', {})
        if candidate.get('state') != 'promoted' or candidate.get('batch_id') != batch['id']:
            raise ValueError('Only a verified promoted batch can finish')
    elif (prs != [batch['pr']] or any(workflow_state.get('main_batches', {}).get(str(pr), {}).get('batch_id') != batch['id']
                                    for pr in prs)):
        raise ValueError('Only the admitted direct-main batch can finish')
    for n in batch['issues']:
        section['tasks'][str(n)].update(state='merged', batch_id=batch['id'])
    batch.update(state='merged', review=copy.deepcopy(lane), main_prs=prs[:], finished_at=now())
    for pr in set(prs) | {batch['pr']}:
        section['completed'][str(pr)] = copy.deepcopy(lane)
    section['batches'][batch['id']] = copy.deepcopy(batch)
    snapshot = section['intake']
    snapshot['remaining'] = [n for n in snapshot['remaining'] if n not in batch['issues']]
    snapshot['batches'].append(batch['id'])
    if not snapshot['remaining']:
        snapshot['state'] = 'finished'
    execution.audit(section, 'batch-integrated', batch=copy.deepcopy(batch))
    section['integration'] = section['review'] = None
    store.write(state, sha)
