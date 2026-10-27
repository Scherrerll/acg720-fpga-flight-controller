"""Record a fresh actual offline validation child wait; preserve earlier receipts."""
from pathlib import Path
import ast,datetime,hashlib,json,os,subprocess,sys
sys.dont_write_bytecode=True
D=Path(__file__).resolve().parent;R=D.parents[2]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
prefix='v22_final_validation_01'
for suffix in ['_exit.json','.stdout.log','.stderr.log']:assert not (D/(prefix+suffix)).exists()
files=[R/'analysis/20261026_z_aw_fix/build/export_qualified_v4.py',R/'firmware/B0B4/verify_release.py',
       R/'firmware/B0B4/build_candidate.py',D/'test_release_evidence.py',D/'check_existing_archives.py',Path(__file__)]
before={str(p):sha(p) for p in files}
for p in files:ast.parse(p.read_text(encoding='utf8'))
assert before[str(files[2])]=='abb5246c203b73c111f80bc91f8db6c8220463f7d4c5cf48dbfe2167ef49db84'
record=dict(command=[sys.executable,'-u','-B',str(D/'check_existing_archives.py')],cwd=str(R),
    started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),parent_pid=os.getpid(),source_script_hashes=before,
    scope='Offline source/proof/SYN/portable archive checks only; no release export/promotion, vendor, simulation, hardware or replacement of prior receipts.')
with (D/(prefix+'.stdout.log')).open('wb') as out,(D/(prefix+'.stderr.log')).open('wb') as err:
    child=subprocess.Popen(record['command'],cwd=R,stdin=subprocess.DEVNULL,stdout=out,stderr=err,
        creationflags=subprocess.CREATE_NO_WINDOW,close_fds=True)
    record['pid']=child.pid;code=child.wait()
record.update(actual_p_wait=code,normal_wait_return=True,ended_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    stdout_sha256=sha(D/(prefix+'.stdout.log')),stderr_sha256=sha(D/(prefix+'.stderr.log')))
assert {str(p):sha(p) for p in files}==before,'Tested source changed during validation'
(D/(prefix+'_exit.json')).write_text(json.dumps(record,indent=2)+'\n',encoding='utf8')
print(json.dumps(record));raise SystemExit(code)
