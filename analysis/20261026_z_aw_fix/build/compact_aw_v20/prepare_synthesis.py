"""Prepare dormant v20 SYN-only scripts; main+peer review gate remains absent."""
from pathlib import Path
import ast,datetime,difflib,hashlib,json
from validation_contract import verify_contract
O=Path(__file__).resolve().parent;R=O.parents[3];P=O.parent/'compact_aw_v19'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf8'))
write=lambda p,j:p.write_text(json.dumps(j,indent=2,ensure_ascii=False)+'\n',encoding='utf8',newline='\n')
contract=verify_contract(check_proof=True);reuse=read(O/'REUSED_BINDINGS_RECHECK.json')
assert reuse['passed'] and reuse['source55']==contract['source55'] and reuse['new_v20_proof_binding_sha256']==sha(O/'PROOF_BINDING.json')
names=['run_synthesis.py','audit_synthesis_only.py','seal_synthesis.py','launch_synthesis_hidden.py']
assert not any((O/n).exists() for n in names) and not (O/'SYNTHESIS_PREPARATION.json').exists()
assert not (R/'out/z_aw_fix_20261026/compact_aw_v20/build_attempt_01').exists() and not (O/'SYN_REVIEW_GATE.json').exists()
def one(s,a,b):assert s.count(a)==1,(a,s.count(a));return s.replace(a,b,1)
parents={n:sha(P/n) for n in names}
for name in names:
    text=(P/name).read_text(encoding='utf8').replace('compact_aw_v19','compact_aw_v20').replace('v19','v20')
    text=text.replace('GUARD_REUSE_RECHECK.json','COMPONENT_REUSE_BINDING.json').replace('AZ_SOURCE_COMPOSITION.json','SOURCE_COMPOSITION.json')
    text=text.replace('len(h.EXPECTED_CHANGES)==10','len(h.EXPECTED_CHANGES)==12').replace('len(helper.EXPECTED_CHANGES)==10','len(helper.EXPECTED_CHANGES)==12')
    if name=='run_synthesis.py':
        text=one(text,'from validation_contract import verify_contract','from validation_contract import verify_contract,verify_syn_review')
        text=one(text,'    contract=verify_contract(check_proof=True)','    contract=verify_contract(check_proof=True)\n    verify_syn_review()')
        text=one(text,"O/'SOURCE_COMPOSITION.json',helper_path","O/'SOURCE_COMPOSITION.json',O/'SYN_REVIEW_GATE.json',helper_path")
    elif name=='launch_synthesis_hidden.py':
        text=one(text,"assert not (O/'runner_process.json').exists()", "from validation_contract import verify_contract,verify_syn_review\nassert verify_contract(check_proof=True)['passed']\nverify_syn_review()\nassert not (O/'runner_process.json').exists()")
    elif name=='audit_synthesis_only.py':
        text=text.replace('Actual v20 AZ guard and landing/fanout composition','Actual v20 AZ/VY guards and landing/fanout composition')
    (O/name).write_text(text,encoding='utf8',newline='\n')
helper=R/'firmware/B0B4/build_candidate.py';auditor=O.parent/'compact_aw_v2/run_synthesis.py'
assert sha(helper)=='abb5246c203b73c111f80bc91f8db6c8220463f7d4c5cf48dbfe2167ef49db84'
assert sha(auditor)=='23fe046b259c6713536fc27862eb80a3b392808a77e842aac2085c3f91f3d658'
syntax={}
for name in names+['validation_contract.py','verify_reused_bindings.py','run_proofs.py','run_proofs_retry02.py','launch_functional_hidden.py','launch_functional_retry02_hidden.py','recheck_component_proofs.py']:
    ast.parse((O/name).read_text(encoding='utf8'),filename=str(O/name));syntax[name]={'AST_parse_passed':True,'sha256':sha(O/name)}
