"""Read-only exact v22 fresh-proof, sealed-SYN and separate v20/v4 source contract."""
from pathlib import Path
import hashlib,importlib.util,json,re,sys
sys.dont_write_bytecode=True
O=Path(__file__).resolve().parent;R=O.parents[3]
ROOT=R/'out/z_aw_fix_20261026/compact_aw_v22';C=ROOT/'canonical/source';A=ROOT/'build_attempt_01';V=A/'verification'
def safe(path,root=None):
    p=Path(path)
    for part in p.parts:
        n=part.lower().rstrip(' .');assert not n.startswith('.env') and not n.endswith('.env') and '.env' not in [s.lower() for s in Path(n).suffixes],str(p)
    if root is not None:assert p.resolve().is_relative_to(Path(root).resolve()),str(p)
    for q in [p,*p.parents]:assert not q.is_symlink() and not (hasattr(q,'is_junction') and q.is_junction()),str(p)
    return p
def sha(p):return hashlib.sha256(safe(p).read_bytes()).hexdigest()
def read(p):return json.loads(safe(p).read_text(encoding='utf8'))
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def validate22(require_preparation=True):
    validator=load('v22_original_bound_functional_contract',O/'validation_contract.py')
    contract=validator.verify_contract(check_proof=True);validator.verify_syn_review();expected=contract['source55']
    assert len(expected)==55 and len(contract['B3_relative_changes'])==12 and contract['legacy_public_output_cycle_change']==0
    assert {n:sha(C/n) for n in expected}=={n:sha(A/'source'/n) for n in expected}==expected
    bound={}
    def bind(p,h=None):
        p=safe(p);actual=sha(p);assert h is None or h==actual,(str(p),h,actual);bound[str(p)]=actual
    changes=read(O/'SOURCE_CHANGES.json');baseline=changes['parent_source55'];baseline_root=Path(changes['parent_source_root'])
    parent=O.parent/'compact_aw_v20';assert baseline==read(parent/'source_freeze.json')['source55']==read(parent/'SYNTHESIS_RESULT.json')['source55']
    assert {n:sha(baseline_root/n) for n in baseline}==baseline and len(baseline)==55
    assert [n for n in expected if expected[n]!=baseline[n]]==['position/mtf_xyz_hold_control.v']
    # Protected old v4 is an independent inventory, never mislabeled the v22 baseline.
    v4_meta=O.parent/'compact_aw_v4';old_v4=read(v4_meta/'source_freeze.json')['source55'];old_root=R/'out/z_aw_fix_20261026/compact_aw_v4/canonical/source'
    assert len(old_v4)==55 and {n:sha(old_root/n) for n in old_v4}==old_v4
    for root,inventory in [(C,expected),(A/'source',expected),(baseline_root,baseline),(old_root,old_v4)]:
        for n,h in inventory.items():bind(root/n,h)
    bind(parent/'source_freeze.json');bind(parent/'SYNTHESIS_RESULT.json');bind(v4_meta/'source_freeze.json')
    proof=read(O/'PROOF_BINDING.json');reuse=read(O/'REUSED_BINDINGS_RECHECK.json');components=read(O/'COMPONENT_REUSE_BINDING.json')
    assert proof['passed'] and proof['source55']==expected and proof['guard_binding_sha256']==contract['guard_binding_sha256']==sha(O/'COMPONENT_REUSE_BINDING.json')
    assert reuse['passed'] and reuse['source55']==expected and reuse['new_v22_proof_binding_sha256']==sha(O/'PROOF_BINDING.json')
    assert components['passed'] and components['source55']==expected and components['new_controller_requires_fresh_proof'] and not components['old_six_controller_hashes_claimed_current']
    for p,h in components['bound_inputs'].items():bind(p,h)
    D=safe(proof['proof_directory'],O);F=safe(proof['fresh_proof_directory'],O);B=safe(proof['alias_retry_directory'],O)
    for p,h in read(D/'inputs.json')['bound_inputs'].items():bind(p,h)
    for p,h in proof['additional_bound_inputs'].items():bind(p,h)
    bind(D/'inputs.json',proof['inputs_sha256']);bind(D/'RESULT.json',proof['result_sha256'])
    successful=[]
    assert len(proof['fresh_actual_exit_receipts'])==22
    for item in proof['fresh_actual_exit_receipts']:
        p=safe(item['path'],O);bind(p,item['sha256']);j=read(p)
        assert j[item['normal_field']] and j[item['actual_wait_field']]==0 and not j.get('terminated_after_timeout')
        successful.append({'path':str(p),'sha256':sha(p),'actual_wait_field':item['actual_wait_field'],'actual_wait':0})
    assert proof['original_attempt_root_actual_wait']==proof['original_failed_alias_compile_wait']==1
    assert proof['actual_alias_retry_root_wait']==proof['actual_completion_runner_wait']==proof['actual_proof_runner_wait']==0
    for path,value in [(F/'functional_runner_exit.json',1),(F/'alias_compile_exit.json',1),(B/'runner_exit.json',0),(D/'functional_runner_exit.json',0)]:
        j=read(path);assert j['normal_wait_return'] and j['actual_p_wait']==value;bind(path)
    assert 'Error opening temporary file' in (F/'alias_compile.stderr.log').read_text() and 'Please check TMP or TMPDIR' in (F/'alias_compile.stderr.log').read_text()
    assert not (F/'alias_vvp_exit.json').exists()
    for stage in ['five','boundary','contention','top13']:
        j=read(F/f'{stage}_exit.json');assert j['normal_wait_return'] and j['actual_p_wait']==0
        for stream in ['stdout','stderr']:bind(F/f'{stage}.{stream}.log',j[f'{stream}_sha256'])
    assert proof['fresh_five_cases']==5 and proof['fresh_fraction_cases']==[0,16] and proof['fresh_four_client'] and proof['actual_function_alias_miter']
    assert not proof['old_six_controller_byte_identity_reuse_claimed'] and proof['new_state_bits']==proof['legacy_public_output_cycle_change']==0
    assert proof['fresh_controller_six_dependencies']=={n:expected[n] for n in proof['fresh_controller_six_dependencies']}
    assert len(proof['fresh_controller_six_dependencies'])==6 and proof['fresh_controller_six_dependencies']['position/mtf_xyz_hold_control.v']!=baseline['position/mtf_xyz_hold_control.v']
    top=proof['fresh_top13'];T=safe(top['directory'],O);assert top['cases']==13 and top['actual_root_wait']==0 and top['original_TB_byte_exact']
    assert sha(T/'top_safety_tb.v')==sha(O.parent/'v4_release_proofs/top_safety_tb.v')
    assert read(F/'five/results.json')['passed'] and read(F/'five/results.json')['completed']==5
    assert read(F/'boundary/results.json')['passed'] and read(F/'boundary/results.json')['completed']==2
    assert read(F/'contention/contention/results.json')['passed'] and read(B/'RESULT.json')['passed']
    for name in ['actual_functions.v','alias_tb.v','STRUCTURAL_IDENTITY.json']:assert (F/'alias'/name).read_bytes()==(B/name).read_bytes()
    syn=read(O/'SYNTHESIS_RESULT.json');manifest_path=A/'synthesis_freeze_manifest_final.json';manifest=read(manifest_path)
    summary=read(V/'synthesis_summary.json');root=read(O/'runner_exit.json');vendor=read(V/'synthesis_exit.json');audit=read(V/'audit_exit.json')
    assert syn['passed_SYN_only'] and syn['source55']==expected and not syn['PNR_started']
    assert syn['vendor_actual_wait']==syn['runner_actual_wait']==syn['audit_actual_wait']==0
    assert manifest['source_sha256']==expected and manifest['runner_actual_wait']==manifest['vendor_actual_wait']==manifest['audit_actual_wait']==0
    assert summary['passed'] and summary['source_sha256']==expected and summary['actual_p_wait']==summary['audit_actual_p_wait']==0
    for j in [root,vendor,audit]:assert j['normal_wait_return'] and j['actual_p_wait']==0 and not j.get('terminated_after_timeout')
    bind(manifest_path,syn['synthesis_freeze_sha256']);bind(V/'synthesis_summary.json',syn['synthesis_summary_sha256']);bind(O/'runner_exit.json',manifest['root_exit_sha256'])
    bind(O/'run_synthesis.py',root['runner_sha256']);bind(O/'launch_synthesis_hidden.py',root['supervisor_sha256'])
    assert Path(root['command'][-1])==O/'run_synthesis.py' and Path(audit['command'][-1])==O/'audit_synthesis_only.py'
    assert vendor['parent_pid']==audit['parent_pid']==root['pid']
    for stream in ['stdout','stderr']:bind(O/f'runner.{stream}.log',root[f'{stream}_sha256'])
    for j,name in [(vendor,'synthesis'),(audit,'audit')]:bind(V/f'{name}.log',j['log_sha256'])
    assert 'SYNTHESIS_COMMAND_RETURNED_EOF' in (V/'synthesis.log').read_text(encoding='utf8',errors='replace')
    vg=A/'source/impl/gwsynthesis/acg720_ano_port.vg';vg_sha=sha(vg)
    assert re.fullmatch(r'[0-9a-f]{64}',vg_sha) and vg_sha==summary['netlist_sha256']==syn['netlist_sha256']
    assert not (A/'source/impl/pnr').exists()
    for rel,x in manifest['artifacts'].items():bind(safe(A/rel,A),x['sha256']);assert (A/rel).stat().st_size==x['bytes']
    for name,key in [('synthesis_exit.json','synthesis_exit_sha256'),('mapped_audit.json','mapped_audit_sha256'),('gain_port_audit.json','gain_port_audit_sha256'),('strict_ff_clock_audit.json','strict_ff_clock_audit_sha256'),('resource_comparison.json','resource_comparison_sha256'),('local_hint_effect_audit.json','local_hint_effect_audit_sha256')]:bind(V/name,summary[key])
    mapped=read(V/'mapped_audit.json');gain=read(V/'gain_port_audit.json');ff=read(V/'strict_ff_clock_audit.json');native=read(V/'native_synthesis_audit.json');hint=read(V/'local_hint_effect_audit.json')
    assert mapped['passed'] and mapped['source_sha256']==expected and mapped['netlist_sha256']==vg_sha
    assert gain['passed'] and gain['netlist_sha256']==vg_sha and len(gain['top_ports'])==18 and gain['gains']['p']['init_wire']==1000 and gain['gains']['i']['init_wire']==350
    assert ff['passed'] and ff['all_FF_CLK50'] and not ff['bad'] and ff['vg_sha256']==vg_sha
    assert native['passed'] and native['source55']==expected and native['netlist_sha256']==vg_sha and native['hook_sha256']==sha(O/'audit_synthesis_only.py')
    assert hint['passed_measurement'] and hint['source55']==expected and hint['current_vg_sha256']==vg_sha
    hint_sha=sha(V/'local_hint_effect_audit.json');assert hint_sha==syn['local_hint_effect_audit_sha256']==native['local_hint_effect_audit_sha256']==summary['local_hint_effect_audit_sha256']
    # Measure actual hint results; never turn an expected DSP decrement into an acceptance assumption.
    build=read(V/'build_input.json');assert build['source_sha256']==expected
    assert build['synthesis_options']=={'map_option':2,'replicate_resources':0,'max_fanout':200,'opt_goal':'area'}
    for inventory in ['bound_inputs','tools']:
        for p,h in build[inventory].items():bind(p,h)
    original=build['original_B4_source55'];assert len(original)==55
    for n,h in original.items():bind(R/'firmware/B0B4/source'/n,h)
    bind(R/'firmware/B0B4/build_candidate.py','abb5246c203b73c111f80bc91f8db6c8220463f7d4c5cf48dbfe2167ef49db84')
    for n in ['source_freeze.json','PROOF_BINDING.json','COMPONENT_REUSE_BINDING.json','REUSED_BINDINGS_RECHECK.json','SYNTHESIS_RESULT.json','SYN_REVIEW_GATE.json','SYNTHESIS_PREPARATION.json','validation_contract.py','SOURCE_CHANGES.json','source_review.md','physical_input_contract.py','prepare_v22_physical.py']:bind(O/n)
    out={'passed':True,'source55':expected,'baseline_source55':baseline,'baseline_version':'v20 sealed source55','protected_v4_source55':old_v4,'B3_relative_change_count':12,'VG_sha256':vg_sha,'guard_binding_sha256':contract['guard_binding_sha256'],'bound_inputs':bound,
         'successful_fresh_exit_receipts':successful,'original_attempt_root_actual_wait':1,'original_TEMP_alias_compile_actual_wait':1,'actual_alias_retry_root_wait':0,'actual_completion_runner_wait':0,'actual_top13_child_root_wait':0,
         'fresh_controller_five_cases':5,'fresh_controller_fraction_cases':[0,16],'fresh_four_client':True,'fresh_top13_cases':13,'old_controller_byte_identity_reuse_claimed':False,
         'new_private_same_publication_predicate_bits':2,'legacy_public_output_cycle_change':0,'local_hint_effect_audit_sha256':hint_sha,'main_and_peer_SYN_review_gate_rechecked':True,
         'scope':'Fresh v22 controller five/FRAC0-16/four-client/original-top13/actual-function alias RTL proof; old TEMP compile1/root1 preserved plus exact-fixture alias retry0/completion0. Unchanged AZ/VY/coreFSM/ground only rebound to exact dependencies; no whole-source parent identity or hardware acceptance.',
         'controller_scope':'New controller bytes actually rerun, never reused by old six-controller hash. Top13 retains original controlled private forces; other controller/function fixtures have none.',
         'component_scope':components['scope']}
    if require_preparation:
        p=read(O/'PHYSICAL_PREPARATION.json');assert p['VG_sha256']==vg_sha and p['source55']==expected and p['baseline_source55']==baseline and p['protected_v4_source55']==old_v4
        assert p['local_hint_effect_audit_sha256']==hint_sha and p['input_binding_sha256']==sha(O/'PHYSICAL_INPUT_BINDING.json')
        assert read(O/'PHYSICAL_INPUT_BINDING.json')['validation']==out
        for n,h in p['new_scripts_sha256'].items():assert sha(O/n)==h
    return out
