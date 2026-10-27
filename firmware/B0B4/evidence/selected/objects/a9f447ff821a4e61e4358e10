"""Read-only complete v20 source/component/fresh-proof contract; no vendor calls."""
from pathlib import Path
import hashlib,json
O=Path(__file__).resolve().parent;R=O.parents[3]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf8'))

def verify_contract(check_proof=False):
    f=read(O/'source_freeze.json');expected=f['source55'];C=Path(f['source_root']);c=read(O/'SOURCE_COMPOSITION.json')
    assert len(expected)==55 and {n:sha(C/n) for n in expected}==expected==c['source55']
    for name,key in [('source_review.md','source_review_sha256'),('SOURCE_EQUIVALENCE_BASIS.json','source_equivalence_basis_sha256'),('SOURCE_COMPOSITION.json','composition_sha256')]:assert sha(O/name)==f[key]
    reuse=read(O/'COMPONENT_REUSE_BINDING.json');assert reuse['passed'] and reuse['source55']==expected
    for p,h in reuse['bound_inputs'].items():assert sha(Path(p))==h,p
    assert reuse['limitations']['no_full_source_parent_identity_claim'] and reuse['limitations']['new_private_predicate_bits']==2
    assert expected!=c['parents']['v18']['source55'] and expected!=c['parents']['v19']['source55']
    for n,p in c['component_files'].items():assert sha(C/n)==p['sha256']==c['parents'][p['parent']]['source55'][n]
    for n,h in c['retained_core_byte_exact'].items():assert sha(C/n)==h
    for n,edits in c['shared_VY_edits_over_v19'].items():
        s=(C/n).read_text(encoding='utf8')
        for a,b in reversed(edits):assert s.count(b)==1;s=s.replace(b,a,1)
        assert s==(Path(c['parents']['v19']['root'])/n).read_text(encoding='utf8')
    for n,edits in c['shared_AZ_edits_over_v18'].items():
        s=(C/n).read_text(encoding='utf8')
        for a,b in reversed(edits):assert s.count(b)==1;s=s.replace(b,a,1)
        assert s==(Path(c['parents']['v18']['root'])/n).read_text(encoding='utf8')
    basis=read(O/'SOURCE_EQUIVALENCE_BASIS.json');oldroot=Path(c['parents']['v4']['root'])
    assert basis['new_private_same_publication_predicate_bits']==2 and basis['legacy_public_output_cycle_change']==0
    assert len(basis['transformations'])==9 and basis['baseline_source55']==f['baseline_source55']
    for n,t in basis['transformations'].items():
        lines=(C/n).read_text(encoding='utf8').splitlines(True)
        for e in reversed(t['normalized_line_edit_spans']):
            assert ''.join(lines[e['new_start']:e['new_end']])==e['new_text']
            lines[e['new_start']:e['new_end']]=e['old_text'].splitlines(True)
        assert ''.join(lines)==(oldroot/n).read_text(encoding='utf8')
    b3=read(R/'firmware/B0B3/qualification.json')['source_sha256']
    assert {n:sha(R/'firmware/B0B3/source'/n) for n in b3}==b3
    changes={n:h for n,h in expected.items() if h!=b3[n]};assert len(changes)==12 and changes==f['B3_relative_changes']
    nav=(C/'mtf_xyz_navigation_control.v').read_text(encoding='utf8');top=(C/'acg720_ano_port.v').read_text(encoding='utf8')
    assert 'PRECHECKED_AZ_RANGE=0,PRECHECKED_INPUT_VELOCITY=0' in nav
    assert '.PRECHECKED_AZ_RANGE(1),.PRECHECKED_INPUT_VELOCITY(1)) native_navigation(' in top
    assert '.az_range_ok(converted_az_range_ok)' in top and '.velocity_range_ok(mtf_velocity_range_ok)' in top
    out={'passed':True,'source55':expected,'baseline_source55':f['baseline_source55'],'B3_relative_changes':changes,
         'guard_binding_sha256':sha(O/'COMPONENT_REUSE_BINDING.json'),'component_binding_sha256':sha(O/'COMPONENT_REUSE_BINDING.json'),
         'new_private_same_publication_predicate_bits':2,'legacy_public_output_cycle_change':0,'no_full_source_parent_identity_claim':True}
    if check_proof:
        p=read(O/'PROOF_BINDING.json');assert p['passed'] and p['source55']==expected and p['guard_binding_sha256']==out['guard_binding_sha256']
        assert p['actual_proof_runner_wait']==0 and p['fresh_top13']['actual_root_wait']==0
        assert p['new_private_same_publication_predicate_bits']==2 and p['legacy_public_output_cycle_change']==0
        D=O/'proofs';root=read(D/'functional_runner_exit.json')
        assert root['normal_wait_return'] and root['actual_p_wait']==0
        assert sha(D/'functional_runner_exit.json')==p['functional_root_exit_sha256']
        assert sha(Path(root['command'][-1]))==root['runner_sha256']
        for stream in ['stdout','stderr']:assert sha(D/f'functional_runner.{stream}.log')==root[f'{stream}_sha256']
        for item in p['fresh_actual_exit_receipts']:
            j=read(Path(item['path']));assert sha(Path(item['path']))==item['sha256']
            assert j[item['actual_wait_field']]==0 and j[item['normal_field']]
        for path,h in read(D/'inputs.json')['bound_inputs'].items():assert sha(Path(path))==h
        assert sha(D/'inputs.json')==p['inputs_sha256']
        assert sha(D/'top13/top_safety_tb.v')==sha(O.parent/'v4_release_proofs/top_safety_tb.v')
        for name in ['integration_compile','integration_vvp']:
            j=read(D/f'{name}_exit.json');assert j['actual_p_wait']==0 and j['normal_wait_return']
            for stream in ['stdout','stderr']:assert sha(D/f'{name}.{stream}.log')==j[f'{stream}_sha256']
        top_root=read(D/'top13_runner_exit.json')
        for stream in ['stdout','stderr']:assert sha(D/f'top13_runner.{stream}.log')==top_root[f'{stream}_sha256']
        out['proof_binding_sha256']=sha(O/'PROOF_BINDING.json')
    return out

def verify_syn_review():
    """Main creates this gate only after its review and another agent's real independent review."""
    gate=read(O/'SYN_REVIEW_GATE.json');assert gate['main_review_passed'] and gate['independent_agent_review_passed']
    assert gate['source_freeze_sha256']==sha(O/'source_freeze.json') and gate['proof_binding_sha256']==sha(O/'PROOF_BINDING.json')
    for n in ['run_synthesis.py','audit_synthesis_only.py','seal_synthesis.py','launch_synthesis_hidden.py','validation_contract.py']:
        assert gate['reviewed_scripts_sha256'][n]==sha(O/n)
    return gate
