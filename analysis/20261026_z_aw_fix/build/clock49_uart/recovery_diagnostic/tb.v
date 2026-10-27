`timescale 1ns/1ps
module tb;
reg c50=0,c49=0;always #10 c50=~c50;always #10.204081632653 c49=~c49;
reg rst_n=0,line_in=1;
wire v50,e50,v49,e49;wire[7:0]d50,d49;
xy_pi_uart_rx #(.BIT_TICKS(434)) original50(.clk(c50),.rst_n(rst_n),.rx(line_in),.valid(v50),.error(e50),.data(d50));
xy_pi_uart_rx #(.BIT_TICKS(425)) configured49(.clk(c49),.rst_n(rst_n),.rx(line_in),.valid(v49),.error(e49),.data(d49));
always@(posedge c50)begin #0.001;if(v50||e50)$display("RX50 t_ns=%0.3f valid=%0d error=%0d data=%02h state=%0d",$realtime,v50,e50,d50,original50.state);end
always@(posedge c49)begin #0.001;if(v49||e49)$display("RX49 t_ns=%0.3f valid=%0d error=%0d data=%02h state=%0d",$realtime,v49,e49,d49,configured49.state);end
task send;
 input[7:0]b;input good;integer k;
 begin
  $display("HOST t_ns=%0.3f byte=%02h goodStop=%0d",$realtime,b,good);
  line_in=0;#8680.555555556;
  for(k=0;k<8;k=k+1)begin line_in=b[k];#8680.555555556;end
  line_in=good;#8680.555555556;line_in=1;
 end
endtask
initial begin
 #200;rst_n=1;#500;line_in=0;#2000;line_in=1;#26000;
 send(8'h5a,0);#26041.666666667;send(8'h00,1);#173611.111111;
 rst_n=0;#200;rst_n=1;#10000;
 $display("LONG_IDLE_CASE");send(8'h5a,0);#121527.7777778;send(8'h00,1);#173611.111111;
 $finish;
end
endmodule
