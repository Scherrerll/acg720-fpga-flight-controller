"""Verify the frozen B0B0 release, optionally install to SRAM for props-off acceptance.

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
FIXTURE = Path('C:\\Users\\ScherrerL\\Desktop\\apple\\routing_closure_20261024\\B0B0_51_608MHz_verified\\fixture')
IMAGE = FIXTURE / 'impl/pnr/acg720_ano_port.fs'
IMAGE_SHA = '83653a2f405cc467ac553fd81ac57d2981c5a9f52543afbbd3368881ab4ac111'
CLI = 'C:/Gowin/Gowin_V1.9.12.04_x64/Programmer/bin/programmer_cli.exe'
URL = 'http://127.0.0.1:8767/api/state'
PREDECESSORS = (0xB0AC, 0xB0AF)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def verify():
    import runpy, contextlib, io
    checker=Path('C:\\Users\\ScherrerL\\Desktop\\apple\\routing_closure_20261024\\verify_package.py')
    require(sha(checker)=='da36413ed311859f3db39bed28c7b2cd24c6fa479904d1ed2ad7a6b94c25a05a', 'Package verifier changed')
    with contextlib.redirect_stdout(io.StringIO()):runpy.run_path(str(checker))['main']()
    manifest=Path('C:\\Users\\ScherrerL\\Desktop\\apple\\routing_closure_20261024\\B0B0_51_608MHz_verified\\manifest.json')
    require(sha(manifest)=='3169a3a24c1944f5560efc9f4d4f3fbef735d2a236aa1bb81717d13a11ff07c9', 'Selected package changed')
    require(sha(IMAGE)==IMAGE_SHA, 'Selected image changed')
    for name,digest in {'ground\\analysis.py': '808e74adea58424a6e2eddda4642a95e1412a96f051e2e166eedf8f84e53b512', 'ground\\dashboard.html': '7c129e19f043bb0645f1403a2205fa65fb4b7bdc96c4283e7d3acbafcee87cd8', 'ground\\dashboard.js': 'bdbde38c12136b6541c4715d27967c8cfaddbfcf5bbfea3f4b7b808f75c6d90b', 'ground\\ground_server.py': '88b7db3d6ab938fdfa0567725c2617a1563c77dcd594cfd4f21784ae75009f79', 'ground\\launch.py': '134799e8d4e3853847afa1a1bb1786c070afe13200273131f0815a9ac8c285d3', 'ground\\logs-ui.html': '72382abf04fb13e725e32f49f933e263e06edc6dcdf7c912e009fe43870cad90', 'ground\\logs.html': '95d6e092c5a0f5d944fb7092066097aa18d92e3aaf814aa7e75d72fff0e4a412', 'ground\\logs.js': '121882f31a2621e03e5494b8672748a40adfcb681cf5e7b9c6c3a1c96591ec34', 'ground\\mtf-ui.js': '3ed46e9b8f791fb7891bf664804eb2e13aa55d01a4b4065c7d6379f65f65b858', 'ground\\mtf_protocol.py': '1d26ff571c5fc0ffe8307f3d73a1f340924627302a081029f9f371c6a5a18844', 'ground\\nav_protocol.py': 'e9e01fdc31c8e286f347d0edcebee37be30e719842596d83e5c7a73c0b7eab73', 'ground\\protocol.py': '84149f22be872de2e93aa13398cea56e4d8f725917af3881d5e2258c9217900d', 'ground\\recorder.py': '0d14b8f99bbaec95a7d55d94140037ad22b50be680eeded980977cf97f3c18cf', 'ground\\rotation_protocol.py': '731761ea9388304e2d9268c0786b8683fc8c7c57fdbfb3973a65ba8709726c23', 'ground\\start_monitor.cmd': '341927114a537ad03818be3f60ccb948e118c8e660dc3e0976e93b7dda31a9e0', 'ground\\telemetry-ui.js': '19a632be2f5f893f22a1f3e3b301a6cbf9f74016727686407b864c8bcc92733f', 'ground\\test_ano_control.py': '0d1e826a9e40ee5b2c892fa6650affe243b9305f9c24632d657c5e667f871bd4', 'ground\\test_height_loss.py': 'ee391d03d55caf4ad44ec0d2a8cef8292876189943963a364fa5542a6c7675d8', 'ground\\test_mtf.py': '6318cbe2e432168e3784462253fbfb30511eb9129bc3be804168206fd15442d7', 'ground\\test_review_fixes.py': '2ef2ac15eb233b20136094fe9bfd27f2a0240168c70fe1292d976bc99e394e82', 'ground\\test_system.py': 'b32f44e709e6ae08839ccd570c4dc509c4af66038f897cd3a4aff2d1d60ea131', 'ground\\ui.css': '4d581350fefe11f8c174119bd5c4cde3b760ba81a6cc559eec68dbf00c08dfc0', 'ground\\verify_log.py': 'c36473cdafb307cbd82a232f6ff0a72563d68d201f9b91e73bab62298ea5a3ad'}.items():require(sha(BASE/name)==digest,'Read-only receiver changed: '+name)
    require(not (BASE/'HARDWARE_REJECTED.json').exists(), 'Hardware acceptance previously rejected this selection')
    return sha(manifest)


def state():
    with urllib.request.urlopen(URL, timeout=4) as response:
        return json.load(response)


def stopped(snapshot, build):
    data = snapshot.get('data') or {}
    require(snapshot.get('status') == 'live' and snapshot.get('fresh') and snapshot.get('flight_info_fresh'), 'Fresh telemetry required')
    require(snapshot.get('receiver_profile') == 'mtf01p.b0b0_synthesis_fix.v7' and snapshot.get('serial_writes') is False, 'Wrong receiver')
    require((snapshot.get('flight_info') or {}).get('build_id') == build, 'Unexpected live build')
    require(data.get('armed') is False and data.get('controller_enabled') is False and
            data.get('physical_output_active') is False and data.get('pwm_us') == [1000] * 4 and
            data.get('command_us') == [1000] * 4, 'Disarmed reported 1000 us outputs required')
    channels = data.get('rc_us') or []
    radio_off = data.get('rc_valid') is False and channels == [0]*8
    radio_low = data.get('rc_valid') is True and len(channels)>=7 and 800<=channels[2]<=1100 and channels[4]<1800 and channels[6]<1800
    require(radio_off or radio_low, 'RC must be explicitly invalid with all channels zero, or valid at low throttle/SWA/SWC')


def capture_predecessor(snapshot):
    build = (snapshot.get('flight_info') or {}).get('build_id')
    require(build in PREDECESSORS, 'Unknown predecessor build')
    stopped(snapshot, build)
    return build


def predecessor_identity(identity, build):
    require(build in PREDECESSORS, 'Unknown predecessor build')
    require('0x0001481B' in identity and re.search(r'0x%08X\b' % build, identity, re.I),
            'Unexpected JTAG predecessor identity')


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
    require(len([port for port in list_ports.comports() if (port.vid, port.pid, port.serial_number) == (0x403, 0x6014, '6')]) == 1,
            'Known programmer missing or ambiguous')
    before = state()
    predecessor = capture_predecessor(before)
    folder = BASE / 'hardware' / dt.datetime.now(dt.timezone.utc).strftime('sram_%Y%m%dT%H%M%S_%fZ')
    folder.mkdir(parents=True, exist_ok=False)
    record = dict(installed=False, sram_write_attempted=False, sram_written=False, flash_written=False,
                  flight_ready=False, image_sha256=IMAGE_SHA, selection_sha256=selection_sha,
                  human_confirmation='Current props-off/RC-off confirmation supplied via --bench-confirmed.',
                  predecessor_build=predecessor, before=summary(before), location=args.location)
    try:
        identity = programmer(0, args.location, folder / 'identity_before.txt')
        predecessor_identity(identity, predecessor)
        require(verify() == selection_sha, 'Selection changed before installation')
        stopped(state(), predecessor)
        record['sram_write_attempted'] = True
        programmer(2, args.location, folder / 'program_sram.txt')
        record['sram_written'] = True
        identity = programmer(0, args.location, folder / 'identity_after.txt')
        require('0x0001481B' in identity and re.search(r'0x0000B0B0\b', identity, re.I), 'SRAM identity mismatch')
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
                if snapshot.get('fresh') and (snapshot.get('flight_info') or {}).get('build_id') == 0xB0B0:
                    stopped(snapshot, 0xB0B0)
                time.sleep(0.25)
        late = [item for item in observations if item['elapsed_s'] >= 10]
        require(len(late) >= 20, 'Insufficient startup observations')
        require(all(item['state']['fresh'] and item['state']['flight_info']['build_id'] == 0xB0B0 and
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
