"""Two new narrow actual-RTL witnesses; never writes frozen sources.

The stick test advances accepted semantic dt after each completed transaction.
The controller test accelerates arrivals (2000 clocks per semantic 1ms), with
original dt values. It proves dependency/response arithmetic, not aircraft
dynamics, real sensor validity or real-time scheduling at that accelerated rate.
"""
from pathlib import Path
import csv
import hashlib
import json
import math
import os
import subprocess

OUT=Path(__file__).resolve().parent
REPO=OUT.parents[2]
S=REPO/'firmware/B0B3/source'
BIN=Path('C:/Users/ScherrerL/Desktop/apple/.tools/iverilog/app/bin')

STICK=r'''`timescale 1ns/1ps
module tb;
reg clk=0,rst_n=0,enabled=1,update_in=0;
reg [15:0]ch1=1500,ch2=1500;wire signed[17:0]nx,ny;wire busy,fault,update_out,valid;wire[15:0]out_dt;
always #10 clk=~clk;
ano_xy_stick dut(.clk(clk),.rst_n(rst_n),.enabled(enabled),.sample_update(update_in),
 .sample_dt_us(32'd1000),.ch1(ch1),.ch2(ch2),.nx(nx),.ny(ny),.busy(busy),.fault(fault),.update(update_out),.valid(valid),.output_dt_us(out_dt));
integer f,n,tail,initial_norm,one_percent=0,point_one_percent=0;
task sample;begin
 @(negedge clk);update_in=1;@(negedge clk);update_in=0;
 while(!update_out)begin @(posedge clk);#2;if(fault)$fatal(1,"stick fault");end
 if(!valid || out_dt!=1000)$fatal(1,"stick publication invalid");
 $fdisplay(f,"%0d,%0d,%0d,%0d,%0d",n,ch1,ch2,nx,ny);
end endtask
initial begin
 f=$fopen("@TRACE@","w");$fdisplay(f,"semantic_ms,ch1,ch2,nx_q16,ny_q16");
 repeat(8)@(negedge clk);rst_n=1;ch1=2000;
 for(n=1;n<=400;n=n+1)sample;
 initial_norm=ny;if(ny<64800 || ny>64900)$fatal(1,"step did not settle");
 ch1=1500;
 for(n=401;n<=900;n=n+1)begin
  sample;tail=n-400;
  if(tail==1 && ny<=0)$fatal(1,"raw recenter incorrectly erases LPF");
  if(one_percent==0 && ny*100<=initial_norm)one_percent=tail;
  if(point_one_percent==0 && ny*1000<=initial_norm)point_one_percent=tail;
 end
 if(one_percent<240 || one_percent>255 || point_one_percent<360 || point_one_percent>380)$fatal(1,"unexpected LPF decay");
 $display("PASS actual stick: recenter tail 1pct=%0dms 0.1pct=%0dms residual500ms=%0dQ16",one_percent,point_one_percent,ny);
 ch1=1550;n=901;sample;if(dut.target_y!=0)$fatal(1,"1550 must be deadzone");
 ch1=1450;n=902;sample;if(dut.target_y!=0)$fatal(1,"1450 must be deadzone");
 ch1=1551;
 for(n=903;n<=1402;n=n+1)sample;
 if(dut.target_y!=144 || ny<143 || ny>145)$fatal(1,"small above-deadzone stick lost");
 $display("PASS actual stick: inclusive1450/1550 deadzone;1551 target144Q16 retained with LPF residue");
 $fclose(f);$finish;
end
initial begin #100000000;$fatal(1,"stick timeout");end
endmodule
'''

PORTS=r'''
 .clk(clk),.rst_n(rst_n),.origin_reset(1'b0),.rc_valid(1'b1),.channel_count(4'd8),
 .ch1(ch1),.ch2(16'd1500),.ch3(16'd1500),.ch4(16'd1500),.ch7(16'd2000),
 .xy_p_value(16'd500),.xy_i_value(16'd0),.parameter_boundary(),
 .enabled(1'b1),.taking_off(1'b1),.position_valid(1'b1),.height_valid(1'b1),
 .position_update(position_update),.height_update(height_update),.sample_update(sample_update),.sample_dt_us(32'd1000),
 .position_age(32'd0),.position_dt_us(32'd20000),.x_q8(x),.y_q8(y),.vx(32'sd0),.vy(vy),
 .height_mm(32'sd1000),.vz(32'sd0),.yaw_cdeg(16'sd0),.acc_valid(1'b1),
 .ax_mmps2(32'sd0),.ay_mmps2(32'sd0),.az_mmps2(32'sd0),.collective_us(16'd1500),
 .requested(),.ready(),.active(active),.height_requested(),.height_ready(),.height_active(),.auto_takeoff(),
 .reason(),.height_reason(),.collective_target_us(),.roll_target(roll),.pitch_target(pitch),.throttle_delta(),
 .requested_climb_mmps(),.target_height_mm(),.pilot_norm_x(),.pilot_norm_y(),.pilot_norm_update(),.pilot_norm_valid(),.pilot_norm_dt_us(),
 .math_mul_start(mreq),.math_mul_cancel(mcancel),.math_mul_a(ma),.math_mul_b(mb),.math_mul_busy(mbusy),.math_mul_done(mdone),.math_mul_result(mresult),
 .math_div_start(dreq),.math_div_cancel(dcancel),.math_div_numerator(da),.math_div_denominator(db),.math_div_busy(dbusy),.math_div_done(ddone),.math_div_error(derror),.math_div_result(dresult)
'''

