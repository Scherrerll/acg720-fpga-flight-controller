"""Offline observer proof: all HTTP/process boundaries mocked; never touches a device."""
from pathlib import Path
import contextlib
import copy
import importlib.util
import io
import json
import sys
import unittest
from unittest.mock import Mock, patch

SPEC = importlib.util.spec_from_file_location('cold_b0b4_under_test', Path(__file__).with_name('observe_cold_b0b4.py'))
o = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(o)
OUT = None
for argument in list(sys.argv[1:]):
    if argument.startswith('--output='):
        OUT = Path(argument.removeprefix('--output=')).resolve(); sys.argv.remove(argument)


def state(sequence=8, uptime=500000, count=1000):
    return dict(connected=True, fresh=True, flight_info_fresh=True, status='live', port='COM17',
                ui_version='flight-console.20261026.b0b4.xy-pi.v1', sequence=sequence,
                source=dict(port='COM17', source='SiK', baud=115200),
                flight_info=dict(build_id=0xB0B2, taking_off=False, sequence=sequence, uptime_ms=uptime),
                imu_diagnostic_fresh=True,
                imu_diagnostic=dict(build_id=0xB0B2, sequence=sequence, raw_count=count+2,
                                    accepted_count=count+1, pose_count=count),
                data=dict(armed=False, controller_enabled=False, command_fresh=False, physical_output_active=False,
                          calibrated=True, attitude_valid=True, sensor_ok=True, pwm_us=[1000]*4, command_us=[1000]*4,
                          rc_valid=True, rc_us=[1500,1500,1000,1500,1000,1500,1000,1500]))


class Clock:
    def __init__(self): self.now = 0.0
    def monotonic(self): return self.now
    def sleep(self, duration): self.now += duration


