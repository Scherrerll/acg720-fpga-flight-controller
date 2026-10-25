`timescale 1ns/1ps
module sik_summary_tb;
 reg clk=0;always #10 clk=~clk;
 reg rst_n=0,snapshot_hold=0,taking_off=0,raw_valid=0,pose_valid=0,fault_valid=0;
 reg [207:0] raw_body=0;reg [223:0] pose_body=0;reg [703:0] fault_body=0;
 reg [31:0] pose_tick=0,fault_tick=0,clock_ticks=0,raw_count=0,pose_count=0;
 reg [63:0] uptime_ms=0,event_time_ms=0;reg [31:0] build_id=32'hb0b2;
 reg [15:0] event_sequence=0;
 reg [7:0] event_code=0,event_mask=0,event_imu=0,event_attitude=0;
 reg [31:0] event_pose_age=0;wire [511:0] summary_body;wire [31:0] summary_tick;
 sik_imu_diagnostic d(.*);
 always @(negedge clk)if(summary_body[319:288]!==32'd0 || summary_body[95:64]!==32'd0)$fatal(1,"v2 unavailable slots nonzero");
 task step;begin @(posedge clk);#1;@(negedge clk);end endtask
 reg [511:0] held;
 initial begin
  step;rst_n=1;clock_ticks=10;raw_count=10;pose_count=1;
  raw_valid=1;raw_body[207:176]=8;raw_body[79:48]=5;raw_body[47:40]=8'h80;raw_body[39:32]=1;
  pose_valid=1;pose_tick=10;pose_body[223:192]=4;pose_body[191:160]=50000;pose_body[15:8]=8'h0f;
  step;
  if(summary_body[383:352]!=5 || summary_body[319:288]!=0 || summary_body[255:224]!=4 || summary_body[223:192]!=50000)$fatal(1,"same-cycle tuple");
  if(summary_body[159:136]!=24'h018000 || summary_body[135:128]!=8'h0f)$fatal(1,"rejection/pose flags");
  raw_valid=0;pose_valid=0;clock_ticks=1000;step;
  if(summary_body[287:256]!=990)$fatal(1,"ongoing gap missing");
  held=summary_body;snapshot_hold=1;clock_ticks=1100;
  raw_valid=1;raw_body[207:176]=9;raw_body[79:48]=6;raw_body[47:40]=0;raw_body[39:32]=8'h40;
  pose_valid=1;pose_tick=1100;pose_body[223:192]=5;pose_body[191:160]=60000;
  taking_off=1;event_sequence=1;event_code=8'h32;event_mask=8'h04;event_imu=8'h80;event_attitude=4;event_pose_age=3000000;event_time_ms=64'h100000064;
  fault_valid=1;fault_tick=100;fault_body[703:696]=1;fault_body[695:688]=0;
  step;if(summary_body!==held)$fatal(1,"hold changed packet");
  raw_valid=0;pose_valid=0;taking_off=0;clock_ticks=1200;
  event_sequence=2;event_code=8'h31;event_time_ms=200;step;
  snapshot_hold=0;clock_ticks=1300;step;
  if(summary_body[383:352]!=6 || summary_body[319:288]!=0 || summary_body[159:144]!=16'h4000)$fatal(1,"held source/reject lost");
  if(summary_body[255:224]!=5 || summary_body[223:192]!=60000 || summary_body[287:256]!=1090)$fatal(1,"pose/max gap lost");
  if(summary_body[191:160]!=100 || summary_body[119:96]!=24'h010000)$fatal(1,"diagnostic anomaly/cause0");
  if(summary_body[95:0]!={32'd0,8'h32,8'h04,8'h80,8'd4,32'd3000000})$fatal(1,"first protection/hold lost");
  // Tap still presents the old frozen fault on the new-window edge.
  taking_off=1;event_sequence=3;event_code=8'h34;step;
  if(summary_body[191:160]!=0 || summary_body[119:96]!=0)$fatal(1,"old diagnostic crossed new-window edge");
  snapshot_hold=1;fault_valid=0;step;
  if(summary_body[191:160]!=0 || summary_body[119:96]!=0)$fatal(1,"old diagnostic frozen by adjacent hold");
  snapshot_hold=0;step;
  if(summary_body[95:0]!=0 || summary_body[119:96]!=0)$fatal(1,"window reset/manual switch incorrectly captured");
  taking_off=0;event_sequence=4;event_code=8'h22;step;
  if(summary_body[95:0]!=0)$fatal(1,"unarmed event captured");
  event_sequence=16'hffff;event_code=0;step;
  event_sequence=0;event_code=8'h31;event_time_ms=333;step;
  if(summary_body[95:64]!=0 || summary_body[63:56]!=8'h31)$fatal(1,"event sequence wrap");
  taking_off=1;event_sequence=1;event_code=8'h32;event_time_ms=444;step;
  if(summary_body[95:64]!=0 || summary_body[63:56]!=8'h32)$fatal(1,"same-edge new window event");
  taking_off=0;step;taking_off=1;step;
  if(summary_body[95:0]!=0)$fatal(1,"stale event reused");
  // A gap crossing tick wrap must retain its prior maximum.
  clock_ticks=32'hffffffff;step;held=summary_body;clock_ticks=0;step;
  if(summary_body[287:256]<held[287:256])$fatal(1,"max decreased at tick wrap");
  rst_n=0;step;if(summary_body!=0)$fatal(1,"reset");
  $display("PASS sik_summary v2 zero slots, same-cycle tuple, hold, ongoing gap, first diagnostic/protection, window, event wrap");$finish;
 end
 initial begin #100000;$fatal(1,"timeout");end
endmodule
