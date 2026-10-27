"""Seal actual completed v22 SYN_ONLY evidence; never infer exits from artifacts."""
from pathlib import Path
import datetime,hashlib,json,sys
O=Path(__file__).resolve().parent;R=O.parents[3];A=R/'out/z_aw_fix_20261026/compact_aw_v22/build_attempt_01';V=A/'verification'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf8'))
from validation_contract import verify_contract,verify_syn_review
assert verify_contract(check_proof=True)['passed']
verify_syn_review()
root=read(O/'runner_exit.json');vendor=read(V/'synthesis_exit.json');audit=read(V/'audit_exit.json');summary=read(V/'synthesis_summary.json')
assert root['normal_wait_return'] and vendor['normal_wait_return'] and audit['normal_wait_return']
assert root['actual_p_wait']==vendor['actual_p_wait']==audit['actual_p_wait']==0 and summary['passed']
assert root['command']==[sys.executable,'-B','-X','utf8',str(O/'run_synthesis.py')]
assert root['runner_sha256']==sha(O/'run_synthesis.py') and root['supervisor_sha256']==sha(O/'launch_synthesis_hidden.py')
for stream in ['stdout','stderr']:assert sha(O/f'runner.{stream}.log')==root[f'{stream}_sha256']
for phase,j in [('synthesis',vendor),('audit',audit)]:
    assert j['stage']==phase and j['parent_pid']==root['pid'] and Path(j['cwd'])==A/'source'
    assert Path(j['log'])==V/f'{phase}.log' and sha(V/f'{phase}.log')==j['log_sha256']
assert audit['command']==[sys.executable,'-B','-X','utf8',str(O/'audit_synthesis_only.py')]
assert vendor['command'][1:]==[str(A/'synth_only.tcl')]
assert 'SYNTHESIS_COMMAND_RETURNED_EOF' in (V/'synthesis.log').read_text(encoding='utf8',errors='replace')
for name,key in [('synthesis_exit.json','synthesis_exit_sha256'),('mapped_audit.json','mapped_audit_sha256'),('gain_port_audit.json','gain_port_audit_sha256'),('strict_ff_clock_audit.json','strict_ff_clock_audit_sha256'),('resource_comparison.json','resource_comparison_sha256'),('local_hint_effect_audit.json','local_hint_effect_audit_sha256')]:assert sha(V/name)==summary[key]
expected=read(O/'source_freeze.json')['source55'];assert summary['source_sha256']==expected
assert {n:sha(A/'source'/n) for n in expected}==expected
vg=A/'source/impl/gwsynthesis/acg720_ano_port.vg';native=read(V/'native_synthesis_audit.json')
assert native['passed'] and native['source55']==expected and sha(vg)==summary['netlist_sha256']==native['netlist_sha256']
assert read(V/'strict_ff_clock_audit.json')['passed'] and read(V/'strict_ff_clock_audit.json')['all_FF_CLK50']
assert read(V/'local_hint_effect_audit.json')['passed_measurement'] and read(V/'local_hint_effect_audit.json')['source55']==expected
assert read(V/'local_hint_effect_audit.json')['current_vg_sha256']==sha(vg)
inputs=read(V/'build_input.json');assert inputs['source_sha256']==expected
for path,h in {**inputs['bound_inputs'],**inputs['tools']}.items():assert sha(Path(path))==h,path
syn_input=read(V/'synthesis_input.json');assert syn_input['source_sha256']==expected and syn_input['execution_tcl_sha256']==sha(A/'synth_only.tcl')
manifest=A/'synthesis_freeze_manifest_final.json';assert not manifest.exists() and not (A/'source/impl/pnr').exists()
items={}
for p in sorted(A.rglob('*')):
    if not p.is_file():continue
    if 'tmp' in p.relative_to(A).parts:continue
    assert not p.is_symlink() and p.resolve().is_relative_to(A)
    assert not p.name.lower().startswith('.env') and not p.name.lower().endswith('.env') and '.env' not in [s.lower() for s in p.suffixes]
    items[p.relative_to(A).as_posix()]={'sha256':sha(p),'bytes':p.stat().st_size}
manifest.write_text(json.dumps({'sealed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'scope':'Actual v22 successful SYN_ONLY plus strict mapped audit, temporary compiler scratch excluded; no physical qualification.',
    'source_sha256':expected,'artifacts':items,'runner_actual_wait':root['actual_p_wait'],'vendor_actual_wait':vendor['actual_p_wait'],
    'audit_actual_wait':audit['actual_p_wait'],'root_exit_sha256':sha(O/'runner_exit.json')},indent=2)+'\n',encoding='utf8')
(O/'SYNTHESIS_RESULT.json').write_text(json.dumps({'passed_SYN_only':True,'source55':expected,'netlist_sha256':summary['netlist_sha256'],
    'vendor_actual_wait':vendor['actual_p_wait'],'runner_actual_wait':root['actual_p_wait'],'audit_actual_wait':audit['actual_p_wait'],
    'synthesis_summary_sha256':sha(V/'synthesis_summary.json'),'synthesis_freeze_sha256':sha(manifest),'local_hint_effect_audit_sha256':sha(V/'local_hint_effect_audit.json'),'PNR_started':False},indent=2)+'\n',encoding='utf8')
print(json.dumps({'sealed':True,'vendor_actual_wait':0,'runner_actual_wait':0,'audit_actual_wait':0,'VG':summary['netlist_sha256'],'PNR_started':False}))
