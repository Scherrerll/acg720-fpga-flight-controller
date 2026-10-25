`timescale 1ns/1ps
// Only the physical reader is isolated. All temporal, guard, estimator and
// arithmetic modules are the real source, at 50,000 ticks per 1ms record.
module policy_pipeline_tb;
 reg clk=0;always #10 clk=~clk;
 reg rst_n=0,stim_record=0;
 reg [95:0] stim_raw={16'd0,16'd0,16'd2048,16'd1,16'd2,16'd3};
 reg [7:0] stim_fault=0,stim_who=8'h1e;
 wire calibrated,attitude_valid,attitude_update,link_usable;
 wire [31:0] accepted_count,rejected_count,dt_ticks,accepted_age;
 wire [7:0] attitude_fault;
 wire signed [15:0] yaw;
 integer ticks=0,sources=0,poses=0,phase=0,n,checked_source=0,last_accepted_source=0;
 integer phase_no_acc=0,phase_acc=0,captured_id=0,last_pose_id=0;
 integer a0,r0,p0,off0,gap_ticks;
 integer last_loss_tick=0,last_loss_age=0;
 reg previous_link=0;
 reg signed [15:0] yaw0;
 reg [95:0] offered_raw[1:1024],captured_raw=0;
 integer offered_tick[1:1024],offered_diag_tick[1:1024];
 reg [31:0] accepted_dt[1:1024],captured_dt=0;
`ifdef POLICY_FIXED
 wire diag_raw_valid,diag_pose_valid;
 wire [207:0] diag_raw_body;wire [223:0] diag_pose_body;
 wire [31:0] diag_raw_tick;
`endif
 imu_pipeline #(.CAL_SAMPLES(2),.DATA_TIMEOUT_TICKS(3000000)) dut(
  .clk50(clk),.rst_n(rst_n),.imu_miso(1'b0),.calibrated(calibrated),
  .attitude_valid(attitude_valid),.attitude_update(attitude_update),.link_usable(link_usable),
  .accepted_count(accepted_count),.rejected_count(rejected_count),.dt_ticks(dt_ticks),
  .accepted_raw_age_ticks(accepted_age),.attitude_fault(attitude_fault),.yaw(yaw)
`ifdef POLICY_FIXED
  ,.diag_taking_off(1'b0),.diag_gate_event(1'b0),.diag_raw_valid(diag_raw_valid),
  .diag_raw_body(diag_raw_body),.diag_raw_tick(diag_raw_tick),
  .diag_pose_valid(diag_pose_valid),.diag_pose_body(diag_pose_body)
`endif
 );
 always @(posedge clk)begin
  ticks<=ticks+1;
  if(rst_n && stim_record)begin
   sources=sources+1;offered_raw[sources]=stim_raw;offered_tick[sources]=ticks;
`ifdef POLICY_FIXED
   offered_diag_tick[sources]=dut.diag_clock_ticks;
