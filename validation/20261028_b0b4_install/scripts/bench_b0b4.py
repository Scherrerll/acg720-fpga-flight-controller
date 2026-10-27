"""Fixed B0B4 bench installation. Default is offline; this script never opens serial.

Only the running ground/B0B4 owner at localhost:8765 may query parameters.
Current implementation provides preflight and SRAM, with no automatic recovery.
Flash and physical cold-boot qualification are separate, not inferred from SRAM.
"""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import hashlib
import importlib.util
import json
import re
import subprocess
import sys
import time
import urllib.request

REPO = Path(__file__).resolve().parents[3]
IMAGE = REPO / 'firmware/B0B4/release/acg720_ano_port.fs'
MANIFEST = REPO / 'firmware/B0B4/release_manifest.json'
HELPER = REPO / 'firmware/B0B2/tools/install_sram.py'
CLI = Path('C:/Gowin/Gowin_V1.9.12.04_x64/Programmer/bin/programmer_cli.exe')
PREVIOUS = REPO / 'firmware/B0B3/release/B0B3_selected_P3R0.fs'
IMAGE_SHA = '199bc466f8a8fe18e891600d18161babcea9c2495eee8d307dac62ac8646c610'
MANIFEST_SHA = 'c8e03412ff44cbe929f5d8ce6fed6eb3c61078a2028df466a340a61894893a2d'
HELPER_SHA = '6b872ec4ab8c0425f8d477d9e2ac63a21f01f8f0bfe69635cbf3420b796f49b1'
CLI_SHA = 'ca28fe178b04fd99780267787f61b0e0ec3729d579fe237ff454c1a0353e8ef6'
PREVIOUS_SHA = 'a5b893b25a5e510348c8a4ac75c914b8a14473bbfb054b4cc4040b86800f64dd'
ORIGIN = 'http://127.0.0.1:8765'
DEFAULT_OUT = REPO / 'out/b0b4_install_20261028'


def require(ok, reason):
    if not ok:
        raise ValueError(reason)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def utc():
    return datetime.now(timezone.utc).isoformat()


