"""Install the sealed V15 image to SRAM with the existing B0B2 hardware guards.

Default is offline verification. --preflight only checks live stopped telemetry
and enumerates serial devices. SRAM requires --program --bench-confirmed after
current human props-off/stable-bench/low-throttle/SWA/SWC confirmation.
No Flash operation or control command is implemented.
"""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import hashlib
import importlib.util
import json
import math
import re
import sys

FW = Path(__file__).resolve().parents[1]
BUNDLE = FW / 'verified_timing_20261025'
MANIFEST_SHA256 = 'c0827d5331af3055770dd999aee89e82ee5074ee20cae3aa076a0956155edca1'
HELPER_SHA256 = '6b872ec4ab8c0425f8d477d9e2ac63a21f01f8f0bfe69635cbf3420b796f49b1'
IMAGE_SHA256 = '3b9920acc1abecf6e0ef50465f5bc408d9b74af2ac6d046cb151137a375b4306'
EVIDENCE_INDEX_SHA256 = 'd0e4abdc824ca1ceb4202f019dfdc2b079482a85096d578f53a04955b83600cb'


def require(ok, reason):
    if not ok:
        raise ValueError(reason)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def tree(path):
    return {p.relative_to(path).as_posix(): sha(p) for p in path.rglob('*') if p.is_file()}


