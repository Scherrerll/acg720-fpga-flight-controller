"""Installer fail-closed proof using temporary artifacts and mocked hardware only."""
from pathlib import Path
import importlib.util
import json
import shutil
import subprocess
import tempfile
import unittest
import xml.etree.ElementTree as ET
from unittest import mock

SPEC = importlib.util.spec_from_file_location('b0b2_install_sram', Path(__file__).resolve().parents[1] / 'tools/install_sram.py')
installer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(installer)
TEST_RUN_NAME = 'verification_20261025T000000_000001Z'
TEST_RECEIPT_NAME = 'tests_receipt_' + TEST_RUN_NAME + '.json'


def subtest_artifact_fixture(build):
    """Small real temporary files; wire contents are mock-only, never hardware."""
    artifacts = {}
    for relative in ('sik_diagnostic/result.json', 'sik_diagnostic/sik_wire.hex',
                     'sik_diagnostic/legacy_wire.hex', 'sik_copy_contract/result.json'):
        name = TEST_RUN_NAME + '/' + relative
        path = build / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('{"passed":true,"mock_only":true}\n' if path.suffix == '.json' else '00\n')
        artifacts[name] = installer.sha(path)
    return artifacts


class InstallerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name).resolve()
        self.root = self.base / 'firmware/B0B2'
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
        self.image.write_text('// UserCode: 0x0000B0B2\nmock bitstream\n')
        (self.pnr / 'acg720_ano_port.tr').write_text('mock timing report\n')
        (self.build / 'build_runner.py').write_text('actual archived builder\n')
        self.inputs = dict(source_root=str(self.source),
                           source_sha256={p.name: installer.sha(p) for p in self.fixture.iterdir() if p.is_file()},
                           runner_sha256=installer.sha(self.build / 'build_runner.py'), options={'user_code': '0000B0B2'})
        self.write('inputs.json', self.inputs)
        self.result = dict(passed=True, routing_passed=True, timing_passed=True, identity_passed=True,
                           pin_contract_passed=True, vendor_returncode=0, errors=[], unrouted_nets=0,
                           audit_runner_sha256=installer.sha(self.root / 'tools/build.py'),
                           inputs_sha256=installer.sha(self.build / 'inputs.json'))
        self.write_complete_test_receipt()
        self.rebind_outputs()
        self.root_patch = mock.patch.object(installer, 'ROOT', self.root)
        self.root_patch.start()
        self.addCleanup(self.root_patch.stop)
        # These deliberately tiny legacy artifacts exercise the installer's
        # local bindings. Real shared-auditor integration is covered separately.
        patcher = mock.patch.object(installer, 'audit_current_source', return_value={})
        self.shared_audit = patcher.start()
        self.addCleanup(patcher.stop)

    def write(self, name, value):
        (self.build / name).write_text(json.dumps(value, sort_keys=True) + '\n')

    def write_complete_test_receipt(self):
        self.write(TEST_RECEIPT_NAME, dict(schema='b0b2.tests.v1', passed=True,
            verification_inputs_unchanged=True, subtest_artifacts_sha256=subtest_artifact_fixture(self.build),
            verification_scripts_sha256={p.relative_to(self.root).as_posix(): installer.sha(p)
                for directory in ('tests', 'ground', 'tools') for p in (self.root / directory).rglob('*')
                if p.is_file() and p.suffix in ('.py', '.v', '.hex')},
            source_sha256={p.name: installer.sha(p) for p in self.source.iterdir()}))

    def rebind_outputs(self):
        self.result['outputs_sha256'] = {p.relative_to(self.build).as_posix(): installer.sha(p) for p in self.pnr.iterdir()}
        self.result['bitstream'] = dict(path=str(self.image), sha256=installer.sha(self.image))
        self.write('result.json', self.result)
        self.acceptance = dict(schema='b0b2.offline-acceptance.v1', passed=True, build_id=0xb0b2,
                               result_sha256=installer.sha(self.build / 'result.json'),
                               inputs_sha256=installer.sha(self.build / 'inputs.json'), bitstream_sha256=installer.sha(self.image),
                               test_receipt=dict(path=TEST_RECEIPT_NAME, sha256=installer.sha(self.build / TEST_RECEIPT_NAME)))
        self.write('offline_acceptance.json', self.acceptance)

    @staticmethod
    def safe_state(build=0xb0b0):
        return dict(fresh=True, flight_info_fresh=True, status='live', serial_writes=False,
                    flight_info={'build_id': build}, data=dict(armed=False, controller_enabled=False,
                    physical_output_active=False, pwm_us=[1000]*4, command_us=[1000]*4, rc_valid=True,
                    rc_us=[1500,1500,1000,1500,1000,1000,1000,1000]))

    def hardware(self, mutate=None, pre=0xb0b0, post=0xb0b2, fail_write=False, device=0x1481b):
        self.operations = []

        def run(args, **kwargs):
            self.assertEqual(args[1:5], ['--device', 'GW5AT-60B', '--cable-index', '1'])
            self.assertEqual(args[5:7], ['--location', '289'])
            self.assertEqual(kwargs['timeout'], 120)
            op = int(args[args.index('--run')+1])
            self.assertIn(op, (0, 2))
            self.operations.append(op)
            if op == 2:
                self.assertEqual(args[-2:], ['--fsFile', str(self.image)])
                if fail_write:
                    raise subprocess.TimeoutExpired(args, 120, output='partial output')
                installer.state.return_value = self.safe_state(0xb0b2)
                text = 'SRAM programmed\nFinished.\n'
            else:
                code = pre if len(self.operations) == 1 else post
                text = f'ID Code is: 0x{device:08X}\nUser Code is: 0x{code:08X}\nFinished.\n'
            if mutate:
                mutate(op)
            return subprocess.CompletedProcess(args, 0, text, '')

        for name, value in [('programmers', [dict(vid=0x403, pid=0x6014, serial='6', device='COM21')]),
                            ('scan_cables', dict(name='Gowin USB Cable(FT2CH)', index=1, location=289)),
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
             mock.patch.object(installer, 'scan_cables', side_effect=AssertionError('cable enumeration accessed')), \
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
        self.assertTrue(result['post_load_telemetry']['passed'])
        self.assertEqual(len(result['post_load_telemetry']['attempts']), 1)
        saved = json.loads((Path(result['folder']) / 'telemetry_after.json').read_text())
        self.assertEqual(saved['flight_info']['build_id'], 0xb0b2)
        self.assertEqual(result['programmer_selection']['serial'], '6')
        self.assertEqual(result['cable_selection'], dict(name='Gowin USB Cable(FT2CH)', index=1, location=289))
        self.assertEqual([s['phase'] for s in result['scans']], ['initial', 'prewrite'])
        self.assertEqual(installer.programmers.call_count, 2)
        self.assertEqual(installer.scan_cables.call_count, 2)

    def test_existing_b0b2_is_an_allowed_prewrite_build(self):
        self.hardware(pre=0xb0b2)
        installer.state.return_value = self.safe_state(0xb0b2)
        self.assertTrue(installer.install(self.build, True, True)['installed'])

    def test_no_programmer_operations_except_zero_and_two(self):
        with mock.patch.object(installer.subprocess, 'run') as run:
            for op in (-1, 1, 3, 4, 5, 6, 10, True, '2'):
                with self.subTest(op=op), self.assertRaises(ValueError):
                    installer.command(op, self.base / 'never.txt')
            run.assert_not_called()

    @staticmethod
    def cable_output(location=289, index=1, usb_location=None):
        if usb_location is None:
            usb_location = location
        return (' Cable found:  USB Debugger A/0/0/null (USB location:0)\n'
                f' Cable found:  Gowin USB Cable(FT2CH)/{index}/{location}/null (USB location:{usb_location})\n')

    def test_scan_parses_unique_vendor_row_and_ignores_separate_debugger(self):
        self.assertEqual(installer.parse_cables(self.cable_output()),
                         dict(name='Gowin USB Cable(FT2CH)', index=1, location=289))
        self.assertEqual(installer.parse_cables(self.cable_output(353))['location'], 353)

    def test_scan_rejects_empty_multiple_malformed_wrong_index_and_locations(self):
        invalid = ['', ' Cable found: USB Debugger A/0/0/null (USB location:0)\n',
                   self.cable_output() + self.cable_output(), self.cable_output(index=0),
                   self.cable_output(index=2), self.cable_output(0), self.cable_output(-1),
                   self.cable_output(289, usb_location=353),
                   self.cable_output().replace('/null', '/unknown'),
                   self.cable_output().replace('(FT2CH)', '(OTHER)')]
        for text in invalid:
            with self.subTest(text=text), self.assertRaises(ValueError):
                installer.parse_cables(text)

    def test_scan_command_is_download_cable_enumeration_only_and_saves_log(self):
        path = self.base / 'scan.txt'
        with mock.patch.object(installer.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, self.cable_output(), '')) as run:
            self.assertEqual(installer.scan_cables(path)['location'], 289)
        args, kwargs = run.call_args
        self.assertEqual(args[0], [str(installer.PROGRAMMER), '--scan-cables', 'F'])
        self.assertNotIn('--scan', args[0]);self.assertNotIn('--run', args[0])
        self.assertEqual(kwargs['timeout'], 120)
        self.assertEqual(path.read_text(), self.cable_output())

    def test_scan_nonzero_or_boolean_exit_cannot_select_cable(self):
        for code in (1, False):
            with self.subTest(code=code), mock.patch.object(installer.subprocess, 'run',
                    return_value=subprocess.CompletedProcess([], code, self.cable_output(), 'vendor error\n')):
                path = self.base / 'failed_scan.txt'
                with self.assertRaisesRegex(ValueError, 'enumeration failed'):
                    installer.scan_cables(path)
                self.assertIn('vendor error', path.read_text())

    def test_scan_timeout_retains_partial_log(self):
        path = self.base / 'timeout_scan.txt'
        with mock.patch.object(installer.subprocess, 'run', side_effect=subprocess.TimeoutExpired([], 120, output=b'partial cable scan')):
            with self.assertRaises(subprocess.TimeoutExpired):
                installer.scan_cables(path)
        self.assertIn('partial cable scan', path.read_text());self.assertIn('TIMEOUT', path.read_text())

    def test_every_identity_or_sram_call_requires_positive_location(self):
        for location in (None, 0, -1, True, '289'):
            with self.subTest(location=location), mock.patch.object(installer.subprocess, 'run') as run:
                with self.assertRaisesRegex(ValueError, 'location'):
                    installer.command(0, self.base / 'never.txt', location=location)
                run.assert_not_called()

    def test_initial_scan_failure_blocks_all_programmer_operations(self):
        self.hardware()
        installer.scan_cables.side_effect = ValueError('Missing or ambiguous Gowin USB cable inventory')
        with self.assertRaisesRegex(ValueError, 'Missing or ambiguous'):
            installer.install(self.build, True, True)
        self.assertEqual(self.operations, []);installer.state.assert_not_called()
        report = self.receipt()
        self.assertEqual(report['scans'], [dict(phase='initial', log='cables_before.txt')])
        self.assertFalse(report['sram_write_attempted'])

    def test_prewrite_vendor_location_change_blocks_sram_and_records_both_scans(self):
        self.hardware()
        installer.scan_cables.side_effect = [installer.parse_cables(self.cable_output(289)),
                                             installer.parse_cables(self.cable_output(353))]
        with self.assertRaisesRegex(ValueError, 'Vendor cable selection changed'):
            installer.install(self.build, True, True)
        self.assertEqual(self.operations, [0]);self.assertEqual(installer.state.call_count, 1)
        report = self.receipt()
        self.assertEqual([s['selection']['location'] for s in report['scans']], [289, 353])
        self.assertFalse(report['sram_write_attempted'])

    def test_prewrite_com_selection_must_still_be_unique_same_serial_and_port(self):
        for changed in ([dict(vid=0x403, pid=0x6014, serial='5', device='COM21')],
                        [dict(vid=0x403, pid=0x6014, serial='6', device='COM22')],
                        [dict(vid=0x403, pid=0x6014, serial='6', device='COM21')] * 2):
            with self.subTest(changed=changed):
                self.hardware()
                installer.programmers.side_effect = [[dict(vid=0x403, pid=0x6014, serial='6', device='COM21')], changed]
                with self.assertRaises(ValueError):
                    installer.install(self.build, True, True)
                self.assertEqual(self.operations, [0]);self.assertEqual(installer.scan_cables.call_count, 1)
                self.assertFalse(self.receipt()['sram_write_attempted'])

    def test_prewrite_scan_failure_blocks_sram(self):
        self.hardware()
        installer.scan_cables.side_effect = [installer.parse_cables(self.cable_output()), ValueError('Cable enumeration failed')]
        with self.assertRaisesRegex(ValueError, 'enumeration failed'):
            installer.install(self.build, True, True)
        self.assertEqual(self.operations, [0]);self.assertFalse(self.receipt()['sram_write_attempted'])

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
        with self.assertRaisesRegex(ValueError, 'UserCode is not B0B2'):
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
        self.write_complete_test_receipt()
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
        receipt = installer.read_json(self.build / TEST_RECEIPT_NAME)
        receipt['source_sha256']['top.v'] = '0'*64
        self.write(TEST_RECEIPT_NAME, receipt)
        self.rebind_outputs()
        with self.assertRaisesRegex(ValueError, 'Tested source differs'):
            installer.verify(self.build)

    def test_test_receipt_requires_schema_and_complete_nonempty_maps(self):
        original = installer.read_json(self.build / TEST_RECEIPT_NAME)
        cases = [('schema', None), ('schema', 'b0b1.tests.v1'),
                 ('verification_scripts_sha256', None), ('verification_scripts_sha256', {}),
                 ('source_sha256', None), ('source_sha256', {}),
                 ('source_sha256', {'top.v': installer.sha(self.source / 'top.v')})]
        for key, value in cases:
            with self.subTest(key=key, value=value):
                receipt = dict(original)
                if value is None:
                    receipt.pop(key)
                else:
                    receipt[key] = value
                self.write(TEST_RECEIPT_NAME, receipt)
                self.rebind_outputs()
                with self.assertRaises(ValueError):
                    installer.verify(self.build)

    def test_test_receipt_requires_literal_unchanged_inputs_true(self):
        original = installer.read_json(self.build / TEST_RECEIPT_NAME)
        for value in (None, False, 1):
            with self.subTest(value=value):
                receipt = json.loads(json.dumps(original))
                if value is None:receipt.pop('verification_inputs_unchanged')
                else:receipt['verification_inputs_unchanged'] = value
                self.write(TEST_RECEIPT_NAME, receipt);self.rebind_outputs()
                with self.assertRaisesRegex(ValueError, 'inputs were not proven unchanged'):
                    installer.verify(self.build)

    def test_subtest_artifact_map_is_exact_and_current_run_relative(self):
        original = installer.read_json(self.build / TEST_RECEIPT_NAME)
        complete = original['subtest_artifacts_sha256']
        first = next(iter(complete))
        missing = dict(complete);missing.pop(first)
        extra = dict(complete, unrelated='0'*64)
        escaped = dict(complete);escaped['../outside.json'] = escaped.pop(first)
        prior_run = {name.replace(TEST_RUN_NAME, 'verification_previous'): digest for name, digest in complete.items()}
        for value in (None, {}, missing, extra, escaped, prior_run):
            with self.subTest(value=value):
                receipt = json.loads(json.dumps(original))
                if value is None:receipt.pop('subtest_artifacts_sha256')
                else:receipt['subtest_artifacts_sha256'] = value
                self.write(TEST_RECEIPT_NAME, receipt);self.rebind_outputs()
                with self.assertRaisesRegex(ValueError, 'exactly the four current-run artifacts'):
                    installer.verify(self.build)

    def test_subtest_artifact_bytes_existence_and_digest_are_bound(self):
        original = installer.read_json(self.build / TEST_RECEIPT_NAME)
        name = next(iter(original['subtest_artifacts_sha256']))
        path = self.build / name
        data = path.read_bytes()
        for change in ('digest', 'bytes', 'missing'):
            with self.subTest(change=change):
                receipt = json.loads(json.dumps(original))
                if change == 'digest':receipt['subtest_artifacts_sha256'][name] = '0'*64
                elif change == 'bytes':path.write_bytes(data + b'changed after tests')
                else:path.unlink()
                try:
                    self.write(TEST_RECEIPT_NAME, receipt);self.rebind_outputs()
                    with self.assertRaisesRegex(ValueError, 'Subtest artifact changed|Missing artifact'):
                        installer.verify(self.build)
                finally:
                    path.write_bytes(data)

    def test_receipt_run_identity_cannot_move_or_use_old_unscoped_name(self):
        original = (self.build / TEST_RECEIPT_NAME).read_bytes()
        for relative in ('tests_receipt.json', 'tests_receipt_.json', 'nested/' + TEST_RECEIPT_NAME):
            with self.subTest(relative=relative):
                path = self.build / relative
                path.parent.mkdir(parents=True, exist_ok=True);path.write_bytes(original)
                acceptance = json.loads(json.dumps(self.acceptance))
                acceptance['test_receipt'] = dict(path=relative, sha256=installer.sha(path))
                self.write('offline_acceptance.json', acceptance)
                with self.assertRaisesRegex(ValueError, 'current build-root|run name is empty or invalid'):
                    installer.verify(self.build)

    def test_added_verification_script_invalidates_coverage(self):
        (self.root / 'tools/untested.py').write_text('new untested helper\n')
        with self.assertRaisesRegex(ValueError, 'incomplete'):
            installer.verify(self.build)

    def test_current_tcl_is_bound_to_the_test_receipt(self):
        (self.source / 'build.tcl').write_text('open_project top.gprj\nset_option -route_option 3\nrun all\nexit\n')
        with self.assertRaisesRegex(ValueError, 'Tested source differs'):
            installer.verify(self.build)

    def test_acceptance_must_bind_result(self):
        self.acceptance['result_sha256'] = '0' * 64
        self.write('offline_acceptance.json', self.acceptance)
        with self.assertRaisesRegex(ValueError, 'not bound'):
            installer.verify(self.build)

    def test_test_receipt_hash_and_pass_are_checked(self):
        self.write(TEST_RECEIPT_NAME, {'passed': False})
        with self.assertRaisesRegex(ValueError, 'Test receipt hash changed'):
            installer.verify(self.build)
        self.acceptance['test_receipt']['sha256'] = installer.sha(self.build / TEST_RECEIPT_NAME)
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
        self.assertEqual(installer.identity('ID Code is: 0x0001481B\nUser Code is: 0x0000B0B2\n'), (0x1481b, 0xb0b2))
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

    def fake_postload_clock(self):
        now = [0.0]
        clock = mock.patch.object(installer.time, 'monotonic', side_effect=lambda: now[0])
        clock.start();self.addCleanup(clock.stop)
        def sleep(seconds):
            now[0] += seconds
        pause = mock.patch.object(installer.time, 'sleep', side_effect=sleep)
        self.sleep = pause.start();self.addCleanup(pause.stop)
        return now

    def test_postload_waits_for_new_fresh_stopped_telemetry(self):
        self.hardware();self.fake_postload_clock()
        incomplete = self.safe_state(0xb0b2);incomplete['data']['rc_valid'] = False
        stale = self.safe_state(0xb0b2);stale['fresh'] = False
        installer.state.side_effect = [self.safe_state(), self.safe_state(), self.safe_state(),
                                       stale, incomplete, self.safe_state(0xb0b2)]
        result = installer.install(self.build, True, True)
        self.assertEqual(self.operations, [0, 2, 0])
        self.assertTrue(result['installed'])
        self.assertEqual(len(result['post_load_telemetry']['attempts']), 4)
        self.assertEqual(self.sleep.call_count, 3)

    def test_postload_transport_failure_can_recover_without_programmer_retry(self):
        self.hardware();self.fake_postload_clock()
        installer.state.side_effect = [self.safe_state(), self.safe_state(), OSError('boot endpoint unavailable'), self.safe_state(0xb0b2)]
        result = installer.install(self.build, True, True)
        self.assertTrue(result['post_load_telemetry']['passed'])
        self.assertIn('OSError', result['post_load_telemetry']['attempts'][0]['error'])
        self.assertEqual(self.operations, [0, 2, 0])

    def test_postload_timeout_preserves_written_fact_and_last_response(self):
        self.hardware();now = self.fake_postload_clock()
        installer.state.side_effect = lambda **kwargs: self.safe_state()
        with self.assertRaisesRegex(ValueError, 'Timed out waiting'):
            installer.install(self.build, True, True)
        self.assertEqual(self.operations, [0, 2, 0])
        self.assertEqual(now[0], 30.0)
        report = self.receipt()
        self.assertFalse(report['installed']);self.assertTrue(report['sram_write_attempted'])
        self.assertTrue(report['sram_written']);self.assertFalse(report['flash_written'])
        self.assertFalse(report['post_load_telemetry']['passed'])
        self.assertTrue((Path(report['folder']) / 'telemetry_after.json').is_file())

    def test_postload_explicit_activity_fails_immediately_without_retry(self):
        for key, value in [('armed', True), ('controller_enabled', True), ('physical_output_active', True),
                           ('pwm_us', [1000, 1000, 1001, 1000]), ('command_us', [1001] * 4)]:
            with self.subTest(key=key):
                self.hardware();self.fake_postload_clock()
                unsafe = self.safe_state(0xb0b2);unsafe['data'][key] = value
                installer.state.side_effect = [self.safe_state(), self.safe_state(), unsafe]
                with self.assertRaises(installer.UnsafePostLoad):
                    installer.install(self.build, True, True)
                self.assertEqual(self.operations, [0, 2, 0]);self.sleep.assert_not_called()
                self.assertEqual(installer.state.call_count, 3)
                report = self.receipt()
                self.assertFalse(report['installed']);self.assertTrue(report['sram_written'])
                self.assertTrue(report['post_load_telemetry']['unsafe']);self.assertFalse(report['flash_written'])

    def test_postload_read_timeout_is_bounded_by_remaining_deadline(self):
        self.hardware();self.fake_postload_clock()
        responses = iter([self.safe_state(), self.safe_state()])
        post_timeouts = []
        def read(**kwargs):
            if not kwargs:
                return next(responses)
            post_timeouts.append(kwargs['timeout'])
            return self.safe_state()
        installer.state.side_effect = read
        with self.assertRaisesRegex(ValueError, 'Timed out waiting'):
            installer.install(self.build, True, True)
        self.assertLessEqual(max(post_timeouts), 4.0)
        self.assertEqual(post_timeouts[-1], 0.25)


