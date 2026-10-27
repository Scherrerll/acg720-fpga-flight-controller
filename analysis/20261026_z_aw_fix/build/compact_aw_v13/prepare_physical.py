"""Seal successful actual SYN result and prepare exact-VG physical scripts; no launch."""
from pathlib import Path
import ast, datetime, hashlib, json
O=Path(__file__).resolve().parent;R=O.parents[3];P=O.parent/'compact_aw_v12'
A=R/'out/z_aw_fix_20261026/compact_aw_v13/build_attempt_01';V=A/'verification'
read=lambda p:json.loads(p.read_text(encoding='utf8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
runner=read(O/'runner_exit.json');vendor=read(V/'synthesis_exit.json');summary=read(V/'synthesis_summary.json')
assert runner['normal_wait_return'] and vendor['normal_wait_return']
assert runner['actual_p_wait']==vendor['actual_p_wait']==summary['actual_p_wait']==0 and summary['passed']
vg=summary['netlist_sha256'];assert sha(A/'source/impl/gwsynthesis/acg720_ano_port.vg')==vg
freeze=read(O/'source_freeze.json');assert summary['source_sha256']==freeze['source55']
for name in ['mapped_audit.json','gain_port_audit.json','strict_ff_clock_audit.json']:
    assert read(V/name)['passed'] and sha(V/name)==summary[name.replace('.json','_sha256')]
assert read(V/'strict_ff_clock_audit.json')['all_FF_CLK50']
assert not (O/'SYNTHESIS_RESULT.json').exists()
files=['run_physical.py','seal_terminal.py','independent_raw_review.py','physical_snapshot.py','launch_physical_hidden.py']
for name in files:
    target=O/name;assert not target.exists()
    text=(P/name).read_text()
    text=text.replace('v12','__CURRENT__').replace('v11','v12').replace('__CURRENT__','v13')
    prior='f18ac77212a4b17ded9c5a6025a034dda91f8af8d13ca77bbf12caaa033eb0c1'
    if name in ['run_physical.py','seal_terminal.py','independent_raw_review.py']:
        assert text.count(prior)==1;text=text.replace(prior,vg)
    ast.parse(text);target.write_text(text,encoding='utf8')
result={'sealed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'passed_SYN_only':True,
    'vendor_actual_wait':vendor['actual_p_wait'],'runner_actual_wait':runner['actual_p_wait'],
    'source55':freeze['source55'],'netlist_sha256':vg,'resources':summary['resources'],
    'physical_scripts':{n:sha(O/n) for n in files},'physical_prepared_not_started':['physical_p2r0_01','physical_p3r0_01'],
    'scope':'Elaboration/SYN and mapped clock/radio/gain/18port gates only; no complete-route or hardware qualification.'}
(O/'SYNTHESIS_RESULT.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
print(json.dumps({'SYN_only_pass':True,'vg_sha256':vg,'resources':summary['resources'],
                  'physical_prepared_not_started':True},indent=2))
