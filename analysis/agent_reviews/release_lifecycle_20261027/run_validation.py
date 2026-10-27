"""Actual focused lifecycle waits only; no real export or promotion."""
from pathlib import Path
import ast,datetime,hashlib,json,os,subprocess,sys
sys.dont_write_bytecode=True
D=Path(__file__).resolve().parent;R=D.parents[2]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
files=[R/'analysis/20261026_z_aw_fix/build/export_qualified_v4.py',R/'firmware/B0B4/verify_release.py',R/'firmware/B0B4/build_candidate.py',
       D/'test_lifecycle.py',Path(__file__),R/'analysis/agent_reviews/release_wait_types_20261027/test_wait_types_retry02.py']
before={str(p):sha(p) for p in files}
for p in files:ast.parse(p.read_text(encoding='utf8'))
assert before[str(files[1])]=='0ba2c0cdca20b7bcf60b34c4d7f2c059762e7f1723f78fa977b0ad4884353cbf'
assert before[str(files[2])]=='abb5246c203b73c111f80bc91f8db6c8220463f7d4c5cf48dbfe2167ef49db84'
old_seal=R/'analysis/agent_reviews/release_wait_types_20261027/RELEASE_WAIT_TYPE_VALIDATION_SEALED.json'
assert sha(old_seal)=='f8b71b3bf9fe0bde8f30e434da0b9bb30c94c5c1459d941b97e01098f7c37bde'
binding=json.loads((R/'analysis/20261026_z_aw_fix/handoff_20261026/SOURCE_BINDINGS.json').read_text())
source=R/'firmware/B0B4/source';old55=next(v for k,v in binding['source_sha256'].items() if Path(binding['roots'][k]).resolve()==source.resolve())
assert {p:sha(source/p) for p in old55}==old55
results={}
for name,target in [('lifecycle8',D/'test_lifecycle.py'),('strict_wait6',files[-1])]:
    output=D/(name+'.stdout.log');error=D/(name+'.stderr.log');receipt=D/(name+'_exit.json')
    assert not any(p.exists() for p in [output,error,receipt])
    record=dict(command=[sys.executable,'-u','-B',str(target)],started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),parent_pid=os.getpid(),
                source_script_hashes=before,scope='Temporary-root real55 lifecycle archives and scalar rejection only; never modifies real B4 source or creates real qualification/release.')
    with output.open('wb') as out,error.open('wb') as err:
        child=subprocess.Popen(record['command'],cwd=R,stdin=subprocess.DEVNULL,stdout=out,stderr=err,creationflags=subprocess.CREATE_NO_WINDOW,close_fds=True)
        record['pid']=child.pid;code=child.wait()
    record.update(actual_p_wait=code,normal_wait_return=True,ended_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),stdout_sha256=sha(output),stderr_sha256=sha(error))
    receipt.write_text(json.dumps(record,indent=2)+'\n',encoding='utf8');results[name]=record
    print(name,code,flush=True)
    if code:raise SystemExit(code)
assert {str(p):sha(p) for p in files}==before
assert {p:sha(source/p) for p in old55}==old55 and sha(old_seal)=='f8b71b3bf9fe0bde8f30e434da0b9bb30c94c5c1459d941b97e01098f7c37bde'
result=D/'VALIDATION_RESULT.json';assert not result.exists()
result.write_text(json.dumps(dict(passed=True,focused_tests=14,actual_child_results=results,source_script_hashes=before,real_prototype_source55_unchanged=old55,
                                 previous48seal_unchanged=sha(old_seal),real_release_or_qualification_created=False),indent=2)+'\n',encoding='utf8')