HARNESS=r'''
module harness #(parameter KP=65536)(input wire clk,rst_n,sample_update,position_update,height_update,
 input wire[15:0]ch1,input wire signed[31:0]x,y,vy,
 output wire signed[15:0]roll,pitch,output wire pub,active,blocked);
wire mreq,mcancel,mbusy,mdone,merror,dreq,dcancel,dbusy,ddone,derror;
wire signed[63:0]ma,mb,mresult,da,dresult;wire[31:0]db;
mtf_xyz_hold_control #(.CAL_MASK(8'hff),.VELOCITY_FRAC_BITS(16),.POSITION_KP_Q16(KP))dut(@PORTS@);
nav_math_service #(.CLIENTS(1),.DIVIDE(0))mul(.clk(clk),.rst_n(rst_n),.request(mreq),.cancel(mcancel),
 .operand_a(ma),.operand_b(mb),.busy(mbusy),.done(mdone),.error(merror),.result(mresult),.grant());
nav_math_service #(.CLIENTS(1),.DIVIDE(1))div(.clk(clk),.rst_n(rst_n),.request(dreq),.cancel(dcancel),
 .operand_a(da),.operand_b({32'd0,db}),.busy(dbusy),.done(ddone),.error(derror),.result(dresult),.grant());
assign pub=dut.command_seen && dut.command_age==0;assign blocked=dut.blocked||dut.xy_blocked;
endmodule
'''

