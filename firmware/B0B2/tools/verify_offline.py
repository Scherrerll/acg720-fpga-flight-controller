"""Bind repair regressions and independent physical audit to one B0B2 build."""
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

from build import ROOT, REPO, sha, write_json, verify_current_source


def verification_inputs():
    return dict(
        source_sha256={p.relative_to(ROOT / 'source').as_posix(): sha(p)
                       for p in (ROOT / 'source').rglob('*') if p.is_file()},
        verification_scripts_sha256={p.relative_to(ROOT).as_posix(): sha(p)
            for directory in ('tests', 'ground', 'tools')
            for p in (ROOT / directory).rglob('*')
            if p.is_file() and p.suffix in ('.py', '.v', '.hex')})


def require_unchanged_inputs(before):
    if verification_inputs() != before:
        raise ValueError('Verification inputs changed while tests ran; preserve this failed run and retry after freezing edits')


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
    initial_inputs = verification_inputs()

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
    receipt = dict(schema='b0b2.tests.v1', passed=False, tests=logs,
                   **initial_inputs, verification_inputs_unchanged=False,
                   hardware_accessed=False, flash_changed=False, flight_ready=False)
    receipt_path = folder / ('tests_receipt_' + run_dir.name + '.json')
    try:
        run('physical_audit', py + [ROOT / 'tools/build.py', '--collect', folder])
        physical = json.loads((folder / 'result.json').read_text())
        if not physical['passed']:
            raise ValueError('Independent physical audit failed')
        fixture = folder / 'fixture'
        verify_current_source(fixture, json.loads((folder / 'inputs.json').read_text()))
        run('bounded_source', py + [ROOT / 'tools/verify_design.py', '--output', run_dir / 'design_source.json'])
        run('passivity_lhs', py + ['-m', 'unittest', 'discover', '-s', ROOT / 'tests', '-p', 'test_passivity.py'])
        run('build_audit_fail_closed', py + ['-m', 'unittest', 'discover', '-s', ROOT / 'tests', '-p', 'test_build_audit.py'])
        run('policy_receipt_fail_closed', py + ['-m', 'unittest', 'discover', '-s', ROOT / 'tests', '-p', 'test_policy_receipt.py'])
        run('policy_ab_bound_evidence', py + [ROOT / 'tests/run_policy_tests.py', '--verify-existing'])
        run('temporal_contract', py + [ROOT / 'tests/run_temporal_contract.py'])
        sik_dir, copy_dir = run_dir / 'sik_diagnostic', run_dir / 'sik_copy_contract'
        run('sik_diagnostic', py + [ROOT / 'tests/run_sik_tests.py', '--output', sik_dir])
        run('sik_copy_contract', py + [ROOT / 'tests/run_sik_copy_tests.py', '--output', copy_dir])
        for subdir, schema in ((sik_dir, 'b0b2.sik-tests.v1'), (copy_dir, 'b0b2.sik-copy-tests.v2')):
            child_receipt = json.loads((subdir / 'result.json').read_text())
            if (child_receipt.get('passed') is not True or child_receipt.get('schema') != schema or
                    child_receipt.get('source_sha256') != initial_inputs['source_sha256']):
                raise ValueError('Subtest receipt is not a passing result for these exact sources: ' + str(subdir))
        sik_receipt = json.loads((sik_dir / 'result.json').read_text())
        copy_receipt = json.loads((copy_dir / 'result.json').read_text())
        if (sik_receipt.get('diagnostic_version') != 2 or sik_receipt.get('wire_bytes') != 644 or
                sik_receipt.get('legacy_bytes_equal') != 568 or
                sik_receipt.get('wire_sha256') != sha(sik_dir / 'sik_wire.hex') or
                copy_receipt.get('preserved_summary_bits') != 448 or
                copy_receipt.get('full_protocol_equivalence') is not False):
            raise ValueError('Subtest receipt does not establish the current v2 wire/projection contract')
        receipt['subtest_artifacts_sha256'] = {p.relative_to(folder).as_posix(): sha(p)
            for p in (sik_dir / 'result.json', sik_dir / 'sik_wire.hex',
                      sik_dir / 'legacy_wire.hex', copy_dir / 'result.json')}
        protocol_env = dict(os.environ, SIK_WIRE_FIXTURE=str(sik_dir / 'sik_wire.hex'))
        run('sik_protocol', py + ['-m', 'unittest', 'discover', '-s', ROOT / 'tests', '-p', 'test_protocol.py'], env=protocol_env)
        run('bench_evaluator', py + ['-m', 'unittest', 'discover', '-s', ROOT / 'tests', '-p', 'test_analyze_bench.py'])
        receiver = run_dir / 'sik_receiver'
        run('prepare_isolated_receiver', py + [ROOT / 'tools/prepare_sik_receiver.py', '--output', receiver])
        run('legacy_receiver_regression', py + ['-m', 'unittest', 'test_system', 'test_mtf'], cwd=receiver)
        run('sram_fail_closed', py + ['-m', 'unittest', 'discover', '-s', ROOT / 'tests', '-p', 'test_install_sram.py'])
        run('tracking_identity', py + ['-m', 'unittest', 'discover', '-s', REPO / 'web/flight-console/local', '-p', 'test_attitude_tracking.py'])
        run('receiver_wrapper', py + ['-m', 'unittest', 'discover', '-s', REPO / 'web/flight-console/local', '-p', 'test_receiver_setpoints.py'])
        iv = args.iverilog or shutil.which('iverilog')
        if not iv:
            iv = Path.home() / 'Desktop/apple/.tools/iverilog/app/bin/iverilog.exe'
        temp = run_dir / 'tmp'
        temp.mkdir()
        env = dict(os.environ, **{key: str(temp) for key in ('TMP', 'TEMP', 'TMPDIR')})
        # Derived PNR projects intentionally contain only the bound synthesized
        # netlist. Elaborate the separately audited logical RTL, not that project.
        logical = ROOT / 'source'
        files = [logical / f.attrib['path'] for f in ET.parse(logical / 'acg720_ano_port.gprj').findall('.//File')
                 if f.attrib.get('enable') == '1' and f.attrib.get('type') == 'file.verilog']
        if not files or any(not f.is_file() or not f.resolve().is_relative_to(logical.resolve()) for f in files):
            raise ValueError('Logical RTL project is empty or references an invalid source')
        run('whole_top_elaboration', [iv, '-g2012', '-Wall', '-I', logical, '-s', 'acg720_ano_port',
                                     '-o', run_dir / 'top.vvp', *files], env=env)
        # unittest silently succeeds with zero tests: require named executable suites.
        for name in ('test_passivity.py', 'test_build_audit.py', 'test_policy_receipt.py',
                     'test_protocol.py', 'test_analyze_bench.py', 'test_install_sram.py'):
            if not (ROOT / 'tests' / name).is_file():
                raise ValueError('Required suite missing: ' + name)
        require_unchanged_inputs(initial_inputs)
        receipt['verification_inputs_unchanged'] = True
        receipt['passed'] = True
    finally:
        write_json(receipt_path, receipt)
    acceptance = dict(schema='b0b2.offline-acceptance.v1', passed=True, build_id=0xB0B2,
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
