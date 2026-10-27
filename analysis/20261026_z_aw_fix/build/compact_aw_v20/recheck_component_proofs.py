"""Independently rehash actual AZ/VY/core/controller evidence for named v20 components."""
from pathlib import Path
import datetime,hashlib,json,re
O=Path(__file__).resolve().parent;R=O.parents[3];B=O.parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf8'))
norm=lambda s:s.replace('\r\n','\n')
freeze=read(O/'source_freeze.json');expected=freeze['source55'];C=Path(freeze['source_root']);composition=read(O/'SOURCE_COMPOSITION.json')
assert {n:sha(C/n) for n in expected}==expected and len(expected)==55
dest=O/'COMPONENT_REUSE_BINDING.json';assert not dest.exists()
bound={}
def bind(p,h=None):
    p=Path(p);assert not p.name.lower().startswith('.env') and not p.name.lower().endswith('.env') and '.env' not in [s.lower() for s in p.suffixes]
    actual=sha(p);assert h is None or h==actual,(p,h,actual);bound[str(p)]=actual;return actual
def record_wait(p,key='actual_p_wait',code=0,log=None):
    j=read(p);bind(p);assert j['normal_wait_return'] and j[key]==code and not j.get('terminated_after_timeout'),p
    if log is not None:bind(log,j['log_sha256'])
    else:
        prefix=p.name.replace('_exit.json','')
        for stream in ['stdout','stderr']:
            if f'{stream}_sha256' in j:bind(p.parent/f'{prefix}.{stream}.log',j[f'{stream}_sha256'])
    return {'path':str(p),'sha256':sha(p),'actual_wait_field':key,'actual_wait':j[key],'normal_wait_return':True}
for v,p in composition['parents'].items():
    bind(p['freeze_path'],p['freeze_sha256']);root=Path(p['root'])
    for n,h in p['source55'].items():bind(root/n,h)
for p in [Path(__file__),O/'source_freeze.json',O/'SOURCE_COMPOSITION.json',O/'SOURCE_EQUIVALENCE_BASIS.json',O/'source_review.md']:bind(p)

AZ=B/'compact_aw_v19/GUARD_REUSE_RECHECK.json';az=read(AZ);bind(AZ)
az_receipts=[]
for x in az['actual_producer_fusion_stages']:
    bind(x['receipt_path'],x['receipt_sha256']);bind(x['log_path'],x['log_sha256'])
    az_receipts.append(record_wait(Path(x['receipt_path']),log=Path(x['log_path'])))
for x in az['completion02_reuse_links']:
    bind(x['path'],x['sha256']);bind(x['receipt'],x['receipt_sha256']);bind(x['log'],x['log_sha256'])
az_roots={}
for name,x in az['roots'].items():
    p=Path(x['path']);bind(p,x['sha256']);j=read(p);assert j['actual_p_wait']==(1 if 'failed_root' in name else 0) and j['normal_wait_return']
    bind(x['runner_path'],x['runner_sha256'])
    for stream in ['stdout','stderr']:bind(p.parent/f'runner.{stream}.log',j[f'{stream}_sha256'])
    az_roots[name]={'path':str(p),'sha256':sha(p),'actual_p_wait':j['actual_p_wait']}
for v in ['v8','v9']:bind(az[f'{v}_results_path'],az[f'{v}_results_sha256']);assert read(Path(az[f'{v}_results_path']))['passed']
r8=read(Path(az['v8_results_path']));P8=B/'compact_aw_v8'
for v in ['v7','v8']:
    root=R/f'out/z_aw_fix_20261026/compact_aw_{v}/canonical/source'
    for n,h in r8['source55'][v].items():bind(root/n,h)
for folder in ['proofs','proofs_completion02']:
    inputs=P8/folder/'inputs.json';bind(inputs);assert read(inputs)['source55']==r8['source55']
    for name in ['adapter_tb.v','adapter_v7.v','fusion_tb.v','v7_height.v','v8_height.v']:bind(P8/folder/name)
