"""Owner-approved adoption history, never admission or delivery evidence."""
import hashlib
import json
import re
from datetime import datetime, timezone

from . import delivery_policy, identifiers


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def issue_digest(issue):
    return delivery_policy.accepted_scope_digest(issue)


def validate(config):
    value = config.get('historical_completion')
    if value is None:
        return None
    fields = {'schema_version', 'repository', 'policy', 'audited_at', 'approved_by', 'report',
              'source_revision', 'source_config_sha256', 'tasks'}
    if not isinstance(value, dict) or set(value) != fields:
        raise ValueError('Invalid historical_completion fields')
    if type(value['schema_version']) is not int or value['schema_version'] != 1:
        raise ValueError('Unsupported historical completion version')
    if not delivery_policy.policy(config) or value['policy'] != delivery_policy.fingerprint(config):
        raise ValueError('Historical completion must match the adopted delivery policy')
    if value['repository'] != config['project']['repository']:
        raise ValueError('Historical completion repository differs')
    for key in ('approved_by', 'report'):
        if not isinstance(value[key], str) or not value[key].strip():
            raise ValueError('Historical completion needs owner approval and a durable report')
    for key, length in (('source_revision', 40), ('source_config_sha256', 64)):
        if not isinstance(value[key], str) or not re.fullmatch('[0-9a-f]{' + str(length) + '}', value[key]):
            raise ValueError('Historical completion needs immutable source provenance')
    try:
        stamp = datetime.fromisoformat(value['audited_at'].replace('Z', '+00:00'))
        if stamp.utcoffset() is None or stamp > datetime.now(timezone.utc):
            raise ValueError()
    except (ValueError, TypeError, AttributeError):
        raise ValueError('Historical completion needs a past, timezone-aware audit timestamp') from None
    if not isinstance(value['tasks'], dict) or not value['tasks']:
        raise ValueError('Historical completion needs an explicit nonempty task allowlist')
    for number, row in value['tasks'].items():
        if not isinstance(number, str) or not re.fullmatch('[1-9][0-9]*', number):
            raise ValueError('Invalid historical task number')
        if (not isinstance(row, dict) or set(row) != {'id', 'issue_sha256'}
                or row['id'] != identifiers.task_id({'number': int(number)}, config)
                or not isinstance(row['issue_sha256'], str) or not re.fullmatch('[0-9a-f]{64}', row['issue_sha256'])):
            raise ValueError('Invalid historical task identity or scope digest')
    return value


def accepted(issue, task, manifest, receipt):
    row = (manifest or {}).get('tasks', {}).get(str(issue['number']), {})
    # Any current/revoked delivery record wins over historical acceptance, even a
    # failed or obsolete record. Restarting through work reserves this revocation.
    return bool(row and not receipt and task['phase'] == 'merged' and not task['archive']
                and not task['blocked'] and row['id'] == task['id'] and row['issue_sha256'] == issue_digest(issue))


def audit(issues, original, candidate, *, source_revision, approved_by, report):
    from .model import tasks_from_issues, is_complete
    if original.get('delivery_policy') or original.get('historical_completion'):
        raise ValueError('Audit requires the original pre-delivery configuration')
    for key in ('repository', 'id_prefix', 'id_offset', 'legacy_task_ids'):
        if original['project'].get(key) != candidate['project'].get(key):
            raise ValueError('Historical audit must preserve repository and task identities')
    if candidate.get('historical_completion'):
        raise ValueError('Do not automatically extend or replace an existing historical manifest')
    previous = tasks_from_issues(issues, original)
    by_number = {i['number']: i for i in issues}
    eligible = [t for t in previous if is_complete(t) and not t['blocked']]
    for task in eligible:
        if not by_number[task['number']].get('created_at'):
            raise ValueError('Historical audit requires issue creation timestamps')
    manifest = {'schema_version': 1, 'repository': original['project']['repository'],
                'policy': delivery_policy.fingerprint(candidate),
                'audited_at': datetime.now(timezone.utc).isoformat(), 'approved_by': approved_by, 'report': report,
                'source_revision': source_revision, 'source_config_sha256': digest(original),
                'tasks': {str(t['number']): {'id': t['id'], 'issue_sha256': issue_digest(by_number[t['number']])}
                          for t in eligible}}
    validate(dict(candidate, historical_completion=manifest))
    return manifest
