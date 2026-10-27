"""Read-only sealed-v20 source/proof/review/SYN contract; no vendor tools."""
from pathlib import Path
import hashlib,importlib.util,json,re
O=Path(__file__).resolve().parent;R=O.parents[3]
ROOT=R/'out/z_aw_fix_20261026/compact_aw_v20';C=ROOT/'canonical/source';A=ROOT/'build_attempt_01';V=A/'verification'
def safe(path,root=None):
    p=Path(path)
    for part in p.parts:
        n=part.lower().rstrip(' .');assert not n.startswith('.env') and not n.endswith('.env') and '.env' not in [s.lower() for s in Path(n).suffixes],str(p)
    if root is not None:assert p.resolve().is_relative_to(Path(root).resolve()),str(p)
    for ancestor in [p,*p.parents]:assert not ancestor.is_symlink() and not (hasattr(ancestor,'is_junction') and ancestor.is_junction()),str(p)
    return p
def sha(p):return hashlib.sha256(safe(p).read_bytes()).hexdigest()
def read(p):return json.loads(safe(p).read_text(encoding='utf8'))
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def validate20(require_preparation=True):
    validator=load('v20_original_bound_functional_contract',O/'validation_contract.py')
    contract=validator.verify_contract(check_proof=True);review=validator.verify_syn_review()
    expected=contract['source55'];before=contract['baseline_source55'];assert len(expected)==55 and len(contract['B3_relative_changes'])==12
    assert {n:sha(C/n) for n in expected}=={n:sha(A/'source'/n) for n in expected}==expected
    assert contract['new_private_same_publication_predicate_bits']==2 and contract['legacy_public_output_cycle_change']==0
    bound={}
    def bind(p,h=None):
        p=safe(p);actual=sha(p);assert h is None or actual==h,(str(p),h,actual);bound[str(p)]=actual
    proof=read(O/'PROOF_BINDING.json');reuse=read(O/'REUSED_BINDINGS_RECHECK.json');components=read(O/'COMPONENT_REUSE_BINDING.json')
    assert proof['passed'] and proof['source55']==expected and proof['actual_proof_runner_wait']==0
    assert proof['guard_binding_sha256']==contract['guard_binding_sha256']==sha(O/'COMPONENT_REUSE_BINDING.json')
    assert reuse['passed'] and reuse['source55']==expected and reuse['new_v20_proof_binding_sha256']==sha(O/'PROOF_BINDING.json')
    assert components['passed'] and components['source55']==expected and components['limitations']['no_full_source_parent_identity_claim']
    for p,h in components['bound_inputs'].items():bind(p,h)
    D=safe(proof['proof_directory'],O);inputs=read(D/'inputs.json');bind(D/'inputs.json',proof['inputs_sha256'])
    assert inputs['source55']==expected
    for p,h in inputs['bound_inputs'].items():bind(p,h)
    successful=[]
    for item in proof['fresh_actual_exit_receipts']:
        p=safe(item['path'],O);bind(p,item['sha256']);j=read(p)
        assert j[item['actual_wait_field']]==0 and j[item['normal_field']]
        successful.append({'path':str(p),'sha256':sha(p),'actual_wait_field':item['actual_wait_field'],'actual_wait':j[item['actual_wait_field']]})
    retry=read(D/'functional_runner_exit.json');assert retry['normal_wait_return'] and retry['actual_p_wait']==0
    bind(D/'functional_runner_exit.json',proof['functional_root_exit_sha256'])
    bind(retry['command'][-1],retry['runner_sha256'])
    for stream in ['stdout','stderr']:bind(D/f'functional_runner.{stream}.log',retry[f'{stream}_sha256'])
    for name in ['integration_compile','integration_vvp']:
        p=D/f'{name}_exit.json';j=read(p);assert j['normal_wait_return'] and j['actual_p_wait']==0 and not j.get('terminated_after_timeout');bind(p)
        for stream in ['stdout','stderr']:bind(D/f'{name}.{stream}.log',j[f'{stream}_sha256'])
    top=proof['fresh_top13'];T=safe(top['directory'],O);top_root_path=safe(top['root_exit_path'],O);top_root=read(top_root_path)
    assert top['passed'] and top['cases']==13 and top['candidate_top13_total_actual_runs']==1 and top_root['normal_wait_return'] and top_root['actual_p_wait']==0
    assert sha(T/'top_safety_tb.v')==sha(O.parent/'v4_release_proofs/top_safety_tb.v')
    bind(top_root_path);bind(T/'top_safety_tb.v');bind(T/'top_safety_results.json')
    for stream in ['stdout','stderr']:bind(top_root_path.parent/f'top13_runner.{stream}.log',top_root[f'{stream}_sha256'])
    old=proof['historical_failed_functional_root'];old_path=safe(old['path'],O);bind(old_path,old['sha256']);old_record=read(old_path)
    assert old['actual_p_wait']==old_record['actual_p_wait']==1 and old_record['normal_wait_return']
    for stream in ['stdout','stderr']:bind(old_path.parent/f'functional_runner.{stream}.log',old_record[f'{stream}_sha256'])
    bind(O/'FUNCTIONAL_CORRECTION_02.json');assert proof['core_FSM_rerun'] is False
    # A successful vendor process alone is insufficient: audit/root0 and seal are mandatory.
    syn=read(O/'SYNTHESIS_RESULT.json');manifest_path=A/'synthesis_freeze_manifest_final.json';manifest=read(manifest_path)
    summary=read(V/'synthesis_summary.json');root=read(O/'runner_exit.json');vendor=read(V/'synthesis_exit.json');audit=read(V/'audit_exit.json')
    assert syn['passed_SYN_only'] and syn['source55']==expected and syn['vendor_actual_wait']==syn['runner_actual_wait']==syn['audit_actual_wait']==0
    assert manifest['source_sha256']==expected and manifest['runner_actual_wait']==manifest['vendor_actual_wait']==manifest['audit_actual_wait']==0
    assert summary['passed'] and summary['source_sha256']==expected and summary['actual_p_wait']==summary['audit_actual_p_wait']==0
    for j in [root,vendor,audit]:assert j['normal_wait_return'] and j['actual_p_wait']==0 and not j.get('terminated_after_timeout')
    bind(manifest_path,syn['synthesis_freeze_sha256']);bind(V/'synthesis_summary.json',syn['synthesis_summary_sha256']);bind(O/'runner_exit.json',manifest['root_exit_sha256'])
    bind(O/'run_synthesis.py',root['runner_sha256']);bind(O/'launch_synthesis_hidden.py',root['supervisor_sha256'])
    for stream in ['stdout','stderr']:bind(O/f'runner.{stream}.log',root[f'{stream}_sha256'])
    for j,name in [(vendor,'synthesis'),(audit,'audit')]:bind(V/f'{name}.log',j['log_sha256'])
    assert 'SYNTHESIS_COMMAND_RETURNED_EOF' in (V/'synthesis.log').read_text(encoding='utf8',errors='replace')
    vg=A/'source/impl/gwsynthesis/acg720_ano_port.vg';vg_sha=sha(vg)
    assert re.fullmatch(r'[0-9a-f]{64}',vg_sha) and vg_sha==summary['netlist_sha256']==syn['netlist_sha256']
    assert not (A/'source/impl/pnr').exists()
    for rel,x in manifest['artifacts'].items():bind(safe(A/rel,A),x['sha256'])
    checks=[('synthesis_exit.json','synthesis_exit_sha256'),('mapped_audit.json','mapped_audit_sha256'),('gain_port_audit.json','gain_port_audit_sha256'),('strict_ff_clock_audit.json','strict_ff_clock_audit_sha256'),('resource_comparison.json','resource_comparison_sha256')]
    for name,key in checks:bind(V/name,summary[key])
    mapped=read(V/'mapped_audit.json');gain=read(V/'gain_port_audit.json');ff=read(V/'strict_ff_clock_audit.json');native=read(V/'native_synthesis_audit.json')
    assert mapped['passed'] and mapped['source_sha256']==expected and mapped['netlist_sha256']==vg_sha
    assert gain['passed'] and gain['netlist_sha256']==vg_sha and len(gain['top_ports'])==18 and gain['gains']['p']['init_wire']==1000 and gain['gains']['i']['init_wire']==350
    assert ff['passed'] and ff['all_FF_CLK50'] and not ff['bad'] and ff['vg_sha256']==vg_sha
    assert native['passed'] and native['source55']==expected and native['netlist_sha256']==vg_sha and native['hook_sha256']==sha(O/'audit_synthesis_only.py')
    build=read(V/'build_input.json')
    for inventory in ['bound_inputs','tools']:
        for p,h in build[inventory].items():bind(p,h)
    helper=R/'firmware/B0B4/build_candidate.py';bind(helper,'abb5246c203b73c111f80bc91f8db6c8220463f7d4c5cf48dbfe2167ef49db84')
    for n in ['source_freeze.json','PROOF_BINDING.json','COMPONENT_REUSE_BINDING.json','REUSED_BINDINGS_RECHECK.json','SYNTHESIS_RESULT.json','SYN_REVIEW_GATE.json','SYNTHESIS_PREPARATION.json','validation_contract.py','SOURCE_COMPOSITION.json','SOURCE_EQUIVALENCE_BASIS.json','source_review.md']:bind(O/n)
    out={'passed':True,'source55':expected,'baseline_source55':before,'B3_relative_change_count':12,'VG_sha256':vg_sha,'guard_binding_sha256':contract['guard_binding_sha256'],'bound_inputs':bound,
         'successful_fresh_exit_receipts':successful,'actual_retry_functional_root_wait':retry['actual_p_wait'],'actual_top13_child_root_wait':top_root['actual_p_wait'],'historical_failed_functional_root_wait':old_record['actual_p_wait'],
         'candidate_top13_total_actual_runs':1,'new_private_same_publication_predicate_bits':2,'legacy_public_output_cycle_change':0,
         'scope':proof['scope'],'integration_scope':proof['fresh_integration']['scope'],'component_limitations':components['limitations'],'main_and_peer_SYN_review_gate_rechecked':True}
    if require_preparation:
        preparation=read(O/'PHYSICAL_PREPARATION.json');assert preparation['VG_sha256']==vg_sha and preparation['source55']==expected
        assert preparation['input_binding_sha256']==sha(O/'PHYSICAL_INPUT_BINDING.json')
        assert read(O/'PHYSICAL_INPUT_BINDING.json')['validation']==out
        for n,h in preparation['new_scripts_sha256'].items():assert sha(O/n)==h
    return out
