"""Actual old/new complete-fusion differential, same-clock expiry and exact top13."""
from pathlib import Path
import datetime,hashlib,json,os,re,subprocess,sys,time
O=Path(__file__).resolve().parent;R=O.parents[3];D=O/'proofs'
OLD=R/'out/z_aw_fix_20261026/compact_aw_v11/canonical/source';NEW=R/'out/z_aw_fix_20261026/compact_aw_v12/canonical/source'
IV=R.parents[1]/'.tools/iverilog/app/bin/iverilog.exe';VVP=IV.with_name('vvp.exe')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text())
before={'old':read(O.parent/'compact_aw_v11/source_freeze.json')['source55'],'new':read(O/'source_freeze.json')['source55']}
for tag,s in [('old',OLD),('new',NEW)]:assert {p:sha(s/p) for p in before[tag]}==before[tag]
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

fixture=O.parent/'compact_aw_v8/proofs_completion02/fusion_tb.v';tb=fixture.read_text()
tb=tb.replace('height_v7 #(','height_old #(').replace('height_v8 #(','height_new #(')
needle='.RANGE_AGE_PRECHECKED(PRE)) d0(';assert tb.count(needle)==1
tb=tb.replace(needle,'.RANGE_AGE_PRECHECKED(PRE),.PRECHECKED_AZ_RANGE(1)) d0(')
needle='.ref_height_mm(refh),.az_up_mmps2(rawaz),';pos=tb.index(needle,tb.index('height_old #('))
tb=tb[:pos]+tb[pos:].replace(needle,needle+'.az_range_ok(rawaz>=-30000 && rawaz<=30000),',1)
needle='  #1;\n  if(pub0!==pub1';assert tb.count(needle)==1
tb=tb.replace(needle,"  #1;\n  if(d0.publication_age!==d1.publication_age || d1.publication_fresh!==(d0.publication_age<5000000))$fatal(1,\"age/predicate invariant ordinary cycle%0d\",cycles);\n  if(pub0!==pub1")
tb='`default_nettype none\n'+tb+'\n`default_nettype wire\n';(D/'fusion_tb.v').write_text(tb)
for label,s in [('old',OLD),('new',NEW)]:
    text=(s/'position/mtf_shared_height_fusion.v').read_text();needle='module mtf_shared_height_fusion #(';assert text.count(needle)==1
    (D/(label+'_height.v')).write_text(text.replace(needle,'module height_'+label+' #(',1))

# Actual modules and real arithmetic services; no force/preset of DUT state.
# A response stall models the shared-service boundary, allowing a16-bit age
# carry and timeout before the original pending-height fault cleans the epoch.
head=tb.split(' always @(posedge clk) begin',1)[0]
head=head.replace(' parameter PRE=0;',' parameter PRE=0,AGE=31;\n reg stall=0;').replace('.AGE_LIMIT(5000000)','.AGE_LIMIT(AGE)')
head=head.replace('if(!rst_n || origin || !rv','if(stall || !rst_n || origin || !rv')
for i in [0,1]:
    for kind in ['mul','div']:
        b='mbusy' if kind=='mul' else 'dbusy';d='md' if kind=='mul' else 'dd'
        a=f'.math_{kind}_busy({b}[{i}])';assert head.count(a)==1;head=head.replace(a,f'.math_{kind}_busy({b}[{i}]|stall)')
        a=f'.math_{kind}_done({d}[{i}])';assert head.count(a)==1;head=head.replace(a,f'.math_{kind}_done({d}[{i}]&&!stall)')
