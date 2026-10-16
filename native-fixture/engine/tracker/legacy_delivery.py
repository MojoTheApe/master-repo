"""Bounded retrospective delivery for original retained pre-batch receipts only.

This is an explicit operator, not exported admission or a policy migration. The
owner and independent reviewer attest complete business scope; the operator
corroborates immutable historical sources and actual native package acceptance.
"""
import copy
from datetime import datetime
import json
import re
from types import SimpleNamespace
from urllib.parse import quote
from . import delivery, delivery_policy as rules, delivery_receipt as native
from . import identifiers, merge, policy_migration, pr_checks, workflow
from .model import names
from .sync import now


def text(value):
    return isinstance(value, str) and bool(value.strip())


def require(condition, message):
    if not condition:
        raise ValueError(message)


def included(api, source, target):
    require(api.request(api.root + '/compare/' + source + '...' + target).get('status')
            in ('ahead', 'identical'), 'Historical source is absent from current main or the installed release')


def config_at(api, revision):
    row = api.request(api.root + '/contents/tracker/config.json?ref=' + quote(revision, safe=''))
    value = json.loads(rules.file_bytes(api.request, api.root, row))
    return value


def report_in_log(log, report):
    """Match real pretty-printed native stdout, never an uploaded JSON artifact."""
    lines = [re.sub(r'^.*?\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d+)?Z\s?', '', line)
             for line in log.splitlines()]
    output = '\n'.join(lines)
    decoder = json.JSONDecoder()
    matches = 0
    for start in re.finditer(r'(?m)^\s*\{', output):
        try:
            actual, _ = decoder.raw_decode(output[start.start():].lstrip())
        except ValueError:
            continue
        matches += actual == report
    require(matches == 1, 'Installed package report must match exactly one real native job stdout report')


def release_identity(value):
    return {k: value.get(k) for k in ('id', 'draft', 'prerelease', 'published_at', 'tag_name', 'html_url')} | {
        'assets': sorted(({k: a.get(k) for k in ('id', 'name', 'size', 'digest', 'state')}
                          for a in value.get('assets', [])), key=lambda a: a['id'])}


