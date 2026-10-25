"""Fail-closed receipt reuse tests; tiny temporary mocks, never run a simulator."""
from contextlib import redirect_stdout
from pathlib import Path
import importlib.util
import io
import json
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('b0b2_policy_receipt_under_test', ROOT / 'tests/run_policy_tests.py')
runner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runner)


class PolicyReceiptTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='b0b2_mock_policy_receipt_')
        self.addCleanup(temporary.cleanup)
        self.repo = Path(temporary.name).resolve()
        self.root = self.repo / 'firmware/B0B2'
        self.baseline = self.repo / 'firmware/B0B0/source_snapshot'
        self.out = self.repo / 'out/B0B2/policy/mock_run'
        for directory in (self.root / 'tests', self.root / 'source/core', self.baseline / 'core',
                          self.root / 'evidence', self.out):
            directory.mkdir(parents=True, exist_ok=True)
        for source in (self.root / 'source', self.baseline):
            for name in runner.FILES + ([] if source == self.baseline else ['imu_diagnostic_tap.v']):
                (source / 'core' / name).write_text('// NONPROGRAMMABLE MOCK\nmodule mock; endmodule\n')
        frozen = {p.relative_to(self.baseline).as_posix(): runner.digest(p)
                  for p in self.baseline.rglob('*') if p.is_file()}
        (self.root / 'baseline.json').write_text(json.dumps({'source_sha256': frozen}))
        tb = self.root / 'tests/policy_pipeline_tb.v'
        tb.write_text('// NONEXECUTABLE MOCK TESTBENCH\n')
        snapshot = self.out / 'policy_pipeline_tb.v'
        snapshot.write_bytes(tb.read_bytes())
        patch = mock.patch.object(runner, 'ROOT', self.root)
        patch.start()
        self.addCleanup(patch.stop)
        for name in ('run', 'Popen'):
            patch = mock.patch.object(runner.subprocess, name, side_effect=AssertionError('Receipt reuse must not launch a process'))
            patch.start()
            self.addCleanup(patch.stop)
        self.report = dict(schema=runner.SCHEMA, baseline=str(self.baseline),
                           baseline_manifest_sha256=runner.digest(self.root / 'baseline.json'),
                           baseline_hashes_verified=len(frozen), hardware_accessed=False, flight_ready=False,
                           tests={}, started_utc='MOCK', unchanged_control_projection=list(runner.UNCHANGED),
                           testbench_sha256=runner.digest(tb), runner_sha256=runner.digest(Path(runner.__file__)),
                           testbench_snapshot_path=str(snapshot), testbench_stable_during_simulation=True,
                           runner_stable_during_simulation=True, passed=True)
        for variant in ('B0B0', 'B0B2'):
            source, paths = runner.variant_sources(variant, self.baseline)
            markers = (('REPRODUCED original_failure gravity_qualified_alternation:',
                        'REPRODUCED original_gyro_fill braking') if variant == 'B0B0' else
                       ('FIXED gravity_qualified_alternation:', 'FIXED gyro_zero_braking'))
            output = '\n'.join(runner.COMMON_MARKERS + markers)
            log = self.out / (variant + '.log')
            log.write_text(output + '\n')
            self.report['tests'][variant] = dict(returncode=0, output=output,
                source_stable_during_simulation=True,
                source_sha256={p.relative_to(source).as_posix(): runner.digest(p) for p in paths},
                log_path=str(log), log_sha256=runner.digest(log))
        self.path = self.root / 'evidence/policy_tests.json'
        self.save()

    def save(self):
        self.path.write_text(json.dumps(self.report))

    def rejected(self):
        self.save()
        with self.assertRaises((ValueError, KeyError, OSError, TypeError)):
            runner.verify_existing(self.baseline)

    def test_valid_reuse_is_read_only_and_does_not_launch_tools(self):
        before = runner.digest(self.path)
        self.assertTrue(runner.verify_existing(self.baseline)['passed'])
        self.assertEqual(runner.digest(self.path), before)

    def test_cli_reuse_does_not_launch_tools(self):
        with mock.patch.object(sys, 'argv', ['run_policy_tests.py', '--verify-existing']), redirect_stdout(io.StringIO()) as output:
            self.assertEqual(runner.main(), 0)
        self.assertIn('"simulation_started": false', output.getvalue())

    def test_unknown_schema_fails(self):
        self.report['schema'] = 'future/unknown'
        self.rejected()

    def test_missing_and_unknown_fields_fail(self):
        self.report.pop('runner_sha256')
        self.rejected()
        self.report['unknown'] = True
        self.rejected()

    def test_failed_or_unstable_receipt_fails(self):
        for field in ('passed', 'runner_stable_during_simulation', 'testbench_stable_during_simulation'):
            with self.subTest(field=field):
                self.report[field] = False
                self.rejected()
                self.report[field] = True

    def test_hardware_or_flight_claim_fails(self):
        self.report['hardware_accessed'] = True
        self.rejected()
        self.report['hardware_accessed'] = False
        self.report['flight_ready'] = True
        self.rejected()

    def test_boolean_or_nonzero_returncode_fails(self):
        for value in (False, 1, None):
            with self.subTest(value=value):
                self.report['tests']['B0B2']['returncode'] = value
                self.rejected()

    def test_source_key_omission_fails(self):
        self.report['tests']['B0B2']['source_sha256'].pop('core/imu_temporal_check_pipelined.v')
        self.rejected()

    def test_current_policy_source_drift_fails(self):
        (self.root / 'source/core/imu_temporal_check_pipelined.v').write_text('// CHANGED MOCK\n')
        self.rejected()

    def test_baseline_source_drift_fails(self):
        (self.baseline / 'core/imu_temporal_check_pipelined.v').write_text('// CHANGED FROZEN MOCK\n')
        self.rejected()

    def test_runner_and_testbench_hash_drift_fail(self):
        for field in ('runner_sha256', 'testbench_sha256'):
            with self.subTest(field=field):
                original = self.report[field]
                self.report[field] = '0' * 64
                self.rejected()
                self.report[field] = original

    def test_log_hash_or_content_drift_fails(self):
        log = Path(self.report['tests']['B0B2']['log_path'])
        log.write_text(log.read_text() + 'CHANGED MOCK LOG\n')
        self.rejected()

    def test_source_stability_false_fails(self):
        self.report['tests']['B0B2']['source_stable_during_simulation'] = False
        self.rejected()

    def test_missing_variant_fails(self):
        self.report['tests'].pop('B0B0')
        self.rejected()

    def test_path_outside_bound_output_fails(self):
        outside = self.repo / 'unrelated.log'
        outside.write_text(self.report['tests']['B0B2']['output'])
        self.report['tests']['B0B2']['log_path'] = str(outside)
        self.report['tests']['B0B2']['log_sha256'] = runner.digest(outside)
        self.rejected()

    def test_required_behavior_marker_missing_even_with_matching_hash_fails(self):
        test = self.report['tests']['B0B2']
        test['output'] = test['output'].replace('PASS exact_deadline:', 'MISSING')
        log = Path(test['log_path'])
        log.write_text(test['output'])
        test['log_sha256'] = runner.digest(log)
        self.rejected()


if __name__ == '__main__':
    unittest.main(verbosity=2)
