from pathlib import Path
import hashlib,json,os,subprocess,time
O=Path(__file__).resolve().parent;R=O.parents[2];D=O/'xy_i0_attempt02';D.mkdir(exist_ok=True)
B4=R/'firmware/B0B4/source';B3=R/'firmware/B0B3/source';B=Path(r'C:\Users\ScherrerL\Desktop\apple\.tools\iverilog\app\bin')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
oldinputs=json.loads((O/'inputs.json').read_text())
def sources(s):return {p:sha(s/p) for p in oldinputs['B3_source55']}
assert sources(B3)==oldinputs['B3_source55'] and sources(B4)==oldinputs['B4_source55']
T=D/'tmp';T.mkdir(exist_ok=True);env=dict(os.environ,TMP=str(T),TEMP=str(T),TMPDIR=str(T))
original=(O/'aw_tb.v').read_text()
diagnostic=original.replace('$fatal(1,"unexpected arithmetic/stick/controller fault");',
 '$fatal(1,"fault flags new=%0d/%0d old=%0d/%0d reason=%0d/%0d height_due=%0d/%0d pos_due=%0d/%0d state=%0d/%0d",candidate.dut.blocked,candidate.dut.xy_blocked,baseline.dut.blocked,baseline.dut.xy_blocked,candidate.dut.fault_reason,baseline.dut.fault_reason,candidate.dut.height_due,baseline.dut.height_due,candidate.dut.position_due,baseline.dut.position_due,candidate.dut.state,baseline.dut.state);')
assert diagnostic!=original
(D/'diagnostic_original_cadence_tb.v').write_text(diagnostic)
fixed=diagnostic.replace('if(cycles%2500==0)begin','if(cycles%20000==0)begin')
assert fixed!=diagnostic
(D/'slower_cadence_tb.v').write_text(fixed)
helper=['nav_math_service.v','position/position_math.v','position/ano_xy_stick.v','position/ano_xy_divide36.v','position/ano_z_stick.v']
receipt={'original_inputs_sha256':sha(O/'inputs.json'),'source55_B3':sources(B3),'source55_B4':sources(B4),
 'script_sha256':sha(Path(__file__)),'original_tb_sha256':sha(O/'aw_tb.v'),'diagnostic_tb_sha256':sha(D/'diagnostic_original_cadence_tb.v'),
 'slower_tb_sha256':sha(D/'slower_cadence_tb.v'),'harness_sha256':sha(O/'pair_harness.v'),'old_reference_sha256':sha(O/'b3_controller_reference.v'),
 'scope':'Only CASE5. Exact original assertions retained; diagnostic original-cadence run changes fatal text only. Corrected run changes only callback cadence2500->20000clocks, still sample_dt11000us/position_dt22000us. No RTL changes.'}
(D/'inputs.json').write_text(json.dumps(receipt,indent=2)+'\n')
results=[]
for name,tb,expected_exit in [('diagnose_original_cadence','diagnostic_original_cadence_tb.v',1),('corrected_xy_i0','slower_cadence_tb.v',0)]:
    run=D/name;run.mkdir(exist_ok=True)
    binary=run/'simulation.vvp'
    cmd=[str(B/'iverilog.exe'),'-g2012','-s','tb','-o',str(binary),str(D/tb),str(O/'pair_harness.v'),str(O/'b3_controller_reference.v'),str(B4/'position/mtf_xyz_hold_control.v'),*[str(B4/p) for p in helper]]
    c=subprocess.run(cmd,env=env,capture_output=True,text=True);(run/'compile.log').write_text(c.stdout+c.stderr)
    assert c.returncode==0,c.stdout+c.stderr
    start=time.time()
    with (run/'simulation.log').open('w') as f:p=subprocess.run([str(B/'vvp.exe'),str(binary),'+CASE=5'],cwd=run,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=400)
    output=(run/'simulation.log').read_text()
    row={'name':name,'actual_exit_code':p.returncode,'expected_exit_code':expected_exit,'compile_exit_code':c.returncode,
         'seconds':time.time()-start,'checks':[x for x in output.splitlines() if x.startswith('PASS')],
         'log_sha256':sha(run/'simulation.log'),'trace_sha256':sha(run/'trace.csv'),'local_compiled_omitted_sha256':sha(binary)}
    results.append(row);(D/'results.json').write_text(json.dumps({'results':results},indent=2)+'\n');print(output,flush=True)
    assert p.returncode==expected_exit,output
    if expected_exit==1:assert 'reason=128/128' in output and 'new=1/1 old=1/1' in output,output
    else:assert len(row['checks'])>=2,output
assert sources(B3)==oldinputs['B3_source55'] and sources(B4)==oldinputs['B4_source55']
(O/'source_stability.json').write_text(json.dumps({'B3_source55_unchanged':True,'B4_source55_unchanged':True,
 'first_attempt_inputs_sha256':sha(O/'inputs.json'),'retry_inputs_sha256':sha(D/'inputs.json'),
 'scope':'Both source55 sets remain equal to original inputs before original compile, after cases1-4, after diagnosed artificial overrun and after corrected I0 run.'},indent=2)+'\n')
first=json.loads((O/'results.json').read_text())
assert all(r['exit_code']==0 for r in first['results'][:4]) and first['results'][4]['exit_code']==1
aggregate={'passed':True,'case_count':5,'scope':'Five bounded actual RTL regressions; original cases1-4 plus slower-cadence CASE5. Original failed artificial-overrun case and exact diagnosis retained. No source changes, no private force, no plant/flight replay. Z-only cadence2500clocks and XY+Z cadence20000clocks; arithmeticdt unchanged.',
 'first_attempt_results_sha256':sha(O/'results.json'),'retry_results_sha256':sha(D/'results.json'),
 'successful_cases':first['results'][:4]+[{'case':5,**results[-1]}],
 'diagnosed_failure':results[0],'source_stability_sha256':sha(O/'source_stability.json')}
(O/'final_results.json').write_text(json.dumps(aggregate,indent=2)+'\n')
