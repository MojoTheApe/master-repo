#!/usr/bin/env python3
"""Refresh generated trust records and engine-free fixtures from a clean exact source.

Preview by default. Publication, review and final paired admission are separate.
This command never reads a consumer repository or calls a network API.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile

SOURCE = Path(__file__).resolve().parents[1]
FIXTURES = 'tests/fixtures/portable-contract'


def git(root, *args):
    return subprocess.check_output(['git', '-C', str(root), *args])


def plan(engine, revision, python):
    engine = Path(engine).resolve()
    if not re.fullmatch(r'[a-f0-9]{40}', revision):
        raise ValueError('Use the exact immutable source revision')
    remote = git(engine, 'remote', 'get-url', 'origin').decode().strip().removesuffix('.git')
    if (git(engine, 'rev-parse', 'HEAD').decode().strip() != revision
            or git(engine, 'status', '--porcelain')
            or remote not in ('https://github.com/MojoTheApe/task-tracker', 'git@github.com:MojoTheApe/task-tracker')):
        raise ValueError('Use a clean official Tracker checkout at the selected exact revision')
    planned, manifests = {}, []
    with tempfile.TemporaryDirectory(prefix='master-tracker-contract-') as temporary:
        for layout in ('raw', 'separated'):
            output = Path(temporary)/layout
            command = [python, '-m', 'tracker', '--config', str(engine/'tracker/config.json'),
                'export-template', '--output', str(output), '--repository', 'example/portable',
                '--name', 'Portable contract fixture', '--base', 'main', '--id-prefix', 'EX',
                '--engine-revision', revision, '--helper-layout', layout]
            result = subprocess.run(command, cwd=engine, capture_output=True, text=True)
            if result.returncode:
                raise ValueError('Actual pinned Tracker export failed: ' + result.stderr + result.stdout)
            raw = (output/'tracker/export-contract.json').read_bytes()
            record = json.loads(raw)
            if record.get('format_version') != 1 or record.get('engine') != {
                    'repository': 'MojoTheApe/task-tracker', 'revision': revision}:
                raise ValueError('Actual export manifest differs from the selected source')
            manifests.append(raw)
            for name, expected in record['layouts'][layout].items():
                path = Path(name)
                if path.is_absolute() or '..' in path.parts or '\\' in name or ':' in name:
                    raise ValueError('Unsafe generated helper path')
                content = (output/path).read_bytes()
                if hashlib.sha256(content).hexdigest() != expected:
                    raise ValueError('Actual exported helper digest differs: ' + name)
                planned[FIXTURES+'/'+layout+'/'+name] = content
            for name in ('.gitattributes', 'tracker/export-contract.json', 'tracker/engine.json'):
                planned[FIXTURES+'/'+layout+'/'+name] = (output/name).read_bytes()
            if layout == 'raw':
                snapshot = (output/'scripts/tracker_ci_evidence.py').read_bytes()
                canonical = git(engine, 'show', revision+':tracker/ci_evidence.py')
                if snapshot != canonical or hashlib.sha256(snapshot).hexdigest() != record['validator']['sha256']:
                    raise ValueError('Structural snapshot is not the actual canonical source module')
                planned['scripts/vendor/tracker_ci_evidence.py'] = snapshot
    if manifests[0] != manifests[1]:
        raise ValueError('Tracker layouts exported different static capability manifests')
    planned['scripts/vendor/tracker-export-contract.json'] = manifests[0]
    # Copy the complete canonical offline runner and its synthetic native data.
    # Master owns orchestration only; it does not reproduce proof semantics.
    fixture_sources = {
        'runner.py': 'tests/portable_fixture.py',
        'native.json': 'tests/fixtures/portable_native.json',
    }
    provenance = {'schema_version': 1, 'synthetic': True,
        'engine': {'repository': 'MojoTheApe/task-tracker', 'revision': revision}, 'files': {}}
    for destination, source in fixture_sources.items():
        raw = git(engine, 'show', revision+':'+source)
        if (engine/source).read_bytes() != raw:
            raise ValueError('Canonical fixture checkout differs from its immutable Git blob')
        planned[FIXTURES+'/'+destination] = raw
        provenance['files'][destination] = {'source': source, 'sha256': hashlib.sha256(raw).hexdigest()}
    planned[FIXTURES+'/provenance.json'] = (json.dumps(provenance, indent=2, sort_keys=True)+'\n').encode()
    compatibility = json.loads((SOURCE/'compatibility.json').read_bytes())
    compatibility.update(tracker_revision=revision, export_contract=1,
                         export_contract_sha256=hashlib.sha256(manifests[0]).hexdigest())
    planned['compatibility.json'] = (json.dumps(compatibility, indent=2)+'\n').encode()
    return planned


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tracker-root', type=Path, required=True)
    parser.add_argument('--revision', required=True)
    parser.add_argument('--engine-python', default=sys.executable)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args(argv)
    try:
        planned = plan(args.tracker_root, args.revision, args.engine_python)
        # Refuse unknown content in the generated fixture area; never delete it.
        fixture = SOURCE/FIXTURES
        if fixture.exists():
            unknown = [p for p in fixture.rglob('*') if p.is_file()
                       and not ('__pycache__' in p.parts and p.suffix == '.pyc')
                       and p.relative_to(SOURCE).as_posix() not in planned]
            if unknown:
                raise ValueError('Inspect unexpected generated-fixture files before refresh')
        import standard
        for name in planned:
            path = standard.safe_path(SOURCE, name)
            if path.exists() and not path.is_file():
                raise ValueError('Expected a regular generated artifact: '+name)
        changed = [name for name, raw in planned.items()
                   if not (SOURCE/name).is_file() or (SOURCE/name).read_bytes() != raw]
        if args.apply:
            for name in changed:
                path = SOURCE/name; path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(planned[name])
        print(json.dumps(dict(applied=args.apply, engine_revision=args.revision,
            generated_files=len(planned), changed=changed,
            publication_verified_by_this_command=False,
            manifest_sha256=hashlib.sha256(planned['scripts/vendor/tracker-export-contract.json']).hexdigest()), indent=2))
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        parser.exit(1, str(error)+'\n')
    return 0


if __name__ == '__main__': raise SystemExit(main())
