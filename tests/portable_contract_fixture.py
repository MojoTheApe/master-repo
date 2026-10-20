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


def fixture_sources(record):
    sources = {'runner.py': 'tests/portable_fixture.py', 'native.json': 'tests/fixtures/portable_native.json',
               'accounting.json': 'tests/fixtures/ci_accounting_synthetic.json',
               'selection.json': 'tests/fixtures/portable_selection.json'}
    if 4 in record.get('contracts', {}).get('execution_policy', []):
        validator = record.get('route_validator')
        if (not isinstance(validator, dict) or set(validator) != {'source', 'sha256'}
                or validator['source'] != 'tracker/direct_policy.py'):
            raise ValueError('Modern fixtures require the canonical route validator')
        sources['direct.json'] = 'tests/fixtures/portable_direct.json'
    if record.get('contracts', {}).get('task_pause') == [1]:
        sources['pause.json'] = 'tests/fixtures/portable_pause.json'
    if record.get('contracts', {}).get('process_support') == [1]:
        sources['process.json'] = 'tests/fixtures/portable_process_support.json'
    return sources


def direct_cases(artifacts):
    """Validate only the copied fixture envelope; Tracker owns its proof semantics."""
    if 'direct.json' not in artifacts:
        return []
    data = json.loads(artifacts['direct.json'], object_pairs_hook=contract.unique)
    expected = ['task-main', 'task-stage', 'capture-main', 'capture-stage']
    if (not isinstance(data, dict) or set(data) != {'schema_version', 'synthetic', 'cases'}
            or type(data['schema_version']) is not int or data['schema_version'] != 1
            or data['synthetic'] is not True or not isinstance(data['cases'], list)
            or len(data['cases']) != len(expected)
            or any(not isinstance(row, dict) for row in data['cases'])
            or [row.get('case') for row in data['cases']] != expected):
        raise ValueError('Canonical direct fixtures need all four exact synthetic cases')
    return data['cases']


def verified_artifacts():
    raw, record, _ = contract.trusted()
    base = SOURCE/FIXTURES
    provenance = json.loads(contract.safe_file(base, 'provenance.json').read_bytes(), object_pairs_hook=contract.unique)
    assert provenance['schema_version'] == 1 and provenance['synthetic'] is True
    assert provenance['engine'] == record['engine']
    expected_sources = fixture_sources(record)
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
    direct_cases(artifacts)
    selection_cases(artifacts)
    for layout in ('raw', 'separated'):
        root = base/layout
        contract.check_manifest(contract.safe_file(root, contract.MANIFEST).read_bytes(), raw)
        assert json.loads(contract.safe_file(root, 'tracker/engine.json').read_bytes(),
                          object_pairs_hook=contract.unique) == record['engine']
        for path, digest in contract.layout_files(record, layout).items():
            assert hashlib.sha256(contract.safe_file(root, path).read_bytes()).hexdigest() == digest, path
    return record, provenance, artifacts, data


def selection_cases(artifacts):
    """Require the complete canonical synthetic envelope, without proof rules."""
    data = json.loads(artifacts['selection.json'], object_pairs_hook=contract.unique)
    expected = ['context-v2', 'completion-v3', 'retry-v3', 'completion-retry-v2']
    if (not isinstance(data, dict) or set(data) != {'schema_version', 'synthetic', 'cases'}
            or type(data['schema_version']) is not int or data['schema_version'] != 1
            or data['synthetic'] is not True or not isinstance(data['cases'], list)
            or len(data['cases']) != len(expected)
            or any(not isinstance(row, dict) for row in data['cases'])
            or [row.get('case') for row in data['cases']] != expected):
        raise ValueError('Canonical selection fixtures need all four exact synthetic cases')
    return data['cases']


