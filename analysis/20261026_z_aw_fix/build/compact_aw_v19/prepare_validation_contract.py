"""Create v19 functional contract and dormant SYN-only scripts from v17 templates."""
from pathlib import Path
import datetime,difflib,hashlib,json

O=Path(__file__).resolve().parent;R=O.parents[3];P=O.parent/'compact_aw_v17'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf8'))
write=lambda p,j:p.write_text(json.dumps(j,indent=2,ensure_ascii=False)+'\n',encoding='utf8',newline='\n')
composition=read(O/'AZ_SOURCE_COMPOSITION.json');C=Path(composition['source_root']);expected=composition['source55']
before=composition['parents']['v4']['source55'];OLD=Path(composition['parents']['v4']['root'])
assert not (O/'source_freeze.json').exists() and not (O/'PROOF_BINDING.json').exists()
assert {n:sha(C/n) for n in expected}==expected
b3=read(R/'firmware/B0B3/qualification.json')['source_sha256'];changes={n:h for n,h in expected.items() if h!=b3[n]}
assert len(changes)==10
guard_files=['position/pose_time_adapter.v','acg720_ano_port.v','mtf_xyz_navigation_control.v','position/mtf_shared_height_fusion.v']
transformations={}
for n in expected:
    if expected[n]==before[n]:continue
    old=(OLD/n).read_text(encoding='utf8').splitlines(True);new=(C/n).read_text(encoding='utf8').splitlines(True)
    edits=[]
    for tag,a,b,c,d in difflib.SequenceMatcher(a=old,b=new,autojunk=False).get_opcodes():
        if tag!='equal':edits.append({'old_start':a,'old_end':b,'new_start':c,'new_end':d,'old_text':''.join(old[a:b]),'new_text':''.join(new[c:d])})
    restored=list(new)
    for e in reversed(edits):restored[e['new_start']:e['new_end']]=e['old_text'].splitlines(True)
    assert restored==old
    transformations[n]={'baseline_sha256':before[n],'candidate_sha256':expected[n],'normalized_line_edit_spans':edits,
        'reverse_exact_normalized_text':True,'meaning':'Edit inventory/source reconstruction only; guard behavior is justified by GUARD_REUSE_RECHECK and same-tuple contract' if n in guard_files else 'Retained v17 source transformation; actual fresh old/new/default core FSM proof required'}
