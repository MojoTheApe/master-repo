"""Engine-free orchestration of canonical Tracker fixtures; no copied proof rules."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import types

SOURCE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SOURCE/'scripts'))
import export_contract as contract

FIXTURES = 'tests/fixtures/portable-contract'


def verified_artifacts():
    raw, record, _ = contract.trusted()
    base = SOURCE/FIXTURES
    provenance = json.loads(contract.safe_file(base, 'provenance.json').read_bytes(), object_pairs_hook=contract.unique)
    assert provenance['schema_version'] == 1 and provenance['synthetic'] is True
    assert provenance['engine'] == record['engine']
    expected_sources = {'runner.py': 'tests/portable_fixture.py', 'native.json': 'tests/fixtures/portable_native.json',
                        'accounting.json': 'tests/fixtures/ci_accounting_synthetic.json'}
    assert set(provenance['files']) == set(expected_sources)
    artifacts = {}
    for name, source in expected_sources.items():
        artifacts[name] = contract.safe_file(base, name).read_bytes()
        assert provenance['files'][name] == {'source': source, 'sha256': hashlib.sha256(artifacts[name]).hexdigest()}
    data = json.loads(artifacts['native.json'], object_pairs_hook=contract.unique)
    assert data['schema_version'] == 1 and data['synthetic'] is True
    assert len(data['contexts']) == 8
    assert {(row['layout'], row['context']) for row in data['contexts']} == {
        (layout, context) for layout in ('raw', 'separated') for context in ('source', 'integration', 'main', 'promotion')}
    accounting = json.loads(artifacts['accounting.json'], object_pairs_hook=contract.unique)
    assert accounting['schema_version'] == 1 and accounting['synthetic'] is True
    for layout in ('raw', 'separated'):
        root = base/layout
        contract.check_manifest(contract.safe_file(root, contract.MANIFEST).read_bytes(), raw)
        assert json.loads(contract.safe_file(root, 'tracker/engine.json').read_bytes(),
                          object_pairs_hook=contract.unique) == record['engine']
        for path, digest in contract.layout_files(record, layout).items():
            assert hashlib.sha256(contract.safe_file(root, path).read_bytes()).hexdigest() == digest, path
    return record, provenance, artifacts, data


def isolated_consumer(root, python):
    """Check both actual entry points/import locations on a representative render."""
    code = '''import json,sys
from pathlib import Path
sys.path.insert(0,sys.argv[1])
import tracker_ci_gate, tracker_ci_evidence, tracker_batch_policy, tracker_pr_check, tracker_task_context, tracker_delivery_receipt
import tracker_ci_retry, tracker_ci_accounting
config=json.loads((Path(sys.argv[2])/'tracker/config.json').read_bytes())
assert tracker_ci_retry.policy(config)==config.get('ci_retry_policy')
assert not any(n=='tracker' or n.startswith('tracker.') for n in sys.modules)
'''
    import os
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
    for key in ('PYTHONPATH', 'TASK_TRACKER_HOME'): env.pop(key, None)
    with tempfile.TemporaryDirectory(prefix='master-portable-import-') as temporary:
        for directory in ('scripts', '.workflow/tools'):
            result = subprocess.run([python, '-B', '-I', '-c', code, str(root/directory), str(root)],
                cwd=temporary, env=env, capture_output=True, text=True)
            assert result.returncode == 0, result.stderr
            result = subprocess.run([python, '-B', str(root/directory/'tracker_ci_gate.py'), '--help'],
                cwd=root, env=env, capture_output=True, text=True)
            assert result.returncode == 0 and '{plan,gate}' in result.stdout, result.stderr
    return {'isolated_imports': ['scripts', '.workflow/tools'], 'actual_cli_help': True, 'private_engine_imported': False}


def exercise_all(python, tracker=None):
    record, provenance, artifacts, data = verified_artifacts()
    if tracker is not None:
        for name, row in provenance['files'].items():
            actual = subprocess.check_output(['git', '-C', str(tracker), 'show', record['engine']['revision']+':'+row['source']])
            assert artifacts[name] == actual, 'Copied native proof artifact differs from actual selected engine'
    runner = types.ModuleType('_canonical_tracker_portable_fixture')
    runner.__file__ = str(SOURCE/FIXTURES/'runner.py')
    exec(compile(artifacts['runner.py'], runner.__file__, 'exec'), runner.__dict__)
    results, accounting_results = [], []
    with tempfile.TemporaryDirectory(prefix='master-portable-native-') as temporary:
        for index, row in enumerate(data['contexts']):
            root = Path(temporary)/str(index); root.mkdir()
            for name in contract.layout_files(record, row['layout']):
                path = root/name; path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes((SOURCE/FIXTURES/row['layout']/name).read_bytes())
            config = root/'tracker/config.json'; config.parent.mkdir(parents=True, exist_ok=True)
            config.write_text(json.dumps(row['config']))
            results.append(runner.exercise(root, python, row['layout'], row))
        for layout in ('raw', 'separated'):
            root = Path(temporary)/('accounting-'+layout); root.mkdir()
            for name in contract.layout_files(record, layout):
                path = root/name; path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes((SOURCE/FIXTURES/layout/name).read_bytes())
            accounting_results.append(runner.exercise_accounting(root, python, layout,
                json.loads(artifacts['accounting.json'], object_pairs_hook=contract.unique)))
    return {'engine': record['engine'], 'provenance': provenance, 'cases': results,
            'accounting': accounting_results, 'clock_fixture_only': True,
            'private_engine_required': False, 'live_requests': 0}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--python', default=sys.executable)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    result = exercise_all(args.python)
    raw = json.dumps(result, indent=2)+'\n'
    if args.output: args.output.write_text(raw)
    print(raw)


if __name__ == '__main__': main()