def package(api, config, state, document):
    proof = document['native']
    request, receipt, report = proof['request'], proof['receipt'], proof['report']
    repo = config['project']['repository']
    require(request.get('eligible') is True and request.get('repository') == repo
            and request.get('policy') == rules.fingerprint(config)
            and request.get('target') == rules.policy(config)['delivery_target'],
            'Original native request must retain the current exact project policy and target')
    batch = state.get('execution', {}).get('batches', {}).get(request.get('batch_id'), {})
    authorization = native.authorization(config, batch)
    require(authorization and native.digest(authorization) == request.get('authorization_sha256')
            and batch.get('state') == 'merged' and batch.get('issues') == request.get('issues')
            and request.get('main_pr') in batch.get('main_prs', [])
            and request.get('workflow') == authorization['workflow'] and request.get('job') == authorization['job']
            and request.get('requested_at') == authorization['requested_at'],
            'Original archived producer authorization/task scope changed')
    require(isinstance(request.get('issues'), list) and request['issues']
            and all(type(n) is int and n > 0 for n in request['issues'])
            and len(set(request['issues'])) == len(request['issues']), 'Invalid original producer task set')
    require(all(isinstance(request.get(k), str) and rules.SHA.fullmatch(request[k])
                for k in ('merge_sha', 'tree_sha')), 'Invalid installed source identity')
    pr = api.request(api.root + '/pulls/' + str(request['main_pr']))
    require(pr.get('merged') is True and pr['base']['ref'] == config['project']['base_branch']
            and pr['base']['repo']['full_name'].lower() == repo.lower()
            and pr.get('merge_commit_sha') == request['merge_sha']
            and pr_checks.linked_numbers(pr.get('body'), config) == request['issues']
            and re.findall(r'^Tracker batch:\s*([a-f0-9]{32})\s*$', pr.get('body') or '', re.M) == [batch['id']]
            and rules.tree(api.request, api.root, request['merge_sha']) == request['tree_sha'],
            'Original native producer is not its exact official admitted main batch')
    expected_request = dict(eligible=True, schema_version=1, repository=repo, batch_id=batch['id'],
        issues=batch['issues'], main_pr=pr['number'], merge_sha=pr['merge_commit_sha'],
        tree_sha=rules.tree(api.request, api.root, pr['merge_commit_sha']), policy=rules.fingerprint(config),
        target=authorization['target'], workflow=authorization['workflow'], job=authorization['job'],
        requested_at=authorization['requested_at'], authorization_sha256=native.digest(authorization), ci_run=request['ci_run'])
    require(request == expected_request and type(request.get('schema_version')) is int
            and type(request.get('main_pr')) is int, 'Original native request document was changed or broadened')
    native.task_context(api.request, repo, config, state, batch, request['merge_sha'])
    ci = native.official_run(api.request, repo, request['ci_run'], request['merge_sha'])
    require(ci.get('status') == 'completed' and ci.get('conclusion') == 'success', 'Original main CI did not pass')
    delivery.check_result(receipt, request['target'])
    require(receipt.get('kind') == 'delivery-verification' and receipt['result'] == 'passed'
            and receipt.get('merge_shas') == [request['merge_sha']], 'Native receipt does not verify the installed source')
    run = native.official_run(api.request, repo, proof['run'], request['merge_sha'])
    require(run.get('status') == 'completed' and run.get('conclusion') == 'success',
            'Retrospective proof requires a successful completed native workflow run')
    native.verified_native(api.request, request, receipt, proof['run'], proof['job'])
    report_in_log(api.request(api.root + '/actions/jobs/' + str(proof['job']) + '/logs'), report)
    published = report.get('published', {})
    current = published.get('current', {})
    signature = published.get('signature', {})
    release_proof = receipt.get('release', {})
    require(report.get('result') == 'passed' and report.get('source_sha') == request['merge_sha']
            and report.get('tree_sha') == request['tree_sha'] and report.get('run_id') == str(proof['run'])
            and current.get('commit') == request['merge_sha'] and current.get('tag') == release_proof.get('tag')
            and published.get('repository') == release_proof.get('repository')
            and signature.get('status') == 'valid' and re.fullmatch(r'[a-f0-9]{16}', signature.get('key_id', ''))
            and report.get('update', {}).get('result') == 'updated'
            and report.get('recovery', {}).get('result') == 'rolled_back'
            and isinstance(report.get('checks'), list) and len(report['checks']) >= 5
            and all(text(check) and check in receipt['checks'] for check in report['checks']),
            'Native signed published install/update/restart/recovery acceptance is incomplete')
    require(re.fullmatch(r'[\w.-]+/[\w.-]+', release_proof.get('repository', ''))
            and text(release_proof.get('tag')), 'Missing official release identity')
    release = api.request('repos/' + release_proof['repository'] + '/releases/tags/' + quote(release_proof['tag'], safe=''))
    supplied = document['release']
    require(release.get('id') == supplied.get('id') and release.get('draft') is False
            and release.get('prerelease') is False and text(release.get('published_at'))
            and release.get('tag_name') == current['tag'] and release.get('html_url') == published.get('release_url'),
            'Published stable release identity changed')
    installer = current.get('installer', {})
    expected = {installer.get('name'): 'sha256:' + release_proof.get('installer_sha256', ''),
                'release.json': 'sha256:' + published.get('manifest_sha256', '')}
    require(len(expected) == 2 and installer.get('sha256') == release_proof.get('installer_sha256')
            and all(re.fullmatch(r'sha256:[a-f0-9]{64}', value) for value in expected.values()),
            'Native report lacks signed manifest and installer content digests')
    assets = release.get('assets', [])
    selected = supplied.get('assets')
    require(isinstance(selected, list) and len(selected) == 3
            and {a.get('name') for a in selected} == set(expected) | {'release.json.sig'},
            'Supply exact installer, signed manifest and signature asset identities')
    for asset in selected:
        matches = [a for a in assets if a.get('name') == asset['name']]
        require(len(matches) == 1 and all(matches[0].get(k) == asset.get(k) for k in ('id', 'name', 'size', 'digest'))
                and matches[0].get('state') == 'uploaded' and type(asset.get('id')) is int and asset['id'] > 0
                and type(asset.get('size')) is int and asset['size'] > 0
                and re.fullmatch(r'sha256:[a-f0-9]{64}', asset.get('digest', '')),
                'Published release asset identity/content changed')
        if asset['name'] in expected:
            require(asset['digest'] == expected[asset['name']], 'Release content differs from actual native acceptance')
        if asset['name'] == installer['name']:
            require(asset['size'] == installer.get('size'), 'Installed package size changed')
    return request, receipt


