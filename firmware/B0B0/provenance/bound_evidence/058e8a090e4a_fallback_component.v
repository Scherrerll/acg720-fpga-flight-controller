`timescale 1ns/1ps
module tb;
reg clk=0;always #5 clk=~clk;
reg rst_n=0,healthy=1,armed=0,taking_off=0,height_available=1,automatic_valid=0;
reg[15:0]automatic_collective_us=1500,ch3=1500;
wire active,prior_valid;wire[15:0]collective;
height_loss_fallback #(.SLEW_TICKS(2)) dut(.clk(clk),.rst_n(rst_n),.healthy(healthy),
 .armed(armed),.taking_off(taking_off),.height_available(height_available),
 .automatic_valid(automatic_valid),.automatic_collective_us(automatic_collective_us),
 .ch3(ch3),.active(active),.prior_collective_valid(prior_valid),.collective_us(collective));
integer a,b,x,entry,y,anchor,expected,error,prior_target,checks=0,previous;
reg[15:0]anchors[0:6];reg[15:0]collectives[0:5];
task tick;input integer n;begin repeat(n)@(negedge clk);end endtask
task reset;begin rst_n=0;armed=0;taking_off=0;automatic_valid=0;healthy=1;height_available=1;tick(3);rst_n=1;tick(2);end endtask
always @(negedge clk)if(rst_n && active && (collective<1000 || collective>1850))$fatal(1,"Output bounds");
initial begin
anchors[0]=1000;anchors[1]=1001;anchors[2]=1150;anchors[3]=1500;anchors[4]=1555;anchors[5]=1999;anchors[6]=2000;
collectives[0]=1000;collectives[1]=1100;collectives[2]=1199;collectives[3]=1200;collectives[4]=1500;collectives[5]=1850;
reset();armed=1;height_available=0;tick(5);if(active)$fatal(1,"Preflight fallback forbidden");
height_available=1;automatic_valid=1;tick(5);height_available=0;tick(3);if(active)$fatal(1,"No fallback before takeoff");
for(a=0;a<7;a=a+1)for(b=0;b<6;b=b+1)begin
 reset();entry=anchors[a];y=collectives[b];ch3=entry;automatic_collective_us=y;
 armed=1;taking_off=1;automatic_valid=1;tick(3);
 if(!prior_valid)$fatal(1,"Good collective not retained");
 automatic_valid=0;height_available=0;#1;
 if(!active || collective!=y)$fatal(1,"First failure must be bumpless");
 tick(1);if(collective!=y)$fatal(1,"Latch edge changed collective");
 tick(60);height_available=1;tick(3);if(!active)$fatal(1,"Recovery must not auto reenter Z");
 anchor=entry<1001?1001:entry>1999?1999:entry;prior_target=1199;
 for(x=1000;x<=2000;x=x+1)begin
  ch3=x;tick(8);
  if(x==1000)expected=1200;
  else if(x==2000)expected=1850;
  else if(x<anchor)expected=y<1200 ?1200:y-((anchor-x)*(y-1200))/(anchor-1000);
  else expected=y+((x-anchor)*(1850-y))/(2000-anchor);
  if(expected<1200)expected=1200;
  error=$signed({1'b0,dut.target_q})-expected;if(error<0)error=-error;
  if(error>1)$fatal(1,"Curve mismatch entry=%0d y=%0d x=%0d got=%0d expected=%0d",entry,y,x,dut.target_q,expected);
  if(dut.target_q<prior_target)$fatal(1,"Non-monotone curve");
  prior_target=dut.target_q;checks=checks+1;
 end
 ch3=1000;tick(10);previous=collective;
 repeat(1400)begin tick(1);if(collective>previous || previous-collective>1)$fatal(1,"Slew limit");previous=collective;end
 if(collective!=1200)$fatal(1,"Bottom endpoint unreachable");
 ch3=2000;tick(1500);if(collective!=1850)$fatal(1,"Top endpoint unreachable");
 healthy=0;#1;if(active || collective!=1000)$fatal(1,"Hard stop must bypass slew");
 tick(1);healthy=1;height_available=0;tick(4);if(active)$fatal(1,"Fault recovery restarted fallback");
end
reset();armed=1;taking_off=1;automatic_valid=1;ch3=1500;automatic_collective_us=1700;tick(3);
height_available=0;automatic_valid=0;tick(70);armed=0;#1;
if(active || collective!=1000)$fatal(1,"Disarm stop must be immediate");
tick(1);armed=1;tick(10);if(active)$fatal(1,"Missing height cannot rearm fallback");
$display("PASS fallback component: %0d curve points; boundary, entry, recovery, stop, slew",checks);$finish;
end
endmodule
