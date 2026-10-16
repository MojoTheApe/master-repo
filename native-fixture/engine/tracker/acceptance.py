"""Explicit post-main checklist evidence, separate from unchanged task scope."""
import copy
import re
from urllib.parse import quote
from . import batch_policy, delivery_policy as rules, execution
from .sync import now


def criteria(body):
    """Return exact unchecked lines, excluding fenced examples, with stable indexes."""
    result, fence = [], None
    for index, line in enumerate((body or '').splitlines(), 1):
        stripped = line.lstrip()
        if stripped.startswith(('```', '~~~')):
            marker = stripped[:3]
            fence = None if fence == marker else marker if fence is None else fence
        elif fence is None and re.match(r'^\s*[-*+]\s+\[ \]\s+', line):
            result.append({'line': index, 'criterion': line})
    return result


def context(api, config, state, pr_number):
    if not rules.batch_mode(config):
        raise ValueError('Acceptance recovery requires an application batch')
    section = rules.execution_state(state, config)
    pr = api.request(api.root + f'/pulls/{pr_number}')
    if not pr.get('merged') or rules.route(config, pr, api.request) not in ('promotion', 'batch'):
        raise ValueError('Acceptance requires an actual admitted main promotion')
    batch_id = batch_policy.batch_id(pr)
    batch = section.get('integration')
    archived = section.get('batches', {}).get(batch_id)
    if not batch or batch.get('id') != batch_id:
        batch = archived if archived and archived.get('state') == 'merged' else None
    if not batch:
        raise ValueError('No retained or completed batch owns this promotion')
    admission = batch_policy.admit(api.request, config, pr, batch['issues'], state)
    comparison = api.request(api.root + '/compare/' + pr['merge_commit_sha'] + '...' + quote(config['project']['base_branch'], safe=''))
    if comparison.get('status') not in ('ahead', 'identical'):
        raise ValueError('Acceptance main merge is no longer included')
    lane = batch.get('review') if batch.get('state') == 'merged' else section.get('review')
    if (lane['actor'] == batch['actor'] or lane['session'] == batch['session']
            or any(lane['actor'] == w['actor'] or lane['session'] == w['session']
                   for n in batch['issues'] for w in section['tasks'][str(n)].get('implementers', []))):
        raise ValueError('Acceptance cannot be attested by a member implementer or Coordinator')
    members = batch['members']
    identity = dict(batch_id=batch_id, pr=pr_number, merge_sha=pr['merge_commit_sha'],
                    head_sha=pr['head']['sha'], tree_sha=admission['tree_sha'], policy=rules.fingerprint(config),
                    issues=batch['issues'], source_heads=[m['head_sha'] for m in members],
                    issue_scopes={str(m['issue']): m['scope'] for m in members},
                    reviewer=lane['actor'], review_session=lane['session'], execution_lane=lane['id'],
                    coordinator=batch['actor'], coordinator_session=batch['session'])
    return section, batch, lane, identity


def validate_document(api, document, identity, config):
    if (not isinstance(document, dict) or document.get('kind') != 'post-main-acceptance'
            or any(document.get(k) != v for k, v in identity.items())
            or not isinstance(document.get('report'), str) or not document['report'].strip()):
        raise ValueError('Acceptance evidence is missing or stale for the exact batch/owner')
    expected = {}
    for n in identity['issues']:
        item = api.issue(n)
        if not rules.scope_matches(item, identity['issue_scopes'][str(n)], config):
            raise ValueError('Acceptance task scope changed during verification')
        entries = criteria(item.get('body'))
        if entries: expected[str(n)] = entries
    supplied = document.get('criteria')
    if not expected or not isinstance(supplied, dict) or set(supplied) != set(expected):
        raise ValueError('Acceptance must cover every unchecked criterion of exactly this batch')
    for n, entries in expected.items():
        rows = supplied[n]
        if not isinstance(rows, list) or len(rows) != len(entries):
            raise ValueError('Acceptance is partial')
        for row, entry in zip(rows, entries):
            if (not isinstance(row, dict) or any(row.get(k) != v for k, v in entry.items())
                    or row.get('result') != 'passed' or not isinstance(row.get('evidence'), str)
                    or not row['evidence'].strip()):
                raise ValueError('Each exact unchecked criterion needs passed concrete evidence')


def record(api, config, store, args, document):
    state, sha = store.read(optional=True)
    section, batch, lane, identity = context(api, config, state, args.pr)
    if batch.get('state') == 'merged':
        raise ValueError('Record acceptance under retained independent integration ownership before completion')
    execution.owned(lane, args, 'Reviewer')
    validate_document(api, document, identity, config)
    receipts = state.setdefault('delivery_workflow', {}).setdefault('acceptances', {})
    old = receipts.get(batch['id'])
    if old and old['evidence'] != document:
        raise ValueError('Resume the original acceptance evidence; do not overwrite its history')
    if args.apply and not old:
        receipts[batch['id']] = {'evidence': copy.deepcopy(document), 'recorded_at': now()}
        execution.audit(section, 'post-main-acceptance-recorded', batch_id=batch['id'], pr=args.pr)
        store.write(state, sha)
    return {'applied': args.apply, 'already_applied': bool(old), 'batch_id': batch['id'], 'issues': batch['issues']}


def verify(api, config, store, issue, prs):
    state, _ = store.read(optional=True)
    for pr in prs:
        section, batch, lane, identity = context(api, config, state, pr)
        if issue['number'] not in batch['issues']:
            continue
        receipt = state.get('delivery_workflow', {}).get('acceptances', {}).get(batch['id'], {})
        validate_document(api, receipt.get('evidence'), identity, config)
        if not rules.scope_matches(issue, identity['issue_scopes'][str(issue['number'])], config):
            raise ValueError('Acceptance task scope changed during completion')
        return
    raise ValueError('No verified acceptance receipt covers this task')