review_scripts={n:sha(O/n) for n in names+['validation_contract.py']}
write(O/'SYN_REVIEW_GATE_REQUIREMENTS.json',{'scope':'Instructions for main after its actual review plus another agent independent review; this is not an approval gate and cannot authorize SYN.',
    'actual_gate_path':str(O/'SYN_REVIEW_GATE.json'),'required_true_fields':['main_review_passed','independent_agent_review_passed'],
    'source_freeze_sha256':sha(O/'source_freeze.json'),'proof_binding_sha256':sha(O/'PROOF_BINDING.json'),'reviewed_scripts_sha256':review_scripts,
    'main_review_passed':False,'independent_agent_review_passed':False,'vendor_started':False})
diff=''
for name in names:diff+=''.join(difflib.unified_diff((P/name).read_text(encoding='utf8').splitlines(True),(O/name).read_text(encoding='utf8').splitlines(True),fromfile='v19/'+name,tofile='v20/'+name))
(O/'SYN_SCRIPT_DERIVATION.diff').write_text(diff,encoding='utf8',newline='\n')
proof=read(O/'PROOF_BINDING.json')
write(O/'SYNTHESIS_PREPARATION.json',{'prepared_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'Offline SYN_ONLY preparation of new complete v20 source55. Main and another agent must review before the absent SYN_REVIEW_GATE can be created; no vendor launch performed.',
    'source55':contract['source55'],'baseline_source55':contract['baseline_source55'],'expected_B3_relative_changes':contract['B3_relative_changes'],'expected_B3_relative_change_count':12,
    'source_freeze_sha256':sha(O/'source_freeze.json'),'proof_binding_sha256':sha(O/'PROOF_BINDING.json'),'guard_binding_sha256':contract['guard_binding_sha256'],'component_reuse_binding_sha256':sha(O/'COMPONENT_REUSE_BINDING.json'),
    'reused_bindings_recheck_sha256':sha(O/'REUSED_BINDINGS_RECHECK.json'),'source_review_sha256':sha(O/'source_review.md'),'source_equivalence_basis_sha256':sha(O/'SOURCE_EQUIVALENCE_BASIS.json'),
    'new_private_same_publication_predicate_bits':2,'legacy_public_output_cycle_change':0,'no_full_source_parent_identity_claim':True,
    'fresh_top13':{'actual_total_new_v20_runs':1,'cases':13,'root_wait':proof['fresh_top13']['actual_root_wait'],'reused_by_retry_without_second_top13_run':True},
    'functional_retry':{'original_aggregate_root_wait':1,'original_top13_child_wait':0,'retry_aggregate_root_wait':proof['actual_proof_runner_wait'],'integration_compile_vvp_waits':[0,0],'core_FSM_rerun':False},
    'proof_limitations':read(O/'COMPONENT_REUSE_BINDING.json')['limitations'],'original_helpers':{str(helper):sha(helper),str(auditor):sha(auditor)},'parent_scripts_sha256':parents,'scripts':syntax,
    'derivation_sha256':sha(O/'SYN_SCRIPT_DERIVATION.diff'),'review_gate_requirements_sha256':sha(O/'SYN_REVIEW_GATE_REQUIREMENTS.json'),'review_gate_created':False,
    'retained_gates':['exact20.000ns clk50 SDC','all FF clk50','radio synchronizers and pad fanout','default1000/350 to real controller','exact18ports and B4 identity','original strict helper/auditor hashes','full50MHz physical acceptance remains separate with all5 slacks/zero endpoints/fullroute/real exits'],
    'vendor_started':False,'PNR_started':False,'hardware_actions':False})
assert verify_contract(check_proof=True)['passed'] and not (O/'SYN_REVIEW_GATE.json').exists()
assert all(sha(P/n)==h for n,h in parents.items())
print(json.dumps({'SYN_ONLY_prepared':True,'source55':55,'B3_relative_changes':12,'private_predicate_bits':2,'legacy_public_output_cycle_change':0,'AST_parse_passed':True,'review_gate_absent':True,'preparation_sha256':sha(O/'SYNTHESIS_PREPARATION.json'),'vendor_started':False}))
