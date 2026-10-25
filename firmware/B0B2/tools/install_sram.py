"""Verify B0B2 offline; optionally install SRAM after current human bench confirmation.

No hardware is accessed unless BOTH --program and --bench-confirmed are supplied.
The confirmation flag is an operator assertion, not evidence that this script
verified props removal. Obtain current human authorization outside this script.
Only programmer operations 0 (identity) and 2 (SRAM) are implemented.
Separate --scan-cables F enumeration binds the unique serial6 download cable's
fresh positive location, rechecked before writing. No JTAG --scan is used.

offline_acceptance.json schema b0b2.offline-acceptance.v1 binds result_sha256,
inputs_sha256, bitstream_sha256 and test_receipt:{path,sha256}. It must have
passed:true and build_id:45234. The bound b0b2.tests.v1 receipt must have
passed:true and complete current source/verification-script hash maps.
The test run must prove unchanged verification inputs and bind exactly its
four fresh run-relative SiK diagnostic/copy-contract artifacts by SHA256.
Success after SRAM additionally requires fresh stopped B0B2 telemetry.
"""
from pathlib import Path
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import math
import re
import subprocess
import sys
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
TOP = 'acg720_ano_port'
BUILD_ID = 0xb0b2
DEVICE_ID = 0x0001481b
PROGRAMMER = Path('C:/Gowin/Gowin_V1.9.12.04_x64/Programmer/bin/programmer_cli.exe')
API = 'http://127.0.0.1:8765/api/state'


def require(ok, reason):
    if not ok:
        raise ValueError(reason)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_json(path):
    value = json.loads(Path(path).read_text(encoding='utf-8-sig'))
    require(isinstance(value, dict), f'Expected JSON object: {path}')
    return value


def child(root, relative):
    require(isinstance(relative, str) and relative and not Path(relative).is_absolute(), 'Expected relative artifact path')
    path = (root / relative).resolve()
    require(path.is_relative_to(root.resolve()) and path != root.resolve(), 'Artifact path escapes its directory')
    require(path.is_file(), 'Missing artifact: ' + relative)
    return path


def tcl_commands(path):
    lines = [s.strip() for s in path.read_text().splitlines() if s.strip() and not s.lstrip().startswith('#')]
    for line in lines:
        if line.startswith('set_option '):
            require(re.fullmatch(r'set_option\s+-[A-Za-z0-9_]+\s+[A-Za-z0-9_.-]+', line), 'Unexpected Tcl option syntax')
    return [line for line in lines if not line.startswith('set_option ')]


def audit_current_source(fixture, manifest):
    """Use the hash-bound current builder's single full/derived source audit.

    This import executes definitions only. The builder's main/process entry
    point is never called, and no derived CST/Tcl exception is implemented here.
    """
    spec = importlib.util.spec_from_file_location('b0b2_installer_source_audit', ROOT / 'tools/build.py')
    require(spec is not None and spec.loader is not None, 'Cannot load shared source auditor')
    auditor = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(auditor)
    return auditor.verify_current_source(fixture, manifest)


