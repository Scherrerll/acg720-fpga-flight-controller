"""Independent read-only v20 review; all writes stay in this review directory."""
from pathlib import Path
import ast,datetime,difflib,hashlib,importlib.util,json,re,sys
sys.dont_write_bytecode=True
D=Path(__file__).resolve().parent;R=D.parents[2];O=R/'analysis/20261026_z_aw_fix/build/compact_aw_v20'
seen={}
def safe(path):
    p=Path(path)
    for part in p.parts:
        name=part.lower().rstrip(' .')
        assert not name.startswith('.env') and not name.endswith('.env') and '.env' not in [x.lower() for x in Path(name).suffixes]
    for q in [p,*p.parents]:assert not q.is_symlink() and not (hasattr(q,'is_junction') and q.is_junction())
    return p
def sha(path):
    p=safe(path);value=hashlib.sha256(p.read_bytes()).hexdigest()
    assert str(p) not in seen or seen[str(p)]==value,('Evidence changed during review',str(p))
    seen[str(p)]=value;return value
def read(path):sha(path);return json.loads(safe(path).read_text(encoding='utf8'))
def check(path,digest):assert sha(path)==digest,(str(path),digest)
def wait(path,key='actual_p_wait',normal='normal_wait_return',code=0,digest=None):
    if digest:check(path,digest)
    j=read(path);assert j[key]==code and j[normal] is True and not j.get('terminated_after_timeout')
    name=Path(path).name.removesuffix('_exit.json').removesuffix('.exit.json')
    for channel in ['stdout','stderr']:
        if channel+'_sha256' in j:check(Path(path).parent/(name+'.'+channel+'.log'),j[channel+'_sha256'])
    if 'log_sha256' in j and 'log' in j:check(j['log'],j['log_sha256'])
    return j
f=read(O/'source_freeze.json');expected=f['source55'];C=Path(f['source_root'])
assert len(expected)==55 and {p.relative_to(C).as_posix() for p in C.rglob('*') if safe(p).is_file()}==set(expected)
for n,h in expected.items():check(C/n,h)
composition=read(O/'SOURCE_COMPOSITION.json');assert composition['source55']==expected
for name,key in [('source_review.md','source_review_sha256'),('SOURCE_EQUIVALENCE_BASIS.json','source_equivalence_basis_sha256'),('SOURCE_COMPOSITION.json','composition_sha256')]:check(O/name,f[key])
for label,parent in composition['parents'].items():
    check(parent['freeze_path'],parent['freeze_sha256'])
    for n,h in parent['source55'].items():check(Path(parent['root'])/n,h)
assert expected!=composition['parents']['v18']['source55'] and expected!=composition['parents']['v19']['source55']
for n,item in composition['component_files'].items():assert expected[n]==item['sha256']==composition['parents'][item['parent']]['source55'][n]
for n,h in composition['retained_core_byte_exact'].items():assert expected[n]==h
for key,parent in [('shared_VY_edits_over_v19','v19'),('shared_AZ_edits_over_v18','v18')]:
    for n,edits in composition[key].items():
        text=(C/n).read_text(encoding='utf8')
        for old,new in reversed(edits):assert text.count(new)==1;text=text.replace(new,old,1)
        assert text==(Path(composition['parents'][parent]['root'])/n).read_text(encoding='utf8')
b3=read(R/'firmware/B0B3/qualification.json')['source_sha256']
for n,h in b3.items():check(R/'firmware/B0B3/source'/n,h)
changes={n:h for n,h in expected.items() if h!=b3[n]};assert len(changes)==12 and changes==f['B3_relative_changes']
basis=read(O/'SOURCE_EQUIVALENCE_BASIS.json');assert len(basis['transformations'])==9 and basis['new_private_same_publication_predicate_bits']==2 and basis['legacy_public_output_cycle_change']==0
for n,t in basis['transformations'].items():
    lines=(C/n).read_text(encoding='utf8').splitlines(True)
    for e in reversed(t['normalized_line_edit_spans']):
        assert ''.join(lines[e['new_start']:e['new_end']])==e['new_text'];lines[e['new_start']:e['new_end']]=e['old_text'].splitlines(True)
    assert ''.join(lines)==(Path(composition['parents']['v4']['root'])/n).read_text(encoding='utf8')