def restored_archive(state, number, item, api):
    """Corroborate only the retained empty stub left by normal Issue restore."""
    record = state.get('execution', {}).get('tasks', {}).get(str(number), {})
    if (record != {'implementers': [], 'state': 'archived'} or not item or not api
            or item.get('number') != number or 'flag:archived' in names(item)
            or item.get('state_reason') == 'not_planned'):
        return False
    history = [r for r in state['execution'].get('history', [])
               if r.get('event') == 'archived' and r.get('issue') == number]
    if not history or not text(history[-1].get('reason')):
        return False
    try:
        archived_at = datetime.fromisoformat(history[-1]['at'].replace('Z', '+00:00'))
        if archived_at.utcoffset() is None:
            return False
    except (KeyError, ValueError, TypeError):
        return False
    events = []
    for page in range(1, 101):
        rows = api.request(api.root + f'/issues/{number}/events?per_page=100&page={page}')
        require(isinstance(rows, list), 'Original archive restoration event history is unavailable')
        events.extend(r for r in rows if r.get('event') in ('labeled', 'unlabeled')
                      and r.get('label', {}).get('name') == 'flag:archived')
        if len(rows) < 100:
            break
    else:
        raise ValueError('Archive restoration event history exceeds proof bound')
    labeled = [event for event in events[:-1] if event.get('event') == 'labeled']
    if not events or events[-1].get('event') != 'unlabeled' or not labeled:
        return False
    try:
        labeled_at = datetime.fromisoformat(labeled[-1]['created_at'].replace('Z', '+00:00'))
        restored_at = datetime.fromisoformat(events[-1]['created_at'].replace('Z', '+00:00'))
        return (labeled_at.utcoffset() is not None and restored_at.utcoffset() is not None
                and labeled_at <= archived_at < restored_at)
    except (KeyError, ValueError, TypeError):
        return False


def inactive(state, number, item=None, api=None):
    """Selected old tasks must be idle; unrelated owners are deliberately allowed."""
    section = state.get('execution', {})
    require(section.get('tasks', {}).get(str(number), {}).get('state', 'merged') == 'merged'
            or restored_archive(state, number, item, api),
            'Selected historical task has unfinished execution work')
    require(str(number) not in section.get('claims', {}) and number not in section.get('review_queue', [])
            and str(number) not in section.get('approvals', {}),
            'Selected historical task has active ownership or queue membership')
    # queue.ordered_todo uses this only to sort tasks whose actual phase is Todo.
    # record() already requires the exact sole Merged label; a retained position
    # is not a live run/claim. Keep the full manual order unchanged.
    manual = state.get('todo_order', [])
    require(isinstance(manual, list) and all(type(n) is int and n > 0 for n in manual),
            'Unsupported historical Todo sort metadata')
    rows = [state.get('active'), state.get('run'), section.get('integration'), section.get('intake')]
    rows += rules.review_lanes(section)
    for intake in state.get('intakes', {}).values():
        require(isinstance(intake, dict), 'Unsupported historical creation journal')
        # work() permanently retains exactly this successful Issue-creation
        # journal. It is not a claim; actual task/claim/queue checks stay above.
        if (set(intake) == {'title', 'state', 'issue'} and intake['state'] == 'created'
                and type(intake['issue']) is int and intake['issue'] > 0 and text(intake['title'])):
            continue
        rows.append(intake)
    for row in rows:
        if not row:
            continue
        require(isinstance(row, dict), 'Unsupported task ownership shape')
        if row.get('state') in ('complete', 'completed', 'merged', 'cancelled'):
            continue
        members = row.get('members', [])
        require(row.get('issue') != number and number not in row.get('issues', [])
                and number not in row.get('tasks', [])
                and not any(isinstance(m, dict) and m.get('issue') == number for m in members),
                'Selected historical task is owned by active work')


