"""Explicit, resumable workflow evidence; never performs a Git merge or deploy."""
import copy
import json
from urllib.parse import quote
from . import delivery_policy as rules, process_instructions as process, pr_checks, workflow
from .model import names
from .sync import now


def require(config):
    if not rules.policy(config) and not process.policy(config):
        raise ValueError('This project has not adopted the delivery policy')


def evidence(path, kind):
    value = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(value, dict) or value.get('kind') != kind:
        raise ValueError('Expected ' + kind + ' evidence')
    if not isinstance(value.get('report'), str) or not value['report'].strip():
        raise ValueError('Evidence needs the actual report or a durable report reference')
    return value


def record_review(api, config, store, number, document, apply=False):
    require(config)
    # Read before validation: a concurrent release/takeover must fail the final CAS.
    state, sha = store.read(optional=True)
    lane = rules.review_lane(state.get('execution'), pr=number) or {}
    if lane.get('route') == 'compatibility':
        raise ValueError('Use task-context review-record; do not overwrite the original source review')
    recovery = bool(rules.batch_mode(config) and lane.get('approval_recovery') and lane.get('pr') == number
                    and lane.get('id') == document.get('execution_lane') and lane.get('session') == document.get('review_session'))
    linked = pr_checks.check(api.request, config, number, approval_recovery=recovery)
    pr = api.request(api.root + f'/pulls/{number}')
    direction = rules.route(config, pr, api.request)
    process_proof = process.classify(api.request, config, pr) if direction == 'process' else None
    legacy_process = bool(process_proof and not rules.execution_policy(config))
    previous = state.get('delivery_workflow', {}).get('reviews', {}).get(str(number), {})
    legacy_recovery = bool(legacy_process and pr.get('merged')
                           and previous.get('process_proof') == process_proof
                           and previous.get('implementer') == document.get('implementer')
                           and not state.get('delivery_workflow', {}).get('tasks', {}).get(str(linked['issues'][0]), {}).get('completed_at'))
    if legacy_process and (state.get('active') or {}).get('issue') != linked['issues'][0]:
        raise ValueError('Process review requires the actual legacy task slot')
    merged_recovery = bool(pr.get('merged') and direction != 'promotion'
                           and (rules.execution_policy(config) or legacy_recovery))
    if (pr.get('merged') or pr.get('state') != 'open' or pr.get('draft')) and not merged_recovery:
        raise ValueError('Review evidence requires an open ready PR')
    if rules.route(config, pr, api.request) == 'promotion':
        raise ValueError('Promotion reuses the verified stage content; review the source PR')
    if (document.get('verdict') != 'approved' or not document.get('reviewer') or not document.get('implementer')
            or document['reviewer'] == document['implementer']):
        raise ValueError('Approval requires distinct reviewer and implementer identities')
    review_base = (process_proof['base_sha'] if process_proof else rules.merge_base(api.request, api.root, pr)
                   if direction == 'batch' and pr.get('merged') else pr['base']['sha'])
    for key, actual in (('head_sha', pr['head']['sha']), ('base_sha', review_base),
                        ('tree_sha', rules.pr_tree(api.request, api.root, pr))):
        if document.get(key) != actual:
            raise ValueError('Review does not match current ' + key)
    main_ref = api.request(api.root + '/git/ref/heads/' + quote(config['project']['base_branch'], safe=''))
    if direction == 'process':
        section = rules.execution_state(state, config)
        active = state.get('delivery_workflow', {}).get('stage', {})
        current = main_ref['object']['sha']
        baseline_current = process_proof['base_sha'] == current
        if merged_recovery and process_proof:
            baseline_current = api.request(api.root + '/compare/' + pr['merge_commit_sha'] + '...' + current).get('status') in ('ahead', 'identical')
        if (not baseline_current or active and active.get('state') != 'promoted'
                or section and (section.get('integration') or section.get('intake') and section['intake'].get('state') == 'running')):
            raise ValueError('Process review requires current main and idle stage/integration')
    if direction == 'stage':
        ancestry = api.request(api.root + '/compare/' + main_ref['object']['sha'] + '...' + pr['head']['sha'])
        if ancestry.get('status') not in ('ahead', 'identical'):
            # A stopped reviewer can be replaced after promotion merged but
            # before completion was recorded. Review the actual integrated tree,
            # not a fictitious rebase of an already merged source branch.
            integrated = (api.request(api.root + '/compare/' + pr['merge_commit_sha'] + '...' + main_ref['object']['sha'])
                          if staged_recovery_source(config, pr) else {})
            if integrated.get('status') not in ('ahead', 'identical'):
                raise ValueError('Reviewed working branch must include current main')
    row = dict(document, main_sha=main_ref['object']['sha'], policy=rules.fingerprint(config), issues=linked['issues'], recorded_at=now())
    if process_proof:
        row.update(process_policy=process.fingerprint(config), process_proof=process_proof,
                   issue_scopes={str(n): process.scope(api.issue(n), config) for n in linked['issues']})
    if rules.batch_mode(config) and not process_proof:
        from . import batch_policy
        if rules.route(config, pr, api.request) == 'approval':
            ancestry = api.request(api.root + '/compare/' + main_ref['object']['sha'] + '...' + pr['head']['sha'])
            if (rules.tree(api.request, api.root, pr['base']['sha']) != rules.tree(api.request, api.root, main_ref['object']['sha'])
                    or ancestry.get('status') not in ('ahead', 'identical')):
                raise ValueError('Source review must use the current main baseline')
        else:
            batch = rules.execution_state(state, config).get('integration')
            if not batch:
                raise ValueError('No integration owner')
            batch_policy.validate_candidate(api.request, config, pr, linked['issues'], batch, state)
        row['issue_scopes'] = {str(n): batch_policy.scope(api.issue(n), config) for n in linked['issues']}
    from .execution import review_evidence
    row.update(review_evidence(config, state, number, document, linked['issues']))
    if apply:
        state.setdefault('delivery_workflow', {}).setdefault('reviews', {})[str(number)] = row
        store.write(state, sha)
    return {'applied': apply, 'review': row}