# Producer files themselves must be the independently proved bytes, not rebuilt approximations.
assert expected['sensor/mtf01p_reader.v']==composition['parents']['v18']['source55']['sensor/mtf01p_reader.v']
assert expected['sensor/mtf_shared_geometry.v']==composition['parents']['v18']['source55']['sensor/mtf_shared_geometry.v']
assert expected['position/pose_time_adapter.v']==composition['parents']['v19']['source55']['position/pose_time_adapter.v']
assert expected['position/mtf_shared_height_fusion.v']==composition['parents']['v19']['source55']['position/mtf_shared_height_fusion.v']
nav=(C/'mtf_xyz_navigation_control.v').read_text();top=(C/'acg720_ano_port.v').read_text();adapter=(C/'position/pose_time_adapter.v').read_text();metric=(C/'sensor/mtf01p_reader.v').read_text();geometry=(C/'sensor/mtf_shared_geometry.v').read_text();fusion=(C/'position/mtf_shared_height_fusion.v').read_text()
assert 'PRECHECKED_AZ_RANGE=0,PRECHECKED_INPUT_VELOCITY=0' in nav
assert '.PRECHECKED_AZ_RANGE(1),.PRECHECKED_INPUT_VELOCITY(1)) native_navigation(' in top
assert 'output reg output_az_range_ok=1' in adapter and 'output_az<=held_az;output_acc_valid<=held_valid;' in adapter and 'output_az_range_ok<=held_az>=-30000 && held_az<=30000;' in adapter
assert 'output_ax<=0;output_ay<=0;output_az<=0;output_az_range_ok<=1;' in adapter
assert 'output reg velocity_range_ok=1' in metric and 'vx_x100<=0;vy_x100<=0;velocity_range_ok<=1;' in metric
assert "wire signed [31:0] next_vx_x100=flow_numeric_ok ? {product_x[30],product_x}:32'sd0;" in metric and 'velocity_range_ok<=next_velocity_range_ok;' in metric
assert metric.index('velocity_range_ok<=next_velocity_range_ok;')<metric.index('if(have_previous && delta_ms==0)')
assert 'PRECHECKED_INPUT_VELOCITY ?velocity_range_ok:' in geometry and 'PRECHECKED_AZ_RANGE ?az_range_ok:' in fusion
assert '.output_az_range_ok(converted_az_range_ok)' in top and '.az_range_ok(converted_az_range_ok)' in top and '.velocity_range_ok(mtf_velocity_range_ok)' in top
assert (C/'acg720_ano_port.sdc').read_text().strip()=='create_clock -name clk50 -period 20.000 [get_ports {clk50}]\nset_false_path -from [get_ports {radio_rx}]'
reuse=read(O/'COMPONENT_REUSE_BINDING.json');assert reuse['passed'] and reuse['source55']==expected and len(reuse['bound_inputs'])==563
for p,h in reuse['bound_inputs'].items():check(p,h)
for family,count in [('AZ',6),('VY',8)]:
    group=reuse[family];assert len(group['actual_compile_sim_receipts'])==count
    for item in group['actual_compile_sim_receipts']:wait(item['path'],key=item['actual_wait_field'],digest=item['sha256'])
    for n,h in group['exact_compiled_source_dependencies'].items():assert expected[n]==h
