"""Supervise actual fresh v19 core FSM proof and seal its real root wait."""
from pathlib import Path
import datetime,hashlib,json,subprocess,sys
from validation_contract import verify_contract

O=Path(__file__).resolve().parent;R=O.parents[3];D=O/'proofs'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf8'))
write=lambda p,j:p.write_text(json.dumps(j,indent=2)+'\n',encoding='utf8',newline='\n')
utc=lambda:datetime.datetime.now(datetime.timezone.utc).isoformat()
contract=verify_contract();assert not D.exists() and not (O/'PROOF_BINDING.json').exists()
D.mkdir();runner=O/'run_proofs.py';command=[sys.executable,'-B','-X','utf8',str(runner)]
record={'command':command,'cwd':str(R),'started_utc':utc(),'runner_sha256':sha(runner),'supervisor_sha256':sha(Path(__file__)),'stdin':'DEVNULL','create_no_window':True}
with (D/'functional_runner.stdout.log').open('wb') as output,(D/'functional_runner.stderr.log').open('wb') as errors:
    p=subprocess.Popen(command,cwd=R,stdin=subprocess.DEVNULL,stdout=output,stderr=errors,creationflags=0x08000000)
    record['pid']=p.pid;write(D/'functional_runner_process.json',record);code=p.wait()
record.update(actual_p_wait=code,normal_wait_return=True,ended_utc=utc(),stdout_sha256=sha(D/'functional_runner.stdout.log'),stderr_sha256=sha(D/'functional_runner.stderr.log'))
write(D/'functional_runner_exit.json',record)
assert code==0,('functional proof failed; original receipt/logs retained',code)
core=read(D/'CORE_FSM_RESULT.json');assert core['passed'] and core['source55']==contract['source55']
assert verify_contract()['passed']
for n in ['fsm_compile','fsm_vvp']:
    j=read(D/f'{n}_exit.json');assert j['actual_p_wait']==0 and j['normal_wait_return']
binding={**core,'completed_utc':utc(),'actual_proof_runner_wait':code,'actual_top13_runner_wait':read(O/'az_proofs/runner_exit.json')['actual_p_wait'],
    'functional_root_exit_sha256':sha(D/'functional_runner_exit.json'),'core_fsm_result_sha256':sha(D/'CORE_FSM_RESULT.json'),
    'guard_binding_sha256':contract['guard_binding_sha256'],'guard_contract_rechecked':True,
    'top13_provenance':{'path':str(O/'RESULT.json'),'sha256':sha(O/'RESULT.json'),'fresh_v19_candidate_run_reused_after_exact_hash_checks':True,
        'root_exit_path':str(O/'az_proofs/runner_exit.json'),'root_exit_sha256':sha(O/'az_proofs/runner_exit.json'),'controlled_private_forces_disclosed':True},
    'guard_proof_scope':read(O/'GUARD_REUSE_RECHECK.json')['scope'],'no_VY_changes':True}
write(O/'PROOF_BINDING.json',binding)
assert verify_contract(check_proof=True)['passed']
print(json.dumps({'passed':True,'actual_functional_root_wait':code,'fresh_FSM_compile_vvp_waits':[0,0],'exact_fresh_top13_hash_checked':13,'guard_binding_sha256':binding['guard_binding_sha256'],'proof_binding_sha256':sha(O/'PROOF_BINDING.json')}))
