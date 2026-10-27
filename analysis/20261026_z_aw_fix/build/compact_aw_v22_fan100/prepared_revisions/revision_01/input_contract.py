"""Read-only whole55 STD22 functional/SYN reuse and option-only candidate contract."""
from pathlib import Path
import hashlib,importlib.util,json,sys
sys.dont_write_bytecode=True
O=Path(__file__).resolve().parent;R=O.parents[3];STANDARD=O.parent/'compact_aw_v22'
C=R/'out/z_aw_fix_20261026/compact_aw_v22/canonical/source'
ROOT=R/'out/z_aw_fix_20261026/compact_aw_v22_fan100'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
read=lambda p:json.loads(Path(p).read_text(encoding='utf8'))
def parent_contract():
    spec=importlib.util.spec_from_file_location('fan100_same_source_STD22',STANDARD/'physical_input_contract.py')
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    return m.validate22(require_preparation=True)
def validate(require_binding=True):
    base=parent_contract();assert base['passed'] and len(base['source55'])==55
    assert base['B3_relative_change_count']==12 and base['fresh_controller_five_cases']==5
    assert base['original_attempt_root_actual_wait']==base['original_TEMP_alias_compile_actual_wait']==1
    assert base['actual_alias_retry_root_wait']==base['actual_completion_runner_wait']==0
    assert len(base['successful_fresh_exit_receipts'])==22 and base['legacy_public_output_cycle_change']==0
    assert (O/'source_freeze.json').read_bytes()==(STANDARD/'source_freeze.json').read_bytes()
    assert not (ROOT/'canonical').exists(),'Canonical source belongs only to STD22'
    assert not any((O/n).exists() for n in ['PROOF_BINDING.json','COMPONENT_REUSE_BINDING.json','VY_BINDING.json'])
    if require_binding:
        b=read(O/'SOURCE_REUSE_BINDING.json')
        assert b['passed'] and b['source55']==base['source55'] and b['parent_VG_sha256']==base['VG_sha256']
        assert b['canonical_source_root']==str(C) and b['standard_source_proof_origin']==str(STANDARD)
        for p,h in b['bound_inputs'].items():assert sha(p)==h,p
        assert b['standard_proof_binding_sha256']==sha(STANDARD/'PROOF_BINDING.json')
        assert b['guard_binding_sha256']==base['guard_binding_sha256']
    return base
def review_gate():
    gate=read(O/'SYN_REVIEW_GATE.json');prep=read(O/'SYNTHESIS_PREPARATION.json')
    assert gate['main_review_passed'] is True and gate['independent_agent_review_passed'] is True
    assert gate['preparation_sha256']==sha(O/'SYNTHESIS_PREPARATION.json')
    assert gate['source_reuse_binding_sha256']==sha(O/'SOURCE_REUSE_BINDING.json')
    assert gate['reviewed_scripts_sha256']==prep['scripts_sha256']
    for n,h in prep['scripts_sha256'].items():assert sha(O/n)==h,n
    return gate
