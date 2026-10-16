"""Owned maintenance intervals share the same CAS file as task admission."""
import copy
import uuid
from . import delivery_policy as rules
from .execution import credentials
from .sync import now


def busy(state):
    execution = state.get('execution') or {}
    stage = state.get('delivery_workflow', {}).get('stage') or {}
    return bool(state.get('active') or (state.get('run') or {}).get('state') == 'running'
                or state.get('release_rollover')
                or any(r.get('state') == 'creating' for r in state.get('intakes', {}).values())
                or any(r.get('state') in ('returning_approval', 'archiving')
                       for r in execution.get('tasks', {}).values())
                or execution.get('claims') or rules.review_lanes(execution)
                or execution.get('integration') or (execution.get('intake') or {}).get('state') == 'running'
                or stage and stage.get('state') != 'promoted')


def report(args):
    path = getattr(args, 'report_file', None)
    if path is None:
        raise ValueError('Supply --report-file with actual maintenance authorization/compatible-writer evidence')
    text = path.read_text(encoding='utf-8').strip()
    if not text or len(text.encode()) > 65536:
        raise ValueError('Maintenance report must be nonempty and bounded to 64 KiB; include no secrets')
    return text


def owned(state, args):
    rules.state_schema(state)
    identity, session = credentials(args, 'Maintainer')
    row = state.get('maintenance')
    if not row or (row['id'], row['actor'], row['session']) != (getattr(args, 'claim', None), identity, session):
        raise ValueError('Stale or foreign maintenance claim; inspect maintenance show and resume its actual owner')
    return row


def show(store):
    state, sha = store.read(optional=True)
    rules.state_schema(state)
    return {'maintenance': state.get('maintenance'), 'history': state.get('maintenance_history', []),
            'idle': not busy(state), 'state_sha': sha, 'private': True}


def reserve(store, args):
    state, sha = store.read(optional=True)
    rules.state_schema(state)
    schema = state['schema_version']
    if state.get('maintenance'):
        row = owned(state, args)
        return {'maintenance': row, 'resumed': True, 'applied': False, 'private': True}
    identity, session = credentials(args, 'Maintainer')
    text = report(args)
    row = {'schema_version': 1, 'state': 'held', 'base_schema_version': schema,
           'id': uuid.uuid4().hex, 'actor': identity, 'session': session, 'reserved_at': now(), 'report': text}
    state['schema_version'] = 3
    state['maintenance'] = row
    state.setdefault('maintenance_history', []).append({'event': 'maintenance-reserved', 'at': now(),
                                                       'owner': copy.deepcopy(row)})
    rules.state_schema(state)
    if args.apply:
        store.write(state, sha)
    return {'applied': args.apply, 'maintenance': row, 'idle': not busy(state), 'private': True,
            'instruction': 'Reservation is not idleness or migration; retain this claim until supported resume/transfer.'}


def resume(store, args):
    state, sha = store.read(optional=True)
    rules.state_schema(state)
    if not state.get('maintenance'):
        identity, session = credentials(args, 'Maintainer')
        history = state.get('maintenance_history', [])
        last = history[-1] if history else {}
        previous = last.get('owner', {})
        if (last.get('event') == 'maintenance-resumed'
                and (previous.get('id'), previous.get('actor'), previous.get('session'))
                == (getattr(args, 'claim', None), identity, session)):
            return {'applied': False, 'already_resumed': True, 'admission_paused': False, 'private': True}
    row = owned(state, args)
    text = report(args)
    state['maintenance_history'].append({'event': 'maintenance-resumed', 'at': now(),
                                         'owner': copy.deepcopy(row), 'report': text})
    state['schema_version'] = row['base_schema_version']
    del state['maintenance']
    if args.apply:
        store.write(state, sha)
    return {'applied': args.apply, 'admission_paused': False, 'private': True,
            'instruction': 'Only admission resumed; all unfinished tasks, claims and delivery obligations remain.'}


def transfer(store, args):
    state, sha = store.read(optional=True)
    rules.state_schema(state)
    previous = state.get('maintenance')
    identity, session = credentials(args, 'Maintainer')
    history = state.get('maintenance_history', [])
    last = history[-1] if history else {}
    if (previous and previous['actor'] == identity and previous['session'] == session
            and last.get('event') == 'maintenance-transferred' and last.get('owner') == previous
            and last.get('previous', {}).get('id') == getattr(args, 'previous_claim', None)):
        return {'applied': False, 'resumed': True, 'maintenance': previous, 'private': True}
    if not previous or previous['id'] != getattr(args, 'previous_claim', None) or not args.stopped:
        raise ValueError('Transfer requires the current --previous-claim and verified --stopped owner')
    if identity == previous['actor'] or session == previous['session']:
        raise ValueError('The actual current maintenance owner must resume its own claim')
    text = report(args)
    row = dict(previous, id=uuid.uuid4().hex, actor=identity, session=session, report=text)
    state['maintenance'] = row
    state['maintenance_history'].append({'event': 'maintenance-transferred', 'at': now(),
                                         'previous': copy.deepcopy(previous), 'owner': copy.deepcopy(row)})
    if args.apply:
        store.write(state, sha)
    return {'applied': args.apply, 'maintenance': row, 'private': True,
            'instruction': 'Stopped owner transferred; existing task/review/batch ownership and admission pause retained.'}
