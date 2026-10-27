"""Detached supervisor: records the synthesis runner's actual p.wait()."""
from pathlib import Path
import datetime, hashlib, json, os, subprocess, sys
O=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
utc=lambda:datetime.datetime.now(datetime.timezone.utc).isoformat()
receipt=O/'runner_process.json'
exit_receipt=O/'runner_exit.json'
assert not receipt.exists() and not exit_receipt.exists(), 'Never overwrite a runner receipt'
runner=O/'run_synthesis.py'
command=[sys.executable,'-u',str(runner)]
record=dict(command=command,cwd=str(O),started_utc=utc(),supervisor_pid=os.getpid(),
    runner_sha256=sha(runner),supervisor_sha256=sha(Path(__file__)),create_no_window=True,stdin='DEVNULL')
with (O/'runner.stdout.log').open('wb') as output, (O/'runner.stderr.log').open('wb') as errors:
    process=subprocess.Popen(command,cwd=O,stdin=subprocess.DEVNULL,stdout=output,stderr=errors,
        creationflags=subprocess.CREATE_NO_WINDOW,close_fds=True)
    record['pid']=process.pid
    receipt.write_text(json.dumps(record,indent=2)+'\n',encoding='utf8')
    code=process.wait()
record.update(ended_utc=utc(),actual_p_wait=code,normal_wait_return=True,
    stdout_sha256=sha(O/'runner.stdout.log'),stderr_sha256=sha(O/'runner.stderr.log'))
exit_receipt.write_text(json.dumps(record,indent=2)+'\n',encoding='utf8')
raise SystemExit(code)
