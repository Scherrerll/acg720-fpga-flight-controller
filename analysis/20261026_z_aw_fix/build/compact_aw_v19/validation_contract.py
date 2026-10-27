"""Read-only v19 source, guard-proof and fresh-top contract checks. No tools launched."""
from pathlib import Path
import hashlib,json

O=Path(__file__).resolve().parent;R=O.parents[3]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf8'))
norm=lambda s:s.replace('\r\n','\n')

def check_wait(path,code=0):
    j=read(path);assert j['normal_wait_return'] and j['actual_p_wait']==code,path
    return j

def verify_contract(check_proof=False):
    freeze=read(O/'source_freeze.json');expected=freeze['source55'];before=freeze['baseline_source55']
    C=Path(freeze['source_root']);OLD=R/'out/z_aw_fix_20261026/compact_aw_v4/canonical/source'
    assert len(expected)==len(before)==55
    assert {n:sha(C/n) for n in expected}==expected
    assert {n:sha(OLD/n) for n in before}==before
    assert sha(O/'source_review.md')==freeze['source_review_sha256']
    assert sha(O/'SOURCE_EQUIVALENCE_BASIS.json')==freeze['source_equivalence_basis_sha256']
    assert sha(O/'AZ_SOURCE_COMPOSITION.json')==freeze['composition_sha256']
    assert sha(O/'GUARD_REUSE_RECHECK.json')==freeze['guard_binding_sha256']
    composition=read(O/'AZ_SOURCE_COMPOSITION.json');assert composition['source55']==expected
    assert composition['parents']['v4']['source55']==before
    for parent in composition['parents'].values():
        root=Path(parent['root']);assert {n:sha(root/n) for n in parent['source55']}==parent['source55']
        assert sha(Path(parent['freeze_path']))==parent['freeze_sha256']
    changed=[n for n in expected if expected[n]!=before[n]]
    basis=read(O/'SOURCE_EQUIVALENCE_BASIS.json')
    assert sorted(changed)==sorted(basis['transformations']) and len(changed)==7
    for n,t in basis['transformations'].items():
        old=norm((OLD/n).read_text(encoding='utf8'));new=norm((C/n).read_text(encoding='utf8'))
        assert sha(OLD/n)==t['baseline_sha256'] and sha(C/n)==t['candidate_sha256']
        lines=new.splitlines(True)
        for e in reversed(t['normalized_line_edit_spans']):
            assert ''.join(lines[e['new_start']:e['new_end']])==e['new_text']
            lines[e['new_start']:e['new_end']]=e['old_text'].splitlines(True)
        assert ''.join(lines)==old
    assert basis['scope_delimitation']['reverse_reconstruction_is_not_guard_correctness_proof'] is True
    assert basis['guard_contract']['new_same_publication_predicate_bits']==1
    assert basis['guard_contract']['legacy_output_cycle_change']==0
    V9=Path(composition['parents']['v9']['root']);V17=Path(composition['parents']['v17']['root'])
    for n in ['position/pose_time_adapter.v','mtf_xyz_navigation_control.v','position/mtf_shared_height_fusion.v']:
        assert (C/n).read_bytes()==(V9/n).read_bytes()
    a=b' reg previous_pose_valid=0;';b=b' reg previous_pose_valid /* synthesis syn_maxfan = 10 */ =0;'
    assert (V9/'acg720_ano_port.v').read_bytes().count(a)==1
    assert (C/'acg720_ano_port.v').read_bytes()==(V9/'acg720_ano_port.v').read_bytes().replace(a,b)
    for n in composition['retained_v17_core_byte_exact']:assert (C/n).read_bytes()==(V17/n).read_bytes()
    b3=read(R/'firmware/B0B3/qualification.json')['source_sha256']
    assert len(b3)==55 and {n:sha(R/'firmware/B0B3/source'/n) for n in b3}==b3
    b3changes={n:h for n,h in expected.items() if h!=b3[n]}
    assert len(b3changes)==10 and b3changes==freeze['B3_relative_changes']
    guard=read(O/'GUARD_REUSE_RECHECK.json')
    for field in ['v8','v9']:
        assert sha(Path(guard[f'{field}_results_path']))==guard[f'{field}_results_sha256']
        assert read(Path(guard[f'{field}_results_path']))['passed']
    for x in guard['actual_producer_fusion_stages']:
        assert sha(Path(x['receipt_path']))==x['receipt_sha256'] and sha(Path(x['log_path']))==x['log_sha256']
        j=check_wait(Path(x['receipt_path']));assert j['log_sha256']==x['log_sha256']
    for x in guard['completion02_reuse_links']:
        assert sha(Path(x['path']))==x['sha256']
        assert sha(Path(x['receipt']))==x['receipt_sha256'] and sha(Path(x['log']))==x['log_sha256']
    for label,x in guard['roots'].items():
        assert sha(Path(x['path']))==x['sha256']
        j=check_wait(Path(x['path']),1 if 'failed_root' in label else 0)
        assert sha(Path(x['runner_path']))==x['runner_sha256']
        for stream in ['stdout','stderr']:
            assert sha(Path(x['path']).parent/f'runner.{stream}.log')==j[f'{stream}_sha256']
    for x in guard['v9_stages']:
        p=Path(x['receipt_path']);assert sha(p)==x['receipt_sha256'];j=check_wait(p)
        name=p.name.replace('_exit.json','')
        for stream in ['stdout','stderr']:assert sha(p.parent/f'{name}.{stream}.log')==j[f'{stream}_sha256']
    for n,h in guard['same_guard_dependencies'].items():assert sha(C/n)==h
    for n,h in guard['six_controller_dependencies'].items():assert sha(C/n)==h
    assert guard['scope']['producer_and_fusion_no_DUT_force_or_private_preload']
    az=read(O/'RESULT.json');D=O/'az_proofs'
    assert az['passed'] and az['source55']==expected and az['source55_unchanged']
    top=az['top13'];assert top['passed'] and top['cases']==13 and top['original_v4_tb_byte_exact']
    assert top['actual_root_p_wait']==top['compile_actual_returncode']==top['vvp_actual_returncode']==0
    for p,h in top['receipts'].items():assert sha(Path(p))==h
    for p,h in read(D/'inputs.json')['bound_files'].items():assert sha(Path(p))==h
    root=check_wait(D/'runner_exit.json')
    for stream in ['stdout','stderr']:assert sha(D/f'runner.{stream}.log')==root[f'{stream}_sha256']
    for name in ['compile','vvp']:
        j=read(D/f'{name}_exit.json');assert j['normal_return'] and j['actual_completedprocess_returncode']==0
    assert sha(D/'top_safety_tb.v')==sha(O.parent/'v4_release_proofs/top_safety_tb.v')==top['top_tb_sha256']
    original=(O.parent/'compact_aw_v17/proofs/run_top13.py').read_bytes()
    assert (D/'run_top13.py').read_bytes()==original.replace(b'compact_aw_v17/canonical',b'compact_aw_v19/canonical')
    result={'passed':True,'source55':expected,'baseline_source55':before,'B3_relative_changes':b3changes,
            'guard_binding_sha256':sha(O/'GUARD_REUSE_RECHECK.json'),'fresh_top13_result_sha256':sha(O/'RESULT.json'),
            'fresh_top13_root_exit_sha256':sha(D/'runner_exit.json'),'scope':'Complete source edit reconstruction; guard correctness bound separately to actual saved producer/fusion proofs. Fresh exact candidate top13 checked with inherited force limitations.'}
    if check_proof:
        proof=read(O/'PROOF_BINDING.json');assert proof['passed'] and proof['source55']==expected
        assert proof['guard_binding_sha256']==result['guard_binding_sha256']
        assert proof['actual_proof_runner_wait']==0 and proof['actual_top13_runner_wait']==0
        assert sha(O/'proofs/functional_runner_exit.json')==proof['functional_root_exit_sha256']
        root=check_wait(O/'proofs/functional_runner_exit.json')
        assert sha(Path(root['command'][-1]))==root['runner_sha256']
        for stream in ['stdout','stderr']:assert sha(O/'proofs'/f'functional_runner.{stream}.log')==root[f'{stream}_sha256']
        assert sha(O/'proofs/inputs.json')==proof['inputs_sha256']
        for p,h in read(O/'proofs/inputs.json')['bound_files'].items():assert sha(Path(p))==h
        for name in ['fsm_compile','fsm_vvp']:
            p=O/'proofs'/f'{name}_exit.json';j=check_wait(p)
            for stream in ['stdout','stderr']:assert sha(p.parent/f'{name}.{stream}.log')==j[f'{stream}_sha256']
        assert sha(O/'proofs/CORE_FSM_RESULT.json')==proof['core_fsm_result_sha256']
        assert read(O/'proofs/CORE_FSM_RESULT.json')['passed']
        result['proof_binding_sha256']=sha(O/'PROOF_BINDING.json')
    return result
