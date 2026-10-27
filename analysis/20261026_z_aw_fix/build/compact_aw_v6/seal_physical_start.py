"""Seal read-only launch provenance for the two authorized v6 PNR trials."""
from pathlib import Path
import datetime,hashlib,json
O=Path(__file__).resolve().parent;R=O.parents[3];ROOT=R/'out/z_aw_fix_20261026/compact_aw_v6'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
freeze=json.loads((O/'source_freeze.json').read_text());expected=freeze['source55']
VG='6b169818d5029c45e0a778d74d8d3e90e129caa430e93eb3778661f18fa7cb99'
assert {p:sha(ROOT/'canonical/source'/p) for p in expected}==expected
assert sha(R/'firmware/B0B4/build_candidate.py')=='abb5246c203b73c111f80bc91f8db6c8220463f7d4c5cf48dbfe2167ef49db84'
manifest=O/'PHYSICAL_START_MANIFEST.json';assert not manifest.exists()
trials={}
for place in [3,2]:
    label=f'physical_p{place}r0_01';reports=O/label;attempt=ROOT/label;verification=attempt/'verification'
    assert {p:sha(attempt/'source'/p) for p in expected}==expected
    assert sha(attempt/'source/impl/gwsynthesis/acg720_ano_port.vg')==VG
    names=['donor_evidence_binding.json','project_serialization_check.json','build_input.json','physical_input.json','physical_process.json']
    names=[verification/n for n in names]+[reports/'launcher_process.json',reports/'runner_process.json',attempt/'physical.tcl',attempt/'source/physical.gprj']
    runner=json.loads((reports/'runner_process.json').read_text());physical=json.loads((verification/'physical_process.json').read_text())
    trials[label]=dict(scope='Physical-only PNR running at launch seal; no terminal success/STA claim.',
        supervisor_pid=runner['supervisor_pid'],runner_pid=runner['pid'],vendor_pid=physical['pid'],
        source55=expected,source55_unchanged_at_seal=True,vg_sha256=VG,
        physical_options=dict(place=place,route=0,map_option=2,replicate_resources=0,timing_driven=1),
        artifacts={str(p.relative_to(R)):{'sha256':sha(p),'bytes':p.stat().st_size} for p in names},
        vendor_exit_receipt=str(verification/'physical_exit.json'),runner_exit_receipt=str(reports/'runner_exit.json'))
result=dict(sealed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    scope='Exactly two root-authorized fresh v6 physical trials; actual terminal receipts remain required. No hardware action.',
    source_freeze_sha256=sha(O/'source_freeze.json'),synthesis_summary_sha256=sha(ROOT/'build_attempt_01/verification/synthesis_summary.json'),
    runner_sha256=sha(O/'run_physical.py'),supervisor_sha256=sha(O/'launch_physical_hidden.py'),trials=trials)
manifest.write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
print(json.dumps({'manifest':str(manifest),'sha256':sha(manifest),'profiles':list(trials)},indent=2))
