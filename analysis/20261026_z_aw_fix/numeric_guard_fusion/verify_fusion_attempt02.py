"""Finite, real-RTL v5/v6 height-fusion differential regression. No hardware."""
from pathlib import Path
import hashlib
import json
import os
import re
import subprocess
import sys
import time

O = Path(__file__).resolve().parent / 'attempt02'
O.mkdir(exist_ok=False)
R = O.parents[3]
OLD = R / 'out/z_aw_fix_20261026/compact_aw_v5/canonical/source'
NEW = R / 'out/z_aw_fix_20261026/compact_aw_v6/canonical/source'
IV = Path(r'C:\Users\ScherrerL\Desktop\apple\.tools\iverilog\app\bin\iverilog.exe')
VVP = IV.with_name('vvp.exe')

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def sources(root):
    return {p.relative_to(root).as_posix(): sha(p) for p in root.rglob('*') if p.is_file()}

before = {'v5': sources(OLD), 'v6': sources(NEW)}
assert len(before['v5']) == len(before['v6']) == 55
assert sorted(p for p in before['v5'] if before['v5'][p] != before['v6'][p]) == [
    'mtf_xyz_navigation_control.v', 'position/mtf_shared_height_fusion.v']
assert before['v5']['position/mtf_xyz_hold_control.v'] == before['v6']['position/mtf_xyz_hold_control.v'] == '04e75ada52551d5622af060efe38fda9aa66ff25199bfb67651f9ec5315ed873'
input_receipt = {'scope': 'Finite actual RTL differential regression; no private force, source edit, synthesis, PNR, hardware or Git.',
                 'source55_before': before, 'runner_sha256': sha(Path(__file__)),
                 'iverilog': str(IV), 'iverilog_sha256': sha(IV),
                 'vvp': str(VVP), 'vvp_sha256': sha(VVP),
                 'clk_period_ns': 20, 'CLK_HZ_parameter': 5000000,
                 'height_period_ticks': 55000, 'acc_dt_us': 11000,
                 'AGE_LIMIT_ticks': 5000000, 'RANGE_AGE_PRECHECKED_runs': [0, 1]}
assert not (O / 'inputs.json').exists(), 'Never overwrite prior proof'
(O / 'inputs.json').write_text(json.dumps(input_receipt, indent=2) + '\n')
for tag, root in [('v5', OLD), ('v6', NEW)]:
    s = (root / 'position/mtf_shared_height_fusion.v').read_text()
    assert s.count('module mtf_shared_height_fusion #(') == 1
    (O / (tag + '_height.v')).write_text(s.replace('module mtf_shared_height_fusion #(', 'module height_' + tag + ' #(', 1))

declarations = '''
 wire [1:0] ms,mc,ds,dc,mbusy,md,dbusy,dd,de,mg,dg;
 wire signed [63:0] ma[0:1],mb[0:1],dn[0:1],mr[0:1],dr[0:1];
 wire [31:0] den[0:1];
 wire [1:0] valid,ready,qr,qv,up,vqok,tail,vraw;
 wire signed [31:0] h[0:1],vz[0:1],az[0:1],vq[0:1];
 wire [15:0] reason[0:1];
'''
instances = ''
for n, tag in enumerate(['v5', 'v6']):
    instances += f'''
 height_{tag} #(.CLK_HZ(5000000),.AGE_LIMIT(5000000),.CAL_MASK(8'h18),.RANGE_AGE_PRECHECKED(PRE)) d{n}(
 .clk(clk),.rst_n(rst_n),.origin_reset(origin),.range_valid(rv),.acc_valid(av),.acc_update(au),
 .acc_dt_us(32'd11000),.range_age_ticks(age),.ref_height_mm(refh),.az_up_mmps2(rawaz),
 .math_mul_start(ms[{n}]),.math_mul_cancel(mc[{n}]),.math_mul_a(ma[{n}]),.math_mul_b(mb[{n}]),
 .math_mul_busy(mbusy[{n}]),.math_mul_done(md[{n}]),.math_mul_result(mr[{n}]),
 .math_div_start(ds[{n}]),.math_div_cancel(dc[{n}]),.math_div_numerator(dn[{n}]),.math_div_denominator(den[{n}]),
 .math_div_busy(dbusy[{n}]),.math_div_done(dd[{n}]),.math_div_error(de[{n}]),.math_div_result(dr[{n}]),
 .valid(valid[{n}]),.estimate_ready(ready[{n}]),.qualified_ready(qr[{n}]),.qualified_valid(qv[{n}]),.update(up[{n}]),
 .fused_height_mm(h[{n}]),.vz_mmps(vz[{n}]),.sample_az_mmps2(az[{n}]),.vz_q16(vq[{n}]),.vz_q16_valid(vqok[{n}]),
 .reason(reason[{n}]),.estimate_ready_state_numeric_tail(tail[{n}]),.vz_q16_range_raw(vraw[{n}]));
 nav_math_service #(.CLIENTS(1),.DIVIDE(0)) m{n}(.clk(clk),.rst_n(rst_n),.request(ms[{n}]),.cancel(mc[{n}]),
 .operand_a(ma[{n}]),.operand_b(mb[{n}]),.busy(mbusy[{n}]),.done(md[{n}]),.error(),.result(mr[{n}]),.grant(mg[{n}]));
 nav_math_service #(.CLIENTS(1),.DIVIDE(1)) q{n}(.clk(clk),.rst_n(rst_n),.request(ds[{n}]),.cancel(dc[{n}]),
 .operand_a(dn[{n}]),.operand_b({{32'd0,den[{n}]}}),.busy(dbusy[{n}]),.done(dd[{n}]),.error(de[{n}]),.result(dr[{n}]),.grant(dg[{n}]));
'''