tail=r'''
 integer expiry_edges=0,last_good=0,pub_count=0,checks=0;
 always @(posedge clk)begin
  cycles=cycles+1;#1;checks=checks+1;
  if(pub0!==pub1 || req0!==req1 || svc0!==svc1 || d0.sources_ok!==d1.sources_ok || d0.publication_age!==d1.publication_age)
   $fatal(1,"full-module expiry differential AGE=%0d PRE=%0d cycle=%0d",AGE,PRE,cycles);
  if(d1.publication_fresh!==(d0.publication_age<AGE))$fatal(1,"same-age predicate AGE=%0d age=%h flag=%b",AGE,d0.publication_age,d1.publication_fresh);
  if(up[0])begin
   pub_count=pub_count+1;
   if(d0.publication_age!==0 || d1.publication_fresh!==1 || ready[0]!==1 || ready[1]!==1)$fatal(1,"publication must restore freshness same clock");
  end
  if(d0.publication_age==AGE-1 && d0.seen && !d0.cleanup && !d0.fault)begin
   if(!ready[0] || !ready[1] || !d1.publication_fresh)$fatal(1,"freshness revoked early AGE=%0d",AGE);
   last_good=last_good+1;
  end
  if(d0.publication_age==AGE && d0.seen && !d0.cleanup && !d0.fault)begin
   if(ready[0] || ready[1] || tail[0] || tail[1] || d1.publication_fresh)$fatal(1,"timeout granted an extra clock AGE=%0d",AGE);
   expiry_edges=expiry_edges+1;
  end
  if(cycles>700000)$fatal(1,"bounded expiry fixture timeout");
 end
 initial begin
  repeat(8)@(negedge clk);rst_n=1;
  while(!up[0])@(negedge clk);
  if(AGE>=65536)stall=1;
  repeat(AGE+10000)@(negedge clk);
  if(expiry_edges!=1 || last_good!=1 || pub_count!=1)$fatal(1,"expiry coverage AGE=%0d lastgood=%0d expiry=%0d pub=%0d",AGE,last_good,expiry_edges,pub_count);
  origin=1;repeat(3)@(negedge clk);origin=0;stall=0;
  while(!up[0])@(negedge clk);
  if(pub_count<2)$fatal(1,"no unforced republish after epoch cancellation");
  $display("PASS expiry AGE=%0d PRE=%0d cycles=%0d same_age_checks=%0d exact_expiry_edges=%0d last_good_edges=%0d publications=%0d no_DUT_state_force=1",AGE,PRE,cycles,checks,expiry_edges,last_good,pub_count);$finish;
 end
endmodule
`default_nettype wire
'''
(D/'expiry_tb.v').write_text(head+tail)
top=R/'analysis/20261026_z_aw_fix/width_integration/verify_top_safety.py';text=top.read_text()
needle='REPO=Path(__file__).resolve().parents[3]';assert text.count(needle)==1;text=text.replace(needle,'REPO=Path('+repr(str(R))+')').replace('compact_aw_v4/canonical','compact_aw_v12/canonical')
(D/'top/run.py').write_text(text)
deps=['position/mtf_xyz_hold_control.v','nav_math_service.v','position/position_math.v','position/ano_xy_stick.v','position/ano_xy_divide36.v','position/ano_z_stick.v']
prior=O.parent/'compact_aw_v9/proofs_retry02';control=read(prior/'results.json');assert control['passed'] and read(prior/'runner_exit.json')['actual_p_wait']==0
assert all(before['new'][p]==control['source55'][p] for p in deps)

# Exact source expressions, tested with the original integer parameter type.
limits=[0,1,31,65536,5000000,0x7fffffff,0x80000000,0xfffffffe,0xffffffff]
oldtext=(OLD/'position/mtf_shared_height_fusion.v').read_text();newtext=(NEW/'position/mtf_shared_height_fusion.v').read_text()
oldexpr="((publication_age+32'd1)<AGE_LIMIT)";newexpr="((AGE_LIMIT!=0)&&(publication_age<(AGE_LIMIT-32'd1)))"
assert oldtext.count('publication_fresh<='+oldexpr)==1 and newtext.count('publication_fresh<='+newexpr)==1
model='module pred #(parameter integer AGE_LIMIT=5000000)(input wire [31:0] publication_age,output wire same);\nwire a='+oldexpr+';wire b='+newexpr+';assign same=(publication_age==32\'hffffffff)||(a===b);endmodule\n'
pred='`timescale 1ns/1ps\n`default_nettype none\n'+model+'module predicate_tb;reg[31:0]publication_age=0;wire[8:0]same;integer checks=0,n;reg[31:0]rng=32\'h9c137ac5;\n'
for i,lim in enumerate(limits):pred+=f"pred #(.AGE_LIMIT(32'h{lim:08x})) p{i}(.publication_age(publication_age),.same(same[{i}]));\n"
pred+="task check;input[31:0]x;begin publication_age=x;#1;if(same!==9'h1ff)$fatal(1,\"unsigned rewrite mismatch A=%h same=%h\",x,same);checks=checks+1;end endtask\ninitial begin\n"
values=[0,1,0xfffffffe,0xffffffff]+[((lim+k)&0xffffffff) for lim in limits for k in [-2,-1,0,1]]
for value in values:pred+=f"check(32'h{value:08x});\n"
pred+="for(n=0;n<200000;n=n+1)begin rng=(rng*32'd1664525)+32'd1013904223;check(rng);end\n$display(\"PASS predicate vectors=%0d integer_limits=9 eligible_increment_age_excludes_MAX=1\",checks);$finish;end\nendmodule\n`default_nettype wire\n"
(D/'predicate_tb.v').write_text(pred)

