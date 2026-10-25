`timescale 1ns/1ps
module uart_load_tb;
 reg clk=0;always #10 clk=~clk;
 reg rst_n=0,raw_valid=0,pose_valid=0,fault_valid=0;
 reg [207:0] raw_body=0;reg [223:0] pose_body=0;
 reg [31:0] tick=0;wire tx;
 diagnostic_uart dut(.clk(clk),.rst_n(rst_n),
  .raw_valid(raw_valid),.raw_body(raw_body),.raw_tick(tick),
  .pose_valid(pose_valid),.pose_body(pose_body),.pose_tick(tick),
  .fault_valid(fault_valid),.fault_body(704'd0),.fault_tick(tick),
  .clock_ticks(tick),.max_accept_gap(32'd50000),.raw_count(32'd20),.pose_count(32'd20),
  .uptime_ms(64'd20),.build_id(32'hb0b1),.tx(tx));
 always @(posedge clk)if(rst_n)tick<=tick+1'b1;
 integer raw_frames=0,pose_frames=0,fault_frames=0,n;
 always @(posedge clk)if(rst_n && dut.frame_done)case(dut.frame_type)
  1:raw_frames=raw_frames+1;2:pose_frames=pose_frames+1;3:fault_frames=fault_frames+1;
 endcase
 initial begin
  repeat(5)@(negedge clk);rst_n=1;
  for(n=1;n<=20;n=n+1)begin
   // Exact one-millisecond cadence at 50 MHz, with simultaneous producers.
   @(negedge clk);raw_valid=1;pose_valid=1;
   raw_body={n[31:0],16'd0,16'd0,16'd2048,16'd0,16'd0,16'd0,n[31:0],8'd0,8'd0,8'h7f,8'd0,8'd5,8'd0};
   pose_body={n[31:0],32'd50000,32'd0,32'd0,32'd0,16'd0,16'd0,16'd0,8'h1f,8'd0};
   if(n==10)fault_valid=1;
   @(negedge clk);raw_valid=0;pose_valid=0;
   repeat(49998)@(negedge clk);
  end
  repeat(300000)@(negedge clk);
  if(raw_frames!=20 || pose_frames!=20 || fault_frames!=1 || dut.available!==0 || dut.state!==0)
   $fatal(1,"Nominal 1kHz+1kHz load did not drain with all frames retained");
  if(dut.dropped_raw!==0 || dut.dropped_pose!==0 || dut.dropped_status!==0 || dut.dropped_fault!==0)
   $fatal(1,"Nominal load plus fault caused producer drops");
  $display("UART_LOAD_PASS 20 raw + 20 pose at simultaneous 1kHz, one 100-byte fault, no drops");$finish;
 end
 initial begin #30000000;$fatal(1,"UART load test timeout");end
endmodule
