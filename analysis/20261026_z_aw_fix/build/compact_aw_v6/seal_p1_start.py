"""Seal P1 startup separately; leave the first two-start manifest frozen."""
from pathlib import Path
import datetime,hashlib,json
O=Path(__file__).resolve().parent;R=O.parents[3];ROOT=R/'out/z_aw_fix_20261026/compact_aw_v6'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
old=O/'PHYSICAL_START_MANIFEST.json';old_sha='f0b8865a7d125703055ff58d8dffa91da273fba800b77a71eae461061d4eef55'
assert sha(old)==old_sha
manifest=O/'PHYSICAL_P1_START_MANIFEST.json';assert not manifest.exists()
expected=json.loads((O/'source_freeze.json').read_text())['source55'];label='physical_p1r0_01'
attempt=ROOT/label;verification=attempt/'verification';reports=O/label
assert {p:sha(attempt/'source'/p) for p in expected}==expected
VG='6b169818d5029c45e0a778d74d8d3e90e129caa430e93eb3778661f18fa7cb99'
assert sha(attempt/'source/impl/gwsynthesis/acg720_ano_port.vg')==VG
runner=json.loads((reports/'runner_process.json').read_text());physical=json.loads((verification/'physical_process.json').read_text())
names=[verification/n for n in ['donor_evidence_binding.json','project_serialization_check.json','build_input.json','physical_input.json','physical_process.json']]
names += [reports/n for n in ['launcher_process.json','runner_process.json','runner_derivation.json']]
names += [attempt/'physical.tcl',attempt/'source/physical.gprj',O/'run_physical_p1r0.py',O/'launch_physical_p1_hidden.py']
result=dict(sealed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    scope='Exactly one last root-authorized extra v6 physical P1/R0 trial; running at seal; actual terminal receipts remain required; no hardware action.',
    previous_two_start_manifest_sha256=old_sha,source55=expected,source55_unchanged_at_seal=True,vg_sha256=VG,
    supervisor_pid=runner['supervisor_pid'],runner_pid=runner['pid'],vendor_pid=physical['pid'],
    physical_options=dict(place=1,route=0,map_option=2,replicate_resources=0,timing_driven=1),
    artifacts={str(p.relative_to(R)):{'sha256':sha(p),'bytes':p.stat().st_size} for p in names},
    vendor_exit_receipt=str(verification/'physical_exit.json'),runner_exit_receipt=str(reports/'runner_exit.json'))
manifest.write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
assert sha(old)==old_sha
print(json.dumps(dict(manifest=str(manifest),sha256=sha(manifest)),indent=2))
