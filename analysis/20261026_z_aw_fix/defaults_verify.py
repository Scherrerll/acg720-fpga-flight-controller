"""Repeat the isolated B0B4 ground tests; never connect a real device/service.

Run from any directory: python -X utf8 -B <this file>
The Python suite owns only mocked serial and its temporary loopback HTTP fixture;
the Node suite uses an in-memory DOM/fetch mock. No existing server is contacted.
"""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
OWN = ROOT / 'ground/B0B4'
OUT = OWN / 'test_results'
BASELINE = Path(__file__).with_name('defaults_baseline.json')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def frozen_check():
    baseline = json.loads(BASELINE.read_text(encoding='utf-8'))['hashes']
    paths = {
        'frozen_ground_B0B3': ROOT / 'ground/B0B3',
        'frozen_firmware_B0B3_source': ROOT / 'firmware/B0B3/source',
    }
    result = {}
    for name, expected in baseline.items():
        differences = [relative for relative, digest in expected.items()
                       if not (paths[name] / relative).is_file()
                       or sha(paths[name] / relative) != digest]
        if differences:
            raise AssertionError(f'Frozen baseline changed: {name}: {differences}')
        result[name] = {'checked_file_count': len(expected), 'unchanged': True}
    return result


def inputs():
    files = [p for p in OWN.rglob('*') if p.is_file()
             and not {'__pycache__', 'test_results'}.intersection(p.relative_to(OWN).parts)]
    files += [ROOT / 'firmware/B0B4/xy_pi_cli.py', Path(__file__), BASELINE]
    return {p.relative_to(ROOT).as_posix(): sha(p) for p in sorted(files)}


def run(name, command, env):
    started = datetime.now(timezone.utc).isoformat()
    process = subprocess.run(command, cwd=ROOT, env=env, capture_output=True)
    output = process.stdout + process.stderr
    log = OUT / f'{name}.log'
    log.write_bytes(output)
    receipt = {
        'command': command,
        'started_utc': started,
        'finished_utc': datetime.now(timezone.utc).isoformat(),
        'actual_exit_code': process.returncode,
        'log_sha256': sha(log),
        'scope': 'Mock serial and owned temporary loopback HTTP fixture only; no hardware'
                 if name == 'python' else 'In-memory DOM and fetch mock; no network',
    }
    if name == 'python':
        match = re.search(rb'Ran (\d+) tests? in ', output)
        receipt['test_count'] = int(match.group(1)) if match else None
        if receipt['test_count'] != 53:
            raise AssertionError('Expected the existing 53 Python tests')
    (OUT / f'{name}_result.json').write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    if process.returncode:
        sys.stderr.buffer.write(output)
        raise AssertionError(f'{name} returned {process.returncode}')
    return receipt


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    temporary = OUT / 'tmp'
    temporary.mkdir(exist_ok=True)
    env = dict(os.environ, PYTHONUTF8='1', PYTHONDONTWRITEBYTECODE='1',
               TEMP=str(temporary), TMP=str(temporary), TMPDIR=str(temporary))
    before = frozen_check()
    bound_inputs = inputs()
    python = run('python', [sys.executable, '-X', 'utf8', '-B', '-m', 'unittest',
                           'discover', '-s', 'ground/B0B4', '-p', 'test_xy_pi_*.py', '-v'], env)
    node_path = shutil.which('node')
    if node_path is None:
        raise AssertionError('Node is required for the dependency-free DOM/API harness')
    node = run('node', [node_path, 'ground/B0B4/test_xy_pi_ui.cjs'], env)
    if inputs() != bound_inputs:
        raise AssertionError('Bound test inputs changed during verification')
    result = {
        'result': 'PASS',
        'scope': 'Isolated B0B4 ground software only; no service, real serial, hardware, build or Git action',
        'frozen_baseline_before': before,
        'frozen_baseline_after': frozen_check(),
        'input_sha256': bound_inputs,
        'python': python,
        'node': node,
    }
    path = OUT / 'verification.json'
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'result': 'PASS', 'python_test_count': 53,
                      'verification': str(path), 'sha256': sha(path)}, ensure_ascii=False))


if __name__ == '__main__':
    main()
