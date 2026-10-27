"""Check and bind dormant v19 SYN-only preparation. Never import/launch vendor runners."""
from pathlib import Path
import ast,datetime,hashlib,json
from validation_contract import verify_contract

O=Path(__file__).resolve().parent;R=O.parents[3];P=O.parent/'compact_aw_v17'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf8'))
write=lambda p,j:p.write_text(json.dumps(j,indent=2)+'\n',encoding='utf8',newline='\n')
contract=verify_contract(check_proof=True)
assert not (R/'out/z_aw_fix_20261026/compact_aw_v19/build_attempt_01').exists()
assert not (O/'runner_process.json').exists() and not (O/'runner_exit.json').exists()
reuse=read(O/'REUSED_BINDINGS_RECHECK.json');assert reuse['passed'] and reuse['source55']==contract['source55']
assert reuse['new_v19_proof_binding_sha256']==sha(O/'PROOF_BINDING.json')
assert reuse['guard_binding_sha256']==contract['guard_binding_sha256'] and reuse['guard_contract_rechecked']
helper=R/'firmware/B0B4/build_candidate.py';auditor=O.parent/'compact_aw_v2/run_synthesis.py'
assert sha(helper)=='abb5246c203b73c111f80bc91f8db6c8220463f7d4c5cf48dbfe2167ef49db84'
assert sha(auditor)=='23fe046b259c6713536fc27862eb80a3b392808a77e842aac2085c3f91f3d658'
original=read(R/'analysis/20261026_z_aw_fix/handoff_20261026/SOURCE_BINDINGS.json')['source_sha256']['B0B4_unpromoted_prototype']
assert {n:sha(R/'firmware/B0B4/source'/n) for n in original}==original
scripts=['run_synthesis.py','audit_synthesis_only.py','seal_synthesis.py','launch_synthesis_hidden.py']
syntax={}
for name in scripts+['validation_contract.py','run_proofs.py','launch_functional_hidden.py','verify_reused_bindings.py','prepare_synthesis_metadata.py']:
    p=O/name;ast.parse(p.read_text(encoding='utf8'),filename=str(p));syntax[name]={'ast_parse_passed':True,'sha256':sha(p)}
assert 'run pnr' not in (O/'launch_synthesis_hidden.py').read_text(encoding='utf8')
text=(O/'run_synthesis.py').read_text(encoding='utf8')
assert 'verify_contract(check_proof=True)' in text and 'guard_binding_sha256' in text
assert 'len(h.EXPECTED_CHANGES)==10' in text and "'run syn' if line=='run all'" in text
audit=(O/'audit_synthesis_only.py').read_text(encoding='utf8')
assert 'len(helper.EXPECTED_CHANGES)==10' in audit and "helper.mapped_audit(vg,expected)" in audit
assert 'auditor.extended_audit(helper,vg)' in audit and "'all_FF_CLK50':not bad" in audit
parent_templates={name:{'path':str(P/name),'sha256':sha(P/name)} for name in scripts+['verify_reused_bindings.py','run_proofs.py']}
write(O/'SYNTHESIS_PREPARATION.json',{
    'prepared_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'Ready SYN_ONLY preparation for exact AZ guard/landing/fanout v19; vendor not launched and no PNR/hardware permission implied',
    'source55':contract['source55'],'baseline_source55':contract['baseline_source55'],
    'expected_B3_relative_changes':contract['B3_relative_changes'],'expected_B3_relative_change_count':10,
    'guard_binding_sha256':contract['guard_binding_sha256'],'proof_binding_sha256':sha(O/'PROOF_BINDING.json'),
    'reused_bindings_recheck_sha256':sha(O/'REUSED_BINDINGS_RECHECK.json'),'source_freeze_sha256':sha(O/'source_freeze.json'),
    'source_equivalence_basis_sha256':sha(O/'SOURCE_EQUIVALENCE_BASIS.json'),'source_review_sha256':sha(O/'source_review.md'),
    'original_helpers':{str(helper):sha(helper),str(auditor):sha(auditor)},'original_B4_source55_rechecked':True,
    'scripts':syntax,'parent_templates':parent_templates,
    'derivation_scope':'v17 SYN-only process/audit/seal/supervisor gates retained; v19 paths, exact10 B3-relative changes and explicit read-only source/guard/functional proof startup checks added. No vendor launch during preparation.',
    'retained_mapped_gates':['exact20.000ns clk50 SDC','all FF clk50 and no divided/gated derived clocks','radio_rx synchronizer chain and pad fanout','default XY P1000/I350 into real controller','exact18 ports/pins and B4 identity','original source55 and helper hashes'],
    'physical_gates_retained_for_later_separate_qualification':['complete routing','actual20ns period','Fmax at least50MHz','setup and hold violated endpoints zero','all five setup/hold/recovery/removal/pulse slacks nonnegative','exact18 pins with radio RX B16/TX B15','B4 identity and actual normal process exits'],
    'functional_contract':{'new_same_publication_predicate_bits':1,'legacy_output_cycle_change':0,'mechanical_reverse_scope_only':True,'guard_correctness':'GUARD_REUSE_RECHECK actual component evidence, not source reversal','top13_private_forces_disclosed':True,'component_timing_acceleration_disclosed':True,'no_VY_changes':True},
    'validation':{'source_contract_passed':True,'fresh_core_FSM_compile_vvp_root_actual_waits':[0,0,0],'already_fresh_exact_v19_top13_actual_compile_vvp_root_waits':[0,0,0],'scripts_ast_passed':True},
    'vendor_launched':False,'PNR_started':False,'hardware_actions':False,
})
print(json.dumps({'SYN_ONLY_prepared':True,'source_files':55,'B3_relative_changes':10,'guard_binding_sha256':contract['guard_binding_sha256'],'proof_binding_sha256':sha(O/'PROOF_BINDING.json'),'preparation_sha256':sha(O/'SYNTHESIS_PREPARATION.json'),'vendor_launched':False}))
