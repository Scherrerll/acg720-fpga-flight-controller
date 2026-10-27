"""Compare v5/v7 control ports and consumed math around numeric cancellation."""
from pathlib import Path
import argparse, hashlib, json, os, subprocess

O = Path(__file__).resolve().parent
R = Path('C:\\Users\\ScherrerL\\Desktop\\apple\\github_publish\\acg720-fpga-flight-controller')
B = Path(r'C:/Users/ScherrerL/Desktop/apple/.tools/iverilog/app/bin')
OLD_SRC = R / 'out/z_aw_fix_20261026/compact_aw_v20/canonical/source'
NEW_SRC = R / 'out/z_aw_fix_20261026/compact_aw_v22/canonical/source'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--expected-hold-sha256', required=True)
    args = p.parse_args()
    assert sha(OLD_SRC/'position/mtf_xyz_hold_control.v') == 'ffddb029cb34a8d2ac8995cc43d85866e273d3d147bb650cfd5d3c66c580b642'
    assert sha(NEW_SRC/'position/mtf_xyz_hold_control.v') == args.expected_hold_sha256
    inputs = {str(root): {f.relative_to(root).as_posix(): sha(f) for f in root.rglob('*') if f.is_file()}
              for root in (OLD_SRC, NEW_SRC)}
    assert all(len(x) == 55 for x in inputs.values())
    (O/'inputs.json').write_text(json.dumps(inputs, indent=2)+'\n')
    old = (OLD_SRC/'position/mtf_xyz_hold_control.v').read_text().replace('module mtf_xyz_hold_control #(', 'module mtf_xyz_hold_control_v5 #(')
    (O/'v5_reference.v').write_text(old)
    ports = '''.clk(clk),.rst_n(rst_n),.origin_reset(1'b0),.rc_valid(1'b1),.channel_count(4'd8),
 .ch1(ch1),.ch2(ch2),.ch3(ch3),.ch4(16'd1500),.ch7(16'd2000),.xy_p_value(pval),.xy_i_value(ival),
 .parameter_boundary(pb),.enabled(1'b1),.taking_off(1'b1),.position_valid(1'b1),.height_valid(1'b1),
 .position_update(pu),.height_update(hu),.sample_update(su),.sample_dt_us(32'd11000),
 .position_age(32'd0),.position_dt_us(32'd100000),.x_q8(32'sd0),.y_q8(32'sd0),
 .vx(vx),.vy(vy),.height_mm(h),.vz(vz),.yaw_cdeg(yaw),.acc_valid(1'b1),
 .ax_mmps2(ax),.ay_mmps2(ay),.az_mmps2(az),.collective_us(16'd1500),
 .requested(req),.ready(ready),.active(active),.height_requested(hr),.height_ready(hready),
 .height_active(ha),.auto_takeoff(auto_to),.reason(reason),.height_reason(hreason),
 .collective_target_us(collective),.roll_target(roll),.pitch_target(pitch),.throttle_delta(delta),
 .requested_climb_mmps(climb),.target_height_mm(target),.pilot_norm_x(nx),.pilot_norm_y(ny),
 .pilot_norm_update(nu),.pilot_norm_valid(nv),.pilot_norm_dt_us(ndt),
 .math_mul_start(mreq),.math_mul_cancel(mc),.math_mul_a(ma),.math_mul_b(mb),
 .math_mul_busy(mbusy),.math_mul_done(mdone),.math_mul_result(mresult),
 .math_div_start(dreq),.math_div_cancel(dc),.math_div_numerator(da),.math_div_denominator(db),
 .math_div_busy(dbusy),.math_div_done(ddone),.math_div_error(derror),.math_div_result(dresult)'''
    def wrapper(name, module):
        return f'''module {name} #(parameter F=0)(input clk,rst_n,su,hu,pu,
input [15:0] ch1,ch2,ch3,pval,ival,input signed[31:0] h,vx,vy,vz,ax,ay,az,input signed[15:0] yaw,
output wire[221:0] observed);
wire req,ready,active,hr,hready,ha,auto_to,nu,nv,pb;
wire[15:0] reason,hreason,collective,ndt;wire signed[15:0] roll,pitch,delta;
wire signed[31:0] climb,target;wire signed[17:0]nx,ny;
wire mreq,mc,mbusy,mdone,me,dreq,dc,dbusy,ddone,derror;
wire signed[63:0]ma,mb,mresult,da,dresult;wire[31:0]db;wire mg;
assign observed={{pb,req,ready,active,hr,hready,ha,auto_to,reason,hreason,collective,roll,pitch,delta,climb,target,nx,ny,nu,nv,ndt}};
{module} #(.CAL_MASK(8'hff),.VELOCITY_FRAC_BITS(F),.POSITION_KP_Q16(98304)) dut({ports});
nav_math_service #(.CLIENTS(1),.DIVIDE(0)) mul(.clk(clk),.rst_n(rst_n),.request(mreq),.cancel(mc),
 .operand_a(ma),.operand_b(mb),.busy(mbusy),.done(mdone),.error(me),.result(mresult),.grant(mg));
nav_math_service #(.CLIENTS(1),.DIVIDE(1)) div(.clk(clk),.rst_n(rst_n),.request(dreq),.cancel(dc),
 .operand_a(da),.operand_b({{32'd0,db}}),.busy(dbusy),.done(ddone),.error(derror),.result(dresult),.grant());
endmodule\n'''
    (O/'sides.v').write_text(wrapper('old_side', 'mtf_xyz_hold_control_v5')+wrapper('new_side', 'mtf_xyz_hold_control'))
    tb = r'''`timescale 1ns/1ps
module tb;
parameter F=0;
reg clk=0,rst_n=0,su=0,hu=0,pu=0;
reg[15:0]ch1=1500,ch2=1500,ch3=1600,pval=1000,ival=350;
reg signed[31:0]h=1000,vx=0,vy=0,vz=0,ax=0,ay=0,az=0;
reg signed[15:0]yaw=0;wire[221:0]a,b;
old_side #(.F(F)) old(clk,rst_n,su,hu,pu,ch1,ch2,ch3,pval,ival,h,vx,vy,vz,ax,ay,az,yaw,a);
new_side #(.F(F)) newx(clk,rst_n,su,hu,pu,ch1,ch2,ch3,pval,ival,h,vx,vy,vz,ax,ay,az,yaw,b);
always #10 clk=~clk;
integer cycles=0,grants=0,pubs=0,differences=0,invalid_checks=0,j,k;
reg forbid=0;reg[31:0]pub_before;
task clocks;input integer n;begin repeat(n)@(negedge clk);end endtask
task callback;input integer both;begin
 @(negedge clk);su=1;hu=1;pu=both;
 @(negedge clk);su=0;hu=0;pu=0;clocks(24000);
end endtask
always @(posedge clk)begin
 #2;
 if(rst_n)begin
  cycles=cycles+1;
  if(a!==b)$fatal(1,"control/safety/normalization ports differ cycle=%0d state=%0d/%0d",cycles,old.dut.state,newx.dut.state);
  if({old.mreq,old.mc,old.dreq,old.dc,old.mbusy,old.mdone,old.dbusy,old.ddone,old.derror}!==
     {newx.mreq,newx.mc,newx.dreq,newx.dc,newx.mbusy,newx.mdone,newx.dbusy,newx.ddone,newx.derror})
   $fatal(1,"math request/cancel/status differs");
  if(old.dut.state!==newx.dut.state || old.dut.iz!==newx.dut.iz || old.dut.bias!==newx.dut.bias ||
     old.dut.ix!==newx.dut.ix || old.dut.iy!==newx.dut.iy)$fatal(1,"persistent state differs");
  if(old.mg)begin
   grants=grants+1;
   if(forbid)$fatal(1,"invalid captured request was granted");
   if(old.mul.held_a!==newx.mul.held_a || old.mul.held_b!==newx.mul.held_b)$fatal(1,"consumed operands differ");
   if(old.mul.held_a!=$signed(old.mul.held_a[33:0]) || old.mul.held_b!=$signed(old.mul.held_b[27:0]))
    $fatal(1,"consumed operand outside retained width");
  end
  if(old.mdone && !old.mc && old.mresult!==newx.mresult)$fatal(1,"accepted multiply differs");
  if(old.ddone && !old.dc && old.dresult!==newx.dresult)$fatal(1,"accepted divide differs");
  if(old.dut.height_command_seen && old.dut.height_command_age==0)begin
   pubs=pubs+1;if(forbid)$fatal(1,"cancelled numeric transaction published");
  end
  if(old.dut.iz!=$signed(old.dut.iz[26:0]) || old.dut.bias!=$signed(old.dut.bias[25:0]))$fatal(1,"I/bias exceeds27/26");
  if(old.dut.state==66 || old.dut.state==67)begin
   if(old.dut.candidate_iz!==newx.dut.candidate_iz || old.dut.p_bias!==newx.dut.p_bias)$fatal(1,"valid candidate/Pbias differs");
   if(old.dut.candidate_iz!=$signed(old.dut.candidate_iz[26:0]) || old.dut.p_bias!=$signed(old.dut.p_bias[28:0]))$fatal(1,"valid candidate/Pbias exceeds27/29");
  end
  if(old.dut.state==67)begin
   if(old.dut.candidate_collective!==newx.dut.candidate_collective || old.dut.current_collective!==newx.dut.current_collective)$fatal(1,"valid collective differs");
   if(old.dut.candidate_collective!=$signed(old.dut.candidate_collective[29:0]) || old.dut.current_collective!=$signed(old.dut.current_collective[29:0]))$fatal(1,"valid collective exceeds30");
  end
  if(old.ma!==newx.ma || old.mb!==newx.mb)differences=differences+1;
  if(old.dut.num!==newx.dut.num || old.dut.value!==newx.dut.value)$fatal(1,"num/value aliases differ");
  if(old.dut.num!=$signed(old.dut.num[49:0]) || old.dut.value!=$signed(old.dut.value[38:0]))
   $fatal(1,"num/value exceeds retained50/39 width");
 end
end
initial begin
 clocks(8);rst_n=1;clocks(30);callback(0);callback(1);
 for(j=0;j<4;j=j+1)begin
  // One invalid pulse is captured while readiness is still from the old sample.
  // Its calc reaches state0 on the same edge registered cancel becomes high.
  clocks(20);if(old.dut.state!=0)$fatal(1,"not idle before invalid fixture");
  pub_before=pubs;forbid=1;
  @(negedge clk);hu=1;az=j==0?32'sh7fffffff:j==1?32'sh80000000:j==2?32'sd30001:-32'sd30001;
  @(negedge clk);hu=0;az=0;
  clocks(15);
  if(pubs!=pub_before || old.dut.tracking || old.dut.height_command_seen)$fatal(1,"invalid pulse not revoked");
  invalid_checks=invalid_checks+1;forbid=0;
  callback(0);callback(1);
 end
 for(k=0;k<24;k=k+1)begin
  h=k%2?5000:0;vx=k%2?(10000<<<F):(-10000<<<F);vy=-vx;vz=vy;
  ax=k%2?30000:-30000;ay=-ax;az=ax;yaw=k%2?18000:-18000;
  ch1=k%2?2000:1000;ch2=3000-ch1;ch3=k%2?1684:1002;
  pval=k%3==0?16'd65535:k%3==1?16'd10000:16'd1000;ival=pval;
  clocks(12);callback(1);
 end
 if(differences!=0 || grants<100 || pubs<15 || invalid_checks!=4)$fatal(1,"fixture coverage incomplete %0d/%0d/%0d/%0d",differences,grants,pubs,invalid_checks);
 $display("PASS fraction=%0d control_cycles=%0d legal_grants=%0d Z_publications=%0d invalid_captures=%0d operand_difference_cycles_must_be_zero=%0d",F,cycles,grants,pubs,invalid_checks,differences);
 $finish;
end
initial begin #100000000;$fatal(1,"timeout");end
endmodule
'''
    (O/'boundary_tb.v').write_text(tb)
    tmp=O/'tmp';tmp.mkdir(exist_ok=True)
    env=dict(os.environ,TMP=str(tmp),TEMP=str(tmp),TMPDIR=str(tmp))
    helpers=['nav_math_service.v','position/position_math.v','position/ano_xy_stick.v','position/ano_xy_divide36.v','position/ano_z_stick.v']
    results=[]
    for frac in (0,16):
        d=O/f'fraction_{frac}';d.mkdir(exist_ok=True)
        cmd=[str(B/'iverilog.exe'),'-g2012','-s','tb',f'-Ptb.F={frac}','-o',str(d/'boundary.vvp'),str(O/'boundary_tb.v'),str(O/'sides.v'),str(O/'v5_reference.v'),str(NEW_SRC/'position/mtf_xyz_hold_control.v'),*[str(NEW_SRC/f) for f in helpers]]
        c=subprocess.run(cmd,env=env,capture_output=True,text=True)
        (d/'compile.log').write_text(c.stdout+c.stderr);assert c.returncode==0,c.stdout+c.stderr
        with (d/'simulation.log').open('w') as log:
            c=subprocess.run([str(B/'vvp.exe'),str(d/'boundary.vvp')],env=env,stdout=log,stderr=subprocess.STDOUT,timeout=300)
        text=(d/'simulation.log').read_text();print(text,flush=True)
        results.append(dict(fraction=frac,exit_code=c.returncode,pass_lines=[x for x in text.splitlines() if x.startswith('PASS')],log_sha256=sha(d/'simulation.log')))
        (O/'results.json').write_text(json.dumps(dict(passed=all(x['exit_code']==0 and x['pass_lines'] for x in results),completed=len(results),results=results,scope='Actual RTL with single-client services. All control/safety/normalization ports every cycle; math requests/cancel/status every cycle and consumed operands/results. All num/value aliases exact every cycle and representable in50/39 bits; all operand differences must be zero. Same MA/MB widths in both sides. Legal boundaries and four single-cycle bad-az captures per fraction. No private force.'),indent=2)+'\n')
        assert c.returncode==0 and results[-1]['pass_lines'],text
    assert inputs == {str(root): {f.relative_to(root).as_posix(): sha(f) for f in root.rglob('*') if f.is_file()} for root in (OLD_SRC,NEW_SRC)}
    (O/'source_stability.json').write_text(json.dumps({'source55_unchanged':True,'inputs_sha256':sha(O/'inputs.json'),'driver_sha256':sha(Path(__file__))},indent=2)+'\n')

if __name__=='__main__':
    main()
