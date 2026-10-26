"""One authorized bench session; fixed B0B3 SRAM only, no Flash operation."""
from pathlib import Path
import hashlib
import importlib.util
import json
import subprocess
import sys
from datetime import datetime, timezone

REPO = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
IMAGE = REPO / 'firmware/B0B3/release/B0B3_selected_P3R0.fs'
IMAGE_SHA = 'a5b893b25a5e510348c8a4ac75c914b8a14473bbfb054b4cc4040b86800f64dd'
MANIFEST_SHA = '23374b5c3aca40e8e71a8ae7ad037541484416a752c683b378083a78a3d4f7a7'
HELPER = REPO / 'firmware/B0B2/tools/install_sram.py'
HELPER_SHA = '6b872ec4ab8c0425f8d477d9e2ac63a21f01f8f0bfe69635cbf3420b796f49b1'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def require(ok, why):
    if not ok:
        raise ValueError(why)

def save(name, value):
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

def verify():
    require(sha(HELPER) == HELPER_SHA, 'Low-level helper changed')
    require(sha(IMAGE) == IMAGE_SHA, 'Qualified B0B3 image changed')
    require(sha(REPO / 'firmware/B0B3/export_manifest.json') == MANIFEST_SHA, 'B0B3 manifest changed')
    ran = subprocess.run([sys.executable, '-B', str(REPO / 'firmware/B0B3/verify_export.py')], cwd=REPO,
                         capture_output=True, text=True, encoding='utf-8', timeout=60)
    require(ran.returncode == 0, 'B0B3 export verifier failed: ' + ran.stderr)
    value = json.loads(ran.stdout)
    require(value.get('passed') is True and value.get('manifest_sha256') == MANIFEST_SHA, 'B0B3 qualification failed')
    return value

def main():
    require(sys.argv[1:] == ['--authorized-sram-only'], 'Explicit session flag required')
    report = dict(started_utc=datetime.now(timezone.utc).isoformat(), image=str(IMAGE), image_sha256=IMAGE_SHA,
                  human_confirmation='User confirmed props removed, CH5 low; authorized this SRAM download and default P/I bench verification, no Flash.',
                  installed=False, sram_write_attempted=False, sram_written=False, flash_written=False,
                  flight_qualified=False, operations=[], installer_sha256=sha(Path(__file__)))
    try:
        report['qualification'] = verify()
        spec = importlib.util.spec_from_file_location('authorized_low_level_sram_helper', HELPER)
        hw = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(hw)
        selected = hw.known_programmer(hw.programmers())
        report['programmer'] = selected
        cable = hw.scan_cables(OUT / 'cables_before.txt')
        report['cable'] = cable
        before = hw.state()
        old_build = hw.stopped(before)
        require(before.get('port') == 'COM17', 'Unexpected telemetry port')
        require((before.get('flight_info') or {}).get('taking_off') is False, 'Taking-off state not stopped')
        save('telemetry_before.json', before)
        report['operations'].append(0)
        old = hw.identity(hw.command(0, OUT / 'identity_before.txt', location=cable['location']))
        require(old == (hw.DEVICE_ID, old_build), 'Current device identity mismatches live stopped telemetry')
        require(verify() == report['qualification'], 'Qualification changed before SRAM')
        require(hw.known_programmer(hw.programmers()) == selected, 'Programmer changed')
        require(hw.scan_cables(OUT / 'cables_prewrite.txt') == cable, 'Cable changed')
        current = hw.state()
        hw.stopped(current, old_build)
        require(current.get('port') == 'COM17' and (current.get('flight_info') or {}).get('taking_off') is False,
                'Current telemetry not same stopped target')
        save('telemetry_prewrite.json', current)
        require(sha(IMAGE) == IMAGE_SHA, 'Image changed at write boundary')
        report['sram_write_attempted'] = True
        report['operations'].append(2)
        save('sram_install_report.json', report)
        hw.command(2, OUT / 'program_sram.txt', IMAGE, IMAGE_SHA, location=cable['location'])
        report['sram_written'] = True
        report['operations'].append(0)
        after = hw.identity(hw.command(0, OUT / 'identity_after.txt', location=cable['location']))
        report['after_identity'] = dict(device_id=after[0], usercode=after[1])
        require(after == (hw.DEVICE_ID, 0xB0B3), 'Post-load identity must be selected B0B3')
        report['installed'] = True
    except Exception as exc:
        report['error'] = type(exc).__name__ + ': ' + str(exc)
        raise
    finally:
        report['finished_utc'] = datetime.now(timezone.utc).isoformat()
        save('sram_install_report.json', report)
        print(json.dumps(report, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
