"""Validate the actual generated proof closure before public native execution."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from portable_contract_fixture import verified_artifacts


class PortableArtifacts(unittest.TestCase):
    def test_actual_canonical_artifacts_and_all_layout_contexts_are_bound(self):
        record, provenance, artifacts, data = verified_artifacts()
        self.assertEqual(len(data['contexts']), 8)
        self.assertEqual(len(record['layouts']['raw']), 9)
        self.assertEqual(len(record['layouts']['separated']), 18)
        self.assertEqual(provenance['engine'], record['engine'])
        self.assertIn(b'def exercise(', artifacts['runner.py'])


if __name__ == '__main__': unittest.main()
