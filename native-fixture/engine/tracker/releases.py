"""One active Release flag with an explicit, resumable published-release archive."""
from .model import tasks_from_issues, release_summary
from .sync import now


def close(api, config, store, name, *, apply=False, published=False, resume=False):
    if not name.strip(): raise ValueError('Name the release being recorded')
    state, sha = store.read(optional=True)
    pending = state.get('release_rollover')
    if pending:
        if not resume or pending['name'] != name.strip():
            raise ValueError('A release rollover is pending; inspect it and resume with the same name')
        entry = pending
    else:
        if resume: raise ValueError('No release rollover to resume')
        if any(r['name'] == name.strip() for r in state.get('release_history', [])):
            raise ValueError('This release name already exists; its history is immutable')
        tasks = tasks_from_issues(api.issues(), config, state.get('delivery_workflow',{}).get('tasks',{}))
        if not release_summary(tasks)['ready']:
            raise ValueError('Release needs a nonempty, completed scope with resolved dependencies and metadata')
        # Include initiative membership in history/cleanup without counting it twice.
        members = [t for t in tasks if t['release']]
        entry = {'name': name.strip(), 'recorded_at': now(),
                 'tasks': [{k: t[k] for k in ('number','id','title','url','status','initiative')} for t in members]}
    if not apply: return {'applied': False, 'release': entry}
    if not published: raise ValueError('Recording a published release requires --published; merge alone is insufficient')
    if not pending:
        state['release_rollover'] = entry; store.write(state, sha)
    # The durable journal precedes label removal. Retry never loses the snapshot
    # and never clears tasks added after the recorded scope was captured.
    for task in entry['tasks']:
        api.labels(task['number'], (), {'release:included','release:required'})
    latest, sha = store.read()
    if latest.get('release_rollover') != entry:
        raise ValueError('Release journal changed; inspect it before continuing')
    latest.setdefault('release_history', []).append(entry)
    latest['release_rollover'] = None; store.write(latest, sha)
    return {'applied': True, 'release': entry, 'next': 'The next Release scope starts empty; Issue statuses and Archive are preserved.'}