class Boundaries(unittest.TestCase):
    def setUp(self):
        self.clock = Clock()
        self.enterContext(patch.object(o.time, 'monotonic', self.clock.monotonic))
        self.enterContext(patch.object(o.time, 'sleep', self.clock.sleep))
        self.http = self.enterContext(patch.object(o.b, 'http', side_effect=AssertionError('HTTP must be mocked explicitly')))
        self.enterContext(patch.object(o.b.subprocess, 'Popen', side_effect=AssertionError('No subprocess permitted')))
        self.enterContext(patch.object(o.b.urllib.request, 'urlopen', side_effect=AssertionError('No network permitted')))
        self.output = self.enterContext(contextlib.redirect_stdout(io.StringIO()))

    def folder(self, name):
        path = OUT/name; path.mkdir(exist_ok=False); return path

    def receipt(self, name):
        folder = self.folder(name)
        operations = []
        for number, label in o.OPERATIONS:
            args = [str(o.b.CLI), '--device', 'GW5AT-60B', '--cable-index', '1', '--location', '292', '--run', str(number)]
            if number in (54, 66): args += ['--spiaddr', '0x000000', '--fsFile', str(o.b.IMAGE)]
            operations.append(dict(operation=number, label=label, args=args))
        report = dict(schema='b0b4.bench-stage.v1', stage='flash', passed=True, flash_written=True,
                      flash_contents_certified=True, independent_flash_verify_passed=True,
                      script_sha256=o.FLASH_SHA, image_sha256=o.IMAGE_SHA, manifest_sha256=o.b.MANIFEST_SHA,
                      operations=operations)
        labels = ['qualification'] + [label+suffix for _, label in o.OPERATIONS for suffix in ('_cables', '')]
        for label in labels:
            child = dict(normal_wait_return=True, actual_p_wait=0)
            for stream in ('stdout', 'stderr'):
                log = folder/(label+'_'+stream+'.log'); log.write_text('Mock only.\n', encoding='utf-8')
                child[stream+'_sha256'] = o.b.sha(log)
            match = [item for item in operations if item['label'] == label]
            if match: child['args'] = match[0]['args']
            o.b.save(folder/(label+'_exit.json'), child)
        path = folder/'stage_report.json'; o.b.save(path, report)
        root = folder/'root_exit.json'; self.rebind_root(path, root)
        return path, root

    def rebind_root(self, path, root):
        o.b.save(root, dict(normal_wait_return=True, actual_p_wait=0, stage_report=str(path), stage_report_sha256=o.b.sha(path)))

    def observer(self, name, duration=600):
        receipt, root = self.receipt(name+'_flash')
        return o.Observer(self.folder(name), receipt, root, duration)

    def simulated_server(self, states, statuses=None, query_operation=5):
        states = list(states); last = states[-1]
        statuses = iter(statuses or [dict(busy=False, epoch=7, operation_id=4),
                                    dict(busy=False, can_query=True, epoch=8, operation_id=None),
                                    dict(busy=False, epoch=8, operation_id=5, supported=True,
                                         active=dict(build='0000B0B4', p_wire=1000, i_wire=350, generation=0),
                                         result=dict(code='queried', operation_id=5))])
        def server(path, body=None, token=None):
            nonlocal last
            if path == '/api/state':
                if states: last = states.pop(0)
                if isinstance(last, BaseException): raise last
                return copy.deepcopy(last)
            if path == '/api/xy-pi/status': return copy.deepcopy(next(statuses))
            if path == '/api/xy-pi/session': return dict(token='SECRET-MOCK-ONLY', unused='SECRET-MOCK-ONLY')
            if path == '/api/xy-pi/query':
                self.assertEqual(token, 'SECRET-MOCK-ONLY')
                self.assertEqual(set(body), {'request_id', 'epoch'})
                self.assertEqual(body['epoch'], 8)
                return dict(operation_id=query_operation)
            raise AssertionError('Outside read/query route whitelist: '+path)
        self.http.side_effect = server

    def boot_states(self):
        stale = state(); stale.update(connected=False, fresh=False, flight_info_fresh=False, status='stale')
        return [state(), stale] + [state(20+n, 100+n*200, 50+n*20) for n in range(13)]

    def test_default_is_offline_with_no_http_process_or_serial(self):
        o.main([])
        self.http.assert_not_called()
        value = json.loads(self.output.getvalue())
        self.assertTrue(value['offline']); self.assertFalse(value['http_accessed'])
        self.assertFalse(value['physical_cold_boot_verified']); self.assertFalse(value['flight_ready'])

    def test_receipt_requires_root_zero_stage_hash_and_all_actual_child_zero(self):
        path, root = self.receipt('receipt_boundaries')
        self.assertEqual(o.flash_evidence(path, root)['actual_p_wait'], 0)
        original = json.loads(root.read_text())
        for bad in (False, True, 1, None, '0'):
            changed = dict(original, actual_p_wait=bad); o.b.save(root, changed)
            with self.subTest(root_wait=bad), self.assertRaises(ValueError): o.flash_evidence(path, root)
        o.b.save(root, original)
        child_path = path.parent/'08_B0B4_independent_verify_exit.json'
        child = json.loads(child_path.read_text()); o.b.save(child_path, dict(child, actual_p_wait=1))
        with self.assertRaises(ValueError): o.flash_evidence(path, root)
        o.b.save(child_path, child)
        (path.parent/'04_B0B4_program_verify_stdout.log').write_text('changed', encoding='utf-8')
        with self.assertRaises(ValueError): o.flash_evidence(path, root)
        self.http.assert_not_called()

    def test_false_flash_certification_and_wrong_image_rejected_before_http(self):
        for key, bad in (('passed', False), ('flash_contents_certified', False),
                         ('independent_flash_verify_passed', False), ('image_sha256', 'wrong'),
                         ('script_sha256', 'wrong')):
            observer = self.observer('bad_'+key)
            report = json.loads(observer.receipt.read_text()); report[key] = bad
            o.b.save(observer.receipt, report); self.rebind_root(observer.receipt, observer.root_receipt)
            with self.subTest(key=key), self.assertRaises(ValueError): observer.run()
        self.http.assert_not_called()

    def test_healthy_boot_new_GET_and_no_secret_or_raw_stream_persistence(self):
        observer = self.observer('success'); self.simulated_server(self.boot_states())
        result = observer.run()
        self.assertTrue(all(result[k] for k in ('passed', 'pass', 'observed_stale_or_offline', 'uptime_reset', 'healthy_new_boot', 'default_GET')))
        self.assertFalse(result['physical_cold_boot_verified']); self.assertFalse(result['flight_ready'])
        self.assertEqual(len(result['healthy_new_boot_samples']), 10)
        self.assertEqual(result['final_health'], dict(calibrated=True, attitude_valid=True, sensor_ok=True))
        self.assertIn('BASELINE_READY', self.output.getvalue())
        query_calls = [call for call in self.http.call_args_list if call.args[0] == '/api/xy-pi/query']
        self.assertEqual(len(query_calls), 1)
        for path in observer.folder.iterdir():
            content = path.read_text(encoding='utf-8')
            self.assertNotIn('SECRET-MOCK-ONLY', content); self.assertNotIn('packet_hex', content)
        samples = result['healthy_new_boot_samples']
        for first, second in zip(samples, samples[1:]):
            self.assertGreater(second['uptime_ms'], first['uptime_ms'])
            for key in o.COUNTERS: self.assertGreater(second[key], first[key])
            self.assertEqual(second['sequence'], second['info_sequence'])

    def test_exact_same_group_retry_recovers_and_is_bounded(self):
        observer = self.observer('same_group')
        mismatch = state(); mismatch['flight_info']['sequence'] -= 1
        self.http.side_effect = [mismatch, state()]
        self.assertEqual(observer.read_stopped()['sequence'], 8)
        self.assertEqual(self.http.call_count, 2)
        self.http.reset_mock(); self.http.side_effect = None; self.http.return_value = mismatch
        started = self.clock.now
        with self.assertRaisesRegex(ValueError, '^Same-group telemetry required$'): observer.read_stopped()
        self.assertLessEqual(self.clock.now-started, 3.051)

    def test_boot_receiver_unready_waits_only_after_boot_evidence(self):
        observer = self.observer('startup_rc')
        values = self.boot_states()
        unready = state(9, 20, 1); unready['data'].update(rc_valid=False, rc_us=[0]*8)
        values.insert(2, unready)
        self.simulated_server(values)
        self.assertTrue(observer.run()['passed'])
        self.assertIn('startup_wait', (observer.folder/'samples.jsonl').read_text())
        second = self.observer('baseline_rc_unready'); self.http.return_value = unready; self.http.side_effect = None
        with self.assertRaisesRegex(ValueError, 'Complete live RC required'): second.run()
        self.http.reset_mock()
        high = state(9, 20, 1); high['data']['rc_us'][2] = 1600
        third = self.observer('startup_high_switch')
        self.simulated_server([state(), values[1], high])
        with self.assertRaisesRegex(ValueError, 'CH3/5/7'): third.run()
        self.assertFalse(any(c.args[0] == '/api/xy-pi/query' for c in self.http.call_args_list))

    def test_startup_whitelist_never_swallows_wrong_owner_schema_or_identity(self):
        for label, mutate in (('wrong_owner', lambda v: v.update(port='COM18')),
                              ('wrong_identity', lambda v: v['flight_info'].update(build_id=0xB0B4)),
                              ('missing_stop_field', lambda v: v['data'].pop('armed')),
                              ('missing_rc_valid', lambda v: v['data'].pop('rc_valid'))):
            observer = self.observer(label)
            values = self.boot_states()
            startup = state(9, 20, 1); startup['data'].update(rc_valid=False, rc_us=[0]*8); mutate(startup)
            self.simulated_server([values[0], values[1], startup])
            with self.subTest(label=label), self.assertRaises(ValueError): observer.run()
            self.assertFalse(any(c.args[0] == '/api/xy-pi/query' for c in self.http.call_args_list))
            self.http.reset_mock()

    def test_other_errors_and_unsafe_activity_abort_without_retry_or_query(self):
        observer = self.observer('strict_errors')
        invalid = state(); invalid['data']['rc_us'][2] = 1600
        self.http.return_value = invalid; self.http.side_effect = None
        with self.assertRaisesRegex(ValueError, 'CH3/5/7'): observer.read_stopped()
        self.assertEqual(self.http.call_count, 1); self.assertEqual(self.clock.now, 0)
        self.http.reset_mock()
        active = state(); active['flight_info']['sequence'] -= 1; active['data']['armed'] = True
        self.simulated_server([state(), active])
        with self.assertRaises(o.b.UnsafeActivity): observer.run()
        self.assertFalse(observer.record['passed'])
        self.assertFalse(any(c.args[0] == '/api/xy-pi/query' for c in self.http.call_args_list))

    def test_ten_healthy_distinct_advancing_samples_required(self):
        for label, mutate in (('uncalibrated', lambda v: v['data'].update(calibrated=False)),
                              ('stale_diagnostic', lambda v: v.update(imu_diagnostic_fresh=False)),
                              ('frozen_counters', lambda v: v['imu_diagnostic'].update(raw_count=20, accepted_count=20, pose_count=20))):
            observer = self.observer(label, duration=3)
            values = self.boot_states()
            for value in values[2:]: mutate(value)
            self.simulated_server(values)
            with self.subTest(label=label), self.assertRaises(TimeoutError): observer.run()
            self.assertFalse(observer.record['healthy_new_boot'])
            self.assertFalse(any(c.args[0] == '/api/xy-pi/query' for c in self.http.call_args_list))
            self.http.reset_mock()

    def test_new_epoch_and_new_operation_and_B4_defaults_required(self):
        for label, status_changes, query_op in (('old_epoch', {'epoch': 7}, 5),
                                               ('old_operation', {}, 4),
                                               ('wrong_build', {'active': dict(build='0000B0B3', p_wire=1000, i_wire=350, generation=0)}, 5),
                                               ('wrong_generation', {'active': dict(build='0000B0B4', p_wire=1000, i_wire=350, generation=1)}, 5)):
            observer = self.observer(label)
            before = dict(busy=False, epoch=7, operation_id=4)
            current = dict(busy=False, can_query=True, epoch=8, operation_id=None)
            final = dict(busy=False, epoch=8, operation_id=5, supported=True,
                         active=dict(build='0000B0B4', p_wire=1000, i_wire=350, generation=0),
                         result=dict(code='queried', operation_id=5))
            if label == 'old_epoch': current.update(status_changes)
            else: final.update(status_changes)
            self.simulated_server(self.boot_states(), [before, current, final], query_op)
            with self.subTest(label=label), self.assertRaises(ValueError): observer.run()
            self.assertFalse(observer.record['default_GET']); self.assertFalse(observer.record['passed'])
            self.http.reset_mock()

    def test_timeout_offline_and_no_uptime_reset_never_pass(self):
        for label, tail in (('offline_forever', OSError('external error text not persisted')),
                            ('never_reset', state(30, 600000, 2000))):
            observer = self.observer(label, duration=1)
            self.simulated_server([state(), tail])
            with self.subTest(label=label), self.assertRaises(TimeoutError): observer.run()
            self.assertFalse(observer.record['passed']); self.assertFalse(observer.record['uptime_reset'])
            self.assertFalse(any(c.args[0] == '/api/xy-pi/query' for c in self.http.call_args_list))
            self.assertNotIn('external error text', (observer.folder/'samples.jsonl').read_text())
            self.http.reset_mock()


if __name__ == '__main__':
    if OUT is None or not OUT.is_relative_to((o.b.DEFAULT_OUT/'offline_cold').resolve()):
        raise SystemExit('Use --output=ABSOLUTE_NEW_DIR under out/b0b4_install_20261028/offline_cold')
    OUT.mkdir(parents=True, exist_ok=False)
    unittest.main()
