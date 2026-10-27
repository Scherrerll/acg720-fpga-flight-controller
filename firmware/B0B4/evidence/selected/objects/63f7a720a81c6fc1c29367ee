`timescale 1ns/1ps
module tb;
reg clk=0;always #10 clk=~clk;
reg rst_n=1,cancel=0,start=0,av=0;
reg [31:0] ticks=0;reg signed [31:0] ax=0,ay=0,az=0;
wire [1:0] up,valid,busy;wire [31:0] dt[0:1];wire signed [31:0] x[0:1],y[0:1],z[0:1];wire [7:0] fault[0:1];wire z_ok;
pose_time_adapter_v7 a(.clk(clk),.rst_n(rst_n),.cancel(cancel),.start(start),.acc_valid(av),.ticks(ticks),.ax(ax),.ay(ay),.az(az),.update(up[0]),.dt_us(dt[0]),.output_ax(x[0]),.output_ay(y[0]),.output_az(z[0]),.output_acc_valid(valid[0]),.busy(busy[0]),.fault(fault[0]));
pose_time_adapter b(.clk(clk),.rst_n(rst_n),.cancel(cancel),.start(start),.acc_valid(av),.ticks(ticks),.ax(ax),.ay(ay),.az(az),.update(up[1]),.dt_us(dt[1]),.output_ax(x[1]),.output_ay(y[1]),.output_az(z[1]),.output_az_range_ok(z_ok),.output_acc_valid(valid[1]),.busy(busy[1]),.fault(fault[1]));
integer cycles=0,publications=0,faultcycles=0,invalidpub=0,unknownpub=0,cancels=0,checks=0;
always @(posedge clk)begin
 cycles=cycles+1;#1;
 if({up[0],dt[0],x[0],y[0],z[0],valid[0],busy[0],fault[0]}!=={up[1],dt[1],x[1],y[1],z[1],valid[1],busy[1],fault[1]})$fatal(1,"adapter output mismatch at cycle%0d",cycles);
 if(z_ok !== (z[1]>=-30000 && z[1]<=30000))$fatal(1,"same tuple numeric predicate mismatch at cycle%0d z=%h flag=%b",cycles,z[1],z_ok);
 checks=checks+1;
 if(up[0])begin
  publications=publications+1;
  if(z_ok===0)invalidpub=invalidpub+1;
  if(z_ok===1'bx)unknownpub=unknownpub+1;
 end
 if(fault[0]!=0)faultcycles=faultcycles+1;
 if(cancel)cancels=cancels+1;
end
function [31:0] sample;
 input integer n;
 begin case(n%16)
  0:sample=0;1:sample=30000;2:sample=-30000;3:sample=30001;4:sample=-30001;
  5:sample=32'h7fffffff;6:sample=32'h80000000;7:sample=32'hffffffff;
  8:sample=32'h0000xxxx;9:sample=32'hzzzzzzzz;10:sample=32'h0000000x;
  default:sample=$random;
 endcase end
endfunction
integer n,j;
initial begin
 repeat(3)@(negedge clk);
 for(n=0;n<12000;n=n+1)begin
  rst_n=1;cancel=1;start=0;@(negedge clk);cancel=0;
  ticks=$random;ax=$random;ay=$random;az=sample(n);av=n%2;start=1;@(negedge clk);start=0;
  for(j=0;j<35;j=j+1)begin
   // Vary unlatched source data while busy. Only the accepted tuple may publish.
   ax=$random;ay=$random;az=$random;ticks=$random;av=~av;
   if(n%31==0 && j==8)cancel=1;
   if(n%31==0 && j==9)cancel=0;
   if(n%37==0 && j==12)start=1;
   if(n%37==0 && j==13)start=0;
   if(n%41==0 && j==20)rst_n=0;
   if(n%41==0 && j==21)rst_n=1;
   @(negedge clk);
  end
 end
 if(publications<10000 || faultcycles<100 || invalidpub<100 || unknownpub<100 || cancels<12000)$fatal(1,"insufficient adapter coverage");
 $display("PASS adapter cycles=%0d publications=%0d invalidpub=%0d unknownpub=%0d faultcycles=%0d cancelcycles=%0d same_tuple_checks=%0d",cycles,publications,invalidpub,unknownpub,faultcycles,cancels,checks);$finish;
end
endmodule
