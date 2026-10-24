"""Verify the frozen B0AF release, optionally install to SRAM for props-off acceptance.

Only programmer operations 0 (identity) and 2 (SRAM) are implemented.
No Flash write, motor command, serial write, or receiver process change.
"""
import argparse
import datetime as dt
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys
import time
import urllib.request
from serial.tools import list_ports

BASE = Path(__file__).resolve().parent
RELEASE = BASE
FIXTURE = RELEASE / 'fixture'
IMAGE = FIXTURE / 'impl/pnr/acg720_ano_port.fs'
IMAGE_SHA = '28284ebb9369d9b4123a4220537002a87e0c15593ec604b4728dc546ee9f393c'
CLI = 'C:/Gowin/Gowin_V1.9.12.04_x64/Programmer/bin/programmer_cli.exe'
URL = 'http://127.0.0.1:8767/api/state'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def verify():
    require(not (BASE / 'HARDWARE_REJECTED.json').exists(),
            'B0AF failed hardware acceptance: implicit-net synthesis fault. Do not program; use a separately verified replacement.')
    release = read(RELEASE / 'offline_release.json')
    qualification = read(RELEASE / 'qualification.json')
    manifest = read(FIXTURE / 'build_manifest.json')
    require(release['offline_verified'] and qualification['offline_tests_passed'], 'Offline qualification missing')
    for key, path in [('qualification_sha256', RELEASE / 'qualification.json'),
                      ('build_manifest_sha256', FIXTURE / 'build_manifest.json'),
                      ('verifier_sha256', FIXTURE / 'build_project.py'),
                      ('source_contract_sha256', RELEASE / 'source_contract.json'),
                      ('operator_notes_sha256', RELEASE / 'OPERATOR_NOTES.txt')]:
        require(sha(path) == release[key], 'Release binding changed: ' + key)
    require(manifest['verified'] and manifest['sources_sha256'] == qualification['sources_sha256'], 'Source binding mismatch')
    require(sha(IMAGE) == IMAGE_SHA == release['bitstream']['sha256'], 'Image changed')
    for name, digest in qualification['evidence_sha256'].items():
        require(sha(RELEASE / name) == digest, 'Proof changed: ' + name)
    spec = importlib.util.spec_from_file_location('b0af_builder', FIXTURE / 'build_project.py')
    builder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(builder)
    builder.static_contract()
    actual = builder.verify(qualification['sources_sha256'])
    for key in ['bitstream', 'artifact_sha256', 'fmax_mhz', 'io_count', 'unrouted_nets', 'slack', 'pins']:
        require(actual[key] == manifest[key], 'Verified build differs: ' + key)
    return sha(RELEASE / 'offline_release.json')


def state():
    with urllib.request.urlopen(URL, timeout=4) as response:
        return json.load(response)


def stopped(snapshot, build):
    data = snapshot.get('data') or {}
    require(snapshot.get('status') == 'live' and snapshot.get('fresh') and snapshot.get('flight_info_fresh'), 'Fresh telemetry required')
    require(snapshot.get('receiver_profile') == 'mtf01p.b0af_height_loss.v6' and snapshot.get('serial_writes') is False, 'Wrong receiver')
    require((snapshot.get('flight_info') or {}).get('build_id') == build, 'Unexpected live build')
    require(data.get('armed') is False and data.get('controller_enabled') is False and
            data.get('physical_output_active') is False and data.get('pwm_us') == [1000] * 4 and
            data.get('command_us') == [1000] * 4, 'Disarmed reported 1000 us outputs required')
    channels = data.get('rc_us') or []
    require(len(channels) >= 7 and 800 <= channels[2] <= 1100 and
            channels[4] < 1800 and channels[6] < 1800, 'Low throttle/SWA/SWC required')


def programmer(operation, location, destination):
    require(operation in (0, 2), 'Only identity/SRAM permitted')
    args = [CLI, '--device', 'GW5AT-60B', '--cable-index', '1', '--location', str(location), '--run', str(operation)]
    if operation == 2:
        require(sha(IMAGE) == IMAGE_SHA, 'Image changed before installation')
        args += ['--fsFile', str(IMAGE)]
    result = subprocess.run(args, capture_output=True, text=True, errors='replace', timeout=120,
                            creationflags=subprocess.CREATE_NO_WINDOW)
    output = result.stdout + result.stderr
    destination.write_text(output, encoding='utf-8')
    require(result.returncode == 0 and 'Finished.' in output and not re.search(r'\bError:', output), 'Programmer failed: ' + str(destination))
    return output


