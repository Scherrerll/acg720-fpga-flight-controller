"""Capture the actual SYN-only child wait; no PNR or hardware controls."""
from pathlib import Path
import datetime,hashlib,json,os,subprocess,sys
O=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
utc=lambda:datetime.datetime.now(datetime.timezone.utc).isoformat()
from validation_contract import verify_contract,verify_syn_review
assert verify_contract(check_proof=True)['passed']
verify_syn_review()
assert not (O/'runner_process.json').exists() and not (O/'runner_exit.json').exists()
runner=O/'run_synthesis.py';command=[sys.executable,'-B','-X','utf8',str(runner)]
record={'command':command,'started_utc':utc(),'supervisor_pid':os.getpid(),'runner_sha256':sha(runner),'supervisor_sha256':sha(Path(__file__))}
with (O/'runner.stdout.log').open('wb') as output,(O/'runner.stderr.log').open('wb') as errors:
    p=subprocess.Popen(command,stdout=output,stderr=errors,stdin=subprocess.DEVNULL,creationflags=subprocess.CREATE_NO_WINDOW)
    record['pid']=p.pid;(O/'runner_process.json').write_text(json.dumps(record,indent=2)+'\n');code=p.wait()
record.update(actual_p_wait=code,normal_wait_return=True,ended_utc=utc(),stdout_sha256=sha(O/'runner.stdout.log'),stderr_sha256=sha(O/'runner.stderr.log'))
(O/'runner_exit.json').write_text(json.dumps(record,indent=2)+'\n');raise SystemExit(code)
