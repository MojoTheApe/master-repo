"""Independent project snapshots behind one authenticated workspace."""
import json
import re
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import quote
from .github import GitHub, file_bytes
from .model import load_config, payload
from .sync import write_page, atomic_write, now, render, sync
from .gallery import write_logo_page
from .skills import write_skills_page


def load_workspace(path):
    path = Path(path)
    value = json.loads(path.read_text(encoding='utf-8'))
    projects = value.get('projects')
    if value.get('schema_version') != 1 or not isinstance(projects, list) or not projects:
        raise ValueError('Expected a nonempty workspace project registry')
    ids, repos, prefixes = set(), set(), set()
    for row in projects:
        if not re.fullmatch(r'[a-z][a-z0-9-]*', row.get('id', '')) or row['id'] in ids:
            raise ValueError('Project IDs must be unique safe URL segments')
        repo = row.get('repository', '')
        if not re.fullmatch(r'[\w.-]+/[\w.-]+', repo) or repo.lower() in repos:
            raise ValueError('Project repositories must be valid and unique')
        if not row.get('name') or not row.get('base_branch'):
            raise ValueError('A project needs a name and base branch')
        fallback = (path.parent / row['config']).resolve()
        config = load_config(fallback)
        if config['project']['repository'] != repo or config['project']['base_branch'] != row['base_branch']:
            raise ValueError('Registry and fallback config identity must agree')
        prefix = config['project'].get('id_prefix')
        if prefix and prefix in prefixes: raise ValueError('Workspace project ID prefixes must be unique')
        if prefix: prefixes.add(prefix)
        ids.add(row['id']); repos.add(repo.lower())
    if value.get('default_project') not in ids:
        raise ValueError('Default project must be registered')
    return value


def remote_config(api, project):
    ref = quote(project['base_branch'], safe='')
    row = api.request(api.root + '/contents/tracker/config.json?ref=' + ref)
    config_text = file_bytes(api.request, api.root, row).decode('utf-8')
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / 'config.json'
        path.write_text(config_text, encoding='utf-8')
        config = load_config(path)
    if config['project']['repository'] != project['repository'] or config['project']['base_branch'] != project['base_branch']:
        raise ValueError('Remote configuration belongs to another project or branch')
    return config


def sync_workspace(path, output, *, command=None, api_factory=None, project_ids=None, freshness_seconds=None):
    from .sync_state import exclusive_lock
    with exclusive_lock(Path(output) / '.sync.lock'):
        return _sync_workspace(path, output, command=command, api_factory=api_factory,
                               project_ids=project_ids, freshness_seconds=freshness_seconds)


