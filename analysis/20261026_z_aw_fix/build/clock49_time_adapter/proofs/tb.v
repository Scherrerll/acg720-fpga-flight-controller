`timescale 1ns/1ps
module tb;
reg clk=0;always #10 clk=~clk;
reg rst_n=0,cancel=0,start=0,valid=0;
reg [31:0] ticks=0;
reg signed [31:0] ax=0,ay=0,az=0;
old_pose_time_adapter old50(.clk(clk),.rst_n(rst_n),.cancel(cancel),.start(start),.acc_valid(valid),.ticks(ticks),.ax(ax),.ay(ay),.az(az));
pose_time_adapter new50(.clk(clk),.rst_n(rst_n),.cancel(cancel),.start(start),.acc_valid(valid),.ticks(ticks),.ax(ax),.ay(ay),.az(az));
pose_time_adapter #(.CLOCK_HZ(49000000)) new49(.clk(clk),.rst_n(rst_n),.cancel(cancel),.start(start),.acc_valid(valid),.ticks(ticks),.ax(ax),.ay(ay),.az(az));
wire [138:0] original={old50.update,old50.dt_us,old50.output_ax,old50.output_ay,old50.output_az,old50.output_acc_valid,old50.busy,old50.fault};
wire [138:0] candidate50={new50.update,new50.dt_us,new50.output_ax,new50.output_ay,new50.output_az,new50.output_acc_valid,new50.busy,new50.fault};
integer cycle=0,n,normal=0,cancellations=0,collisions=0;
reg [31:0] seed=32'h72049;
reg [63:0] total,expected_dt;
integer fraction=0;
function [31:0] random32;
 input [31:0] a;reg [31:0] b;
 begin b=a^(a<<13);b=b^(b>>17);random32=b^(b<<5);end
endfunction
always @(negedge clk)begin
 #1;cycle=cycle+1;
 if(original!==candidate50)$fatal(1,"default50 full public output mismatch at cycle%0d",cycle);
 if(old50.tick_fraction!==new50.tick_fraction || old50.remainder!==new50.remainder || old50.index!==new50.index)
  $fatal(1,"default50 internal division state mismatch");
end
task reset_units;
 begin
  @(negedge clk);rst_n=0;cancel=0;start=0;
  repeat(2)@(negedge clk);rst_n=1;fraction=0;
 end
endtask
task transaction;
 input [31:0] value;input ok;
 begin
  @(negedge clk);ticks=value;valid=ok;start=1;
  seed=random32(seed);ax=seed;seed=random32(seed);ay=seed;seed=random32(seed);az=seed;
  if(ok)total={32'd0,value}+fraction;else total={32'd0,value};
  expected_dt=total/49;
  if(ok)fraction=total%49;else fraction=0;
  @(negedge clk);start=0;
  wait(new49.update===1'b1);#1;
  if(new49.dt_us!==expected_dt[31:0] || new49.tick_fraction!==fraction[5:0])
   $fatal(1,"49MHz divide/carry value%0d dt%0d expected%0d fraction%0d/%0d",value,new49.dt_us,expected_dt,new49.tick_fraction,fraction);
  if(new49.output_ax!==ax || new49.output_ay!==ay || new49.output_az!==az || new49.output_acc_valid!==ok || new49.busy || new49.fault)
   $fatal(1,"49MHz output tuple/valid/fault changed");
  normal=normal+1;
  @(negedge clk);
 end
endtask
task cancel_midflight;
 begin
  @(negedge clk);ticks=32'hffffffff;valid=1;start=1;
  @(negedge clk);start=0;repeat(6)@(negedge clk);cancel=1;start=1;
  @(negedge clk);cancel=0;start=0;fraction=0;#1;
  if(new49.busy || new49.update || new49.fault || new49.output_acc_valid || new49.tick_fraction!=0)
   $fatal(1,"49MHz simultaneous cancel/start priority changed");
  cancellations=cancellations+1;
 end
endtask
task collide_midflight;
 begin
  @(negedge clk);ticks=49;valid=1;start=1;
  @(negedge clk);start=0;repeat(2)@(negedge clk);start=1;
  @(negedge clk);start=0;fraction=0;#1;
  if(new49.busy || new49.fault!=1 || new49.output_acc_valid || new49.tick_fraction!=0)
   $fatal(1,"49MHz busy overrun behavior changed");
  collisions=collisions+1;reset_units;
 end
endtask
initial begin
 reset_units;
 for(n=0;n<12000;n=n+1)begin
  seed=random32(seed);
  case(n%16)
   0:transaction(0,1);1:transaction(48,1);2:transaction(49,1);3:transaction(50,1);
   4:transaction(97,1);5:transaction(98,1);6:transaction(99,1);7:transaction(32'hffffffff,1);
   8:transaction(49000,1);9:transaction(50000,1);10:transaction(32'hfffffffe,0);
   default:transaction(seed,n%7!=0);
  endcase
  if(n%211==0)cancel_midflight;
  if(n%257==0)collide_midflight;
  if(n%128==0)reset_units;
 end
 $display("PASS default50 actual-module equivalence public139+division state;49MHz full32bit carry transactions=%0d cancellations=%0d busy_overruns=%0d cycles=%0d",normal,cancellations,collisions,cycle);
 $finish;
end
initial begin #20000000;$fatal(1,"time-adapter unit test timeout");end
endmodule
