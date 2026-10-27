"""Record actual supervised SYN-only runner wait; no PNR or hardware controls."""
from pathlib import Path
import datetime,hashlib,json,os,subprocess,sys
sys.dont_write_bytecode=True
O=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
from input_contract import validate,review_gate
validate();review_gate()
assert not any((O/n).exists() for n in ['runner_process.json','runner_exit.json','runner.stdout.log','runner.stderr.log'])
command=[sys.executable,'-B','-X','utf8',str(O/'run_synthesis.py')]
j={'command':command,'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'supervisor_pid':os.getpid(),'runner_sha256':sha(O/'run_synthesis.py'),'supervisor_sha256':sha(Path(__file__))}
with (O/'runner.stdout.log').open('xb') as out,(O/'runner.stderr.log').open('xb') as err:
    p=subprocess.Popen(command,stdout=out,stderr=err,stdin=subprocess.DEVNULL,creationflags=subprocess.CREATE_NO_WINDOW);j['pid']=p.pid
    (O/'runner_process.json').write_text(json.dumps(j,indent=2)+'\n',encoding='utf8');code=p.wait()
j.update(actual_p_wait=code,normal_wait_return=True,ended_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),stdout_sha256=sha(O/'runner.stdout.log'),stderr_sha256=sha(O/'runner.stderr.log'))
(O/'runner_exit.json').write_text(json.dumps(j,indent=2)+'\n',encoding='utf8');raise SystemExit(code)
