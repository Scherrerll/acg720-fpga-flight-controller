"""Rehash actual parent result/root receipts, exact controller inputs and unchanged ground tests."""
from pathlib import Path
import datetime,hashlib,json
O=Path(__file__).resolve().parent;R=O.parents[3];C=R/'out/z_aw_fix_20261026/compact_aw_v15/canonical/source';P=O.parent/'v4_release_proofs'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf8'))
proof=read(O/'PROOF_BINDING.json');assert proof['passed'] and proof['actual_proof_runner_wait']==0
parent=read(P/'RESULT.json');inputs=read(P/'inputs.json')
assert sha(P/'RESULT.json')==proof['parent_proof_sha256'] and sha(P/'inputs.json')==parent['inputs_sha256']
controller=Path(inputs['reused_controller_proofs']);results=read(controller/'results.json');exit=read(controller/'runner_exit.json')
assert sha(controller/'results.json')==inputs['reused_results_sha256']
assert results['passed'] and exit['normal_wait_return'] and exit['actual_p_wait']==0
assert results['five']['passed'] and results['five']['completed']==5 and results['boundary']['passed'] and results['boundary']['completed']==2 and results['contention']['passed']
dependencies=inputs['exact_dependencies'];assert len(dependencies)==6
assert all(sha(C/n)==parent['source55'][n]==results['source55'][n]==digest for n,digest in dependencies.items())
ground=R/'ground/B0B4/test_results/verification.json';g=read(ground)
assert sha(ground)==inputs['ground_verification_sha256'] and g['result']=='PASS' and len(g['input_sha256'])==43
for name,digest in g['input_sha256'].items():
    p=R/name
    assert p.resolve().is_relative_to(R) and not p.name.lower().startswith('.env') and not p.name.lower().endswith('.env') and '.env' not in [s.lower() for s in p.suffixes]
    assert sha(p)==digest
receipt={'verified_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'passed':True,'source55':proof['source55'],
    'scope':'Rehashed original successful controller result/root and exact six source dependencies, parent v4 binding and all43 ground test inputs. Does not rerun five cases, FRAC boundary, arbitration or ground tests; trace/log hashes remain the original parent proof records.',
    'new_v15_proof_binding_sha256':sha(O/'PROOF_BINDING.json'),'parent_binding_sha256':sha(P/'RESULT.json'),
    'parent_controller_results_sha256':sha(controller/'results.json'),'parent_controller_runner_exit_sha256':sha(controller/'runner_exit.json'),
    'reused_controller_actual_root_wait':exit['actual_p_wait'],'six_exact_controller_dependencies':dependencies,
    'ground_verification_sha256':sha(ground),'ground_current_inputs_rehashed':43}
dest=O/'REUSED_BINDINGS_RECHECK.json';assert not dest.exists();dest.write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf8')
print(json.dumps({'passed':True,'six_controller_dependencies_unchanged':True,'ground_inputs_rehashed':43,'tests_rerun':False}))
