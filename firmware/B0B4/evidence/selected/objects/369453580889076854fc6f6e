"""Supervised v9 proofs. No hardware, SYN or PNR."""
from pathlib import Path
import datetime,hashlib,json,os,subprocess,sys
O=Path(__file__).resolve().parent;R=O.parents[3];D=O/'proofs'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text())
freeze=read(O/'source_freeze.json');S=Path(freeze['source_root']);expected=freeze['source55']
assert {p:sha(S/p) for p in expected}==expected
assert not (D/'results.json').exists()
stages=[]
for kind in ['five','boundary','top','contention']:
    command=[sys.executable,'-B','-u',str(D/kind/'run.py')]
    if kind=='boundary':command+=['--expected-hold-sha256',expected['position/mtf_xyz_hold_control.v']]
    receipt={'command':command,'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
    with (D/(kind+'.stdout.log')).open('wb') as output,(D/(kind+'.stderr.log')).open('wb') as errors:
        p=subprocess.Popen(command,cwd=D/kind,stdin=subprocess.DEVNULL,stdout=output,stderr=errors,creationflags=subprocess.CREATE_NO_WINDOW)
        receipt['pid']=p.pid;(D/(kind+'_process.json')).write_text(json.dumps(receipt,indent=2)+'\n')
        code=p.wait()
    receipt.update(actual_p_wait=code,normal_wait_return=True,ended_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        stdout_sha256=sha(D/(kind+'.stdout.log')),stderr_sha256=sha(D/(kind+'.stderr.log')))
    (D/(kind+'_exit.json')).write_text(json.dumps(receipt,indent=2)+'\n');stages.append(receipt)
    print(kind,'actual_wait',code,flush=True);assert code==0,(kind,'see stdout/stderr')
five=read(D/'five/results.json');boundary=read(D/'boundary/results.json')
top=read(D/'top/top_safety_results.json');contention=read(D/'contention/contention/results.json')
assert five['completed']==5 and five['passed'] and boundary['completed']==2 and boundary['passed'] and top['passed'] and contention['passed']
assert {p:sha(S/p) for p in expected}==expected
v8=read(O.parent/'compact_aw_v8/source_freeze.json')['source55']
guard=['position/pose_time_adapter.v','position/mtf_shared_height_fusion.v','mtf_xyz_navigation_control.v','nav_math_service.v','position/position_math.v']
assert all(expected[p]==v8[p] for p in guard)
reused=O.parent/'compact_aw_v8/proofs_completion02/results.json';rx=O.parent/'compact_aw_v8/proofs_completion02/runner_exit.json'
assert read(reused)['passed'] and read(rx)['actual_p_wait']==0
(D/'results.json').write_text(json.dumps({'passed':True,'source55':expected,'source55_unchanged':True,'five':five,'boundary':boundary,'top13':top,'contention':contention,
    'reused_v8_guard_proofs':{'results_sha256':sha(reused),'runner_exit_sha256':sha(rx),'identical_dependencies':guard},'stages':stages},indent=2)+'\n')
print('PASS v9 five/boundary/top13/four-client proofs',flush=True)
