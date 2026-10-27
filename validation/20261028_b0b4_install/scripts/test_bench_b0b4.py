"""Offline boundary checks only; every HTTP/programmer boundary is mocked."""
from pathlib import Path
import copy
import importlib.util
import json
import sys
import unittest
from unittest.mock import Mock, patch

SPEC = importlib.util.spec_from_file_location('bench_b0b4_under_test', Path(__file__).with_name('bench_b0b4.py'))
b = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(b)
OUT = Path(sys.argv.pop()) if len(sys.argv) > 1 and sys.argv[-1].startswith('--output=') else None
if OUT is not None:
    OUT = Path(str(OUT).removeprefix('--output='))


def state():
    return dict(connected=True, fresh=True, flight_info_fresh=True, status='live', port='COM17',
                ui_version='flight-console.20261026.b0b4.xy-pi.v1', sequence=8,
                source=dict(port='COM17', source='SiK', baud=115200),
                flight_info=dict(build_id=0xB0B2, taking_off=False, sequence=8),
                data=dict(armed=False, controller_enabled=False, command_fresh=False, physical_output_active=False,
                          pwm_us=[1000]*4, command_us=[1000]*4, rc_valid=True,
                          rc_us=[1500, 1500, 1000, 1500, 1000, 1500, 1000, 1500]))


class Boundaries(unittest.TestCase):
    def folder(self, name):
        path = OUT / name; path.mkdir(exist_ok=False); return path

    def test_stopped_guard_and_unsafe_activity(self):
        self.assertIs(b.stopped(state()).get('fresh'), True)
        for key in ('armed', 'controller_enabled', 'command_fresh', 'physical_output_active'):
            value = state(); value['data'][key] = True
            with self.subTest(key=key), self.assertRaises(b.UnsafeActivity): b.stopped(value)
        for index in (2, 4, 6):
            value = state(); value['data']['rc_us'][index] = 1600
            with self.assertRaises(ValueError): b.stopped(value)
        value = state(); value['fresh'] = False
        with self.assertRaises(ValueError): b.stopped(value)

    def test_operation_whitelist_and_fixed_image_at_boundary(self):
        s = b.Session('sram', self.folder('operations')); s.bind = Mock(return_value=292)
        s.guard = Mock(return_value=state()); s.child = Mock(return_value='Finished.\n')
        for operation in (1, 54, 66, True, '2', -1):
            with self.subTest(operation=operation), self.assertRaises(ValueError): s.operation(operation, 'reject')
        s.child.assert_not_called()
        with patch.object(b, 'offline', return_value={'passed': True}), patch.object(b, 'sha', return_value=b.IMAGE_SHA):
            s.operation(2, 'allowed_sram')
        command = s.child.call_args.args[0]
        self.assertEqual(command, [str(b.CLI), '--device', 'GW5AT-60B', '--cable-index', '1', '--location', '292',
                                   '--run', '2', '--fsFile', str(b.IMAGE)])
        s.child.reset_mock()
        with patch.object(b, 'offline', return_value={'passed': True}), patch.object(b, 'sha', return_value='changed'):
            with self.assertRaises(ValueError): s.operation(2, 'reject_changed_image')
        s.child.assert_not_called()

    def test_GET_polling_busy_and_no_token_persistence(self):
        s = b.Session('sram', self.folder('GET')); s.guard = Mock(return_value=state())
        secret = 'mock-token-never-saved'
        calls = []; statuses = iter([
            dict(can_query=True, epoch=7), dict(busy=True, epoch=7, operation_id=9),
            dict(busy=False, epoch=7, operation_id=9, supported=True,
                 active=dict(build='0000B0B4', p_wire=1000, i_wire=350, generation=0),
                 result=dict(code='queried', operation_id=9))])
        def fake_http(path, body=None, token=None):
            calls.append((path, body, token))
            if path == '/api/state': return state()
            if path == '/api/xy-pi/status': return next(statuses)
            if path == '/api/xy-pi/session': return dict(token=secret)
            if path == '/api/xy-pi/query':
                self.assertEqual(token, secret); return dict(operation_id=9)
            raise AssertionError('HTTP route not allowed')
        with patch.object(b, 'http', side_effect=fake_http), patch.object(b.time, 'sleep'):
            self.assertEqual(s.defaults('fresh_GET')['active']['generation'], 0)
        self.assertEqual(len([c for c in calls if c[0] == '/api/xy-pi/query']), 1)
        self.assertEqual(s.guard.call_count, 1)
        self.assertNotIn(secret, (s.folder/'fresh_GET.json').read_text())
        with self.assertRaises(ValueError): b.http('/api/xy-pi/set', {}, secret)


if __name__ == '__main__':
    if OUT is None: raise SystemExit('Use --output=ABSOLUTE_NEW_TEST_DIR')
    OUT.mkdir(parents=True, exist_ok=False)
    unittest.main()