tb = r'''
`timescale 1ns/1ps
module tb;
 parameter PRE=0;
 reg clk=0; always #10 clk=~clk;
 reg rst_n=0,origin=0,rv=1,av=1,au=0;
 reg [31:0] age=0;
 reg signed [31:0] refh=300,rawaz=0;
 integer cycles=0,pubs=0,mcons=0,dcons=0,acccons=0;
 integer numeric_pulses=0,ready_numeric_pulses=0,commit_vetoes=0,epoch_pulses=0;
 integer age_rejects=0,age_bypasses=0,seeds=0,ready_cycles=0;
 integer acc_cadence=0;
 // Real 11,000us integration dt retained; only sample admission cadence and
 // height timer are accelerated. 10,000 clocks leaves arithmetic time to finish.
 always @(negedge clk) begin
  if(!rst_n || origin || !rv || !av || rawaz>30000 || rawaz< -30000 || refh<0 || refh>5000 || (!PRE && age>=5000000))begin au=0;acc_cadence=0;end
  else if(acc_cadence==9999)begin au=1;acc_cadence=0;end
  else begin au=0;acc_cadence=acc_cadence+1;end
 end
@DECL@
@INST@
 wire [151:0] pub0={valid[0],ready[0],qr[0],qv[0],up[0],h[0],vz[0],az[0],vq[0],vqok[0],reason[0],tail[0],vraw[0]};
 wire [151:0] pub1={valid[1],ready[1],qr[1],qv[1],up[1],h[1],vz[1],az[1],vq[1],vqok[1],reason[1],tail[1],vraw[1]};
 wire [227:0] req0={ms[0],mc[0],ma[0],mb[0],ds[0],dc[0],dn[0],den[0]};
 wire [227:0] req1={ms[1],mc[1],ma[1],mb[1],ds[1],dc[1],dn[1],den[1]};
 wire [134:0] svc0={mbusy[0],md[0],mr[0],dbusy[0],dd[0],de[0],dr[0],mg[0],dg[0]};
 wire [134:0] svc1={mbusy[1],md[1],mr[1],dbusy[1],dd[1],de[1],dr[1],mg[1],dg[1]};
 always @(posedge clk) begin
  cycles=cycles+1;
  if(rst_n && !d0.cleanup)begin
   if((d0.state==100 || d0.state==102) && md[0]) mcons=mcons+1;
   if(d0.state==101 && dd[0])begin
    dcons=dcons+1;
    if(de[0])$fatal(1,"unexpected real divider error");
    if(d0.return_state==70 || d0.return_state==72 || d0.return_state==73)acccons=acccons+1;
   end
   if(d0.state==80)seeds=seeds+1;
  end
  #1;
  if(pub0!==pub1 || req0!==req1 || svc0!==svc1 || d0.sources_ok!==d1.sources_ok)
   $fatal(1,"differential mismatch PRE=%0d cycle=%0d state=%0d/%0d pub=%h/%h req=%h/%h svc=%h/%h",PRE,cycles,d0.state,d1.state,pub0,pub1,req0,req1,svc0,svc1);
  if(up[0])pubs=pubs+1;
  if(ready[0])ready_cycles=ready_cycles+1;
  if(cycles>3000000)$fatal(1,"bounded global timeout");
 end
 task wait_ready;
 integer k;
 begin : wr
  for(k=0;k<90000;k=k+1)begin
   @(negedge clk);
   if(ready[0])disable wr;
  end
  $fatal(1,"no ready after legal source recovery PRE=%0d state=%0d fault=%0d",PRE,d0.state,d0.fault);
 end endtask
 task wait_publish_stage;
 integer k;
 begin : wp
  for(k=0;k<90000;k=k+1)begin
   @(negedge clk);
   if(d0.state==84 && ready[0])disable wp;
  end
  $fatal(1,"no live publish-stage boundary");
 end endtask
 task bad_numeric;
 input signed [31:0] x;
 begin
  wait_ready;wait_publish_stage;
  rawaz=x;numeric_pulses=numeric_pulses+1;
  #1;
  if(d0.sources_ok || d1.sources_ok || ready[0] || ready[1] || tail[0] || tail[1])$fatal(1,"bad az did not immediately revoke sources/tail");
  ready_numeric_pulses=ready_numeric_pulses+1;
  @(posedge clk);#2;
  if(up[0] || up[1] || !mc[0] || !mc[1] || !dc[0] || !dc[1])$fatal(1,"bad az publication veto/cancel failed");
  commit_vetoes=commit_vetoes+1;
  @(negedge clk);rawaz=0;
  wait_ready;
 end endtask
 task external_age;
 input [31:0] x;
 begin
  wait_ready;age=x;#1;
  if(PRE)begin
   if(!d0.sources_ok || !d1.sources_ok || !ready[0])$fatal(1,"prechecked range age unexpectedly checked");
   age_bypasses=age_bypasses+1;
  end else if(x>=5000000)begin
   if(d0.sources_ok || ready[0] || tail[0])$fatal(1,"range age threshold failed");
   age_rejects=age_rejects+1;
  end else if(!d0.sources_ok || !ready[0])$fatal(1,"age below threshold rejected");
  @(negedge clk);age=0;wait_ready;
 end endtask
 integer p0;
 initial begin
  repeat(8)@(negedge clk);rst_n=1;
  wait_ready;
  p0=pubs;repeat(330000)@(negedge clk);
  if(pubs-p0<5)$fatal(1,"normal zero-acc publications missing");
  rawaz=30000;refh=500;repeat(110000)@(negedge clk);
  if(!d0.sources_ok)$fatal(1,"+30000 not qualified");
  rawaz=-30000;refh=490;repeat(110000)@(negedge clk);
  if(!d0.sources_ok)$fatal(1,"-30000 not qualified");
  rawaz=0;repeat(55000)@(negedge clk);
  bad_numeric(30001);bad_numeric(-30001);bad_numeric(32'sh7fffffff);bad_numeric(32'sh80000000);
  wait_ready;origin=1;#1;if(ready[0])$fatal(1,"origin live revoke failed");
  @(posedge clk);#2;if(qr[0] || qv[0])$fatal(1,"origin qualified revoke failed");
  @(negedge clk);origin=0;epoch_pulses=epoch_pulses+1;wait_ready;
  rv=0;#1;if(d0.sources_ok || ready[0])$fatal(1,"range valid revoke failed");
  @(negedge clk);rv=1;epoch_pulses=epoch_pulses+1;wait_ready;
  av=0;#1;if(d0.sources_ok || ready[0])$fatal(1,"acc valid revoke failed");
  @(negedge clk);av=1;epoch_pulses=epoch_pulses+1;wait_ready;
  refh=-1;#1;if(d0.sources_ok || tail[0])$fatal(1,"negative height not rejected");
  @(negedge clk);refh=300;epoch_pulses=epoch_pulses+1;wait_ready;
  refh=5001;#1;if(d0.sources_ok || tail[0])$fatal(1,"excessive height not rejected");
  @(negedge clk);refh=300;epoch_pulses=epoch_pulses+1;wait_ready;
  // Legal height endpoints qualified combinationally, then restored before a clock.
  refh=0;#1;if(!d0.sources_ok)$fatal(1,"zero height rejected");
  refh=5000;#1;if(!d0.sources_ok)$fatal(1,"5000mm rejected");refh=300;
  external_age(4999999);external_age(5000000);external_age(5000001);external_age(32'hffffffff);
  // Reset during real arithmetic, followed by a fresh unforced seed/publication.
  while(!(d0.state==100 && mbusy[0]))@(negedge clk);
  rst_n=0;repeat(3)@(negedge clk);rst_n=1;wait_ready;
  repeat(110000)@(negedge clk);
  if(pubs<20 || seeds<8 || mcons<200 || dcons<200 || acccons<100 || numeric_pulses!=4 || commit_vetoes!=4 || epoch_pulses!=5)
   $fatal(1,"insufficient finite coverage pub=%0d seed=%0d mul=%0d div=%0d acc=%0d",pubs,seeds,mcons,dcons,acccons);
  if((!PRE && age_rejects!=3)||(PRE && age_bypasses!=4))$fatal(1,"age mode coverage missing");
  $display("PASS PRE=%0d cycles=%0d public_bits=152 request_bits=228 service_bits=135 publications=%0d seeds=%0d mul_consumed=%0d div_consumed=%0d acc_div_consumed=%0d numeric_pulses=%0d commit_vetoes=%0d epoch_pulses=%0d age_rejects=%0d age_bypasses=%0d ready_cycles=%0d",PRE,cycles,pubs,seeds,mcons,dcons,acccons,numeric_pulses,commit_vetoes,epoch_pulses,age_rejects,age_bypasses,ready_cycles);
  $finish;
 end
endmodule
'''.replace('@DECL@', declarations).replace('@INST@', instances)
(O / 'tb.v').write_text(tb)
temp = O / 'tmp'
temp.mkdir()
task_env = dict(os.environ, TMP=str(temp), TEMP=str(temp), TMPDIR=str(temp))
shared = [OLD / 'nav_math_service.v', OLD / 'position/position_math.v']
results = []
for pre in [0, 1]:
    exe = O / ('pre' + str(pre) + '.vvp')
    commands = [
        [str(IV), '-g2012', '-s', 'tb', '-Ptb.PRE=' + str(pre), '-o', str(exe),
         str(O / 'tb.v'), str(O / 'v5_height.v'), str(O / 'v6_height.v'), *map(str, shared)],
        [str(VVP), str(exe)],
    ]
    stages = []
    for stage, command in zip(['compile', 'simulation'], commands):
        start = time.time()
        log = O / ('pre' + str(pre) + '_' + stage + '.log')
        with log.open('wb') as f:
            try:
                completed = subprocess.run(command, stdout=f, stderr=subprocess.STDOUT,
                    stdin=subprocess.DEVNULL, timeout=240, creationflags=subprocess.CREATE_NO_WINDOW, env=task_env)
                code, timeout = completed.returncode, False
            except subprocess.TimeoutExpired:
                code, timeout = None, True
        rec = {'stage': stage, 'command': command, 'actual_returncode': code,
               'timed_out': timeout, 'elapsed_seconds': round(time.time()-start, 3),
               'log': log.name, 'log_sha256': sha(log)}
        stages.append(rec)
        (O / ('pre' + str(pre) + '_' + stage + '_exit.json')).write_text(json.dumps(rec, indent=2) + '\n')
        if code != 0 or timeout:
            raise RuntimeError('Real tool failed: ' + log.name)
    text = (O / ('pre' + str(pre) + '_simulation.log')).read_text()
    match = re.fullmatch(r'PASS ((?:\w+=\d+ ?)+)\s*', text)
    assert match, text
    counters = {k: int(v) for k, v in re.findall(r'(\w+)=(\d+)', match[1])}
    results.append({'PRE': pre, 'passed': True, 'stages': stages, 'coverage': counters,
                    'compiled_vvp_local_only': {'bytes': exe.stat().st_size, 'sha256': sha(exe)}})
after = {'v5': sources(OLD), 'v6': sources(NEW)}
assert before == after
receipt = {'passed': True, 'source55_before_after_identical': True,
           'source55_after': after, 'runs': results,
           'input_sha256': sha(O / 'inputs.json'), 'testbench_sha256': sha(O / 'tb.v'),
           'generated_source_hashes': {tag: sha(O / (tag + '_height.v')) for tag in ['v5', 'v6']},
           'scope_limit': 'Finite 2-state traces; no exhaustive state proof, wrapper simulation, natural 5,000,000-clock publication expiry, contention, flight/plant or hardware claim. RANGE_AGE_PRECHECKED=1 bypass is expected only at AGE_LIMIT=5,000,000.'}
(O / 'results.json').write_text(json.dumps(receipt, indent=2) + '\n')
print(json.dumps({'passed': True, 'results_sha256': sha(O / 'results.json'),
                  'coverage': [r['coverage'] for r in results]}, indent=2))
