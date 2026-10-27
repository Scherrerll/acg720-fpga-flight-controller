"""Real hidden Python audit-only child wait; no Gowin, synthesis, PNR or hardware."""
from pathlib import Path
import datetime,hashlib,json,os,subprocess,sys
sys.dont_write_bytecode=True
D=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
from run_audit_retry02 import require_review
require_review()
assert not (D/'completion_runner_process.json').exists() and not (D/'completion_runner_exit.json').exists() and not (D/'completion_manifest.json').exists()
runner=D/'complete_audit_retry02.py';command=[sys.executable,'-B','-X','utf8',str(runner)]
record=dict(command=command,cwd=str(D),started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),supervisor_pid=os.getpid(),
    runner_sha256=sha(runner),supervisor_sha256=sha(Path(__file__)),preparation_sha256=sha(D/'RETRY_PREPARATION.json'),approval_sha256=sha(D/'REVIEW_APPROVAL.json'),
    no_vendor_process=True,SYN_rerun=False)
with (D/'completion_runner.stdout.log').open('wb') as out,(D/'completion_runner.stderr.log').open('wb') as err:
    p=subprocess.Popen(command,cwd=D,stdin=subprocess.DEVNULL,stdout=out,stderr=err,creationflags=subprocess.CREATE_NO_WINDOW,close_fds=True)
    record['pid']=p.pid;(D/'completion_runner_process.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf8');code=p.wait()
record.update(normal_wait_return=True,actual_p_wait=code,ended_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),stdout_sha256=sha(D/'completion_runner.stdout.log'),stderr_sha256=sha(D/'completion_runner.stderr.log'))
(D/'completion_runner_exit.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf8')
if code==0:
    p=D/'completion_result.json';result=json.loads(p.read_text(encoding='utf8'));assert result['passed_audit_completion'] and result['successful_audit_wait']==0
    result.update(passed_SYN_only=True,actual_completion_root_wait=code,completion_runner_actual_wait=code,
        completion_root_exit=dict(path=str(D/'completion_runner_exit.json'),sha256=sha(D/'completion_runner_exit.json')),
        completion_root_logs={channel:dict(path=str(D/('completion_runner.'+channel+'.log')),sha256=sha(D/('completion_runner.'+channel+'.log'))) for channel in ['stdout','stderr']},
        completion_manifest_path=str(D/'completion_manifest.json'))
    assert result['original_runner_actual_wait']==result['original_audit_actual_wait']==1 and result['original_vendor_actual_wait']==0
    p.write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
    artifacts={q.relative_to(D).as_posix():dict(sha256=sha(q),bytes=q.stat().st_size) for q in D.rglob('*') if q.is_file() and '__pycache__' not in q.relative_to(D).parts}
    manifest=dict(source55=result['source55'],original_VG_sha256=result['original_VG_sha256'],completion_directory=str(D),artifacts=artifacts,
        original_vendor_actual_wait=0,original_audit_actual_wait=1,original_runner_actual_wait=1,successful_audit_wait=0,actual_completion_root_wait=code,
        original_actual_exit_receipts=result['original_actual_exit_receipts'],successful_audit_exit=result['successful_audit_exit'],completion_root_exit=result['completion_root_exit'],SYN_rerun=False)
    (D/'completion_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf8')
print(json.dumps(record));raise SystemExit(code)
