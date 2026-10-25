"""Bind current diagnostics tests and independent physical audit to one B0B1 build."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET

from build import ROOT, REPO, sha, write_json


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--build', required=True, type=Path)
    ap.add_argument('--iverilog', type=Path)
    args = ap.parse_args()
    folder = args.build.resolve()
    acceptance_path = folder / 'offline_acceptance.json'
    if acceptance_path.exists():
        raise ValueError('This build already has an acceptance record; preserve it')
    if not (folder / 'result.json').exists():
        raise ValueError('Wait for the real vendor process to finish')
    run_dir = folder / datetime.now(timezone.utc).strftime('verification_%Y%m%dT%H%M%S_%fZ')
    run_dir.mkdir()
    logs = []

    def run(name, command, cwd=REPO, env=None):
        result = subprocess.run(list(map(str, command)), cwd=cwd, env=env,
                                capture_output=True, text=True, timeout=300)
        log = run_dir / (name + '.log')
        log.write_text(result.stdout + result.stderr, encoding='utf8')
        unit_count = re.search(r'Ran (\d+) tests?', result.stdout + result.stderr)
        if '-m' in command and 'unittest' in command and (not unit_count or int(unit_count[1]) == 0):
            raise RuntimeError(name + ' did not execute any unit tests')
        logs.append(dict(name=name, command=list(map(str, command)),
                         log=log.relative_to(folder).as_posix(),
                         log_sha256=sha(log), returncode=result.returncode,
                         passed=result.returncode == 0))
        print(name + (' PASS' if result.returncode == 0 else ' FAIL'), flush=True)
        if result.returncode:
            raise RuntimeError(name + ' failed; see ' + str(log))

    py = [sys.executable, '-B']
    receipt = dict(schema='b0b1.tests.v1', passed=False, tests=logs,
                   hardware_accessed=False, flash_changed=False, flight_ready=False)
    receipt_path = folder / ('tests_receipt_' + run_dir.name + '.json')
    try:
        run('physical_audit', py + [ROOT / 'tools/build.py', '--collect', folder])
        physical = json.loads((folder / 'result.json').read_text())
        if not physical['passed']:
            raise ValueError('Independent physical audit failed')
        fixture = folder / 'fixture'
        for p in (ROOT / 'source').rglob('*'):
            if p.is_file() and p.name != 'build.tcl' and sha(p) != sha(fixture / p.relative_to(ROOT / 'source')):
                raise ValueError('Current source differs from built source: ' + str(p))
        run('passive_source', py + [ROOT / 'tools/verify_passive.py', '--output', run_dir / 'passive_source.json'])
        run('passivity_lhs', py + ['-m', 'unittest', 'discover', '-s', ROOT / 'tests', '-p', 'test_passivity.py'])
        run('build_audit_fail_closed', py + ['-m', 'unittest', 'discover', '-s', ROOT / 'tests', '-p', 'test_build_audit.py'])
        run('tap', py + [ROOT / 'tests/run_tap_tests.py'])
        run('uart', py + [ROOT / 'tests/uart_test.py'])
        run('usb_protocol', py + ['-m', 'unittest', 'discover', '-s', ROOT / 'tests', '-p', 'test_protocol.py'])
        run('sram_fail_closed', py + ['-m', 'unittest', 'discover', '-s', ROOT / 'tests', '-p', 'test_install_sram.py'])
        run('tracking_identity', py + ['-m', 'unittest', 'discover', '-s', REPO / 'web/flight-console/local', '-p', 'test_attitude_tracking.py'])
        run('receiver_wrapper', py + ['-m', 'unittest', 'discover', '-s', REPO / 'web/flight-console/local', '-p', 'test_receiver_setpoints.py'])
        iv = args.iverilog or shutil.which('iverilog')
        if not iv:
            iv = Path.home() / 'Desktop/apple/.tools/iverilog/app/bin/iverilog.exe'
        temp = run_dir / 'tmp'
        temp.mkdir()
        env = dict(os.environ, **{key: str(temp) for key in ('TMP', 'TEMP', 'TMPDIR')})
        files = [fixture / f.attrib['path'] for f in ET.parse(fixture / 'acg720_ano_port.gprj').findall('.//File')
                 if f.attrib.get('enable') == '1' and f.attrib.get('type') == 'file.verilog']
        run('whole_top_elaboration', [iv, '-g2012', '-Wall', '-I', fixture, '-s', 'acg720_ano_port',
                                     '-o', run_dir / 'top.vvp', *files], env=env)
        # unittest silently succeeds with zero tests: require named executable suites.
        for name in ('test_passivity.py', 'test_build_audit.py', 'test_protocol.py', 'test_install_sram.py'):
            if not (ROOT / 'tests' / name).is_file():
                raise ValueError('Required suite missing: ' + name)
        receipt['source_sha256'] = {p.relative_to(ROOT / 'source').as_posix(): sha(p)
                                    for p in (ROOT / 'source').rglob('*') if p.is_file()}
        receipt['verification_scripts_sha256'] = {p.relative_to(ROOT).as_posix(): sha(p)
                                                  for d in ('tests', 'ground', 'tools')
                                                  for p in (ROOT / d).rglob('*')
                                                  if p.is_file() and p.suffix in ('.py', '.v', '.hex')}
        receipt['passed'] = True
    finally:
        write_json(receipt_path, receipt)
    acceptance = dict(schema='b0b1.offline-acceptance.v1', passed=True, build_id=0xB0B1,
                      result_sha256=sha(folder / 'result.json'), inputs_sha256=sha(folder / 'inputs.json'),
                      bitstream_sha256=physical['bitstream']['sha256'],
                      test_receipt=dict(path=receipt_path.name, sha256=sha(receipt_path)),
                      audit_runner_sha256=sha(ROOT / 'tools/build.py'),
                      verification_runner_sha256=sha(Path(__file__)),
                      hardware_accessed=False, flash_changed=False, flight_ready=False)
    write_json(acceptance_path, acceptance)
    print(str(acceptance_path), flush=True)


if __name__ == '__main__':
    main()
