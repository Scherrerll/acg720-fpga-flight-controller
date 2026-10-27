"""Fresh actual waits; never overwrite the previous42 seal or any receipt."""
from pathlib import Path
import ast,datetime,hashlib,json,os,subprocess,sys
sys.dont_write_bytecode=True
D=Path(__file__).resolve().parent;R=D.parents[2]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
files=[R/'analysis/20261026_z_aw_fix/build/export_qualified_v4.py',R/'firmware/B0B4/verify_release.py',R/'firmware/B0B4/build_candidate.py',
       D/'test_wait_types_retry02.py',Path(__file__),R/'analysis/agent_reviews/release_20261027/test_release_evidence.py',
       R/'analysis/agent_reviews/release_20261027/check_existing_archives.py']
before={str(p):sha(p) for p in files}
for p in files:ast.parse(p.read_text(encoding='utf8'))
assert before[str(files[2])]=='abb5246c203b73c111f80bc91f8db6c8220463f7d4c5cf48dbfe2167ef49db84'
results={}
for name,target in [('negative_types_retry02',D/'test_wait_types_retry02.py'),('existing42_retry02',R/'analysis/agent_reviews/release_20261027/check_existing_archives.py')]:
    paths={s:D/(name+s) for s in ['.stdout.log','.stderr.log','_exit.json']}
    assert not any(p.exists() for p in paths.values())
    record=dict(command=[sys.executable,'-u','-B',str(target)],started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                parent_pid=os.getpid(),source_script_hashes=before,scope='Offline receipt rejection and existing proof/SYN/preparation archives only; no export, promotion, vendor or hardware.')
    with paths['.stdout.log'].open('wb') as out,paths['.stderr.log'].open('wb') as err:
        child=subprocess.Popen(record['command'],cwd=R,stdin=subprocess.DEVNULL,stdout=out,stderr=err,creationflags=subprocess.CREATE_NO_WINDOW,close_fds=True)
        record['pid']=child.pid;code=child.wait()
    record.update(actual_p_wait=code,normal_wait_return=True,ended_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                  stdout_sha256=sha(paths['.stdout.log']),stderr_sha256=sha(paths['.stderr.log']))
    paths['_exit.json'].write_text(json.dumps(record,indent=2)+'\n',encoding='utf8')
    results[name]=record
    print(name,code,flush=True)
    if code:raise SystemExit(code)
assert {str(p):sha(p) for p in files}==before,'Source changed during validation'
result=D/'VALIDATION_RESULT_RETRY02.json';assert not result.exists()
result.write_text(json.dumps({'passed':True,'actual_child_results':results,'source_script_hashes':before},indent=2)+'\n',encoding='utf8')
