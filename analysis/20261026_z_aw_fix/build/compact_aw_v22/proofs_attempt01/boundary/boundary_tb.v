`timescale 1ns/1ps
module tb;
parameter F=0;
reg clk=0,rst_n=0,su=0,hu=0,pu=0;
reg[15:0]ch1=1500,ch2=1500,ch3=1600,pval=1000,ival=350;
reg signed[31:0]h=1000,vx=0,vy=0,vz=0,ax=0,ay=0,az=0;
reg signed[15:0]yaw=0;wire[221:0]a,b;
old_side #(.F(F)) old(clk,rst_n,su,hu,pu,ch1,ch2,ch3,pval,ival,h,vx,vy,vz,ax,ay,az,yaw,a);
new_side #(.F(F)) newx(clk,rst_n,su,hu,pu,ch1,ch2,ch3,pval,ival,h,vx,vy,vz,ax,ay,az,yaw,b);
always #10 clk=~clk;
integer cycles=0,grants=0,pubs=0,differences=0,invalid_checks=0,j,k;
reg forbid=0;reg[31:0]pub_before;
task clocks;input integer n;begin repeat(n)@(negedge clk);end endtask
task callback;input integer both;begin
 @(negedge clk);su=1;hu=1;pu=both;
 @(negedge clk);su=0;hu=0;pu=0;clocks(24000);
end endtask
always @(posedge clk)begin
 #2;
 if(rst_n)begin
  cycles=cycles+1;
  if(a!==b)$fatal(1,"control/safety/normalization ports differ cycle=%0d state=%0d/%0d",cycles,old.dut.state,newx.dut.state);
  if({old.mreq,old.mc,old.dreq,old.dc,old.mbusy,old.mdone,old.dbusy,old.ddone,old.derror}!==
     {newx.mreq,newx.mc,newx.dreq,newx.dc,newx.mbusy,newx.mdone,newx.dbusy,newx.ddone,newx.derror})
   $fatal(1,"math request/cancel/status differs");
  if(old.dut.state!==newx.dut.state || old.dut.iz!==newx.dut.iz || old.dut.bias!==newx.dut.bias ||
     old.dut.ix!==newx.dut.ix || old.dut.iy!==newx.dut.iy)$fatal(1,"persistent state differs");
  if(old.mg)begin
   grants=grants+1;
   if(forbid)$fatal(1,"invalid captured request was granted");
   if(old.mul.held_a!==newx.mul.held_a || old.mul.held_b!==newx.mul.held_b)$fatal(1,"consumed operands differ");
   if(old.mul.held_a!=$signed(old.mul.held_a[33:0]) || old.mul.held_b!=$signed(old.mul.held_b[27:0]))
    $fatal(1,"consumed operand outside retained width");
  end
  if(old.mdone && !old.mc && old.mresult!==newx.mresult)$fatal(1,"accepted multiply differs");
  if(old.ddone && !old.dc && old.dresult!==newx.dresult)$fatal(1,"accepted divide differs");
  if(old.dut.height_command_seen && old.dut.height_command_age==0)begin
   pubs=pubs+1;if(forbid)$fatal(1,"cancelled numeric transaction published");
  end
  if(old.dut.iz!=$signed(old.dut.iz[26:0]) || old.dut.bias!=$signed(old.dut.bias[25:0]))$fatal(1,"I/bias exceeds27/26");
  if(old.dut.state==66 || old.dut.state==67)begin
   if(old.dut.candidate_iz!==newx.dut.candidate_iz || old.dut.p_bias!==newx.dut.p_bias)$fatal(1,"valid candidate/Pbias differs");
   if(old.dut.candidate_iz!=$signed(old.dut.candidate_iz[26:0]) || old.dut.p_bias!=$signed(old.dut.p_bias[28:0]))$fatal(1,"valid candidate/Pbias exceeds27/29");
  end
  if(old.dut.state==67)begin
   if(old.dut.candidate_collective!==newx.dut.candidate_collective || old.dut.current_collective!==newx.dut.current_collective)$fatal(1,"valid collective differs");
   if(old.dut.candidate_collective!=$signed(old.dut.candidate_collective[29:0]) || old.dut.current_collective!=$signed(old.dut.current_collective[29:0]))$fatal(1,"valid collective exceeds30");
  end
  if(old.ma!==newx.ma || old.mb!==newx.mb)differences=differences+1;
  if(old.dut.num!==newx.dut.num || old.dut.value!==newx.dut.value)$fatal(1,"num/value aliases differ");
  if(old.dut.num!=$signed(old.dut.num[49:0]) || old.dut.value!=$signed(old.dut.value[38:0]))
   $fatal(1,"num/value exceeds retained50/39 width");
 end
end
initial begin
 clocks(8);rst_n=1;clocks(30);callback(0);callback(1);
 for(j=0;j<4;j=j+1)begin
  // One invalid pulse is captured while readiness is still from the old sample.
  // Its calc reaches state0 on the same edge registered cancel becomes high.
  clocks(20);if(old.dut.state!=0)$fatal(1,"not idle before invalid fixture");
  pub_before=pubs;forbid=1;
  @(negedge clk);hu=1;az=j==0?32'sh7fffffff:j==1?32'sh80000000:j==2?32'sd30001:-32'sd30001;
  @(negedge clk);hu=0;az=0;
  clocks(15);
  if(pubs!=pub_before || old.dut.tracking || old.dut.height_command_seen)$fatal(1,"invalid pulse not revoked");
  invalid_checks=invalid_checks+1;forbid=0;
  callback(0);callback(1);
 end
 for(k=0;k<24;k=k+1)begin
  h=k%2?5000:0;vx=k%2?(10000<<<F):(-10000<<<F);vy=-vx;vz=vy;
  ax=k%2?30000:-30000;ay=-ax;az=ax;yaw=k%2?18000:-18000;
  ch1=k%2?2000:1000;ch2=3000-ch1;ch3=k%2?1684:1002;
  pval=k%3==0?16'd65535:k%3==1?16'd10000:16'd1000;ival=pval;
  clocks(12);callback(1);
 end
 if(differences!=0 || grants<100 || pubs<15 || invalid_checks!=4)$fatal(1,"fixture coverage incomplete %0d/%0d/%0d/%0d",differences,grants,pubs,invalid_checks);
 $display("PASS fraction=%0d control_cycles=%0d legal_grants=%0d Z_publications=%0d invalid_captures=%0d operand_difference_cycles_must_be_zero=%0d",F,cycles,grants,pubs,invalid_checks,differences);
 $finish;
end
initial begin #100000000;$fatal(1,"timeout");end
endmodule
