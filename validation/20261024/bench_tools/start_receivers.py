"""Operator-run switch to the B0B0 read-only receivers. No FPGA/Flash/serial writes."""
from pathlib import Path
import datetime as dt
import json
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request

from serial.tools import list_ports
from install_sram import verify, RELEASE

BASE = Path(__file__).resolve().parent
ROOT = BASE.parent.parent
PROFILE = 'mtf01p.b0b0_synthesis_fix.v7'
TARGETS = [(8765, 'COM17', 'SiK', (0x403, 0x6015)),
           (8767, 'COM23', 'USB', (0x1a86, 0x7523))]


def state(port):
    try:
        with urllib.request.urlopen(f'http://127.0.0.1:{port}/api/state', timeout=4) as response:
            return json.load(response)
    except urllib.error.URLError:
        # Refused connection is absent; a listening but unresponsive service is an error.
        with socket.socket() as probe:
            probe.settimeout(2)
            if probe.connect_ex(('127.0.0.1', port)) == 0:
                raise RuntimeError(f'Port {port} is occupied but has no readable receiver state')
        return None


def stopped(s):
    d = s.get('data') or {}
    return bool(s.get('fresh') and s.get('flight_info_fresh') and
                d.get('armed') is False and d.get('controller_enabled') is False and
                d.get('physical_output_active') is False and
                d.get('command_us') == [1000] * 4 and d.get('pwm_us') == [1000] * 4)


def ready(s, com, source):
    if not s:
        return False
    config = (s.get('recording') or {}).get('source') or {}
    return bool(s.get('receiver_profile') == PROFILE and s.get('serial_writes') is False and
                (s.get('flight_info') or {}).get('build_id') in (0xB0AC, 0xB0AF, 0xB0B0) and
                config.get('port') == com and config.get('baud') == 115200 and
                config.get('source') == source and stopped(s))


def main():
    verify()  # Frozen image/source verification only; never accesses hardware.
    available = {p.device: (p.vid, p.pid) for p in list_ports.comports()}
    for _, com, _, identity in TARGETS:
        if available.get(com) != identity:
            raise RuntimeError(f'Expected telemetry device missing: {com}')
    before = {port: state(port) for port, *_ in TARGETS}
    if not any(s and stopped(s) for s in before.values()):
        raise RuntimeError('A fresh, disarmed receiver reporting all outputs 1000 us is required')
    folder = BASE / 'hardware' / dt.datetime.now(dt.timezone.utc).strftime('receiver_manual_%Y%m%dT%H%M%S_%fZ')
    folder.mkdir(parents=True)
    (folder / 'before.json').write_text(json.dumps(before, indent=2), encoding='utf-8')
    for port, *_ in TARGETS:
        s = before[port]
        if s is None:
            continue
        if not s.get('receiver_profile', '').startswith('mtf01p.') or s.get('serial_writes') is not False:
            raise RuntimeError(f'Unexpected service on {port}; no process will be terminated')
        # Empty inactive receiver is allowed only with a separate fresh stopped witness.
        if s.get('data') and not stopped(s):
            raise RuntimeError(f'Receiver {port} must be fresh and stopped before switching')
    children = []
    for port, com, source, _ in TARGETS:
        s = before[port]
        if ready(s, com, source):
            continue
        if s is not None:
            req = urllib.request.Request(f'http://127.0.0.1:{port}/api/service/stop',
                                         data=b'{}', headers={'Content-Type': 'application/json'})
            with urllib.request.urlopen(req, timeout=4) as response:
                if not json.load(response).get('stopping'):
                    raise RuntimeError(f'Receiver {port} did not accept graceful stop')
            deadline = time.monotonic() + 10
            while time.monotonic() < deadline:
                with socket.socket() as probe:
                    probe.settimeout(.3)
                    if probe.connect_ex(('127.0.0.1', port)) != 0:
                        break
                time.sleep(.2)
            else:
                raise RuntimeError(f'Receiver {port} still listening; no second process started')
        with (folder / f'{port}.stdout.log').open('wb') as out, (folder / f'{port}.stderr.log').open('wb') as err:
            child = subprocess.Popen([sys.executable, '-u', str(RELEASE / 'ground/ground_server.py'),
                                      '--port', com, '--baud', '115200', '--source', source,
                                      '--http-port', str(port), '--logs', str(ROOT / 'flight_logs')],
                                     cwd=ROOT, stdout=out, stderr=err,
                                     creationflags=subprocess.CREATE_NO_WINDOW)
        children.append({'port': port, 'pid': child.pid, 'com': com})
        (folder / 'processes.json').write_text(json.dumps(children, indent=2), encoding='utf-8')
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            if child.poll() is not None:
                raise RuntimeError(f'Receiver {port} exited; see {folder}')
            try:
                after = state(port)
            except (OSError, RuntimeError, ValueError):
                after = None
            if ready(after, com, source):
                (folder / f'after_{port}.json').write_text(json.dumps(after, indent=2), encoding='utf-8')
                break
            time.sleep(.5)
        else:
            raise RuntimeError(f'Receiver {port} did not reach fresh stopped state; see {folder}')
    print('B0B0 read-only receivers ready. No FPGA or Flash programming performed.')
    print('Website: http://127.0.0.1:8765/')
    print('Evidence:', folder)


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print('Receiver switch stopped:', exc)
        sys.exit(1)
