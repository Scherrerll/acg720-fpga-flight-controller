"""Installer fail-closed proof using temporary artifacts and mocked hardware only."""
from pathlib import Path
import importlib.util
import json
import subprocess
import tempfile
import unittest
from unittest import mock

SPEC = importlib.util.spec_from_file_location('b0b1_install_sram', Path(__file__).resolve().parents[1] / 'tools/install_sram.py')
installer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(installer)


class InstallerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name).resolve()
        self.root = self.base / 'firmware/B0B1'
        self.source = self.root / 'source'
        self.build = self.base / 'build'
        self.fixture = self.build / 'fixture'
        self.source.mkdir(parents=True)
        (self.root / 'tools').mkdir()
        (self.root / 'tools/build.py').write_text('current auditor\n')
        (self.source / 'top.v').write_text('module top; endmodule\n')
        (self.source / 'build.tcl').write_text('open_project top.gprj\nset_option -route_option 1\nrun all\nexit\n')
        (self.source / 'top.gprj').write_text('<Project/>\n')
        self.fixture.mkdir(parents=True)
        for p in self.source.iterdir():
            (self.fixture / p.name).write_bytes(p.read_bytes())
        (self.fixture / 'build.tcl').write_text('open_project top.gprj\nset_option -route_option 2\nset_option -route_maxfan 23\nrun all\nexit\n')
        self.pnr = self.fixture / 'impl/pnr'
        self.pnr.mkdir(parents=True)
        self.image = self.pnr / 'acg720_ano_port.fs'
        self.image.write_text('// UserCode: 0x0000B0B1\nmock bitstream\n')
        (self.pnr / 'acg720_ano_port.tr').write_text('mock timing report\n')
        (self.build / 'build_runner.py').write_text('actual archived builder\n')
        self.inputs = dict(source_root=str(self.source),
                           source_sha256={p.name: installer.sha(p) for p in self.fixture.iterdir() if p.is_file()},
                           runner_sha256=installer.sha(self.build / 'build_runner.py'), options={'user_code': '0000B0B1'})
        self.write('inputs.json', self.inputs)
        self.result = dict(passed=True, routing_passed=True, timing_passed=True, identity_passed=True,
                           pin_contract_passed=True, vendor_returncode=0, errors=[], unrouted_nets=0,
                           audit_runner_sha256=installer.sha(self.root / 'tools/build.py'),
                           inputs_sha256=installer.sha(self.build / 'inputs.json'))
        self.write('tests_receipt.json', {'passed': True, 'mocked_hardware': True})
        self.rebind_outputs()
        self.root_patch = mock.patch.object(installer, 'ROOT', self.root)
        self.root_patch.start()
        self.addCleanup(self.root_patch.stop)

    def write(self, name, value):
        (self.build / name).write_text(json.dumps(value, sort_keys=True) + '\n')

    def rebind_outputs(self):
        self.result['outputs_sha256'] = {p.relative_to(self.build).as_posix(): installer.sha(p) for p in self.pnr.iterdir()}
        self.result['bitstream'] = dict(path=str(self.image), sha256=installer.sha(self.image))
        self.write('result.json', self.result)
        self.acceptance = dict(schema='b0b1.offline-acceptance.v1', passed=True, build_id=0xb0b1,
                               result_sha256=installer.sha(self.build / 'result.json'),
                               inputs_sha256=installer.sha(self.build / 'inputs.json'), bitstream_sha256=installer.sha(self.image),
                               test_receipt=dict(path='tests_receipt.json', sha256=installer.sha(self.build / 'tests_receipt.json')))
        self.write('offline_acceptance.json', self.acceptance)

    @staticmethod
    def safe_state(build=0xb0b0):
        return dict(fresh=True, flight_info_fresh=True, status='live', serial_writes=False,
                    flight_info={'build_id': build}, data=dict(armed=False, controller_enabled=False,
                    physical_output_active=False, pwm_us=[1000]*4, command_us=[1000]*4, rc_valid=True,
                    rc_us=[1500,1500,1000,1500,1000,1000,1000,1000]))

    def hardware(self, mutate=None, pre=0xb0b0, post=0xb0b1, fail_write=False, device=0x1481b):
        self.operations = []

        def run(args, **kwargs):
            self.assertEqual(args[1:5], ['--device', 'GW5AT-60B', '--cable-index', '1'])
            self.assertEqual(kwargs['timeout'], 120)
            op = int(args[args.index('--run')+1])
            self.assertIn(op, (0, 2))
            self.operations.append(op)
            if op == 2:
                self.assertEqual(args[-2:], ['--fsFile', str(self.image)])
                if fail_write:
                    raise subprocess.TimeoutExpired(args, 120, output='partial output')
                text = 'SRAM programmed\nFinished.\n'
            else:
                code = pre if len(self.operations) == 1 else post
                text = f'ID Code is: 0x{device:08X}\nUser Code is: 0x{code:08X}\nFinished.\n'
            if mutate:
                mutate(op)
            return subprocess.CompletedProcess(args, 0, text, '')

        for name, value in [('programmers', [dict(vid=0x403, pid=0x6014, serial='5', device='mock')]),
                            ('state', self.safe_state())]:
            patcher = mock.patch.object(installer, name, return_value=value)
            patcher.start()
            self.addCleanup(patcher.stop)
        patcher = mock.patch.object(installer.subprocess, 'run', side_effect=run)
        patcher.start()
        self.addCleanup(patcher.stop)

    def receipt(self):
        folders = sorted(self.build.glob('hardware_*'))
        return json.loads((folders[-1] / 'report.json').read_text())

    def test_default_is_offline_only(self):
        with mock.patch.object(installer, 'state', side_effect=AssertionError('network accessed')), \
             mock.patch.object(installer, 'programmers', side_effect=AssertionError('inventory accessed')), \
             mock.patch.object(installer.subprocess, 'run', side_effect=AssertionError('programmer accessed')):
            result = installer.install(self.build)
        self.assertTrue(result['passed'])
        self.assertFalse(result['hardware_accessed'])
        self.assertEqual(list(self.build.glob('hardware_*')), [])

    def test_program_requires_current_operator_flag(self):
        self.hardware()
        with self.assertRaisesRegex(ValueError, 'Current human'):
            installer.install(self.build, program=True)
        self.assertEqual(self.operations, [])
        self.assertFalse(self.receipt()['hardware_accessed'])

    def test_normal_sequence_and_receipt(self):
        self.hardware()
        result = installer.install(self.build, program=True, bench_confirmed=True)
        self.assertEqual(self.operations, [0, 2, 0])
        self.assertTrue(result['installed'])
        self.assertTrue(self.receipt()['sram_written'])
        self.assertFalse(self.receipt()['flash_written'])

    def test_existing_b0b1_is_an_allowed_prewrite_build(self):
        self.hardware(pre=0xb0b1)
        installer.state.return_value = self.safe_state(0xb0b1)
        self.assertTrue(installer.install(self.build, True, True)['installed'])

    def test_no_programmer_operations_except_zero_and_two(self):
        with mock.patch.object(installer.subprocess, 'run') as run:
            for op in (-1, 1, 3, 4, 5, 6, 10, True, '2'):
                with self.subTest(op=op), self.assertRaises(ValueError):
                    installer.command(op, self.base / 'never.txt')
            run.assert_not_called()

    def test_fixture_source_tamper_blocks_offline(self):
        (self.fixture / 'top.v').write_text('tampered')
        with self.assertRaisesRegex(ValueError, 'Fixture input changed'):
            installer.verify(self.build)

    def test_latest_source_tamper_blocks_offline(self):
        (self.source / 'top.v').write_text('new unbuilt source')
        with self.assertRaisesRegex(ValueError, 'Latest source differs'):
            installer.verify(self.build)

    def test_latest_source_added_file_blocks_offline(self):
        (self.source / 'extra.v').write_text('new unbuilt source')
        with self.assertRaisesRegex(ValueError, 'file set differs'):
            installer.verify(self.build)

    def test_tcl_only_option_differences_allowed(self):
        self.assertTrue(installer.verify(self.build)['passed'])
        (self.source / 'build.tcl').write_text('open_project different.gprj\nrun all\nexit\n')
        with self.assertRaisesRegex(ValueError, 'beyond build options'):
            installer.verify(self.build)

    def test_inputs_hash_tamper(self):
        self.inputs['new'] = True
        self.write('inputs.json', self.inputs)
        with self.assertRaisesRegex(ValueError, 'inputs.json hash changed'):
            installer.verify(self.build)

    def test_archived_builder_and_current_auditor_are_both_bound(self):
        (self.build / 'build_runner.py').write_text('wrong old builder')
        with self.assertRaisesRegex(ValueError, 'Archived executing'):
            installer.verify(self.build)
        (self.build / 'build_runner.py').write_text('actual archived builder\n')
        (self.root / 'tools/build.py').write_text('new unaudited collector')
        with self.assertRaisesRegex(ValueError, 'Current build auditor'):
            installer.verify(self.build)

    def test_bitstream_hash_tamper(self):
        self.image.write_text('bad data')
        with self.assertRaisesRegex(ValueError, 'Build output changed'):
            installer.verify(self.build)

    def test_bitstream_usercode_checked_even_when_hashes_match(self):
        self.image.write_text('// UserCode: 0x0000B0B0\nwrong image\n')
        self.rebind_outputs()
        with self.assertRaisesRegex(ValueError, 'UserCode is not B0B1'):
            installer.verify(self.build)

    def test_boolean_vendor_exit_is_rejected_even_with_rebound_hashes(self):
        self.result['vendor_returncode'] = False
        self.rebind_outputs()
        with self.assertRaisesRegex(ValueError, 'invalid exit code'):
            installer.verify(self.build)

    def test_result_and_acceptance_must_pass(self):
        self.result['passed'] = False
        self.rebind_outputs()
        with self.assertRaisesRegex(ValueError, 'Build result did not pass'):
            installer.verify(self.build)
        self.result['passed'] = True
        self.rebind_outputs()
        self.acceptance['passed'] = False
        self.write('offline_acceptance.json', self.acceptance)
        with self.assertRaisesRegex(ValueError, 'Offline acceptance did not pass'):
            installer.verify(self.build)

    def omitted_unrouted_proof(self):
        self.result.update(unrouted_nets=None, actual_input_paths_passed=True,
                           report_clock_contract_passed=True, timing_exceptions_added=False,
                           routing_status_proof='Real vendor exit 0; routing/bitstream completed; explicit zero count omitted',
                           worst_reported_slack_ns=dict(setup=0.1, hold=0.2, recovery=1.0, removal=1.0, minimum_pulse_width=9.0))
        self.rebind_outputs()

    def test_missing_unrouted_count_with_complete_vendor_proof_is_allowed(self):
        self.omitted_unrouted_proof()
        self.assertTrue(installer.verify(self.build)['passed'])

    def test_missing_unrouted_count_without_complete_proof_is_rejected(self):
        for key, value in [('actual_input_paths_passed', False), ('report_clock_contract_passed', False),
                           ('timing_exceptions_added', True), ('routing_status_proof', ''),
                           ('worst_reported_slack_ns', {}), ('vendor_returncode', 1), ('errors', ['error'])]:
            with self.subTest(key=key):
                self.omitted_unrouted_proof()
                self.result[key] = value
                self.rebind_outputs()
                with self.assertRaises(ValueError):
                    installer.verify(self.build)

    def test_missing_unrouted_count_negative_or_missing_any_sta_kind_is_rejected(self):
        for kind in ('setup', 'hold', 'recovery', 'removal', 'minimum_pulse_width'):
            for value in (-0.001, None):
                with self.subTest(kind=kind, value=value):
                    self.omitted_unrouted_proof()
                    self.result['worst_reported_slack_ns'][kind] = value
                    self.rebind_outputs()
                    with self.assertRaises(ValueError):
                        installer.verify(self.build)

    def test_explicit_nonzero_unrouted_is_always_rejected(self):
        self.omitted_unrouted_proof()
        self.result['unrouted_nets'] = 1
        self.rebind_outputs()
        with self.assertRaisesRegex(ValueError, 'explicit nonzero'):
            installer.verify(self.build)

    def bind_tested_scripts_and_sources(self):
        (self.root / 'tests').mkdir(exist_ok=True)
        script = self.root / 'tests/new_check.py'
        script.write_text('print("test proof")\n')
        self.write('tests_receipt.json', dict(schema='b0b1.tests.v1', passed=True,
                   verification_scripts_sha256={'tests/new_check.py': installer.sha(script)},
                   source_sha256={p.name: installer.sha(p) for p in self.source.iterdir()}))
        self.rebind_outputs()
        return script

    def test_bound_verification_script_changes_are_rejected(self):
        script = self.bind_tested_scripts_and_sources()
        self.assertTrue(installer.verify(self.build)['passed'])
        script.write_text('print("changed after tests")\n')
        with self.assertRaisesRegex(ValueError, 'Verification script changed since tests'):
            installer.verify(self.build)

    def test_bound_test_source_map_must_match_fixture_and_current(self):
        self.bind_tested_scripts_and_sources()
        receipt = installer.read_json(self.build / 'tests_receipt.json')
        receipt['source_sha256']['top.v'] = '0'*64
        self.write('tests_receipt.json', receipt)
        self.rebind_outputs()
        with self.assertRaisesRegex(ValueError, 'Tested source differs'):
            installer.verify(self.build)

    def test_acceptance_must_bind_result(self):
        self.acceptance['result_sha256'] = '0' * 64
        self.write('offline_acceptance.json', self.acceptance)
        with self.assertRaisesRegex(ValueError, 'not bound'):
            installer.verify(self.build)

    def test_test_receipt_hash_and_pass_are_checked(self):
        self.write('tests_receipt.json', {'passed': False})
        with self.assertRaisesRegex(ValueError, 'Test receipt hash changed'):
            installer.verify(self.build)
        self.acceptance['test_receipt']['sha256'] = installer.sha(self.build / 'tests_receipt.json')
        self.write('offline_acceptance.json', self.acceptance)
        with self.assertRaisesRegex(ValueError, 'test receipt did not pass'):
            installer.verify(self.build)

    def test_receipt_path_cannot_escape_build(self):
        self.acceptance['test_receipt']['path'] = '../outside.json'
        self.write('offline_acceptance.json', self.acceptance)
        with self.assertRaisesRegex(ValueError, 'escapes'):
            installer.verify(self.build)

    def test_unsafe_or_stale_state_fails_closed(self):
        unsafe = [({'fresh': False}, None), ({'flight_info_fresh': False}, None),
                  ({'status': 'waiting'}, None), ({'serial_writes': True}, None),
                  ({'flight_info': {'build_id': 0xb0ac}}, None)]
        unsafe += [(None, {k: value}) for k, value in [('armed', True), ('controller_enabled', True),
                    ('physical_output_active', True), ('pwm_us', [1000,1000,1000,1001]),
                    ('command_us', [1001]*4), ('rc_valid', False),
                    ('rc_us', [1500,1500,1200,1500,1000,1000,1000]),
                    ('rc_us', [1500,1500,1000,1500,2000,1000,1000]),
                    ('rc_us', [1500,1500,1000,1500,1000,1000,2000])]]
        self.hardware()
        for top, data in unsafe:
            with self.subTest(top=top, data=data):
                snapshot = self.safe_state()
                if top:
                    snapshot.update(top)
                if data:
                    snapshot['data'].update(data)
                installer.state.return_value = snapshot
                with self.assertRaises(ValueError):
                    installer.install(self.build, True, True)
                self.assertEqual(self.operations, [])

    def test_prewrite_state_is_rechecked(self):
        self.hardware()
        bad = self.safe_state()
        bad['data']['armed'] = True
        installer.state.side_effect = [self.safe_state(), bad]
        with self.assertRaises(ValueError):
            installer.install(self.build, True, True)
        self.assertEqual(self.operations, [0])

    def test_programmer_inventory_ambiguity_blocks_identity(self):
        self.hardware()
        installer.programmers.return_value *= 2
        with self.assertRaisesRegex(ValueError, 'missing or ambiguous'):
            installer.install(self.build, True, True)
        self.assertEqual(self.operations, [])

    def test_identity_mismatch_blocks_write(self):
        self.hardware(pre=0xb0ac)
        with self.assertRaisesRegex(ValueError, 'does not match'):
            installer.install(self.build, True, True)
        self.assertEqual(self.operations, [0])

    def test_target_device_identity_is_checked(self):
        self.assertEqual(installer.identity('ID Code is: 0x0001481B\nUser Code is: 0x0000B0B1\n'), (0x1481b, 0xb0b1))
        for text in ('Target Device GW5AT-60B(0x0001481B)', 'ID Code is: 0x0001481B\n'):
            with self.assertRaises(ValueError):
                installer.identity(text)

    def test_wrong_device_id_blocks_write(self):
        self.hardware(device=0x12345678)
        with self.assertRaisesRegex(ValueError, 'does not match'):
            installer.install(self.build, True, True)
        self.assertEqual(self.operations, [0])

    def test_wrong_programmer_serial_blocks_identity(self):
        self.hardware()
        installer.programmers.return_value[0]['serial'] = 'other'
        with self.assertRaisesRegex(ValueError, 'missing or ambiguous'):
            installer.install(self.build, True, True)
        self.assertEqual(self.operations, [])

    def test_hash_change_after_read_identity_blocks_write(self):
        self.hardware(mutate=lambda op: (self.fixture / 'top.v').write_text('raced') if op == 0 else None)
        with self.assertRaisesRegex(ValueError, 'Fixture input changed'):
            installer.install(self.build, True, True)
        self.assertEqual(self.operations, [0])

    def test_write_timeout_preserves_report_and_never_retries(self):
        self.hardware(fail_write=True)
        with self.assertRaises(subprocess.TimeoutExpired):
            installer.install(self.build, True, True)
        self.assertEqual(self.operations, [0, 2])
        report = self.receipt()
        self.assertTrue(report['sram_write_attempted'])
        self.assertFalse(report['sram_written'])
        self.assertIn('TimeoutExpired', report['error'])
        self.assertIn('TIMEOUT', (Path(report['folder']) / 'program_sram.txt').read_text())

    def test_bad_post_identity_does_not_flash_or_blind_rollback(self):
        self.hardware(post=0xb0b0)
        with self.assertRaisesRegex(ValueError, 'Post-write'):
            installer.install(self.build, True, True)
        self.assertEqual(self.operations, [0, 2, 0])
        report = self.receipt()
        self.assertTrue(report['sram_written'])
        self.assertFalse(report['installed'])
        self.assertFalse(report['flash_written'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
