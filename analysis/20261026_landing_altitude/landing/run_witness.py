from pathlib import Path
import hashlib,json,os,subprocess,time

O=Path(__file__).resolve().parent
R=O.parents[2]
S=R/'firmware/B0B3/source'
B=Path(r'C:\Users\ScherrerL\Desktop\apple\.tools\iverilog\app\bin')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
T=O/'tmp';T.mkdir(exist_ok=True)
env=dict(os.environ,TMP=str(T),TEMP=str(T),TMPDIR=str(T))
sources=['position/mtf_xyz_hold_control.v','nav_math_service.v','position/position_math.v','position/ano_xy_stick.v','position/ano_xy_divide36.v','position/ano_z_stick.v']
inputs={'source55':{str(p.relative_to(S)).replace('\\','/'):sha(p) for p in sorted(S.rglob('*')) if p.is_file()},'tools':{str(p):sha(p) for p in [B/'iverilog.exe',B/'vvp.exe']},'scripts':{p.name:sha(p) for p in [O/'run_witness.py',O/'landing_witness_tb.v',O/'flight_state_boundary_tb.v']}}
(O/'inputs.json').write_text(json.dumps(inputs,indent=2)+'\n')
results=[]
for name,tb,srcs in [('z_windup','landing_witness_tb.v',sources),('flight_state_boundary','flight_state_boundary_tb.v',['core/ano_flight_state.v'])]:
    binary=O/(name+'.vvp')
    cmd=[str(B/'iverilog.exe'),'-g2012','-s','tb','-o',str(binary),str(O/tb),*[str(S/p) for p in srcs]]
    c=subprocess.run(cmd,cwd=O,env=env,capture_output=True,text=True)
    (O/(name+'.compile.log')).write_text(c.stdout+c.stderr)
    if c.returncode:raise RuntimeError(c.stdout+c.stderr)
    started=time.time()
    with (O/(name+'.log')).open('w') as f:
        p=subprocess.run([str(B/'vvp.exe'),str(binary)],cwd=O,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=600)
    text=(O/(name+'.log')).read_text()
    result={'name':name,'exit_code':p.returncode,'seconds':time.time()-started,'checks':[x for x in text.splitlines() if x.startswith('PASS')],'log_sha256':sha(O/(name+'.log')),'compiled_local_omitted_sha256':sha(binary)}
    results.append(result)
    (O/'rtl_results.json').write_text(json.dumps({'scope':'Directed real RTL witnesses, accelerated callback wall-clock cadence; original 11ms Z/1ms stick dt; no plant model or flight replay; no forced private state. Flight-state TICKS_PER_MS=1 timer boundary test.','results':results},indent=2)+'\n')
    print(text,flush=True)
    if p.returncode or not result['checks']:raise RuntimeError('RTL witness failed')
assert inputs['source55']=={str(p.relative_to(S)).replace('\\','/'):sha(p) for p in sorted(S.rglob('*')) if p.is_file()}