def verify(build):
    """Read files only. Rehash all bound inputs/outputs and the current source."""
    build = Path(build).resolve()
    require(build.is_dir(), 'Build directory does not exist')
    inputs = read_json(build / 'inputs.json')
    require(inputs.get('build_mode') != 'synthesis-only',
            'Synthesis-only build has no physical acceptance and cannot be installed')
    result = read_json(build / 'result.json')
    acceptance = read_json(build / 'offline_acceptance.json')
    require(result.get('passed') is True, 'Build result did not pass')
    require(all(result.get(k) is True for k in ('routing_passed', 'timing_passed', 'identity_passed', 'pin_contract_passed')),
            'Build routing/timing/identity/pin checks did not all pass')
    require(type(result.get('vendor_returncode')) is int and result['vendor_returncode'] == 0
            and result.get('errors') == [], 'Build result contains vendor errors or invalid exit code')
    unrouted = result.get('unrouted_nets')
    if unrouted is None:
        minima = result.get('worst_reported_slack_ns') or {}
        kinds = ('setup', 'hold', 'recovery', 'removal', 'minimum_pulse_width')
        require(result.get('actual_input_paths_passed') is True and result.get('report_clock_contract_passed') is True
                and result.get('timing_exceptions_added') is False
                and isinstance(result.get('routing_status_proof'), str) and result['routing_status_proof'].strip()
                and all(type(minima.get(k)) in (int, float) and math.isfinite(minima[k]) and minima[k] >= 0 for k in kinds),
                'Missing explicit zero-unrouted count requires complete routing/clock/input/STA proof')
    else:
        require(type(unrouted) is int and unrouted == 0, 'Build has explicit nonzero unrouted nets')
    inputs_hash = sha(build / 'inputs.json')
    result_hash = sha(build / 'result.json')
    require(result.get('inputs_sha256') == inputs_hash, 'inputs.json hash changed')
    source = (ROOT / 'source').resolve()
    require(Path(inputs.get('source_root', '')).resolve() == source, 'Build came from a different source root')
    require(inputs.get('runner_sha256') == sha(build / 'build_runner.py'), 'Archived executing build runner changed')
    require(result.get('audit_runner_sha256') == sha(ROOT / 'tools/build.py'), 'Current build auditor differs from audited result')
    require((inputs.get('options') or {}).get('user_code') == '0000B0B2', 'Build UserCode option is not B0B2')
    fixture = build / 'fixture'
    hashes = inputs.get('source_sha256')
    require(isinstance(hashes, dict) and hashes, 'Missing input source hashes')
    current = {p.relative_to(source).as_posix(): p for p in source.rglob('*') if p.is_file()}
    require(set(hashes) == set(current), 'Current source file set differs from built inputs')
    derived = inputs.get('derived_netlist') is not None
    for name, digest in hashes.items():
        saved = child(fixture, name)
        require(sha(saved) == digest, 'Fixture input changed: ' + name)
        require(current[name].resolve().is_relative_to(source), 'Current source symlink escapes source root')
        if derived:
            # The shared auditor below verifies every logical/physical mapping
            # and the complete donor/proof chain. Never infer exceptions here.
            continue
        if name == 'build.tcl':
            require(tcl_commands(saved) == tcl_commands(current[name]), 'Build Tcl changed beyond build options')
        else:
            require(sha(current[name]) == digest, 'Latest source differs from fixture: ' + name)
    audit_current_source(fixture, inputs)
    logical_hashes = inputs.get('logical_source_sha256') if derived else hashes
    if derived:
        require(result.get('observer_global_contract_passed') is True,
                'Derived physical report did not verify the observer global assignment')
        require(result.get('pnr_only_synthesis_absent') is True,
                'Derived physical report did not exclude automatic synthesis')
    outputs = result.get('outputs_sha256')
    require(isinstance(outputs, dict) and outputs, 'Missing output hashes')
    pnr = fixture / 'impl/pnr'
    actual_outputs = {p.relative_to(build).as_posix() for p in pnr.glob('*') if p.is_file()}
    require(set(outputs) == actual_outputs, 'Build output file set changed')
    for name, digest in outputs.items():
        require(sha(child(build, name)) == digest, 'Build output changed: ' + name)
    image = child(build, f'fixture/impl/pnr/{TOP}.fs')
    image_hash = sha(image)
    bitstream = result.get('bitstream') or {}
    require(Path(bitstream.get('path', '')).resolve() == image, 'Unexpected bitstream path')
    require(bitstream.get('sha256') == image_hash, 'Bitstream hash changed')
    header = '\n'.join(image.read_text(errors='replace').splitlines()[:15])
    require(re.search(r'UserCode:\s*0x0000b0b2\b', header, re.I), 'Bitstream UserCode is not B0B2')
    require(acceptance.get('schema') == 'b0b2.offline-acceptance.v1' and acceptance.get('passed') is True
            and acceptance.get('build_id') == BUILD_ID, 'Offline acceptance did not pass for B0B2')
    require(acceptance.get('result_sha256') == result_hash and acceptance.get('inputs_sha256') == inputs_hash
            and acceptance.get('bitstream_sha256') == image_hash, 'Offline acceptance is not bound to this build')
    tests = acceptance.get('test_receipt') or {}
    test_path = child(build, tests.get('path'))
    require(tests.get('sha256') == sha(test_path), 'Test receipt hash changed')
    test_receipt = read_json(test_path)
    require(test_receipt.get('passed') is True, 'Bound test receipt did not pass')
    require(test_receipt.get('schema') == 'b0b2.tests.v1', 'Bound test receipt schema is not b0b2.tests.v1')
    require(test_receipt.get('verification_inputs_unchanged') is True,
            'Verification inputs were not proven unchanged across the test run')
    prefix = 'tests_receipt_'
    require(test_path.parent == build and test_path.suffix == '.json' and test_path.stem.startswith(prefix),
            'Test receipt must be a current build-root tests_receipt_<run>.json')
    run_name = test_path.stem.removeprefix(prefix)
    require(re.fullmatch(r'[A-Za-z0-9_-]+', run_name) is not None,
            'Test receipt run name is empty or invalid')
    artifact_names = {run_name + '/' + name for name in (
        'sik_diagnostic/result.json', 'sik_diagnostic/sik_wire.hex',
        'sik_diagnostic/legacy_wire.hex', 'sik_copy_contract/result.json')}
    artifacts = test_receipt.get('subtest_artifacts_sha256')
    require(isinstance(artifacts, dict) and set(artifacts) == artifact_names,
            'Subtest artifact hash map must contain exactly the four current-run artifacts')
    for name, digest in artifacts.items():
        require(sha(child(build, name)) == digest, 'Subtest artifact changed: ' + name)
    scripts = test_receipt.get('verification_scripts_sha256')
    current_scripts = {p.relative_to(ROOT).as_posix(): p
                       for directory in ('tests', 'ground', 'tools')
                       for p in (ROOT / directory).rglob('*')
                       if p.is_file() and p.suffix in ('.py', '.v', '.hex')}
    require(isinstance(scripts, dict) and scripts and set(scripts) == set(current_scripts),
            'Verification script hash map is missing, empty or incomplete')
    for name, digest in scripts.items():
        require(sha(child(ROOT, name)) == digest, 'Verification script changed since tests: ' + name)
    tested_sources = test_receipt.get('source_sha256')
    require(isinstance(tested_sources, dict) and tested_sources and set(tested_sources) == set(hashes),
            'Tested source hash map is missing, empty or differs from build')
    for name, digest in tested_sources.items():
        require(sha(current[name]) == digest and (name == 'build.tcl' or digest == logical_hashes[name]),
                'Tested source differs from fixture/current source: ' + name)
    return dict(passed=True, build=str(build), image=str(image), image_sha256=image_hash,
                result_sha256=result_hash, inputs_sha256=inputs_hash,
                acceptance_sha256=sha(build / 'offline_acceptance.json'), test_receipt_sha256=sha(test_path),
                verification_inputs_unchanged=True, subtest_artifacts_sha256=dict(artifacts),
                hardware_accessed=False, flash_written=False)


