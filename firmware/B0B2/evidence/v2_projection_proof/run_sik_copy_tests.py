"""Replay actual-tap v1-to-v2 projected 120k-cycle SiK proof.

Only the archived reference is renamed into the fresh output directory. The
candidate and actual tap are compiled directly from current source. No device,
serial, programmer, build or state-API operation is available in this runner.
"""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys

FW = Path(__file__).resolve().parents[1]
REPO = FW.parents[1]
OLD = FW / 'evidence/source_revisions/copy99_v1/source/sik_imu_diagnostic.v'
OLD_SHA256 = '7783baba34cc7cdc014d17f38e9e0d5f52210e1d8b02bde49a5f308d8ee3160e'
CANDIDATE = FW / 'source/sik_imu_diagnostic.v'
TAP = FW / 'source/core/imu_diagnostic_tap.v'
TB = FW / 'tests/sik_copy_contract_tb.v'
RUNNER = Path(__file__).resolve()
COVERAGE = re.compile(
    r'PASS v2_projection actual_tap miter (\d+) cycles, projected448bit\+tick exact every edge; '
    r'raw_pose_same=(\d+) rejects=(\d+) held_updates=(\d+) hold_rise=(\d+) '
    r'hold_fall=(\d+) max_no_pose=(\d+) reset_cycles=(\d+)')
COVERAGE_NAMES = ('cycles', 'raw_pose_same', 'rejects', 'held_updates',
                  'hold_rise', 'hold_fall', 'max_no_pose', 'reset_cycles')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_hashes():
    return {p.relative_to(FW / 'source').as_posix(): sha(p)
            for p in sorted((FW / 'source').rglob('*')) if p.is_file()}


