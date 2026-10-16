import os
from pathlib import Path
import sys
import tempfile
import time
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
import measure_verification as measure


@unittest.skipUnless(os.name == 'posix', 'POSIX measurement cleanup')
class Measurement(unittest.TestCase):
    def test_failed_reuse_is_never_reported_as_a_performance_result(self):
        with self.assertRaisesRegex(RuntimeError, 'no performance result'):
            measure.measure([sys.executable, '-c', 'pass'], [sys.executable, '-c', 'raise SystemExit(7)'], 1)

    def test_success_reports_observed_local_feedback_and_explicit_native_limit(self):
        value = measure.measure([sys.executable, '-c', 'pass'], [sys.executable, '-c', 'pass'], 2)
        self.assertEqual(len(value['rows']), 4)
        self.assertEqual([r['route'] for r in value['rows']], ['fresh', 'reuse', 'reuse', 'fresh'])
        self.assertIsNone(value['native_job_seconds'])
        self.assertTrue(all(r['cycle_seconds'] >= r['first_feedback_seconds'] > 0 for r in value['rows']))

    def test_timeout_stops_the_command_group(self):
        with tempfile.TemporaryDirectory() as scratch:
            pid = Path(scratch)/'pid'
            code = 'import os,time;from pathlib import Path;Path('+repr(str(pid))+').write_text(str(os.getpid()));time.sleep(30)'
            with self.assertRaisesRegex(RuntimeError, 'process group was stopped'):
                measure.measure([sys.executable, '-c', code], [sys.executable, '-c', 'pass'], 1, timeout=1)
            number = int(pid.read_text())
            with self.assertRaises(ProcessLookupError): os.kill(number, 0)

    def test_failed_command_cannot_leave_a_redirected_background_helper(self):
        with tempfile.TemporaryDirectory() as scratch:
            ready, leaked = Path(scratch)/'ready', Path(scratch)/'leaked'
            child = ('from pathlib import Path;import time;Path('+repr(str(ready))+').touch();'
                     'time.sleep(0.5);Path('+repr(str(leaked))+').touch()')
            parent = ('import subprocess,time;from pathlib import Path;'
                      'subprocess.Popen(['+repr(sys.executable)+',"-c",'+repr(child)+'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);'
                      'deadline=time.monotonic()+2\n'
                      'while not Path('+repr(str(ready))+').exists() and time.monotonic()<deadline: time.sleep(0.01)\n'
                      'raise SystemExit(7)')
            with self.assertRaisesRegex(RuntimeError, 'no performance result'):
                measure.measure([sys.executable, '-c', parent], [sys.executable, '-c', 'pass'], 1, 3)
            self.assertTrue(ready.exists())
            time.sleep(0.6)
            self.assertFalse(leaked.exists(), 'Background command survived failed measurement')