def state(timeout=4):
    with urllib.request.urlopen(API, timeout=timeout) as response:
        return json.load(response)


def stopped(snapshot, expected_build=None):
    require(isinstance(snapshot, dict), 'Invalid telemetry response')
    data = snapshot.get('data') or {}
    build_id = (snapshot.get('flight_info') or {}).get('build_id')
    require(snapshot.get('fresh') is True and snapshot.get('flight_info_fresh') is True and snapshot.get('status') == 'live',
            'Fresh live telemetry and build identity required')
    require(snapshot.get('serial_writes') is False, 'Receiver must be read-only')
    require(type(build_id) is int and build_id in (0xb0b0, 0xb0b1, BUILD_ID), 'Expected current B0B0 or B0B2')
    if expected_build is not None:
        require(build_id == expected_build, 'Telemetry build changed before SRAM write')
    require(data.get('armed') is False and data.get('controller_enabled') is False and
            data.get('physical_output_active') is False, 'Aircraft must be unarmed, disabled and physically inactive')
    require(data.get('pwm_us') == [1000] * 4 and data.get('command_us') == [1000] * 4,
            'Reported PWM and commands must all be 1000 us')
    require(data.get('rc_valid') is True, 'Valid live RC required')
    rc = data.get('rc_us') or []
    require(isinstance(rc, list) and len(rc) >= 7 and all(type(rc[i]) is int and 800 <= rc[i] <= 1100 for i in (2, 4, 6)),
            'CH3, CH5 and CH7 must all be low')
    return build_id


