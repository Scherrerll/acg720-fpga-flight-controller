"""Freeze the completed v4 P4R0 route failure; never run a vendor tool."""
from pathlib import Path
import hashlib
import json
import shutil
from datetime import datetime, timezone

REPO = Path(__file__).resolve().parents[4]
ATTEMPT = REPO / 'out/z_aw_fix_20261026/compact_aw_v4/physical_p4r0_01'
VERIFY = ATTEMPT / 'verification'
SOURCE = ATTEMPT / 'source'
PROFILE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, obj):
    assert not path.exists(), f'Frozen receipt already exists: {path}'
    path.write_text(json.dumps(obj, indent=2) + '\n', encoding='utf8')


def main():
    inputs = json.loads((VERIFY / 'physical_input.json').read_text())
    ended = json.loads((VERIFY / 'physical_exit.json').read_text())
    expected = inputs['source_sha256']
    assert len(expected) == 55
    canonical = Path(inputs['canonical_source'])
    assert all(sha(canonical / rel) == sha(SOURCE / rel) == digest
               for rel, digest in expected.items())
    assert {p.relative_to(canonical).as_posix() for p in canonical.rglob('*') if p.is_file()} == set(expected)
    donor = Path(inputs['donor_directory'])
    assert all(sha(donor / rel) == digest for rel, digest in inputs['donor_evidence_sha256'].items())
    vg = SOURCE / 'impl/gwsynthesis/acg720_ano_port.vg'
    assert sha(vg) == inputs['donor_netlist_sha256']
    assert sha(ATTEMPT / 'physical.tcl') == inputs['tcl_sha256']
    assert sha(SOURCE / 'physical.gprj') == inputs['project_sha256']
    assert inputs['physical_options'] == dict(place=4, route=0, map_option=2, replicate_resources=0)
    tcl = (ATTEMPT / 'physical.tcl').read_text()
    for option in ('set_option -place_option 4', 'set_option -route_option 0',
                   'set_option -map_option 2', 'set_option -replicate_resources 0',
                   'set_option -timing_driven 1', 'set_option -user_code 0000B0B4'):
        assert tcl.splitlines().count(option) == 1
    assert '-inc_pnr' not in tcl
    assert 'create_clock -name clk50 -period 20.000' in (SOURCE / 'acg720_ano_port.sdc').read_text()
    for tool, digest in inputs['tools'].items():
        assert sha(Path(tool)) == digest
    runner = PROFILE / 'run_physical_p4r0.py'
    gate = REPO / 'firmware/B0B4/build_candidate.py'
    assert sha(runner) == inputs['helper_sha256']
    assert sha(gate) == inputs['original_runner_sha256']
    log = (VERIFY / 'physical.log').read_text()
    report = (SOURCE / 'impl/pnr/acg720_ano_port.rpt.txt').read_text()
    assert ended['actual_p_wait'] == 1 and ended['normal_wait_return'] is True
    assert sha(VERIFY / 'physical.log') == ended['log_sha256']
    assert 'DesRoute failed' in log
    assert 'There are total 7273 unrouted nets' in log and 'There are total 7273 unrouted nets' in report
    assert 'Skip synthesis, because there is only one netlist file' in log
    assert not list((SOURCE / 'impl/pnr').glob('*.tr'))
    assert not list((SOURCE / 'impl/pnr').glob('*.fs'))
    assert '45798(36061 LUT, 9737 ALU, 0 ROM16)' in report
    for text in ('27766/60780', '27881/29952', '59.5/118', '2/118', '18/297'):
        assert text in report
    for original, name in ((runner, 'executed_physical_runner.py'), (gate, 'executed_gate_provider.py')):
        dest = VERIFY / name
        assert not dest.exists()
        shutil.copy2(original, dest)
        assert sha(dest) == sha(original)
    result = dict(status='V4_MAP2_P4R0_ROUTE_FAILED_7273_NOT_SELECTED',
                  recorded_utc=datetime.now(timezone.utc).isoformat(),
                  actual_physical_p_wait=1, normal_wait_return=True, normal_completion=False,
                  source55_unchanged_at_freeze=True, source_sha256=expected,
                  donor_evidence_unchanged=True, netlist_sha256=sha(vg),
                  physical_options=inputs['physical_options'], timing_driven=1,
                  actual_period_constraint_ns=20, unrouted_nets=7273,
                  TR_generated=False, FS_generated=False, STA=None,
                  resource_usage=dict(logic=dict(used=45798, available=59904, LUT=36061, ALU=9737),
                                      FF=27766, CLS=dict(used=27881, available=29952),
                                      DSP=dict(used=59.5, available=118),
                                      BSRAM=dict(used=2, available=118), IO_ports=18),
                  route_phase1_elapsed='0h 56m 18s', total_elapsed='1h 1m 45s',
                  failure_scope='Actual route failure. No TR/FS, STA worst path, physical qualification, or delivery claim. Resource usage does not establish a unique failed net/control set/congestion cause.',
                  helper_sha256=inputs['helper_sha256'], original_gate_sha256=inputs['original_runner_sha256'],
                  freeze_script_sha256=sha(Path(__file__)))
    write(VERIFY / 'physical_failure_summary.json', result)
    artifacts = {}
    for path in sorted(ATTEMPT.rglob('*')):
        if path.is_file() and not path.is_relative_to(VERIFY / 'tmp'):
            artifacts[path.relative_to(ATTEMPT).as_posix()] = dict(sha256=sha(path), bytes=path.stat().st_size)
    manifest = dict(**result, self_reference='This manifest intentionally excludes itself.',
                    artifact_count=len(artifacts), artifact_bytes=sum(x['bytes'] for x in artifacts.values()),
                    artifacts=artifacts)
    frozen = ATTEMPT / 'failure_freeze_manifest.json'
    write(frozen, manifest)
    write(PROFILE / 'physical_failure.json', dict(**result, failure_manifest=str(frozen),
          failure_manifest_sha256=sha(frozen), artifact_count=len(artifacts),
          artifact_bytes=manifest['artifact_bytes']))
    print(json.dumps(dict(failure_manifest_sha256=sha(frozen),
                         report_sha256=sha(PROFILE / 'physical_failure.json'),
                         artifact_count=len(artifacts), artifact_bytes=manifest['artifact_bytes'])))


if __name__ == '__main__':
    main()
