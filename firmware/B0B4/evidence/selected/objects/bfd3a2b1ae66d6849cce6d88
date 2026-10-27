"""Record real alias retry root wait after actual compile/vvp completion."""
from pathlib import Path
import hashlib,json,os,subprocess,sys
O=Path(__file__).resolve().parent;D=O/'proofs_alias_retry02';D.mkdir();runner=O/'run_alias_compile_retry02.py'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
cmd=[sys.executable,'-B','-X','utf8',str(runner)];j={'command':cmd,'runner_sha256':sha(runner),'supervisor_sha256':sha(Path(__file__)),'supervisor_pid':os.getpid()}
with (D/'runner.stdout.log').open('wb') as out,(D/'runner.stderr.log').open('wb') as err:
 p=subprocess.Popen(cmd,stdout=out,stderr=err,stdin=subprocess.DEVNULL,creationflags=subprocess.CREATE_NO_WINDOW);j['pid']=p.pid;code=p.wait()
j.update(normal_wait_return=True,actual_p_wait=code,stdout_sha256=sha(D/'runner.stdout.log'),stderr_sha256=sha(D/'runner.stderr.log'))
(D/'runner_exit.json').write_text(json.dumps(j,indent=2)+'\n');print(json.dumps({'actual_alias_retry_root_wait':code}));raise SystemExit(code)