class UnsafePostLoad(ValueError):
    """A fresh new-image report contains explicit activity; never retry it."""


def wait_stopped_after_load(folder, report, timeout=30.0, interval=0.25):
    """Read-only, bounded boot wait. Preserve the last response and each reason.

    Missing/stale identity or incomplete startup data may recover within the
    deadline. Explicit activity in fresh B0B2 telemetry fails immediately.
    No control command, programmer operation or recovery action occurs here.
    """
    start = time.monotonic()
    deadline = start + timeout
    progress = dict(passed=False, timeout_seconds=timeout, attempts=[], elapsed_seconds=0.0)
    report['post_load_telemetry'] = progress
    last_reason = 'No post-load telemetry response'
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            progress.update(elapsed_seconds=time.monotonic() - start, last_error=last_reason)
            raise ValueError('Timed out waiting for fresh stopped B0B2 telemetry: ' + last_reason)
        try:
            snapshot = state(timeout=min(4.0, remaining))
        except (OSError, ValueError) as exc:
            last_reason = f'{type(exc).__name__}: {exc}'
            progress['attempts'].append(dict(elapsed_seconds=time.monotonic() - start, error=last_reason))
        else:
            (folder / 'telemetry_after.json').write_text(json.dumps(snapshot, indent=2), encoding='utf8')
            info = snapshot.get('flight_info') if isinstance(snapshot, dict) else None
            build_id = info.get('build_id') if isinstance(info, dict) else None
            data = snapshot.get('data') if isinstance(snapshot, dict) else None
            entry = dict(elapsed_seconds=time.monotonic() - start, build_id=build_id,
                         fresh=snapshot.get('fresh') if isinstance(snapshot, dict) else None)
            progress['attempts'].append(entry)
            fresh_new = (isinstance(snapshot, dict) and snapshot.get('fresh') is True
                         and snapshot.get('flight_info_fresh') is True and snapshot.get('status') == 'live'
                         and type(build_id) is int and build_id == BUILD_ID)
            if fresh_new and isinstance(data, dict):
                active = any(data.get(k) is True for k in ('armed', 'controller_enabled', 'physical_output_active'))
                for field in ('pwm_us', 'command_us'):
                    widths = data.get(field)
                    if isinstance(widths, list):
                        active |= any(type(v) in (int, float) and math.isfinite(v) and v != 1000 for v in widths)
                if active:
                    last_reason = 'Fresh B0B2 telemetry reports armed/enabled/activity or non-1000 outputs'
                    entry['error'] = last_reason
                    progress.update(elapsed_seconds=time.monotonic() - start, last_error=last_reason, unsafe=True)
                    raise UnsafePostLoad(last_reason)
            try:
                stopped(snapshot, BUILD_ID)
            except (ValueError, AttributeError, TypeError) as exc:
                last_reason = f'{type(exc).__name__}: {exc}'
                entry['error'] = last_reason
            else:
                progress.update(passed=True, elapsed_seconds=time.monotonic() - start)
                return snapshot
        remaining = deadline - time.monotonic()
        if remaining > 0:
            time.sleep(min(interval, remaining))