assert (P8/'proofs/fusion_tb.v').read_bytes()==(P8/'proofs_completion02/fusion_tb.v').read_bytes()
for folder in ['proofs','proofs_completion02']:
    for v in ['v7','v8']:
        source=R/f'out/z_aw_fix_20261026/compact_aw_{v}/canonical/source/position/mtf_shared_height_fusion.v'
        assert norm((P8/folder/f'{v}_height.v').read_text(encoding='utf8'))==norm(source.read_text(encoding='utf8')).replace('module mtf_shared_height_fusion #(',f'module height_{v} #(',1)
    for name in ['adapter_tb.v','fusion_tb.v']:assert not re.search(r'\bforce\b', (P8/folder/name).read_text(encoding='utf8'))
bind(R/'analysis/20261026_z_aw_fix/numeric_guard_fusion/completion03/tb.v',r8['original_fusion_fixture_sha256'])
AZdeps=['position/pose_time_adapter.v','position/mtf_shared_height_fusion.v','nav_math_service.v','position/position_math.v']
for n in AZdeps:assert sha(C/n)==r8['source55']['v8'][n]

P18=B/'compact_aw_v18';VY=P18/'VY_BINDING.json';vy=read(VY);bind(VY)
VR=P18/'vy_proofs/RESULT.json';vyr=read(VR);bind(VR,vy['result_sha256']);assert vyr['passed'] and vyr['no_DUT_force_or_preload']
D=Path(vyr['attempt_directory']);assert D.resolve().is_relative_to((P18/'vy_proofs').resolve())
VI=D/'inputs.json';vi=read(VI);bind(VI,vyr['inputs_sha256']);assert vi['source55']==composition['parents']['v18']['source55'] and vi['no_DUT_force_or_preload']
for p,h in vi['bound_files'].items():bind(p,h)
root=Path(vyr['supervisor_exit_receipt']);bind(root,vyr['supervisor_exit_receipt_sha256']);vr=read(root)
assert vr['normal_wait_return'] and vr['actual_proof_supervisor_child_wait']==0
bind(P18/'supervise_vy_proofs.py',vr['supervisor_script_sha256']);bind(P18/'run_vy_proofs.py',vr['runner_sha256'])
for stream in ['stdout','stderr']:bind(P18/'vy_proofs'/f'{D.name}_supervisor.{stream}.log',vr[f'{stream}_sha256'])
vy_receipts=[]
for name in ['metric_compile','metric_vvp','uart_mode0_compile','uart_mode0_vvp','uart_mode1_compile','uart_mode1_vvp','geometry_compile','geometry_vvp']:
    vy_receipts.append(record_wait(D/f'{name}_exit.json',key='actual_child_p_wait'))
for rel,h in vyr['exit_receipts'].items():
    p=P18/'vy_proofs'/rel;bind(p,h);adapter=read(p);original=P18/'vy_proofs'/adapter['original_receipt'];bind(original,adapter['original_receipt_sha256'])
    assert adapter['schema_adapter_only'] and read(original)[adapter['original_actual_wait_field']]==adapter['actual_p_wait']==0
VYdeps=['sensor/mtf01p_reader.v','sensor/mtf_shared_geometry.v','sensor/mtf_native_geometry.v','nav_math_service.v','position/position_math.v']
for n in VYdeps:assert sha(C/n)==vi['source55'][n]
for n in ['metric_tb.v','uart_reader_tb.v','geometry_tb.v']:assert not re.search(r'\bforce\b', (D/n).read_text(encoding='utf8'))

fp=P18/'PROOF_BINDING.json';fsm=read(fp);bind(fp);assert fsm['passed'] and fsm['source55']==composition['parents']['v18']['source55']
FI=P18/'proofs/inputs.json';fi=read(FI);bind(FI,fsm['inputs_sha256'])
for p,h in fi['bound_files'].items():bind(p,h)
fsm_receipts=[record_wait(P18/'proofs'/f'{n}_exit.json') for n in ['fsm_compile','fsm_vvp']]
core=['core/ano_flight_state.v','core/flight_core.v','core/height_loss_fallback.v']
for n in core:assert sha(C/n)==fsm['source55'][n]
assert fsm['flight_state_miter']['no_DUT_force_or_preload']
bind(P18/'proofs/flight_state_miter.v');bind(P18/'proofs/legacy_ano_flight_state.v')
assert not re.search(r'\bforce\b',(P18/'proofs/flight_state_miter.v').read_text(encoding='utf8'))

