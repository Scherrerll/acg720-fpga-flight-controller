"""Run fresh v22 source-bound proofs, with actual root and phase waits."""
from pathlib import Path
import concurrent.futures,datetime,hashlib,json,os,subprocess,sys,traceback
O=Path(__file__).resolve().parent;R=O.parents[3];D=O/'proofs_attempt01';S=R/'out/z_aw_fix_20261026/compact_aw_v22/canonical/source'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf8'))
write=lambda p,j:p.write_text(json.dumps(j,indent=2)+'\n',encoding='utf8')
utc=lambda:datetime.datetime.now(datetime.timezone.utc).isoformat()
expected=read(O/'source_freeze.json')['source55'];assert {n:sha(S/n) for n in expected}==expected
B=R.parents[1]/'.tools/iverilog/app/bin';IV=B/'iverilog.exe';VVP=B/'vvp.exe'
model=Path('C:/Gowin/Gowin_V1.9.12.04_x64/IDE/simlib/gw5a/prim_sim.v')
bound_files=[Path(__file__),O/'record_stage.py',O/'prepare_alias.py',O/'source_freeze.json',O/'SOURCE_CHANGES.json',O/'FIXTURE_ADAPTATIONS.json',IV,VVP,model,R/'firmware/B0B4/xy_pi_cli.py']
bound_files += [p for p in D.rglob('*') if p.is_file()]
assert not (D/'inputs.json').exists();write(D/'inputs.json',{'source55':expected,'bound_inputs':{str(p):sha(p) for p in bound_files},'scope':'Fresh actual v22 top13; original five antiwindup cases; v20/v22 whole-controller FRAC0/16 everycycle miter; four-client service contention; actual unchanged-function signed alias miter. No vendor process.'})
exits=[]
def run(name,command,timeout=1800,cwd=R):
 j={'command':list(map(str,command)),'cwd':str(cwd),'started_utc':utc()}
 assert not (D/f'{name}_exit.json').exists()
 with (D/f'{name}.stdout.log').open('wb') as out,(D/f'{name}.stderr.log').open('wb') as err:
  p=subprocess.Popen(command,cwd=cwd,stdin=subprocess.DEVNULL,stdout=out,stderr=err,creationflags=subprocess.CREATE_NO_WINDOW)
  j['pid']=p.pid;write(D/f'{name}_process.json',j)
  try:code=p.wait(timeout=timeout)
  except subprocess.TimeoutExpired:p.terminate();code=p.wait();j['terminated_after_timeout']=True
 j.update(actual_p_wait=code,normal_wait_return=True,ended_utc=utc(),stdout_sha256=sha(D/f'{name}.stdout.log'),stderr_sha256=sha(D/f'{name}.stderr.log'))
 path=D/f'{name}_exit.json';write(path,j);exits.append(path)
 print(json.dumps({'stage':name,'actual_p_wait':code}),flush=True)
 assert code==0 and not j.get('terminated_after_timeout'),(name,code)
def stage(name):
 target=D/name/('run_top13.py' if name=='top13' else 'run.py')
 args=['--expected-hold-sha256',expected['position/mtf_xyz_hold_control.v']] if name=='boundary' else []
 run(name,[sys.executable,'-B','-X','utf8',str(O/'record_stage.py'),str(target),*args])
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
 futures=[pool.submit(stage,n) for n in ['five','boundary','contention','top13']]
 for future in futures:future.result()
run('alias_compile',[str(IV),'-g2012','-s','tb','-o',str(D/'alias/alias.vvp'),str(D/'alias/alias_tb.v'),str(D/'alias/actual_functions.v')])
run('alias_vvp',[str(VVP),str(D/'alias/alias.vvp')])
assert (D/'top13/top_safety_tb.v').read_bytes()==(O.parent/'v4_release_proofs/top_safety_tb.v').read_bytes()
for a,b in [('five/aw_tb.v',O.parent/'compact_aw_v9/proofs_retry02/five/aw_tb.v'),('boundary/boundary_tb.v',O.parent/'compact_aw_v9/proofs_retry02/boundary/boundary_tb.v'),('contention/contention/contention_tb.v',O.parent/'compact_aw_v9/proofs_retry02/contention/contention/contention_tb.v')]:assert (D/a).read_bytes()==b.read_bytes(),a
assert read(D/'five/results.json')['passed'] and read(D/'five/results.json')['completed']==5
assert read(D/'boundary/results.json')['passed'] and read(D/'boundary/results.json')['completed']==2
assert read(D/'contention/contention/results.json')['passed']
assert read(D/'top13/top_safety_results.json')['cases']==13
assert 'PASS actual_alias' in (D/'alias_vvp.stdout.log').read_text()
inputs=read(D/'inputs.json');assert {p:sha(Path(p)) for p in inputs['bound_inputs']}==inputs['bound_inputs']
assert {n:sha(S/n) for n in expected}==expected
for name in ['five','boundary','contention','top13']:
 index=read(D/name/'actual_child_receipts/INDEX.json');assert index['passed']
 for x in index['receipts']:assert sha(Path(x['path']))==x['sha256'];exits.append(Path(x['path']))
receipts={p.relative_to(D).as_posix():sha(p) for p in exits}
artifacts={p.relative_to(D).as_posix():sha(p) for p in D.rglob('*') if p.is_file() and 'tmp' not in p.relative_to(D).parts and p.suffix not in ['.vvp']}
write(D/'RESULT.json',{'passed':True,'source55':expected,'inputs_sha256':sha(D/'inputs.json'),'exit_receipts_base':str(D),'exit_receipts':receipts,'artifacts':artifacts,'fresh_controller_dependency_hashes':{n:expected[n] for n in ['position/mtf_xyz_hold_control.v','nav_math_service.v','position/position_math.v','position/ano_xy_stick.v','position/ano_xy_divide36.v','position/ano_z_stick.v']},'new_controller_not_claimed_byte_identical_to_parent':True,'fresh_top13_cases':13,'fresh_five_cases':5,'fresh_fraction_cases':[0,16],'four_client':read(D/'contention/contention/results.json'),'alias_identity_sha256':sha(D/'alias/STRUCTURAL_IDENTITY.json'),'scope':'Offline RTL proof only; top13 retains original disclosed controlled private forces. Controller scenarios/boundary/contention and extracted function miter have no DUT state force/preload. No vendor or physical timing claim.'})
print(json.dumps({'passed':True,'RESULT_sha256':sha(D/'RESULT.json')}),flush=True)
