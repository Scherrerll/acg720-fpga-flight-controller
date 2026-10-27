"""Record the actual proof-runner child wait, including unsuccessful attempts."""
from pathlib import Path
import datetime,hashlib,json,subprocess,sys
O=Path(__file__).resolve().parent;P=O/'vy_proofs';P.mkdir(exist_ok=True)
attempt=sys.argv[1] if len(sys.argv)>1 else 'attempt01'
base=P/(attempt+'_supervisor');assert not base.with_suffix('.exit.json').exists()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
record=dict(started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),command=[sys.executable,'-B','-X','utf8',str(O/'run_vy_proofs.py'),attempt])
with base.with_suffix('.stdout.log').open('wb') as out,base.with_suffix('.stderr.log').open('wb') as err:
    child=subprocess.Popen(record['command'],cwd=O,stdin=subprocess.DEVNULL,stdout=out,stderr=err,creationflags=subprocess.CREATE_NO_WINDOW)
    record['pid']=child.pid;base.with_suffix('.process.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf8')
    code=child.wait()
record.update(actual_proof_supervisor_child_wait=code,normal_wait_return=True,ended_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    stdout_sha256=sha(base.with_suffix('.stdout.log')),stderr_sha256=sha(base.with_suffix('.stderr.log')),supervisor_script_sha256=sha(Path(__file__)),runner_sha256=sha(O/'run_vy_proofs.py'))
base.with_suffix('.exit.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf8')
if code==0:
    result=P/'RESULT.json';data=json.loads(result.read_text(encoding='utf8'))
    data['supervisor_exit_receipt']=str(base.with_suffix('.exit.json'));data['supervisor_exit_receipt_sha256']=sha(base.with_suffix('.exit.json'))
    data['actual_proof_supervisor_child_wait']=code;result.write_text(json.dumps(data,indent=2)+'\n',encoding='utf8')
print(json.dumps(record));sys.exit(code)
