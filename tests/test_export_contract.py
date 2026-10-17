"""Observable trust-boundary tests; real portable export execution uses the paired gate."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
import export_contract as contract

SOURCE = Path(__file__).resolve().parents[1]


class TrustedExport(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(); self.addCleanup(temp.cleanup)
        self.source = Path(temp.name)/'action'; self.source.mkdir()
        self.root = Path(temp.name)/'consumer'; self.root.mkdir()
        self.patch = mock.patch.object(contract, 'SOURCE', self.source)
        self.patch.start(); self.addCleanup(self.patch.stop)
        self.helper = '.workflow/tools/tracker_ci_gate.py'
        self.raw_helper = b'# Synthetic hash-boundary fixture; never a real export proof.\n'
        self.snapshot = (SOURCE/'scripts/vendor/tracker_ci_evidence.py').read_bytes()
        self.retry_snapshot = (SOURCE/'scripts/vendor/tracker_ci_retry.py').read_bytes()
        self.record = {'format_version': 1,
            'engine': {'repository': 'MojoTheApe/task-tracker', 'revision': 'a'*40},
            'runtime': {'engine_min_python': '3.11', 'portable_min_python': '3.9'},
            'validator': {'source': 'tracker/ci_evidence.py', 'sha256': hashlib.sha256(self.snapshot).hexdigest()},
            'retry_validator': {'source': 'tracker/ci_retry.py', 'sha256': hashlib.sha256(self.retry_snapshot).hexdigest()},
            'contracts': {'delivery_policy': [1], 'execution_policy': [1,2,3], 'ci_evidence_policy': [1,2], 'ci_retry_policy': [1]},
            'layouts': {'separated': {self.helper: hashlib.sha256(self.raw_helper).hexdigest()}}}
        self.write(self.source, contract.SNAPSHOT, self.snapshot)
        self.write(self.source, contract.RETRY_SNAPSHOT, self.retry_snapshot)
        self.set_trust(self.record)
        self.write(self.root, self.helper, self.raw_helper)
        self.descriptor = {'workflow': {'execution': {'schema_version': 3}}}

    def write(self, root, path, raw):
        p = root/path; p.parent.mkdir(parents=True, exist_ok=True); p.write_bytes(raw)

    def set_trust(self, record):
        raw = (json.dumps(record, sort_keys=True, indent=2)+'\n').encode()
        self.write(self.source, contract.RECORD, raw)
        self.write(self.root, contract.MANIFEST, raw)
        self.write(self.source, 'compatibility.json', json.dumps(dict(tracker_repository='MojoTheApe/task-tracker',
            tracker_revision='a'*40, export_contract=1, export_contract_sha256=hashlib.sha256(raw).hexdigest())).encode())

    def test_matching_installed_and_rendered_bytes_pass_without_writes(self):
        before = {p:p.read_bytes() for p in self.source.parent.rglob('*') if p.is_file()}
        contract.validate_root(self.root, self.descriptor)
        files = {contract.MANIFEST:(self.root/contract.MANIFEST).read_text(), self.helper:self.raw_helper.decode()}
        contract.validate_rendered(files, self.descriptor)
        self.assertEqual(before, {p:p.read_bytes() for p in self.source.parent.rglob('*') if p.is_file()})

    def test_rehashed_consumer_tampering_cannot_establish_trust(self):
        changed = b'# A changed consumer helper.\n'
        self.write(self.root, self.helper, changed)
        with self.assertRaisesRegex(ValueError, 'helper bytes differ'):
            contract.validate_root(self.root, self.descriptor)
        forged = copy.deepcopy(self.record)
        forged['layouts']['separated'][self.helper] = hashlib.sha256(changed).hexdigest()
        self.write(self.root, contract.MANIFEST, json.dumps(forged).encode())
        with self.assertRaisesRegex(ValueError, 'trusted compatible source record'):
            contract.validate_root(self.root, self.descriptor)

    def test_invalid_future_or_duplicate_format_fails_clearly(self):
        for raw in (b'{"format_version":2}', b'{"format_version":true}',
                    b'{"format_version":1,"format_version":1}', b'not json'):
            self.write(self.root, contract.MANIFEST, raw)
            with self.assertRaises(ValueError):
                contract.validate_root(self.root, self.descriptor)

    def test_poisoned_consumer_validator_is_never_loaded(self):
        poison = b'raise AssertionError("Consumer code executed")\n'
        for path in ('tracker_ci_evidence.py', 'scripts/vendor/tracker_ci_evidence.py'):
            self.write(self.root, path, poison)
        fake = types.ModuleType('_master_trusted_tracker_ci_evidence')
        fake.policy = mock.Mock(side_effect=AssertionError('Cached consumer module executed'))
        with mock.patch.dict(sys.modules, {'_master_trusted_tracker_ci_evidence': fake}), \
                mock.patch('subprocess.run', side_effect=AssertionError('Unexpected process')), \
                mock.patch('subprocess.check_output', side_effect=AssertionError('Unexpected process')), \
                mock.patch('socket.socket', side_effect=AssertionError('Unexpected network')):
            self.assertIsNone(contract.structural_policy({}))
            self.assertEqual(contract.structural_policy({'ci_evidence_policy': {'schema_version': 2,
                'profiles': {'checks': {'workflow_path': '.github/workflows/test.yml', 'workflow_blob_sha': 'b'*40,
                'producer_files': {'scripts/producer.py': 'c'*40}, 'metadata_mode': 'tree',
                'max_age_seconds': 100, 'jobs': {'Fresh checks': {'mode': 'fresh'}}}}}})['schema_version'], 2)
        self.assertFalse(fake.policy.called)
        self.assertFalse((self.source/'scripts/vendor/__pycache__').exists())

    def test_changed_trusted_snapshot_is_refused_before_execution(self):
        self.write(self.source, contract.SNAPSHOT, b'raise AssertionError("Changed snapshot executed")\n')
        with self.assertRaisesRegex(ValueError, 'reviewed Tracker snapshot'):
            contract.structural_policy({})

    def test_retry_uses_verified_fixed_snapshot_without_consumer_import_or_side_effect(self):
        poison = b'raise AssertionError("Consumer retry validator executed")\n'
        for path in ('tracker_ci_retry.py', 'scripts/vendor/tracker_ci_retry.py'):
            self.write(self.root, path, poison)
        cached = types.ModuleType('_master_trusted_tracker_ci_retry')
        cached.policy = mock.Mock(side_effect=AssertionError('Cached retry validator executed'))
        before = {p:p.read_bytes() for p in self.source.parent.rglob('*') if p.is_file()}
        with mock.patch.dict(sys.modules, {'_master_trusted_tracker_ci_retry': cached}), \
                mock.patch('subprocess.run', side_effect=AssertionError('Unexpected process')), \
                mock.patch('subprocess.check_output', side_effect=AssertionError('Unexpected process')), \
                mock.patch('socket.socket', side_effect=AssertionError('Unexpected network')):
            self.assertIsNone(contract.structural_retry_policy({}))
            for limit in (1, 2):
                policy = {'schema_version': 1, 'max_executions': limit}
                self.assertEqual(contract.structural_retry_policy({'ci_retry_policy': policy}), policy)
            with self.assertRaises(ValueError):
                contract.structural_retry_policy({'ci_retry_policy': {'schema_version': True, 'max_executions': 2}})
        self.assertFalse(cached.policy.called)
        self.assertEqual(before, {p:p.read_bytes() for p in self.source.parent.rglob('*') if p.is_file()})

    def test_changed_or_redirected_retry_snapshot_fails_before_execution(self):
        self.write(self.source, contract.RETRY_SNAPSHOT, b'raise AssertionError("Changed retry source executed")\n')
        with self.assertRaisesRegex(ValueError, 'reviewed Tracker snapshot'):
            contract.structural_retry_policy({})
        self.write(self.source, contract.RETRY_SNAPSHOT, self.retry_snapshot)
        forged = copy.deepcopy(self.record)
        forged['retry_validator']['source'] = 'consumer/validator.py'
        self.set_trust(forged)
        with self.assertRaisesRegex(ValueError, 'reviewed Tracker snapshot'):
            contract.structural_retry_policy({})

    def test_missing_linked_and_unsafe_helpers_are_rejected(self):
        helper = self.root/self.helper; helper.unlink()
        with self.assertRaisesRegex(ValueError, 'Missing export contract file'):
            contract.validate_root(self.root, self.descriptor)
        target = self.root/'outside.py'; target.write_bytes(self.raw_helper)
        helper.symlink_to(target)
        with self.assertRaisesRegex(ValueError, 'Unsafe export contract file'):
            contract.validate_root(self.root, self.descriptor)
        for path in ('/outside.py', '../outside.py', 'C:/outside.py', 'a\\b.py', 'a/./b.py'):
            with self.assertRaises(ValueError): contract.safe_file(self.root, path)

    def test_unsupported_selection_and_mismatched_engine_fail(self):
        self.descriptor['workflow']['execution']['schema_version'] = 4
        with self.assertRaisesRegex(ValueError, 'unsupported by the pinned export'):
            contract.validate_root(self.root, self.descriptor)
        changed = copy.deepcopy(self.record); changed['engine']['revision'] = 'b'*40
        self.set_trust(changed)
        with self.assertRaisesRegex(ValueError, 'immutable compatible Tracker pin'):
            contract.validate_root(self.root, self.descriptor)


if __name__ == '__main__': unittest.main()