def staged_recovery_source(config, pr):
    return bool(rules.execution_policy(config) and pr.get('merged') and rules.route(config, pr) == 'stage')


def stage(api, config, store, number, apply=False):
    require(config)
    if not rules.policy(config) or not rules.policy(config)['staging']['enabled']:
        raise ValueError('Stage requires an adopted delivery policy')
    # Pin the write version before admission; a newer owner's write must make CAS fail.
    state, sha = store.read(optional=True)
    linked = pr_checks.check(api.request, config, number, allow_transition=True, admission=True)
    pr = api.request(api.root + f'/pulls/{number}')
    if not pr.get('merged') or rules.route(config, pr, api.request) != 'stage':
        raise ValueError('Stage entry requires a reviewed PR actually merged into stage')
    content = rules.pr_tree(api.request, api.root, pr)
    stage_ref = api.request(api.root + '/git/ref/heads/' + quote(rules.policy(config)['staging']['branch'], safe=''))
    if rules.tree(api.request, api.root, stage_ref['object']['sha']) != content:
        raise ValueError('Stage changed after this PR; reconcile the candidate before recording')
    section = state.setdefault('delivery_workflow', {})
    active = section.get('stage', {})
    main_ref = api.request(api.root + '/git/ref/heads/' + quote(config['project']['base_branch'], safe=''))
    if main_ref['object']['sha'] != linked['admission']['main_sha']:
        raise ValueError('Main changed while admitting stage; repeat review and admission')
    main_tree = rules.tree(api.request, api.root, main_ref['object']['sha'])
    row = {'pr': number, 'issues': linked['issues'], 'tree_sha': content, 'source_sha': pr['merge_commit_sha'],
           'main_tree': main_tree, 'policy': rules.fingerprint(config), 'state': 'testing', 'recorded_at': now()}
    if rules.batch_mode(config):
        row['batch_id'] = linked['admission']['batch_id']
        batch = rules.execution_state(state, config)['integration']
        if not batch or batch['id'] != row['batch_id']:
            raise ValueError('Integration ownership changed while admitting stage')
        batch.update(entered_stage=True, state='stage')
        for n in batch['issues']:
            state['execution']['tasks'][str(n)]['state'] = 'stage'
    # Retrying a partially applied status transition must not erase passing evidence.
    if all(active.get(k) == row[k] for k in ('pr', 'issues', 'tree_sha', 'main_tree', 'policy')):
        row = active
    if apply:
        section['stage'] = row
        store.write(state, sha)
        for n in linked['issues']:
            labels = names(api.issue(n))
            api.labels(n, {'status:' + workflow.target(config, 'stage')}, {x for x in labels if x.startswith('status:')})
    return {'applied': apply, 'candidate': row}


