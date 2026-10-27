"""Read-only STD22 whole55 proof plus actual sealed fan100 SYN contract."""
from pathlib import Path
import hashlib,importlib.util,json,sys
sys.dont_write_bytecode=True
O=Path(__file__).resolve().parent;R=O.parents[3];STANDARD=O.parent/'compact_aw_v22'
ROOT=R/'out/z_aw_fix_20261026/compact_aw_v22_fan100';DONOR=ROOT/'build_attempt_01';V=DONOR/'verification'
CANON=R/'out/z_aw_fix_20261026/compact_aw_v22/canonical/source'
VG_SHA='bf2c2de81c82f16bd3c0badd8790aa0a4c216ad9bf8273bbcd1e79a3f997508e'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
read=lambda p:json.loads(Path(p).read_text(encoding='utf8'))
def load(n,p):
    s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def successful(j):return isinstance(j,dict) and j.get('normal_wait_return') is True and type(j.get('actual_p_wait')) is int and j['actual_p_wait']==0
def validate_physical(require_preparation=True,require_review=False):
    inherited=load('unchanged_fan100_SYN_contract',O/'input_contract.py');base=inherited.validate();inherited.review_gate()
    expected=base['source55'];bound=dict(read(O/'SOURCE_REUSE_BINDING.json')['bound_inputs'])
    def bind(p,h=None):
        p=Path(p);assert not p.is_symlink() and '.env' not in p.name.lower();got=sha(p);assert h is None or got==h,(str(p),h,got);bound[str(p)]=got
    for n,h in expected.items():bind(CANON/n,h);bind(DONOR/'source'/n,h)
    assert len(expected)==55 and not (ROOT/'canonical').exists()
    result=read(O/'SYNTHESIS_RESULT.json');summary=read(V/'synthesis_summary.json');manifest=read(DONOR/'synthesis_freeze_manifest_final.json')
    review_path=R/'analysis/agent_reviews/v22_fan100_result_20261027/REVIEW.json'
    bind(review_path,'511546e7805297dfe8654e9ddfb2d9f80400d754ca5e03b5a0c2589f41369370');independent=read(review_path)
    assert independent['passed_independent_SYN_result_review'] is True and independent['source55']==expected and independent['VG_sha256']==VG_SHA
    assert independent['SYNTHESIS_RESULT_sha256']==sha(O/'SYNTHESIS_RESULT.json') and independent['synthesis_manifest_sha256']==result['synthesis_freeze_sha256']
    assert independent['strict_clock_radio_gain18pin_gates_passed'] is True and independent['whole55_byte_unchanged'] is True
    root=read(O/'runner_exit.json');vendor=read(V/'synthesis_exit.json');audit=read(V/'audit_exit.json')
    assert all(successful(j) for j in [root,vendor,audit])
    assert result['passed_SYN_only'] is True and result['source55']==expected and result['netlist_sha256']==VG_SHA
    assert result['vendor_actual_wait']==result['audit_actual_wait']==result['runner_actual_wait']==0 and result['PNR_started'] is False
    assert result['effective_option_delta']=={'max_fanout':{'from':200,'to':100}} and result['source_build_tcl_unchanged'] is True
    assert summary['passed'] is True and summary['source_sha256']==expected and summary['netlist_sha256']==VG_SHA
    assert summary['actual_vendor_wait']==summary['actual_audit_wait']==0 and summary['PNR_started'] is False
    assert manifest['source_sha256']==expected and manifest['vendor_actual_wait']==manifest['audit_actual_wait']==manifest['runner_actual_wait']==0
    bind(DONOR/'synthesis_freeze_manifest_final.json',result['synthesis_freeze_sha256']);bind(V/'synthesis_summary.json',result['synthesis_summary_sha256']);bind(O/'runner_exit.json',manifest['root_exit_sha256'])
    assert root['command']==[sys.executable,'-B','-X','utf8',str(O/'run_synthesis.py')]
    bind(O/'run_synthesis.py',root['runner_sha256']);bind(O/'launch_synthesis_hidden.py',root['supervisor_sha256'])
    for stream in ['stdout','stderr']:bind(O/f'runner.{stream}.log',root[f'{stream}_sha256'])
    for phase,j in [('synthesis',vendor),('audit',audit)]:
        assert j['stage']==phase and j['parent_pid']==root['pid'] and Path(j['cwd'])==DONOR/'source'
        assert Path(j['log'])==V/f'{phase}.log';bind(V/f'{phase}.log',j['log_sha256'])
    assert vendor['command'][1:]==[str(DONOR/'synth_only.tcl')]
    assert audit['command']==[sys.executable,'-B','-X','utf8',str(O/'audit_synthesis_only.py')]
    assert 'SYNTHESIS_COMMAND_RETURNED_EOF' in (V/'synthesis.log').read_text(errors='replace')
    assert 'NATIVE_SYNTHESIS_AUDIT_PASS '+VG_SHA in (V/'audit.log').read_text(errors='replace')
    for rel,x in manifest['artifacts'].items():bind(DONOR/rel,x['sha256']);assert (DONOR/rel).stat().st_size==x['bytes']
    for n,h in summary['artifacts_sha256'].items():bind(V/n,h)
    native=read(V/'native_synthesis_audit.json');mapped=read(V/'mapped_audit.json');gain=read(V/'gain_port_audit.json');clock=read(V/'strict_ff_clock_audit.json')
    assert native['passed'] is True and native['source55']==expected and native['netlist_sha256']==VG_SHA
    bind(O/'audit_synthesis_only.py',native['hook_sha256'])
    for n,h in native['artifacts_sha256'].items():bind(V/n,h)
    assert mapped['passed'] is True and mapped['source_sha256']==expected and mapped['netlist_sha256']==VG_SHA
    assert gain['passed'] is True and gain['netlist_sha256']==VG_SHA and len(gain['top_ports'])==18
    assert gain['gains']['p']['init_wire']==1000 and gain['gains']['i']['init_wire']==350
    assert clock['passed'] is True and clock['all_FF_CLK50'] is True and not clock['bad'] and clock['vg_sha256']==VG_SHA
    vg=DONOR/'source/impl/gwsynthesis/acg720_ano_port.vg';bind(vg,VG_SHA);assert not (DONOR/'source/impl/pnr').exists()
    from effective_recipe import make_recipe
    assert (DONOR/'synth_only.tcl').read_text()==make_recipe(DONOR/'source/build.tcl')
    actual_input=read(V/'build_input.json');assert actual_input['source_sha256']==expected and actual_input['synthesis_options']=={'map_option':2,'replicate_resources':0,'max_fanout':100,'opt_goal':'area'}
    for inventory in ['bound_inputs','tools']:
        for p,h in actual_input[inventory].items():bind(p,h)
    original=read(R/'out/z_aw_fix_20261026/compact_aw_v22/build_attempt_01/verification/build_input.json')['original_B4_source55']
    for n,h in original.items():bind(R/'firmware/B0B4/source'/n,h)
    for n,h in base['protected_v4_source55'].items():bind(R/'out/z_aw_fix_20261026/compact_aw_v4/canonical/source'/n,h)
    for n,h in base['baseline_source55'].items():bind(R/'out/z_aw_fix_20261026/compact_aw_v20/canonical/source'/n,h)
    for n in ['SYNTHESIS_RESULT.json','SOURCE_REUSE_BINDING.json','SYN_REVIEW_GATE.json','SYNTHESIS_PREPARATION.json','source_freeze.json','input_contract.py','effective_recipe.py','mapped_fanout.py','seal_synthesis.py']:bind(O/n)
    helper=R/'firmware/B0B4/build_candidate.py';bind(helper,'abb5246c203b73c111f80bc91f8db6c8220463f7d4c5cf48dbfe2167ef49db84')
    out={'passed':True,'source55':expected,'canonical_source_root':str(CANON),'standard_source_proof_origin':str(STANDARD),'DONOR':str(DONOR),'VG_sha256':VG_SHA,'guard_binding_sha256':base['guard_binding_sha256'],'bound_inputs':bound,
         'original_B4_source55':original,'protected_v4_source55':base['protected_v4_source55'],'baseline_v20_source55':base['baseline_source55'],
         'original_TEMP_compile1_root1_preserved':True,'actual_alias_retry_root_wait':0,'actual_completion_runner_wait':0,'successful_fresh_proof_receipts':22,
         'independent_fan100_SYN_result_review_sha256':sha(review_path),
         'local_hint_effect_audit_sha256':base['local_hint_effect_audit_sha256'],'source_build_Tcl_max_fanout':200,'actual_donor_SYN_max_fanout':100,'actual_vendor_audit_root_waits':[vendor['actual_p_wait'],audit['actual_p_wait'],root['actual_p_wait']],
         'scope':'Whole55 and functional proof belong to STD22. fan100 donor is separately actual SYN/audit/root0 and sealed; only effective SYN max_fanout changes. No new RTL proof or physical acceptance.',
         'functional_scope':base['scope'],'component_scope':base['component_scope'],'controller_scope':base['controller_scope']}
    if require_preparation:
        b=read(O/'PHYSICAL_INPUT_BINDING.json');prep=read(O/'PHYSICAL_PREPARATION.json')
        assert b['validation']==out and b['passed'] is True and prep['input_binding_sha256']==sha(O/'PHYSICAL_INPUT_BINDING.json')
        assert prep['source55']==expected and prep['VG_sha256']==VG_SHA
        for n,h in prep['new_scripts_sha256'].items():assert sha(O/n)==h,n
    if require_review:
        gate=read(O/'PHYSICAL_REVIEW_GATE.json');prep=read(O/'PHYSICAL_PREPARATION.json')
        assert gate['main_review_passed'] is True and gate['independent_agent_review_passed'] is True
        assert gate['preparation_sha256']==sha(O/'PHYSICAL_PREPARATION.json') and gate['input_binding_sha256']==sha(O/'PHYSICAL_INPUT_BINDING.json')
        assert gate['reviewed_scripts_sha256']==prep['new_scripts_sha256']
    return out
