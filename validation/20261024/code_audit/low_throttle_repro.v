`timescale 1ns/1ps
module tb;
 reg clk=0;always #5 clk=~clk;
 reg rst_n=0,armed=0;reg[15:0]ch3=1000,collective=1800;
 wire prepared,takeoff,flying,land_lock;wire[3:0]mask;
 localparam T=10;
 ano_flight_state #(.TICKS_PER_MS(T)) dut(.clk(clk),.rst_n(rst_n),.armed(armed),.ch3(ch3),.collective_us(collective),.motor_prepared(prepared),.taking_off(takeoff),.flying(flying),.land_lock(land_lock),.preparation_mask(mask));
 integer elapsed_ticks=0,first_lock=-1;reg low_phase=0;
 always @(posedge clk)if(low_phase)begin elapsed_ticks=elapsed_ticks+1;if(land_lock && first_lock<0)first_lock=elapsed_ticks/T;end
 initial begin
  repeat(3)@(negedge clk);rst_n=1;armed=1;
  repeat(1250*T)@(negedge clk);if(!prepared)$fatal(1,"Preparation not complete");
  ch3=1600;repeat(20*T)@(negedge clk);if(!takeoff)$fatal(1,"Takeoff precondition absent");
  ch3=1000;collective=1200;low_phase=1;
  repeat(1900*T)@(negedge clk);
  if(first_lock<0)$fatal(1,"Reported lock mechanism did not reproduce");
  $display("REPRODUCED: low stick ch3=1000 / collective=1200 asserted land_lock after %0d ms while armed remained high; taking_off=%b",first_lock,takeoff);
  $finish;
 end
endmodule
