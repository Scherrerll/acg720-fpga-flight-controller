`timescale 1ns/1ps
module uart_fault_loss_tb;
 reg clk=0;always #10 clk=~clk;
 reg rst_n=0,fault_valid=0;reg [31:0] fault_tick=0;wire tx;
 diagnostic_uart #(.BIT_TICKS(2),.STATUS_PERIOD_TICKS(100000)) dut(
  .clk(clk),.rst_n(rst_n),.raw_valid(1'b0),.raw_body(208'd0),.raw_tick(32'd0),
  .pose_valid(1'b0),.pose_body(224'd0),.pose_tick(32'd0),
  .fault_valid(fault_valid),.fault_body(704'd0),.fault_tick(fault_tick),
  .clock_ticks(32'd0),.max_accept_gap(32'd0),.raw_count(32'd0),.pose_count(32'd0),
  .uptime_ms(64'd0),.build_id(32'hb0b1),.tx(tx));
 task offer;input [31:0] timestamp;begin
  @(negedge clk);fault_valid=1;fault_tick=timestamp;
  @(negedge clk);fault_valid=0;
  @(negedge clk);
 end endtask
 task cancel_pending;begin
  @(negedge clk);fault_valid=1;
  repeat(4)@(negedge clk);
  if(dut.fault_enqueued || !dut.fault_waiting_seen)$fatal(1,"Full fault queue did not retain pending offer");
  fault_valid=0;@(negedge clk);
 end endtask
 initial begin
  repeat(4)@(negedge clk);rst_n=1;
  offer(1);offer(2);
  if(dut.dropped_fault!==0 || dut.ready[2])$fatal(1,"Enqueued releases counted as loss / queue not full");
  @(negedge clk);fault_valid=1;fault_tick=3;
  repeat(12)@(negedge clk);
  if(dut.dropped_fault!==0 || !dut.fault_waiting_seen)$fatal(1,"Retry cycles counted as loss");
  fault_valid=0;@(negedge clk);
  if(dut.dropped_fault!==1)$fatal(1,"Unenqueued canceled window was not counted once");
  repeat(5)@(negedge clk);
  if(dut.dropped_fault!==1)$fatal(1,"Canceled window counted repeatedly");
  dut.dropped_fault=32'hfffffffe;
  cancel_pending();if(dut.dropped_fault!==32'hffffffff)$fatal(1,"Fault loss counter failed to reach saturation");
  cancel_pending();if(dut.dropped_fault!==32'hffffffff)$fatal(1,"Fault loss counter wrapped");
  @(negedge clk);fault_valid=1;repeat(3)@(negedge clk);rst_n=0;
  @(negedge clk);fault_valid=0;
  if(dut.dropped_fault!==0 || dut.fault_waiting_seen)$fatal(1,"Reset counted pending offer as a loss");
  rst_n=1;repeat(3)@(negedge clk);
  if(dut.dropped_fault!==0)$fatal(1,"Post-reset loss counter not clear");
  $display("UART_FAULT_LOSS_PASS pending cancel counted once; retries/enqueued release/reset do not count; saturation");$finish;
 end
 initial begin #1000000;$fatal(1,"Fault loss test timeout");end
endmodule
