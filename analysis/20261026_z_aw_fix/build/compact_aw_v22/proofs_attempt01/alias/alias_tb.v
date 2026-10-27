`timescale 1ns/1ps
module tb;
reg signed [28:0] v=0;reg signed [31:0] next_auto_speed=0;reg taking_off=0;
wire signed [31:0] oq,nq,oa,na;
old_actual old(v,next_auto_speed,taking_off,oq,oa);new_actual newx(v,next_auto_speed,taking_off,nq,na);
integer i,j,k,n=0,two=0,four=0;reg signed [63:0] reference;reg [31:0] random_word;
task check;input integer known;begin
 #1;n=n+1;
 if(oq!==nq || oa!==na)$fatal(1,"actual function/alias mismatch v=%h next=%h taking=%b q=%h/%h alt=%h/%h",v,next_auto_speed,taking_off,oq,nq,oa,na);
 if(known)begin
  reference=$signed(v);reference=reference/64'sd65536;reference=reference/64'sd10;reference=reference*64'sd655360;
  if(oq!==reference[31:0])$fatal(1,"independent signed64 reference mismatch v=%h got=%h ref=%h",v,oq,reference);
  two=two+1;
 end else four=four+1;
end endtask
initial begin
 // Every upper13 bit pattern, both equivalence classes of lower16 |reduction,
 // plus multiple concrete nonzero patterns, including every signed boundary.
 for(i=0;i<8192;i=i+1)for(j=0;j<4;j=j+1)begin
  v={i[12:0],16'd0};
  case(j)1:v[15:0]=1;2:v[15:0]=16'h8000;3:v[15:0]=16'hffff;endcase
  next_auto_speed=i-4096;taking_off=j[0];check(1);
 end
 // X/Z at every bit; fractional low bits cover known-one dominance and unknown OR.
 for(i=0;i<29;i=i+1)for(j=0;j<4;j=j+1)begin
  v=j[1]?29'h1fffffff:0;v[i]=j[0]?1'bz:1'bx;
  next_auto_speed=32'sd0;taking_off=1;check(0);
  taking_off=1'bx;check(0);taking_off=1'bz;check(0);
 end
 for(i=0;i<10000;i=i+1)begin
  v=$random;next_auto_speed=$random;taking_off=i[0];check(1);
  for(k=0;k<29;k=k+1)begin random_word=$random;v[k]=random_word[1:0]==0?1'b0:random_word[1:0]==1?1'b1:random_word[1:0]==2?1'bx:1'bz;end
  for(k=0;k<32;k=k+1)begin random_word=$random;next_auto_speed[k]=random_word[1:0]==0?1'b0:random_word[1:0]==1?1'b1:random_word[1:0]==2?1'bx:1'bz;end
  taking_off=i%4==0?1'b0:i%4==1?1'b1:i%4==2?1'bx:1'bz;check(0);
 end
 $display("PASS actual_alias vectors=%0d signed64=%0d fourstate=%0d all_upper13=8192 low16_reduction_classes=2 function_byte_identical=1",n,two,four);$finish;
end
endmodule