def verify_stage(api, config, store, document, apply=False):
    require(config)
    if not rules.policy(config) or not rules.policy(config)['staging']['enabled']:
        raise ValueError('Stage requires an adopted delivery policy')
    state, sha = store.read(optional=True)
    row = state.get('delivery_workflow', {}).get('stage', {})
    if row.get('state') not in ('testing', 'failed', 'passed') or row.get('policy') != rules.fingerprint(config):
        raise ValueError('No active stage candidate')
    ref = api.request(api.root + '/git/ref/heads/' + quote(rules.policy(config)['staging']['branch'], safe=''))
    main_ref = api.request(api.root + '/git/ref/heads/' + quote(config['project']['base_branch'], safe=''))
    if (document.get('tree_sha') != row['tree_sha'] or document.get('source_sha') != row['source_sha']
            or rules.tree(api.request, api.root, ref['object']['sha']) != row['tree_sha']
            or rules.tree(api.request, api.root, main_ref['object']['sha']) != row['main_tree']):
        raise ValueError('Stage verification is stale for the current candidate or main')
    check_result(document, rules.policy(config)['staging']['target'])
    result = dict(row, state=document['result'], verification=document, verified_at=now())
    if apply:
        state['delivery_workflow']['stage'] = result
        store.write(state, sha)
    return {'applied': apply, 'candidate': result}


def record_merge(api, config, store, plan, prs):
    if not rules.policy(config) and not process.policy(config):
        return
    state, sha = store.read(optional=True)
    section = state.setdefault('delivery_workflow', {})
    tasks = section.setdefault('tasks', {})
    verified_prs, admissions = {}, {}
    for number in prs:
        checked = pr_checks.check(api.request, config, number, allow_transition=True, admission=True)
        admissions[number] = checked['admission']
        pr = api.request(api.root + f'/pulls/{number}')
        if not pr.get('merged') or pr['base']['ref'] != config['project']['base_branch']:
            raise ValueError('Completion requires a real main merge')
        verified_prs[number] = pr
    for item in plan:
        # Multiple PRs may jointly implement one task. Track all of their identities.
        sources = [{'pr': n, 'merge_sha': verified_prs[n]['merge_commit_sha'],
                    'tree_sha': rules.pr_tree(api.request, api.root, verified_prs[n])} for n in item['prs']]
        row = {'policy': rules.fingerprint(config), 'sources': sources, 'state': 'pending', 'recorded_at': now()}
        process_sources = [n for n in item['prs'] if admissions[n] and admissions[n]['route'] == 'process']
        if process_sources:
            if len(item['prs']) != 1:
                raise ValueError('Process completion cannot combine ordinary or multiple source PRs')
            row.update(state='verified', process=True, verification=admissions[process_sources[0]], verified_at=now())
        old = tasks.get(str(item['number']), {})
        if old.get('sources') == sources and old.get('policy') == row['policy']:
            row = old
        elif old:
            row['history'] = [*old.get('history', []), {k: v for k, v in old.items() if k != 'history'}]
        tasks[str(item['number'])] = row
    candidate = section.get('stage', {})
    for number, pr in verified_prs.items():
        if rules.route(config, pr, api.request) == 'batch':
            section.setdefault('main_batches', {})[str(number)] = dict(admissions[number], pr=number,
                issues=pr_checks.linked_numbers(pr.get('body'), config), source_sha=pr['merge_commit_sha'], recorded_at=now())
            continue
        if rules.route(config, pr, api.request) != 'promotion':
            continue
        archive = section.setdefault('promotions', {})
        if str(number) not in archive:
            archive[str(number)] = copy.deepcopy(candidate)
        receipt = archive[str(number)]
        identity = ('pr', 'issues', 'tree_sha', 'source_sha', 'main_tree', 'policy')
        if candidate and all(candidate.get(k) == receipt.get(k) for k in identity):
            candidate['state'] = 'promoted'
    store.write(state, sha)


