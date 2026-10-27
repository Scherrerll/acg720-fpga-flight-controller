`timescale 1ns/1ps
module tb;
reg clk=0;always #10 clk=~clk;
reg rst_n=0,hold=0;reg [671:0] data=0;reg [15:0] flags=0;reg [7:0] live=0;
wire [719:0] a0,b0,a1,b1;
diag_v9 #(.STARTUP_ONLY_DIAGNOSTIC_RESET(0)) a(.clk(clk),.rst_n(rst_n),.diagnostic_hold(hold),.payload(data),.shadow_flags(flags),.live(live),.diagnostic_body(a0));
diag_v10 #(.STARTUP_ONLY_DIAGNOSTIC_RESET(0)) b(.clk(clk),.rst_n(rst_n),.diagnostic_hold(hold),.payload(data),.shadow_flags(flags),.live(live),.diagnostic_body(b0));
diag_v9 #(.STARTUP_ONLY_DIAGNOSTIC_RESET(1)) c(.clk(clk),.rst_n(rst_n),.diagnostic_hold(hold),.payload(data),.shadow_flags(flags),.live(live),.diagnostic_body(a1));
diag_v10 #(.STARTUP_ONLY_DIAGNOSTIC_RESET(1)) d(.clk(clk),.rst_n(rst_n),.diagnostic_hold(hold),.payload(data),.shadow_flags(flags),.live(live),.diagnostic_body(b1));
integer cycles=0,active=0,inactive=0,unknown=0,held=0,resets=0,n,j;
reg [719:0] previous0,previous1;
task compare;begin
 if(a0!==b0 || a1!==b1)$fatal(1,"diagnostic mismatch cycle%0d flag=%h hold=%b rst=%b",cycles,flags,hold,rst_n);
end endtask
always @(posedge clk)begin
 cycles=cycles+1;
 if(rst_n===1 && hold===0)begin
  if(flags[4]===1)active=active+1;else if(flags[4]===0)inactive=inactive+1;else unknown=unknown+1;
 end
 if(hold===1)held=held+1;if(rst_n===0)resets=resets+1;
 #1;compare;
end
initial begin
 #1;compare;
 for(n=0;n<160000;n=n+1)begin
  @(negedge clk);previous0=a0;previous1=a1;
  for(j=0;j<21;j=j+1)data[j*32+:32]=$random;
  live=$random;flags=$random;
  case(n%4)0:flags[4]=0;1:flags[4]=1;2:flags[4]=1'bx;3:flags[4]=1'bz;endcase
  case(n%13)0:flags[5]=1'bx;1:flags[5]=1'bz;endcase
  if(n%17==0)data[589:574]=16'hxxxx;
  if(n%23==0)data[605:590]=16'hzzzz;
  if(n%19==0)data[637:606]=32'hzzzzzzzz;
  rst_n=n%211<3 ?1'b0:1'b1;hold=n%7==0;
  if(n%97==0)hold=1'bx;
  if(n%101==0)rst_n=1'bx;
  #1;compare;
  if(a0!==previous0 || a1!==previous1)$fatal(1,"current input leaked through held snapshot");
 end
 @(negedge clk);
 if(active<10000 || inactive<10000 || unknown<20000 || held<10000 || resets<1000)$fatal(1,"coverage insufficient");
 $display("PASS diagnostic cycles=%0d public_bits_per_mode=720 modes=2 active=%0d inactive=%0d unknown=%0d held=%0d reset=%0d",cycles,active,inactive,unknown,held,resets);$finish;
end
endmodule
