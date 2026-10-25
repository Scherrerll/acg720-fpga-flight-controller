"""Audit the repair's bounded source changes; does not claim netlist equivalence."""
import argparse
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT.parent / 'B0B0/source_snapshot'
PARENT = ROOT.parent / 'B0B1/source'
REPAIR = 'core/imu_temporal_check_pipelined.v'
COMMUNICATION = {'acg720_ano_port.v', 'telemetry_tx.v', 'diagnostic_uart.v',
                 'acg720_ano_port.gprj', 'build.tcl'}
NEW = {'sik_imu_diagnostic.v'}
REMOVED = {'diagnostic_uart.v'}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tokens(text):
    text = re.sub(r'/\*.*?\*/|//[^\n]*', '', text, flags=re.S)
    return re.findall(r'[A-Za-z_$][\w$]*|\d+\s*\x27[sS]?[bBoOdDhH][\da-fA-F_xXzZ?]+|\d+|[^\s]', text)


def check():
    baseline = json.loads((ROOT / 'baseline.json').read_text())
    for name, digest in baseline['source_sha256'].items():
        if sha(BASE / name) != digest:
            raise ValueError('Frozen B0B0 source changed: ' + name)
    parent = json.loads((ROOT / 'parent_snapshot.json').read_text())['files']
    for name, digest in parent.items():
        if sha(PARENT / name) != digest:
            raise ValueError('Frozen B0B1 parent changed: ' + name)
    current = {p.relative_to(ROOT / 'source').as_posix(): sha(p)
               for p in (ROOT / 'source').rglob('*') if p.is_file()}
    if set(current) != (set(parent) - REMOVED) | NEW:
        raise ValueError('Unexpected repair source file set')
    changed = {name for name in parent if name in current and current[name] != parent[name]}
    if not changed <= COMMUNICATION | {REPAIR}:
        raise ValueError('Unrelated source changed: ' + repr(changed - COMMUNICATION - {REPAIR}))
    projected = []
    for name in ('core/ano_attitude_estimator.v', 'core/imu_checked_guard_pipelined.v',
                 'core/imu_pipeline_pipelined.v'):
        text = (ROOT / 'source' / name).read_text()
        text = re.sub(r'//\s*DIAG_TAP_BEGIN[^\n]*\n.*?//\s*DIAG_TAP_END[^\n]*(?:\n|$)', '', text, flags=re.S)
        text = re.sub(r',\s*\)', ')', text)
        old = re.sub(r',\s*\)', ')', (BASE / name).read_text())
        if tokens(text) != tokens(old):
            raise ValueError('Protected control tokens changed: ' + name)
        projected.append(name)
    name = 'core/flight_core.v'
    text = (ROOT / 'source' / name).read_text()
    text = re.sub(r',\s*output wire diag_raw_valid,diag_pose_valid,diag_fault_valid,.*?diag_pose_count\s*\n',
                  '\n', text, count=1, flags=re.S)
    text = re.sub(r',\s*\.diag_taking_off\(taking_off\).*?\.diag_pose_count\(diag_pose_count\)',
                  '', text, count=1, flags=re.S)
    if tokens(text) != tokens((BASE / name).read_text()):
        raise ValueError('Flight core changed beyond diagnostic outputs')
    projected.append(name)
    # Motor, RC, gains, takeoff/landing, geometry and fusion stay byte-for-byte.
    protected = [p.relative_to(BASE).as_posix() for p in BASE.rglob('*')
                 if p.is_file() and p.suffix in ('.v', '.vh')
                 and p.relative_to(BASE).as_posix() not in projected
                 and p.relative_to(BASE).as_posix() not in
                 {REPAIR, 'core/flight_core.v', 'acg720_ano_port.v', 'telemetry_tx.v'}]
    for name in protected:
        if current[name] != sha(BASE / name):
            raise ValueError('Unrelated baseline control source changed: ' + name)
    top = (ROOT / 'source/acg720_ano_port.v').read_text()
    project = (ROOT / 'source/acg720_ano_port.gprj').read_text()
    if (any(name in tokens(top) for name in
            ('diagnostic_uart', 'usb_diagnostic', 'ENABLE_USB_DIAGNOSTIC'))
            or 'diagnostic_uart.v' in project):
        raise ValueError('Removed USB high-rate sender remains in synthesized project')
    return dict(passed=True, changed_parent_files=sorted(changed), new_files=sorted(NEW),
                removed_parent_files=sorted(REMOVED), usb_high_rate_in_project=False,
                projected_control_files=projected, unchanged_control_files=protected,
                source_sha256=current, hardware_accessed=False, flash_changed=False,
                whole_synthesized_netlist_equivalence_proved=False, flight_ready=False)


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output', type=Path)
    args = ap.parse_args()
    result = check()
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'source_sha256'}))
