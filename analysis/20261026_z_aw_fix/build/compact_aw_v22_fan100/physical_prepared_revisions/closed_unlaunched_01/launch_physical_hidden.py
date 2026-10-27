"""Single-profile supervised physical runner; main controls vendor slot scheduling."""
from pathlib import Path
import datetime,hashlib,json,os,subprocess,sys
sys.dont_write_bytecode=True
assert len(sys.argv)==2 and sys.argv[1]=='3'
BASE=Path(__file__).resolve().parent;O=BASE/'physical_p3r0_01'
from physical_input_contract import validate_physical
validate_physical(require_review=True)
assert O.is_dir() and not any(O.iterdir())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
cmd=[sys.executable,'-B','-X','utf8',str(BASE/'run_physical.py'),'3']
j={'command':cmd,'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'supervisor_pid':os.getpid(),'runner_sha256':sha(BASE/'run_physical.py'),'supervisor_sha256':sha(Path(__file__))}
with (O/'runner.stdout.log').open('xb') as out,(O/'runner.stderr.log').open('xb') as err:
    p=subprocess.Popen(cmd,stdout=out,stderr=err,stdin=subprocess.DEVNULL,creationflags=subprocess.CREATE_NO_WINDOW);j['pid']=p.pid
    (O/'runner_process.json').write_text(json.dumps(j,indent=2)+'\n',encoding='utf8');code=p.wait()
j.update(normal_wait_return=True,actual_p_wait=code,ended_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),stdout_sha256=sha(O/'runner.stdout.log'),stderr_sha256=sha(O/'runner.stderr.log'))
(O/'runner_exit.json').write_text(json.dumps(j,indent=2)+'\n',encoding='utf8');raise SystemExit(code)
