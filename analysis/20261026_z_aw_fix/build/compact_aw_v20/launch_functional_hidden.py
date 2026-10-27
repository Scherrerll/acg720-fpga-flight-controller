"""Record a real root child wait for fresh v20 top13/integration; no vendor calls."""
from pathlib import Path
import datetime,hashlib,json,subprocess,sys
from validation_contract import verify_contract
O=Path(__file__).resolve().parent;R=O.parents[3];D=O/'proofs'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf8'))
write=lambda p,j:p.write_text(json.dumps(j,indent=2)+'\n',encoding='utf8',newline='\n')
utc=lambda:datetime.datetime.now(datetime.timezone.utc).isoformat()
contract=verify_contract();assert not D.exists() and not (O/'PROOF_BINDING.json').exists();D.mkdir()
runner=O/'run_proofs.py';command=[sys.executable,'-B','-X','utf8',str(runner)]
j={'command':command,'cwd':str(R),'started_utc':utc(),'runner_sha256':sha(runner),'supervisor_sha256':sha(Path(__file__)),'create_no_window':True,'stdin':'DEVNULL'}
with (D/'functional_runner.stdout.log').open('wb') as out,(D/'functional_runner.stderr.log').open('wb') as err:
    p=subprocess.Popen(command,cwd=R,stdin=subprocess.DEVNULL,stdout=out,stderr=err,creationflags=0x08000000)
    j['pid']=p.pid;write(D/'functional_runner_process.json',j);code=p.wait()
j.update(actual_p_wait=code,normal_wait_return=True,ended_utc=utc(),stdout_sha256=sha(D/'functional_runner.stdout.log'),stderr_sha256=sha(D/'functional_runner.stderr.log'))
write(D/'functional_runner_exit.json',j)
assert code==0,('Fresh functional root failed; original receipts/logs retained',code)
result=read(D/'RESULT.json');assert result['passed'] and result['source55']==contract['source55']
assert verify_contract()['passed'];reuse=read(O/'COMPONENT_REUSE_BINDING.json')
write(O/'PROOF_BINDING.json',{**result,'completed_utc':utc(),'actual_proof_runner_wait':code,'actual_top13_runner_wait':result['fresh_top13']['actual_root_wait'],
    'functional_root_exit_sha256':sha(D/'functional_runner_exit.json'),'component_binding_sha256':contract['component_binding_sha256'],
    'AZ_parent_binding_sha256':reuse['AZ']['parent_binding_sha256'],'VY_parent_binding_sha256':reuse['VY']['parent_binding_sha256'],
    'reused_core_FSM':reuse['reused_core_FSM'],'six_controller_dependencies':reuse['six_controller_dependencies'],'ground_current_inputs_rehashed':43,
    'scope':'New complete v20 source55: exact named parent components plus new merged wrapper, fresh complete original top13 and ordinary-input combined-guard integration. Old-new core FSM proof reused only for exact unchanged core/test inputs. No whole-source parent identity, physical timing or hardware acceptance claim.'})
assert verify_contract(check_proof=True)['passed']
print(json.dumps({'passed':True,'actual_functional_root_wait':code,'fresh_top13':13,'fresh_integration':True,'core_FSM_rerun':False,'proof_binding_sha256':sha(O/'PROOF_BINDING.json')}))
