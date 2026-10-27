"""Independent hidden supervisor; preserve real root verification wait."""
from pathlib import Path
import datetime,hashlib,json,os,subprocess,sys
O=Path(__file__).resolve().parent;D=O/'proofs'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
utc=lambda:datetime.datetime.now(datetime.timezone.utc).isoformat()
assert D.is_dir() and not (D/'runner_process.json').exists()
runner=O/'verify_candidate.py';command=[sys.executable,'-B','-u',str(runner)]
r={'command':command,'cwd':str(D),'started_utc':utc(),'supervisor_pid':os.getpid(),'runner_sha256':sha(runner),'supervisor_sha256':sha(Path(__file__)),'create_no_window':True,'stdin':'DEVNULL'}
with (D/'runner.stdout.log').open('wb') as output,(D/'runner.stderr.log').open('wb') as errors:
    p=subprocess.Popen(command,cwd=D,stdin=subprocess.DEVNULL,stdout=output,stderr=errors,creationflags=subprocess.CREATE_NO_WINDOW,close_fds=True)
    r['pid']=p.pid;(D/'runner_process.json').write_text(json.dumps(r,indent=2)+'\n');code=p.wait()
r.update(ended_utc=utc(),actual_p_wait=code,normal_wait_return=True,stdout_sha256=sha(D/'runner.stdout.log'),stderr_sha256=sha(D/'runner.stderr.log'))
(D/'runner_exit.json').write_text(json.dumps(r,indent=2)+'\n');raise SystemExit(code)
