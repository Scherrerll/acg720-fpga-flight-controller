"""Producer invariant + real fusion differential + top safety, isolated offline."""
from pathlib import Path
import datetime,hashlib,json,os,re,subprocess,sys,time
sys.dont_write_bytecode=True
BASE=Path(__file__).resolve().parent; R=BASE.parents[3]; O=BASE/'proofs_completion02'
OLD=R/'out/z_aw_fix_20261026/compact_aw_v7/canonical/source'
NEW=R/'out/z_aw_fix_20261026/compact_aw_v8/canonical/source'
IV=R.parents[1]/'.tools/iverilog/app/bin/iverilog.exe';VVP=IV.with_name('vvp.exe')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text())
before={'v7':read(BASE.parent/'compact_aw_v7/source_freeze.json')['source55'],'v8':read(BASE/'source_freeze.json')['source55']}
for tag,root in [('v7',OLD),('v8',NEW)]:assert {p:sha(root/p) for p in before[tag]}==before[tag]
assert O.is_dir() and not (O/'inputs.json').exists()
(O/'tmp').mkdir();env=dict(os.environ,TMP=str(O/'tmp'),TEMP=str(O/'tmp'),TMPDIR=str(O/'tmp'))
(O/'inputs.json').write_text(json.dumps({'source55':before,'runner_sha256':sha(Path(__file__)),
    'tools':{str(p):sha(p) for p in [IV,VVP]},'scope':'Actual RTL, no serial/hardware, no private state forces in producer/fusion. Existing top safety fixture retains documented gate forces.'},indent=2)+'\n')
