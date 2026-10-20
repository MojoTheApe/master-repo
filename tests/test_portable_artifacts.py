"""Validate the actual generated proof closure before public native execution."""
import copy
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import portable_contract_fixture as fixtures
from portable_contract_fixture import verified_artifacts


class PortableArtifacts(unittest.TestCase):
    def test_actual_canonical_artifacts_and_all_layout_contexts_are_bound(self):
        record, provenance, artifacts, data = verified_artifacts()
        self.assertEqual(len(data['contexts']), 8)
        modern = 'direct.json' in fixtures.fixture_sources(record)
        support = record.get('contracts', {}).get('process_support') == [1]
        raw_count = 11 + int(modern) + int(support)
        self.assertEqual(len(record['layouts']['raw']), raw_count)
        self.assertEqual(len(record['layouts']['separated']), raw_count * 2)
        self.assertEqual(provenance['engine'], record['engine'])
        self.assertIn(b'def exercise(', artifacts['runner.py'])
        self.assertIn('accounting.json', artifacts)
        self.assertEqual(len(fixtures.selection_cases(artifacts)), 4)
        self.assertIn(b'def exercise_selection(', artifacts['runner.py'])
        self.assertEqual(len(fixtures.direct_cases(artifacts)), 4 if modern else 0)
        if modern:
            self.assertIn(b'def exercise_direct(', artifacts['runner.py'])
        if support:
            self.assertIn('process.json', artifacts)
            self.assertIn(b'def exercise_support(', artifacts['runner.py'])

    def copied_source(self):
        temporary = tempfile.TemporaryDirectory(); self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        for name in ('compatibility.json', fixtures.contract.RECORD, fixtures.contract.SNAPSHOT):
            path = root/name; path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes((fixtures.SOURCE/name).read_bytes())
        shutil.copytree(fixtures.SOURCE/fixtures.FIXTURES, root/fixtures.FIXTURES)
        return root

    def test_changed_canonical_runner_is_refused_before_any_execution(self):
        root = self.copied_source()
        runner = root/fixtures.FIXTURES/'runner.py'
        runner.write_bytes(b'raise RuntimeError("Unverified runner executed")\n')
        before = {p:p.read_bytes() for p in root.rglob('*') if p.is_file()}
        with mock.patch.object(fixtures, 'SOURCE', root), mock.patch.object(fixtures.contract, 'SOURCE', root), \
                self.assertRaises(AssertionError):
            fixtures.verified_artifacts()
        self.assertEqual(before, {p:p.read_bytes() for p in root.rglob('*') if p.is_file()})

    def test_optional_closure_cannot_be_removed_or_added_by_provenance_alone(self):
        root = self.copied_source(); path = root/fixtures.FIXTURES/'provenance.json'
        value = json.loads(path.read_bytes())
        if 'direct.json' in value['files']:
            value['files'].pop('direct.json')
        else:
            value['files']['direct.json'] = {'source': 'tests/fixtures/portable_direct.json', 'sha256': 'a'*64}
        path.write_text(json.dumps(value))
        with mock.patch.object(fixtures, 'SOURCE', root), mock.patch.object(fixtures.contract, 'SOURCE', root), \
                self.assertRaises(AssertionError):
            fixtures.verified_artifacts()

    def test_modern_advertisement_without_canonical_provider_is_refused(self):
        # A malformed metadata negative, never a fabricated positive v4 export.
        _, record, _ = fixtures.contract.trusted()
        bad = copy.deepcopy(record); bad['contracts']['execution_policy'] = [1,2,3,4]
        bad.pop('route_validator', None)
        with self.assertRaisesRegex(ValueError, 'canonical route validator'):
            fixtures.fixture_sources(bad)

    def test_selection_closure_cannot_be_removed_from_provenance(self):
        root = self.copied_source(); path = root/fixtures.FIXTURES/'provenance.json'
        value = json.loads(path.read_bytes()); value['files'].pop('selection.json')
        path.write_text(json.dumps(value))
        with mock.patch.object(fixtures, 'SOURCE', root), mock.patch.object(fixtures.contract, 'SOURCE', root), \
                self.assertRaises(AssertionError):
            fixtures.verified_artifacts()

    def test_selection_envelope_requires_every_canonical_case_before_execution(self):
        _, _, artifacts, _ = verified_artifacts()
        original = json.loads(artifacts['selection.json'])
        for change in ('missing', 'duplicate', 'non-synthetic'):
            with self.subTest(change=change):
                bad = copy.deepcopy(original)
                if change == 'missing': bad['cases'].pop()
                elif change == 'duplicate': bad['cases'][-1] = bad['cases'][0]
                else: bad['synthetic'] = False
                with self.assertRaisesRegex(ValueError, 'all four exact synthetic cases'):
                    fixtures.selection_cases(dict(artifacts, **{'selection.json': json.dumps(bad).encode()}))


if __name__ == '__main__': unittest.main()
