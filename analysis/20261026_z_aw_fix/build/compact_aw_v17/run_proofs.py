"""Actual v17 old/new flight FSM miter, full-value threshold proof and original top13."""
from pathlib import Path
import datetime, hashlib, json, os, subprocess, sys
O=Path(__file__).resolve().parent;R=O.parents[3];D=O/'proofs';P=O.parent/'v4_release_proofs'
C=R/'out/z_aw_fix_20261026/compact_aw_v17/canonical/source';OLD=R/'out/z_aw_fix_20261026/compact_aw_v4/canonical/source'
B=Path('C:/Users/ScherrerL/Desktop/apple/.tools/iverilog/app/bin')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf8'))
utc=lambda:datetime.datetime.now(datetime.timezone.utc).isoformat()
freeze=read(O/'source_freeze.json');expected=freeze['source55'];before=freeze['baseline_source55']
assert not (D/'inputs.json').exists() and not (O/'PROOF_BINDING.json').exists()
assert len(expected)==55 and all(sha(C/n)==h for n,h in expected.items()) and all(sha(OLD/n)==h for n,h in before.items())
assert sha(O/'source_review.md')==freeze['source_review_sha256'] and sha(O/'SOURCE_EQUIVALENCE_BASIS.json')==freeze['source_equivalence_basis_sha256']
basis=read(O/'SOURCE_EQUIVALENCE_BASIS.json')
for n,t in basis['transformations'].items():
    s=(C/n).read_text(encoding='utf8')
    for a,b in reversed(t['edits']):assert s.count(b)==1;s=s.replace(b,a)
    assert s==(OLD/n).read_text(encoding='utf8')
