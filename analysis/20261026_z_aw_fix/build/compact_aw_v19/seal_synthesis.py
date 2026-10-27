"""Seal actual completed v19 SYN_ONLY evidence; never infer exits from artifacts."""
from pathlib import Path
import datetime,hashlib,json
O=Path(__file__).resolve().parent;R=O.parents[3];A=R/'out/z_aw_fix_20261026/compact_aw_v19/build_attempt_01';V=A/'verification'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf8'))
from validation_contract import verify_contract
assert verify_contract(check_proof=True)['passed']
root=read(O/'runner_exit.json');vendor=read(V/'synthesis_exit.json');audit=read(V/'audit_exit.json');summary=read(V/'synthesis_summary.json')
assert root['normal_wait_return'] and vendor['normal_wait_return'] and audit['normal_wait_return']
assert root['actual_p_wait']==vendor['actual_p_wait']==audit['actual_p_wait']==0 and summary['passed']
for name,key in [('synthesis_exit.json','synthesis_exit_sha256'),('mapped_audit.json','mapped_audit_sha256'),('gain_port_audit.json','gain_port_audit_sha256'),('strict_ff_clock_audit.json','strict_ff_clock_audit_sha256')]:assert sha(V/name)==summary[key]
expected=read(O/'source_freeze.json')['source55'];assert summary['source_sha256']==expected
assert {n:sha(A/'source'/n) for n in expected}==expected
manifest=A/'synthesis_freeze_manifest_final.json';assert not manifest.exists() and not (A/'source/impl/pnr').exists()
items={}
for p in sorted(A.rglob('*')):
    if not p.is_file():continue
    if 'tmp' in p.relative_to(A).parts:continue
    assert not p.is_symlink() and p.resolve().is_relative_to(A)
    assert not p.name.lower().startswith('.env') and not p.name.lower().endswith('.env') and '.env' not in [s.lower() for s in p.suffixes]
    items[p.relative_to(A).as_posix()]={'sha256':sha(p),'bytes':p.stat().st_size}
manifest.write_text(json.dumps({'sealed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'scope':'Actual v19 successful SYN_ONLY plus strict mapped audit, temporary compiler scratch excluded; no physical qualification.',
    'source_sha256':expected,'artifacts':items,'runner_actual_wait':root['actual_p_wait'],'vendor_actual_wait':vendor['actual_p_wait'],
    'audit_actual_wait':audit['actual_p_wait'],'root_exit_sha256':sha(O/'runner_exit.json')},indent=2)+'\n',encoding='utf8')
(O/'SYNTHESIS_RESULT.json').write_text(json.dumps({'passed_SYN_only':True,'source55':expected,'netlist_sha256':summary['netlist_sha256'],
    'vendor_actual_wait':vendor['actual_p_wait'],'runner_actual_wait':root['actual_p_wait'],'audit_actual_wait':audit['actual_p_wait'],
    'synthesis_summary_sha256':sha(V/'synthesis_summary.json'),'synthesis_freeze_sha256':sha(manifest),'PNR_started':False},indent=2)+'\n',encoding='utf8')
print(json.dumps({'sealed':True,'vendor_actual_wait':0,'runner_actual_wait':0,'audit_actual_wait':0,'VG':summary['netlist_sha256'],'PNR_started':False}))