`endif
  end
  if(rst_n && dut.sample_valid && link_usable && dut.estimator.state==0)begin
   captured_id=accepted_count;captured_raw=dut.accepted_raw;captured_dt=dt_ticks;
  end
 end
 always @(negedge clk)if(rst_n)begin
  // Observe after NBA on every clock, independently of gap-task sampling.
  if(accepted_age>=3000000 && link_usable)$fatal(1,"link remained usable at/after source-age deadline");
  if(previous_link && !link_usable)begin
   last_loss_tick=ticks;last_loss_age=accepted_age;
   if(accepted_age!=3000000)$fatal(1,"source link expired at unexpected age=%0d",accepted_age);
   $display("OBS source_expiry phase=%0d age_ticks=%0d global_tick=%0d source_delta_ticks=%0d link=%0d",phase,accepted_age,ticks,ticks-offered_tick[last_accepted_source],link_usable);
  end
  previous_link=link_usable;
  if(dut.checked_ready)begin
   checked_source=sources;
   if(dut.checked_raw!==offered_raw[checked_source])$fatal(1,"snapshot raw changed before temporal publication");
  end
  if(dut.sample_valid)begin
   if(dut.accepted_raw!==offered_raw[checked_source])$fatal(1,"guard raw not from published snapshot");
   accepted_dt[accepted_count]=dt_ticks;
   if(last_accepted_source!=0)begin
    gap_ticks=offered_tick[checked_source]-offered_tick[last_accepted_source];
    if((gap_ticks>=3000000 && dt_ticks!=0) || (gap_ticks<3000000 && dt_ticks!=gap_ticks))
     $fatal(1,"dt not from actual accepted source interval: gap=%0d dt=%0d",gap_ticks,dt_ticks);
   end
   last_accepted_source=checked_source;
  end
  if(attitude_update)begin
   poses=poses+1;
   if(captured_id<=last_pose_id || dut.estimator.held_dt!==captured_dt ||
      dut.estimator.captured_raw!==captured_raw || captured_dt!==accepted_dt[captured_id])
    $fatal(1,"pose did not retain consumed accepted sample/id/dt");
   last_pose_id=captured_id;
   if(phase==2)begin
    if(dut.accel_correction)phase_acc=phase_acc+1;else phase_no_acc=phase_no_acc+1;
   end
  end
`ifdef POLICY_FIXED
  if(diag_raw_valid)begin
   if(diag_raw_body[207:176]!=checked_source ||
      diag_raw_body[175:80]!==offered_raw[checked_source] ||
      diag_raw_tick!==offered_diag_tick[checked_source])$fatal(1,"diagnostic source id/raw/tick incoherent id=%0d expected=%0d tick=%0d expected=%0d",diag_raw_body[207:176],checked_source,diag_raw_tick,offered_diag_tick[checked_source]);
  end
  if(diag_pose_valid)begin
   if(diag_pose_body[223:192]!=last_pose_id || diag_pose_body[191:160]!==accepted_dt[last_pose_id])
    $fatal(1,"published diagnostic pose id/dt differs from consumed acceptance");
  end
`endif
 end
 task packet;
  input [95:0] value;input [7:0] bad;
  begin
   @(negedge clk);stim_raw=value;stim_fault=bad;stim_record=1;
   @(negedge clk);stim_record=0;stim_raw=96'hfedcba987654321001234567;stim_fault=0;
   repeat(49998)@(negedge clk);
  end
 endtask
 task frame;
  input signed [15:0] x,z,gz;input [7:0] bad;
  begin packet({x,16'd0,z,16'd1,16'd2,gz},bad);end
 endtask
 task normal;begin frame(0,2048,3,0);end endtask
 task idle_to_gap;
  input integer milliseconds;
  begin repeat(milliseconds*50000-50000)@(negedge clk);end
 endtask
 task short_gap;
  input integer milliseconds;
  begin
   p0=poses;idle_to_gap(milliseconds);
   if(!link_usable || !attitude_valid || poses!=p0)$fatal(1,"short true gap incorrectly revoked or fabricated pose");
   normal();
   if(!link_usable || !attitude_valid || poses!=p0+1 || dt_ticks!=milliseconds*50000)
    $fatal(1,"short true gap recovery/dt changed %0dms dt=%0d",milliseconds,dt_ticks);
   $display("PASS true_gap_%0dms retained qualified epoch; first real sample dt=%0d",milliseconds,dt_ticks);
  end
 endtask
 initial begin
  force dut.record_ready=stim_record;force dut.record_raw=stim_raw;
  force dut.reader_valid=1;force dut.reader_config_ok=1;force dut.reader_fault=stim_fault;
  force dut.who=stim_who;force dut.pwr=8'h0f;
  repeat(3)@(negedge clk);rst_n=1;
  for(n=0;n<10;n=n+1)frame(n[0] ?-16'sd600:16'sd600,2048,3,0);
  if(calibrated || poses!=0)$fatal(1,"startup motion/vibration completed stationary calibration");
  $display("PASS startup_motion: legal vibration cannot complete stationary calibration");
  for(n=0;n<40;n=n+1)normal();
  if(!calibrated || !attitude_valid || poses<20)$fatal(1,"stationary startup/calibration/gravity reseed failed");
  $display("PASS startup: real guard5 + calibration2 + gravity reseed3; poses=%0d",poses);
  phase=1;a0=accepted_count;r0=rejected_count;p0=poses;
  for(n=0;n<90;n=n+1)frame(n[0] ?-16'sd600:16'sd600,2048,3,0);
`ifdef POLICY_FIXED
  if(accepted_count-a0!=90 || rejected_count!=r0 || poses-p0!=90 || !attitude_valid || !link_usable)
   $fatal(1,"legal +/-600X still starved actual pose chain");
  $display("FIXED gravity_qualified_alternation: accepted=%0d rejected=%0d pose=%0d link=%0d",accepted_count-a0,rejected_count-r0,poses-p0,link_usable);