assert len(transformations)==7
basis={
    'scope':'v4 baseline plus v17 landing/fanout transformations and exact v9/v8 AZ-guard composition. Source reconstruction is not an equivalence proof for the added guard state.',
    'transformations':transformations,'unchanged_files':48,'line_endings_normalized':['core/height_loss_fallback.v'],
    'scope_delimitation':{'reverse_reconstruction_is_not_guard_correctness_proof':True,'reverse_reconstruction_proves':'Complete textual change inventory and unchanged residual relative to frozen v4, after line-ending normalization',
        'core_equivalence_basis':'v17 threshold-distribution/default-interface argument plus a fresh full-state old/new/default FSM miter and actual fallback implication',
        'guard_correctness_basis':'Exact three v9/v8 module bodies, exact v9 wiring with only existing v17 synthesis comment; actual producer invariant/full fusion receipt dependencies bound by GUARD_REUSE_RECHECK',
        'no_general_four_state_landing_algebra_claim':True,'no_standalone_full_flight_or_physical_claim':True},
    'guard_contract':{'guard_binding_path':str(O/'GUARD_REUSE_RECHECK.json'),'guard_binding_sha256':sha(O/'GUARD_REUSE_RECHECK.json'),
        'new_same_publication_predicate_bits':1,'new_bit':'pose_time_adapter.output_az_range_ok','legacy_output_cycle_change':0,
        'predicate':'signed32 published output_az >= -30000 && output_az <= 30000',
        'reset_cancel':'output_az=0 and predicate=1 on the same edge',
        'ordinary_publication':'held signed32 AZ and its exact inclusive predicate publish together; no extra public cycle',
        'fault_busy_idle':'Public AZ and predicate hold together in all branches without publication, including fault and start-while-busy; validity clears independently',
        'default_callers':'PRECHECKED_AZ_RANGE=0 retains original signed32 numeric compare; native top explicitly enables1 and wires the same tuple flag',
        'preserved':'All original numeric axes, Q16 precision,64-bit arithmetic and legacy output schedules; no VY changes',
        'component_limits':'Producer/fusion finite traces, full actual math RTL with accelerated component timing; top13 deliberately forces core/gate/controller dependencies'},
    'core_state_or_cycle_additions':0,'new_predicate_register_bits':1,
}
write(O/'SOURCE_EQUIVALENCE_BASIS.json',basis)
review='''# v19: exact AZ guard composed with v17 landing and fanout changes

The frozen v4 source55 is the functional baseline. The candidate preserves the three v17 core files byte for byte and copies the proven v9/v8 pose-time adapter, navigation consumer and shared height consumer byte for byte. The top is exact v9 with the existing v17 previous_pose_valid syn_maxfan10 comment merged once. Seven files differ from v4; ten differ from B3; the other48 v4 files are byte-identical. No VY changes are present.

There is one new registered same-publication AZ predicate bit. This is new predicate state, so this candidate must not be described as having no new state. Every legacy public output retains its original publication cycle. The flag is initialized/reset/cancelled to1 beside output_az0, publishes the exact signed32 inclusive +/-30000 expression beside held_az, and holds beside the public AZ during fault, start-while-busy, nonfinal busy and idle branches. Acceleration validity remains independently governed by the original branches. Default PRECHECKED_AZ_RANGE=0 callers select the original numeric expression; the native top enables1 and passes the matching public tuple flag. All full32-bit axes, original Q16 precision and64-bit arithmetic remain unchanged.

SOURCE_EQUIVALENCE_BASIS records every normalized edit and mechanically reverses the complete edit inventory to frozen v4. That establishes source scope and unchanged residual only. It does not prove correctness of the new predicate register or consumer replacement. Guard correctness instead relies on exact copied module bodies and the actual producer444003-cycle invariant plus full height-fusion3194862-cycle differential evidence, whose current sources, logs, receipts and successful completion02 root are separately rehashed in GUARD_REUSE_RECHECK. Original v8/v9 failed roots remain bound as actual failure1; their successful continuation/retry roots are distinct actual wait0 records.

Landing logic retains the exact v17 two-branch threshold distribution, default-off interface, same numeric1250 threshold and original FSM priorities. The same-value fallback fanout wire and previous-pose synthesis comment add no core state or cycle. A fresh candidate old/new/default full-state FSM miter, real fallback implication and all16-bit threshold values are required; the landing algebra statement covers hardware binary inputs and does not assert arbitrary X-state equivalence.

The already fresh v19 top13 may be reused only after exact source55, path-only driver derivation, original-v4 TB bytes, result/log hashes and actual compile/vvp/root exits are rechecked. Its documented private forces include gate readiness/counts, controller state/cancel and decoded RX/core dependencies; this is gate and wiring evidence. Producer/fusion tests use no DUT force or private preload, but the fusion component fixture accelerates timer/sample admission while retaining actual11000us integration and real math services. Neither component proof nor top13 establishes unforced full-flight behavior, real50MHz timing or installation acceptance.

SYN-only preparation retains the original B4 helper and v2 mapped/gain/port auditor hashes, clk50 FF checks, radio synchronizers, default XY1000/350 and18-port checks. The exact ten B3-relative source changes are checked before any vendor call. A fresh SYN and later complete real50MHz physical qualification are separate requirements; no vendor process is launched by this preparation.
'''
(O/'source_review.md').write_text(review,encoding='utf8',newline='\n')
write(O/'source_freeze.json',{'prepared_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'Final v19 functional input freeze for proof/SYN preparation; no physical qualification',
    'source_root':str(C),'source55':expected,'baseline_source55':before,'changed_files':list(transformations),
    'parent_v17_source55':composition['parents']['v17']['source55'],'parent_v9_source55':composition['parents']['v9']['source55'],
    'B3_relative_changes':changes,'B3_relative_change_count':10,'source_review_sha256':sha(O/'source_review.md'),
    'source_equivalence_basis_sha256':sha(O/'SOURCE_EQUIVALENCE_BASIS.json'),'composition_sha256':sha(O/'AZ_SOURCE_COMPOSITION.json'),
    'guard_binding_sha256':sha(O/'GUARD_REUSE_RECHECK.json'),'new_same_publication_predicate_bits':1,'legacy_output_cycle_change':0})

def one(text,a,b):
    assert text.count(a)==1,(a,text.count(a));return text.replace(a,b,1)

