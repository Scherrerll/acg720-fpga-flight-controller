`timescale 1ns/1ps
module tb;
reg c50=0,c49=0;always #10 c50=~c50;always #10.204081632653 c49=~c49;
reg rst_n=0,s50=0,s49=0,host=1;
reg [7:0] d50=0,d49=0,host_expected=0;
reg host_good=0;
wire txold,txnew,tx49,bo,bn,b49,lv,le,hv,he;
wire [7:0] ld,hd;
old_uart_tx_115200 old50(.clk(c50),.start(s50),.data(d50),.tx(txold),.busy(bo));
uart_tx_115200 new50(.clk(c50),.start(s50),.data(d50),.tx(txnew),.busy(bn));
uart_tx_115200 #(.BIT_TICKS(425)) new49(.clk(c49),.start(s49),.data(d49),.tx(tx49),.busy(b49));
xy_pi_uart_rx #(.BIT_TICKS(425)) loop_rx(.clk(c49),.rst_n(rst_n),.rx(tx49),.valid(lv),.error(le),.data(ld));
xy_pi_uart_rx #(.BIT_TICKS(425)) host_rx(.clk(c49),.rst_n(rst_n),.rx(host),.valid(hv),.error(he),.data(hd));
integer loop_count=0,host_count=0,host_errors=0,tx50_count=0,tx49_count=0,bit_widths=0;
reg edge_seen=0;real last_edge,delta;
always @(negedge c50)begin
 #0.001;
 if({old50.tx,old50.busy,old50.baud,old50.bit_index,old50.shift}!=={new50.tx,new50.busy,new50.baud,new50.bit_index,new50.shift})
  $fatal(1,"default50 actual UART TX cycle/state mismatch");
end
always @(posedge c49)begin
 #0.001;
 if(rst_n && lv)begin if(ld!==d49)$fatal(1,"49MHz loopback byte mismatch");loop_count=loop_count+1;end
 if(rst_n && le)$fatal(1,"49MHz loopback error");
 if(rst_n && hv)begin
  if(!host_good || hd!==host_expected)$fatal(1,"49MHz nominal-host RX accepted wrong/bad-stop byte");
  host_count=host_count+1;
 end
 if(rst_n && he)begin if(host_good)$fatal(1,"nominal-host good frame rejected");host_errors=host_errors+1;end
end
always @(tx49)begin
 #0.001;
 if(d49==8'h55 && b49)begin
  if(edge_seen)begin
   delta=$realtime-last_edge;
   if(delta<8650.0 || delta>8700.0)$fatal(1,"49MHz TX wrong physical bit width=%0.6f",delta);
   bit_widths=bit_widths+1;
  end
  last_edge=$realtime;edge_seen=1;
 end else edge_seen=0;
end
task nominal_host_frame;
 input [7:0] b;input good;integer k;
 begin
  host_expected=b;host_good=good;
  host=0;#8680.555555556;
  for(k=0;k<8;k=k+1)begin host=b[k];#8680.555555556;end
  host=good;#8680.555555556;
  host=1;#26041.666666667;
 end
endtask
integer a,b,c;
initial begin
 #200;rst_n=1;
 fork
  begin
   for(a=0;a<256;a=a+1)begin
    @(negedge c50);d50=a;s50=1;
    @(negedge c50);s50=0;
    wait(bo);wait(!bo);repeat(3)@(negedge c50);tx50_count=tx50_count+1;
   end
  end
  begin
   for(b=0;b<256;b=b+1)begin
    @(negedge c49);d49=b;s49=1;
    @(negedge c49);s49=0;
    wait(b49);wait(!b49);repeat(5)@(negedge c49);tx49_count=tx49_count+1;
   end
  end
  begin
   // A quarter-bit false start must disappear before center qualification.
   #500;host=0;#2000;host=1;#26000;
   for(c=0;c<256;c=c+1)begin
    if(c%16==0)nominal_host_frame(c^8'h5a,0);
    nominal_host_frame(c,1);
   end
  end
 join
 #100000;
 if(tx50_count!=256 || tx49_count!=256 || loop_count!=256 || host_count!=256 || host_errors!=16 || bit_widths<9)
  $fatal(1,"UART coverage incomplete tx50=%0d tx49=%0d loop=%0d host=%0d errors=%0d bitWidths=%0d",tx50_count,tx49_count,loop_count,host_count,host_errors,bit_widths);
 $display("PASS actual UART sources: default50 cycle/state equivalence256 bytes;49MHz Tx/Rx256 loopback bytes; nominal115200 external host256 good/16 bad-stop frames plus false start; physical TX bit widths checked=%0d",bit_widths);
 $finish;
end
initial begin #80000000;$fatal(1,"UART unit timeout");end
endmodule