`else
  if(accepted_count<=a0 || rejected_count-r0<60 || poses!=p0 || link_usable)
   $fatal(1,"original starvation not reproduced: accepted=%0d rejected=%0d pose=%0d link=%0d",accepted_count-a0,rejected_count-r0,poses-p0,link_usable);
  $display("REPRODUCED original_failure gravity_qualified_alternation: accepted=%0d rejected=%0d pose=%0d link=%0d",accepted_count-a0,rejected_count-r0,poses-p0,link_usable);
`endif
  phase=0;for(n=0;n<40;n=n+1)normal();
  if(!attitude_valid)$fatal(1,"continuous good recovery did not restore original protections");
  phase=2;p0=poses;r0=rejected_count;yaw0=yaw;
  for(n=0;n<100;n=n+1)frame(0,4096,167,0);
  if(!attitude_valid || poses-p0<80 || phase_no_acc<40 ||
     ($signed(yaw)-$signed(yaw0)<30 && $signed(yaw)-$signed(yaw0)>-30))
   $fatal(1,"ACC outside window stopped gyro integration: poses=%0d no_acc=%0d yaw_delta=%0d",poses-p0,phase_no_acc,$signed(yaw)-$signed(yaw0));
`ifdef POLICY_FIXED
  if(rejected_count!=r0)$fatal(1,"legal dynamic acceleration rejected whole IMU frame");
`endif
  $display("PASS dynamic_accel: az=2g gyro_z_delta=164; poses=%0d correction_off=%0d correction_on=%0d yaw_delta_cdeg=%0d rejects=%0d",poses-p0,phase_no_acc,phase_acc,$signed(yaw)-$signed(yaw0),rejected_count-r0);
  phase=0;for(n=0;n<40;n=n+1)normal();
  a0=accepted_count;r0=rejected_count;p0=poses;
  frame(0,2048,3,8'h04);
  if(accepted_count!=a0 || rejected_count!=r0+1 || !attitude_valid || poses!=p0)
   $fatal(1,"explicit transport-fault sample refreshed acceptance or revoked stable epoch");
  normal();if(poses!=p0+1 || dt_ticks!=100000)$fatal(1,"bad-sample gap did not preserve elapsed dt");
  $display("PASS explicit_bad_sample rejected without source refresh; next valid dt=100000");
  a0=accepted_count;r0=rejected_count;p0=poses;
  packet(96'd0,0);packet({96{1'b1}},0);stim_who=0;normal();stim_who=8'h1e;
  if(accepted_count!=a0 || rejected_count!=r0+3 || poses!=p0 || !attitude_valid)
   $fatal(1,"zero/all-one/wrong-ID samples refreshed accepted source or revoked stable epoch");
  normal();if(poses!=p0+1 || dt_ticks!=200000)$fatal(1,"sentinel/ID rejection interval lost");
  $display("PASS invalid_transport: zero, all-one, wrong-ID rejected; next real dt=200000");
  for(n=0;n<10;n=n+1)packet({16'd0,16'd0,16'd2048,16'd30,16'd0,16'd300},0);
  a0=accepted_count;r0=rejected_count;p0=poses;
  for(n=0;n<10;n=n+1)packet({16'd0,16'd0,16'd2048,48'd0},0);