CONTROL=r'''`timescale 1ns/1ps
module tb;
reg clk=0,rst_n=0,sample_update=0,position_update=0,height_update=0;
reg[15:0]ch1=2000;reg signed[31:0]vy=500*65536,x=0,y=0;
wire signed[15:0]ar,ap,br,bp;wire pa,pb,aa,ab,ba,bb;
harness a(clk,rst_n,sample_update,position_update,height_update,ch1,32'sd0,32'sd0,vy,ar,ap,pa,aa,ba);
harness #(.KP(32768))b(clk,rst_n,sample_update,position_update,height_update,ch1,x,y,vy,br,bp,pb,ab,bb);
always #10 clk=~clk;
integer cycles=0,samples=0,phase=0,f,pubs=0,position_changes=0;
reg signed[63:0]last_p=0,last_ff=0;
always @(negedge clk)begin
 sample_update<=0;position_update<=0;height_update<=0;
 if(rst_n)begin
  cycles=cycles+1;
  if(cycles%2000==0)begin
   samples=samples+1;sample_update<=1;
   if(samples%11==0)height_update<=1;
   if(samples%20==0)begin position_update<=1;x<=-x+32'sd123457;y<=-y-32'sd765432;position_changes=position_changes+1;end
  end
 end
end
always @(posedge clk)begin
 if(rst_n && a.dut.work_xy && a.dut.state==9)last_p=a.dut.value;
 if(rst_n && a.dut.work_xy && a.dut.state==11)last_ff=a.dut.value;
 #2;
 if(rst_n)begin
  if(ba || bb)$fatal(1,"controller blocked");
  if({ar,ap,pa,aa}!=={br,bp,pb,ab})$fatal(1,"position/KP changed control behavior");
  if(pa)begin
   pubs=pubs+1;
   if(a.dut.iy!=0)$fatal(1,"default I not zero");
   $fdisplay(f,"%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d",samples,phase,ch1,vy,x,y,a.dut.pending_ny,a.dut.sy,last_p,a.dut.iy,last_ff,ar,ap);
  end
 end
end
initial begin
 f=$fopen("@TRACE@","w");$fdisplay(f,"semantic_ms,phase,ch1,vy_q16,alternate_x_q8,alternate_y_q8,captured_norm_y_q16,desired_y_mmps_q16,actual_P_y_cdeg_q16,actual_I_y_cdeg_q16,actual_FF_y_cdeg_q16,roll_target_cdeg,pitch_target_cdeg");
 repeat(8)@(negedge clk);rst_n=1;
 wait(samples>=400);@(negedge clk);phase=1;ch1=1500;
 wait(samples>=900);@(negedge clk);
 if(ar< -251 || ar> -249 || ap!=0)$fatal(1,"centered moving feedback must brake roll=%0d",ar);
 $display("PASS actual controller: centered after500ms, rightward500mmps commands opposing roll=%0dcdeg withI0",ar);
 phase=2;vy=0;
 wait(samples>=1000);@(negedge clk);
 if(ar!=0 || ap!=0)$fatal(1,"stationary command should be zero despite position displacement %0d,%0d",ar,ap);
 if(pubs<40 || position_changes<45)$fatal(1,"insufficient actual callbacks");
 $display("PASS actual controller: changed x/y and POSITION_KP never affect roll/pitch/activity; %0d callback publications,%0d position changes",pubs,position_changes);
 $display("PASS actual controller: zero velocity after recenter yields zero command despite nonzero position offset; no position restoration");
 $fclose(f);$finish;
end
initial begin #100000000;$fatal(1,"controller timeout");end
endmodule
'''

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
    tmp=OUT/'rtl_tmp';tmp.mkdir(exist_ok=True)
    sources=[S/'position/mtf_xyz_hold_control.v',S/'nav_math_service.v',S/'position/position_math.v',
             S/'position/ano_xy_stick.v',S/'position/ano_xy_divide36.v',S/'position/ano_z_stick.v']
    before={str(p):sha(p)for p in sources}
    results=[]
    for name,body,files in (
       ('stick_tail',STICK,[S/'position/ano_xy_stick.v',S/'position/ano_xy_divide36.v']),
       ('controller_position',CONTROL+HARNESS.replace('@PORTS@',PORTS),sources)):
        trace=(OUT/(name+'_trace.csv')).as_posix()
        bench=OUT/(name+'_tb.v');bench.write_text(body.replace('@TRACE@',trace),encoding='utf8')
        output=tmp/(name+'.vvp')
        env=dict(os.environ,TMP=str(tmp),TEMP=str(tmp),TMPDIR=str(tmp))
        compile_args=[str(BIN/'iverilog.exe'),'-g2012','-s','tb','-o',str(output),str(bench),*map(str,files)]
        compiled=subprocess.run(compile_args,cwd=OUT,capture_output=True,text=True,env=env)
        (OUT/(name+'_compile.log')).write_text(compiled.stdout+compiled.stderr,encoding='utf8')
        if compiled.returncode:raise RuntimeError(compiled.stderr)
        with (OUT/(name+'.log')).open('w',encoding='utf8')as log:
            p=subprocess.Popen([str(BIN/'vvp.exe'),str(output)],cwd=OUT,stdout=log,stderr=subprocess.STDOUT,env=env,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
            code=p.wait(timeout=180)
        text=(OUT/(name+'.log')).read_text(encoding='utf8')
        if code:raise RuntimeError(text)
        results.append(dict(name=name,compile_exit=compiled.returncode,actual_wait_return=code,pid=p.pid,
            bench_sha256=sha(bench),trace_sha256=sha(OUT/(name+'_trace.csv')),checks=[line for line in text.splitlines()if line.startswith('PASS')]))
    # Independent float equation check; this executes Python, not P2 C.
    f=0.0;max_error=0.0
    for row in csv.DictReader((OUT/'stick_tail_trace.csv').open(encoding='utf8')):
        value=int(row['ch1'])-1500;dead=value-50 if value>50 else value+50 if value< -50 else 0
        target=dead*.0022;alpha=.01884/1.01884
        f+=(target-f)*alpha
        max_error=max(max_error,abs(int(row['ny_q16'])/65536-f))
    if max_error>3/65536:raise AssertionError(('LPF float model divergence',max_error))
    after={str(p):sha(p)for p in sources}
    assert before==after
    result=dict(passed=True,scope=__doc__,actual_RTL_results=results,
        python_float_equation_comparison=dict(execution='Python model of source LPF equation; P2 C not compiled or executed',max_abs_norm_error=max_error,max_error_q16_lsb=max_error*65536),
        immutable_source_sha256=before,immutable_sources_unchanged=True)
    (OUT/'rtl_witness_results.json').write_text(json.dumps(result,indent=2),encoding='utf8')
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