def _sync_workspace(path, output, *, command=None, api_factory=None, project_ids=None, freshness_seconds=None):
    path, output = Path(path), Path(output)
    registry = load_workspace(path)
    menu = [{'id': p['id'], 'name': p['name'], 'repository': p['repository'], 'url': '/projects/' + p['id'] + '/'} for p in registry['projects']]
    make_api = api_factory or (lambda repo: GitHub(repo, command))
    identifiers = {p['id'] for p in registry['projects']}
    selected = identifiers if project_ids is None else set(project_ids)
    if not selected <= identifiers:
        raise ValueError('Unknown workspace project selection')
    # A first installation still needs an isolated snapshot/shell for every menu entry.
    selected |= {p['id'] for p in registry['projects'] if not (output / 'projects' / p['id'] / 'data.json').exists()}

    def refresh(project):
        destination = output / 'projects' / project['id']
        meta = {'current': project['id'], 'base_url': '/projects/' + project['id'] + '/', 'projects': menu}
        try:
            old = json.loads((destination / 'data.json').read_text())
            if old['project']['repository'] == project['repository']:
                meta['redirects'] = old.get('workspace', {}).get('redirects', {})
        except (OSError, ValueError, KeyError):
            pass
        stage = 'config_failed'
        try:
            api = make_api(project['repository'])
            config = remote_config(api, project)
            fallback = load_config(path.parent / project['config'])
            # Public ID namespaces are immutable after rollout; mismatches fail
            # one project's refresh instead of silently renumbering its tasks.
            for key in ('id_prefix', 'id_offset', 'legacy_task_ids'):
                if fallback['project'].get(key) != config['project'].get(key):
                    raise ValueError('Remote task ID namespace differs from the approved registry')
            # The registry is authoritative for menu names; module/workflow content belongs to the project.
            config['project']['name'] = project['name']
            stage = 'sync_failed'
            result = sync(api, config, destination, workspace=meta, freshness_seconds=freshness_seconds)
            return {'id': project['id'], 'ok': True, 'issues': result['issues']}
        except Exception:
            # Initial unavailable projects get an explicitly failed empty shell, never another project's data.
            if not (destination / 'data.json').exists():
                config = load_config(path.parent / project['config'])
                config['project']['name'] = project['name']
                data = payload([], config)
                data['workspace'] = meta
                page, data = render(data)
                atomic_write(destination / 'data.json', json.dumps(data))
                write_page(destination, page)
                atomic_write(destination / 'status.json', json.dumps({'ok': False, 'error': stage, 'attempted_at': now(), 'issues': 0, 'repository': project['repository']}))
            elif stage == 'config_failed':
                try: status = json.loads((destination / 'status.json').read_text())
                except (OSError, ValueError): status = {}
                status.update(ok=False, error=stage, attempted_at=now())
                atomic_write(destination / 'status.json', json.dumps(status))
            return {'id': project['id'], 'ok': False, 'error': stage}

    # One failing/slow repository does not serialize all other project snapshots.
    with ThreadPoolExecutor(max_workers=min(6, len(menu))) as pool:
        results = list(pool.map(refresh, [p for p in registry['projects'] if p['id'] in selected]))
    # Transferred Issues keep their old UI deep links. Only registered repository
    # identities and positive Issue numbers can contribute an internal redirect.
    repositories = {p['repository'].lower(): p['id'] for p in registry['projects']}
    routes = {p['id']: {} for p in registry['projects']}
    snapshots = {}
    for project in registry['projects']:
        data = json.loads((output / 'projects' / project['id'] / 'data.json').read_text())
        snapshots[project['id']] = data
        for task in data['tasks']:
            for origin in task.get('origins', []):
                match = re.fullmatch(r'https://github\.com/([\w.-]+/[\w.-]+)/issues/([1-9]\d*)', origin)
                source = repositories.get(match[1].lower()) if match else None
                if source and source != project['id']:
                    target = {'project': project['id'], 'number': task['number']}
                    key = match[2]
                    if key in routes[source] and routes[source][key] != target:
                        routes[source][key] = None  # ambiguous provenance must not pick a random task
                    else: routes[source][key] = target
    for project in registry['projects']:
        identifier = project['id']; data = snapshots[identifier]
        destination = output / 'projects' / identifier
        status = json.loads((destination / 'status.json').read_text())
        if not status.get('ok'): continue
        redirects = {key: value for key, value in routes[identifier].items() if value}
        if data['workspace'].get('redirects', {}) == redirects: continue
        data['workspace']['redirects'] = redirects
        data.pop('digest', None); data.pop('revision', None)
        page, data = render(data)
        status.update(digest=data['digest'], revision=data['revision'])
        atomic_write(destination / 'data.json', json.dumps(data))
        write_page(destination, page)
        atomic_write(destination / 'status.json', json.dumps(status))
    default = output / 'projects' / registry['default_project']
    # Old ACL tabs validate schema before noticing a new UI revision. Keep the
    # root envelope readable so they can reload; project paths use schema 3.
    root_data = json.loads((default / 'data.json').read_text(encoding='utf-8'))
    root_data.pop('digest', None); root_data.pop('revision', None)
    root_data['schema_version'] = 2
    page, root_data = render(root_data)
    status = json.loads((default / 'status.json').read_text(encoding='utf-8'))
    status.update(digest=root_data['digest'], revision=root_data['revision'])
    atomic_write(output / 'data.json', json.dumps(root_data))
    write_page(output, page)
    atomic_write(output / 'status.json', json.dumps(status))
    write_logo_page(output)
    write_skills_page(output)
    attempted = {r['id'] for r in results}
    for project in registry['projects']:
        if project['id'] in attempted: continue
        saved = json.loads((output / 'projects' / project['id'] / 'status.json').read_text())
        results.append({'id': project['id'], 'ok': bool(saved.get('ok')), 'issues': saved.get('issues', 0), 'refreshed': False})
    result = {'ok': all(r['ok'] for r in results), 'projects': results, 'attempted_at': now()}
    atomic_write(output / 'workspace-status.json', json.dumps(result))
    return result
