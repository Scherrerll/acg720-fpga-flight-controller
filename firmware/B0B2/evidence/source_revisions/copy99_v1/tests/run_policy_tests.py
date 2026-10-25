"""Actual B0B0/B0B2 IMU-chain A/B, no Gowin, hardware or programmable receipt.

--verify-existing reads the successful receipt and hashes only. It never runs
Icarus or VVP, and refuses missing fields or drift in source, runner, TB or logs.
"""
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = 'b0b2.imu-policy-tests.v1'
FILES = ["imu_pipeline_pipelined.v", "imu_temporal_check_pipelined.v",
         "imu_checked_guard_pipelined.v", "ano_attitude_estimator.v",
         "bmi088_reader.v", "spi_uart_modules.v", "cordic_atan2.v"]
UNCHANGED = ("imu_pipeline_pipelined.v", "imu_checked_guard_pipelined.v", "ano_attitude_estimator.v")
COMMON_MARKERS = ('PASS startup_motion:', 'PASS startup:', 'PASS dynamic_accel:',
                  'PASS explicit_bad_sample', 'PASS invalid_transport:', 'PASS true_gap_20ms',
                  'PASS true_gap_30ms', 'PASS exact_deadline:', 'PASS true_gap_60ms',
                  'PASS recovery_gravity:', 'PASS overrun:', 'PASS integrated_policy_suite')
REPORT_KEYS = {'schema', 'baseline', 'baseline_manifest_sha256', 'baseline_hashes_verified',
               'hardware_accessed', 'flight_ready', 'tests', 'started_utc',
               'unchanged_control_projection', 'testbench_sha256', 'runner_sha256',
               'testbench_snapshot_path', 'testbench_stable_during_simulation',
               'runner_stable_during_simulation', 'passed'}
TEST_KEYS = {'returncode', 'output', 'source_stable_during_simulation',
             'source_sha256', 'log_path', 'log_sha256'}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def control_tokens(path):
    text = path.read_text()
    text = re.sub(r"// DIAG_TAP_BEGIN\n.*?// DIAG_TAP_END\n", "", text, flags=re.S)
    text = re.sub(r"//[^\n]*|/\*.*?\*/", "", text, flags=re.S)
    return re.findall(r"\w+|[^\s]", text)


def verified_baseline(baseline):
    frozen = json.loads((ROOT / 'baseline.json').read_text())['source_sha256']
    if not frozen:
        raise ValueError('Empty frozen baseline hash set')
    for name, expected in frozen.items():
        if digest(baseline / name) != expected:
            raise ValueError('Frozen baseline changed: ' + name)
    for name in UNCHANGED:
        if control_tokens(baseline / 'core' / name) != control_tokens(ROOT / 'source/core' / name):
            raise ValueError('Protected control source changed: ' + name)
    return frozen


def variant_sources(variant, baseline):
    source = baseline if variant == 'B0B0' else ROOT / 'source'
    names = FILES + ([] if variant == 'B0B0' else ['imu_diagnostic_tap.v'])
    return source, [source / 'core' / name for name in names]


def output_ok(variant, text):
    variant_markers = (('REPRODUCED original_failure gravity_qualified_alternation:',
                        'REPRODUCED original_gyro_fill braking') if variant == 'B0B0' else
                       ('FIXED gravity_qualified_alternation:', 'FIXED gyro_zero_braking'))
    return all(x in text for x in COMMON_MARKERS + variant_markers) and 'FATAL:' not in text


def bound_output_path(value):
    path = Path(value).resolve()
    root = (ROOT.parents[1] / 'out/B0B2/policy').resolve()
    if root not in path.parents:
        raise ValueError('Receipt artifact path escapes the policy output directory')
    return path


def verify_existing(baseline, report_path=None):
    """Read-only validation; deliberately contains no subprocess/compile call."""
    baseline = baseline.resolve()
    frozen = verified_baseline(baseline)
    path = report_path or ROOT / 'evidence/policy_tests.json'
    report = json.loads(path.read_text())
    if set(report) != REPORT_KEYS or report['schema'] != SCHEMA:
        raise ValueError('Unknown or incomplete policy receipt schema')
    if (report['passed'] is not True or report['hardware_accessed'] is not False
            or report['flight_ready'] is not False
            or report['runner_stable_during_simulation'] is not True
            or report['testbench_stable_during_simulation'] is not True):
        raise ValueError('Receipt does not bind a successful stable offline run')
    if (Path(report['baseline']).resolve() != baseline or report['baseline_hashes_verified'] != len(frozen)
            or report['baseline_manifest_sha256'] != digest(ROOT / 'baseline.json')
            or report['unchanged_control_projection'] != list(UNCHANGED)):
        raise ValueError('Baseline/control projection binding differs')
    if report['runner_sha256'] != digest(Path(__file__)):
        raise ValueError('Policy runner changed since the run')
    if report['testbench_sha256'] != digest(ROOT / 'tests/policy_pipeline_tb.v'):
        raise ValueError('Policy testbench changed since the run')
    if digest(bound_output_path(report['testbench_snapshot_path'])) != report['testbench_sha256']:
        raise ValueError('Compiled testbench snapshot changed')
    if set(report['tests']) != {'B0B0', 'B0B2'}:
        raise ValueError('Missing/unknown policy variant')
    for variant, test in report['tests'].items():
        if (set(test) != TEST_KEYS or type(test['returncode']) is not int or test['returncode'] != 0
                or test['source_stable_during_simulation'] is not True):
            raise ValueError('Incomplete or failed policy run: ' + variant)
        source, paths = variant_sources(variant, baseline)
        actual = {p.relative_to(source).as_posix(): digest(p) for p in paths}
        if test['source_sha256'] != actual:
            raise ValueError('Compiled source changed: ' + variant)
        log = bound_output_path(test['log_path'])
        if digest(log) != test['log_sha256'] or log.read_text().strip() != test['output']:
            raise ValueError('Policy log changed: ' + variant)
        if not output_ok(variant, test['output']):
            raise ValueError('Policy log misses required behavioral assertions: ' + variant)
    return report


