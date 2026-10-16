"""Prepare a workspace registration without publishing or replacing project data."""
from contextlib import contextmanager
import os
import tempfile
import json
import re
from pathlib import Path
from .model import load_config
from .workspace import load_workspace


@contextmanager
def registration_lock(workspace):
    lock = workspace.parent / '.tracker-registration.lock'
    try:
        lock.mkdir()
    except FileExistsError:
        raise ValueError('Another registration is active; inspect the lock before retrying') from None
    try:
        yield
    finally:
        lock.rmdir()


def register(workspace, project_config, identifier, apply=False):
    workspace = Path(workspace).absolute()
    if any(p.is_symlink() for p in (workspace, *workspace.parents)):
        raise ValueError('Registration paths must not be symlinks')
    if not apply:
        return _register(workspace, project_config, identifier, False)
    with registration_lock(workspace):
        return _register(workspace, project_config, identifier, True)


def _register(workspace, project_config, identifier, apply):
    workspace, project_config = Path(workspace).absolute(), Path(project_config).absolute()
    if not re.fullmatch(r'[a-z][a-z0-9-]*', identifier):
        raise ValueError('Project ID must be a safe URL segment')
    if any(p.is_symlink() for path in (workspace, project_config) for p in (path, *path.parents)):
        raise ValueError('Registration paths must not be symlinks')
    config = load_config(project_config)
    before = workspace.read_bytes()
    registry = load_workspace(workspace)
    project = config['project']
    destination = workspace.parent / 'projects' / (identifier + '.json')
    if destination.parent.is_symlink() or destination.is_symlink():
        raise ValueError('Registration target must not be a symlink')
    row = {'id': identifier, 'name': project['name'], 'repository': project['repository'],
           'base_branch': project['base_branch'], 'config': destination.relative_to(workspace.parent).as_posix()}
    matches = [p for p in registry['projects'] if p['id'] == identifier or p['repository'].lower() == project['repository'].lower()]
    if matches:
        if matches != [row] or not destination.is_file() or load_config(destination) != config:
            raise ValueError('Registration conflicts with an existing project; prepare an explicit migration')
        return {'registered': identifier, 'changed': False, 'published': False}
    for existing in registry['projects']:
        other = load_config(workspace.parent / existing['config'])
        if other['project'].get('id_prefix') == project.get('id_prefix'):
            raise ValueError('Project prefix is already registered')
    text = json.dumps(config, indent=2) + '\n'
    if destination.exists() and destination.read_text() != text:
        raise ValueError('Existing fallback configuration must be preserved')
    registry['projects'].append(row)
    if apply:
        if workspace.read_bytes() != before:
            raise ValueError('Registry changed; inspect before retrying')
        destination.parent.mkdir(parents=True, exist_ok=True)
        if not destination.exists():
            with destination.open('x') as output: output.write(text)
        with tempfile.NamedTemporaryFile(mode='w', dir=workspace.parent, delete=False) as output:
            temporary = Path(output.name)
            output.write(json.dumps(registry, indent=2) + '\n')
        try:
            os.replace(temporary, workspace)
        finally:
            temporary.unlink(missing_ok=True)
    return {'registered': identifier, 'changed': True, 'applied': apply, 'published': False,
            'next': 'Review and publish the registry change through the maintained Tracker process, then verify the project snapshot.'}
