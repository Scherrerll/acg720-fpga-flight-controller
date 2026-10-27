"""Seal only this agent's terminal v5 P3R0 evidence; no vendor invocation."""
from pathlib import Path
import hashlib
import json
import re

O = Path(__file__).resolve().parent
R = O.parents[4]
A = R / 'out/z_aw_fix_20261026/compact_aw_v5/physical_p3r0_01'
V = A / 'verification'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def receipt(path):
    return {'bytes': path.stat().st_size, 'sha256': sha(path)}

inp = json.loads((V / 'build_input.json').read_text())
ex = json.loads((V / 'physical_exit.json').read_text())
log = (V / 'physical.log').read_text()
expected = inp['source_sha256']
assert len(expected) == 55
assert ex['actual_p_wait'] == 1 and ex['normal_wait_return'] is True
assert 'Error: DesRoute failed.' in log
assert re.search(r'PR0004\) : There are total 648 unrouted nets', log)
assert sha(V / 'physical.log') == ex['log_sha256']
assert 'Skip synthesis' in log
assert inp['physical_options'] == {
    'place': 3, 'route': 0, 'map_option': 2,
    'replicate_resources': 0, 'timing_driven': 1}
assert inp['period_ns'] == 20 and inp['usercode'] == '0000B0B4'
assert expected['position/mtf_xyz_hold_control.v'] == (
    '04e75ada52551d5622af060efe38fda9aa66ff25199bfb67651f9ec5315ed873')
checks = []
for root, hashes in [
    (Path(inp['canonical_override']), expected),
    (A / 'source', expected),
    (Path(inp['donor']) / 'source', expected),
    (R / 'firmware/B0B4/source', inp['original_B4_source55']),
    (R / 'out/z_aw_fix_20261026/compact_aw_v4/canonical/source',
     inp['v4_source55']),
]:
    assert len(hashes) == 55
    assert all(sha(root / p) == h for p, h in hashes.items())
    checks.append({'source': str(root), 'source55_match': True})
vg = A / 'source/impl/gwsynthesis/acg720_ano_port.vg'
assert sha(vg) == inp['donor_netlist_sha256'] == (
    '2d670218e97041bb3d4cc7c67218f4bef12e5bf96261225b9b97203ce3b4a1c9')
donor = Path(inp['donor'])
synex = json.loads((donor / 'verification/synthesis_exit.json').read_text())
assert synex['actual_p_wait'] == 0 and synex['normal_wait_return'] is True
for suffix, name in [
    ('synthesis_summary', 'synthesis_summary'),
    ('synthesis_exit', 'synthesis_exit'),
    ('mapped_audit', 'mapped_audit'),
    ('gain_port_audit', 'gain_port_audit'),
    ('strict_ff_clock_audit', 'strict_ff_clock_audit'),
]:
    assert sha(donor / ('verification/' + name + '.json')) == inp['donor_' + suffix + '_sha256']
pnr = A / 'source/impl/pnr'
absent = {s: not (pnr / ('acg720_ano_port.' + s)).exists()
          for s in ['tr', 'fs', 'pr']}
assert all(absent.values())
assert not (V / 'physical_audit.json').exists()
paths = [V / n for n in [
    'build_input.json', 'physical_input.json', 'physical_process.json',
    'physical_exit.json', 'physical.log', 'build_failure.json',
    'project_serialization_check.json']]
paths += [A / 'physical.tcl', A / 'source/physical.gprj', vg,
          A / 'source/acg720_ano_port.cst', A / 'source/acg720_ano_port.sdc',
          pnr / 'acg720_ano_port.rpt.txt', pnr / 'acg720_ano_port.pin.html',
          pnr / 'device.cfg']
paths += [donor / ('verification/' + n) for n in [
    'build_input.json', 'synthesis_input.json', 'synthesis_exit.json',
    'synthesis.log', 'synthesis_summary.json', 'mapped_audit.json',
    'gain_port_audit.json', 'strict_ff_clock_audit.json',
    'resource_comparison.json']]
paths += [O.parent / n for n in [
    'run_physical_p3r0_launch02.py', 'launch02_derivation.json',
    'physical_p3_launch02_process.json', 'physical_p3_launch02.stdout.log',
    'physical_p3_launch02.stderr.log', 'prepare_launch02.py',
    'run_physical_p3r0.py', 'prepare_p3_runner.py',
    'p3_runner_derivation.json', 'physical_p3_runner_process.json',
    'physical_p3_runner.stdout.log', 'physical_p3_runner.stderr.log']]
paths += sorted(p for p in (O.parent / 'launcher_attempt01').rglob('*') if p.is_file())
data = {
    'scope': 'Frozen v5 normal P3R0 terminal evidence only; no hardware or new build.',
    'classification': 'route failure; no STA evidence',
    'actual_p_wait': ex['actual_p_wait'],
    'normal_wait_return': ex['normal_wait_return'],
    'physical_ended_utc': ex['ended_utc'],
    'unrouted': 648,
    'accepted_for_delivery': False,
    'physical_audit_not_run_reason': 'run_phase rejected actual exit1 before full timing audit; TR/FS/PR absent',
    'tr_fs_pr_absent': absent,
    'physical_options': inp['physical_options'],
    'period_constraint_ns': inp['period_ns'],
    'actual_fmax_and_slacks': None,
    'netlist_sha256': sha(vg),
    'source55_checks': checks,
    'source55': expected,
    'synthesis_actual_p_wait': synex['actual_p_wait'],
    'launcher_history': 'First Python donor-options assertion rejected before profile/vendor creation; immutable original and launch02 derivation retained. Launch02 is the actual vendor run.',
    'external_evidence': {p.relative_to(R).as_posix(): receipt(p) for p in paths},
}
(O / 'FINAL_STATUS.json').write_text(json.dumps(data, indent=2) + '\n')
manifest_paths = [O / 'seal.py', O / 'README.md', O / 'FINAL_STATUS.json']
manifest = {'scope': 'Only this terminal evidence directory; external raw artifacts are separately hash-bound in FINAL_STATUS.json. No compiled VVP/cache included.',
            'files': {p.name: receipt(p) for p in manifest_paths}}
(O / 'MANIFEST.json').write_text(json.dumps(manifest, indent=2) + '\n')
print(json.dumps({'final_status_sha256': sha(O / 'FINAL_STATUS.json'),
                  'manifest_sha256': sha(O / 'MANIFEST.json'),
                  'physical_exit_sha256': sha(V / 'physical_exit.json'),
                  'rpt_sha256': sha(pnr / 'acg720_ano_port.rpt.txt')}, indent=2))
