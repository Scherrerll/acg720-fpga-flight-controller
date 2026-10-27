"""Capture the actual reviewed v21 SYN_ONLY child wait; no PNR/hardware controls."""
from pathlib import Path
import datetime,hashlib,json,os,subprocess,sys
O=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf8'))
utc=lambda:datetime.datetime.now(datetime.timezone.utc).isoformat()
assert not (O/'runner_process.json').exists() and not (O/'runner_exit.json').exists()
runner=O/'run_synthesis.py';sealer=O/'seal_synthesis.py';approval=read(O/'SYNTHESIS_REVIEW_APPROVAL.json')
expected=read(O/'source_freeze.json')['source55']
assert approval['approved'] is True and approval['source55']==expected and len(set(approval['reviewers']))>=2
assert approval['run_synthesis_sha256']==sha(runner)
assert approval['audit_synthesis_only_sha256']==sha(O/'audit_synthesis_only.py')
assert approval['sp_clock_audit_sha256']==sha(O/'sp_clock_audit.py')
command=[sys.executable,'-B','-X','utf8',str(runner)]
record=dict(command=command,cwd=str(O),started_utc=utc(),supervisor_pid=os.getpid(),
    runner_sha256=sha(runner),supervisor_sha256=sha(Path(__file__)),seal_synthesis_sha256=sha(sealer),
    review_approval_sha256=sha(O/'SYNTHESIS_REVIEW_APPROVAL.json'),source55=expected,
    source_freeze_sha256=sha(O/'source_freeze.json'),proof_binding_sha256=sha(O/'PROOF_BINDING.json'),
    reused_bindings_sha256=sha(O/'REUSED_BINDINGS_RECHECK.json'),create_no_window=True,stdin='DEVNULL')
with (O/'runner.stdout.log').open('wb') as output,(O/'runner.stderr.log').open('wb') as errors:
    p=subprocess.Popen(command,cwd=O,stdout=output,stderr=errors,stdin=subprocess.DEVNULL,
        creationflags=subprocess.CREATE_NO_WINDOW,close_fds=True)
    record['pid']=p.pid;(O/'runner_process.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf8')
    code=p.wait()
record.update(actual_p_wait=code,normal_wait_return=True,ended_utc=utc(),
    stdout_sha256=sha(O/'runner.stdout.log'),stderr_sha256=sha(O/'runner.stderr.log'))
(O/'runner_exit.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf8')
raise SystemExit(code)