for label,item in reuse['AZ']['roots_including_historical_failure1'].items():wait(item['path'],code=1 if 'failed_root' in label else 0,digest=item['sha256'])
for item in reuse['reused_core_FSM']['actual_compile_vvp_receipts']:wait(item['path'],key=item['actual_wait_field'],digest=item['sha256'])
for n,h in reuse['reused_core_FSM']['exact_core_dependencies'].items():assert expected[n]==h
six=reuse['six_controller_dependencies'];assert len(six)==6
controller=read(reuse['controller_results_path']);check(reuse['controller_results_path'],reuse['controller_results_sha256']);wait(reuse['controller_root_path'])
assert controller['five']['passed'] and controller['five']['completed']==5 and controller['boundary']['passed'] and controller['boundary']['completed']==2 and controller['contention']['passed']
for n,h in six.items():assert expected[n]==controller['source55'][n]==h
controller_dir=Path(reuse['controller_results_path']).parent
for name,stage in zip(['five','boundary','top','contention'],controller['stages']):
    actual=wait(controller_dir/(name+'_exit.json'));assert all(actual.get(k)==v for k,v in stage.items())
for case in controller['five']['results']:
    assert case['exit_code']==0;base=controller_dir/'five'/case['name'];check(base/'simulation.log',case['log_sha256']);check(base/'trace.csv',case['trace_sha256'])
for case in controller['boundary']['results']:assert case['exit_code']==0;check(controller_dir/'boundary'/('fraction_'+str(case['fraction']))/'simulation.log',case['log_sha256'])
g=read(R/'ground/B0B4/test_results/verification.json');assert g['result']=='PASS' and len(g['input_sha256'])==43;check(R/'ground/B0B4/test_results/verification.json',reuse['ground_verification_sha256'])
for n,h in g['input_sha256'].items():check(R/n,h)
for name in ['python','node']:assert g[name]['actual_exit_code']==0;check(R/'ground/B0B4/test_results'/(name+'.log'),g[name]['log_sha256'])
proof=read(O/'PROOF_BINDING.json');assert proof['passed'] and proof['source55']==expected and proof['component_binding_sha256']==sha(O/'COMPONENT_REUSE_BINDING.json')
for item in proof['fresh_actual_exit_receipts']:wait(item['path'],key=item['actual_wait_field'],normal=item['normal_field'],digest=item['sha256'])
retry=Path(proof['proof_directory']);wait(retry/'functional_runner_exit.json',digest=proof['functional_root_exit_sha256'])
wait(proof['historical_failed_functional_root']['path'],code=1,digest=proof['historical_failed_functional_root']['sha256'])
correction=read(O/'FUNCTIONAL_CORRECTION_02.json');wait(correction['original_compile_failure']['path'],code=1,digest=correction['original_compile_failure']['sha256'])
assert proof['fresh_top13']['candidate_top13_total_actual_runs']==1 and proof['fresh_top13']['actual_root_wait']==0
assert len(list(O.rglob('top13_runner_exit.json')))==1
T=Path(proof['fresh_top13']['directory']);assert (T/'top_safety_tb.v').read_bytes()==(O.parent/'v4_release_proofs/top_safety_tb.v').read_bytes()
check(T/'top_safety_results.json',proof['fresh_top13']['result_sha256']);assert read(T/'top_safety_results.json')['cases']==13
for folder in [O/'proofs',retry]:
    info=read(folder/'inputs.json')
    for p,h in info['bound_inputs'].items():
        replacement=correction.get('changed_original_input_snapshots',{}).get(p)
        check(replacement['preserved_path'] if folder.name=='proofs' and replacement else p,h)
