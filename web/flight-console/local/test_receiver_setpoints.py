"""Exercise the actual wrapper over loopback, with serial explicitly disabled."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import urllib.request


class ReceiverWrapperTests(unittest.TestCase):
    def test_existing_receiver_exports_additive_schema_and_records_wrapper_provenance(self):
        with tempfile.TemporaryDirectory(prefix='gmfly_tracking_') as directory:
            process = subprocess.Popen([sys.executable, '-B', str(Path(__file__).with_name('receiver_setpoints.py')),
                                        '--no-serial', '--http-port', '0', '--logs', directory],
                                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            try:
                line = process.stdout.readline()
                self.assertTrue(line, 'offline receiver failed to start')
                started = json.loads(line)
                base = started['url']
                with urllib.request.urlopen(base + '/api/state', timeout=5) as response:
                    state = json.load(response)
                self.assertFalse(state['serial_writes'])
                self.assertFalse(state['fresh'])
                self.assertTrue(all(value is None for value in state['tracking'].values()))
                with urllib.request.urlopen(base + '/api/logs', timeout=5) as response:
                    self.assertIn('yaw_rate_sp_dps', json.load(response)['fields'])
                meta = json.loads((Path(directory) / started['session'] / 'meta.json').read_text(encoding='utf-8'))
                provenance = meta['reported_attitude_tracking']
                self.assertEqual(provenance['firmware'], 'B0B0')
                self.assertIn('attitude_tracking.py', provenance['software_sha256'])
                request = urllib.request.Request(base + '/api/service/stop', data=b'{}', headers={'Content-Type': 'application/json'})
                with urllib.request.urlopen(request, timeout=5):
                    pass
                process.communicate(timeout=8)
                self.assertEqual(process.returncode, 0)
            finally:
                if process.poll() is None:
                    process.terminate()
                    process.communicate(timeout=8)


if __name__ == '__main__':
    unittest.main()
