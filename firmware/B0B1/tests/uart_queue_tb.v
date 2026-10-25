`timescale 1ns/1ps
module uart_queue_tb;
 reg clk=0;always #10 clk=~clk;
 reg rst_n=0,push=0,pop=0;reg [31:0] body=0,tick=0;
 reg [6:0] read_index=0;wire ready,available;wire [7:0] read_byte;wire [31:0] head_tick;
 diagnostic_packet_queue #(.PAYLOAD_BYTES(4)) q(
  .clk(clk),.rst_n(rst_n),.push(push),.body(body),.tick(tick),.pop(pop),
  .ready(ready),.available(available),.read_index(read_index),.read_byte(read_byte),.head_tick(head_tick));
 task offer;input [31:0] value,timestamp;begin
  @(negedge clk);push=1;body=value;tick=timestamp;
  @(negedge clk);push=0;
 end endtask
 task expect_head;input [31:0] value,timestamp;integer j;begin
  if(!available || head_tick!==timestamp)$fatal(1,"Queue head tick/order mismatch");
  for(j=0;j<4;j=j+1)begin
   read_index=j;#1;if(read_byte!==value[31-j*8-:8])$fatal(1,"Queue byte mismatch");
  end
 end endtask
 initial begin
  repeat(3)@(negedge clk);rst_n=1;
  offer(32'h12345678,32'hfffffff0);offer(32'h90abcdef,32'h00000010);
  if(ready!==0)$fatal(1,"Queue should be full");
  expect_head(32'h12345678,32'hfffffff0);
  offer(32'hdeadbeef,32'h33333333); // dropped newest; A/B must survive.
  expect_head(32'h12345678,32'hfffffff0);
  // A full queue can replace its just-consumed slot on the same edge.
  @(negedge clk);pop=1;push=1;body=32'h01020304;tick=32'h44444444;
  #1;if(!ready)$fatal(1,"Pop must make room for simultaneous push");
  @(negedge clk);pop=0;push=0;
  expect_head(32'h90abcdef,32'h00000010);
  @(negedge clk);pop=1;@(negedge clk);pop=0;
  expect_head(32'h01020304,32'h44444444);
  @(negedge clk);pop=1;@(negedge clk);pop=0;
  if(available || !ready)$fatal(1,"Queue should be empty");
  $display("UART_QUEUE_PASS");$finish;
 end
 initial begin #100000;$fatal(1,"Queue test timeout");end
endmodule