def load_hardware_helpers():
    path = FW / 'tools/install_sram.py'
    require(sha(path) == HELPER_SHA256, 'Existing hardware guards changed')
    spec = importlib.util.spec_from_file_location('b0b2_verified_hardware_helpers', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def verify():
    require(sha(BUNDLE / 'manifest.json') == MANIFEST_SHA256, 'Sealed V15 manifest changed')
    m = json.loads((BUNDLE / 'manifest.json').read_text())
    require(m['status'] == 'qualified_offline' and m['source_promoted'] is True, 'V15 delivery not qualified')
    require(tree(FW / 'source') == tree(BUNDLE / 'source') == m['source_sha256'], 'Current or archived source changed')
    for folder, key in [('project', 'project_sha256'), ('reports', 'report_sha256'), ('bitstream', 'bitstream_sha256')]:
        for name, digest in m[key].items():
            require(sha(BUNDLE / folder / name) == digest, f'Changed delivery file: {folder}/{name}')
    require(sha(BUNDLE / 'full_sta.py') == m['full_sta_sha256'], 'Full STA parser changed')
    require(sha(BUNDLE / 'evidence/index.json') == EVIDENCE_INDEX_SHA256, 'Proof index changed')
    evidence = json.loads((BUNDLE / 'evidence/index.json').read_text())
    require(len(evidence) == m['evidence_item_count'] == 313, 'Incomplete proof archive')
    for digest in evidence.values():
        require(sha(BUNDLE / 'evidence/blobs' / digest) == digest, 'Archived proof changed: ' + digest)
    audit = json.loads((BUNDLE / 'reports/complete_audit.json').read_text())
    require(all(audit[k] is True for k in ('physical_passed', 'routing_passed', 'full_timing_passed',
                                          'pins_passed', 'part_passed', 'identity_passed', 'output_freshness_passed')),
            'Physical qualification incomplete')
    require(audit['unrouted_nets'] == 0 and audit['sta']['constraint_period_ns'] == 19.5,
            'Routing or original clock constraint failed')
    kinds = ('setup', 'hold', 'recovery', 'removal', 'minimum_pulse_width')
    require(all(math.isfinite(audit['sta']['worst_reported_slack_ns'][k]) and
                audit['sta']['worst_reported_slack_ns'][k] >= 0 for k in kinds), 'Full STA did not pass')
    for name in ('source_verification.json', 'source_review.json', 'policy_protocol_verification.json'):
        proof = json.loads((BUNDLE / 'reports' / name).read_text())
        require(proof['passed'] is True and proof['source_sha256'] == m['source_sha256'], 'Functional proof mismatch: ' + name)
    for name in ('mapping_proof.json', 'mapped_reset_proof.json', 'synthesis_binding.json'):
        proof = json.loads((BUNDLE / 'reports' / name).read_text())
        require(proof['passed'] is True and proof['netlist_sha256'] == m['netlist_sha256'], 'Mapped proof mismatch: ' + name)
    image = BUNDLE / 'bitstream/acg720_ano_port.fs'
    require(sha(image) == IMAGE_SHA256, 'Image differs from qualified V15 bitstream')
    with image.open() as stream:
        header = ''.join(next(stream, '') for _ in range(16))
    require(all(re.search(p, header, re.I) for p in (
        r'//UserCode: 0x0000b0b2\b', r'//Part Number: GW5AT-LV60PG484AC1/I0',
        r'//Device-package: GW5AT-60B-PBGA484A\b')), 'Image identity mismatch')
    load_hardware_helpers()
    return dict(passed=True, image=str(image), image_sha256=IMAGE_SHA256,
                manifest_sha256=MANIFEST_SHA256, hardware_helpers_sha256=HELPER_SHA256,
                source_files=len(m['source_sha256']), evidence_items=len(evidence),
                hardware_accessed=False, flash_written=False)


def preflight(hw):
    inventory = hw.programmers()
    selected = hw.known_programmer(inventory)
    before = hw.state()
    build_id = hw.stopped(before)
    return dict(programmer=selected, telemetry_build_id=build_id, telemetry=before)


def install(bench_confirmed=False):
    require(bench_confirmed is True, 'Current human bench confirmation required')
    verified = verify()
    hw = load_hardware_helpers()
    folder = FW / 'hardware' / datetime.now(timezone.utc).strftime('v15_sram_%Y%m%dT%H%M%S_%fZ')
    folder.mkdir(parents=True, exist_ok=False)
    report = dict(installed=False, hardware_accessed=False, sram_write_attempted=False,
                  sram_written=False, flash_written=False, bench_only=True, flight_ready=False,
                  operations=[], scans=[], folder=str(folder), operator_confirmation_flag=True,
                  confirmation_scope='Current human confirmed props-off, stable bench, low throttle and SWA/SWC low.')
    try:
        report['verification'] = verified
        report['hardware_accessed'] = True
        initial = preflight(hw)
        selected = initial['programmer']
        report['programmer_selection'] = selected
        old_build = initial['telemetry_build_id']
        (folder / 'telemetry_before.json').write_text(json.dumps(initial['telemetry'], indent=2) + '\n')
        cable = hw.scan_cables(folder / 'cables_before.txt')
        report['scans'].append(dict(phase='initial', selection=cable))
        report['operations'].append(0)
        old = hw.identity(hw.command(0, folder / 'identity_before.txt', location=cable['location']))
        require(old == (hw.DEVICE_ID, old_build), 'Device identity differs from stopped telemetry')
        require(verify() == verified, 'Qualification changed before SRAM write')
        require(hw.known_programmer(hw.programmers()) == selected, 'Programmer inventory changed')
        cable_latest = hw.scan_cables(folder / 'cables_prewrite.txt')
        report['scans'].append(dict(phase='prewrite', selection=cable_latest))
        require(cable_latest == cable, 'Selected cable changed before SRAM write')
        require(verify() == verified, 'Qualification changed at SRAM write boundary')
        latest = hw.state()
        hw.stopped(latest, old_build)
        (folder / 'telemetry_prewrite.json').write_text(json.dumps(latest, indent=2) + '\n')
        report['sram_write_attempted'] = True
        report['operations'].append(2)
        hw.command(2, folder / 'program_sram.txt', Path(verified['image']), verified['image_sha256'], location=cable['location'])
        report['sram_written'] = True
        report['operations'].append(0)
        after = hw.identity(hw.command(0, folder / 'identity_after.txt', location=cable['location']))
        require(after == (hw.DEVICE_ID, hw.BUILD_ID), 'Post-write identity is not B0B2')
        report['after_identity'] = dict(device_id=after[0], usercode=after[1])
        hw.wait_stopped_after_load(folder, report)
        require(verify() == verified, 'Qualification changed during SRAM installation')
        report['installed'] = True
        return report
    except Exception as exc:
        report['error'] = f'{type(exc).__name__}: {exc}'
        raise
    finally:
        report.update(utc=datetime.now(timezone.utc).isoformat(), installer_sha256=sha(Path(__file__)))
        (folder / 'report.json').write_text(json.dumps(report, indent=2) + '\n')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--program', action='store_true')
    mode.add_argument('--preflight', action='store_true')
    parser.add_argument('--bench-confirmed', action='store_true')
    args = parser.parse_args(argv)
    try:
        if args.program:
            result = install(args.bench_confirmed)
        else:
            result = verify()
            if args.preflight:
                result['preflight'] = preflight(load_hardware_helpers())
                result['hardware_accessed'] = True
        print(json.dumps(result, indent=2))
        return 0
    except Exception as exc:
        print(json.dumps(dict(passed=False, error=f'{type(exc).__name__}: {exc}')), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
