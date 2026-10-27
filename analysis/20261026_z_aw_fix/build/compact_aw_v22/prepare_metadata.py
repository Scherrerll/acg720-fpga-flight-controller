"""Prepare local SYN_ONLY wrappers and rebind unchanged parent components; no vendor."""
from pathlib import Path
import datetime,hashlib,json
O=Path(__file__).resolve().parent;R=O.parents[3];P=O.parent/'compact_aw_v20'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf8'))
write=lambda p,j:p.write_text(json.dumps(j,indent=2)+'\n',encoding='utf8')
f=read(O/'source_freeze.json');expected=f['source55'];parent=read(P/'COMPONENT_REUSE_BINDING.json')
assert parent['passed'] and len(parent['bound_inputs'])==563
bound=dict(parent['bound_inputs'])
assert {p:sha(Path(p)) for p in bound}==bound
for name in ['source_freeze.json','SYNTHESIS_RESULT.json','PROOF_BINDING.json','COMPONENT_REUSE_BINDING.json','REUSED_BINDINGS_RECHECK.json','validation_contract.py']:
 bound[str(P/name)]=sha(P/name)
deps={'AZ':parent['AZ']['exact_compiled_source_dependencies'],'VY':parent['VY']['exact_compiled_source_dependencies'],'core_FSM':parent['reused_core_FSM']['exact_core_dependencies']}
deps['unchanged_controller_helpers']={n:h for n,h in parent['six_controller_dependencies'].items() if n!='position/mtf_xyz_hold_control.v'}
for group,items in deps.items():
 for n,h in items.items():assert expected[n]==h,(group,n)
assert expected['position/mtf_xyz_hold_control.v']!=parent['six_controller_dependencies']['position/mtf_xyz_hold_control.v']
write(O/'COMPONENT_REUSE_BINDING.json',{'passed':True,'verified_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source55':expected,'parent_binding_path':str(P/'COMPONENT_REUSE_BINDING.json'),'parent_binding_sha256':sha(P/'COMPONENT_REUSE_BINDING.json'),'parent_context_input_count':563,'bound_inputs':bound,'unchanged_dependency_sets':deps,'AZ':parent['AZ'],'VY':parent['VY'],'reused_core_FSM':parent['reused_core_FSM'],'ground_current_inputs_rehashed':43,'ground_verification_sha256':parent['ground_verification_sha256'],'new_controller_requires_fresh_proof':True,'old_six_controller_hashes_claimed_current':False,'historical_controller_evidence_is_context_only':{'six_dependencies':parent['six_controller_dependencies'],'controller_root_path':parent['controller_root_path'],'controller_results_path':parent['controller_results_path']},'scope':'Rehashed all563 old context inputs, including historical controller evidence, without claiming its changed controller bytes current. AZ/VY/core-FSM exact compiled dependencies and five unchanged controller helpers remain exact. Current controller is proved freshly in v22 five/boundary/contention and actual-function alias tests. Ground43 unchanged; no ground rerun or whole parent source identity claimed.'})
for name in ['run_synthesis.py','audit_synthesis_only.py','seal_synthesis.py','launch_synthesis_hidden.py']:
 assert not (O/name).exists();s=(P/name).read_text(encoding='utf8').replace('compact_aw_v20','compact_aw_v22').replace('v20','v22')
 if name=='run_synthesis.py':
  s=s.replace("O/'SOURCE_EQUIVALENCE_BASIS.json',O/'SOURCE_COMPOSITION.json'","O/'SOURCE_CHANGES.json',O/'FIXTURE_ADAPTATIONS.json'")
  s=s.replace("'resource_comparison_sha256':sha(V/'resource_comparison.json'),'audit_actual_p_wait'","'resource_comparison_sha256':sha(V/'resource_comparison.json'),'local_hint_effect_audit_sha256':sha(V/'local_hint_effect_audit.json'),'audit_actual_p_wait'")
 if name=='audit_synthesis_only.py':
  key="    helper.check_sources(expected)\n    write('native_synthesis_audit.json'"
  insertion="""    # Actual resource measurement against the sealed v20 parent; no predicted DSP or timing result.
    parent_xml=R/'out/z_aw_fix_20261026/compact_aw_v20/build_attempt_01/source/impl/gwsynthesis/acg720_ano_port_syn_rsc.xml'
    parent_vg=parent_xml.with_name('acg720_ano_port.vg')
    assert sha(parent_vg)==read(O.parent/'compact_aw_v20/SYNTHESIS_RESULT.json')['netlist_sha256']
    parent_resources=auditor.resources(parent_xml)
    measured={n:{'sealed_v20':parent_resources[n],'v22_local_function_result_hint':new[n],
        'delta':{k:new[n].get(k,0)-parent_resources[n].get(k,0) for k in new[n].keys()|parent_resources[n].keys()}} for n in names}
    write('local_hint_effect_audit.json',{'passed_measurement':True,'source55':expected,
        'new_local_hint':'wire signed [31:0] quantized_climb_logic_q16 /* synthesis syn_dspstyle="logic" */;',
        'mathematics_changed':False,'DSP_reduction_required_for_gate':False,
        'scope':'Measure actual parent/current mapped resource counts. An unchanged DSP count is a valid negative experiment; strict source/clock/gain/port gates still apply. No physical timing claim.',
        'resources':measured,'parent_xml_sha256':sha(parent_xml),'current_xml_sha256':sha(current),
        'parent_vg_sha256':sha(parent_vg),'current_vg_sha256':sha(vg)})
    helper.check_sources(expected)
    write('native_synthesis_audit.json'"""
  assert s.count(key)==1;s=s.replace(key,insertion)
  s=s.replace("'resource_comparison_sha256':sha(V/'resource_comparison.json'),","'resource_comparison_sha256':sha(V/'resource_comparison.json'),'local_hint_effect_audit_sha256':sha(V/'local_hint_effect_audit.json'),")
 if name=='seal_synthesis.py':
  s=s.replace("('strict_ff_clock_audit.json','strict_ff_clock_audit_sha256')]","('strict_ff_clock_audit.json','strict_ff_clock_audit_sha256'),('resource_comparison.json','resource_comparison_sha256'),('local_hint_effect_audit.json','local_hint_effect_audit_sha256')]")
  s=s.replace("'PNR_started':False},indent=2)","'local_hint_effect_audit_sha256':sha(V/'local_hint_effect_audit.json'),'PNR_started':False},indent=2)")
 (O/name).write_text(s,encoding='utf8',newline='\n')
for p in [O/n for n in ['run_synthesis.py','audit_synthesis_only.py','seal_synthesis.py','launch_synthesis_hidden.py','validation_contract.py']]:compile(p.read_text(),str(p),'exec')
print(json.dumps({'prepared_without_vendor':True,'rehashed_parent_context_inputs':563,'guard_binding_sha256':sha(O/'COMPONENT_REUSE_BINDING.json')}))
