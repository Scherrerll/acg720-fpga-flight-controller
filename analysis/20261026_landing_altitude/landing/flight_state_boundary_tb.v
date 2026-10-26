`timescale 1ns/1ps
// Only the public TICKS_PER_MS parameter is accelerated; 1 clock is one
// logical ms here. This proves threshold/timer state, not real elapsed time.
module tb;
 reg clk=0,rst_n=0,armed=1;reg[15:0]ch3=1600,collective=1850;
 wire prepared,taking_off,flying,land_lock;wire[3:0]mask;
 ano_flight_state #(.TICKS_PER_MS(1)) dut(.clk(clk),.rst_n(rst_n),.armed(armed),
  .ch3(ch3),.collective_us(collective),.motor_prepared(prepared),.taking_off(taking_off),
  .flying(flying),.land_lock(land_lock),.preparation_mask(mask));
 always #10 clk=~clk;
 task step;input integer n;integer k;begin for(k=0;k<n;k=k+1)begin @(posedge clk);#1;end end endtask
 initial begin
  step(4);@(negedge clk);rst_n=1;step(1300);
  if(!prepared || !taking_off)$fatal(1,"takeoff setup failed");
  @(negedge clk);ch3=1002;collective=1850;step(5000);
  if(land_lock || !taking_off || dut.landing_ms!=0)$fatal(1,"high collective must block landing timer");
  $display("PASS low-stick 5000 logical ms at collective1850 does not land; landing_ms=0");
  @(negedge clk);collective=1250;step(2000);
  if(land_lock || dut.landing_ms!=0)$fatal(1,"1250 threshold must be strict");
  @(negedge clk);collective=1249;step(1500);
  if(land_lock || dut.landing_ms!=1500)$fatal(1,"landing timer boundary");
  step(1);if(!land_lock || taking_off)$fatal(1,"expected land lock after 1501 consecutive qualified ms");
  $display("PASS collective1250 excluded;1249 triggers land_lock at1501 logical ms; post-mixer1200 floor is not consumed by this module");
  $finish;
 end
endmodule
