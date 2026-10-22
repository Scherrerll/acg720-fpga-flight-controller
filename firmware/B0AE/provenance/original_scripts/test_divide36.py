from test_tools import *
import random
random.seed(210036)
cases=[]
for n in [-(1<<35),-(1<<32),-65536,-3,-1,0,1,3,65536,(1<<32),(1<<35)-1]:
 for d in [1,2,3,10,10000,65536,91756,101884,131071]:cases.append((n,d))
cases += [(dead*1441792,10000)for dead in range(-450,451)]
cases += [(random.randint(-(1<<34),(1<<34)-1),random.randint(1,131071))for _ in range(2000)]
for d in [2,10,10000,65536,101884]:
 for q in [0,1,17,500]:
  for sign in [-1,1]:cases.append((sign*(q*d+d//2),d))
def rounded(n,d):
 q,r=divmod(abs(n),d);q+=2*r>=d
 return -q if n<0 else q
(ROOT/'tests/divide36_inputs.txt').write_text('\n'.join(f'{n} {d} {rounded(n,d)}'for n,d in cases)+'\n')
bench=r'''
`timescale 1ns/1ps
module tb;
reg clk=0;always #10 clk=~clk;
reg rst_n=0,start=0,cancel=0;reg signed[35:0]n=0;reg[16:0]d=1;
wire b0,b1,q0done,q1done,e0,e1;wire signed[35:0]q1;wire signed[63:0]q0;
wire signed[17:0]residue;
ano_xy_divide36 compact(.clk(clk),.rst_n(rst_n),.start(start),.cancel(cancel),.numerator(n),.denominator(d),.busy(b1),.done(q1done),.error(e1),.quotient(q1),.residue(residue));
position_divide reference(.clk(clk),.rst_n(rst_n),.start(start),.cancel(cancel),.numerator({{28{n[35]}},n}),.denominator({15'd0,d}),.busy(b0),.done(q0done),.error(e0),.quotient(q0));
reg seen0=0,seen1=0;reg signed[63:0]out0=0,out1=0;
always @(negedge clk)begin
 if(q0done)begin seen0=1;out0=q0;end
 if(q1done)begin seen1=1;out1=q1;end
end
integer f,rv,count=0,k;reg signed[63:0]expected,expected_residue;
initial begin
 repeat(3)@(posedge clk);#1;rst_n=1;
 f=$fopen("divide36_inputs.txt","r");
 while(!$feof(f))begin
  rv=$fscanf(f,"%d %d %d\n",n,d,expected);
  if(rv==3)begin
   @(posedge clk);#1;seen0=0;seen1=0;start=1;
   @(posedge clk);#1;start=0;
   wait(seen0 && seen1);@(posedge clk);#1;
   if(out0!==expected || out1!==expected || e0 || e1)$fatal(1,"divider mismatch n=%d d=%d old=%d new=%d expected=%d",n,d,out0,out1,expected);
   expected_residue=$signed({{28{n[35]}},n})-expected*$signed({47'd0,d});
   if($signed(residue)!==expected_residue)$fatal(1,"rounded residue mismatch n=%d d=%d r=%d expected=%d",n,d,residue,expected_residue);
   count=count+1;
  end
 end
 // Every partial transaction must be discarded by cancellation.
 for(k=1;k<=40;k=k+1)begin
  @(posedge clk);#1;n=-36'sd4252041216;d=101884;start=1;
  @(posedge clk);#1;start=0;repeat(k)@(posedge clk);#1;cancel=1;
  @(posedge clk);#1;cancel=0;seen0=0;seen1=0;
  repeat(160)@(posedge clk);#1;
  if(b0 || b1 || seen0 || seen1)$fatal(1,"cancel leaked result");
 end
 $display("DIVIDE36_EQUIVALENCE_PASS %d cases plus40cancel phases; old64bit and independent integer rounding",count);$finish;
end
initial begin #1000000000;$fatal(1,"divider test timeout");end
endmodule
'''
(ROOT/'tests/divide36_equivalence.v').write_text(bench)
simulate('divide36_equivalence',[FIX/'position/ano_xy_divide36.v',FIX/'position/position_math.v'],ROOT/'tests/divide36_equivalence.v')
