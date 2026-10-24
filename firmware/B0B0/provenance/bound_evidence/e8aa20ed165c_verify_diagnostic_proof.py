from pathlib import Path
import json,hashlib
ROOT=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def verify_original():
    folder=ROOT/'hardware/diagnostic_reset_proof'
    bundle=json.loads((folder/'proof_bundle.json').read_text())
    assert bundle['passed'] is True
    artifacts=bundle['study_artifacts_sha256']
    required={'proof.json','simulation.log','full_top.proof.json','full_top_acceptance.log','proposed.patch','acg720_ano_port.proposed.v','mtf_xyz_navigation_control.proposed.v','prove.py','full_top.py','check_packets.py','banks.v','tb.v','full_top_tb.v','full_proposed.v'}
    assert required<=set(artifacts)
    for name,digest in artifacts.items():
        p=(folder/name).resolve()
        assert p.is_relative_to(folder.resolve()) and p.is_file()
        assert sha(p)==digest,('Diagnostic artifact changed',name)
    for name,digest in bundle['original_dependencies_sha256'].items():
        assert sha(Path(name))==digest,('Original dependency changed',name)
    bank=json.loads((folder/'proof.json').read_text())
    full=json.loads((folder/'full_top.proof.json').read_text())
    assert bank['passed'] is True and bank['cycles']==50000
    assert full['passed'] is True and full['accepted_bytes']==1136
    assert full['checksums_verified'] is True and full['navigation_payload_changed'] is True
    assert full['packet_counts']=={k:2 for k in ['A579','A57A','A580','A581','A582','A583']}
    assert full['source_sha256']==bundle['original_dependencies_sha256']
    delta=json.loads((ROOT/'diagnostic_delta.json').read_text())
    assert not delta['full_top_proof_pending']
    assert sha(folder/'proposed.patch')==delta['reviewed_patch_sha256']
    for name,proposal in [('acg720_ano_port.v','acg720_ano_port.proposed.v'),('mtf_xyz_navigation_control.v','mtf_xyz_navigation_control.proposed.v')]:
        expected=delta['files'][name]['candidate_sha256']
        assert sha(ROOT/'fixture'/name)==sha(folder/proposal)==expected
    return {'passed':True,'scope':'ORIGINAL-source bank and actual dual-top UART simulation evidence. This is not a current patched-core full-top simulation PASS.'}
def verify():
    original=verify_original()
    from diagnostic_context_bridge import verify as verify_bridge
    bridge=verify_bridge()
    return dict(passed=True,original=original,compositional_bridge=bridge,current_full_top_simulation_passed=False)
if __name__=='__main__':print(json.dumps(verify()))
