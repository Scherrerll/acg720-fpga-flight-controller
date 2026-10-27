"""Record actual isolated proof-runner wait; never run vendor or hardware tools."""
from pathlib import Path
import datetime,hashlib,json,subprocess,sys
O=Path(__file__).resolve().parent
assert not (O/'root_exit.json').exists()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
command=[sys.executable,'-B','-X','utf8',str(O/'run_proof.py')]
record=dict(command=command,cwd=str(O),started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),runner_sha256=sha(O/'run_proof.py'),supervisor_script_sha256=sha(Path(__file__)))
with (O/'root.stdout.log').open('wb') as out,(O/'root.stderr.log').open('wb') as err:
    p=subprocess.Popen(command,cwd=O,stdin=subprocess.DEVNULL,stdout=out,stderr=err,creationflags=subprocess.CREATE_NO_WINDOW)
    record['pid']=p.pid;(O/'root_process.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf8')
    code=p.wait()
record.update(normal_wait_return=True,actual_p_wait=code,ended_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),stdout_sha256=sha(O/'root.stdout.log'),stderr_sha256=sha(O/'root.stderr.log'))
(O/'root_exit.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf8')
if code==0:
    result=O/'RESULT.json';data=json.loads(result.read_text(encoding='utf8'))
    data['actual_root_wait']=code;data['exit_receipts']['root_exit.json']=sha(O/'root_exit.json')
    result.write_text(json.dumps(data,indent=2)+'\n',encoding='utf8')
print(json.dumps(record));sys.exit(code)
