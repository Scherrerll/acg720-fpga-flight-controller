"""Recheck component, exact-six controller and43 ground dependencies; no reruns."""
from pathlib import Path
import datetime,hashlib,json
from validation_contract import verify_contract
O=Path(__file__).resolve().parent;R=O.parents[3]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf8'))
contract=verify_contract(check_proof=True);reuse=read(O/'COMPONENT_REUSE_BINDING.json');C=Path(read(O/'source_freeze.json')['source_root'])
six=reuse['six_controller_dependencies'];assert len(six)==6 and all(sha(C/n)==h for n,h in six.items())
results=read(Path(reuse['controller_results_path']));root=read(Path(reuse['controller_root_path']))
assert sha(Path(reuse['controller_results_path']))==reuse['controller_results_sha256']
assert results['passed'] and root['normal_wait_return'] and root['actual_p_wait']==0
ground=R/'ground/B0B4/test_results/verification.json';g=read(ground);assert sha(ground)==reuse['ground_verification_sha256'] and g['result']=='PASS' and len(g['input_sha256'])==43
for name,h in g['input_sha256'].items():assert sha(R/name)==h
record={'verified_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'passed':True,'source55':contract['source55'],
    'new_v20_proof_binding_sha256':sha(O/'PROOF_BINDING.json'),'guard_binding_sha256':contract['guard_binding_sha256'],'component_reuse_binding_sha256':sha(O/'COMPONENT_REUSE_BINDING.json'),
    'six_exact_controller_dependencies':six,'controller_actual_root_wait':root['actual_p_wait'],'ground_verification_sha256':sha(ground),'ground_current_inputs_rehashed':43,
    'scope':'Rehashed named parent components, unchanged-six controller and43 ground inputs. New v20 wrapper/top is separately tested; no complete-parent source identity, repeated core FSM or ground run claimed.'}
dest=O/'REUSED_BINDINGS_RECHECK.json';assert not dest.exists();dest.write_text(json.dumps(record,indent=2)+'\n',encoding='utf8',newline='\n')
print(json.dumps({'passed':True,'six_controller_dependencies':6,'ground_inputs':43,'tests_rerun':False,'binding_sha256':sha(dest)}))