new_tb=(O/'guard_integration_tb.v').read_text();old_tb=(O/'proofs/guard_integration_tb_attempt01.v').read_text()
assert new_tb==old_tb.replace('input [31:0] dist;','input [31:0] distance_value;').replace('distance=dist;','distance=distance_value;')
assert not re.search(r'\b(?:force|release)\b',new_tb)
assert "combinations!==4'b1111" in new_tb and 'ON ?vok:~vok' in new_tb and 'ON ?zok:~zok' in new_tb
log=(retry/'integration_vvp.stdout.log').read_text();assert 'PASS combined_guard cycles=423 checks=423 AZ_publications=10 metric_publications=15 combinations=1111 default_wrong_flags_ignored=1 no_DUT_force_preload=1' in log
contract_path=O/'validation_contract.py';spec=importlib.util.spec_from_file_location('reviewed_v20_read_only_contract',contract_path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
assert module.verify_contract(check_proof=True)['passed']
requirements=read(O/'SYN_REVIEW_GATE_REQUIREMENTS.json');check(O/'source_freeze.json',requirements['source_freeze_sha256']);check(O/'PROOF_BINDING.json',requirements['proof_binding_sha256'])
for n,h in requirements['reviewed_scripts_sha256'].items():check(O/n,h);ast.parse((O/n).read_text())
syn=(O/'run_synthesis.py').read_text();audit=(O/'audit_synthesis_only.py').read_text();launch=(O/'launch_synthesis_hidden.py').read_text()
assert syn.index('verify_syn_review()')<syn.index('A.mkdir(')<syn.index("h.run_phase('synthesis'") and launch.index('verify_syn_review()')<launch.index('subprocess.Popen')
assert "assert len(h.EXPECTED_CHANGES)==12" in syn and "assert len(helper.EXPECTED_CHANGES)==12" in audit
helper=R/'firmware/B0B4/build_candidate.py';check(helper,'abb5246c203b73c111f80bc91f8db6c8220463f7d4c5cf48dbfe2167ef49db84')
assert 'helper.mapped_audit(vg,expected)' in audit and 'auditor.extended_audit(helper,vg)' in audit
assert "g.find(p['CLK'][0])!=g.find(clocks[0])" in audit and "'all_FF_CLK50':not bad" in audit
assert "'run syn' if line=='run all'" in syn and "assert 'run pnr' not in tcl and 'run all' not in tcl" in syn and 'SYNTHESIS_COMMAND_RETURNED_EOF' in syn
assert not (O/'SYN_REVIEW_GATE.json').exists() and not (R/'out/z_aw_fix_20261026/compact_aw_v20/build_attempt_01').exists()
assert all(hashlib.sha256(safe(p).read_bytes()).hexdigest()==h for p,h in seen.items())
out=dict(passed=True,confirmed_actionable_findings=[],reviewed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),reviewer='vy_path_scout second independent review',source55=expected,
    source_freeze_sha256=sha(O/'source_freeze.json'),proof_binding_sha256=sha(O/'PROOF_BINDING.json'),component_binding_sha256=sha(O/'COMPONENT_REUSE_BINDING.json'),
    reviewed_scripts_sha256=requirements['reviewed_scripts_sha256'],B3_changes=list(changes),component_declared_inputs_rehashed=563,total_unique_files_rehashed=len(seen),
    source_composition_and_two_same_tuple_predicates=True,default_off_consumers_preserved=True,new_public_latency_cycles=0,
    preserved_failed_functional_root_wait=1,new_top13_total_actual_runs=1,new_top13_child_root_wait=0,retry_integration_root_wait=0,
    combined_integration=dict(cycles=423,AZ_publications=10,metric_publications=15,all_four_predicate_combinations=True,default_wrong_flags_ignored=True,no_DUT_force_preload=True),
    exact_six_controller_dependencies=True,ground43_rehashed=True,coreFSM_reused_exact_inputs=True,
    SYN_ONLY_original_helper_gain_18pin_strict50_gates_preserved=True,review_gate_not_created=True,vendor_started=False,simulations_rerun=False,
    limitations=['Fresh combined integration checks actual producer tuples and merged consumer gates; it is not a full navigation output/flight-state equivalence run.',
                'Original top13 controlled internal forces remain byte-identical and explicitly scoped.',
                'Parent AZ consumer tests use accelerated admission/timers; parent whole-source55 identities are not assigned to v20.',
                'This is source/evidence/SYN-preparation review; actual mapped and physical results remain required.'],
    evidence_sha256=seen,review_script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
(D/'REVIEW.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf8')
print(json.dumps(dict(passed=True,findings=0,component_inputs=563,total_files=len(seen),vendor_started=False)))
