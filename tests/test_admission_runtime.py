"""The own native gate must consume the exact portable canonical runtime."""
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import check_admission


class AdmissionRuntimeTests(unittest.TestCase):
    def test_actual_compatible_adapter_loads_without_private_engine_or_network(self):
        result = subprocess.run([sys.executable, '-I', str(ROOT / 'scripts/check_admission.py'), '--help'],
                                text=True, capture_output=True, cwd=ROOT)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('--check-only', result.stdout)
        self.assertIn('--admission-policy', result.stdout)

    def test_changed_portable_code_is_rejected_before_import(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = pathlib.Path(temporary) / 'runtime'
            shutil.copytree(check_admission.RUNTIME, root)
            target = root / 'scripts/tracker_pr_check.py'
            target.write_bytes(target.read_bytes() + b'\nraise RuntimeError("candidate code executed")\n')
            with mock.patch.object(check_admission, 'RUNTIME', root):
                with self.assertRaisesRegex(ValueError, 'Trusted admission runtime differs'):
                    check_admission.runtime()


if __name__ == '__main__':
    unittest.main()