(D/'inputs.json').write_text(json.dumps({'source55':before,'runner_sha256':sha(Path(__file__)),'original_fusion_fixture_sha256':sha(fixture),
    'fixtures':{p.relative_to(D).as_posix():sha(p) for p in D.rglob('*') if p.is_file() and (p.suffix=='.v' or p==D/'top/run.py')},'tools':{str(p):sha(p) for p in [IV,VVP]},
    'scope':'Full old/new modules with actual mathematical services; no internal DUT force. Ordinary PRE0/1 plus exact timeout AGE1/31/65536, with service-response stall only for16bit carry. Top13 retains its documented core-input forces.',
    'reused_control_results_sha256':sha(prior/'results.json'),'exact_control_dependencies':{p:before['new'][p] for p in deps}},indent=2)+'\n')
run('predicate_compile',[str(IV),'-g2012','-Wall','-s','predicate_tb','-o',str(D/'predicate.vvp'),str(D/'predicate_tb.v')])
predicate_log=run('predicate_simulation',[str(VVP),str(D/'predicate.vvp')]);assert 'PASS predicate vectors=200040 integer_limits=9' in predicate_log
records=[]
for pre in [0,1]:
    name=f'fusion_pre{pre}';exe=D/(name+'.vvp')
    run(name+'_compile',[str(IV),'-g2012','-Wall','-s','tb',f'-Ptb.PRE={pre}','-o',str(exe),str(D/'fusion_tb.v'),str(D/'old_height.v'),str(D/'new_height.v'),str(NEW/'nav_math_service.v'),str(NEW/'position/position_math.v')])
    log=run(name+'_simulation',[str(VVP),str(exe)]);assert re.search(r'^PASS PRE='+str(pre)+r' ',log,re.M);records.append({'kind':'ordinary','PRE':pre,'pass_lines':[x for x in log.splitlines() if x.startswith('PASS ')]})
    for age in [1,31,65536]:
        name=f'expiry_pre{pre}_age{age}';exe=D/(name+'.vvp')
        run(name+'_compile',[str(IV),'-g2012','-Wall','-s','tb',f'-Ptb.PRE={pre}',f'-Ptb.AGE={age}','-o',str(exe),str(D/'expiry_tb.v'),str(D/'old_height.v'),str(D/'new_height.v'),str(NEW/'nav_math_service.v'),str(NEW/'position/position_math.v')])
        log=run(name+'_simulation',[str(VVP),str(exe)]);assert re.search(r'^PASS expiry AGE='+str(age)+r' PRE='+str(pre)+r' ',log,re.M);records.append({'kind':'expiry','PRE':pre,'AGE':age,'pass_lines':[x for x in log.splitlines() if x.startswith('PASS ')]})
run('top13',[sys.executable,'-B',str(D/'top/run.py')]);assert read(D/'top/top_safety_results.json')['passed']
for tag,s in [('old',OLD),('new',NEW)]:assert {p:sha(s/p) for p in before[tag]}==before[tag]
(D/'results.json').write_text(json.dumps({'passed':True,'source55':before['new'],'source55_unchanged':True,'records':records,'stages':stages,
    'top13':read(D/'top/top_safety_results.json'),'reused_control_results_sha256':sha(prior/'results.json'),'exact_control_dependencies':deps,
    'scope':'Functional proof only; no synthesis, physical/hardware qualification.'},indent=2)+'\n')
print('PASS v12 predicate/full fusion/expiry/top13; controller proofs reused by exact dependency hashes.',flush=True)
