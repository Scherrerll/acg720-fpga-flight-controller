
`timescale 1ns/1ps
module tb;
reg clk=0;always #10 clk=~clk;
reg rst_n=0,a=0;reg[15:0]r=0,p=0,d=0,c=0;
wire[64:0]old_out,raw_out;wire[64:0]new_out={raw_out[64],raw_out[64]?raw_out[63:48]:16'd0,raw_out[64]?raw_out[47:32]:16'd0,raw_out[31:0]};
nav_control_handoff old_h(.clk(clk),.rst_n(rst_n),.command_in({a,a?r:16'd0,a?p:16'd0,d,c}),.command_out(old_out));
nav_control_handoff new_h(.clk(clk),.rst_n(rst_n),.command_in({a,r,p,d,c}),.command_out(raw_out));
integer i;
initial begin
 repeat(2)@(negedge clk);rst_n=1;
 for(i=0;i<50000;i=i+1)begin
  a=$random;r=$random;p=$random;d=$random;c=$random;rst_n=i%7001>2;
  @(negedge clk);#1;if(old_out!==new_out)$fatal(1,"handoff bit mismatch");
 end
 $display("HANDOFF_MASK_COMMUTATION_PASS50000cycles no latency or value change");$finish;
end
endmodule
