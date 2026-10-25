`timescale 1ns/1ps
module sik_copy_contract_tb;
 reg clk=0;always #10 clk=~clk;
 reg rst_n=0,snapshot_hold=0,taking_off=0;
 reg record_ready=0,checked_ready=0,accepted=0,attitude_update=0;
 reg [95:0] checked_raw=0;reg [31:0] accepted_count=0,source_id=0;
 reg [31:0] source_tick=0,held_dt=50000,consumed_id=0;
 reg [9:0] reader_meta=3;reg checked_base_ok=1;
 reg [7:0] temporal_detail=0,first_cause=0;
 wire raw_valid,pose_valid,fault_valid;wire [207:0] raw_body;wire [223:0] pose_body;wire [703:0] fault_body;
 wire [31:0] pose_tick,fault_tick,clock_ticks,raw_count,pose_count;
 reg [63:0] uptime_ms=0,event_time_ms=0;
 reg [15:0] event_sequence=0;reg [7:0] event_code=0,event_mask=0,event_imu=0,event_attitude=0;
 reg [31:0] event_pose_age=0;
 wire [511:0] original_body,copy_body;wire [31:0] original_tick,copy_tick;
 imu_diagnostic_tap #(.POSE_AGE_TRIGGER(1000)) actual_tap(.clk(clk),.rst_n(rst_n),.taking_off(taking_off),.gate_event(1'b0),
 .record_ready(record_ready),.checked_ready(checked_ready),.checked_base_ok(checked_base_ok),.checked_raw(checked_raw),
 .trusted(96'd0),.candidate(96'd0),.source_id(source_id),.source_tick(source_tick),.reader_meta(reader_meta),
 .temporal_detail(temporal_detail),.quiet_count(8'd0),.candidate_pending(1'b0),.accepted(accepted),
 .accepted_count(accepted_count),.accepted_age(32'd50000),.link_usable(rst_n),.guard_qualified(rst_n),.guard_stale(1'b0),
 .recovery_count(32'd5),.attitude_update(attitude_update),.attitude_valid(rst_n),.linear_accel_valid(rst_n),
 .calibrated(rst_n),.initialized(rst_n),.ready(rst_n),.reseed(1'b0),.reseed_count(8'd0),
 .estimator_state(8'd0),.resume_state(8'd0),.first_cause(first_cause),.attitude_fault(8'd0),
 .consumed_id(consumed_id),.held_dt(held_dt),.world_ax(32'sd0),.world_ay(32'sd0),.world_az(32'sd0),
 .roll(16'sd0),.pitch(16'sd0),.yaw(16'sd0),.raw_valid(raw_valid),.raw_body(raw_body),.raw_tick(),
 .pose_valid(pose_valid),.pose_body(pose_body),.pose_tick(pose_tick),.fault_valid(fault_valid),
 .fault_body(fault_body),.fault_tick(fault_tick),.clock_ticks(clock_ticks),.max_accept_gap(),.raw_count(raw_count),.pose_count(pose_count));
 sik_original original(.clk(clk),.rst_n(rst_n),.snapshot_hold(snapshot_hold),.taking_off(taking_off),
 .raw_valid(raw_valid),.raw_body(raw_body),.pose_valid(pose_valid),.pose_body(pose_body),.pose_tick(pose_tick),
 .fault_valid(fault_valid),.fault_body(fault_body),.fault_tick(fault_tick),.clock_ticks(clock_ticks),.raw_count(raw_count),.pose_count(pose_count),
 .uptime_ms(uptime_ms),.build_id(32'hb0b2),.event_sequence(event_sequence),.event_time_ms(event_time_ms),
 .event_code(event_code),.event_mask(event_mask),.event_imu(event_imu),.event_attitude(event_attitude),.event_pose_age(event_pose_age),
 .summary_body(original_body),.summary_tick(original_tick));
 sik_imu_diagnostic copy(.clk(clk),.rst_n(rst_n),.snapshot_hold(snapshot_hold),.taking_off(taking_off),
 .raw_valid(raw_valid),.raw_body(raw_body),.pose_valid(pose_valid),.pose_body(pose_body),.pose_tick(pose_tick),
 .fault_valid(fault_valid),.fault_body(fault_body),.fault_tick(fault_tick),.clock_ticks(clock_ticks),.raw_count(raw_count),.pose_count(pose_count),
 .uptime_ms(uptime_ms),.build_id(32'hb0b2),.event_sequence(event_sequence),.event_time_ms(event_time_ms),
 .event_code(event_code),.event_mask(event_mask),.event_imu(event_imu),.event_attitude(event_attitude),.event_pose_age(event_pose_age),
 .summary_body(copy_body),.summary_tick(copy_tick));
 integer cycle=0,same_cycle=0,rejects=0,hold_rise=0,hold_fall=0,held_updates=0,resets=0,no_pose=0,max_no_pose=0;
 reg prior_hold=0;reg [207:0] prior_raw=0;reg [223:0] prior_pose=0;reg [31:0] random_state=32'hc18a53f1;
 always @(negedge clk)begin
  if(original_body!==copy_body || original_tick!==copy_tick)$fatal(1,"copy99 output/edge mismatch cycle=%0d bodyxor=%h",cycle,original_body^copy_body);
  if(rst_n && !raw_valid && raw_body!==prior_raw)$fatal(1,"actual tap violated raw held-data prerequisite");
  if(rst_n && !pose_valid && pose_body!==prior_pose)$fatal(1,"actual tap violated pose held-data prerequisite");
  prior_raw=raw_body;prior_pose=pose_body;
  if(raw_valid && pose_valid)same_cycle=same_cycle+1;
  if(raw_valid && !raw_body[27])rejects=rejects+1;
  if(snapshot_hold && (raw_valid || pose_valid))held_updates=held_updates+1;
  if(snapshot_hold && !prior_hold)hold_rise=hold_rise+1;
  if(!snapshot_hold && prior_hold)hold_fall=hold_fall+1;
  prior_hold=snapshot_hold;
  if(!pose_valid)no_pose=no_pose+1;else begin if(no_pose>max_no_pose)max_no_pose=no_pose;no_pose=0;end
  cycle=cycle+1;
  if(cycle>=120000)begin
   if(same_cycle<100 || rejects<100 || held_updates<100 || hold_rise<100 || hold_fall<100 || max_no_pose<6000 || resets<5)$fatal(1,"coverage insufficient same=%0d rejects=%0d held=%0d rise=%0d fall=%0d outage=%0d resets=%0d",same_cycle,rejects,held_updates,hold_rise,hold_fall,max_no_pose,resets);
   $display("PASS copy99 actual_tap miter 120000 cycles, body+tick exact every edge; raw_pose_same=%0d rejects=%0d held_updates=%0d hold_rise=%0d hold_fall=%0d max_no_pose=%0d reset_cycles=%0d",same_cycle,rejects,held_updates,hold_rise,hold_fall,max_no_pose,resets);$finish;
  end
  random_state={random_state[30:0],random_state[31]^random_state[21]^random_state[1]^random_state[0]};
  rst_n=!(cycle<5 || (cycle>=30000 && cycle<30003) || (cycle>=80000 && cycle<80004));
  if(!rst_n)resets=resets+1;
  snapshot_hold=random_state[3] || (cycle>=6000 && cycle<11000);
  taking_off=(cycle%997)<20;
  record_ready=random_state[0];checked_ready=random_state[1];accepted=random_state[18];
  attitude_update=random_state[4] && random_state[5] && !(cycle>=5000 && cycle<12000);
  checked_raw={random_state,random_state^32'hf31a93c1,random_state+32'h43278};
  source_id=source_id+checked_ready;source_tick=clock_ticks;
  reader_meta={random_state[14:7],2'b11};temporal_detail=random_state[7]?8'h80:0;
  checked_base_ok=random_state[8];first_cause=random_state[11:8];
  held_dt=50000+{16'd0,random_state[15:0]};
  if(accepted)accepted_count=accepted_count+1;
  if(attitude_update)consumed_id=accepted_count;
  if(cycle%50==0)uptime_ms=uptime_ms+1;
  if(random_state[11:8]==4'h3)begin
   event_sequence=event_sequence+1;event_time_ms=uptime_ms;event_code=random_state[12]?8'h31:8'h32;
   event_mask=random_state[23:16];event_imu=random_state[31:24];event_attitude=random_state[19:12];event_pose_age=random_state;
  end
 end
endmodule
