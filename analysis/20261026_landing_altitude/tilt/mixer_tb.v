`timescale 1ns/1ps
module tb;
reg enabled=1;reg[15:0]t=1000;reg signed[15:0]r=0,p=0,y=0;
wire[15:0]a,b,c,d;wire sat;wire[2:0]pos,neg;
quad_mixer_feedback #(.MIN_US(1200),.MAX_US(2000))dut(.enabled(enabled),.throttle_us(t),.roll_us(r),.pitch_us(p),.yaw_us(y),.m1_us(a),.m2_us(b),.m3_us(c),.m4_us(d),.saturated(sat),.saturation_positive(pos),.saturation_negative(neg));
initial begin
t=1658;r=0;p=0;y=0;#10;
if(a!=1658 || b!=1658 || c!=1658 || d!=1658 || sat!=0)$fatal(1,"mixer case0 mismatch");
$display("PASS mixer case0: t=%0d r=%0d p=%0d y=%0d motors=%0d,%0d,%0d,%0d sat=%0d pos=%0d neg=%0d",t,r,p,y,a,b,c,d,sat,pos,neg);
t=1658;r=0;p=100;y=0;#10;
if(a!=1758 || b!=1758 || c!=1558 || d!=1558 || sat!=0)$fatal(1,"mixer case1 mismatch");
$display("PASS mixer case1: t=%0d r=%0d p=%0d y=%0d motors=%0d,%0d,%0d,%0d sat=%0d pos=%0d neg=%0d",t,r,p,y,a,b,c,d,sat,pos,neg);
t=1658;r=0;p=300;y=0;#10;
if(a!=1958 || b!=1958 || c!=1358 || d!=1358 || sat!=0)$fatal(1,"mixer case2 mismatch");
$display("PASS mixer case2: t=%0d r=%0d p=%0d y=%0d motors=%0d,%0d,%0d,%0d sat=%0d pos=%0d neg=%0d",t,r,p,y,a,b,c,d,sat,pos,neg);
t=1658;r=0;p=400;y=0;#10;
if(a!=2000 || b!=2000 || c!=1258 || d!=1258 || sat!=1)$fatal(1,"mixer case3 mismatch");
$display("PASS mixer case3: t=%0d r=%0d p=%0d y=%0d motors=%0d,%0d,%0d,%0d sat=%0d pos=%0d neg=%0d",t,r,p,y,a,b,c,d,sat,pos,neg);
t=1850;r=0;p=150;y=0;#10;
if(a!=2000 || b!=2000 || c!=1700 || d!=1700 || sat!=0)$fatal(1,"mixer case4 mismatch");
if(!pos[1] || sat)$fatal(1,"limit-touch must flag directional saturation before strict clip");
$display("PASS mixer case4: t=%0d r=%0d p=%0d y=%0d motors=%0d,%0d,%0d,%0d sat=%0d pos=%0d neg=%0d",t,r,p,y,a,b,c,d,sat,pos,neg);
t=1850;r=0;p=300;y=0;#10;
if(a!=2000 || b!=2000 || c!=1550 || d!=1550 || sat!=1)$fatal(1,"mixer case5 mismatch");
$display("PASS mixer case5: t=%0d r=%0d p=%0d y=%0d motors=%0d,%0d,%0d,%0d sat=%0d pos=%0d neg=%0d",t,r,p,y,a,b,c,d,sat,pos,neg);
t=1350;r=0;p=300;y=0;#10;
if(a!=1650 || b!=1650 || c!=1200 || d!=1200 || sat!=1)$fatal(1,"mixer case6 mismatch");
$display("PASS mixer case6: t=%0d r=%0d p=%0d y=%0d motors=%0d,%0d,%0d,%0d sat=%0d pos=%0d neg=%0d",t,r,p,y,a,b,c,d,sat,pos,neg);
t=1850;r=200;p=200;y=100;#10;
if(a!=2000 || b!=1950 || c!=1350 || d!=1950 || sat!=1)$fatal(1,"mixer case7 mismatch");
$display("PASS mixer case7: t=%0d r=%0d p=%0d y=%0d motors=%0d,%0d,%0d,%0d sat=%0d pos=%0d neg=%0d",t,r,p,y,a,b,c,d,sat,pos,neg);
enabled=0;#10;if({a,b,c,d}!={16'd1000,16'd1000,16'd1000,16'd1000} || sat || pos || neg)$fatal(1,"disabled outputs");
$display("PASS disabled mixer outputs1000, feedback0");$finish;end
endmodule
