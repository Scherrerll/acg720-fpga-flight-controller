`timescale 1ns/1ps
module tap_pipeline_tb;
 reg clk=0;always #5 clk=~clk;
 reg rst_n=0,stim_record=0;
 reg [95:0] stim_raw={16'd0,16'd0,16'd2048,16'd1,16'd2,16'd3};
 wire diag_raw_valid,diag_pose_valid,diag_fault_valid;
 wire [207:0] diag_raw_body;wire [223:0] diag_pose_body;wire [703:0] diag_fault_body;
 wire [31:0] diag_raw_tick,diag_pose_tick,diag_fault_tick,diag_clock_ticks,diag_max_accept_gap,diag_raw_count,diag_pose_count;
 integer raw_packets=0,pose_packets=0,reject_packets=0,n;
 reg [95:0] expected_raw[1:64];reg [31:0] expected_tick[1:64],accepted_dt[1:64];
 reg [31:0] last_accept=0,id;
 // Shorter source deadline exposes the actual guard->estimator NBA boundary
 // before the independent tap's default 20ms pose-age trigger.
 imu_pipeline #(.CAL_SAMPLES(2),.DATA_TIMEOUT_TICKS(50000)) dut(.clk50(clk),.rst_n(rst_n),.imu_miso(1'b0),
  .diag_taking_off(1'b0),.diag_gate_event(1'b0),.diag_raw_valid(diag_raw_valid),.diag_pose_valid(diag_pose_valid),
  .diag_fault_valid(diag_fault_valid),.diag_raw_body(diag_raw_body),.diag_pose_body(diag_pose_body),.diag_fault_body(diag_fault_body),
  .diag_raw_tick(diag_raw_tick),.diag_pose_tick(diag_pose_tick),.diag_fault_tick(diag_fault_tick),
  .diag_clock_ticks(diag_clock_ticks),.diag_max_accept_gap(diag_max_accept_gap),.diag_raw_count(diag_raw_count),.diag_pose_count(diag_pose_count));
 always @(posedge clk)if(rst_n && stim_record)begin
  expected_raw[diag_raw_count+1]=stim_raw;expected_tick[diag_raw_count+1]=diag_clock_ticks;
 end
 always @(negedge clk)if(rst_n)begin
  if(dut.sample_valid)accepted_dt[dut.accepted_count]=dut.dt_ticks;
  if(diag_raw_valid)begin
   raw_packets=raw_packets+1;id=diag_raw_body[207:176];
   if(id!=raw_packets || diag_raw_body[175:80]!==expected_raw[id] || diag_raw_tick!==expected_tick[id])
    $fatal(1,"pipeline source/tuple/timestamp association");
   if(diag_raw_body[27])begin
    if(diag_raw_body[79:48]!=last_accept+1)$fatal(1,"raw guard acceptance count mismatch");
    last_accept=diag_raw_body[79:48];
   end else begin
    reject_packets=reject_packets+1;
    if(diag_raw_body[79:48]!=last_accept || diag_raw_body[47:40]==0)$fatal(1,"reject decision mismatch");
   end
  end
  if(diag_pose_valid)begin
   pose_packets=pose_packets+1;id=diag_pose_body[223:192];
   if(id==0 || id>last_accept || diag_pose_body[191:160]!==accepted_dt[id])
    $fatal(1,"pipeline pose did not retain consumed acceptance/dt");
  end
 end
 initial begin
  // Exercise the actual temporal/guard/estimator path; isolate physical SPI.
  force dut.record_ready=stim_record;force dut.record_raw=stim_raw;
  force dut.reader_valid=1;force dut.reader_config_ok=1;force dut.reader_fault=0;
  force dut.who=8'h1e;force dut.pwr=8'h0f;
  repeat(3)@(negedge clk);rst_n=1;
  for(n=1;n<=40;n=n+1)begin
   @(negedge clk);
   if(n==24)stim_raw={16'd600,16'd0,16'd2048,16'd1,16'd2,16'd3};
   else if(n==25)stim_raw={-16'sd600,16'd0,16'd2048,16'd1,16'd2,16'd3};
   else stim_raw={16'd0,16'd0,16'd2048,16'd1,16'd2,16'd3};
   stim_record=1;@(negedge clk);stim_record=0;stim_raw=96'hffffffffffffffffffffffff;
   repeat(9999)@(negedge clk);
  end
  repeat(20)@(negedge clk);
  if(raw_packets!=40 || reject_packets!=2 || pose_packets<20 || diag_raw_count!=40 || diag_pose_count!=pose_packets)
   $fatal(1,"pipeline event coverage raw=%0d reject=%0d pose=%0d",raw_packets,reject_packets,pose_packets);
  repeat(60000)@(negedge clk);
  if(!diag_fault_valid || diag_fault_body[703:696]!=2 || diag_fault_body[695:688]!=1)
   $fatal(1,"guard timeout first-cause race: expected trigger=2 cause=1, got trigger=%0d cause=%0d",diag_fault_body[703:696],diag_fault_body[695:688]);
  $display("PASS pipeline: 40 coherent raw decisions, 2 temporal rejects, consumed acceptance/dt mapped across rejection gaps; %0d pose packets",pose_packets);$finish;
 end
 initial begin #5000000;$fatal(1,"timeout");end
endmodule
