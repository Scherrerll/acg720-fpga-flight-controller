
`timescale 1ns/1ps
module tb;
reg clk=0;always #10 clk=~clk;
reg rst_n=0,sample=0,hu=0,pu=0,en=0,to=0;
reg[15:0]c1=1500,c2=1500,c3=1000,c7=2000;
wire active,za,ready,zr,req,zreq,auto_to,ms,mc,ds,dc,mb,md,db,dd,de;
wire signed[63:0]ma,mba,dn,mr,dr;wire[31:0]den;wire[15:0]coll,reason,zreason;
wire signed[15:0]rt,pt,delta;wire signed[31:0]target,climb;
mtf_xyz_hold_control #(.CAL_MASK(8'hff),.VELOCITY_FRAC_BITS(16)) dut(
 .clk(clk),.rst_n(rst_n),.origin_reset(1'b0),.rc_valid(1'b1),.channel_count(4'd8),
 .ch1(c1),.ch2(c2),.ch3(c3),.ch4(16'd1500),.ch7(c7),.enabled(en),.taking_off(to),
 .position_valid(1'b1),.height_valid(1'b1),.position_update(pu),.height_update(hu),
 .sample_update(sample),.sample_dt_us(32'd1000),.position_age(32'd0),.position_dt_us(32'd20000),
 .x_q8(32'sd0),.y_q8(32'sd0),.vx(32'sd0),.vy(32'sd0),.height_mm(32'sd234),.vz(32'sd0),
 .yaw_cdeg(16'sd0),.acc_valid(1'b1),.ax_mmps2(32'sd0),.ay_mmps2(32'sd0),.az_mmps2(32'sd0),
 .collective_us(16'd1000),.requested(req),.ready(ready),.active(active),.height_requested(zreq),.height_ready(zr),.height_active(za),.auto_takeoff(auto_to),
 .reason(reason),.height_reason(zreason),.collective_target_us(coll),.roll_target(rt),.pitch_target(pt),.throttle_delta(delta),.requested_climb_mmps(climb),.target_height_mm(target),
 .math_mul_start(ms),.math_mul_cancel(mc),.math_mul_a(ma),.math_mul_b(mba),.math_mul_busy(mb),.math_mul_done(md),.math_mul_result(mr),
 .math_div_start(ds),.math_div_cancel(dc),.math_div_numerator(dn),.math_div_denominator(den),.math_div_busy(db),.math_div_done(dd),.math_div_error(de),.math_div_result(dr));
nav_math_service #(.DIVIDE(0),.CLIENTS(1)) mul(.clk(clk),.rst_n(rst_n),.request(ms),.cancel(mc),.operand_a(ma),.operand_b(mba),.busy(mb),.done(md),.error(),.result(mr),.grant());
nav_math_service #(.DIVIDE(1),.CLIENTS(1)) div(.clk(clk),.rst_n(rst_n),.request(ds),.cancel(dc),.operand_a(dn),.operand_b({32'd0,den}),.busy(db),.done(dd),.error(de),.result(dr),.grant());

integer phase=0,msidx=0;reg signed[26:0]saved_x,saved_y;reg signed[32:0]saved_ax,saved_ay;
always @(negedge clk)begin
 sample=0;hu=0;pu=0;
 if(rst_n)begin
  if(phase==1999)begin
   phase=0;msidx=msidx+1;sample=1;hu=(msidx%11==0);pu=(msidx%20==0);
  end else phase=phase+1;
 end
end
task ticks;input integer n;begin repeat(n)@(posedge clk);#1;end endtask
initial begin
 repeat(2)@(posedge clk);#1;rst_n=1;c3=2000;c1=1700;c2=1800;c7=2000;en=0;to=0;
 ticks(50000);if(active || za)$fatal(1,"selected mode cannot run while locked");
 en=1;to=1;wait(active && za);
 // A mode change is allowed while shared math is inside an uncommitted XY
 // callback. It must withdraw XY immediately, preserve Z, and roll back PI.
 wait(dut.work_xy && dut.state==7);#1;
 saved_x=dut.saved_ix;saved_y=dut.saved_iy;saved_ax=dut.saved_afx;saved_ay=dut.saved_afy;
 if(dut.ix_store==saved_x)$fatal(1,"race did not reach partial PI update");
 c7=1000;#1;if(active || !za)$fatal(1,"immediate XY revoke/Z continuity");
 ticks(20);
 if(dut.ix_store!=saved_x || dut.iy_store!=saved_y || dut.afx_store!=saved_ax || dut.afy_store!=saved_ay)$fatal(1,"partial callback not rolled back atomically");
 c7=2000;wait(active && za); // Full throttle, no center/reselect handshake.
 en=0;to=0;#1;if(active || za)$fatal(1,"lock revoke");
 ticks(20);en=1;to=1;wait(active && za);
 $display("CONTROL_RACE_PASS preselected/full-stick entry, immediate cancel, atomic PI rollback, vertical continuity, recovery");$finish;
end
initial begin #100000000;$fatal(1,"race timeout");end
endmodule
