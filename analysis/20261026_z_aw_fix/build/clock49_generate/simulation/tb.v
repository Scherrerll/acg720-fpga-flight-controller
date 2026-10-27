`timescale 1ns/1ps
module tb;
reg input50=0;
always #10 input50=~input50;
wire output49,locked;
clock49 dut(.clkin(input50),.mdclk(input50),.clkout0(output49),.lock(locked));
real start_ns,previous_ns,period_ns,elapsed_ns;
integer n;
initial begin
 wait(locked===1'b1);
 repeat(100) @(posedge output49);
 @(posedge output49);start_ns=$realtime;previous_ns=$realtime;
 for(n=0;n<49000;n=n+1)begin
  @(posedge output49);
  if(locked!==1'b1)$fatal(1,"generated PLL lost lock during measurement");
  period_ns=$realtime-previous_ns;previous_ns=$realtime;
  if(period_ns<20.390 || period_ns>20.430)$fatal(1,"unexpected49MHz model period=%0.6f",period_ns);
 end
 elapsed_ns=$realtime-start_ns;
 if(elapsed_ns<999980.0 || elapsed_ns>1000020.0)$fatal(1,"49000 periods must span1ms; elapsed=%0.6f",elapsed_ns);
 $display("PASS unmodified vendor PLLA+PLL_INIT model, natural50MHz input, lock held,49000 output periods elapsed_ns=%0.6f",elapsed_ns);
 $finish;
end
initial begin #10000000;$fatal(1,"PLL model did not lock/complete within10ms");end
endmodule
