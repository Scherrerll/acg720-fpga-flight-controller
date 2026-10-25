`timescale 1ns/1ps
module tap_tb;
 reg clk=0;always #5 clk=~clk;
 reg rst_n=0,taking_off=0,gate_event=0,record_ready=0,checked_ready=0,checked_base_ok=1;
 reg [95:0] checked_raw=0,trusted=0,candidate=0;
 reg [31:0] source_id=0,source_tick=0,accepted_count=0,accepted_age=0,recovery_count=0;
 reg [9:0] reader_meta=10'b11;
 reg [7:0] temporal_detail=0,quiet_count=0;
 reg candidate_pending=0,accepted=0,link_usable=1,guard_qualified=1,guard_stale=0;
 reg attitude_update=0,attitude_valid=0,linear_accel_valid=1,calibrated=1,initialized=1,ready=1,reseed=0;
 reg [7:0] reseed_count=0,estimator_state=0,resume_state=0,first_cause=6,attitude_fault=0;
 reg [31:0] consumed_id=5,held_dt=50000;
 reg signed [31:0] world_ax=-123,world_ay=456,world_az=-789;
 reg signed [15:0] roll=-101,pitch=202,yaw=-303;
 wire raw_valid,pose_valid,fault_valid;
 wire [207:0] raw_body;wire [223:0] pose_body;wire [703:0] fault_body;
 wire [31:0] raw_tick,pose_tick,fault_tick,clock_ticks,max_accept_gap,raw_count,pose_count;
 reg [703:0] frozen;reg [31:0] frozen_tick;
 imu_diagnostic_tap #(.POSE_AGE_TRIGGER(40)) dut(.*);
 task step;begin @(posedge clk);#1;end endtask
 initial begin
  repeat(2)step();@(negedge clk);rst_n=1;
  // Source metadata must remain coherent even when producer words change.
  @(negedge clk);record_ready=1;checked_ready=1;source_id=32'h12345678;source_tick=32'h89abcdef;
  checked_raw=96'h0001fffe0003fffc0005fffa;trusted=96'h111122223333444455556666;
  candidate=96'h777788889999aaaabbbbcccc;temporal_detail=2;quiet_count=16;candidate_pending=1;
  reader_meta={8'h40,2'b11};step();
  if(raw_valid)$fatal(1,"raw precedes guard decision");
  @(negedge clk);checked_ready=0;record_ready=0;checked_raw=0;trusted=0;candidate=0;
  accepted=0;accepted_count=5;recovery_count=3;step();
  if(!raw_valid || raw_tick!==32'h89abcdef ||
    raw_body!=={32'h12345678,96'h0001fffe0003fffc0005fffa,32'd5,8'd2,8'h40,8'hb7,8'd16,8'd3,8'd0})
    $fatal(1,"raw payload/flags/guard alignment %h",raw_body);
  @(negedge clk);accepted=1;step();@(negedge clk);accepted=0;
  attitude_update=1;attitude_valid=1;step();
  if(!pose_valid || pose_count!=1 || pose_body!=={32'd5,32'd50000,-32'sd123,32'sd456,-32'sd789,-16'sd101,16'sd202,-16'sd303,8'h1f,8'd0})
    $fatal(1,"pose source/dt/world/sign contract %h",pose_body);
  @(negedge clk);attitude_update=0;
  repeat(42)step();
  if(!fault_valid || fault_body[703:696]!==8'd1 || fault_body[671:640]!==32'h12345678 ||
    fault_body[287:192]!==96'h0001fffe0003fffc0005fffa ||
    fault_body[191:96]!==96'h111122223333444455556666 ||
    fault_body[95:0]!==96'h777788889999aaaabbbbcccc)$fatal(1,"fault coherent triple/age trigger");
  frozen=fault_body;frozen_tick=fault_tick;
  @(negedge clk);source_id=99;temporal_detail=8;checked_ready=1;checked_raw=96'hffffffffffffffffffffffff;step();
  if(fault_body!==frozen || fault_tick!==frozen_tick)$fatal(1,"frozen fault changed");
  @(negedge clk);taking_off=1;checked_ready=0;step();
  if(fault_valid)$fatal(1,"new window did not expose low-valid clock");
  @(negedge clk);gate_event=1;attitude_valid=0;step();
  if(!fault_valid || fault_body[703:696]!==8'd7 || fault_tick==frozen_tick)$fatal(1,"simultaneous triggers/window rearm");
  if(raw_count!=1 || pose_count!=1 || max_accept_gap==0)$fatal(1,"producer counters/gap");
  $display("PASS tap: raw/pose wire contract, coherent reject triple, freeze, simultaneous triggers, rearm");$finish;
 end
 initial begin #100000;$fatal(1,"timeout");end
endmodule
