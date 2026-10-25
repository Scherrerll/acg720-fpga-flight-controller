`timescale 1ns/1ps
// Actual B0B2 temporal stage only: no sensor, control, UART or hardware model.
module temporal_contract_tb;
 reg clk=0;always #5 clk=~clk;
 reg rst_n=0,record_ready=0,base_ok=0,calibrated=0;
 reg [95:0] raw=0;
 reg signed [15:0] bias_x=0,bias_y=0,bias_z=16'sd123;
 reg [31:0] source_id=0,source_tick=0;
 reg [9:0] reader_meta=0;
 wire checked_ready,checked_base_ok,candidate_pending;
 wire [7:0] detail,quiet_count;
 wire [95:0] checked_raw,trusted_out,candidate_out;
 wire [31:0] output_id,output_tick;
 wire [9:0] output_meta;
 // Nondefault deprecated values prove names still elaborate. Acceptance must
 // not depend on these zero thresholds, one quiet sample, calibration or bias.
 imu_temporal_check #(.TIMEOUT_TICKS(7),.QUIET_SAMPLES(1),
  .QUIET_GYRO_DELTA(0),.QUIET_ACCEL_DELTA(0),
  .MOTION_GYRO_DELTA(0),.MOTION_ACCEL_DELTA(0),
  .CONFIRM_GYRO_DELTA(0),.CONFIRM_ACCEL_DELTA(0)) dut(
  .clk(clk),.rst_n(rst_n),.record_ready(record_ready),.base_ok(base_ok),
  .calibrated(calibrated),.raw(raw),.bias_x(bias_x),.bias_y(bias_y),.bias_z(bias_z),
  .checked_ready(checked_ready),.reject_detail(detail),.quiet_count(quiet_count),
  .candidate_pending(candidate_pending),.checked_raw(checked_raw),
  .diag_source_id_in(source_id),.diag_tick_in(source_tick),.diag_reader_meta_in(reader_meta),
  .diag_source_id_out(output_id),.diag_tick_out(output_tick),.diag_reader_meta_out(output_meta),
  .diag_trusted_out(trusted_out),.diag_candidate_out(candidate_out),.checked_base_ok(checked_base_ok));

 integer checks=0,cases=0,published=0,cycles=0,gap,k;
 function [95:0] pattern;
 input [31:0] key;
 begin pattern={key,~key,key^32'h5a69c3f0};end
 endfunction

 always @(posedge clk)begin
  #1;cycles=cycles+1;
  if(quiet_count!==8'd0 || candidate_pending!==1'b0 || candidate_out!==96'd0)
   $fatal(1,"Disabled policy diagnostics not zero at cycle %0d",cycles);
  if(rst_n && checked_ready===1'b1)published=published+1;
 end

 task reset_stage;
 begin
  @(negedge clk);rst_n=0;record_ready=0;
  repeat(2)begin @(posedge clk);#2;if(checked_ready!==0)$fatal(1,"Reset published a record");end
  @(negedge clk);rst_n=1;
 end endtask

 task drive;
 input send,base;
 input [31:0] key,id,tick;
 input [9:0] meta;
 begin
  @(negedge clk);
  record_ready=send;base_ok=base;raw=pattern(key);
  source_id=id;source_tick=tick;reader_meta=meta;
  calibrated=~calibrated;bias_x=~bias_x;bias_y=bias_y+16'sd777;bias_z=-bias_z;
  @(posedge clk);#2;
 end endtask

 task none;
 input string label;
 begin
  checks=checks+1;
  if(checked_ready!==0)$fatal(1,"Unexpected/early/duplicate record: %s id=%0d",label,output_id);
 end endtask

 task packet;
 input string label;
 input base;
 input [7:0] expected_detail;
 input [31:0] key,id,tick;
 input [9:0] meta;
 input [95:0] expected_trusted;
 begin
  checks=checks+1;
  if(checked_ready!==1 || checked_base_ok!==base || detail!==expected_detail ||
    checked_raw!==pattern(key) || output_id!==id || output_tick!==tick ||
    output_meta!==meta || trusted_out!==expected_trusted)
   $fatal(1,"Packet tuple mismatch: %s ready=%b base=%b detail=%h id=%h tick=%h meta=%h raw=%h trusted=%h",
    label,checked_ready,checked_base_ok,detail,output_id,output_tick,output_meta,checked_raw,trusted_out);
 end endtask

 task bubble;
 begin drive(0,0,32'hbad00001,32'hdead0002,32'hfffffff0,10'h3ff);end
 endtask

 // Send one normal record. Mutate every live field while it is in flight.
 task normal;
 input base;
 input [31:0] key,id,tick;
 input [9:0] meta;
 input [95:0] previous_trusted;
 begin
  drive(1,base,key,id,tick,meta);none("normal capture t0");
  bubble();none("normal wait t1");
  bubble();none("normal wait t2");
  bubble();packet("normal exactly t3",base,0,key,id,tick,meta,previous_trusted);
 end endtask

 initial begin
  // Hierarchical references make removed parameter names hard elaboration
  // failures, even on tools that merely warn about unknown named overrides.
  if(dut.TIMEOUT_TICKS!=7 || dut.QUIET_SAMPLES!=1 || dut.QUIET_GYRO_DELTA!=0 ||
    dut.QUIET_ACCEL_DELTA!=0 || dut.MOTION_GYRO_DELTA!=0 || dut.MOTION_ACCEL_DELTA!=0 ||
    dut.CONFIRM_GYRO_DELTA!=0 || dut.CONFIRM_ACCEL_DELTA!=0)
   $fatal(1,"Deprecated named-parameter ABI mismatch");
  cases=cases+1;$display("CASE_PASS deprecated_named_parameter_abi");

  reset_stage();normal(1,1,101,32'hffffffef,10'h155,96'd0);
  bubble();none("normal pulse ends");
  cases=cases+1;$display("CASE_PASS exact_three_clock_tuple_and_live_input_isolation");

  // Gaps 1/2/3 cover collision in WAIT_ONE, WAIT_TWO and DECIDE itself.
  for(gap=1;gap<=3;gap=gap+1)begin
   reset_stage();drive(1,1,10,110,500010,10'h123);none("collision old t0");
   for(k=1;k<gap;k=k+1)begin bubble();none("collision before arrival");end
   drive(1,gap!=2,20+gap,220+gap,1000020+gap,10'h280+gap);
   packet("collision reports new input only",gap!=2,8'h80,20+gap,220+gap,
    1000020+gap,10'h280+gap,96'd0);
   repeat(5)begin bubble();none("both abandoned/colliding inputs must not replay");end
   // Neither rejected snapshot may become the next historical trusted tuple.
   normal(1,30,330,1500030,10'h035,96'd0);
   bubble();none("collision recovery pulse ends");
   cases=cases+1;$display("CASE_PASS collision_gap_%0d",gap);
  end

  reset_stage();normal(1,40,440,2000040,10'h145,96'd0);
  // normal() returns at t3; this send occurs at t4, the minimum safe cadence.
  normal(1,41,441,2000044,10'h246,pattern(40));
  bubble();none("four-clock cadence no extra pulse");
  cases=cases+1;$display("CASE_PASS four_clock_minimum_normal_interval");

  reset_stage();normal(1,50,550,2500050,10'h003,96'd0);
  normal(0,51,551,2500054,10'h3fc,pattern(50));
  normal(1,52,552,2500058,10'h157,pattern(50));
  bubble();none("basebad does not leak or update trusted");
  cases=cases+1;$display("CASE_PASS good_basebad_good_metadata_isolation");

  if(cases!=7 || published!=12)$fatal(1,"Contract coverage mismatch cases=%0d publications=%0d",cases,published);
  $display("TEMPORAL_CONTRACT_PASS cases=%0d checks=%0d publications=%0d cycles=%0d",cases,checks,published,cycles);
  $finish;
 end
 initial begin #20000;$fatal(1,"Contract test timeout");end
endmodule
