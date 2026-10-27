"""Full UART reader differential, extracted inductive transitions and actual top13."""
from pathlib import Path
import datetime, hashlib, json, os, re, subprocess, sys, time
O=Path(__file__).resolve().parent;R=O.parents[3];D=O/'proofs'
OLD=R/'out/z_aw_fix_20261026/compact_aw_v12/canonical/source'
NEW=R/'out/z_aw_fix_20261026/compact_aw_v13/canonical/source'
IV=R.parents[1]/'.tools/iverilog/app/bin/iverilog.exe';VVP=IV.with_name('vvp.exe')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf8'))
freeze=read(O/'source_freeze.json');expected=freeze['source55'];old55=freeze['baseline_source55']
assert {n:sha(OLD/n) for n in old55}==old55 and {n:sha(NEW/n) for n in expected}==expected
assert [n for n in expected if expected[n]!=old55[n]]==['sensor/mtf01p_reader.v']
assert sha(O/'source_review.md')==freeze['source_review_sha256']
parent=O.parent/'compact_aw_v12/PROOF_BINDING.json';binding=read(parent)
assert binding['passed'] and binding['source55']==old55 and binding['actual_proof_runner_wait']==0
assert not (D/'inputs.json').exists();D.mkdir(exist_ok=True);(D/'tmp').mkdir();(D/'top').mkdir()
env=dict(os.environ,TMP=str(D/'tmp'),TEMP=str(D/'tmp'),TMPDIR=str(D/'tmp'))
stages=[]
def run(name,command,timeout=600):
    log=D/(name+'.log');rec={'command':command,'cwd':str(D),'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()};start=time.time()
    with log.open('wb') as out:
        p=subprocess.Popen(command,cwd=D,env=env,stdin=subprocess.DEVNULL,stdout=out,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
        rec['pid']=p.pid;(D/(name+'_process.json')).write_text(json.dumps(rec,indent=2)+'\n')
        try:code=p.wait(timeout=timeout)
        except subprocess.TimeoutExpired:p.kill();code=p.wait();rec['timeout_kill_own_child']=True
    rec.update(actual_p_wait=code,normal_wait_return=True,seconds=time.time()-start,ended_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),log_sha256=sha(log))
    (D/(name+'_exit.json')).write_text(json.dumps(rec,indent=2)+'\n');stages.append(rec);print(name,'actual_wait',code,flush=True)
    assert code==0,(name,log.read_text(errors='replace'))
    return log.read_text(errors='replace')

for tag,root in [('old',OLD),('new',NEW)]:
    text=(root/'sensor/mtf01p_reader.v').read_text()
    for name in ['mtf_uart_rx','micolink_parser','mtf_metric_observer','mtf01p_reader']:
        assert len(re.findall(r'\bmodule\s+'+name+r'\b',text))==1
        text=re.sub(r'\b'+name+r'\b',tag+'_'+name,text)
    (D/(tag+'_reader.v')).write_text(text,encoding='utf8')
(D/'reader_tb.v').write_bytes((O/'reader_tb.v').read_bytes())

# The actual age block is wrapped with a fixture-only reseed branch. Each trial
# assumes the invariant and checks one original transition for arbitrary known
# 32-bit age, including MAX-1->MAX. No full reader DUT is forced or preset.
models='`timescale 1ns/1ps\n`default_nettype none\n'
for tag,root in [('old',OLD),('new',NEW)]:
    text=(root/'sensor/mtf01p_reader.v').read_text()
    start=text.index(" reg [31:0] age_ms=32'hffffffff,age_previous_time=0;reg age_seen=0;")
    end=text.index(' // P2 module offline indication',start)
    block=text[start:end]
    prefix='module age_'+tag+'''(input wire clk,rst_n,sample_valid,tick_ms,seed,
 input wire[31:0]time_ms,seed_age,seed_previous,input wire seed_seen,
 output wire[31:0]age,previous,output wire seen,f1000,f200);
'''
    inject=' always @(posedge clk)begin\n  if(seed)begin age_ms<=seed_age;age_previous_time<=seed_previous;age_seen<=seed_seen;'
    if tag=='new':inject+='age_below_1000<=seed_age<1000;age_below_200<=seed_age<200;'
    inject+='end else begin'
    assert block.count(' always @(posedge clk)begin')==1
    block=block.replace(' always @(posedge clk)begin',inject)
    suffix='\n end\n assign age=age_ms;assign previous=age_previous_time;assign seen=age_seen;\n'
    suffix+=' assign f1000='+('age_below_1000' if tag=='new' else '(age_ms<1000)')+';\n'
    suffix+=' assign f200='+('age_below_200' if tag=='new' else '(age_ms<200)')+';\nendmodule\n'
    models+=prefix+block+suffix
(D/'age_models.v').write_text(models+'`default_nettype wire\n')
tb=r'''`timescale 1ns/1ps
`default_nettype none
module age_tb;
 reg clk=0,rst_n=1,sample_valid=0,tick_ms=0,seed=0,seed_seen=0;
 reg[31:0]time_ms=0,seed_age=0,seed_previous=0,rng=32'h876c2bd9;
 always #5 clk=~clk;
 wire[31:0]a0,a1,p0,p1;wire s0,s1,b0,b1,c0,c1;
 age_old d0(.*,.age(a0),.previous(p0),.seen(s0),.f1000(b0),.f200(c0));
 age_new d1(.*,.age(a1),.previous(p1),.seen(s1),.f1000(b1),.f200(c1));
 integer checks=0,n,j;
 task trial;input[31:0]a;input integer mode;begin
  @(negedge clk);seed=1;seed_age=a;seed_previous=rng;seed_seen=mode[0];
  @(negedge clk);seed=0;rst_n=mode[1];sample_valid=mode[2];tick_ms=mode[3];time_ms=mode[4] ? seed_previous:~seed_previous;
  if(mode[5])sample_valid=1'bx;if(mode[6])tick_ms=1'bx;
  if(mode[7])rst_n=1'bx;if(mode[8])time_ms=32'hxxxxxxxx;
  @(posedge clk);#1;
  if({a0,p0,s0,b0,c0}!=={a1,p1,s1,b1,c1})$fatal(1,"age transition mismatch age=%h mode=%h",a,mode);
  if(b1!==(a1<1000) || c1!==(a1<200))$fatal(1,"age transition invariant failed");
  checks=checks+1;
 end endtask
 initial begin
  for(j=0;j<512;j=j+1)begin
   trial(0,j);trial(198,j);trial(199,j);trial(200,j);trial(998,j);trial(999,j);trial(1000,j);
   trial(32'hfffffffe,j);trial(32'hffffffff,j);trial(32'h0000ffff,j);trial(32'h7fffffff,j);
  end
  for(n=0;n<100000;n=n+1)begin rng=rng*32'd1664525+32'd1013904223;trial(rng,n%512);end
  $display("PASS inductive vectors=%0d known_age32=1 four_state_control=1 arbitrary_invariant_state_fixture=1 no_full_reader_DUT_force=1",checks);$finish;
 end
endmodule
`default_nettype wire
'''
(D/'age_tb.v').write_text(tb)
top=R/'analysis/20261026_z_aw_fix/width_integration/verify_top_safety.py';text=top.read_text()
needle='REPO=Path(__file__).resolve().parents[3]';assert text.count(needle)==1
text=text.replace(needle,'REPO=Path('+repr(str(R))+')').replace('compact_aw_v4/canonical','compact_aw_v13/canonical')
(D/'top/run.py').write_text(text)
fixtures={p.relative_to(D).as_posix():sha(p) for p in D.rglob('*') if p.is_file() and (p.suffix=='.v' or p==D/'top/run.py')}
inputs={'source55':expected,'baseline_source55':old55,'fixtures':fixtures,'tools':{str(p):sha(p) for p in [IV,VVP]},
        'parent_proof_binding_sha256':sha(parent),'source_review_sha256':sha(O/'source_review.md'),
        'scope':'Complete actual UART reader at1.152MHz for feasible millisecond expiry; extracted actual age logic with independent tick tests arbitrary32bit transitions. Full top remains50MHz. No DUT state force in full-reader test.'}
(D/'inputs.json').write_text(json.dumps(inputs,indent=2)+'\n')
run('inductive_compile',[str(IV),'-g2012','-s','age_tb','-o',str(D/'age.vvp'),str(D/'age_models.v'),str(D/'age_tb.v')])
log=run('inductive_simulation',[str(VVP),str(D/'age.vvp')]);assert 'PASS inductive vectors=105632' in log
records=[]
for mode in [0,1]:
    name=f'uart_mode{mode}';exe=D/(name+'.vvp')
    run(name+'_compile',[str(IV),'-g2012','-s','reader_tb','-P',f'reader_tb.MODE={mode}','-o',str(exe),str(D/'old_reader.v'),str(D/'new_reader.v'),str(D/'reader_tb.v')])
    log=run(name+'_simulation',[str(VVP),str(exe)]);assert f'PASS UART MODE={mode} ' in log
    records.append({'mode':mode,'pass_lines':[x for x in log.splitlines() if x.startswith('PASS ')]})
run('top13',[sys.executable,'-B',str(D/'top/run.py')]);assert read(D/'top/top_safety_results.json')['passed']
assert fixtures=={n:sha(D/n) for n in fixtures}
assert {n:sha(NEW/n) for n in expected}==expected and {n:sha(OLD/n) for n in old55}==old55
assert sha(parent)==inputs['parent_proof_binding_sha256']
(D/'results.json').write_text(json.dumps({'passed':True,'source55':expected,'stages':stages,'UART':records,
    'inductive_log_sha256':sha(D/'inductive_simulation.log'),'fixtures_unchanged':True,
    'parent_proof_binding_sha256':sha(parent),'top13':read(D/'top/top_safety_results.json'),
    'reused_scope':'All v12 source and behavior proofs except changed reader. Controller, fusion, AZ producer and math dependencies unchanged by exact55 comparison.'},indent=2)+'\n')
print('PASS v13 full UART reader/inductive age/top13; v12 dependencies reused by exact hashes.',flush=True)
