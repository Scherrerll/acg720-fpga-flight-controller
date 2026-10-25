`timescale 1ns/1ps
// Actual frozen temporal + guard policy, actual B0B1 tap. Only pose production
// is a stub: one publication per qualified acceptance, no estimator arithmetic.
module tap_starvation_tb;
 reg clk=0;always #5 clk=~clk;
 reg rst_n=0,record_ready=0,taking_off=0;
 reg [95:0] raw={16'd0,16'd0,16'd2048,16'd1,16'd2,16'd3};
 reg origin_record_ready=0,attitude_update=0;
 reg [31:0] consumed_id=0;
 wire checked_ready,checked_base_ok,candidate_pending,accepted,link_usable,guard_qualified,guard_stale;
 wire [95:0] checked_raw,trusted,candidate;
 wire [7:0] temporal_detail,quiet_count;
 wire [31:0] source_id,source_tick,accepted_count,rejected_count,recovery_count,accepted_age,held_dt;
 wire [9:0] reader_meta;
 wire raw_valid,pose_valid,fault_valid;wire [207:0] raw_body;wire [223:0] pose_body;wire [703:0] fault_body;
 wire [31:0] raw_tick,pose_tick,fault_tick,clock_ticks,max_accept_gap,raw_count,pose_count;
 wire [7:0] first_cause=link_usable ?8'd0:8'd1;
 reg previous_link=0;integer phase=0,n;
 reg [31:0] lost_tick=0,a0,r0,p0,last_before_long=0,freeze_tick;
 reg [703:0] frozen;
 always @(posedge clk)begin
  origin_record_ready<=rst_n && record_ready;
  attitude_update<=rst_n && accepted && link_usable;
  if(accepted)consumed_id<=accepted_count;
  previous_link<=link_usable;
  if(phase==2 && previous_link && !link_usable)lost_tick<=clock_ticks;
 end
 imu_temporal_check #(.TIMEOUT_TICKS(3000000)) temporal(.clk(clk),.rst_n(rst_n),
  .record_ready(record_ready),.base_ok(1'b1),.calibrated(1'b1),.raw(raw),
  .bias_x(16'sd1),.bias_y(16'sd2),.bias_z(16'sd3),
  .checked_ready(checked_ready),.reject_detail(temporal_detail),.quiet_count(quiet_count),
  .candidate_pending(candidate_pending),.checked_raw(checked_raw),.checked_base_ok(checked_base_ok),
  .diag_source_id_in(raw_count+32'd1),.diag_tick_in(clock_ticks),.diag_reader_meta_in(10'd3),
  .diag_source_id_out(source_id),.diag_tick_out(source_tick),.diag_reader_meta_out(reader_meta),
  .diag_trusted_out(trusted),.diag_candidate_out(candidate));
 imu_checked_guard_pipelined #(.TIMEOUT_TICKS(3000000),.USE_PRECHECKED(1),.BAD_STREAK_REVOKES_LINK(0)) guard(
  .clk(clk),.rst_n(rst_n),.record_ready(checked_ready),.origin_record_ready(origin_record_ready),
  .who(8'h1e),.pwr(8'h0f),.raw(checked_raw),.extra_reason(temporal_detail!=0 ?8'h80:8'd0),
  .checked_base_ok(checked_base_ok),.sample_valid(accepted),.accepted_raw(),.sample_dt_ticks(held_dt),
  .link_usable(link_usable),.stale(guard_stale),.reject_reason(),.accepted_count(accepted_count),
  .rejected_count(rejected_count),.bad_streak(),.age_ticks(accepted_age),
  .diag_qualified(guard_qualified),.diag_recovery_count(recovery_count));
 imu_diagnostic_tap tap(.clk(clk),.rst_n(rst_n),.taking_off(taking_off),.gate_event(1'b0),.record_ready(record_ready),
  .checked_ready(checked_ready),.checked_base_ok(checked_base_ok),.checked_raw(checked_raw),
  .trusted(trusted),.candidate(candidate),.source_id(source_id),.source_tick(source_tick),.reader_meta(reader_meta),
  .temporal_detail(temporal_detail),.quiet_count(quiet_count),.candidate_pending(candidate_pending),
  .accepted(accepted),.accepted_count(accepted_count),.accepted_age(accepted_age),.link_usable(link_usable),
  .guard_qualified(guard_qualified),.guard_stale(guard_stale),.recovery_count(recovery_count),
  .attitude_update(attitude_update),.attitude_valid(link_usable),.linear_accel_valid(link_usable),
  .calibrated(1'b1),.initialized(1'b1),.ready(1'b1),.reseed(1'b0),.reseed_count(8'd0),
  .estimator_state(8'd0),.resume_state(8'd0),.first_cause(first_cause),.attitude_fault(8'd0),
  .consumed_id(consumed_id),.held_dt(held_dt),.world_ax(32'sd0),.world_ay(32'sd0),.world_az(32'sd0),
  .roll(16'sd0),.pitch(16'sd0),.yaw(16'sd0),.raw_valid(raw_valid),.raw_body(raw_body),.raw_tick(raw_tick),
  .pose_valid(pose_valid),.pose_body(pose_body),.pose_tick(pose_tick),.fault_valid(fault_valid),
  .fault_body(fault_body),.fault_tick(fault_tick),.clock_ticks(clock_ticks),.max_accept_gap(max_accept_gap),
  .raw_count(raw_count),.pose_count(pose_count));
 task frame;
  input signed [15:0] x;
  begin
   @(negedge clk);raw={x,16'd0,16'd2048,16'd1,16'd2,16'd3};record_ready=1;
   @(negedge clk);record_ready=0;repeat(49998)@(negedge clk);
  end
 endtask
 task new_window;
  begin @(negedge clk);taking_off=0;@(negedge clk);taking_off=1;
   @(negedge clk);if(fault_valid)$fatal(1,"new window valid did not deassert");end
 endtask
 initial begin
  repeat(3)@(negedge clk);rst_n=1;
  for(n=0;n<20;n=n+1)frame(0);
  if(!link_usable || quiet_count<16 || pose_count==0)$fatal(1,"qualified quiet warmup missing");
  new_window();phase=1;a0=accepted_count;r0=rejected_count;
  for(n=0;n<30;n=n+1)frame(n[0] ?-16'sd600:16'sd600);
  if(accepted_count!=a0 || rejected_count-r0!=30 || !link_usable || !fault_valid || fault_body[703:696]!=1)
   $fatal(1,"30ms rejection gap/20ms early freeze changed");
  frozen=fault_body;freeze_tick=fault_tick;p0=pose_count;
  for(n=0;n<10;n=n+1)frame(0);
  if(!link_usable || pose_count<=p0 || fault_body!==frozen || fault_tick!=freeze_tick)
   $fatal(1,"sub-deadline recovery/freeze changed");
  $display("PASS preserved policy: 30ms all-reject gap; tap froze at20ms while guard remained usable; baseline input restored pose");
  new_window();phase=2;a0=accepted_count;r0=rejected_count;p0=pose_count;last_before_long=tap.last_accept_tick;
  for(n=0;n<90;n=n+1)frame(n[0] ?-16'sd600:16'sd600);
  if(!fault_valid || link_usable || accepted_count<=a0 || pose_count!=p0 || recovery_count>1 || lost_tick==0)
   $fatal(1,"gravity-qualified periodic input did not reproduce recovery starvation");
  if(lost_tick-last_before_long<2999990 || lost_tick-last_before_long>3000010 ||
     fault_tick>=lost_tick || lost_tick-fault_tick<1900000)
   $fatal(1,"20ms freeze/60ms guard ordering changed: freeze=%0d lost=%0d last=%0d",fault_tick,lost_tick,last_before_long);
  frozen=fault_body;freeze_tick=fault_tick;
  $display("PASS preserved starvation: norm2=4554304 gravity-qualified +/-600X; accepted_delta=%0d rejected_delta=%0d pose_delta=0 recovery=%0d; guard_loss_gap=%0d freeze_lead=%0d ticks",accepted_count-a0,rejected_count-r0,recovery_count,lost_tick-last_before_long,lost_tick-fault_tick);
  for(n=0;n<10;n=n+1)frame(0);
  if(!link_usable || pose_count<=p0 || fault_body!==frozen || fault_tick!=freeze_tick)
   $fatal(1,"continuous-good recovery/frozen first event changed");
  $display("PASS recovery: continuous good input requalified guard and resumed pose; original frozen fault retained");$finish;
 end
 initial begin #100000000;$fatal(1,"timeout");end
endmodule
