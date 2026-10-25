"""Offline verification of the six existing progress diffs; never stages or edits source."""
from pathlib import Path
import datetime
import hashlib
import json
import os
import re
import subprocess
import sys

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
FILES = [
    'support/monitor_control.py',
    'support/server.py',
    'web/flight-console/local/attitude_tracking.py',
    'web/flight-console/local/receiver_setpoints.py',
    'web/flight-console/local/test_attitude_tracking.py',
    'web/flight-console/local/test_receiver_setpoints.py',
]

def sha_bytes(data):
    return hashlib.sha256(data).hexdigest()

def snapshot():
    values = {}
    for name in FILES:
        patch = subprocess.check_output(
            ['git', 'diff', '--no-ext-diff', '--binary', '--no-color', '--', name], cwd=ROOT)
        values[name] = {
            'file_sha256': sha_bytes((ROOT / name).read_bytes()),
            'dirty_diff_sha256': sha_bytes(patch),
            'dirty_diff_bytes': len(patch),
        }
    return values

assert not (OUT / 'results.json').exists(), 'Preserve this completed receipt; use a new output directory for another run'
before = snapshot()
started = datetime.datetime.now(datetime.timezone.utc).isoformat()
head_before = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
specs = [
    ('attitude_tracking', 'web/flight-console/local', 'test_attitude_tracking.py'),
    ('receiver_setpoints', 'web/flight-console/local', 'test_receiver_setpoints.py'),
    ('b0b2_protocol', 'firmware/B0B2/tests', 'test_protocol.py'),
]
inputs = {
    'started_utc': started,
    'repository': str(ROOT),
    'head_before': head_before,
    'six_inputs_before': before,
    'test_source_sha256': {
        f'{folder}/{pattern}': sha_bytes((ROOT / folder / pattern).read_bytes())
        for _, folder, pattern in specs
    },
    'runner_sha256': sha_bytes(Path(__file__).read_bytes()),
    'entry_review': {
        'receiver_wrapper': 'Test child explicitly passes --no-serial and --http-port 0; HTTP requests address only its own ephemeral loopback server',
        'b0b2_protocol': 'In-memory decoder/Dashboard/Recorder tests; isolated temporary clone under ignored out/B0B2 with cleanup; prepare_sik_receiver imports no serial/programmer APIs',
        'attitude_tracking': 'Pure field/protocol/identity unit tests',
        'hardware_or_existing_network_services_requested': False,
        'B0B3_rejection_unchanged': 'Actual legacy telemetry identity remains B0B2; the explicit unknown B0B3 target-tracking test is retained',
    },
    'fixture_override_environment_present': bool(os.environ.get('SIK_WIRE_FIXTURE')),
}
(OUT / 'inputs.json').write_text(json.dumps(inputs, indent=2) + '\n', encoding='utf-8')
env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONUTF8='1')
jobs = []
for name, folder, pattern in specs:
    command = [sys.executable, '-B', '-m', 'unittest', 'discover', '-s', folder, '-p', pattern, '-v']
    stream = (OUT / f'{name}.log').open('w', encoding='utf-8')
    process = subprocess.Popen(command, cwd=ROOT, env=env, stdin=subprocess.DEVNULL,
                               stdout=stream, stderr=subprocess.STDOUT, close_fds=True,
                               creationflags=subprocess.CREATE_NO_WINDOW)
    jobs.append((name, command, process, stream))
print('Started three offline suites: ' + ', '.join(name for name, _, _, _ in jobs), flush=True)
rows = []
for name, command, process, stream in jobs:
    code = process.wait()
    stream.close()
    log_path = OUT / f'{name}.log'
    output = log_path.read_text(encoding='utf-8')
    match = re.search(r'Ran (\d+) tests? in ([0-9.]+)s', output)
    row = {
        'name': name,
        'command': command,
        'exit_code': code,
        'actual_p_wait': code,
        'test_count': int(match[1]) if match else None,
        'reported_seconds': float(match[2]) if match else None,
        'unittest_OK': bool(re.search(r'^OK\s*$', output, re.M)),
        'log': log_path.name,
        'log_sha256': sha_bytes(log_path.read_bytes()),
    }
    rows.append(row)
    print(json.dumps(row), flush=True)
after = snapshot()
head_after = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
stable = before == after
result = {
    'passed': stable and all(r['exit_code'] == 0 and r['unittest_OK'] and r['test_count'] is not None for r in rows),
    'finished_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'repository': str(ROOT),
    'six_inputs_before': before,
    'six_inputs_after': after,
    'six_files_and_dirty_diffs_unchanged': stable,
    'head_before': head_before,
    'head_after': head_after,
    'suites': rows,
    'total_tests': sum(r['test_count'] or 0 for r in rows),
    'scope': 'The three requested offline unittest suites; no hardware, serial port or pre-existing real network service; only test-local loopback where explicitly used',
    'source_changed_by_runner': False,
    'git_staged_or_committed_by_runner': False,
    'inputs_sha256': sha_bytes((OUT / 'inputs.json').read_bytes()),
    'runner_sha256': sha_bytes(Path(__file__).read_bytes()),
}
(OUT / 'results.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'passed': result['passed'], 'total_tests': result['total_tests'],
                  'six_inputs_stable': stable, 'result_sha256': sha_bytes((OUT / 'results.json').read_bytes())}, indent=2), flush=True)
assert result['passed'], 'See the saved test logs and before/after receipt'