def summary(snapshot):
    data = snapshot.get('data') or {}
    return dict(fresh=snapshot.get('fresh'), flight_info=snapshot.get('flight_info'),
                receiver=snapshot.get('receiver_profile'), armed=data.get('armed'),
                calibrated=data.get('calibrated'), attitude_valid=data.get('attitude_valid'),
                pwm_us=data.get('pwm_us'), command_us=data.get('command_us'),
                mtf_fresh=snapshot.get('mtf_fresh'), navigation_fresh=snapshot.get('navigation_fresh'),
                navigation=snapshot.get('navigation'), mtf_sensor=snapshot.get('mtf_sensor'),
                session_id=(snapshot.get('recording') or {}).get('session_id'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sram', action='store_true')
    parser.add_argument('--bench-confirmed', action='store_true')
    parser.add_argument('--location', type=int)
    args = parser.parse_args()
    selection_sha = verify()
    if not args.sram:
        print(json.dumps(dict(verified=True, image_sha256=IMAGE_SHA, hardware_accessed=False)))
        return
    require(args.bench_confirmed and args.location is not None, 'Current props-off/RC-off confirmation and enumerated location required')
    require(len([port for port in list_ports.comports() if (port.vid, port.pid, port.serial_number) == (0x403, 0x6014, '5')]) == 1,
            'Known programmer missing or ambiguous')
    stopped(state(), 0xB0AE)
    folder = BASE / 'hardware' / dt.datetime.now(dt.timezone.utc).strftime('sram_%Y%m%dT%H%M%S_%fZ')
    folder.mkdir(parents=True, exist_ok=False)
    record = dict(installed=False, sram_write_attempted=False, sram_written=False, flash_written=False,
                  flight_ready=False, image_sha256=IMAGE_SHA, selection_sha256=selection_sha,
                  human_confirmation='2026-10-23: all props removed, transmitter off, both FPGA USB connected; frame kept still.',
                  before=summary(state()), location=args.location)
    try:
        identity = programmer(0, args.location, folder / 'identity_before.txt')
        require('0x0001481B' in identity and re.search(r'0x0000B0AE\b', identity, re.I), 'Unexpected JTAG identity')
        require(verify() == selection_sha, 'Selection changed before installation')
        stopped(state(), 0xB0AE)
        record['sram_write_attempted'] = True
        programmer(2, args.location, folder / 'program_sram.txt')
        record['sram_written'] = True
        identity = programmer(0, args.location, folder / 'identity_after.txt')
        require('0x0001481B' in identity and re.search(r'0x0000B0AF\b', identity, re.I), 'SRAM identity mismatch')
        record['installed'] = True
        started = time.monotonic()
        observations = []
        with (folder / 'stopped_observations.jsonl').open('w', encoding='utf-8') as stream:
            while time.monotonic() - started < 20:
                snapshot = state()
                observation = dict(elapsed_s=time.monotonic() - started, state=summary(snapshot))
                stream.write(json.dumps(observation) + '\n')
                stream.flush()
                observations.append(observation)
                if snapshot.get('fresh') and (snapshot.get('flight_info') or {}).get('build_id') == 0xB0AF:
                    stopped(snapshot, 0xB0AF)
                time.sleep(0.25)
        late = [item for item in observations if item['elapsed_s'] >= 10]
        require(len(late) >= 20, 'Insufficient startup observations')
        require(all(item['state']['fresh'] and item['state']['flight_info']['build_id'] == 0xB0AF and
                    item['state']['calibrated'] and item['state']['attitude_valid'] and
                    item['state']['mtf_fresh'] and item['state']['navigation_fresh'] for item in late),
                'Startup telemetry/calibration not consistently valid')
        record.update(stopped_startup_passed=True, post_startup_samples=len(late), after=summary(state()))
    finally:
        record.update(utc=dt.datetime.now(dt.timezone.utc).isoformat(), folder=str(folder), installer_sha256=sha(Path(__file__)))
        (folder / 'report.json').write_text(json.dumps(record, indent=2), encoding='utf-8')
    print(json.dumps(dict(installed=record['installed'], stopped_startup_passed=record.get('stopped_startup_passed', False),
                         flash_written=False, flight_ready=False, evidence=str(folder)), indent=2))


if __name__ == '__main__':
    main()
