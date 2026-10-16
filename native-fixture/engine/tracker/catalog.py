"""Explicit, auditable module extensions and archival actions."""
import copy
import json
import re
import tempfile
from pathlib import Path
from urllib.parse import quote
from .model import load_config, names
from .sync import atomic_write, now


def add_module(api, config, path, *, identifier, name, description, examples, reason):
    if not re.fullmatch(r'[a-z][a-z0-9_-]*', identifier):
        raise ValueError('Use a stable lowercase module ID')
    if not name.strip() or not description.strip() or not examples or not all(isinstance(e,str) and e.strip() for e in examples) or not reason.strip():
        raise ValueError('A new module needs a name, responsibility, examples and a reason')
    if any(m['id'] == identifier or m['name'].casefold() == name.strip().casefold() for m in config['modules']):
        raise ValueError('A module with that ID or name already exists; inspect its boundaries')
    updated = copy.deepcopy(config)
    updated['modules'].append({'id': identifier, 'name': name.strip(), 'description': description.strip(), 'examples': examples})
    updated.setdefault('module_history', []).append({'module': identifier, 'reason': reason.strip(), 'added_at': now()})
    # Validate without risking the original configuration on a failed API operation.
    with tempfile.TemporaryDirectory() as directory:
        candidate = Path(directory) / 'config.json'
        candidate.write_text(json.dumps(updated), encoding='utf-8')
        load_config(candidate)
    label = 'module:' + identifier
    existing = api.request(api.root + '/labels/' + quote(label, safe=''), optional=True)
    if existing is None:
        api.request(api.root + '/labels', 'POST', {'name': label, 'description': name.strip()[:100], 'color': '7B8994'})
    if api.request(api.root + '/labels/' + quote(label, safe=''))['name'] != label:
        raise ValueError('New module label did not verify')
    if json.loads(Path(path).read_text(encoding='utf-8')) != config:
        raise ValueError('Project configuration changed during module creation; reload and reconcile it')
    atomic_write(path, json.dumps(updated, indent=2, ensure_ascii=False) + '\n')
    return {'module': identifier, 'config': str(path), 'next': 'Review and commit this configuration through the project workflow. Agent instructions read module boundaries from this file. Report the reason for the new module.'}


def archive(api, store, number, reason):
    if not reason.strip():
        raise ValueError('Archiving requires a reason')
    state, _ = store.read(optional=True)
    if state.get('active') and state['active']['issue'] == number:
        raise ValueError('Record a blocker or review handoff and release the active task before archiving')
    issue = api.issue(number)
    if 'flag:archived' not in names(issue):
        api.request(api.root + f'/issues/{number}', 'PATCH', {'body': (issue.get('body') or '') + '\n\nArchived: ' + reason.strip()})
    api.labels(number, {'flag:archived'})
    from .timing import end_observations
    state, sha = store.read(optional=True)
    if end_observations(state, number):
        store.write(state, sha)
    return {'number': number, 'archived': True, 'status_preserved': True}


def restore(api, number):
    issue = api.issue(number)
    if issue.get('state') == 'closed':
        api.request(api.root + f'/issues/{number}', 'PATCH', {'state': 'open'})
    api.labels(number, (), {'flag:archived'})
    return {'number': number, 'archived': False, 'status_preserved': True}
