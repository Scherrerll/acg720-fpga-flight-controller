"""Independent hidden proof supervisor; preserves genuine final p.wait."""
from pathlib import Path
import datetime,hashlib,json,os,subprocess,sys
O=Path(__file__).resolve().parent;D=O/'proofs';D.mkdir(exist_ok=True)
assert not (D/'runner_process.json').exists() and not (D/'runner_exit.json').exists()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
command=[sys.executable,'-B','-u',str(O/'run_proofs.py')]
rec={'command':command,'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'parent_pid':os.getpid(),'runner_sha256':sha(O/'run_proofs.py'),'create_no_window':True}
with (D/'runner.stdout.log').open('wb') as so,(D/'runner.stderr.log').open('wb') as se:
    p=subprocess.Popen(command,cwd=D,stdin=subprocess.DEVNULL,stdout=so,stderr=se,creationflags=subprocess.CREATE_NO_WINDOW,close_fds=True)
    rec['pid']=p.pid;(D/'runner_process.json').write_text(json.dumps(rec,indent=2)+'\n');code=p.wait()
rec.update(actual_p_wait=code,normal_wait_return=True,ended_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),stdout_sha256=sha(D/'runner.stdout.log'),stderr_sha256=sha(D/'runner.stderr.log'))
(D/'runner_exit.json').write_text(json.dumps(rec,indent=2)+'\n');raise SystemExit(code)