def save(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def offline():
    for path, digest in ((IMAGE, IMAGE_SHA), (MANIFEST, MANIFEST_SHA),
                         (HELPER, HELPER_SHA), (CLI, CLI_SHA), (PREVIOUS, PREVIOUS_SHA)):
        require(sha(path) == digest, 'Pinned file changed: ' + str(path))
    manifest = json.loads(MANIFEST.read_text(encoding='utf-8'))
    entries = {item['path']: item['sha256'] for item in manifest['files']}
    verifier = REPO / 'firmware/B0B4/verify_release.py'
    require(entries.get(IMAGE.relative_to(REPO).as_posix()) == IMAGE_SHA, 'Manifest does not bind image')
    require(entries.get(verifier.relative_to(REPO).as_posix()) == sha(verifier), 'Verifier not manifest-bound')
    with IMAGE.open('rb') as stream:
        require(re.search(rb'UserCode:\s*0x0000b0b4\b', stream.read(4096), re.I), 'Image UserCode is not B0B4')
    return dict(passed=True, image_sha256=IMAGE_SHA, manifest_sha256=MANIFEST_SHA,
                helper_sha256=HELPER_SHA, cli_sha256=CLI_SHA, previous_readonly_sha256=PREVIOUS_SHA,
                hardware_accessed=False, scope='Pinned inputs only; full verifier runs in an explicit live stage.')


class UnsafeActivity(RuntimeError):
    pass


def no_activity(value):
    if value.get('connected') is True and value.get('fresh') is True:
        data = value.get('data') or {}
        active = any(data.get(k) is True for k in ('armed', 'controller_enabled', 'command_fresh', 'physical_output_active'))
        active |= any(type(v) in (int, float) and v != 1000
                      for k in ('pwm_us', 'command_us') for v in (data.get(k) or []))
        if active:
            raise UnsafeActivity('Fresh telemetry reports activity; no further automatic hardware operation')


def stopped(value):
    require(isinstance(value, dict), 'Invalid telemetry object')
    no_activity(value)
    require(value.get('connected') is True and value.get('fresh') is True and
            value.get('flight_info_fresh') is True and value.get('status') == 'live', 'Fresh live telemetry required')
    require(value.get('port') == 'COM17' and value.get('ui_version') == 'flight-console.20261026.b0b4.xy-pi.v1',
            'Require existing B0B4 ground owner on COM17')
    source = value.get('source') or {}
    require(source.get('port') == 'COM17' and source.get('source') == 'SiK' and source.get('baud') == 115200,
            'Unexpected ground connection')
    data = value.get('data') or {}; info = value.get('flight_info') or {}
    # A580/A585 deliberately retain the compatible B0B2 label. JTAG/A591 prove B4 separately.
    require(info.get('build_id') == 0xB0B2 and info.get('taking_off') is False, 'Legacy telemetry identity/takeoff mismatch')
    require(type(value.get('sequence')) is int and info.get('sequence') == value['sequence'], 'Same-group telemetry required')
    require(all(data.get(k) is False for k in ('armed', 'controller_enabled', 'command_fresh', 'physical_output_active')),
            'All stopped booleans must be false')
    require(data.get('pwm_us') == [1000] * 4 and data.get('command_us') == [1000] * 4, 'All PWM/commands must equal 1000')
    rc = data.get('rc_us')
    require(data.get('rc_valid') is True and isinstance(rc, list) and len(rc) == 8 and all(type(v) is int for v in rc),
            'Complete live RC required')
    require(all(800 <= rc[k] <= 1100 for k in (2, 4, 6)) and all(1450 <= rc[k] <= 1550 for k in (0, 1, 3)),
            'CH3/5/7 low and sticks centered required')
    return value


def http(path, body=None, token=None):
    require(path in ('/api/state', '/api/xy-pi/status', '/api/xy-pi/session', '/api/xy-pi/query'), 'HTTP route outside query-only whitelist')
    require((body is not None) == (path == '/api/xy-pi/query'), 'Only parameter GET query may POST')
    headers = {}
    if body is not None:
        require(isinstance(token, str) and token and token.isascii(), 'Missing in-memory session token')
        headers = {'Origin': ORIGIN, 'X-XY-PI-Token': token, 'Content-Type': 'application/json'}
    request = urllib.request.Request(ORIGIN + path, data=None if body is None else json.dumps(body).encode(), headers=headers)
    # No request/response containing the session token is printed or persisted.
    with urllib.request.urlopen(request, timeout=4) as response:
        return json.load(response)


class Session:
    def __init__(self, stage, folder):
        require(stage in ('preflight', 'sram'), 'Stage not implemented')
        self.stage = stage; self.folder = Path(folder); self.hw = None; self.cable = None; self.inventory = None
        self.record = dict(schema='b0b4.bench-stage.v1', stage=stage, passed=False, started_utc=utc(),
                           script_sha256=sha(__file__), image_sha256=IMAGE_SHA, manifest_sha256=MANIFEST_SHA,
                           hardware_accessed=False, sram_write_attempted=False, sram_written=False,
                           flash_written=False, physical_cold_boot_verified=False, flight_ready=False,
                           automatic_recovery=False, operations=[], current_operator_bench_assertion=True)

    def persist(self):
        self.record['updated_utc'] = utc()
        save(self.folder / 'stage_report.json', self.record)

    def child(self, args, label, timeout=240):
        entry = dict(args=list(args), started_utc=utc(), normal_wait_return=False, actual_p_wait=None, timeout=False)
        save(self.folder / (label + '_process.json'), entry)
        start = time.monotonic()
        process = subprocess.Popen(args, cwd=REPO, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        entry['pid'] = process.pid
        save(self.folder / (label + '_process.json'), entry)
        try:
            stdout, stderr = process.communicate(timeout=timeout)
            entry.update(normal_wait_return=True, actual_p_wait=process.wait())
        except subprocess.TimeoutExpired:
            process.kill(); stdout, stderr = process.communicate(); entry.update(timeout=True, actual_p_wait=process.wait())
        (self.folder / (label + '_stdout.log')).write_bytes(stdout)
        (self.folder / (label + '_stderr.log')).write_bytes(stderr)
        entry.update(elapsed_s=round(time.monotonic() - start, 3), stdout_sha256=sha(self.folder / (label + '_stdout.log')),
                     stderr_sha256=sha(self.folder / (label + '_stderr.log')), finished_utc=utc())
        save(self.folder / (label + '_exit.json'), entry)
        require(entry['normal_wait_return'] is True and type(entry['actual_p_wait']) is int and entry['actual_p_wait'] == 0,
                'Child failed or timed out: ' + label)
        return (stdout + stderr).decode('utf-8', errors='replace')

    def guard(self):
        value = stopped(http('/api/state'))
        require(http('/api/xy-pi/status').get('busy') is False, 'Parameter transaction is busy')
        return value

    def bind(self, label):
        require(sha(CLI) == CLI_SHA and sha(HELPER) == HELPER_SHA, 'Programmer/helper changed')
        inventory = self.hw.known_programmer(self.hw.programmers())
        output = self.child([str(CLI), '--scan-cables', 'F'], label + '_cables', 120)
        cable = self.hw.parse_cables(output)
        if self.cable is not None:
            require(inventory == self.inventory and cable == self.cable, 'Programmer/cable selection changed')
        self.inventory = inventory; self.cable = cable
        self.record.update(programmer=inventory, cable=cable); self.persist()
        return cable['location']

    def operation(self, operation, label):
        require(type(operation) is int and operation in ((0, 2) if self.stage == 'sram' else (0,)), 'Operation outside stage whitelist')
        offline()
        location = self.bind(label)
        save(self.folder / (label + '_stopped.json'), self.guard())
        args = [str(CLI), '--device', 'GW5AT-60B', '--cable-index', '1', '--location', str(location), '--run', str(operation)]
        if operation == 2:
            require(sha(IMAGE) == IMAGE_SHA, 'Image changed at SRAM boundary')
            args += ['--fsFile', str(IMAGE)]
            self.record['sram_write_attempted'] = True
        self.record['operations'].append(dict(operation=operation, label=label, args=args)); self.persist()
        output = self.child(args, label)
        require('Finished.' in output and not re.search(r'\b(error|failed)\b', output, re.I), 'Programmer output failed: ' + label)
        if operation == 0:
            identity = self.hw.identity(output)
            require(identity[0] == 0x0001481B, 'Wrong device ID')
            return identity
        self.record['sram_written'] = True; self.persist()

    def health(self, label, loaded_at):
        deadline = time.monotonic() + 40; good = []; attempts = []
        try:
            while time.monotonic() < deadline:
                try:
                    value = self.guard(); data = value['data']; info = value['flight_info']; diagnostic = value.get('imu_diagnostic') or {}
                    require(all(data.get(k) is True for k in ('calibrated', 'attitude_valid', 'sensor_ok')), 'Waiting for IMU/attitude')
                    uptime = info.get('uptime_ms')
                    require(type(uptime) is int and 0 <= uptime <= (time.monotonic() - loaded_at) * 1000 + 5000, 'Waiting for new boot epoch')
                    require(value.get('imu_diagnostic_fresh') is True and diagnostic.get('build_id') == 0xB0B2 and
                            all(type(diagnostic.get(k)) is int for k in ('sequence', 'raw_count', 'accepted_count', 'pose_count')), 'Fresh IMU diagnostic required')
                    if good:
                        prior = good[-1]; old = prior['imu_diagnostic']
                        require(uptime >= prior['flight_info']['uptime_ms'], 'Uptime rolled back during health check')
                        require(all(diagnostic[k] > old[k] for k in ('raw_count', 'accepted_count', 'pose_count')), 'Waiting for new IMU counts')
                    good.append(value)
                    if len(good) >= 5:
                        require(good[-1]['flight_info']['uptime_ms'] > good[0]['flight_info']['uptime_ms'], 'Boot time must advance')
                        return value
                except (ValueError, OSError) as exc:
                    attempts.append(dict(at_utc=utc(), reason=str(exc))); good = []
                time.sleep(.2)
            raise ValueError('Stopped healthy SRAM boot not proven')
        finally:
            save(self.folder / (label + '.json'), dict(samples=good, attempts=attempts))

    def defaults(self, label):
        self.guard(); status = http('/api/xy-pi/status')
        require(status.get('can_query') is True and type(status.get('epoch')) is int, 'Ground owner cannot query')
        # Keep token only in these local variables; never save the session endpoint response.
        token = http('/api/xy-pi/session').get('token')
        reply = http('/api/xy-pi/query', dict(request_id=self.folder.name + '-' + label, epoch=status['epoch']), token)
        token = None
        operation_id = reply.get('operation_id'); require(type(operation_id) is int, 'Query not accepted')
        deadline = time.monotonic() + 7
        while time.monotonic() < deadline:
            stopped(http('/api/state')); value = http('/api/xy-pi/status')
            require(value.get('epoch') == status['epoch'], 'Transport epoch changed during GET')
            if value.get('busy') is False and value.get('operation_id') == operation_id:
                save(self.folder / (label + '.json'), value)
                active = value.get('active') or {}; result = value.get('result') or {}
                require(value.get('supported') is True and result.get('code') == 'queried' and result.get('operation_id') == operation_id and
                        active.get('build') == '0000B0B4' and active.get('p_wire') == 1000 and active.get('i_wire') == 350 and
                        type(active.get('generation')) is int and active['generation'] == 0, 'Fresh A591 B0B4 default GET failed')
                return value
            time.sleep(.1)
        raise ValueError('Fresh default GET timed out; no automatic retry')

    def run(self):
        self.persist()
        try:
            self.record['pins'] = offline()
            text = self.child([sys.executable, '-B', str(REPO / 'firmware/B0B4/verify_release.py'), '--external-build'], 'qualification', 300)
            require(json.loads(text).get('passed') is True, 'Full offline qualification failed')
            spec = importlib.util.spec_from_file_location('b0b4_inventory_definitions_only', HELPER)
            self.hw = importlib.util.module_from_spec(spec); spec.loader.exec_module(self.hw)
            # Old install/main/command/scan_cables entry points are never called.
            save(self.folder / 'initial_stopped.json', self.guard())
            self.record['hardware_accessed'] = True
            self.record['initial_identity'] = self.operation(0, '01_identity_before')
            require(self.record['initial_identity'][1] in (0xB0B3, 0xB0B4), 'Current SRAM stage requires explicit B3 or B4 JTAG UserCode')
            if self.stage == 'sram':
                self.operation(2, '02_B0B4_sram'); loaded_at = time.monotonic()
                self.health('03_sram_healthy', loaded_at)
                require(self.operation(0, '04_identity_B0B4') == (0x0001481B, 0xB0B4), 'SRAM UserCode must equal B0B4')
                self.defaults('05_sram_default_GET')
            self.record['passed'] = True
        except Exception as exc:
            self.record.update(error=type(exc).__name__ + ': ' + str(exc), automatic_recovery=False)
            raise
        finally:
            self.persist()
        return self.record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage', choices=('offline', 'preflight', 'sram'), default='offline')
    parser.add_argument('--execute', action='store_true', help='Explicit live-stage selection; default is offline')
    parser.add_argument('--bench-confirmed-current', action='store_true', help='Current human props-off/low-switch/correct-board assertion')
    parser.add_argument('--out', type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    if args.stage == 'offline':
        require(not args.execute, 'Offline stage cannot execute hardware')
        print(json.dumps(offline(), indent=2)); return
    require(args.execute and args.bench_confirmed_current, 'Explicit live stage and current bench confirmation required')
    folder = args.out.resolve() / (args.stage + '_' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ'))
    folder.mkdir(parents=True, exist_ok=False)
    result = Session(args.stage, folder).run()
    print(json.dumps(dict(passed=result['passed'], stage=args.stage, folder=str(folder), flash_written=False, flight_ready=False), indent=2))


if __name__ == '__main__':
    main()