def programmers():
    # Enumeration only, never serial.Serial/open. Imported only on --program.
    from serial.tools import list_ports
    return [dict(vid=p.vid, pid=p.pid, serial=p.serial_number, device=p.device) for p in list_ports.comports()]


def known_programmer(inventory):
    candidates = [p for p in inventory if (p.get('vid'), p.get('pid')) == (0x403, 0x6014)]
    require(len(candidates) == 1 and candidates[0].get('serial') == '6', 'Known programmer missing or ambiguous')
    return dict(candidates[0])


def parse_cables(output):
    """Parse only the vendor cable inventory, never a JTAG device scan."""
    rows = [line.strip() for line in output.splitlines() if 'Gowin USB Cable' in line]
    require(len(rows) == 1, 'Missing or ambiguous Gowin USB cable inventory')
    row = re.fullmatch(r'Cable found:\s+Gowin USB Cable\(FT2CH\)/(\d+)/(\d+)/null\s+\(USB location:(\d+)\)', rows[0])
    require(row is not None, 'Unexpected Gowin USB cable inventory format')
    index, path_location, usb_location = map(int, row.groups())
    require(index == 1 and path_location == usb_location and usb_location > 0,
            'Gowin USB cable must be index 1 with consistent positive location')
    return dict(name='Gowin USB Cable(FT2CH)', index=index, location=usb_location)


