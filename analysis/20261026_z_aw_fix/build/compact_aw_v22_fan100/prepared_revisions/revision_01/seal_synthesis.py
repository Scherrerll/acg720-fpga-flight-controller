"""Seal only actual successful vendor/audit/root0 receipts; failures remain intact."""
from pathlib import Path
import datetime,hashlib,json,sys
sys.dont_write_bytecode=True
O=Path(__file__).resolve().parent;R=O.parents[3];ROOT=R/'out/z_aw_fix_20261026/compact_aw_v22_fan100'
A=ROOT/'build_attempt_01';V=A/'verification';S=A/'source'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf8'))
from input_contract import validate,review_gate
from effective_recipe import make_recipe
base=validate();review_gate();expected=base['source55']
root=read(O/'runner_exit.json');vendor=read(V/'synthesis_exit.json');audit=read(V/'audit_exit.json');summary=read(V/'synthesis_summary.json')
for j in [root,vendor,audit]:assert isinstance(j,dict) and j.get('normal_wait_return') is True and type(j.get('actual_p_wait')) is int and j['actual_p_wait']==0
assert root['command']==[sys.executable,'-B','-X','utf8',str(O/'run_synthesis.py')]
assert root['runner_sha256']==sha(O/'run_synthesis.py') and root['supervisor_sha256']==sha(O/'launch_synthesis_hidden.py')
for stream in ['stdout','stderr']:assert sha(O/f'runner.{stream}.log')==root[f'{stream}_sha256']
for phase,j in [('synthesis',vendor),('audit',audit)]:
    assert j['stage']==phase and j['parent_pid']==root['pid'] and Path(j['cwd'])==S
    assert Path(j['log'])==V/f'{phase}.log' and sha(V/f'{phase}.log')==j['log_sha256']
assert audit['command']==[sys.executable,'-B','-X','utf8',str(O/'audit_synthesis_only.py')]
assert vendor['command'][1:]==[str(A/'synth_only.tcl')]
assert 'SYNTHESIS_COMMAND_RETURNED_EOF' in (V/'synthesis.log').read_text(errors='replace')
assert summary['passed'] is True and summary['source_sha256']==expected and summary['actual_vendor_wait']==summary['actual_audit_wait']==0
for n,h in summary['artifacts_sha256'].items():assert sha(V/n)==h
native=read(V/'native_synthesis_audit.json');vg=S/'impl/gwsynthesis/acg720_ano_port.vg'
assert native['passed'] is True and native['source55']==expected and sha(vg)==native['netlist_sha256']==summary['netlist_sha256']
for n,h in native['artifacts_sha256'].items():assert sha(V/n)==h
assert read(V/'strict_ff_clock_audit.json')['all_FF_CLK50'] is True
assert {n:sha(S/n) for n in expected}==expected
assert (A/'synth_only.tcl').read_text()==make_recipe(S/'build.tcl')
inputs=read(V/'build_input.json');assert inputs['source_sha256']==expected
for p,h in {**inputs['bound_inputs'],**inputs['tools']}.items():assert sha(Path(p))==h,p
assert not (S/'impl/pnr').exists() and not (ROOT/'canonical').exists()
manifest=A/'synthesis_freeze_manifest_final.json';assert not manifest.exists() and not (O/'SYNTHESIS_RESULT.json').exists()
items={}
for p in sorted(A.rglob('*')):
    if not p.is_file() or 'tmp' in p.relative_to(A).parts:continue
    assert not p.is_symlink() and p.resolve().is_relative_to(A.resolve()) and '.env' not in p.name.lower()
    items[p.relative_to(A).as_posix()]={'sha256':sha(p),'bytes':p.stat().st_size}
manifest.write_text(json.dumps({'sealed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_sha256':expected,'canonical_source_root':inputs['canonical_override'],'standard_source_proof_origin':inputs['standard_source_proof_origin'],'artifacts':items,'vendor_actual_wait':vendor['actual_p_wait'],'audit_actual_wait':audit['actual_p_wait'],'runner_actual_wait':root['actual_p_wait'],'root_exit_sha256':sha(O/'runner_exit.json'),'scope':'Same whole55 STD22 source with only effective SYN max_fanout100. No physical qualification.'},indent=2)+'\n',encoding='utf8')
(O/'SYNTHESIS_RESULT.json').write_text(json.dumps({'passed_SYN_only':True,'source55':expected,'parent_VG_sha256':base['VG_sha256'],'netlist_sha256':sha(vg),'vendor_actual_wait':vendor['actual_p_wait'],'audit_actual_wait':audit['actual_p_wait'],'runner_actual_wait':root['actual_p_wait'],'synthesis_summary_sha256':sha(V/'synthesis_summary.json'),'synthesis_freeze_sha256':sha(manifest),'effective_option_delta':{'max_fanout':{'from':200,'to':100}},'source_build_tcl_unchanged':True,'PNR_started':False},indent=2)+'\n',encoding='utf8')
print(json.dumps({'sealed_SYN_only':True,'actual_vendor_audit_root_waits':[0,0,0],'VG':sha(vg),'PNR_started':False}))