stages=[]
def run(name,command,timeout=300):
    if name in ['adapter_compile','adapter_simulation','fusion_pre0_compile','fusion_pre0_simulation']:
        previous=BASE/'proofs';receipt=previous/(name+'_exit.json');r=read(receipt)
        assert r['actual_p_wait']==0 and r['normal_wait_return'] and sha(previous/(name+'.log'))==r['log_sha256']
        reuse={'kind':'reuse_completed_actual_stage','receipt':str(receipt),'receipt_sha256':sha(receipt),'actual_p_wait':r['actual_p_wait'],'log':str(previous/(name+'.log')),'log_sha256':r['log_sha256']}
        (O/(name+'_reuse.json')).write_text(json.dumps(reuse,indent=2)+'\n');stages.append(reuse)
        print(name,'reuse prior actual_wait0',flush=True)
        return (previous/(name+'.log')).read_text(errors='replace')
    log=O/(name+'.log');start=time.time()
    record={'command':command,'cwd':str(O),'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
    with log.open('wb') as output:
        p=subprocess.Popen(command,cwd=O,env=env,stdin=subprocess.DEVNULL,stdout=output,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
        record['pid']=p.pid
        (O/(name+'_process.json')).write_text(json.dumps(record,indent=2)+'\n')
        try:code=p.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            p.kill();code=p.wait();record['timeout_kill']=True
    record.update(actual_p_wait=code,normal_wait_return=True,seconds=time.time()-start,log_sha256=sha(log),ended_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
    (O/(name+'_exit.json')).write_text(json.dumps(record,indent=2)+'\n');stages.append(record)
    print(name,'actual_wait',code,'seconds',round(record['seconds'],3),flush=True)
    assert code==0,(name,log.read_text(errors='replace'))
    return log.read_text(errors='replace')

old=(OLD/'position/pose_time_adapter.v').read_text().replace('module pose_time_adapter(', 'module pose_time_adapter_v7(',1)
(O/'adapter_v7.v').write_text(old)
adapter_tb=r'''`timescale 1ns/1ps
module tb;
reg clk=0;always #10 clk=~clk;
reg rst_n=1,cancel=0,start=0,av=0;
reg [31:0] ticks=0;reg signed [31:0] ax=0,ay=0,az=0;
wire [1:0] up,valid,busy;wire [31:0] dt[0:1];wire signed [31:0] x[0:1],y[0:1],z[0:1];wire [7:0] fault[0:1];wire z_ok;
pose_time_adapter_v7 a(.clk(clk),.rst_n(rst_n),.cancel(cancel),.start(start),.acc_valid(av),.ticks(ticks),.ax(ax),.ay(ay),.az(az),.update(up[0]),.dt_us(dt[0]),.output_ax(x[0]),.output_ay(y[0]),.output_az(z[0]),.output_acc_valid(valid[0]),.busy(busy[0]),.fault(fault[0]));
pose_time_adapter b(.clk(clk),.rst_n(rst_n),.cancel(cancel),.start(start),.acc_valid(av),.ticks(ticks),.ax(ax),.ay(ay),.az(az),.update(up[1]),.dt_us(dt[1]),.output_ax(x[1]),.output_ay(y[1]),.output_az(z[1]),.output_az_range_ok(z_ok),.output_acc_valid(valid[1]),.busy(busy[1]),.fault(fault[1]));
integer cycles=0,publications=0,faultcycles=0,invalidpub=0,unknownpub=0,cancels=0,checks=0;
always @(posedge clk)begin
 cycles=cycles+1;#1;
 if({up[0],dt[0],x[0],y[0],z[0],valid[0],busy[0],fault[0]}!=={up[1],dt[1],x[1],y[1],z[1],valid[1],busy[1],fault[1]})$fatal(1,"adapter output mismatch at cycle%0d",cycles);
 if(z_ok !== (z[1]>=-30000 && z[1]<=30000))$fatal(1,"same tuple numeric predicate mismatch at cycle%0d z=%h flag=%b",cycles,z[1],z_ok);
 checks=checks+1;
 if(up[0])begin
  publications=publications+1;
  if(z_ok===0)invalidpub=invalidpub+1;
  if(z_ok===1'bx)unknownpub=unknownpub+1;
 end
 if(fault[0]!=0)faultcycles=faultcycles+1;
 if(cancel)cancels=cancels+1;
end
function [31:0] sample;
 input integer n;
 begin case(n%16)
  0:sample=0;1:sample=30000;2:sample=-30000;3:sample=30001;4:sample=-30001;
  5:sample=32'h7fffffff;6:sample=32'h80000000;7:sample=32'hffffffff;
  8:sample=32'h0000xxxx;9:sample=32'hzzzzzzzz;10:sample=32'h0000000x;
  default:sample=$random;
 endcase end
endfunction
integer n,j;
initial begin
 repeat(3)@(negedge clk);
 for(n=0;n<12000;n=n+1)begin
  rst_n=1;cancel=1;start=0;@(negedge clk);cancel=0;
  ticks=$random;ax=$random;ay=$random;az=sample(n);av=n%2;start=1;@(negedge clk);start=0;
  for(j=0;j<35;j=j+1)begin
   // Vary unlatched source data while busy. Only the accepted tuple may publish.
   ax=$random;ay=$random;az=$random;ticks=$random;av=~av;
   if(n%31==0 && j==8)cancel=1;
   if(n%31==0 && j==9)cancel=0;
   if(n%37==0 && j==12)start=1;
   if(n%37==0 && j==13)start=0;
   if(n%41==0 && j==20)rst_n=0;
   if(n%41==0 && j==21)rst_n=1;
   @(negedge clk);
  end
 end
 if(publications<10000 || faultcycles<100 || invalidpub<100 || unknownpub<100 || cancels<12000)$fatal(1,"insufficient adapter coverage");
 $display("PASS adapter cycles=%0d publications=%0d invalidpub=%0d unknownpub=%0d faultcycles=%0d cancelcycles=%0d same_tuple_checks=%0d",cycles,publications,invalidpub,unknownpub,faultcycles,cancels,checks);$finish;
end
endmodule
'''
(O/'adapter_tb.v').write_text(adapter_tb)
run('adapter_compile',[str(IV),'-g2012','-s','tb','-o',str(O/'adapter.vvp'),str(O/'adapter_tb.v'),str(O/'adapter_v7.v'),str(NEW/'position/pose_time_adapter.v')])
adapter_log=run('adapter_simulation',[str(VVP),str(O/'adapter.vvp')])
assert adapter_log.startswith('PASS adapter ')

# Frozen completion03 test covers all publication-stage bad-az pulses, requests,
# math services, epoch cancellation, real arithmetic and both age modes.
fixture=R/'analysis/20261026_z_aw_fix/numeric_guard_fusion/completion03/tb.v'
tb=fixture.read_text().replace('height_v5 #(', 'height_v7 #(').replace('height_v6 #(', 'height_v8 #(')
needle='.RANGE_AGE_PRECHECKED(PRE)) d1('
assert tb.count(needle)==1
tb=tb.replace(needle,'.RANGE_AGE_PRECHECKED(PRE),.PRECHECKED_AZ_RANGE(1)) d1(')
needle='.ref_height_mm(refh),.az_up_mmps2(rawaz),';assert tb.count(needle)==2
pos=tb.index(needle,tb.index('height_v8 #('))
tb=tb[:pos]+tb[pos:].replace(needle,needle+'.az_range_ok(rawaz>=-30000 && rawaz<=30000),',1)
(O/'fusion_tb.v').write_text(tb)
for tag,root in [('v7',OLD),('v8',NEW)]:
    text=(root/'position/mtf_shared_height_fusion.v').read_text().replace('module mtf_shared_height_fusion #(',f'module height_{tag} #(',1)
    (O/(tag+'_height.v')).write_text(text)
fusion=[]
for pre in [0,1]:
    exe=O/f'fusion_pre{pre}.vvp'
    run(f'fusion_pre{pre}_compile',[str(IV),'-g2012','-s','tb',f'-Ptb.PRE={pre}','-o',str(exe),str(O/'fusion_tb.v'),str(O/'v7_height.v'),str(O/'v8_height.v'),str(OLD/'nav_math_service.v'),str(OLD/'position/position_math.v')])
    log=run(f'fusion_pre{pre}_simulation',[str(VVP),str(exe)],600)
    pass_lines=[line for line in log.splitlines() if line.startswith('PASS ')]
    assert len(pass_lines)==1 and re.fullmatch(r'PASS ((?:\w+=\d+ ?)+)',pass_lines[0]),log
    fusion.append(dict(re.findall(r'(\w+)=(\d+)',log)))

# Retain all thirteen substantive top safety cases; source/output paths only.
fixture_top=R/'analysis/20261026_z_aw_fix/aw_storage_integration/verify_top_safety.py'
text=fixture_top.read_text().replace("'compact_aw_v7/canonical'","'compact_aw_v8/canonical'")
text=text.replace("REPO/'out/z_aw_fix_20261026/compact_aw_v7/canonical'", "REPO/'out/z_aw_fix_20261026/compact_aw_v8/canonical'")
text=text.replace("O=Path(__file__).resolve().parent;O.mkdir(exist_ok=True);", "O=Path(__file__).resolve().parent/'top';O.mkdir(exist_ok=False);")
text=text.replace('REPO=Path(__file__).resolve().parents[3]',f'REPO=Path({str(R)!r})')
assert 'compact_aw_v7/canonical' not in text
(O/'verify_top.py').write_text(text)
run('top13',[sys.executable,'-B',str(O/'verify_top.py')],300)
for tag,root in [('v7',OLD),('v8',NEW)]:assert {p:sha(root/p) for p in before[tag]}==before[tag]
unchanged=[p for p in before['v7'] if before['v7'][p]==before['v8'][p]]
reused=[R/'analysis/20261026_z_aw_fix'/p for p in ['aw_storage_regression/results.json','aw_storage_regression/source_stability.json','aw_storage_boundary/results.json','aw_storage_integration/contention/results.json']]
(O/'results.json').write_text(json.dumps({'passed':True,'source55_unchanged':True,'source55':before,
    'adapter':adapter_log.strip(),'fusion':fusion,'top13':read(O/'top/top_safety_results.json'),
    'reused_v7_proofs':{str(p.relative_to(R)):sha(p) for p in reused},'reuse_reason':'Controller and all six contention math/controller dependencies unchanged; four changed files separately exercised here.',
    'unchanged_source_files':unchanged,'stages':stages,'original_fusion_fixture_sha256':sha(fixture),'original_top_fixture_sha256':sha(fixture_top),
    'scope_limit':'Finite traces plus producer invariant argument. No plant/flight/physical qualification.'},indent=2)+'\n')
print('PASS v8 focused candidate proofs',flush=True)
