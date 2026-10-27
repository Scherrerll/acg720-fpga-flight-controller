"""Record actual v21 proof-runner child wait. No vendor tool is started."""
from pathlib import Path
import datetime,hashlib,json,subprocess,sys
O=Path(__file__).resolve().parent
assert not (O/'proof_runner_exit.json').exists()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
record=dict(command=[sys.executable,'-B','-X','utf8',str(O/'run_proofs.py')],cwd=str(O),started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),runner_sha256=sha(O/'run_proofs.py'),supervisor_script_sha256=sha(Path(__file__)))
with (O/'proof_runner.stdout.log').open('wb') as out,(O/'proof_runner.stderr.log').open('wb') as err:
    p=subprocess.Popen(record['command'],cwd=O,stdin=subprocess.DEVNULL,stdout=out,stderr=err,creationflags=subprocess.CREATE_NO_WINDOW)
    record['pid']=p.pid;(O/'proof_runner_process.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf8');code=p.wait()
record.update(normal_wait_return=True,actual_p_wait=code,ended_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),stdout_sha256=sha(O/'proof_runner.stdout.log'),stderr_sha256=sha(O/'proof_runner.stderr.log'))
(O/'proof_runner_exit.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf8')
if code==0:
    result=O/'proofs/RESULT.json';data=json.loads(result.read_text(encoding='utf8'));data['actual_proof_runner_wait']=code;data['root_exit_sha256']=sha(O/'proof_runner_exit.json')
    result.write_text(json.dumps(data,indent=2)+'\n',encoding='utf8')
print(json.dumps(record));sys.exit(code)
