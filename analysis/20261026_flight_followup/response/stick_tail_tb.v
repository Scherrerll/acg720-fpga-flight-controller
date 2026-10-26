`timescale 1ns/1ps
module tb;
reg clk=0,rst_n=0,enabled=1,update_in=0;
reg [15:0]ch1=1500,ch2=1500;wire signed[17:0]nx,ny;wire busy,fault,update_out,valid;wire[15:0]out_dt;
always #10 clk=~clk;
ano_xy_stick dut(.clk(clk),.rst_n(rst_n),.enabled(enabled),.sample_update(update_in),
 .sample_dt_us(32'd1000),.ch1(ch1),.ch2(ch2),.nx(nx),.ny(ny),.busy(busy),.fault(fault),.update(update_out),.valid(valid),.output_dt_us(out_dt));
integer f,n,tail,initial_norm,one_percent=0,point_one_percent=0;
task sample;begin
 @(negedge clk);update_in=1;@(negedge clk);update_in=0;
 while(!update_out)begin @(posedge clk);#2;if(fault)$fatal(1,"stick fault");end
 if(!valid || out_dt!=1000)$fatal(1,"stick publication invalid");
 $fdisplay(f,"%0d,%0d,%0d,%0d,%0d",n,ch1,ch2,nx,ny);
end endtask
initial begin
 f=$fopen("C:/Users/ScherrerL/Desktop/apple/github_publish/acg720-fpga-flight-controller/analysis/20261026_flight_followup/response/stick_tail_trace.csv","w");$fdisplay(f,"semantic_ms,ch1,ch2,nx_q16,ny_q16");
 repeat(8)@(negedge clk);rst_n=1;ch1=2000;
 for(n=1;n<=400;n=n+1)sample;
 initial_norm=ny;if(ny<64800 || ny>64900)$fatal(1,"step did not settle");
 ch1=1500;
 for(n=401;n<=900;n=n+1)begin
  sample;tail=n-400;
  if(tail==1 && ny<=0)$fatal(1,"raw recenter incorrectly erases LPF");
  if(one_percent==0 && ny*100<=initial_norm)one_percent=tail;
  if(point_one_percent==0 && ny*1000<=initial_norm)point_one_percent=tail;
 end
 if(one_percent<240 || one_percent>255 || point_one_percent<360 || point_one_percent>380)$fatal(1,"unexpected LPF decay");
 $display("PASS actual stick: recenter tail 1pct=%0dms 0.1pct=%0dms residual500ms=%0dQ16",one_percent,point_one_percent,ny);
 ch1=1550;n=901;sample;if(dut.target_y!=0)$fatal(1,"1550 must be deadzone");
 ch1=1450;n=902;sample;if(dut.target_y!=0)$fatal(1,"1450 must be deadzone");
 ch1=1551;
 for(n=903;n<=1402;n=n+1)sample;
 if(dut.target_y!=144 || ny<143 || ny>145)$fatal(1,"small above-deadzone stick lost");
 $display("PASS actual stick: inclusive1450/1550 deadzone;1551 target144Q16 retained with LPF residue");
 $fclose(f);$finish;
end
initial begin #100000000;$fatal(1,"stick timeout");end
endmodule
