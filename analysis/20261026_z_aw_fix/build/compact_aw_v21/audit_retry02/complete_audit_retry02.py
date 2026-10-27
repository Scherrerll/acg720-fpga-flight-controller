"""Completion coordinator: actual separate audit child wait, original exits unchanged."""
from pathlib import Path
import datetime,hashlib,json,os,subprocess,sys
sys.dont_write_bytecode=True
D=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
from run_audit_retry02 import require_review
prep=require_review()
assert not (D/'successful_audit_exit.json').exists() and not (D/'completion_result.json').exists()
runner=D/'run_audit_retry02.py';command=[sys.executable,'-B','-X','utf8',str(runner)]
record=dict(command=command,cwd=str(D),started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),parent_pid=os.getpid(),
    runner_sha256=sha(runner),coordinator_sha256=sha(Path(__file__)),preparation_sha256=sha(D/'RETRY_PREPARATION.json'),SYN_rerun=False)
with (D/'successful_audit.stdout.log').open('wb') as out,(D/'successful_audit.stderr.log').open('wb') as err:
    p=subprocess.Popen(command,cwd=D,stdin=subprocess.DEVNULL,stdout=out,stderr=err,creationflags=subprocess.CREATE_NO_WINDOW,close_fds=True)
    record['pid']=p.pid;(D/'successful_audit_process.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf8')
    try:code=p.wait(timeout=300)
    except subprocess.TimeoutExpired:p.terminate();code=p.wait();record['terminated_after_timeout']=True
record.update(normal_wait_return=True,actual_p_wait=code,ended_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),stdout_sha256=sha(D/'successful_audit.stdout.log'),stderr_sha256=sha(D/'successful_audit.stderr.log'))
(D/'successful_audit_exit.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf8')
assert code==0 and not record.get('terminated_after_timeout')
result_path=D/'results_01/RESULT.json';result=json.loads(result_path.read_text(encoding='utf8'));assert result['passed_checks']
result=dict(passed_audit_completion=True,source55=prep['source55'],original_VG_sha256=prep['original_VG_sha256'],completion_directory=str(D),
    original_vendor_actual_wait=0,original_audit_actual_wait=1,original_runner_actual_wait=1,successful_audit_wait=code,
    successful_audit_exit=dict(path=str(D/'successful_audit_exit.json'),sha256=sha(D/'successful_audit_exit.json')),
    successful_audit_logs={channel:dict(path=str(D/('successful_audit.'+channel+'.log')),sha256=sha(D/('successful_audit.'+channel+'.log'))) for channel in ['stdout','stderr']},
    original_actual_exit_receipts=result['original_actual_exit_receipts'],original_bound_files=prep['original_bound_files'],
    original_attempt_artifacts=prep['original_attempt_artifacts'],original_metadata_artifacts=prep['original_metadata_artifacts'],
    retry_audit_result=dict(path=str(result_path),sha256=sha(result_path)),preparation_sha256=sha(D/'RETRY_PREPARATION.json'),approval_sha256=sha(D/'REVIEW_APPROVAL.json'),
    SYN_rerun=False,PNR_started=False,scope='Audit-only completion on exact SYN0 VG. The original canonical root and audit remain1; new audit child wait is recorded separately. Completion root wait is supplied only by its actual supervising process.')
(D/'completion_result.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
print(json.dumps(dict(passed_audit_completion=True,successful_audit_wait=code,original_vendor_actual_wait=0,original_audit_actual_wait=1,original_runner_actual_wait=1,SYN_rerun=False)))
