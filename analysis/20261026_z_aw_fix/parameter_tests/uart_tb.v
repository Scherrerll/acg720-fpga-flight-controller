`timescale 1ns/1ps
module tb;
reg clk=0,rst_n=0,rx=1;wire valid,error;wire[7:0]data;
integer received=0,errors=0;
always #10 clk=~clk;
xy_pi_uart_rx dut(clk,rst_n,rx,valid,error,data);
always @(posedge clk)if(valid)begin
 if(data!==(received==0?8'ha5:8'h90))$fatal(1,"UART byte mismatch %h",data);
 received=received+1;
end else if(error)errors=errors+1;
task octet;input[7:0]b;input stop;integer k;begin
 @(negedge clk);rx=0;repeat(434)@(negedge clk);
 for(k=0;k<8;k=k+1)begin rx=b[k];repeat(434)@(negedge clk);end
 rx=stop;repeat(434)@(negedge clk);rx=1;repeat(20)@(negedge clk);
end endtask
initial begin repeat(5)@(negedge clk);rst_n=1;
 rx=0;repeat(30)@(negedge clk);rx=1;repeat(500)@(negedge clk);
 octet(8'ha5,1);octet(8'h90,1);octet(8'hff,0);repeat(500)@(negedge clk);
 if(received!=2 || errors!=1)$fatal(1,"UART count valid=%0d errors=%0d",received,errors);
 $display("PASS UART physical 434 clocks/bit 115200 false-start bad-stop");$finish;end
initial begin #1000000;$fatal(1,"UART timeout");end
endmodule