def executable(value):
    path = Path(shutil.which(str(value)) or value).resolve()
    if not path.is_file():
        raise FileNotFoundError(str(path))
    return path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path,
                        help='new output directory; existing paths are rejected')
    args = parser.parse_args()
    output = (args.output or REPO / 'out/B0B2' /
              ('sik_v2_projection_' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ'))).resolve()
    # Do not erase, reuse or replace previous evidence, even on failed runs.
    output.mkdir(parents=True, exist_ok=False)
    result = dict(schema='b0b2.sik-copy-tests.v2', passed=False,
                  hardware_accessed=False, output=str(output),
                  started_at_utc=datetime.now(timezone.utc).isoformat(),
                  scope='Actual tap, archived copy99/v1 vs current v2:448 summary bits plus tick; two zero slots intentionally excluded',
                  full_protocol_equivalence=False, preserved_summary_bits=448,
                  unavailable_summary_slots={'latest_rejected_source_id': [319, 288],
                                             'first_protection_time_ms_low32': [95, 64]},
                  commands=[])
    try:
        inputs = {'reference': OLD, 'candidate': CANDIDATE, 'tap': TAP,
                  'testbench': TB, 'runner': RUNNER}
        result['inputs'] = {name: {'path': str(path), 'sha256': sha(path)}
                            for name, path in inputs.items()}
        if result['inputs']['reference']['sha256'] != OLD_SHA256:
            raise ValueError('archived copy99_v1 reference SHA256 mismatch')
        before = source_hashes()
        result['source_sha256'] = before
        result['verification_scripts_sha256'] = {
            path.relative_to(REPO).as_posix(): sha(path) for path in (TB, RUNNER)}
        iv = executable(os.environ.get('IVERILOG') or shutil.which('iverilog') or
                        REPO.parents[1] / '.tools/iverilog/app/bin/iverilog.exe')
        vvp = executable(os.environ.get('VVP') or
                         iv.with_name('vvp.exe' if os.name == 'nt' else 'vvp'))
        tools = {'iverilog': iv, 'vvp': vvp, 'python': Path(sys.executable).resolve()}
        result['tools'] = {name: {'path': str(path), 'sha256': sha(path)}
                           for name, path in tools.items()}
        reference = OLD.read_text(encoding='utf-8')
        declaration = 'module sik_imu_diagnostic('
        if reference.count(declaration) != 1:
            raise ValueError('reference module declaration is not unique')
        renamed = output / 'sik_copy_reference.v'
        renamed.write_text(reference.replace(declaration, 'module sik_original('),
                           encoding='utf-8', newline='\n')
        result['renamed_reference_sha256'] = sha(renamed)
        env = dict(os.environ, **{key: str(output) for key in ('TMP', 'TEMP', 'TMPDIR')})

        def run(command, log_name):
            command = list(map(str, command))
            entry = {'argv': command, 'cwd': str(output), 'log': log_name}
            result['commands'].append(entry)
            try:
                proc = subprocess.run(command, cwd=output, env=env,
                                      capture_output=True, text=True,
                                      encoding='utf-8', errors='replace', timeout=180)
            except subprocess.TimeoutExpired as exc:
                def decoded(value):
                    return value.decode('utf-8', errors='replace') if isinstance(value, bytes) else value or ''
                (output / log_name).write_text(decoded(exc.stdout) + decoded(exc.stderr),
                                               encoding='utf-8')
                entry['timeout_seconds'] = 180
                entry['log_sha256'] = sha(output / log_name)
                raise
            log = proc.stdout + proc.stderr
            (output / log_name).write_text(log, encoding='utf-8')
            entry.update(returncode=proc.returncode, log_sha256=sha(output / log_name))
            if log.strip():
                print(log.strip(), flush=True)
            proc.check_returncode()
            return log

        target = output / 'sik_copy_contract.vvp'
        run([iv, '-g2012', '-s', 'sik_copy_contract_tb', '-o', target,
             renamed, CANDIDATE, TAP, TB], 'compile.log')
        stdout = run([vvp, target], 'simulation.log')
        matches = COVERAGE.findall(stdout)
        if len(matches) != 1:
            raise ValueError('missing or ambiguous completed miter coverage')
        coverage = dict(zip(COVERAGE_NAMES, map(int, matches[0])))
        result['coverage'] = coverage
        window = re.findall(r'COVERAGE v2_projection window_rises=(\d+) held_window=(\d+) window_event_same=(\d+)', stdout)
        if len(window) != 1 or any(int(value) < 1 for value in window[0]):
            raise ValueError('missing existing window/hold/same-edge event coverage')
        result['window_coverage'] = dict(zip(('window_rises', 'held_window', 'window_event_same'),
                                           map(int, window[0])))
        minimum = {'raw_pose_same': 100, 'rejects': 100, 'held_updates': 100,
                   'hold_rise': 100, 'hold_fall': 100, 'max_no_pose': 6000,
                   'reset_cycles': 5}
        if coverage['cycles'] != 120000 or any(coverage[k] < v for k, v in minimum.items()):
            raise ValueError('existing miter coverage threshold not reached')
        result['source_unchanged'] = source_hashes() == before
        result['inputs_unchanged'] = all(sha(path) == result['inputs'][name]['sha256']
                                         for name, path in inputs.items())
        result['tools_unchanged'] = all(sha(path) == result['tools'][name]['sha256']
                                        for name, path in tools.items())
        if not all(result[key] for key in ('source_unchanged', 'inputs_unchanged', 'tools_unchanged')):
            raise ValueError('an input changed during the run')
        result['artifacts_sha256'] = {name: sha(output / name) for name in
                                     ('sik_copy_reference.v', 'compile.log',
                                      'simulation.log', 'sik_copy_contract.vvp')}
        result['passed'] = True
    except Exception as exc:
        result['error'] = type(exc).__name__ + ': ' + str(exc)
        print(result['error'], file=sys.stderr, flush=True)
    finally:
        result['finished_at_utc'] = datetime.now(timezone.utc).isoformat()
        (output / 'result.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(('PASS' if result['passed'] else 'FAIL') + ' SiK copy contract: ' + str(output), flush=True)
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
