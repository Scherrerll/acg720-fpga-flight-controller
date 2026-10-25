`timescale 1ns/1ps
// Reuses the existing real-50MHz navigation_control.v interface/callback cadence.
// Synthetic sensor/RC inputs only. No IMU, plant, motor, transport or flight-cause model.
module tb;
 reg clk=0;always #10 clk=~clk;
 reg rst_n=0,sample=0,acc=0,en=1,origin_reset=0,sample_enable=1;
 reg signed [15:0] roll=0;
 wire xr,xready,xa,za,pr,hr;wire [15:0] xc,zc,coll;wire [719:0] diag;
 wire signed [15:0] rt,pt;
 wire tilt4500=roll>=-4500 && roll<=4500;
 mtf_xyz_navigation_control #(.PROOF_CONTROLLER(1),.PRECHECKED_YAW_RANGE(1),.PRECHECKED_HEIGHT_TILT4500(1)) dut(
  .clk(clk),.rst_n(rst_n),.origin_reset(origin_reset),.diagnostic_hold(1'b0),
  .sample_valid(sample),.range_valid(1'b1),.flow_valid(1'b1),.distance_mm(32'd1000),.dt_ms(32'd10),.source_age_ms(32'd0),
  .vx_x100(32'sd0),.vy_x100(-32'sd900000),.pose_valid(1'b1),.pose_age_ticks(32'd0),
  .roll_cdeg(roll),.pitch_cdeg(16'sd0),.yaw_cdeg(16'sd0),.yaw_range_ok(1'b1),.height_tilt4500_ok(tilt4500),
  .acc_valid(1'b1),.acc_update(acc),.acc_dt_us(32'd2000),.ax_mmps2(32'sd0),.ay_mmps2(32'sd0),.az_up_mmps2(32'sd0),
  .rc_valid(1'b1),.enabled(en),.taking_off(1'b1),.channel_count(4'd8),
  .ch1(16'd1500),.ch2(16'd1500),.ch3(16'd1500),.ch4(16'd1500),.ch7(16'd2000),.collective_us(16'd1000),
  .uptime_ms(64'd0),.diagnostic_body(diag),.position_ready(pr),.height_ready(hr),
  .xy_requested(xr),.xy_ready(xready),.xy_active(xa),.xy_reason(xc),.xy_roll_target(rt),.xy_pitch_target(pt),
  .z_active(za),.z_collective(coll),.z_reason(zc));
 integer ticks=0,stage=0;reg signed [26:0] saved_ix,saved_iy;reg signed [32:0] saved_afx,saved_afy;
 always @(negedge clk)begin
  sample=0;acc=0;
  if(rst_n)begin
   ticks=ticks+1;
   if(ticks%100000==0)acc=1;
   if(sample_enable && ticks%500000==0)sample=1;
  end
 end
 task clocks(input integer n);begin repeat(n)@(negedge clk);#1;end endtask
 initial begin
  clocks(4);rst_n=1;
  wait(xa && za && pt < -1500);@(negedge clk);#1;
  if(!dut.geometry_flow_ready || !hr || roll!=0 || pt < -2500)$fatal(1,"target/geometry condition");
  $display("STAGE target_gt15 t_ns=%0t roll_cdeg=%0d target_pitch_cdeg=%0d fused_vx_q16=%0d xy=%0d z=%0d",$time,roll,pt,dut.fused_vx_q16,xa,za);
  stage=1;wait(dut.controller_proof.state==0 && !dut.controller_proof.work_xy);@(negedge clk);#1;
  saved_ix=dut.controller_proof.ix_store;saved_iy=dut.controller_proof.iy_store;
  saved_afx=dut.controller_proof.afx_store;saved_afy=dut.controller_proof.afy_store;
  if(saved_ix==0)$fatal(1,"nonzero PI not established");
  roll=1500;#1;if(!dut.geometry_flow_ready || !xa || !za)$fatal(1,"inclusive 15 degree boundary");
  roll=1501;#1;if(dut.geometry_flow_ready || xa || !za || !hr || xc!=4)$fatal(1,"immediate flow exit/Z continuity");
  clocks(50);
  if(dut.velocity_fusion.iqx_store!=0 || dut.velocity_fusion.iqy_store!=0 || dut.fused_vx_q16!=0 || dut.fused_vy_q16!=0)$fatal(1,"fusion reset");
  if(dut.controller_proof.ix_store!==saved_ix || dut.controller_proof.iy_store!==saved_iy || dut.controller_proof.afx_store!==saved_afx || dut.controller_proof.afy_store!==saved_afy)$fatal(1,"completed XY PI/filter was not retained");
  $display("STAGE tilt_exit t_ns=%0t roll_cdeg=%0d xy=%0d z=%0d reason=%0d ix_q16=%0d fusion_iqx_q16=%0d",$time,roll,xa,za,xc,dut.controller_proof.ix_store,dut.velocity_fusion.iqx_store);
  stage=2;clocks(1000000);
  if(xa || !za || !hr || dut.controller_proof.ix_store!==saved_ix)$fatal(1,"20ms flow-loss retention");
  sample_enable=0;roll=1499;clocks(100);
  if(xa || dut.geometry_flow_ready || !za)$fatal(1,"angle alone incorrectly restored stale flow");
  $display("STAGE angle_return_no_sample xy=%0d geometry_flow=%0d z=%0d",xa,dut.geometry_flow_ready,za);
  sample_enable=1;stage=3;
  wait(dut.controller_proof.work_xy && dut.controller_proof.state==43);#1;
  if(dut.controller_proof.saved_ix!==saved_ix || dut.controller_proof.ix_store!==saved_ix)$fatal(1,"PI not retained at first recovery callback");
  wait(xa && za);@(negedge clk);#1;
  $display("STAGE restored t_ns=%0t roll_cdeg=%0d target_pitch_cdeg=%0d xy=%0d z=%0d retained_ix_before_callback=%0d",$time,roll,pt,xa,za,saved_ix);
  stage=4;origin_reset=1;clocks(30);
  if(dut.controller_proof.ix_store!=0 || dut.controller_proof.iy_store!=0 || xa || za)$fatal(1,"global reset did not clear XY PI");
  $display("PASS actual frozen navigation RTL: target>15 while geometry eligible; inclusive15/15.01 exit; Z retained; fusion resets but completed XY PI/filter retained; no-sample remains invalid; automatic fresh-callback recovery; origin clears PI");$finish;
 end
 initial begin #500000000;$fatal(1,"timeout stage=%0d xy=%b z=%b ready=%b reasons=%0d/%0d geom=%h flow=%h",stage,xa,za,xready,xc,zc,dut.geometry_reason,dut.flow_reason);end
endmodule