text=(P/'run_proofs.py').read_text(encoding='utf8').replace('v17','v19')
text=one(text,"assert not (D/'inputs.json').exists() and not (O/'PROOF_BINDING.json').exists()","assert D.is_dir() and not (D/'inputs.json').exists() and not (O/'PROOF_BINDING.json').exists()")
a=text.index("for n,t in basis['transformations'].items():");b=text.index("parent=read(P/'RESULT.json');",a)
text=text[:a]+"from validation_contract import verify_contract\ncontract=verify_contract()\n"+text[b:]
text=one(text,",D/'run_top13.py',P/",",O/'az_proofs/run_top13.py',P/")
text=one(text,"O/'SOURCE_EQUIVALENCE_BASIS.json',D/'flight_state_miter.v'","O/'SOURCE_EQUIVALENCE_BASIS.json',O/'validation_contract.py',O/'GUARD_REUSE_RECHECK.json',O/'RESULT.json',O/'az_proofs/inputs.json',D/'flight_state_miter.v'")
a=text.index("top=run('runner',");b=text.index("assert all(sha(Path(p))",a)
text=text[:a]+"top=read(O/'az_proofs/runner_exit.json');assert top['actual_p_wait']==0 and top['normal_wait_return']\nassert verify_contract()['passed']\n"+text[b:]
text=one(text,"sha(D/'runner_exit.json')","sha(O/'az_proofs/runner_exit.json')")
text=one(text,"sha(D/'top_safety_results.json')","sha(O/'az_proofs/top_safety_results.json')")
text=one(text,"(O/'PROOF_BINDING.json').write_text","(D/'CORE_FSM_RESULT.json').write_text")
text=one(text,"print(json.dumps(dict(passed=True,new_top13=13,FSM_miter=True,threshold_vectors=2097152,actual_top_runner_wait=0)))","print(json.dumps(dict(passed=True,exact_fresh_v19_top13_reused=13,FSM_miter=True,threshold_vectors=2097152,actual_top_runner_wait=top['actual_p_wait'])))")
text=one(text,"scope='New comparator/FSM old-new-default cycle proof, real fallback implication and original top13. Exact unchanged six controller inputs and ground43 separately rehashed; no physical or installation claim.'","guard_binding_sha256=contract['guard_binding_sha256'],new_same_publication_predicate_bits=1,legacy_output_cycle_change=0,scope='Fresh comparator/FSM old-new-default proof and real fallback implication, plus hash-checked already-fresh exact v19 top13. Exact AZ guard correctness is separately bound to GUARD_REUSE_RECHECK; reverse source reconstruction is not its correctness proof. No physical/full-flight/installation claim.'")
(O/'run_proofs.py').write_text(text,encoding='utf8',newline='\n')

for name in ['run_synthesis.py','audit_synthesis_only.py','seal_synthesis.py','launch_synthesis_hidden.py']:
    text=(P/name).read_text(encoding='utf8').replace('v17','v19')
    text=text.replace('len(h.EXPECTED_CHANGES)==7','len(h.EXPECTED_CHANGES)==10').replace('len(helper.EXPECTED_CHANGES)==7','len(helper.EXPECTED_CHANGES)==10')
    if name=='run_synthesis.py':
        text=one(text,"    assert not A.exists()","    from validation_contract import verify_contract\n    contract=verify_contract(check_proof=True)\n    assert contract['guard_binding_sha256']==read(O/'PROOF_BINDING.json')['guard_binding_sha256']\n    assert not A.exists()")
        text=one(text,"O/'SYNTHESIS_PREPARATION.json',helper_path","O/'SYNTHESIS_PREPARATION.json',O/'validation_contract.py',O/'GUARD_REUSE_RECHECK.json',O/'SOURCE_EQUIVALENCE_BASIS.json',O/'AZ_SOURCE_COMPOSITION.json',helper_path")
        text=one(text,"'source_sha256':expected,'original_B4_source55'","'guard_binding_sha256':contract['guard_binding_sha256'],'source_sha256':expected,'original_B4_source55'")
    elif name=='audit_synthesis_only.py':
        text=one(text,"def main():","def main():\n    from validation_contract import verify_contract\n    assert verify_contract(check_proof=True)['passed']")
        text=text.replace("'local_fanout_map2':new[n]","'composed_guard_landing_fanout_map2':new[n]")
        text=text.replace('Actual v19 local fanout synthesis versus v4','Actual v19 AZ guard and landing/fanout composition synthesis versus v4')
    elif name=='seal_synthesis.py':
        text=one(text,"root=read(O/'runner_exit.json');","from validation_contract import verify_contract\nassert verify_contract(check_proof=True)['passed']\nroot=read(O/'runner_exit.json');")
    (O/name).write_text(text,encoding='utf8',newline='\n')

text=(P/'verify_reused_bindings.py').read_text(encoding='utf8').replace('v17','v19')
text=one(text,"proof=read(O/'PROOF_BINDING.json');","from validation_contract import verify_contract\ncontract=verify_contract(check_proof=True)\nproof=read(O/'PROOF_BINDING.json');")
text=one(text,"'new_v19_proof_binding_sha256':sha(O/'PROOF_BINDING.json')","'guard_binding_sha256':contract['guard_binding_sha256'],'guard_contract_rechecked':True,'new_v19_proof_binding_sha256':sha(O/'PROOF_BINDING.json')")
(O/'verify_reused_bindings.py').write_text(text,encoding='utf8',newline='\n')
from validation_contract import verify_contract
assert verify_contract()['passed']
print(json.dumps({'prepared_functional_contract':True,'v4_changed_files':7,'B3_relative_changes':len(changes),'new_predicate_bits':1,'legacy_output_cycle_change':0,'vendor_launched':False}))