def run_variant(variant, baseline, temporary, snapshot, executable, vvp, env):
    source, sources = variant_sources(variant, baseline)
    hashes = {p.relative_to(source).as_posix(): digest(p) for p in sources}
    product = temporary / (variant + '_policy.vvp')
    log = temporary / (variant + '_policy.log')
    defines = [] if variant == 'B0B0' else ['-DPOLICY_FIXED']
    lines = []
    try:
        subprocess.run([executable, '-g2012', *defines, '-s', 'policy_pipeline_tb', '-o', str(product),
                        str(snapshot), *map(str, sources)], check=True, cwd=ROOT, env=env)
        print('Running actual ' + variant + ' policy chain', flush=True)
        # -i is VVP unbuffered stdio; -n makes $stop noninteractive. No UI/hardware.
        with subprocess.Popen([vvp, '-i', '-n', str(product)], stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                              text=True, cwd=ROOT, env=env) as run:
            for line in run.stdout:
                lines.append(line)
                print('[' + variant + '] ' + line, end='', flush=True)
            returncode = run.wait()
    except (OSError, subprocess.CalledProcessError) as error:
        returncode = -1
        lines.append('Compile/simulation failed: ' + str(error) + '\n')
    output = ''.join(lines)
    log.write_text(output)
    stable = hashes == {p.relative_to(source).as_posix(): digest(p) for p in sources}
    return dict(returncode=returncode, output=output.strip(), source_stable_during_simulation=stable,
                source_sha256=hashes, log_path=str(log.resolve()), log_sha256=digest(log))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--iverilog')
    ap.add_argument('--baseline', type=Path, default=ROOT.parent / 'B0B0/source_snapshot')
    ap.add_argument('--verify-existing', action='store_true', help='Read-only receipt/hash audit; never simulate')
    args = ap.parse_args()
    baseline = args.baseline.resolve()
    if args.verify_existing:
        verify_existing(baseline)
        print(json.dumps(dict(passed=True, reused_existing_evidence=True, simulation_started=False,
                              evidence=str(ROOT / 'evidence/policy_tests.json'))))
        return 0
    frozen = verified_baseline(baseline)
    runner_before = digest(Path(__file__))
    tb = ROOT / 'tests/policy_pipeline_tb.v'
    tb_before = digest(tb)
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ')
    result = dict(schema=SCHEMA, baseline=str(baseline), baseline_manifest_sha256=digest(ROOT / 'baseline.json'),
                  baseline_hashes_verified=len(frozen), hardware_accessed=False, flight_ready=False,
                  tests={}, started_utc=stamp, unchanged_control_projection=list(UNCHANGED),
                  testbench_sha256=tb_before, runner_sha256=runner_before,
                  testbench_stable_during_simulation=False, runner_stable_during_simulation=False, passed=False)
    executable = args.iverilog or shutil.which('iverilog')
    if not executable:
        executable = str(Path.home() / 'Desktop/apple/.tools/iverilog/app/bin/iverilog.exe')
    vvp = str(Path(executable).with_name('vvp.exe' if os.name == 'nt' else 'vvp'))
    temporary = ROOT.parents[1] / 'out/B0B2/policy' / stamp
    temporary.mkdir(parents=True, exist_ok=False)
    (ROOT / 'evidence').mkdir(exist_ok=True)
    snapshot = temporary / 'policy_pipeline_tb.v'
    snapshot.write_bytes(tb.read_bytes())
    result['testbench_snapshot_path'] = str(snapshot.resolve())
    env = {**os.environ, **{key: str(temporary) for key in ('TMP', 'TEMP', 'TMPDIR')}}
    with ThreadPoolExecutor(max_workers=2) as pool:
        pending = {pool.submit(run_variant, name, baseline, temporary, snapshot, executable, vvp, env): name
                   for name in ('B0B0', 'B0B2')}
        for future in as_completed(pending):
            result['tests'][pending[future]] = future.result()
            (ROOT / 'evidence/policy_tests.json').write_text(json.dumps(result, indent=2) + '\n')
    result['testbench_stable_during_simulation'] = tb_before == digest(tb) == digest(snapshot)
    result['runner_stable_during_simulation'] = runner_before == digest(Path(__file__))
    result['passed'] = (result['testbench_stable_during_simulation'] and result['runner_stable_during_simulation']
                        and all(x['returncode'] == 0 and x['source_stable_during_simulation']
                                and output_ok(v, x['output']) for v, x in result['tests'].items()))
    report = ROOT / 'evidence/policy_tests.json'
    report.write_text(json.dumps(result, indent=2) + '\n')
    (ROOT / 'evidence' / ('policy_tests_' + stamp + '.json')).write_text(json.dumps(result, indent=2) + '\n')
    if result['passed']:
        verify_existing(baseline)
    print(json.dumps(dict(passed=result['passed'], evidence=str(report))), flush=True)
    return int(not result['passed'])


if __name__ == '__main__':
    raise SystemExit(main())
