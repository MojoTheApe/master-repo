"""Inspected staging-only policy changes; retain original evidence and queues."""
import copy
import json
from types import SimpleNamespace
from urllib.parse import quote
from . import delivery_policy as rules, maintenance, pr_checks, workflow
from .model import load_config, names
from .sync import now


def batch_bound(state, number, sources):
    """Known modern work must never escape admission through missing PR text."""
    section = state.get('execution', {})
    workflow_state = state.get('delivery_workflow', {})
    prs = {source['pr'] for source in sources}
    task = section.get('tasks', {}).get(str(number), {})
    if 'batch_id' in task or 'delivery_request' in task:
        return True
    rows = list(section.get('batches', {}).values())
    if section.get('integration'):
        rows.append(section['integration'])
    for group in ('completed', 'approvals'):
        for key, row in section.get(group, {}).items():
            if 'batch_id' in row or 'delivery_request' in row:
                if (group == 'completed' and int(key) in prs) or (group == 'approvals' and int(key) == number):
                    return True
                rows.append(row)
    rows += list(workflow_state.get('main_batches', {}).values())
    for group in ('promotions', 'reviews', 'acceptances'):
        for key, row in workflow_state.get(group, {}).items():
            if 'batch_id' in row or 'delivery_request' in row:
                if int(key) in prs:
                    return True
                rows.append(row)
    stage = workflow_state.get('stage', {})
    if 'batch_id' in stage or 'delivery_request' in stage:
        rows.append(stage)
    for row in rows:
        request = row.get('delivery_request', {})
        if (number in row.get('issues', []) or row.get('issue') == number
                or row.get('pr') in prs or prs.intersection(row.get('main_prs', []))
                or number in request.get('issues', [])
                or any(member.get('issue') == number or member.get('pr') in prs for member in row.get('members', []))):
            return True
    # The map key itself is the main PR identity, even in a damaged admission row.
    return bool(prs.intersection(int(pr) for pr in workflow_state.get('main_batches', {})))


def legacy_pending(api, previous, state, number, receipt):
    """Recognize only untouched, unfinished pre-batch promotion evidence.

    No current-policy admission or reconciliation is granted. Unknown formats,
    any verification/history, and every known modern binding use full admission.
    """
    if (set(receipt) != {'policy', 'sources', 'state', 'recorded_at'} or receipt['state'] != 'pending'
            or not isinstance(receipt['recorded_at'], str) or not receipt['recorded_at']
            or not isinstance(receipt['sources'], list) or not receipt['sources']):
        return False
    for source in receipt['sources']:
        if (not isinstance(source, dict) or set(source) != {'pr', 'merge_sha', 'tree_sha'}
                or type(source['pr']) is not int or source['pr'] <= 0
                or any(not isinstance(source[k], str) or not rules.SHA.fullmatch(source[k]) for k in ('merge_sha', 'tree_sha'))):
            return False
    if batch_bound(state, number, receipt['sources']):
        return False
    for source in receipt['sources']:
        pr = api.request(api.root + f'/pulls/{source["pr"]}')
        if (pr['head']['ref'] != rules.policy(previous)['staging']['branch']
                or 'tracker batch' in (pr.get('body') or '').lower()):
            return False
        if (not pr.get('merged') or pr['base']['ref'] != previous['project']['base_branch']
                or any(pr[side].get('repo', {}).get('full_name', '').lower() != api.repository.lower() for side in ('base', 'head'))
                or number not in pr_checks.linked_numbers(pr.get('body'), previous)
                or pr['merge_commit_sha'] != source['merge_sha']):
            raise ValueError('Historical pending retention needs original official main promotion metadata')
    return True


