`timescale 1ns/1ps
module uart_serial_tb;
 localparam BIT_TICKS=54,STATUS_PERIOD=200000;
 reg clk=0;always #10 clk=~clk;
 reg rst_n=0,raw_valid=0,pose_valid=0,fault_valid=0;
 reg [207:0] raw_body=0;reg [223:0] pose_body=0;reg [703:0] fault_body=0;
 reg [31:0] raw_tick=0,pose_tick=0,fault_tick=0,clock_ticks=32'hfffff000;
 wire tx;
 diagnostic_uart #(.STATUS_PERIOD_TICKS(STATUS_PERIOD)) dut(
  .clk(clk),.rst_n(rst_n),.raw_valid(raw_valid),.raw_body(raw_body),.raw_tick(raw_tick),
  .pose_valid(pose_valid),.pose_body(pose_body),.pose_tick(pose_tick),
  .fault_valid(fault_valid),.fault_body(fault_body),.fault_tick(fault_tick),
  .clock_ticks(clock_ticks),.max_accept_gap(32'h12345678),.raw_count(32'd1111),.pose_count(32'd999),
  .uptime_ms(64'h0123456789abcdef),.build_id(32'h0000b0b1),.tx(tx));
 always @(posedge clk)if(rst_n)clock_ticks<=clock_ticks+1'b1;
 integer output_file,status_file,received_bytes=0,bit_index;
 reg [7:0] received;
 reg [4095:0] hex_path,status_path;
 initial begin
  if(!$value$plusargs("HEX=%s",hex_path))hex_path="uart_interop.hex";
  if(!$value$plusargs("STATUS=%s",status_path))status_path="uart_status_ticks.hex";
  output_file=$fopen(hex_path,"w");status_file=$fopen(status_path,"w");
  if(!output_file || !status_file)$fatal(1,"Cannot open UART test outputs");
 end
 // Independent wire receiver, sampling actual tx at each bit's center.
 // This never observes byte_start/data or assumes packet arbitration order.
 initial forever begin
  @(negedge tx);
  repeat(BIT_TICKS/2)@(posedge clk);#1;
  if(tx!==0)$fatal(1,"UART start bit is not low");
  received=0;
  for(bit_index=0;bit_index<8;bit_index=bit_index+1)begin
   repeat(BIT_TICKS)@(posedge clk);#1;received[bit_index]=tx;
  end
  repeat(BIT_TICKS)@(posedge clk);#1;
  if(tx!==1)$fatal(1,"UART stop bit is not high");
  $fdisplay(output_file,"%02x",received);received_bytes=received_bytes+1;
 end
 always @(posedge clk)if(rst_n && dut.status_due && dut.ready[3])
  $fdisplay(status_file,"%08x",clock_ticks);
 task raw_pattern;input integer base;integer j;begin
  for(j=0;j<26;j=j+1)raw_body[207-j*8-:8]=(base+j)&255;
 end endtask
 task pose_pattern;input integer base;integer j;begin
  for(j=0;j<28;j=j+1)pose_body[223-j*8-:8]=(base+j)&255;
  pose_body[15:8]=pose_body[15:8]&8'h3f; // Reserved pose flags stay zero.
 end endtask
 task fault_pattern;input integer base;integer j;begin
  for(j=0;j<88;j=j+1)fault_body[703-j*8-:8]=(base+j)&255;
  fault_body[703-:8]=fault_body[703-:8]&8'h07;
  fault_body[695-:8]=fault_body[695-:8]%10;
  fault_body[703-48*8-:8]=fault_body[703-48*8-:8]&8'h03;
 end endtask
 initial begin
  repeat(5)@(negedge clk);rst_n=1;
  @(negedge clk);
  // Same-edge raw + pose + a held fault. Two slots retain A and B;
  // C/D/E arrive before any frame can finish and must drop as NEW items.
  raw_valid=1;pose_valid=1;fault_valid=1;
  raw_pattern('h10);pose_pattern('h80);fault_pattern(0);
  raw_tick=32'hfffffff0;pose_tick=32'h01020304;fault_tick=32'h11112222;
  @(negedge clk);raw_pattern('h50);pose_pattern('ha0);
  raw_tick=32'h00000010;pose_tick=32'h05060708;
  @(negedge clk);raw_pattern('hd0);pose_pattern('he0);fault_valid=0;
  @(negedge clk);raw_pattern('hd1);pose_pattern('he1);
  fault_valid=1;fault_pattern('h90);fault_tick=32'h33334444;
  @(negedge clk);raw_pattern('hd2);pose_pattern('he2);fault_valid=0;
  @(negedge clk);raw_valid=0;pose_valid=0;
  fault_valid=1;fault_pattern('h40);fault_tick=32'h55556666;
  // Fault queue is full; this third window must wait and be accepted once.
  repeat(20)@(negedge clk);
  if(dut.fault_enqueued!==0)$fatal(1,"Full fault queue incorrectly accepted third fault");
  if(dut.dropped_raw!==3 || dut.dropped_pose!==3 || dut.dropped_fault!==0)
   $fatal(1,"Wrong overflow/drop counts");
  wait(dut.fault_enqueued);
  // Keep fault asserted after enqueue to prove level deduplication.
  repeat(600000)@(negedge clk);
  if(dut.dropped_raw!==3 || dut.dropped_pose!==3 || dut.dropped_fault!==0 || dut.dropped_status!==0)
   $fatal(1,"Counters changed unexpectedly while draining");
  if(dut.available!==0 || dut.state!==0)$fatal(1,"Queues did not drain");
  $display("UART_SERIAL_PASS bytes=%0d drops_raw=%0d drops_pose=%0d",received_bytes,dut.dropped_raw,dut.dropped_pose);
  $fclose(output_file);$fclose(status_file);$finish;
 end
 initial begin #30000000;$fatal(1,"UART serial test timeout");end
endmodule
