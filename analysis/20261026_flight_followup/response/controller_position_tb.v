`timescale 1ns/1ps
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
 f=$fopen("C:/Users/ScherrerL/Desktop/apple/github_publish/acg720-fpga-flight-controller/analysis/20261026_flight_followup/response/controller_position_trace.csv","w");$fdisplay(f,"semantic_ms,phase,ch1,vy_q16,alternate_x_q8,alternate_y_q8,captured_norm_y_q16,desired_y_mmps_q16,actual_P_y_cdeg_q16,actual_I_y_cdeg_q16,actual_FF_y_cdeg_q16,roll_target_cdeg,pitch_target_cdeg");
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

module harness #(parameter KP=65536)(input wire clk,rst_n,sample_update,position_update,height_update,
 input wire[15:0]ch1,input wire signed[31:0]x,y,vy,
 output wire signed[15:0]roll,pitch,output wire pub,active,blocked);
wire mreq,mcancel,mbusy,mdone,merror,dreq,dcancel,dbusy,ddone,derror;
wire signed[63:0]ma,mb,mresult,da,dresult;wire[31:0]db;
mtf_xyz_hold_control #(.CAL_MASK(8'hff),.VELOCITY_FRAC_BITS(16),.POSITION_KP_Q16(KP))dut(
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
);
nav_math_service #(.CLIENTS(1),.DIVIDE(0))mul(.clk(clk),.rst_n(rst_n),.request(mreq),.cancel(mcancel),
 .operand_a(ma),.operand_b(mb),.busy(mbusy),.done(mdone),.error(merror),.result(mresult),.grant());
nav_math_service #(.CLIENTS(1),.DIVIDE(1))div(.clk(clk),.rst_n(rst_n),.request(dreq),.cancel(dcancel),
 .operand_a(da),.operand_b({32'd0,db}),.busy(dbusy),.done(ddone),.error(derror),.result(dresult),.grant());
assign pub=dut.command_seen && dut.command_age==0;assign blocked=dut.blocked||dut.xy_blocked;
endmodule