def scan_cables(log_path):
    # Fixed vendor download-cable enumeration. In particular, do not use --scan
    # (which scans JTAG devices) or introduce any programmer --run operation.
    args = [str(PROGRAMMER), '--scan-cables', 'F']
    try:
        ran = subprocess.run(args, capture_output=True, text=True, errors='replace', timeout=120,
                             creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    except subprocess.TimeoutExpired as exc:
        def as_text(value):
            return value.decode(errors='replace') if isinstance(value, bytes) else value or ''
        Path(log_path).write_text(as_text(exc.stdout) + as_text(exc.stderr) + '\nTIMEOUT\n', encoding='utf8')
        raise
    output = ran.stdout + ran.stderr
    Path(log_path).write_text(output, encoding='utf8')
    require(type(ran.returncode) is int and ran.returncode == 0, 'Cable enumeration failed; see ' + str(log_path))
    return parse_cables(output)


def identity(output):
    ids = re.findall(r'^\s*ID Code is:\s*(0x[0-9a-f]{8})\b', output, re.I | re.M)
    codes = re.findall(r'^\s*User Code is:\s*(0x[0-9a-f]{8})\b', output, re.I | re.M)
    require(len(ids) == 1 and len(codes) == 1, 'Missing or ambiguous programmer identity')
    return int(ids[0], 16), int(codes[0], 16)


def command(operation, log_path, image=None, image_sha256=None, *, location=None):
    require(type(operation) is int and operation in (0, 2), 'Only identity (0) and SRAM (2) operations are allowed')
    require(type(location) is int and location > 0, 'Fresh positive cable location is required')
    args = [str(PROGRAMMER), '--device', 'GW5AT-60B', '--cable-index', '1',
            '--location', str(location), '--run', str(operation)]
    if operation == 2:
        require(image is not None and sha(image) == image_sha256, 'Bitstream changed immediately before SRAM write')
        args += ['--fsFile', str(image)]
    try:
        ran = subprocess.run(args, capture_output=True, text=True, errors='replace', timeout=120,
                             creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    except subprocess.TimeoutExpired as exc:
        def as_text(value):
            return value.decode(errors='replace') if isinstance(value, bytes) else value or ''
        Path(log_path).write_text(as_text(exc.stdout) + as_text(exc.stderr) + '\nTIMEOUT\n', encoding='utf8')
        raise
    output = ran.stdout + ran.stderr
    Path(log_path).write_text(output, encoding='utf8')
    require(type(ran.returncode) is int and ran.returncode == 0 and 'Finished.' in output, 'Programmer failed; see ' + str(log_path))
    return output


def install(build, program=False, bench_confirmed=False):
    if not program:
        return verify(build)
    build = Path(build).resolve()
    require(build.is_dir(), 'Build directory does not exist')
    folder = build / datetime.now(timezone.utc).strftime('hardware_%Y%m%dT%H%M%S_%fZ')
    folder.mkdir(exist_ok=False)
    report = dict(installed=False, hardware_accessed=False, sram_write_attempted=False, sram_written=False,
                  flash_written=False, bench_only=True, flight_ready=False, operations=[], scans=[], folder=str(folder),
                  operator_confirmation_flag=bool(bench_confirmed),
                  confirmation_scope='Operator asserts current human-confirmed props-off and stable bench; flag alone is not independent verification.')
    try:
        require(bench_confirmed is True, 'Current human props-off and stable-bench confirmation required before --bench-confirmed')
        verified = verify(build)
        report['verification'] = verified
        report['hardware_accessed'] = True
        inventory = programmers()
        report['programmers'] = inventory
        selected_programmer = known_programmer(inventory)
        report['programmer_selection'] = selected_programmer
        scan = dict(phase='initial', log='cables_before.txt')
        report['scans'].append(scan)
        cable = scan_cables(folder / scan['log'])
        scan['selection'] = cable
        report['cable_selection'] = cable
        before = state()
        old_build = stopped(before)
        (folder / 'telemetry_before.json').write_text(json.dumps(before, indent=2), encoding='utf8')
        report['operations'].append(0)
        old = identity(command(0, folder / 'identity_before.txt', location=cable['location']))
        require(old == (DEVICE_ID, old_build), 'Pre-write hardware identity does not match device/telemetry')
        require(verify(build) == verified, 'Build or acceptance changed before SRAM write')
        inventory_latest = programmers()
        report['programmers_prewrite'] = inventory_latest
        require(known_programmer(inventory_latest) == selected_programmer, 'Programmer inventory changed before SRAM write')
        scan = dict(phase='prewrite', log='cables_prewrite.txt')
        report['scans'].append(scan)
        cable_latest = scan_cables(folder / scan['log'])
        scan['selection'] = cable_latest
        require(cable_latest == cable, 'Vendor cable selection changed before SRAM write')
        latest = state()
        stopped(latest, old_build)
        (folder / 'telemetry_prewrite.json').write_text(json.dumps(latest, indent=2), encoding='utf8')
        report['sram_write_attempted'] = True
        report['operations'].append(2)
        command(2, folder / 'program_sram.txt', Path(verified['image']), verified['image_sha256'], location=cable['location'])
        report['sram_written'] = True
        report['operations'].append(0)
        after = identity(command(0, folder / 'identity_after.txt', location=cable['location']))
        require(after == (DEVICE_ID, BUILD_ID), 'Post-write hardware identity is not B0B2 on the same target device')
        report['after_identity'] = dict(device_id=after[0], usercode=after[1])
        wait_stopped_after_load(folder, report)
        require(verify(build) == verified, 'Build or acceptance changed during SRAM write')
        report['installed'] = True
        return report
    except Exception as exc:
        report['error'] = f'{type(exc).__name__}: {exc}'
        raise
    finally:
        report['utc'] = datetime.now(timezone.utc).isoformat()
        report['installer_sha256'] = sha(Path(__file__))
        (folder / 'report.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf8')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build', required=True, type=Path)
    parser.add_argument('--program', action='store_true', help='Explicitly enable identity/SRAM programmer operations')
    parser.add_argument('--bench-confirmed', action='store_true', help='Assert current human-confirmed props-off, stable bench setup')
    args = parser.parse_args(argv)
    try:
        report = install(args.build, args.program, args.bench_confirmed)
    except Exception as exc:
        print(json.dumps(dict(passed=False, error=f'{type(exc).__name__}: {exc}')), file=sys.stderr)
        return 2
    print(json.dumps(report, indent=2))
    return 0


if __name__ == '__main__':
    sys.exit(main())
