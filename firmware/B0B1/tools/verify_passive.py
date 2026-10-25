"""Prove diagnostic additions leave the original control Verilog token stream intact."""
import argparse
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT.parent / 'B0B0/source_snapshot'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tokens(text):
    text = re.sub(r'/\*.*?\*/', '', text, flags=re.S)
    text = re.sub(r'//[^\n]*', '', text)
    return re.findall(r'[A-Za-z_$][\w$]*|\d+\s*\x27[sS]?[bBoOdDhH][\da-fA-F_xXzZ?]+|\d+|[^\s]', text)


def check():
    baseline = json.loads((ROOT / 'baseline.json').read_text())
    for name, digest in baseline['source_sha256'].items():
        if sha(BASE / name) != digest:
            raise ValueError('Frozen repository baseline changed: ' + name)
    protected = ['core/imu_temporal_check_pipelined.v', 'core/imu_checked_guard_pipelined.v',
                 'core/ano_attitude_estimator.v', 'core/imu_pipeline_pipelined.v']
    results = []
    for name in protected:
        text = (ROOT / 'source' / name).read_text()
        text = re.sub(r'//\s*DIAG_TAP_BEGIN[^\n]*\n.*?//\s*DIAG_TAP_END[^\n]*(?:\n|$)', '', text, flags=re.S)
        # Instrumented ANSI ports need a comma before the diagnostic-only region.
        text = re.sub(r',\s*\)', ')', text)
        old = re.sub(r',\s*\)', ')', (BASE / name).read_text())
        if tokens(text) != tokens(old):
            raise ValueError('Non-diagnostic control tokens changed: ' + name)
        results.append(name)
    name = 'core/flight_core.v'
    text = (ROOT / 'source' / name).read_text()
    text = re.sub(r',\s*output wire diag_raw_valid,diag_pose_valid,diag_fault_valid,.*?diag_pose_count\s*\n', '\n', text, count=1, flags=re.S)
    text = re.sub(r',\s*\.diag_taking_off\(taking_off\).*?\.diag_pose_count\(diag_pose_count\)', '', text, count=1, flags=re.S)
    if tokens(text) != tokens((BASE / name).read_text()):
        raise ValueError('Flight core changed beyond diagnostic connections')
    results.append(name)
    name = 'acg720_ano_port.v'
    text = (ROOT / 'source' / name).read_text()
    text = re.sub(r' // Separate USB diagnostic.*?wire \[31:0\] diag_clock_ticks,diag_max_accept_gap,diag_raw_count,diag_pose_count;',
                  ' assign radio_tx=uart_tx;', text, count=1, flags=re.S)
    text = re.sub(r',\s*\.diag_raw_valid\(diag_raw_valid\).*?\.diag_pose_count\(diag_pose_count\)', '', text, count=1, flags=re.S)
    text = re.sub(r'\n diagnostic_uart usb_diagnostic\(.*?\.tx\(uart_tx\)\);\n', '\n', text, count=1, flags=re.S)
    text = text.replace("32'h0000B0B1", "32'h0000B0B0")
    text = text.replace('.tx(telemetry_radio_tx)', '.tx(uart_tx)')
    if tokens(text) != tokens((BASE / name).read_text()):
        raise ValueError('Top changed beyond diagnostic wiring and build identity')
    results.append(name)
    for path in [*BASE.rglob('*.v'), *BASE.rglob('*.vh')]:
        name = path.relative_to(BASE).as_posix()
        if name not in results:
            if sha(path) != sha(ROOT / 'source' / name):
                raise ValueError('Unrelated Verilog changed: ' + name)
            results.append(name)
    return dict(passed=True, baseline_source_count=len(baseline['source_sha256']),
                checked_control_verilog_and_header_count=len(results),
                exceptions='Only explicitly stripped diagnostic outputs/state and top serial routing/build ID',
                source_sha256={p.relative_to(ROOT / 'source').as_posix(): sha(p)
                               for p in (ROOT / 'source').rglob('*') if p.is_file()},
                hardware_accessed=False, flash_changed=False,
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