class SharedSourceInstallerTests(unittest.TestCase):
    """Real shared source auditor with the build suite's nonprogrammable donor.

    Only vendor output/acceptance values are mocks. Source, donor provenance,
    reset proof and bounded physical exceptions use the production builder.
    """
    def setUp(self):
        path = Path(__file__).resolve().with_name('test_build_audit.py')
        spec = importlib.util.spec_from_file_location('b0b2_installer_shared_fixture', path)
        self.fixtures = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.fixtures)
        self.case = self.fixtures.BuildAuditTests()
        self.case.setUp()
        self.addCleanup(self.case.doCleanups)
        self.builder = self.fixtures.builder
        self.root, self.repo = self.case.root, self.case.repo
        (self.root / 'tools').mkdir()
        shutil.copyfile(Path(__file__).resolve().parents[1] / 'tools/build.py', self.root / 'tools/build.py')
        self.donor = self.repo / 'installer_mock_donor'
        self.fixtures.make_mock_donor(self.builder, self.donor)
        self.build = self.repo / 'installer_mock_derived'
        self.fixture, self.inputs = self.builder.prepare(self.build, 2, 2, 1, self.donor, True)
        patcher = mock.patch.object(installer, 'ROOT', self.root)
        patcher.start();self.addCleanup(patcher.stop)
        self.acceptance()

    def acceptance(self):
        pnr = self.fixture / 'impl/pnr'
        pnr.mkdir(parents=True, exist_ok=True)
        image = pnr / 'acg720_ano_port.fs'
        image.write_text('// UserCode: 0x0000B0B2\nMOCK ONLY -- NOT PROGRAMMABLE\n')
        self.builder.write_json(self.build / 'inputs.json', self.inputs)
        self.builder.write_json(self.build / TEST_RECEIPT_NAME, dict(schema='b0b2.tests.v1', passed=True,
            verification_inputs_unchanged=True, subtest_artifacts_sha256=subtest_artifact_fixture(self.build),
            source_sha256=self.builder.source_hashes(self.root / 'source'),
            verification_scripts_sha256={'tools/build.py': installer.sha(self.root / 'tools/build.py')}))
        result = dict(passed=True, routing_passed=True, timing_passed=True, identity_passed=True,
            pin_contract_passed=True, vendor_returncode=0, errors=[], unrouted_nets=0,
            observer_global_contract_passed=True, pnr_only_synthesis_absent=True,
            audit_runner_sha256=installer.sha(self.root / 'tools/build.py'),
            inputs_sha256=installer.sha(self.build / 'inputs.json'),
            outputs_sha256={p.relative_to(self.build).as_posix(): installer.sha(p) for p in pnr.iterdir()},
            bitstream=dict(path=str(image), sha256=installer.sha(image)))
        self.builder.write_json(self.build / 'result.json', result)
        self.bind_acceptance()

    def bind_acceptance(self):
        result = installer.read_json(self.build / 'result.json')
        self.builder.write_json(self.build / 'offline_acceptance.json',
            dict(schema='b0b2.offline-acceptance.v1', passed=True, build_id=0xb0b2,
                result_sha256=installer.sha(self.build / 'result.json'),
                inputs_sha256=installer.sha(self.build / 'inputs.json'),
                bitstream_sha256=result['bitstream']['sha256'],
                test_receipt=dict(path=TEST_RECEIPT_NAME, sha256=installer.sha(self.build / TEST_RECEIPT_NAME))))

    def rebind_input(self, name=None):
        if name:
            self.inputs['source_sha256'][name] = installer.sha(self.fixture / name)
        self.acceptance()

    def test_real_shared_audit_accepts_proven_derived_cst_gprj_and_pnr_tcl(self):
        self.assertTrue(installer.verify(self.build)['passed'])
        physical = self.inputs['source_sha256']
        logical = self.inputs['logical_source_sha256']
        self.assertEqual({k for k in physical if physical[k] != logical[k]},
                         {'acg720_ano_port.cst', 'acg720_ano_port.gprj', 'build.tcl'})
        project = self.fixture / 'acg720_ano_port.gprj'
        self.assertEqual(project.read_bytes(), self.builder.netlist_project(self.root / 'source'))
        self.assertEqual([(f.attrib['path'], f.attrib['type']) for f in ET.parse(project).findall('.//File')],
            [('impl/gwsynthesis/acg720_ano_port.vg', 'file.netlist'),
             ('acg720_ano_port.cst', 'file.cst'), ('acg720_ano_port.sdc', 'file.sdc')])
        receipt = installer.read_json(self.build / TEST_RECEIPT_NAME)
        self.assertEqual(receipt['source_sha256'], logical)

    def test_real_shared_audit_still_accepts_full_build_and_rejects_full_cst_edit(self):
        self.build = self.repo / 'installer_mock_full'
        self.fixture, self.inputs = self.builder.prepare(self.build, 2, 2, 1)
        self.acceptance()
        self.assertTrue(installer.verify(self.build)['passed'])
        path = self.fixture / 'acg720_ano_port.cst'
        path.write_text(path.read_text() + 'CLOCK_LOC "unproven" BUFG = CE|SR|LOGIC;\n')
        self.rebind_input('acg720_ano_port.cst')
        with self.assertRaises(ValueError):installer.verify(self.build)

    def test_synthesis_only_rejected_even_with_forged_complete_physical_acceptance(self):
        self.build = self.repo / 'installer_mock_synthesis_only'
        self.fixture, self.inputs = self.builder.prepare(self.build, 2, 2, 0, synthesis_only=True)
        # A synthesis-only source fixture is legitimate to the shared auditor.
        self.builder.verify_current_source(self.fixture, self.inputs)
        # Add fully rebound mock PNR outputs, result and offline acceptance.
        # Those files cannot turn its explicit synthesis mode into installation.
        self.acceptance()
        with mock.patch.object(installer, 'state', side_effect=AssertionError('network accessed')), \
             mock.patch.object(installer, 'programmers', side_effect=AssertionError('inventory accessed')), \
             mock.patch.object(installer, 'scan_cables', side_effect=AssertionError('cable enumeration accessed')), \
             mock.patch.object(installer.subprocess, 'run', side_effect=AssertionError('programmer accessed')):
            with self.assertRaisesRegex(ValueError, 'Synthesis-only build has no physical acceptance'):
                installer.install(self.build)
        self.assertEqual(list(self.build.glob('hardware_*')), [])

    def test_unknown_build_modes_are_rejected_by_real_shared_auditor(self):
        for mode in ('syn', 'pnr-only', '', False, ['full']):
            with self.subTest(mode=mode):
                self.inputs['build_mode'] = mode
                self.rebind_input()
                with self.assertRaisesRegex(ValueError, 'Unknown build mode'):
                    installer.verify(self.build)

    def test_rebound_extra_global_cst_cannot_bypass_shared_audit(self):
        path = self.fixture / 'acg720_ano_port.cst'
        path.write_text(path.read_text() + 'CLOCK_LOC "unproven" BUFG = CE|SR|LOGIC;\n')
        self.rebind_input('acg720_ano_port.cst')
        with self.assertRaisesRegex(ValueError, 'Physical CST'):installer.verify(self.build)

    def test_rebound_changed_pnr_tcl_cannot_bypass_shared_audit(self):
        path = self.fixture / 'build.tcl'
        path.write_text(path.read_text().replace('run pnr', 'run all'))
        self.rebind_input('build.tcl')
        with self.assertRaisesRegex(ValueError, 'bounded run/options'):installer.verify(self.build)

    def test_rebound_rtl_extra_or_wrong_type_project_is_rejected(self):
        path = self.fixture / 'acg720_ano_port.gprj'
        canonical = path.read_bytes()
        variants = [(self.root / 'source/acg720_ano_port.gprj').read_bytes(),
                    canonical.replace(b'file.netlist', b'file.verilog'),
                    canonical.replace(b'</FileList>', b'<File path="acg720_ano_port.v" type="file.verilog" enable="1" /></FileList>'),
                    canonical.replace(b'<Project>', b'<Project unexpected="change">')]
        for data in variants:
            with self.subTest(data=data):
                path.write_bytes(data);self.rebind_input('acg720_ano_port.gprj')
                with self.assertRaisesRegex(ValueError, 'Derived GPRJ'):installer.verify(self.build)

    def test_derived_unknown_schema_or_missing_logical_map_is_rejected(self):
        original = json.loads(json.dumps(self.inputs))
        for missing in (False, True):
            with self.subTest(missing=missing):
                self.inputs = json.loads(json.dumps(original))
                if missing:self.inputs.pop('logical_source_sha256')
                else:self.inputs['derived_netlist']['schema'] = 'unknown'
                self.rebind_input()
                with self.assertRaises(ValueError):installer.verify(self.build)

    def test_changed_donor_receipt_is_rejected_by_shared_audit(self):
        path = self.donor / 'inputs.json'
        data = installer.read_json(path);data['created_utc'] = 'tampered'
        self.builder.write_json(path, data)
        with self.assertRaisesRegex(ValueError, 'Donor input receipt'):installer.verify(self.build)

    def test_changed_copied_netlist_is_rejected_by_shared_audit(self):
        path = self.fixture / 'impl/gwsynthesis/acg720_ano_port.vg'
        path.write_bytes(path.read_bytes() + b'// tampered copied VG\n')
        with self.assertRaisesRegex(ValueError, 'netlist hash mismatch'):installer.verify(self.build)

    def test_changed_synthesis_receipt_is_rejected_by_shared_audit(self):
        path = self.build / 'donor_synthesis.log'
        path.write_bytes(path.read_bytes() + b'// tampered synthesis receipt\n')
        with self.assertRaisesRegex(ValueError, 'synthesis completion prefix'):installer.verify(self.build)

    def test_test_receipt_must_bind_logical_rather_than_physical_cst_and_gprj(self):
        path = self.build / TEST_RECEIPT_NAME
        original = path.read_text()
        for name in ('acg720_ano_port.cst', 'acg720_ano_port.gprj'):
            with self.subTest(name=name):
                receipt = json.loads(original)
                receipt['source_sha256'][name] = self.inputs['source_sha256'][name]
                self.builder.write_json(path, receipt);self.bind_acceptance()
                with self.assertRaisesRegex(ValueError, 'Tested source differs'):installer.verify(self.build)

    def test_derived_result_requires_reported_global_assignment(self):
        path = self.build / 'result.json'
        result = installer.read_json(path);result.pop('observer_global_contract_passed')
        self.builder.write_json(path, result);self.bind_acceptance()
        with self.assertRaisesRegex(ValueError, 'global assignment'):installer.verify(self.build)

    def test_derived_result_requires_explicit_absence_of_automatic_synthesis(self):
        path = self.build / 'result.json'
        original = path.read_text()
        for flag in (None, False, 1):
            with self.subTest(flag=flag):
                result = json.loads(original)
                if flag is None:result.pop('pnr_only_synthesis_absent')
                else:result['pnr_only_synthesis_absent'] = flag
                self.builder.write_json(path, result);self.bind_acceptance()
                with self.assertRaisesRegex(ValueError, 'automatic synthesis'):installer.verify(self.build)


if __name__ == '__main__':
    unittest.main(verbosity=2)
