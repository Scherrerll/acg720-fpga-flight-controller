`timescale 1ns/1ps
module uart_edge_tb;
 reg clk=0;always #10 clk=~clk;
 reg rst_n=0,offer=0,burst=0;wire tx,unused_tx;
 diagnostic_uart #(.BIT_TICKS(2),.STATUS_PERIOD_TICKS(100000)) dut(
  .clk(clk),.rst_n(rst_n),.raw_valid(offer),.raw_body(208'd0),.raw_tick(32'hffffffff),
  .pose_valid(offer),.pose_body(224'd0),.pose_tick(32'd0),
  .fault_valid(1'b0),.fault_body(704'd0),.fault_tick(32'd0),
  .clock_ticks(32'd0),.max_accept_gap(32'd0),.raw_count(32'd0),.pose_count(32'd0),
  .uptime_ms(64'd0),.build_id(32'hb0b1),.tx(tx));
 // The deliberately impossible status-offer rate exercises all drop counters
 // without waiting billions of cycles to reach saturation.
 diagnostic_uart #(.BIT_TICKS(2),.STATUS_PERIOD_TICKS(1)) crowded(
  .clk(clk),.rst_n(rst_n),.raw_valid(burst),.raw_body(208'd0),.raw_tick(32'd0),
  .pose_valid(burst),.pose_body(224'd0),.pose_tick(32'd0),
  .fault_valid(1'b0),.fault_body(704'd0),.fault_tick(32'd0),
  .clock_ticks(32'd0),.max_accept_gap(32'd0),.raw_count(32'd0),.pose_count(32'd0),
  .uptime_ms(64'd0),.build_id(32'hb0b1),.tx(unused_tx));
 reg [7:0] observed[0:255];integer count=0;
 always @(posedge clk)if(rst_n && dut.byte_start)begin observed[count]=dut.byte_data;count=count+1;end
 initial begin
  repeat(4)@(negedge clk);rst_n=1;burst=1;
  repeat(10)@(negedge clk);
  if(crowded.ready[0] || crowded.ready[1] || crowded.ready[3])$fatal(1,"Overflow test queues not full");
  crowded.dropped_raw=32'hfffffffe;crowded.dropped_pose=32'hfffffffe;crowded.dropped_status=32'hfffffffe;
  repeat(10)@(negedge clk);
  if(crowded.dropped_raw!==32'hffffffff || crowded.dropped_pose!==32'hffffffff ||
     crowded.dropped_status!==32'hffffffff || crowded.dropped_fault!==0)
   $fatal(1,"Drop counters failed to saturate");
  dut.transmit_sequence=16'hffff;
  offer=1;@(negedge clk);offer=0;
  wait(dut.transmit_sequence==1);@(negedge clk);
  if(count!=78 || observed[4]!==8'hff || observed[5]!==8'hff || observed[42]!==0 || observed[43]!==0)
   $fatal(1,"Transmit sequence did not wrap ffff -> 0000");
  offer=1;@(negedge clk);offer=0;repeat(80)@(negedge clk);
  rst_n=0;@(negedge clk);
  if(tx!==1 || dut.available!==0 || dut.transmit_sequence!==0 || dut.dropped_raw!==0)
   $fatal(1,"Reset did not abort frame/clear queues and counters");
  $display("UART_EDGE_PASS saturating counters, status overflow, sequence wrap, mid-frame reset");$finish;
 end
 initial begin #1000000;$fatal(1,"UART edge test timeout");end
endmodule