`ifdef POLICY_FIXED
  if(accepted_count-a0!=10 || rejected_count!=r0 || poses-p0!=10 || !attitude_valid)
   $fatal(1,"legal gyro braking to all-zero was treated as fill/corruption");
  $display("FIXED gyro_zero_braking accepted=10 rejected=0 pose=10");
`else
  if(rejected_count<=r0 || !attitude_valid)$fatal(1,"original gyro_fill rejection not reproduced");
  $display("REPRODUCED original_gyro_fill braking rejects=%0d pose=%0d",rejected_count-r0,poses-p0);
`endif
  for(n=0;n<20;n=n+1)normal();
  short_gap(20);short_gap(30);
  // The guard includes its original three-clock validation-age correction.
  // Check just after, rather than one clock before, the physical 60ms edge.
  p0=poses;idle_to_gap(60);repeat(4)@(negedge clk);
  if(link_usable || attitude_valid || poses!=p0 || dut.estimator.initialized || last_loss_age!=3000000)
   $fatal(1,"real 60ms source timeout protection weakened");
  $display("PASS exact_deadline: expiry_age_ticks=%0d expiry_global_tick=%0d; every age>=3000000 observed link=0",last_loss_age,last_loss_tick);
  for(n=0;n<4;n=n+1)begin normal();if(link_usable || attitude_valid || poses!=p0)$fatal(1,"recovery qualified before5 good records");end
  normal();if(!link_usable || attitude_valid || poses!=p0)$fatal(1,"guard5 recovery/estimator reseed3 boundary changed");
  for(n=0;n<10;n=n+1)normal();
  if(!attitude_valid || poses<=p0)$fatal(1,"60ms good-data recovery failed");
  $display("PASS true_gap_60ms revoked; guard needs5 fresh good and estimator gravity reseed before pose");
  p0=poses;idle_to_gap(60);repeat(4)@(negedge clk);
  for(n=0;n<10;n=n+1)frame(0,4096,3,0);
  if(!link_usable || attitude_valid || poses!=p0 || !calibrated || attitude_fault!=4)
   $fatal(1,"recovery gravity qualification weakened or confused with source failure");
  for(n=0;n<10;n=n+1)normal();
  if(!attitude_valid || poses<=p0)$fatal(1,"gravity-qualified reseed did not recover");
  $display("PASS recovery_gravity: source recovers at2g; pose waits for valid gravity reseed");
  a0=accepted_count;r0=rejected_count;
  @(negedge clk);stim_raw={16'd11,16'd0,16'd2048,16'd1,16'd2,16'd3};stim_record=1;
  @(negedge clk);stim_raw={16'd22,16'd0,16'd2048,16'd1,16'd2,16'd3};
  @(negedge clk);stim_record=0;repeat(20)@(negedge clk);
  if(accepted_count!=a0 || rejected_count!=r0+1 || dut.temporal_detail!=8'h80)
   $fatal(1,"overrun accepted unfinished/colliding snapshot");
  repeat(50000)@(negedge clk);normal();
  if(!attitude_valid)$fatal(1,"overrun recovery failed");
  $display("PASS overrun: unfinished and colliding frames discarded; detail80; no accepted-count refresh");
  $display("PASS integrated_policy_suite sources=%0d accepted=%0d rejected=%0d poses=%0d",sources,accepted_count,rejected_count,poses);
  $finish;
 end
 initial begin #800000000;$fatal(1,"policy timeout");end
endmodule