P4=B/'v4_release_proofs';parent=read(P4/'RESULT.json');inputs=read(P4/'inputs.json');bind(P4/'RESULT.json');bind(P4/'inputs.json',parent['inputs_sha256'])
controller=Path(inputs['reused_controller_proofs']);cr=read(controller/'results.json');bind(controller/'results.json',inputs['reused_results_sha256'])
ce=read(controller/'runner_exit.json');bind(controller/'runner_exit.json');assert cr['passed'] and ce['normal_wait_return'] and ce['actual_p_wait']==0
six=inputs['exact_dependencies'];assert len(six)==6
for n,h in six.items():assert sha(C/n)==cr['source55'][n]==parent['source55'][n]==h
ground=R/'ground/B0B4/test_results/verification.json';g=read(ground);bind(ground,inputs['ground_verification_sha256']);assert g['result']=='PASS' and len(g['input_sha256'])==43
for name,h in g['input_sha256'].items():
    p=R/name;assert p.resolve().is_relative_to(R);bind(p,h)
for n,h in expected.items():assert sha(C/n)==h
result={'passed':True,'verified_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source55':expected,
    'scope':'Named component source and real receipt/log reuse only. Complete v20 source55 differs from both parent full source55 sets; shared top/nav require fresh tests. No vendor/physical/hardware claim.',
    'AZ':{'parent_binding_path':str(AZ),'parent_binding_sha256':sha(AZ),'exact_compiled_source_dependencies':{n:sha(C/n) for n in AZdeps},'actual_compile_sim_receipts':az_receipts,'roots_including_historical_failure1':az_roots,'coverage':{'producer':r8['adapter'],'fusion':r8['fusion']},'new_wrapper_is_not_parent_identity':True},
    'VY':{'parent_binding_path':str(VY),'parent_binding_sha256':sha(VY),'result_path':str(VR),'result_sha256':sha(VR),'exact_compiled_source_dependencies':{n:sha(C/n) for n in VYdeps},'actual_compile_sim_receipts':vy_receipts,'actual_root_receipt':str(root),'actual_root_wait_field':'actual_proof_supervisor_child_wait','actual_root_wait':vr['actual_proof_supervisor_child_wait'],'metric':vyr['metric_pass_lines'],'UART':vyr['uart_pass_lines'],'geometry':vyr['geometry_pass_lines']},
    'reused_core_FSM':{'parent_proof_path':str(fp),'parent_proof_sha256':sha(fp),'exact_core_dependencies':{n:sha(C/n) for n in core},'actual_compile_vvp_receipts':fsm_receipts,'testbench_sha256':sha(P18/'proofs/flight_state_miter.v'),'scope':'Only the actual complete core FSM miter is reused; no invented parent supervisor/root wait or parent top13 reuse is claimed.'},
    'six_controller_dependencies':six,'controller_results_path':str(controller/'results.json'),'controller_results_sha256':sha(controller/'results.json'),'controller_root_path':str(controller/'runner_exit.json'),'controller_actual_root_wait':ce['actual_p_wait'],
    'ground_verification_sha256':sha(ground),'ground_current_inputs_rehashed':43,'bound_inputs':bound,
    'limitations':{'AZ_fusion_timer_and_admission_accelerated':True,'component_no_private_force_or_preload':True,'fresh_top13_controlled_private_forces_required':True,'new_private_predicate_bits':2,'legacy_public_output_cycle_change':0,'no_full_source_parent_identity_claim':True}}
dest.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf8',newline='\n')
print(json.dumps({'component_reuse_passed':True,'AZ_compile_sim_receipts':len(az_receipts),'VY_compile_sim_receipts':len(vy_receipts),'core_FSM_real_receipts':len(fsm_receipts),'six_controller_dependencies':6,'ground_inputs':43,'bound_inputs':len(bound),'binding_sha256':sha(dest)}))
