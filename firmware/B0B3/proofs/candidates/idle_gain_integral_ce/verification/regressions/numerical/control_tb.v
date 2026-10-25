`timescale 1ns/1ps
module tb;
reg clk=0,rst_n=0,enabled=1,rc_valid=1,taking_off=1,origin=0,sensor_valid=1;
reg[15:0]ch7=2000,pval=500,ival=0;reg sample_update=0,position_update=0,height_update=0;
reg signed[31:0]vx=0,vy=0;
wire signed[15:0]nr,np,br,bp,orr,orp;wire signed[63:0]ix,iy,bix,biy,oix,oiy;
wire pub,bpub,opub,blocked,bb,ob,active,ba,oa;
new_harness candidate(clk,rst_n,enabled,rc_valid,taking_off,origin,sensor_valid,ch7,pval,ival,sample_update,position_update,height_update,vx,vy,nr,np,ix,iy,pub,blocked,active);
base_harness baseline(clk,rst_n,enabled,rc_valid,taking_off,origin,sensor_valid,ch7,pval,ival,sample_update,position_update,height_update,vx,vy,br,bp,bix,biy,bpub,bb,ba);
original_harness original(clk,rst_n,enabled,rc_valid,taking_off,origin,sensor_valid,ch7,pval,ival,sample_update,position_update,height_update,vx,vy,orr,orp,oix,oiy,opub,ob,oa);
always #10 clk=~clk;
integer cycles=0,samples=0,publications=0,phase=0,zcompares=0,xy_cycles=0,max_xy_cycles=0;
reg signed[15:0]last_br=0,last_bp=0,last_or=0,last_op=0;reg signed[63:0]last_oix=0,last_oiy=0;
always @(negedge clk)begin
 sample_update<=0;position_update<=0;height_update<=0;
 if(rst_n)begin
  if(candidate.dut.work_xy)xy_cycles=xy_cycles+1;
  else begin if(xy_cycles>max_xy_cycles)max_xy_cycles=xy_cycles;xy_cycles=0;end
  cycles=cycles+1;
  if(cycles%2000==0)begin
   samples=samples+1;sample_update<=1;
   if(samples%11==0)height_update<=1;
   if(samples%20==0)position_update<=1;
  end
 end
end
always @(posedge clk)begin #1;
 if(rst_n)begin
  if(blocked || bb || ob)$fatal(1,"controller blocked");
  if(bpub)begin last_br=br;last_bp=bp;end
  if(opub)begin last_or=orr;last_op=orp;last_oix=oix;last_oiy=oiy;end
  if(pub)begin
   publications=publications+1;
   if(phase==0 && (nr!==last_br || np!==last_bp || ix!=0 || iy!=0))$fatal(1,"default mismatch new=%0d,%0d old=%0d,%0d",nr,np,last_br,last_bp);
   if(phase==1 && (nr!==last_or || np!==last_op || ix!==last_oix || iy!==last_oiy))$fatal(1,"V15 restored PI mismatch %0d,%0d vs %0d,%0d I=%0d,%0d vs%0d,%0d",nr,np,last_or,last_op,ix,iy,last_oix,last_oiy);
  end
 end
end
task pubs;input integer n;integer k;begin k=0;while(k<n)begin @(posedge clk);#2;if(pub)k=k+1;end end endtask
task reset_pair;input integer p,i;begin
 @(negedge clk);rst_n=0;enabled=0;repeat(8)@(negedge clk);pval=p;ival=i;
 cycles=0;samples=0;rst_n=1;enabled=1;ch7=2000;rc_valid=1;sensor_valid=1;origin=0;taking_off=1;vx=0;vy=0;
 pubs(2);
end endtask
task velocity;input integer x,y;begin @(negedge clk);vx=x*65536;vy=y*65536;pubs(5);end endtask
function integer absint;input integer a;begin absint=a<0?-a:a;end endfunction
reg signed[63:0]savedx,savedy;integer i;
initial begin
 repeat(8)@(negedge clk);rst_n=1;
 velocity(0,0);velocity(1000,0);velocity(-1000,0);velocity(0,1000);velocity(0,-1000);velocity(401,-603);velocity(0,0);
 $display("PASS default P005/I0 exact callback outputs positive negative fractional zero");
 phase=1;reset_pair(1500,1000);velocity(1000,-1000);velocity(-400,600);velocity(0,0);
 $display("PASS original V15 P015/I010 restored integral exact callback equivalence");
 phase=2;reset_pair(1000,0);velocity(400,-600);
 if(absint(np-400)>2 || absint(nr-600)>2)$fatal(1,"nondefault P not effective %0d,%0d",nr,np);
 reset_pair(0,10000);velocity(1000,-1000);pubs(15);
 if(ix!=-65536000 || iy!=65536000 || nr!=1000 || np!=1000)$fatal(1,"I rails/output %0d,%0d angle=%0d,%0d",ix,iy,nr,np);
 velocity(0,0);savedx=ix;savedy=iy;pubs(4);
 if(ix!==savedx || iy!==savedy)$fatal(1,"zero error I changed");
 velocity(-1000,1000);pubs(20);
 if(ix!=65536000 || iy!=-65536000)$fatal(1,"negative I rails");
 // During ATT_STAB, completed states survive. Interrupted callback rolls back.
 wait(candidate.dut.work_xy && candidate.dut.state==65);@(negedge clk);ch7=1500;
 repeat(100)@(negedge clk);savedx=ix;savedy=iy;
 repeat(45000)@(negedge clk);if(ix!==savedx || iy!==savedy || active)$fatal(1,"ATT_STAB state retention/active");
 ch7=2000;pubs(2);
 taking_off=0;pubs(2);if(ix!=0 || iy!=0)$fatal(1,"not-taking-off integral not reset");taking_off=1;
 velocity(1000,0);@(negedge clk);sensor_valid=0;repeat(50)@(negedge clk);
 if(active || ix!=0 || iy!=0)$fatal(1,"sensor loss did not cancel/reset");sensor_valid=1;pubs(3);
 @(negedge clk);rc_valid=0;repeat(50)@(negedge clk);if(active || ix!=0 || iy!=0)$fatal(1,"RC loss");rc_valid=1;pubs(2);
 @(negedge clk);enabled=0;repeat(50)@(negedge clk);if(active || ix!=0 || iy!=0)$fatal(1,"stop reset");
 // Safe stopped parameter change followed by re-entry must not reuse old I.
 pval=500;ival=0;enabled=1;velocity(1000,0);if(ix!=0 || iy!=0 || absint(np-500)>2)$fatal(1,"I0 residue on restart");
 $display("PASS nondefault P, nonzero I, both rails, zero error, cancellation, mode reentry, RC/sensor/stop reset publications=%0d",publications);
 // Directly perturb interface inputs mid-callback (the production bank
 // forbids this), proving the controller's coherent work-pair snapshot.
 reset_pair(1000,0);@(negedge clk);vx=400*65536;vy=-600*65536;
 wait(candidate.dut.work_xy && candidate.dut.state==6);@(negedge clk);pval=2000;ival=5000;
 @(posedge clk);#2;if(candidate.dut.work_p!=1000 || candidate.dut.work_i!=0)$fatal(1,"work pair changed during callback");
 pubs(1);if(ix!=0 || iy!=0 || absint(np-400)>2 || absint(nr-600)>2)$fatal(1,"callback mixed gain pairs");
 pubs(1);if(candidate.dut.work_p!=2000 || candidate.dut.work_i!=5000)$fatal(1,"next callback missed pair");
 if(max_xy_cycles>=50000)$fatal(1,"isolated callback exceeded 1ms budget");
 $display("PASS coherent work pair across interleaved input update; max isolated XY callback %0d clocks (%0d ns at 50MHz)",max_xy_cycles,max_xy_cycles*20);
 reset_pair(10000,0);velocity(10000,10000);
 if(np!=2500 || nr!=-2500)$fatal(1,"max legal P positive velocity overflow before angle clip %0d,%0d",nr,np);
 velocity(-10000,-10000);if(np!=-2500 || nr!=2500)$fatal(1,"max legal P negative velocity overflow before angle clip %0d,%0d",nr,np);
 $display("PASS maximum encoded P=1 with +/-10000mm/s: signed P+I+FF reaches final angle clip without wrap");
 $finish;
end
initial begin #500000000;$fatal(1,"control timeout");end
endmodule
module new_harness(input wire clk,rst_n,enabled,rc_valid,taking_off,origin,sensor_valid,
 input wire[15:0]ch7,pval,ival,input wire sample_update,position_update,height_update,
 input wire signed[31:0]vx,vy,output wire signed[15:0]roll,pitch,
 output wire signed[63:0]ix,iy,output wire published,blocked,active);
 wire mreq,mcancel,mbusy,mdone,merror,dreq,dcancel,dbusy,ddone,derror;
 wire signed[63:0]ma,mb,mresult,da,dresult;wire[31:0]db;
 mtf_xyz_hold_control #(.CAL_MASK(8'hff),.VELOCITY_FRAC_BITS(16))dut(.xy_p_value(pval),.xy_i_value(ival),.parameter_boundary(),
 .clk(clk),.rst_n(rst_n),.origin_reset(origin),.rc_valid(rc_valid),.channel_count(4'd8),
 .ch1(16'd1500),.ch2(16'd1500),.ch3(16'd1500),.ch4(16'd1500),.ch7(ch7),
 .enabled(enabled),.taking_off(taking_off),.position_valid(sensor_valid),.height_valid(sensor_valid),
 .position_update(position_update),.height_update(height_update),
 .sample_update(sample_update),.sample_dt_us(32'd1000),.position_age(32'd0),.position_dt_us(32'd20000),
 .x_q8(32'sd0),.y_q8(32'sd0),.vx(vx),.vy(vy),.height_mm(32'sd1000),.vz(32'sd0),.yaw_cdeg(16'sd0),
 .acc_valid(sensor_valid),.ax_mmps2(32'sd0),.ay_mmps2(32'sd0),.az_mmps2(32'sd0),.collective_us(16'd1500),
 .requested(),.ready(),.active(active),.height_requested(),.height_ready(),.height_active(),
 .auto_takeoff(),.reason(),.height_reason(),.collective_target_us(),
 .roll_target(roll),.pitch_target(pitch),.throttle_delta(),.requested_climb_mmps(),.target_height_mm(),
 .pilot_norm_x(),.pilot_norm_y(),.pilot_norm_update(),.pilot_norm_valid(),.pilot_norm_dt_us(),
 .math_mul_start(mreq),.math_mul_cancel(mcancel),.math_mul_a(ma),.math_mul_b(mb),
 .math_mul_busy(mbusy),.math_mul_done(mdone),.math_mul_result(mresult),
 .math_div_start(dreq),.math_div_cancel(dcancel),.math_div_numerator(da),.math_div_denominator(db),
 .math_div_busy(dbusy),.math_div_done(ddone),.math_div_error(derror),.math_div_result(dresult));
 nav_math_service #(.CLIENTS(1),.DIVIDE(0))mul(.clk(clk),.rst_n(rst_n),.request(mreq),.cancel(mcancel),
 .operand_a(ma),.operand_b(mb),.busy(mbusy),.done(mdone),.error(merror),.result(mresult),.grant());
 nav_math_service #(.CLIENTS(1),.DIVIDE(1))div(.clk(clk),.rst_n(rst_n),.request(dreq),.cancel(dcancel),
 .operand_a(da),.operand_b({32'd0,db}),.busy(dbusy),.done(ddone),.error(derror),.result(dresult),.grant());
 assign ix=dut.ix;assign iy=dut.iy;assign blocked=dut.blocked||dut.xy_blocked;
 assign published=dut.command_seen && dut.command_age==0;
 endmodule
module base_harness(input wire clk,rst_n,enabled,rc_valid,taking_off,origin,sensor_valid,
 input wire[15:0]ch7,pval,ival,input wire sample_update,position_update,height_update,
 input wire signed[31:0]vx,vy,output wire signed[15:0]roll,pitch,
 output wire signed[63:0]ix,iy,output wire published,blocked,active);
 wire mreq,mcancel,mbusy,mdone,merror,dreq,dcancel,dbusy,ddone,derror;
 wire signed[63:0]ma,mb,mresult,da,dresult;wire[31:0]db;
 mtf_xyz_hold_control_p005 #(.CAL_MASK(8'hff),.VELOCITY_FRAC_BITS(16))dut(
 .clk(clk),.rst_n(rst_n),.origin_reset(origin),.rc_valid(rc_valid),.channel_count(4'd8),
 .ch1(16'd1500),.ch2(16'd1500),.ch3(16'd1500),.ch4(16'd1500),.ch7(ch7),
 .enabled(enabled),.taking_off(taking_off),.position_valid(sensor_valid),.height_valid(sensor_valid),
 .position_update(position_update),.height_update(height_update),
 .sample_update(sample_update),.sample_dt_us(32'd1000),.position_age(32'd0),.position_dt_us(32'd20000),
 .x_q8(32'sd0),.y_q8(32'sd0),.vx(vx),.vy(vy),.height_mm(32'sd1000),.vz(32'sd0),.yaw_cdeg(16'sd0),
 .acc_valid(sensor_valid),.ax_mmps2(32'sd0),.ay_mmps2(32'sd0),.az_mmps2(32'sd0),.collective_us(16'd1500),
 .requested(),.ready(),.active(active),.height_requested(),.height_ready(),.height_active(),
 .auto_takeoff(),.reason(),.height_reason(),.collective_target_us(),
 .roll_target(roll),.pitch_target(pitch),.throttle_delta(),.requested_climb_mmps(),.target_height_mm(),
 .pilot_norm_x(),.pilot_norm_y(),.pilot_norm_update(),.pilot_norm_valid(),.pilot_norm_dt_us(),
 .math_mul_start(mreq),.math_mul_cancel(mcancel),.math_mul_a(ma),.math_mul_b(mb),
 .math_mul_busy(mbusy),.math_mul_done(mdone),.math_mul_result(mresult),
 .math_div_start(dreq),.math_div_cancel(dcancel),.math_div_numerator(da),.math_div_denominator(db),
 .math_div_busy(dbusy),.math_div_done(ddone),.math_div_error(derror),.math_div_result(dresult));
 nav_math_service #(.CLIENTS(1),.DIVIDE(0))mul(.clk(clk),.rst_n(rst_n),.request(mreq),.cancel(mcancel),
 .operand_a(ma),.operand_b(mb),.busy(mbusy),.done(mdone),.error(merror),.result(mresult),.grant());
 nav_math_service #(.CLIENTS(1),.DIVIDE(1))div(.clk(clk),.rst_n(rst_n),.request(dreq),.cancel(dcancel),
 .operand_a(da),.operand_b({32'd0,db}),.busy(dbusy),.done(ddone),.error(derror),.result(dresult),.grant());
 assign ix=dut.ix;assign iy=dut.iy;assign blocked=dut.blocked||dut.xy_blocked;
 assign published=dut.command_seen && dut.command_age==0;
 endmodule
module original_harness(input wire clk,rst_n,enabled,rc_valid,taking_off,origin,sensor_valid,
 input wire[15:0]ch7,pval,ival,input wire sample_update,position_update,height_update,
 input wire signed[31:0]vx,vy,output wire signed[15:0]roll,pitch,
 output wire signed[63:0]ix,iy,output wire published,blocked,active);
 wire mreq,mcancel,mbusy,mdone,merror,dreq,dcancel,dbusy,ddone,derror;
 wire signed[63:0]ma,mb,mresult,da,dresult;wire[31:0]db;
 mtf_xyz_hold_control_v15 #(.CAL_MASK(8'hff),.VELOCITY_FRAC_BITS(16))dut(
 .clk(clk),.rst_n(rst_n),.origin_reset(origin),.rc_valid(rc_valid),.channel_count(4'd8),
 .ch1(16'd1500),.ch2(16'd1500),.ch3(16'd1500),.ch4(16'd1500),.ch7(ch7),
 .enabled(enabled),.taking_off(taking_off),.position_valid(sensor_valid),.height_valid(sensor_valid),
 .position_update(position_update),.height_update(height_update),
 .sample_update(sample_update),.sample_dt_us(32'd1000),.position_age(32'd0),.position_dt_us(32'd20000),
 .x_q8(32'sd0),.y_q8(32'sd0),.vx(vx),.vy(vy),.height_mm(32'sd1000),.vz(32'sd0),.yaw_cdeg(16'sd0),
 .acc_valid(sensor_valid),.ax_mmps2(32'sd0),.ay_mmps2(32'sd0),.az_mmps2(32'sd0),.collective_us(16'd1500),
 .requested(),.ready(),.active(active),.height_requested(),.height_ready(),.height_active(),
 .auto_takeoff(),.reason(),.height_reason(),.collective_target_us(),
 .roll_target(roll),.pitch_target(pitch),.throttle_delta(),.requested_climb_mmps(),.target_height_mm(),
 .pilot_norm_x(),.pilot_norm_y(),.pilot_norm_update(),.pilot_norm_valid(),.pilot_norm_dt_us(),
 .math_mul_start(mreq),.math_mul_cancel(mcancel),.math_mul_a(ma),.math_mul_b(mb),
 .math_mul_busy(mbusy),.math_mul_done(mdone),.math_mul_result(mresult),
 .math_div_start(dreq),.math_div_cancel(dcancel),.math_div_numerator(da),.math_div_denominator(db),
 .math_div_busy(dbusy),.math_div_done(ddone),.math_div_error(derror),.math_div_result(dresult));
 nav_math_service #(.CLIENTS(1),.DIVIDE(0))mul(.clk(clk),.rst_n(rst_n),.request(mreq),.cancel(mcancel),
 .operand_a(ma),.operand_b(mb),.busy(mbusy),.done(mdone),.error(merror),.result(mresult),.grant());
 nav_math_service #(.CLIENTS(1),.DIVIDE(1))div(.clk(clk),.rst_n(rst_n),.request(dreq),.cancel(dcancel),
 .operand_a(da),.operand_b({32'd0,db}),.busy(dbusy),.done(ddone),.error(derror),.result(dresult),.grant());
 assign ix=dut.ix;assign iy=dut.iy;assign blocked=dut.blocked||dut.xy_blocked;
 assign published=dut.command_seen && dut.command_age==0;
 endmodule
