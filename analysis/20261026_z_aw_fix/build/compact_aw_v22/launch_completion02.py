"""Record the real completion coordinator child wait, preserving old root1."""
from pathlib import Path
import datetime,hashlib,json,os,subprocess,sys
O=Path(__file__).resolve().parent;D=O/'proofs_completion02';runner=O/'run_completion02.py';D.mkdir()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
command=[sys.executable,'-B','-X','utf8',str(runner)];j={'command':command,'supervisor_pid':os.getpid(),'supervisor_sha256':sha(Path(__file__)),'runner_sha256':sha(runner),'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
with (D/'functional_runner.stdout.log').open('wb') as out,(D/'functional_runner.stderr.log').open('wb') as err:
 p=subprocess.Popen(command,stdout=out,stderr=err,stdin=subprocess.DEVNULL,creationflags=subprocess.CREATE_NO_WINDOW);j['pid']=p.pid;(D/'functional_runner_process.json').write_text(json.dumps(j,indent=2)+'\n');code=p.wait()
j.update(normal_wait_return=True,actual_p_wait=code,ended_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),stdout_sha256=sha(D/'functional_runner.stdout.log'),stderr_sha256=sha(D/'functional_runner.stderr.log'))
(D/'functional_runner_exit.json').write_text(json.dumps(j,indent=2)+'\n');print(json.dumps({'original_attempt_root_actual_wait':1,'actual_completion_root_wait':code}));raise SystemExit(code)