parent=read(P/'RESULT.json');assert parent['passed'] and parent['source55']==before and read(P/'runner_exit.json')['actual_p_wait']==0
orig=(OLD/'core/ano_flight_state.v').read_text(encoding='utf8')
assert orig.count('module ano_flight_state ')==1
(D/'legacy_ano_flight_state.v').write_text(orig.replace('module ano_flight_state ','module legacy_ano_flight_state '),encoding='utf8')
core=(C/'core/flight_core.v').read_text(encoding='utf8')
start=core.index('    (* syn_keep = 1 *) wire fallback_collective_below_landing=')
end=core.index('\n',core.index('wire selected_collective_below_landing=',start))
glue=core[start:end]
assert '.collective_below_landing(selected_collective_below_landing)' in core and '.PRECHECKED_COLLECTIVE(1)' in core
tb='''`timescale 1ns/1ps
module pair #(parameter T=1)(input clk,rst_n,armed,input[15:0] ch3,hold_collective_us,fallback_unmasked_collective,input height_fallback_active,
 output reg saw_prepared,saw_takeoff,saw_flying,saw_land);
initial begin saw_prepared=0;saw_takeoff=0;saw_flying=0;saw_land=0;end
wire[15:0] fallback_collective=height_fallback_active ?fallback_unmasked_collective:16'd1000;
wire[15:0] selected_throttle=height_fallback_active ?fallback_collective:hold_collective_us;
'''+glue+'''
legacy_ano_flight_state #(.TICKS_PER_MS(T)) old(.clk(clk),.rst_n(rst_n),.armed(armed),.ch3(ch3),.collective_us(selected_throttle));
ano_flight_state #(.TICKS_PER_MS(T)) def(.clk(clk),.rst_n(rst_n),.armed(armed),.ch3(ch3),.collective_us(selected_throttle),.collective_below_landing(1'b0));
ano_flight_state #(.TICKS_PER_MS(T),.PRECHECKED_COLLECTIVE(1)) dut(.clk(clk),.rst_n(rst_n),.armed(armed),.ch3(ch3),.collective_us(selected_throttle),.collective_below_landing(selected_collective_below_landing));
wire[80:0] ov={old.phase,old.half,old.preparation_ms,old.flying_ms,old.landing_ms,old.landing_delay,old.normal_unlock,old.motor_prepared,old.taking_off,old.flying,old.land_lock,old.preparation_mask};
wire[80:0] dv={dut.phase,dut.half,dut.preparation_ms,dut.flying_ms,dut.landing_ms,dut.landing_delay,dut.normal_unlock,dut.motor_prepared,dut.taking_off,dut.flying,dut.land_lock,dut.preparation_mask};
wire[80:0] fv={def.phase,def.half,def.preparation_ms,def.flying_ms,def.landing_ms,def.landing_delay,def.normal_unlock,def.motor_prepared,def.taking_off,def.flying,def.land_lock,def.preparation_mask};
always @(posedge clk)begin
 #1;
 if(ov!==dv || ov!==fv)$fatal(1,"FSM mismatch T=%0d old=%h new=%h default=%h",T,ov,dv,fv);
 if(selected_collective_below_landing!==(selected_throttle<1250))$fatal(1,"threshold distributivity mismatch T=%0d",T);
 if(old.motor_prepared)saw_prepared<=1;if(old.taking_off)saw_takeoff<=1;if(old.flying)saw_flying<=1;if(old.land_lock)saw_land<=1;
end
endmodule
module tb;
reg clk=0;always #10 clk=~clk;
reg rst_n=0,armed=0,active=0;
reg[15:0] ch3=1000,auto_value=1000,unmasked=1000;
wire[3:0] p1,p3,p7;
pair #(.T(1)) a(clk,rst_n,armed,ch3,auto_value,unmasked,active,p1[3],p1[2],p1[1],p1[0]);
pair #(.T(3)) b(clk,rst_n,armed,ch3,auto_value,unmasked,active,p3[3],p3[2],p3[1],p3[0]);
pair #(.T(7)) c(clk,rst_n,armed,ch3,auto_value,unmasked,active,p7[3],p7[2],p7[1],p7[0]);
reg healthy=0,height=1,automatic_valid=0;
wire actual_active;wire[15:0] actual_public,actual_unmasked;
height_loss_fallback #(.SLEW_TICKS(3)) fall(.clk(clk),.rst_n(rst_n),.healthy(healthy),.armed(armed),.taking_off(a.old.taking_off),.height_available(height),.automatic_valid(automatic_valid),.automatic_collective_us(auto_value),.ch3(ch3),.active(actual_active),.collective_us(actual_public),.unmasked_collective_us(actual_unmasked));
integer cycles=0,k,j;reg saw_actual_fallback=0;
reg[31:0] rng=32'h6d15a3c7;
function[15:0] boundary;input integer i;begin case(i)
0:boundary=0;1:boundary=1000;2:boundary=1249;3:boundary=1250;4:boundary=1251;5:boundary=1850;6:boundary=2000;default:boundary=65535;
endcase end endfunction
always @(posedge clk)begin
 #2;cycles=cycles+1;
 if(actual_active)begin saw_actual_fallback=1;if(actual_public!==actual_unmasked)$fatal(1,"active public/unmasked implication failed");end
 if(((actual_active ?actual_public:auto_value)<1250)!==(actual_active ?(actual_unmasked<1250):(auto_value<1250)))$fatal(1,"actual fallback comparison failed");
end
task run;input integer n;integer i;begin for(i=0;i<n;i=i+1)@(negedge clk);end endtask
initial begin
 run(4);rst_n=1;armed=1;healthy=1;automatic_valid=1;ch3=1800;auto_value=1400;unmasked=1400;
 run(21000);height=0;active=1;run(400);ch3=1000;auto_value=1249;unmasked=1249;
 run(8000);unmasked=1250;run(70);unmasked=1249;run(14000);
 if(p1!==15 || p3!==15 || p7!==15 || !saw_actual_fallback)$fatal(1,"directed flight/preparation/landing/fallback coverage missing %b %b %b %b",p1,p3,p7,saw_actual_fallback);
 armed=0;run(17);rst_n=0;run(3);rst_n=1;
 // Every16bit value in both numeric branches, against eight independent opposite-branch boundaries and both selections.
 for(k=0;k<65536;k=k+1)begin
  for(j=0;j<8;j=j+1)begin
   auto_value=k;unmasked=boundary(j);active=0;run(1);active=1;run(1);
   auto_value=boundary(j);unmasked=k;active=0;run(1);active=1;run(1);
  end
 end
 // General state/input transitions, resets and revocation, reproducible LFSR stream.
 for(k=0;k<100000;k=k+1)begin
  rng={rng[30:0],rng[31]^rng[21]^rng[1]^rng[0]};
  rst_n=(k%997)!=0;armed=rng[0];active=rng[1];healthy=rng[2];height=rng[3];automatic_valid=rng[4];
  ch3=rng[31:16];auto_value=rng[15:0];unmasked=rng[31:16];run(1);
 end
 $display("PASS v17 completeFSM old/new/default T=1/3/7, all state bits, directed preparation/takeoff/flying/landing/revoke, actual fallback implication, 2097152 threshold vectors,100000 random transitions cycles=%0d",cycles);$finish;
end
initial begin #60000000;$fatal(1,"miter timeout cycles=%0d",cycles);end
endmodule
'''
(D/'flight_state_miter.v').write_text(tb,encoding='utf8')
bound={str(p):sha(p) for p in [Path(__file__),O/'source_freeze.json',O/'source_review.md',O/'SOURCE_EQUIVALENCE_BASIS.json',D/'flight_state_miter.v',D/'legacy_ano_flight_state.v',D/'run_top13.py',P/'RESULT.json',P/'runner_exit.json',P/'top_safety_tb.v',B/'iverilog.exe',B/'vvp.exe']}
(D/'inputs.json').write_text(json.dumps(dict(source55=expected,parent_source55=before,bound_files=bound,scope='New actual FSM miter/default-interface/full-value threshold proof and exact original top13; no new five-case or ground run'),indent=2)+'\n',encoding='utf8')
env=dict(os.environ);tmp=D/'fsm_tmp';tmp.mkdir();env.update(TMP=str(tmp),TEMP=str(tmp),TMPDIR=str(tmp))
def run(name,command,timeout=120):
    assert not (D/(name+'_exit.json')).exists()
    record=dict(command=command,cwd=str(R),started_utc=utc(),parent_pid=os.getpid())
    with (D/(name+'.stdout.log')).open('wb') as out,(D/(name+'.stderr.log')).open('wb') as err:
        p=subprocess.Popen(command,cwd=R,env=env,stdin=subprocess.DEVNULL,stdout=out,stderr=err,creationflags=subprocess.CREATE_NO_WINDOW)
        record['pid']=p.pid
        try:code=p.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            p.terminate();code=p.wait();record['terminated_after_timeout']=True
        record.update(actual_p_wait=code,normal_wait_return=True,ended_utc=utc(),stdout_sha256=sha(D/(name+'.stdout.log')),stderr_sha256=sha(D/(name+'.stderr.log')))
    (D/(name+'_exit.json')).write_text(json.dumps(record,indent=2)+'\n',encoding='utf8')
    assert code==0 and not record.get('terminated_after_timeout'),(name,code)
    return record