def closed_untracked(item, config, state):
    """Preserve old closed metadata only; never infer a completed workflow task."""
    number = item['number']
    if (item.get('state') != 'closed' or item.get('state_reason') != 'completed'
            or any(label.startswith('status:') for label in names(item))
            or str(number) in (config.get('historical_completion') or {}).get('tasks', {})):
        return False

    def bound(value):
        if isinstance(value, list):
            return any(bound(row) for row in value)
        if not isinstance(value, dict):
            return False
        # These are task identities. An unrelated PR number or actor ID must not
        # match an Issue merely because it contains the same decimal number.
        if value.get('issue') == number:
            return True
        for key in ('issues', 'todo_order', 'review_queue'):
            if key in value:
                if not isinstance(value[key], list):
                    raise ValueError('Unsupported historical task identity list: ' + key)
                if number in value[key]:
                    return True
        for key in ('tasks', 'claims', 'approvals'):
            if key not in value:
                continue
            rows = value[key]
            if key == 'tasks' and isinstance(rows, list):
                if any(row == number or isinstance(row, dict) and row.get('number') == number for row in rows):
                    return True
            elif not isinstance(rows, dict):
                raise ValueError('Unsupported historical task identity map: ' + key)
            elif str(number) in rows:
                return True
        # todo_added is a retained sort timestamp, not actual Todo membership.
        # Keep the metadata intact; todo_order/run/labels still establish work.
        if 'todo_added' in value and not isinstance(value['todo_added'], dict):
            raise ValueError('Unsupported historical Todo timestamp map')
        # Our own retention-only audit is not task ownership. It must not block
        # a later inspected Stage toggle merely by documenting preserved history.
        return any(bound(row) for key, row in value.items() if key != 'retained_untracked_closed')

    return not bound(state)


def compatible(previous, config):
    old, new = rules.policy(previous), rules.policy(config)
    if (not old or not new or old['staging']['enabled'] == new['staging']['enabled']
            or {k: v for k, v in old.items() if k != 'staging'} != {k: v for k, v in new.items() if k != 'staging'}
            or old['staging']['branch'] != new['staging']['branch']):
        raise ValueError('Only an explicit staging toggle with unchanged delivery target, completion, checks and branches is supported')
    ignored = {'delivery_policy', 'workflow', 'historical_completion'}
    if ({k: v for k, v in previous.items() if k not in ignored} != {k: v for k, v in config.items() if k not in ignored}
            or [r for r in workflow.stages(previous) if r['phase'] != 'stage']
            != [r for r in workflow.stages(config) if r['phase'] != 'stage']
            or not rules.batch_mode(previous) or not rules.batch_mode(config)):
        raise ValueError('Policy migration must preserve project identities, execution policy and every non-Stage setting')
    original, candidate = previous.get('historical_completion'), config.get('historical_completion')
    if bool(original) != bool(candidate) or original and (
            {k: v for k, v in original.items() if k != 'policy'} != {k: v for k, v in candidate.items() if k != 'policy'}
            or original['policy'] != rules.fingerprint(previous) or candidate['policy'] != rules.fingerprint(config)):
        raise ValueError('Historical reconciliation must preserve the exact existing allowlist and provenance, changing only its policy')