def record(api, config, store, document, apply=False):
    require(document.get('kind') == 'legacy-delivery-reconciliation' and type(document.get('schema_version')) is int
            and document['schema_version'] == 1, 'Expected legacy-delivery-reconciliation schema 1')
    require(rules.batch_mode(config) and rules.policy(config)['completion'] == 'verified-stable-package',
            'This bounded operator requires an adopted stable-package batch project')
    repo = config['project']['repository']
    require(document.get('repository') == repo and document.get('policy') == rules.fingerprint(config)
            and document.get('config_sha256') == native.digest(config), 'Exact current project configuration/policy required')
    numbers = document.get('issues')
    require(isinstance(numbers, list) and 0 < len(numbers) <= 128
            and all(type(n) is int and n > 0 for n in numbers) and len(set(numbers)) == len(numbers),
            'Supply a bounded explicit unique Issue allowlist (maximum 128)')
    auth = document.get('authorization', {})
    require(auth.get('issues') == numbers and text(auth.get('approved_by')) and text(auth.get('report'))
            and text(document.get('report')) and text(document.get('implementer')),
            'Explicit new owner authorization and actual complete-scope report required')
    attestations = document.get('tasks', {})
    require(set(attestations) == {str(n) for n in numbers}, 'Attest exactly the selected tasks')
    state, sha = store.read(optional=False)
    rules.execution_state(state, config)
    current = api.request(api.root + '/git/ref/heads/' + quote(config['project']['base_branch'], safe=''))['object']['sha']
    require(config_at(api, current) == config, 'Use the exact official current consumer configuration')
    # Memoize one inspected snapshot. Final mutable Issue/config/release/native
    # proofs below bypass this cache; the CAS SHA predates the expensive audit.
    source_api, cache = api, {}
    def request(path):
        if path not in cache:
            cache[path] = (source_api.action_job_log(int(path.rsplit('/', 2)[-2]))
                           if path.endswith('/logs') else source_api.request(path))
        return copy.deepcopy(cache[path])
    api = SimpleNamespace(root=source_api.root, repository=repo, request=request)
    migrations = state.get('delivery_workflow', {}).get('policy_migrations', [])
    matches = [m for m in migrations if native.digest(m) == document.get('migration_sha256')]
    require(len(matches) == 1, 'Original genuine retained-legacy migration audit required')
    migration = matches[0]
    require(migration.get('to_policy') == rules.fingerprint(config) and text(migration.get('report'))
            and rules.SHA.fullmatch(migration.get('previous_revision', ''))
            and rules.SHA.fullmatch(migration.get('main_sha', '')), 'Stale or malformed migration provenance')
    previous = config_at(api, migration['previous_revision'])
    policy_migration.compatible(previous, config)
    require(migration.get('from_policy') == rules.fingerprint(previous), 'Original official policy provenance changed')
    included(api, migration['previous_revision'], current)
    included(api, migration['main_sha'], current)
    producer, original_verification = package(api, config, state, document)
    included(api, producer['merge_sha'], current)
    rows = state['delivery_workflow']['tasks']
    plan, already = [], []
    for number in numbers:
        item = source_api.issue(number)
        attestation = attestations[str(number)]
        require(attestation.get('id') == identifiers.task_id(item, config)
                and attestation.get('scope') == rules.task_scope(item)
                and attestation.get('accepted_scope') == rules.accepted_scope_digest(item)
                and text(attestation.get('reviewer')) and attestation['reviewer'] != document['implementer']
                and attestation.get('verdict') == 'complete' and text(attestation.get('report'))
                and isinstance(attestation.get('checks'), list) and attestation['checks']
                and all(text(c) for c in attestation['checks']), 'Independent full-scope attestation is missing or stale')
        labels = names(item)
        require({s for s in labels if s.startswith('status:')} == {'status:' + workflow.target(config, 'merged')}
                and not {'flag:blocked', 'flag:archived', 'tracker:control'} & labels
                and item.get('state_reason') != 'not_planned' and 'pull_request' not in item
                and not merge.unchecked_subtasks(item.get('body') or ''), 'Selected task has incomplete, blocked or archived work')
        require(str(number) not in (config.get('historical_completion') or {}).get('tasks', {}),
                'Historical completion exemptions cannot be extended or replaced by this operator')
        inactive(state, number, item, api)
        row = rows.get(str(number), {})
        recorded = row.get('legacy_delivery_reconciliation', {})
        if recorded:
            require(row.get('state') == 'verified' and row.get('policy') == rules.fingerprint(config)
                    and recorded.get('manifest_sha256') == native.digest(document)
                    and len(row.get('history', [])) == 1, 'Existing delivery differs; preserve its actual evidence')
            original = row['history'][0]
        else:
            original = row
        require(original.get('policy') == migration['from_policy']
                and rules.receipt_digest(original) == attestation.get('receipt_sha256')
                and policy_migration.legacy_pending(api, previous, state, number, original),
                'Only the exact original minimal retained pending receipt is eligible')
        retained = [r for r in migration.get('retained_legacy_pending', []) if r.get('issue') == number]
        require(len(retained) == 1 and retained[0].get('receipt_sha256') == rules.receipt_digest(original)
                and retained[0].get('sources') == original['sources'] and text(retained[0].get('reason')),
                'Original pending receipt does not match its genuine retention audit')
        for source in original['sources']:
            require(rules.tree(api.request, api.root, source['merge_sha']) == source['tree_sha'],
                    'Historical main merge/tree identity differs')
            included(api, source['merge_sha'], current)
            included(api, source['merge_sha'], producer['merge_sha'])
        verification = dict(kind='delivery-verification', result='passed', target=producer['target'],
                            merge_shas=list(dict.fromkeys(s['merge_sha'] for s in original['sources'])),
                            checks=attestation['checks'], report=attestation['report'])
        recovery = dict(manifest_sha256=native.digest(document), authorization=copy.deepcopy(auth),
                        scope=attestation['scope'], accepted_scope=attestation['accepted_scope'],
                        reviewer=attestation['reviewer'], implementer=document['implementer'], report=document['report'],
                        migration_sha256=document['migration_sha256'], native=dict(request=copy.deepcopy(producer), run=document['native']['run'], job=document['native']['job'],
                                    receipt_sha256=native.digest(original_verification),
                                    report_sha256=native.digest(document['native']['report'])),
                        release=copy.deepcopy(document['release']))
        if recorded:
            require(row.get('verification') == verification and recorded == recovery
                    and row.get('sources') == original['sources'], 'Existing verified evidence changed')
            already.append(number)
        else:
            plan.append((number, original, verification, recovery))
    # Re-read mutable Issue scope, main/config and release identity immediately
    # before the single CAS. Unrelated state writes conflict instead of being lost.
    for number in numbers:
        require(rules.accepted_scope_digest(source_api.issue(number)) == attestations[str(number)]['accepted_scope'],
                'Issue changed during audit; inspect a fresh preview')
    require(source_api.request(api.root + '/git/ref/heads/' + quote(config['project']['base_branch'], safe=''))['object']['sha'] == current
            and config_at(source_api, current) == config, 'Main/config changed during audit; inspect a fresh preview')
    release = original_verification['release']
    release_path = 'repos/' + release['repository'] + '/releases/tags/' + quote(release['tag'], safe='')
    require(release_identity(source_api.request(release_path)) == release_identity(cache[release_path]), 'Release changed during audit; inspect a fresh preview')
    # The source audit may cover many tasks. A native run can rerun without
    # changing the Tracker state SHA, so repeat the actual producer/job/attempt,
    # stdout and release proof through uncached transport immediately before CAS.
    def fresh_request(path):
        return (source_api.action_job_log(int(path.rsplit('/', 2)[-2]))
                if path.endswith('/logs') else source_api.request(path))
    fresh_api = SimpleNamespace(root=source_api.root, repository=repo, request=fresh_request)
    package(fresh_api, config, state, document)
    if apply and plan:
        at = now()
        for number, original, verification, recovery in plan:
            rows[str(number)] = dict(copy.deepcopy(original), policy=rules.fingerprint(config), state='verified',
                                     verification=verification, verified_at=at, history=[copy.deepcopy(original)],
                                     legacy_delivery_reconciliation=recovery)
        store.write(state, sha)
    return dict(applied=bool(apply and plan), issues=numbers, eligible=[p[0] for p in plan],
                already_recorded=already, result='passed', manifest_sha256=native.digest(document))
