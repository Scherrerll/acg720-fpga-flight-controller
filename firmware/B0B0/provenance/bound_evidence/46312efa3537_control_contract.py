from pathlib import Path
import hashlib,json,re
ROOT=Path(__file__).resolve().parent
FIX=ROOT/'fixture'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def verify():
    baseline=json.loads((ROOT/'baseline.json').read_text(encoding='utf8'))
    contract=json.loads((ROOT/'source_contract.json').read_text(encoding='utf8'))
    parent=Path(baseline['parent'])
    assert sha(parent/'qualification.json')==contract['parent_qualification_sha256']
    for name,digest in baseline['parent_sources'].items():
        if name.endswith(('.v','.vh','.cst','.sdc','.gprj','.tcl','.py')):
            assert (FIX/name).is_file(),('Inherited source missing',name)
            expected=contract['allowed_changes'].get(name,digest)
            assert sha(FIX/name)==expected,('Unqualified source changed',name)
            if name not in contract['allowed_changes']:
                assert sha(parent/'fixture'/name)==digest,('Frozen parent changed',name)
    for name,digest in contract['new_sources'].items():assert sha(FIX/name)==digest
    reference=(ROOT/'reference/flight_core_b0ae.v').read_text(encoding='utf8')
    assert sha(ROOT/'reference/flight_core_b0ae.v')==contract['reference_core_sha256']
    assert reference.replace('module flight_core_b0ae #(','module flight_core #(',1)==(parent/'fixture/core/flight_core.v').read_text(encoding='utf8')
    original_project=(parent/'fixture/acg720_ano_port.gprj').read_text(encoding='utf8')
    current=(FIX/'acg720_ano_port.gprj').read_text(encoding='utf8')
    assert current.replace('<File path="core/height_loss_fallback.v" type="file.verilog" enable="1"/>\n','')==original_project
    assert (FIX/'build.tcl').read_text(encoding='utf8').replace('0000B0B0','0000B0AE').replace('-replicate_resources 1','-replicate_resources 0').replace('-place_option 2','-place_option 3')==(parent/'fixture/build.tcl').read_text(encoding='utf8')
    delta=json.loads((ROOT/'diagnostic_delta.json').read_text())
    current_reference=Path(delta['reference'])
    for name,hashes in delta['files'].items():
        assert sha(current_reference/'fixture'/name)==hashes['reference_sha256']
        assert sha(FIX/name)==hashes['candidate_sha256']
    anchor=json.loads((ROOT/'published_anchor_delta.json').read_text())
    anchor_reference=Path(anchor['reference'])
    assert sha(ROOT/'hardware/published_anchor.patch')==anchor['reviewed_patch_sha256']
    for name,hashes in anchor['files'].items():
        assert sha(anchor_reference/'fixture'/name)==hashes['reference_sha256']
        assert sha(FIX/name)==hashes['candidate_sha256']
    assert (ROOT/'DO_NOT_PROGRAM').is_file()
    return dict(passed=True,parent_unmodified=True,hardware_accessed=False)
if __name__=='__main__':print(json.dumps(verify()))