def migrate(api, config, store, args):
    previous = load_config(args.previous_config)
    compatible(previous, config)
    revision = args.previous_revision
    if not rules.SHA.fullmatch(revision):
        raise ValueError('Supply the immutable --previous-revision of the inspected original config')
    original = api.request(api.root + '/contents/tracker/config.json?ref=' + revision)
    if json.loads(rules.file_bytes(api.request, api.root, original)) != previous:
        raise ValueError('Previous config differs from its official immutable repository revision')
    current = api.request(api.root + '/git/ref/heads/' + quote(config['project']['base_branch'], safe=''))['object']['sha']
    if api.request(api.root + '/compare/' + revision + '...' + current).get('status') not in ('ahead', 'identical'):
        raise ValueError('Previous config revision must be included in current main')
    # Read before all remaining proofs; the final CAS cannot erase a new owner.
    state, sha = store.read(optional=True)
    source_api, reads = api, {}
    def snapshot_request(path):
        if path not in reads:
            reads[path] = source_api.request(path)
        return copy.deepcopy(reads[path])
    api = SimpleNamespace(root=source_api.root, repository=source_api.repository,
                          request=snapshot_request, issues=source_api.issues)
    text = maintenance.report(args)
    old_policy, new_policy = rules.fingerprint(previous), rules.fingerprint(config)
    migrations = state.get('delivery_workflow', {}).get('policy_migrations', [])
    section = state.get('execution') or {}
    if (section.get('delivery_policy') == new_policy and migrations
            and migrations[-1].get('from_policy') == old_policy
            and migrations[-1].get('to_policy') == new_policy
            and migrations[-1].get('previous_revision') == revision):
        rules.execution_state(state, config)
        return {'applied': False, 'already_applied': True, 'from_policy': old_policy, 'to_policy': new_policy}
    rules.execution_state(state, previous)
    if args.apply:
        maintenance.owned(state, args)
        published = api.request(api.root + '/contents/tracker/config.json?ref=' + current)
        if json.loads(rules.file_bytes(api.request, api.root, published)) != config:
            raise ValueError('Apply requires the exact reviewed candidate config already published on current main')
    if maintenance.busy(state):
        raise ValueError('Drain all Workers, Reviewers, pending operations, intake, integration and unpromoted Stage before changing policy')
    if rules.policy(previous)['staging']['enabled']:
        stage_sha = api.request(api.root + '/git/ref/heads/' + quote(rules.policy(previous)['staging']['branch'], safe=''))['object']['sha']
        if (rules.tree(api.request, api.root, stage_sha) != rules.tree(api.request, api.root, current)
                and not ('process_instructions' in previous and rules.process_module().stage_base_compatible(
                    api.request, previous, stage_sha, current, state))):
            raise ValueError('Reconcile actual unpromoted Stage content before changing policy, including interrupted receipts')
    issues = api.issues()
    by_number = {i['number']: i for i in issues if 'pull_request' not in i and 'tracker:control' not in names(i)}
    queued = set(section['review_queue'])
    approved = {int(n) for n, r in section['tasks'].items() if r.get('state') == 'approved'}
    actual_queue, actual_approved, retained_untracked_closed = set(), set(), []
    for item in by_number.values():
        labels = names(item)
        if 'flag:archived' in labels or item.get('state_reason') == 'not_planned':
            continue
        phases = [workflow.phase(previous, x[7:]) for x in labels if x.startswith('status:')]
        if not phases and closed_untracked(item, previous, state):
            retained_untracked_closed.append(dict(issue=item['number'], scope=rules.accepted_scope_digest(item),
                reason='Closed completed untracked Issue retained unchanged without a workflow status or new completion'))
            continue
        if any(p in ('in_progress', 'stage') for p in phases) or len(phases) != 1:
            raise ValueError('Resolve live In Progress/Stage tasks and transitional statuses before policy migration')
        if phases == ['review']: actual_queue.add(item['number'])
        if phases == ['approved']: actual_approved.add(item['number'])
    if len(queued) != len(section['review_queue']) or queued != actual_queue or approved != actual_approved:
        raise ValueError('Current Review/Approved Issues must exactly match retained durable queues')
    if any(section['approvals'].get(str(n), {}).get('issue') != n for n in approved):
        raise ValueError('Every preserved Approved task needs its original durable approval for supported author return')
    for n in queued:
        record = section['tasks'].get(str(n), {})
        handoff = record.get('handoff', {})
        if record.get('state') != 'queued' or not handoff or record.get('pr') != handoff.get('pr'):
            raise ValueError('Preserved Review requires its original durable Worker handoff')
        pr = api.request(api.root + f'/pulls/{record["pr"]}')
        implementer = {'actor': handoff.get('actor'), 'session': handoff.get('session')}
        if (pr.get('merged') or pr.get('draft') or pr['head']['ref'] != handoff.get('branch')
                or pr['head'].get('repo', {}).get('full_name', '').lower() != api.repository.lower()
                or pr_checks.check(api.request, previous, record['pr'])['issues'] != [n]
                or handoff.get('issue') != n or record.get('worker') != implementer['actor']
                or implementer not in record.get('implementers', [])
                or section['actors'].get(implementer['actor']) != {'session': implementer['session'], 'role': 'Worker'}
                or rules.route(previous, pr, api.request) not in ('approval', 'process')):
            raise ValueError('Preserved Review needs its original unmerged source and recorded Worker')
    receipts = state.get('delivery_workflow', {}).get('tasks', {})
    carried, retained, retained_legacy_pending, verified_sources = [], [], [], {}
    for number, receipt in receipts.items():
        item = by_number.get(int(number))
        projected = rules.summary(receipt)
        if (not item or {x for x in names(item) if x.startswith('status:')} != {'status:' + workflow.target(previous, 'merged')}
                or 'flag:archived' in names(item) or 'flag:blocked' in names(item)
                or item.get('state_reason') == 'not_planned' or not projected.get('admitted')
                or projected.get('policy') != old_policy
                or not rules.scope_matches(item, projected.get('reconciled_scope', rules.task_scope(item, previous)), previous)):
            retained.append(int(number))
            continue
        if legacy_pending(api, previous, state, int(number), receipt):
            retained.append(int(number))
            retained_legacy_pending.append(dict(issue=int(number), receipt_sha256=rules.receipt_digest(receipt),
                sources=copy.deepcopy(receipt['sources']),
                reason='Pre-batch pending promotion retained unchanged under its original policy; no current delivery authority'))
            continue
        for source in receipt.get('sources', []):
            if source['pr'] not in verified_sources:
                verified_sources[source['pr']] = (
                    pr_checks.check(api.request, previous, source['pr'], allow_transition=True, admission=True),
                    api.request(api.root + f'/pulls/{source["pr"]}'))
            checked, pr = verified_sources[source['pr']]
            if (not pr.get('merged') or pr['base']['ref'] != config['project']['base_branch']
                    or int(number) not in checked['issues'] or pr['merge_commit_sha'] != source['merge_sha']
                    or rules.pr_tree(api.request, api.root, pr) != source.get('tree_sha')
                    or api.request(api.root + '/compare/' + source['merge_sha'] + '...' + current).get('status') not in ('ahead', 'identical')):
                raise ValueError('Carry-forward needs exact original admitted sources still included in main')
        row = dict(from_policy=old_policy, to_policy=new_policy, receipt_sha256=rules.receipt_digest(receipt),
                   scope=rules.task_scope(item, config), sources=copy.deepcopy(receipt.get('sources', [])),
                   previous_revision=revision, report=text, recorded_at=now())
        receipt.setdefault('policy_reconciliations', []).append(row)
        carried.append(int(number))
    carried_requests = []
    for batch in section.get('batches', {}).values():
        request = batch.get('delivery_request', {})
        if (batch.get('state') != 'merged' or request.get('state') != 'requested'
                or rules.reconciled_request_policy(request, batch) != old_policy):
            continue
        if (request.get('batch_id') != batch['id'] or request.get('issues') != batch['issues']
                or request.get('target') != rules.policy(previous)['delivery_target']
                or not set(batch['issues']) <= set(carried)
                or any(set(batch['main_prs']) != {s.get('pr') for s in receipts[str(n)].get('sources', [])}
                       for n in batch['issues'])):
            raise ValueError('Existing authorized delivery needs its complete exact carried main batch before policy reconciliation')
        request.setdefault('policy_reconciliations', []).append(dict(from_policy=old_policy, to_policy=new_policy,
            request_sha256=rules.receipt_digest(request), batch_id=batch['id'], issues=batch['issues'][:],
            target=request['target'], main_prs=batch['main_prs'][:], source_heads=[m['head_sha'] for m in batch['members']],
            previous_revision=revision, report=text, recorded_at=now()))
        carried_requests.append(batch['id'])
    audit = dict(from_policy=old_policy, to_policy=new_policy, previous_revision=revision, main_sha=current,
                 report=text, recorded_at=now(), carried_tasks=sorted(carried), retained_old_tasks=sorted(retained),
                 preserved_review_queue=section['review_queue'][:], stale_approved=sorted(approved),
                 carried_delivery_requests=carried_requests,
                 retained_legacy_pending=sorted(retained_legacy_pending, key=lambda row: row['issue']),
                 retained_untracked_closed=sorted(retained_untracked_closed, key=lambda row: row['issue']),
                 historical_tasks=sorted(int(n) for n in (previous.get('historical_completion') or {}).get('tasks', {})))
    state.setdefault('delivery_workflow', {}).setdefault('policy_migrations', []).append(audit)
    section['delivery_policy'] = new_policy
    section['history'].append(dict(event='delivery-policy-migrated', **copy.deepcopy(audit)))
    rules.execution_state(state, config)
    if args.apply:
        if source_api.request(api.root + '/git/ref/heads/' + quote(config['project']['base_branch'], safe=''))['object']['sha'] != current:
            raise ValueError('Main changed during policy audit; inspect a fresh preview before applying')
        store.write(state, sha)
    return dict(applied=args.apply, **audit,
                instruction='Preserve maintenance until compatible config/writers/service are aligned. Old Approved proof needs author return and fresh independent review; pending delivery remains pending.')
