"""Bind reused exact-dependency proofs and run only the final exact-v4 top13 gap."""
from pathlib import Path
import ast,datetime,hashlib,json,subprocess,sys
O=Path(__file__).resolve().parent/'v4_release_proofs';R=O.parents[3]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf8'))
assert not O.exists();O.mkdir()
expected=read(O.parent/'compact_aw_v4/source_freeze.json')['source55']
S=R/'out/z_aw_fix_20261026/compact_aw_v4/canonical/source'
assert len(expected)==55 and {p:sha(S/p) for p in expected}==expected
D=O.parent/'compact_aw_v9/proofs_retry02';proof=read(D/'results.json')
assert proof['passed'] and read(D/'runner_exit.json')['actual_p_wait']==0
deps=['position/mtf_xyz_hold_control.v','nav_math_service.v','position/position_math.v','position/ano_xy_stick.v','position/ano_xy_divide36.v','position/ano_z_stick.v']
assert all(expected[p]==proof['source55'][p] for p in deps)
assert proof['five']['passed'] and proof['five']['completed']==5 and all(x['exit_code']==0 for x in proof['five']['results'])
assert proof['boundary']['passed'] and proof['boundary']['completed']==2 and proof['contention']['passed']
for kind in ['five','boundary','contention']:assert read(D/(kind+'_exit.json'))['actual_p_wait']==0
groot=R/'ground/B0B4/test_results';ground=read(groot/'verification.json')
assert ground['result']=='PASS'
for name,digest in ground['input_sha256'].items():
    p=Path(name)
    assert p.name.lower()!='deployment.env' and '.env' not in p.suffixes,'Never open environment credentials'
    assert sha(R/p)==digest,('Ground input changed',name)
for kind in ['python','node']:
    item=read(groot/(kind+'_result.json'))
    assert item['actual_exit_code']==0 and sha(groot/(kind+'.log'))==item['log_sha256']
fixture=R/'analysis/20261026_z_aw_fix/width_integration/verify_top_safety.py'
t=fixture.read_text();old='REPO=Path(__file__).resolve().parents[3]';assert t.count(old)==1
t=t.replace(old,'REPO=Path('+repr(str(R))+')');ast.parse(t)
run=O/'run_top13.py';run.write_text(t)
inputs={'source_root':str(S),'source55':expected,'fixture_original_sha256':sha(fixture),'executed_fixture_sha256':sha(run),
    'adaptation':'Only repo path constant/output location; original13 assertions, simulation forces and source v4 unchanged.',
    'reused_controller_proofs':str(D),'reused_results_sha256':sha(D/'results.json'),'exact_dependencies':{p:expected[p] for p in deps},
    'ground_verification_sha256':sha(groot/'verification.json'),'ground_input_count':len(ground['input_sha256'])}
(O/'inputs.json').write_text(json.dumps(inputs,indent=2)+'\n')
command=[sys.executable,'-B',str(run)];receipt={'command':command,'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
with (O/'runner.stdout.log').open('wb') as so,(O/'runner.stderr.log').open('wb') as se:
    p=subprocess.Popen(command,cwd=O,stdin=subprocess.DEVNULL,stdout=so,stderr=se,creationflags=subprocess.CREATE_NO_WINDOW)
    receipt['pid']=p.pid;(O/'runner_process.json').write_text(json.dumps(receipt,indent=2)+'\n');code=p.wait()
receipt.update(actual_p_wait=code,normal_wait_return=True,ended_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),stdout_sha256=sha(O/'runner.stdout.log'),stderr_sha256=sha(O/'runner.stderr.log'))
(O/'runner_exit.json').write_text(json.dumps(receipt,indent=2)+'\n');assert code==0
assert read(O/'top_safety_results.json')['passed'] and {p:sha(S/p) for p in expected}==expected
(O/'RESULT.json').write_text(json.dumps({'passed':True,'scope':'Functional/software evidence only, no physical/hardware acceptance.','source55':expected,
    'top13_new_exact_source_actual_wait':code,'reused_five_boundary_fourclient_exact_dependencies':True,'ground_reused_unchanged_inputs':True,
    'inputs_sha256':sha(O/'inputs.json'),'runner_exit_sha256':sha(O/'runner_exit.json'),'top13_result_sha256':sha(O/'top_safety_results.json'),
    'note':'Fixed-sensor simulation times are not flight/landing wait instructions; top13 deliberately forces core gate inputs as inherited fixture states.'},indent=2)+'\n')
print('PASS exact-v4 top13; hash-reused five/boundary/contention and unchanged ground tests. No hardware.')
