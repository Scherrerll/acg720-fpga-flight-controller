"""Actual unmodified vendor SP/FF miter; only this isolated proof directory is written."""
from pathlib import Path
import datetime,hashlib,json,os,re,subprocess,sys,time
O=Path(__file__).resolve().parent;R=O.parents[2];D=O/'attempt01'
assert not D.exists();D.mkdir();(D/'tmp').mkdir()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
utc=lambda:datetime.datetime.now(datetime.timezone.utc).isoformat()
C=R/'out/z_aw_fix_20261026/compact_aw_v18/canonical/source'
freeze=R/'analysis/20261026_z_aw_fix/build/compact_aw_v18/source_freeze.json'
expected=json.loads(freeze.read_text(encoding='utf8'))['source55']
assert len(expected)==55 and all(sha(C/n)==h for n,h in expected.items())
wrapper=C/'gw5_snapshot_bram.v'
model=Path('C:/Gowin/Gowin_V1.9.12.04_x64/IDE/simlib/gw5a/prim_sim.v')
assert sha(model)=='7109c2568188627465d218bc099cf72f12e90807c21d4d862d2335b499043544'
B=R.parents[1]/'.tools/iverilog/app/bin';IV=B/'iverilog.exe';VVP=B/'vvp.exe'
bound={str(p):sha(p) for p in [Path(__file__),O/'supervise_proof.py',O/'extension_bram_tb.v',freeze,wrapper,model,IV,VVP,Path(sys.executable)]}
inputs=dict(started_utc=utc(),source_root=str(C),source55=expected,bound_files=bound,
    model_unmodified=True,model=str(model),model_sha256=sha(model),wrapper=str(wrapper),wrapper_sha256=sha(wrapper),
    compile_define='GW5_USE_VENDOR_BRAM',default_FF_bypass_forbidden=True,width=888,physical_SP_banks=28,clock_hz=50000000,
    no_DUT_force_or_preload=True,scope='Isolated actual vendor functional model versus original initialized enabled-FF semantics. Not top integration, synthesized mapping, physical timing or hardware qualification.')
(D/'inputs.json').write_text(json.dumps(inputs,indent=2)+'\n',encoding='utf8')
env=dict(os.environ);env.update(TMP=str(D/'tmp'),TEMP=str(D/'tmp'),TMPDIR=str(D/'tmp'))
stages=[]
def run(name,command):
    rec=dict(command=command,cwd=str(D),started_utc=utc(),parent_pid=os.getpid());start=time.monotonic()
    with (D/(name+'.stdout.log')).open('wb') as out,(D/(name+'.stderr.log')).open('wb') as err:
        p=subprocess.Popen(command,cwd=D,env=env,stdin=subprocess.DEVNULL,stdout=out,stderr=err,creationflags=subprocess.CREATE_NO_WINDOW)
        rec['pid']=p.pid;(D/(name+'_process.json')).write_text(json.dumps(rec,indent=2)+'\n',encoding='utf8')
        try:code=p.wait(timeout=120)
        except subprocess.TimeoutExpired:p.terminate();code=p.wait();rec['terminated_after_timeout']=True
    rec.update(normal_wait_return=True,actual_p_wait=code,ended_utc=utc(),seconds=time.monotonic()-start,
        stdout_sha256=sha(D/(name+'.stdout.log')),stderr_sha256=sha(D/(name+'.stderr.log')))
    (D/(name+'_exit.json')).write_text(json.dumps(rec,indent=2)+'\n',encoding='utf8');stages.append(rec)
    print(json.dumps(dict(stage=name,actual_p_wait=code,seconds=rec['seconds'])),flush=True)
    assert code==0 and not rec.get('terminated_after_timeout'),(name,code,(D/(name+'.stdout.log')).read_text(errors='replace'),(D/(name+'.stderr.log')).read_text(errors='replace'))
    return (D/(name+'.stdout.log')).read_text(encoding='utf8',errors='replace')
exe=D/'extension_bram.vvp'
run('compile',[str(IV),'-g2012','-DGW5_USE_VENDOR_BRAM','-s','extension_bram_tb','-o',str(exe),str(O/'extension_bram_tb.v'),str(wrapper),str(model)])
elaborated=exe.read_text(encoding='utf8',errors='strict')
sp_count=len(re.findall(r'\.scope module,\s*"memory"\s*"SP"',elaborated))
gsr_count=len(re.findall(r'\.scope module,\s*"GSR"\s*"GSR"',elaborated))
assert sp_count==28 and gsr_count==1 and 'portable_simulation' not in elaborated,(sp_count,gsr_count)
elaboration=dict(passed=True,actual_SP_instances=sp_count,actual_GSR_instances=gsr_count,portable_FF_branch_absent=True,vvp_sha256=sha(exe))
(D/'elaboration.json').write_text(json.dumps(elaboration,indent=2)+'\n',encoding='utf8')
log=run('vvp',[str(VVP),str(exe)])
assert 'PASS WIDTH=888 actual_SP=28 GSR=1 SIMULATION_BYPASS=0 CLK_HZ=50000000' in log
assert all(sha(Path(p))==h for p,h in bound.items()) and all(sha(C/n)==h for n,h in expected.items())
receipts={str((D/(name+'_exit.json')).relative_to(O)).replace('\\','/'):sha(D/(name+'_exit.json')) for name in ['compile','vvp']}
result=dict(passed=True,finished_utc=utc(),source55=expected,inputs_file='attempt01/inputs.json',inputs_sha256=sha(D/'inputs.json'),
    source_fixture_tools_model_unchanged=True,elaboration=elaboration,elaboration_receipt_sha256=sha(D/'elaboration.json'),
    pass_lines=[s for s in log.splitlines() if s.startswith('PASS ')],stages=stages,exit_receipts=receipts,
    scope=inputs['scope'])
(O/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
print(json.dumps(dict(passed=True,elaboration=elaboration,pass_lines=result['pass_lines'])),flush=True)