def check_result(document, target):
    checks = document.get('checks')
    if (document.get('result') not in ('passed', 'failed') or document.get('target') != target
            or not isinstance(checks, list) or not checks
            or any(not isinstance(x, str) or not x.strip() for x in checks)
            or not isinstance(document.get('report'), str) or not document['report'].strip()):
        raise ValueError('Result needs passed/failed, the configured target, actual checks and report')


def record_delivery(api, config, store, numbers, document, apply=False):
    require(config)
    state, sha = store.read(optional=True)
    tasks = state.get('delivery_workflow', {}).get('tasks', {})
    if any(tasks.get(str(n), {}).get('process') for n in numbers):
        raise ValueError('Instruction-only completion records reviewed merge proof, not package delivery')
    if not rules.policy(config):
        raise ValueError('No configured package/production delivery target')
    check_result(document, rules.policy(config)['delivery_target'])
    supplied = document.get('merge_shas')
    if not isinstance(supplied, list) or not supplied or any(not isinstance(x, str) or not rules.SHA.fullmatch(x) for x in supplied):
        raise ValueError('Delivery must identify the installed merge revisions')
    for number in numbers:
        item = api.issue(number)
        stages = [workflow.phase(config, x[7:]) for x in names(item) if x.startswith('status:')]
        row = tasks.get(str(number), {})
        expected = {s['merge_sha'] for s in row.get('sources', [])}
        if stages != ['merged'] or 'flag:archived' in names(item) or not expected or not expected <= set(supplied):
            raise ValueError('Delivery does not cover this merged task')
        effective, scope = rules.reconciled_policy(row)
        if effective != rules.fingerprint(config) or scope and not rules.scope_matches(item, scope, config):
            raise ValueError('Task policy changed; reconcile its completion evidence')
        for source in row['sources']:
            comparison = api.request(api.root + '/compare/' + source['merge_sha'] + '...' + quote(config['project']['base_branch'], safe=''))
            if comparison.get('status') not in ('ahead', 'identical'):
                raise ValueError('Delivered source is no longer included in main')
    if apply:
        for number in numbers:
            row = tasks[str(number)]
            row.setdefault('history', []).append({k: copy.deepcopy(v) for k, v in row.items() if k != 'history'})
            row.pop('policy_reconciliations', None)
            row.update(policy=rules.fingerprint(config), state='verified' if document['result'] == 'passed' else 'failed',
                       verification=document, verified_at=now())
        store.write(state, sha)
    return {'applied': apply, 'issues': numbers, 'result': document['result']}


def non_code(config, store, number, report):
    if rules.policy(config):
        state, sha = store.read(optional=True)
        state.setdefault('delivery_workflow', {}).setdefault('tasks', {})[str(number)] = {
            'state': 'verified', 'non_code': True, 'report': report,
            'policy': rules.fingerprint(config), 'recorded_at': now()}
        store.write(state, sha)