run('fsm_compile',[str(B/'iverilog.exe'),'-g2012','-s','tb','-o',str(D/'flight_state_miter.vvp'),str(D/'flight_state_miter.v'),str(D/'legacy_ano_flight_state.v'),str(C/'core/ano_flight_state.v'),str(C/'core/height_loss_fallback.v')])
run('fsm_vvp',[str(B/'vvp.exe'),str(D/'flight_state_miter.vvp')])
assert 'PASS v17 completeFSM' in (D/'fsm_vvp.stdout.log').read_text(encoding='utf8')
top=run('runner',[sys.executable,'-B','-X','utf8',str(D/'run_top13.py')])
assert read(D/'top_safety_results.json')['cases']==13 and read(D/'top_safety_results.json')['passed']
assert sha(D/'top_safety_tb.v')==sha(P/'top_safety_tb.v')
assert all(read(D/(n+'_exit.json'))['actual_completedprocess_returncode']==0 and read(D/(n+'_exit.json'))['normal_return'] for n in ['compile','vvp'])
assert all(sha(Path(p))==h for p,h in bound.items()) and all(sha(C/n)==h for n,h in expected.items())
out=dict(passed=True,source55=expected,actual_proof_runner_wait=top['actual_p_wait'],parent_proof_sha256=sha(P/'RESULT.json'),inputs_sha256=sha(D/'inputs.json'),actual_top13_runner_exit_sha256=sha(D/'runner_exit.json'),top13_result_sha256=sha(D/'top_safety_results.json'),top13=dict(passed=True,cases=13,actual_root_wait=0,compile_and_vvp_actual_waits=[0,0]),flight_state_miter=dict(passed=True,all_internal_and_public_state_bits=True,TICKS_PER_MS=[1,3,7],threshold_vectors=2097152,random_transitions=100000,no_DUT_force_or_preload=True,compile_actual_wait=0,vvp_actual_wait=0),line_endings_normalized_without_token_change=basis['line_endings_normalized'],scope='New comparator/FSM old-new-default cycle proof, real fallback implication and original top13. Exact unchanged six controller inputs and ground43 separately rehashed; no physical or installation claim.')
(O/'PROOF_BINDING.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf8')
print(json.dumps(dict(passed=True,new_top13=13,FSM_miter=True,threshold_vectors=2097152,actual_top_runner_wait=0)))
