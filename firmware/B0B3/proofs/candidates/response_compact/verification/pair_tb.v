`timescale 1ns/1ps
module tb;
reg clk=0,rst_n=0,rx_valid=0,rx_error=0,write_safe=1,boundary=1,ready=0;reg[7:0]data=0;
wire[15:0]p,i;wire[31:0]gen;wire valid;wire[191:0]resp;
always #10 clk=~clk;
xy_pi_parameters #(.TIMEOUT_TICKS(100))dut(clk,rst_n,rx_valid,rx_error,data,write_safe,boundary,p,i,gen,valid,resp,ready);
wire[15:0]oldp,oldi;wire[31:0]oldgen;wire oldvalid;wire[191:0]oldresp;
xy_pi_parameters_before #(.TIMEOUT_TICKS(100))previous(clk,rst_n,rx_valid,rx_error,data,write_safe,boundary,oldp,oldi,oldgen,oldvalid,oldresp,ready);
integer cycle_checks=0,valid_word_checks=0,crc_body_checks=0;
always @(posedge clk)begin #1;
 cycle_checks=cycle_checks+1;
 if({p,i,gen,valid}!=={oldp,oldi,oldgen,oldvalid})$fatal(1,"cycle mismatch gains/gen/valid p=%0d/%0d i=%0d/%0d gen=%0d/%0d valid=%b/%b",p,oldp,i,oldi,gen,oldgen,valid,oldvalid);
 if(valid)begin
  valid_word_checks=valid_word_checks+1;
  if(resp!==oldresp)$fatal(1,"valid full response differs candidate=%048h old=%048h",resp,oldresp);
 end
 if(dut.state==4 || dut.state==5)begin
  crc_body_checks=crc_body_checks+1;
  if(resp[175:16]!==oldresp[175:16])$fatal(1,"CRC input body differs");
  if(dut.state==4 && (dut.crc_index<2 || dut.crc_index>21))$fatal(1,"CRC consumed its own tail/header");
 end
end

task put;input[7:0]b;begin @(negedge clk);data=b;rx_valid=1;@(negedge clk);rx_valid=0;repeat(2)@(negedge clk);end endtask
task send_frame;input[127:0]f;integer k;begin for(k=15;k>=0;k=k-1)put(f[k*8+:8]);end endtask
task check;input integer status,ep,ei,eg;begin
 wait(valid);#1;
 if(resp[151:144]!=status || p!=ep || i!=ei || gen!=eg)$fatal(1,"response status=%0d expected=%0d p=%0d i=%0d gen=%0d",resp[151:144],status,p,i,gen);
 $display("RESPONSE %048h",resp);
 repeat(4)@(negedge clk);if(!valid)$fatal(1,"response not held under backpressure");
 ready=1;@(negedge clk);ready=0;repeat(3)@(negedge clk);
end endtask
initial begin repeat(5)@(negedge clk);rst_n=1;
send_frame(128'ha5900101100000000001000000006102);check(0,500,0,0);
send_frame(128'ha590010210000000000a05dc03e870c2);check(0,1500,1000,1);
send_frame(128'ha590010210000000000a05dc03e870c2);check(5,1500,1000,1);
send_frame(128'ha590010210000000000a03e700004b7a);check(5,1500,1000,1);
send_frame(128'ha590010210000000000901f4000052f3);check(5,1500,1000,1);
write_safe=0;
send_frame(128'ha590010210000000000b025800004551);check(4,1500,1000,1);
write_safe=1;
send_frame(128'ha590010210000000000b025800004551);check(5,1500,1000,1);
send_frame(128'ha590010210000000000c271100002ab2);check(3,1500,1000,1);
send_frame(128'ha590010210000000000d01f40000dbf5 ^ 128'd1);check(2,1500,1000,1);
send_frame(128'ha590010210000000000d01f40000dbf5);check(0,500,0,2);
send_frame(128'ha590020210000000000e02bc03206e59);check(1,500,0,2);
send_frame(128'ha590010810000000000e02bc032069fb);check(6,500,0,2);
send_frame(128'ha590010210010000000e02bc032080e5);check(1,500,0,2);
send_frame(128'ha590010211000000000e02bc03200483);check(1,500,0,2);
send_frame(128'ha590010110000000000e0001000033cb);check(1,500,0,2);
boundary=0;send_frame(128'ha590010210000000000e02bc03206bc6);wait(dut.state==2);@(negedge clk);write_safe=0;check(4,500,0,2);write_safe=1;boundary=1;
boundary=0;send_frame(128'ha590010210000000000f02bc0320c197);wait(dut.state==2);repeat(40)@(negedge clk);if(p!=500 || i!=0 || gen!=2)$fatal(1,"early commit");boundary=1;check(0,700,800,3);
put(8'h00);put(8'ha5);put(8'ha5);put(8'h90);put(1);repeat(110)@(negedge clk);
send_frame(128'ha590010110000000005800000000dc4c);check(0,700,800,3);
put(8'ha5);put(8'h90);put(1);rx_error=1;@(negedge clk);rx_error=0;
send_frame(128'ha590010110000000005900000000761d);check(0,700,800,3);
rst_n=0;repeat(3)@(negedge clk);rst_n=1;
send_frame(128'ha590010110000000005a0000000098cf);check(0,500,0,0);
send_frame(128'ha59001021000000000010000271094b8);check(0,0,10000,1);
send_frame(128'ha590010210000000000227100000d22a);check(0,10000,0,2);
send_frame(128'ha590010210000000000300002711c01a);check(3,10000,0,2);
send_frame(128'ha590010210000000000405dc03e8bf6a ^ (128'd1<<16));check(2,10000,0,2);
send_frame(128'ha590010210000000000405dc03e8bf6a ^ (128'd1<<17));check(2,10000,0,2);
send_frame(128'ha590010210000000000405dc03e8bf6a ^ (128'd1<<18));check(2,10000,0,2);
send_frame(128'ha590010210000000000405dc03e8bf6a ^ (128'd1<<19));check(2,10000,0,2);
send_frame(128'ha590010210000000000405dc03e8bf6a ^ (128'd1<<20));check(2,10000,0,2);
send_frame(128'ha590010210000000000405dc03e8bf6a ^ (128'd1<<21));check(2,10000,0,2);
send_frame(128'ha590010210000000000405dc03e8bf6a ^ (128'd1<<22));check(2,10000,0,2);
send_frame(128'ha590010210000000000405dc03e8bf6a ^ (128'd1<<23));check(2,10000,0,2);
send_frame(128'ha590010210000000000405dc03e8bf6a ^ (128'd1<<24));check(2,10000,0,2);
send_frame(128'ha590010210000000000405dc03e8bf6a ^ (128'd1<<25));check(2,10000,0,2);
send_frame(128'ha590010210000000000405dc03e8bf6a ^ (128'd1<<26));check(2,10000,0,2);
send_frame(128'ha590010210000000000405dc03e8bf6a ^ (128'd1<<27));check(2,10000,0,2);
send_frame(128'ha590010210000000000405dc03e8bf6a ^ (128'd1<<28));check(2,10000,0,2);
send_frame(128'ha590010210000000000405dc03e8bf6a ^ (128'd1<<29));check(2,10000,0,2);
send_frame(128'ha590010210000000000405dc03e8bf6a ^ (128'd1<<30));check(2,10000,0,2);
send_frame(128'ha590010210000000000405dc03e8bf6a ^ (128'd1<<31));check(2,10000,0,2);
send_frame(128'ha590010210000000000405dc03e8bf6a ^ (128'd1<<32));check(2,10000,0,2);
send_frame(128'ha590010210000000000405dc03e8bf6a ^ (128'd1<<33));check(2,10000,0,2);
send_frame(128'ha590010210000000000405dc03e8bf6a ^ (128'd1<<34));check(2,10000,0,2);
send_frame(128'ha590010210000000000405dc03e8bf6a ^ (128'd1<<35));check(2,10000,0,2);
send_frame(128'ha590010210000000000405dc03e8bf6a ^ (128'd1<<36));check(2,10000,0,2);
send_frame(128'ha590010210000000000405dc03e8bf6a ^ (128'd1<<37));check(2,10000,0,2);
send_frame(128'ha590010210000000000405dc03e8bf6a ^ (128'd1<<38));check(2,10000,0,2);
send_frame(128'ha590010210000000000405dc03e8bf6a ^ (128'd1<<39));check(2,10000,0,2);
send_frame(128'ha590010210000000000405dc03e8bf6a ^ (128'd1<<40));check(2,10000,0,2);
send_frame(128'ha590010210000000000405dc03e8bf6a ^ (128'd1<<41));check(2,10000,0,2);
send_frame(128'ha590010210000000000405dc03e8bf6a ^ (128'd1<<42));check(2,10000,0,2);
send_frame(128'ha590010210000000000405dc03e8bf6a ^ (128'd1<<43));check(2,10000,0,2);
send_frame(128'ha590010210000000000405dc03e8bf6a ^ (128'd1<<44));check(2,10000,0,2);
send_frame(128'ha590010210000000000405dc03e8bf6a ^ (128'd1<<45));check(2,10000,0,2);
send_frame(128'ha590010210000000000405dc03e8bf6a ^ (128'd1<<46));check(2,10000,0,2);
send_frame(128'ha590010210000000000405dc03e8bf6a ^ (128'd1<<47));check(2,10000,0,2);
send_frame(128'ha590010210000000000405dc03e8bf6a ^ (128'd1<<48));check(2,10000,0,2);
send_frame(128'ha590010210000000000405dc03e8bf6a ^ (128'd1<<49));check(2,10000,0,2);
send_frame(128'ha590010210000000000405dc03e8bf6a ^ (128'd1<<50));check(2,10000,0,2);
send_frame(128'ha590010210000000000405dc03e8bf6a ^ (128'd1<<51));check(2,10000,0,2);
send_frame(128'ha590010210000000000405dc03e8bf6a ^ (128'd1<<52));check(2,10000,0,2);
send_frame(128'ha590010210000000000405dc03e8bf6a ^ (128'd1<<53));check(2,10000,0,2);
send_frame(128'ha590010210000000000405dc03e8bf6a ^ (128'd1<<54));check(2,10000,0,2);
send_frame(128'ha590010210000000000405dc03e8bf6a ^ (128'd1<<55));check(2,10000,0,2);
send_frame(128'ha590010210000000000405dc03e8bf6a ^ (128'd1<<56));check(2,10000,0,2);
send_frame(128'ha590010210000000000405dc03e8bf6a ^ (128'd1<<57));check(2,10000,0,2);
send_frame(128'ha590010210000000000405dc03e8bf6a ^ (128'd1<<58));check(2,10000,0,2);
send_frame(128'ha590010210000000000405dc03e8bf6a ^ (128'd1<<59));check(2,10000,0,2);
send_frame(128'ha590010210000000000405dc03e8bf6a ^ (128'd1<<60));check(2,10000,0,2);
send_frame(128'ha590010210000000000405dc03e8bf6a ^ (128'd1<<61));check(2,10000,0,2);
send_frame(128'ha590010210000000000405dc03e8bf6a ^ (128'd1<<62));check(2,10000,0,2);
send_frame(128'ha590010210000000000405dc03e8bf6a ^ (128'd1<<63));check(2,10000,0,2);
send_frame(128'ha590010210000000000405dc03e8bf6a ^ (128'd1<<64));check(2,10000,0,2);
send_frame(128'ha590010210000000000405dc03e8bf6a ^ (128'd1<<65));check(2,10000,0,2);
send_frame(128'ha590010210000000000405dc03e8bf6a ^ (128'd1<<66));check(2,10000,0,2);
send_frame(128'ha590010210000000000405dc03e8bf6a ^ (128'd1<<67));check(2,10000,0,2);
send_frame(128'ha590010210000000000405dc03e8bf6a ^ (128'd1<<68));check(2,10000,0,2);
send_frame(128'ha590010210000000000405dc03e8bf6a ^ (128'd1<<69));check(2,10000,0,2);
send_frame(128'ha590010210000000000405dc03e8bf6a ^ (128'd1<<70));check(2,10000,0,2);
send_frame(128'ha590010210000000000405dc03e8bf6a ^ (128'd1<<71));check(2,10000,0,2);
send_frame(128'ha590010210000000000405dc03e8bf6a ^ (128'd1<<72));check(2,10000,0,2);
send_frame(128'ha590010210000000000405dc03e8bf6a ^ (128'd1<<73));check(2,10000,0,2);
send_frame(128'ha590010210000000000405dc03e8bf6a ^ (128'd1<<74));check(2,10000,0,2);
send_frame(128'ha590010210000000000405dc03e8bf6a ^ (128'd1<<75));check(2,10000,0,2);
send_frame(128'ha590010210000000000405dc03e8bf6a ^ (128'd1<<76));check(2,10000,0,2);
send_frame(128'ha590010210000000000405dc03e8bf6a ^ (128'd1<<77));check(2,10000,0,2);
send_frame(128'ha590010210000000000405dc03e8bf6a ^ (128'd1<<78));check(2,10000,0,2);
send_frame(128'ha590010210000000000405dc03e8bf6a ^ (128'd1<<79));check(2,10000,0,2);
send_frame(128'ha590010210000000000405dc03e8bf6a ^ (128'd1<<80));check(2,10000,0,2);
send_frame(128'ha590010210000000000405dc03e8bf6a ^ (128'd1<<81));check(2,10000,0,2);
send_frame(128'ha590010210000000000405dc03e8bf6a ^ (128'd1<<82));check(2,10000,0,2);
send_frame(128'ha590010210000000000405dc03e8bf6a ^ (128'd1<<83));check(2,10000,0,2);
send_frame(128'ha590010210000000000405dc03e8bf6a ^ (128'd1<<84));check(2,10000,0,2);
send_frame(128'ha590010210000000000405dc03e8bf6a ^ (128'd1<<85));check(2,10000,0,2);
send_frame(128'ha590010210000000000405dc03e8bf6a ^ (128'd1<<86));check(2,10000,0,2);
send_frame(128'ha590010210000000000405dc03e8bf6a ^ (128'd1<<87));check(2,10000,0,2);
send_frame(128'ha590010210000000000405dc03e8bf6a ^ (128'd1<<88));check(2,10000,0,2);
send_frame(128'ha590010210000000000405dc03e8bf6a ^ (128'd1<<89));check(2,10000,0,2);
send_frame(128'ha590010210000000000405dc03e8bf6a ^ (128'd1<<90));check(2,10000,0,2);
send_frame(128'ha590010210000000000405dc03e8bf6a ^ (128'd1<<91));check(2,10000,0,2);
send_frame(128'ha590010210000000000405dc03e8bf6a ^ (128'd1<<92));check(2,10000,0,2);
send_frame(128'ha590010210000000000405dc03e8bf6a ^ (128'd1<<93));check(2,10000,0,2);
send_frame(128'ha590010210000000000405dc03e8bf6a ^ (128'd1<<94));check(2,10000,0,2);
send_frame(128'ha590010210000000000405dc03e8bf6a ^ (128'd1<<95));check(2,10000,0,2);
send_frame(128'ha590010210000000000405dc03e8bf6a ^ (128'd1<<96));check(2,10000,0,2);
send_frame(128'ha590010210000000000405dc03e8bf6a ^ (128'd1<<97));check(2,10000,0,2);
send_frame(128'ha590010210000000000405dc03e8bf6a ^ (128'd1<<98));check(2,10000,0,2);
send_frame(128'ha590010210000000000405dc03e8bf6a ^ (128'd1<<99));check(2,10000,0,2);
send_frame(128'ha590010210000000000405dc03e8bf6a ^ (128'd1<<100));check(2,10000,0,2);
send_frame(128'ha590010210000000000405dc03e8bf6a ^ (128'd1<<101));check(2,10000,0,2);
send_frame(128'ha590010210000000000405dc03e8bf6a ^ (128'd1<<102));check(2,10000,0,2);
send_frame(128'ha590010210000000000405dc03e8bf6a ^ (128'd1<<103));check(2,10000,0,2);
send_frame(128'ha590010210000000000405dc03e8bf6a ^ (128'd1<<104));check(2,10000,0,2);
send_frame(128'ha590010210000000000405dc03e8bf6a ^ (128'd1<<105));check(2,10000,0,2);
send_frame(128'ha590010210000000000405dc03e8bf6a ^ (128'd1<<106));check(2,10000,0,2);
send_frame(128'ha590010210000000000405dc03e8bf6a ^ (128'd1<<107));check(2,10000,0,2);
send_frame(128'ha590010210000000000405dc03e8bf6a ^ (128'd1<<108));check(2,10000,0,2);
send_frame(128'ha590010210000000000405dc03e8bf6a ^ (128'd1<<109));check(2,10000,0,2);
send_frame(128'ha590010210000000000405dc03e8bf6a ^ (128'd1<<110));check(2,10000,0,2);
send_frame(128'ha590010210000000000405dc03e8bf6a ^ (128'd1<<111));check(2,10000,0,2);
put(8'ha5);put(8'h90);put(1);put(2);put(16);repeat(110)@(negedge clk);
send_frame(128'ha59001011000000000c800000000fac6);check(0,10000,0,2);
put(8'h11);put(8'h22);put(8'h33);
send_frame(128'ha59001011000000000c9000000005097);check(0,10000,0,2);

// Reset during CRC: active write occurred, but no ACK escaped; defaults return.
send_frame(128'ha590010210000000012c04b00384c5c7);wait(dut.state==4);repeat(5)@(negedge clk);
rst_n=0;repeat(3)@(negedge clk);rst_n=1;
send_frame(128'ha590010110000000012d00000000a73d);check(0,500,0,0);
// Reset while valid is backpressured: old and new valid both withdraw.
send_frame(128'ha590010210000000012e038403e86426);wait(valid);repeat(35)@(negedge clk);
rst_n=0;repeat(3)@(negedge clk);rst_n=1;
send_frame(128'ha590010110000000012f00000000e3be);check(0,500,0,0);
// Reset abandons an uncommitted pair held at a blocked boundary.
boundary=0;send_frame(128'ha5900102100000000130032002bce7c8);wait(dut.state==2);repeat(10)@(negedge clk);
rst_n=0;repeat(3)@(negedge clk);rst_n=1;boundary=1;
send_frame(128'ha590010110000000013100000000284c);check(0,500,0,0);
// A complete premature request cannot overwrite the held response fields.
send_frame(128'ha59001021000000001321f4023289a5f);wait(valid);
send_frame(128'ha5900101100000000133000000006ccf);repeat(30)@(negedge clk);check(0,8000,9000,1);
send_frame(128'ha5900101100000000134000000000b1b);check(0,8000,9000,1);
$display("PAIR cycles=%0d valid_words=%0d CRC_body_cycles=%0d",cycle_checks,valid_word_checks,crc_body_checks);
$display("PASS protocol registers replay CRC range reset timeout lock race atomic-boundary backpressure");$finish;end
initial begin #10000000;$fatal(1,"timeout");end
endmodule
