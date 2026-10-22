
`timescale 1ns/1ps
module tb;
reg clk=0;always #5 clk=~clk;
reg rst_n=0,armed=0;reg [15:0]ch3=1000,collective=1350;
wire prep,takeoff,flying,land;wire[3:0]mask;
ano_flight_state #(.TICKS_PER_MS(20)) dut(.clk(clk),.rst_n(rst_n),.armed(armed),.ch3(ch3),.collective_us(collective),.motor_prepared(prep),.taking_off(takeoff),.flying(flying),.land_lock(land),.preparation_mask(mask));
integer f,g,k,rv,a,c1,c2,c3,fl;real h,v,acc,t;
initial begin
 f=$fopen("state_inputs.txt","r");g=$fopen("state_rtl.txt","w");
 repeat(2)@(negedge clk);rst_n=1;
 while(!$feof(f))begin
  rv=$fscanf(f,"%d %d %d %d %d %f %f %f %f\n",a,c1,c2,c3,fl,h,v,acc,t);
  if(rv==9)begin
   armed=a;ch3=c3;collective=1000+$rtoi(t);
   repeat(20)@(negedge clk);
   $fwrite(g,"%d %d %d %d %d\n",prep,takeoff,flying,land,mask);
  end
 end
 $fclose(g);$display("state trace completed");$finish;
end
endmodule