def isolated_consumer(root, python):
    """Check both actual entry points/import locations on a representative render."""
    code = '''import json,sys
from pathlib import Path
sys.path.insert(0,sys.argv[1])
import tracker_ci_gate, tracker_ci_evidence, tracker_batch_policy, tracker_pr_check, tracker_task_context, tracker_delivery_receipt
import tracker_ci_retry, tracker_ci_accounting
config=json.loads((Path(sys.argv[2])/'tracker/config.json').read_bytes())
assert tracker_ci_retry.policy(config)==config.get('ci_retry_policy')
if config.get('execution_policy',{}).get('schema_version')==4:
 import tracker_direct_policy
 assert tracker_direct_policy.bundle(config)['execution_policy']==config['execution_policy']
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


def exercise_direct_cases(record, artifacts, runner, python, temporary):
    """Replay only the verified engine-owned direct rows, without engine imports."""
    results = []
    for row in direct_cases(artifacts):
        for layout in ('raw', 'separated'):
            root = Path(temporary)/('direct-'+row['case']+'-'+layout); root.mkdir()
            for name in contract.layout_files(record, layout):
                path = root/name; path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes((SOURCE/FIXTURES/layout/name).read_bytes())
            config = root/'tracker/config.json'; config.parent.mkdir(parents=True, exist_ok=True)
            config.write_text(json.dumps(row['config']))
            results.append(runner.exercise_direct(root, python, layout, row))
    return results


def exercise_selection_cases(record, artifacts, runner, python, temporary):
    """Replay Tracker's complete selection package cases through every entry."""
    results = []
    for row in selection_cases(artifacts):
        for layout in ('raw', 'separated'):
            root = Path(temporary)/('selection-'+row['case']+'-'+layout); root.mkdir()
            for name in contract.layout_files(record, layout):
                path = root/name; path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes((SOURCE/FIXTURES/layout/name).read_bytes())
            config = root/'tracker/config.json'; config.parent.mkdir(parents=True, exist_ok=True)
            config.write_text(json.dumps(row['config']))
            results.append(runner.exercise_selection(root, python, layout, row))
    return results


def exercise_all(python, tracker=None):
    record, provenance, artifacts, data = verified_artifacts()
    if tracker is not None:
        for name, row in provenance['files'].items():
            actual = subprocess.check_output(['git', '-C', str(tracker), 'show', record['engine']['revision']+':'+row['source']])
            assert artifacts[name] == actual, 'Copied native proof artifact differs from actual selected engine'
    runner = types.ModuleType('_canonical_tracker_portable_fixture')
    runner.__file__ = str(SOURCE/FIXTURES/'runner.py')
    exec(compile(artifacts['runner.py'], runner.__file__, 'exec'), runner.__dict__)
    results, accounting_results, direct_results, selection_results, process_results, pause_results = [], [], [], [], [], []
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
        direct_results = exercise_direct_cases(record, artifacts, runner, python, temporary)
        selection_results = exercise_selection_cases(record, artifacts, runner, python, temporary)
        if 'process.json' in artifacts:
            support = json.loads(artifacts['process.json'], object_pairs_hook=contract.unique)
            if support.get('schema_version') != 1 or support.get('synthetic') is not True or support.get('case') != 'canonical-support-main':
                raise ValueError('Canonical process fixture requires actual synthetic ordinary admission and completion')
            for layout in ('raw', 'separated'):
                root = Path(temporary)/('process-'+layout); root.mkdir()
                for name in contract.layout_files(record, layout):
                    path = root/name; path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_bytes((SOURCE/FIXTURES/layout/name).read_bytes())
                process_results.append(runner.exercise_support(root, python, layout, support))
        if 'pause.json' in artifacts:
            pause = json.loads(artifacts['pause.json'], object_pairs_hook=contract.unique)
            if pause.get('schema_version') != 1 or pause.get('synthetic') is not True:
                raise ValueError('Canonical pause fixture requires actual synthetic native histories')
            for layout in ('raw', 'separated'):
                root = Path(temporary)/('pause-'+layout); root.mkdir()
                for name in contract.layout_files(record, layout):
                    path = root/name; path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_bytes((SOURCE/FIXTURES/layout/name).read_bytes())
                pause_results.append(runner.exercise_pause(root, python, layout, pause))
    return {'engine': record['engine'], 'provenance': provenance, 'cases': results,
            'accounting': accounting_results, 'direct': direct_results, 'selection_delivery': selection_results,
            'process_support': process_results, 'task_pause': pause_results,
            'clock_fixture_only': True,
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
