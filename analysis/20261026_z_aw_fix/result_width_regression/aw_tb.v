`timescale 1ns/1ps
module tb;
 reg clk=0,rst_n=0,enabled=1,rc_valid=1,height_valid=1,origin=0,taking_off=1;
 reg sample_update=0,height_update=0,position_update=0;
 reg[15:0]ch3=1500,pval=1000,ival=350;
 reg signed[31:0]height_mm=1000,vz=0,vx=0,vy=0;
 wire[15:0]nc,bc;wire signed[31:0]nt,bt,ns,bs;wire signed[15:0]nr,np,br,bp;wire na,ba;
 candidate_side candidate(clk,rst_n,enabled,rc_valid,height_valid,origin,taking_off,sample_update,height_update,position_update,ch3,pval,ival,height_mm,vz,vx,vy,nc,nt,ns,nr,np,na);
 base_side baseline(clk,rst_n,enabled,rc_valid,height_valid,origin,taking_off,sample_update,height_update,position_update,ch3,pval,ival,height_mm,vz,vx,vy,bc,bt,bs,br,bp,ba);
 wire[15:0]vc;wire signed[31:0]vt,vs;wire signed[15:0]vr,vp;wire va;
 v1_side previous_b4(clk,rst_n,enabled,rc_valid,height_valid,origin,taking_off,sample_update,height_update,position_update,ch3,pval,ival,height_mm,vz,vx,vy,vc,vt,vs,vr,vp,va);
 always #10 clk=~clk;
 integer test_case=0,cycles=0,callbacks=0,new_pubs=0,base_pubs=0,base_xy_pubs=0,new_xy_pubs=0;
 integer upper_rejects=0,lower_rejects=0,accepted_up=0,accepted_down=0,commits=0;
 integer positive_i_steps=0,negative_i_steps=0,base_low_count=0,base_low_high=0;
 integer low_start=-1,first_below1850=-1,first_below1250=-1,elapsed=0,fd,checks=0;
 integer expect_new_time=0,last_base_time=0,max_pub_delay=0;
 reg done=0,xy_enable=0,compare_unsat=0,reverse_phase=0;
 reg[15:0]saved_bc=0;reg signed[31:0]saved_bt=0,saved_bs=0;
 reg signed[63:0]saved_bi=0,saved_bb=0,expected_i=0,expected_u=0,old_i=0,cand_i=0,pb=0;
 reg signed[15:0]saved_br=0,saved_bp=0;
 reg will_commit=0,reject_ref=0,was_taking_off=0;
 reg signed[63:0]last_i=0;
 function signed[63:0] clip_ref;input signed[63:0]v;begin clip_ref=v<0?0:v>64'sd55705600?64'sd55705600:v;end endfunction
 always @(negedge clk)begin
  sample_update=0;height_update=0;position_update=0;
  if(rst_n)begin
   cycles=cycles+1;
   if(cycles%(test_case==5?20000:2500)==0)begin
    callbacks=callbacks+1;
    if(test_case==1 && callbacks==1819)begin ch3=1002;low_start=callbacks*11;end
    sample_update=1;height_update=1;
    if(xy_enable && callbacks%2==0)position_update=1;
   end
  end
 end
 // Reference the candidate selection contract independently at the actual
 // commit edge. These are observations, never hierarchical force/preloads.
 always @(posedge clk)begin
  will_commit=rst_n && !candidate.dut.cancel && !origin && !candidate.dut.blocked && candidate.dut.tracking && candidate.dut.state==67;
  if(will_commit)begin
   old_i=candidate.dut.iz;cand_i=candidate.dut.candidate_iz;pb=candidate.dut.p_bias;
   if(candidate.dut.candidate_collective!==pb+cand_i || candidate.dut.current_collective!==pb+old_i)
    $fatal(1,"staged signed sums mismatch");
   if(candidate.dut.candidate_i_up!==(cand_i>old_i) || candidate.dut.candidate_i_down!==(cand_i<old_i))
    $fatal(1,"actual candidate direction mismatch");
   reject_ref=((pb+cand_i)>64'sd55705600 && cand_i>old_i) || ((pb+cand_i)<0 && cand_i<old_i);
   if(candidate.dut.reject_z_i!==reject_ref)$fatal(1,"reject predicate mismatch");
   expected_i=taking_off?(reject_ref?old_i:cand_i):0;
   expected_u=taking_off?clip_ref(pb+expected_i):0;
   was_taking_off=taking_off;
   if(taking_off)begin
    commits=commits+1;
    if(reject_ref && pb+cand_i>64'sd55705600)upper_rejects=upper_rejects+1;
    if(reject_ref && pb+cand_i<0)lower_rejects=lower_rejects+1;
    if(!reject_ref && cand_i>old_i)accepted_up=accepted_up+1;
    if(!reject_ref && cand_i<old_i)accepted_down=accepted_down+1;
   end
  end
  #1;
  if(will_commit)begin
   if(candidate.dut.iz!==expected_i || candidate.dut.collective_q16!==expected_u)
    $fatal(1,"I/output commit mismatch i=%0d/%0d u=%0d/%0d",candidate.dut.iz,expected_i,candidate.dut.collective_q16,expected_u);
   if(reject_ref && candidate.dut.iz!==old_i)$fatal(1,"rejected I committed");
   checks=checks+1;
  end
  if(rst_n)begin
   if(candidate.dut.num!==previous_b4.dut.num || candidate.dut.value!==previous_b4.dut.value)
    $fatal(1,"num/value64 aliases differ from original v1");
   if(candidate.dut.num!=$signed(candidate.dut.num[49:0]) || candidate.dut.value!=$signed(candidate.dut.value[38:0]))
    $fatal(1,"num/value exceeds retained50/39 width");
   if(candidate.dut.iz< -64'sd22937600 || candidate.dut.iz>64'sd55705600 || candidate.dut.bias<0 || candidate.dut.bias>64'sd22937600)
    $fatal(1,"reachable I/bias bounds violated I=%0d bias=%0d",candidate.dut.iz,candidate.dut.bias);
   if(nc!==vc || nt!==vt || ns!==vs || nr!==vr || np!==vp || na!==va ||
      candidate.dut.iz!==previous_b4.dut.iz || candidate.dut.bias!==previous_b4.dut.bias ||
      candidate.dut.ix!==previous_b4.dut.ix || candidate.dut.iy!==previous_b4.dut.iy ||
      candidate.dut.throttle_delta!==previous_b4.dut.throttle_delta ||
      candidate.dut.height_reason!==previous_b4.dut.height_reason || candidate.dut.reason!==previous_b4.dut.reason)
    $fatal(1,"compact/v1 externally visible or persistent-integral mismatch state=%0d/%0d",candidate.dut.state,previous_b4.dut.state);
   if(candidate.dut.blocked || baseline.dut.blocked || candidate.dut.xy_blocked || baseline.dut.xy_blocked || candidate.dut.z_stick_fault || baseline.dut.z_stick_fault)
    $fatal(1,"unexpected arithmetic/stick/controller fault");
   if(baseline.dut.height_command_seen && baseline.dut.height_command_age==0)begin
    base_pubs=base_pubs+1;last_base_time=cycles;
    saved_bc=bc;saved_bt=bt;saved_bs=bs;saved_bi=baseline.dut.iz;saved_bb=baseline.dut.bias;
    if(test_case==1 && low_start>=0 && callbacks*11-low_start<=4600)begin
     base_low_count=base_low_count+1;
     if(bc==1850)base_low_high=base_low_high+1;
     else $fatal(1,"historical old-RTL windup counterexample did not reproduce");
    end
   end
   if(candidate.dut.height_command_seen && candidate.dut.height_command_age==0)begin
    new_pubs=new_pubs+1;
    if(base_pubs!=new_pubs)$fatal(1,"publication pair count mismatch old=%0d new=%0d",base_pubs,new_pubs);
    if(cycles-last_base_time>max_pub_delay)max_pub_delay=cycles-last_base_time;
    if(cycles-last_base_time!=2)$fatal(1,"Z publication latency changed by %0d clocks, expected2",cycles-last_base_time);
    if(compare_unsat)begin
     if(nc!==saved_bc || nt!==saved_bt || ns!==saved_bs || candidate.dut.iz!==saved_bi || candidate.dut.bias!==saved_bb)
      $fatal(1,"unsaturated per-publication mismatch new=%0d,%0d,%0d I%0d old=%0d,%0d,%0d I%0d",nc,nt,ns,candidate.dut.iz,saved_bc,saved_bt,saved_bs,saved_bi);
     if(candidate.dut.iz>last_i)positive_i_steps=positive_i_steps+1;
     if(candidate.dut.iz<last_i)negative_i_steps=negative_i_steps+1;
     last_i=candidate.dut.iz;
    end
    $fdisplay(fd,"%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d",callbacks*11,ch3,nc,saved_bc,nt,ns,candidate.dut.iz,saved_bi,candidate.dut.bias,upper_rejects,lower_rejects);
    if(test_case==1 && low_start>=0)begin
     elapsed=callbacks*11-low_start;
     if(nc<1850 && first_below1850<0)first_below1850=elapsed;
     if(nc<1250 && first_below1250<0)first_below1250=elapsed;
     if(elapsed>=4600)done=1;
    end
   end
   if(baseline.dut.command_seen && baseline.dut.command_age==0)begin base_xy_pubs=base_xy_pubs+1;saved_br=br;saved_bp=bp;end
   if(candidate.dut.command_seen && candidate.dut.command_age==0)begin
    new_xy_pubs=new_xy_pubs+1;
    if(test_case==5 && (nr!==saved_br || np!==saved_bp || candidate.dut.ix!=0 || candidate.dut.iy!=0))
     $fatal(1,"XY I0 regression new=%0d,%0d old=%0d,%0d",nr,np,saved_br,saved_bp);
   end
  end
 end
 task pubs;input integer n;integer goal;begin goal=new_pubs+n;while(new_pubs<goal)begin @(posedge clk);#2;end end endtask
 task reset_pair;begin
  @(negedge clk);rst_n=0;repeat(8)@(negedge clk);
  cycles=0;callbacks=0;new_pubs=0;base_pubs=0;base_xy_pubs=0;new_xy_pubs=0;last_i=0;
  enabled=1;rc_valid=1;height_valid=1;origin=0;taking_off=1;rst_n=1;
 end endtask
 task cancellation;input integer state_value,kind;integer oldpubs;begin
  reset_pair();ch3=1684;height_mm=300;pubs(5);
  wait(candidate.dut.state==state_value);@(negedge clk);oldpubs=new_pubs;
  case(kind)0:enabled=0;1:rc_valid=0;2:height_valid=0;3:origin=1;endcase
  // The standalone hold block registers RC cancellation; its nav wrapper
  // provides the combinational public RC mask (covered by root top tests).
  #1;if(kind!=1 && na)$fatal(1,"live revoke did not immediately mask height_active");
  repeat(8)@(negedge clk);
  if(na || candidate.dut.iz!=0 || candidate.dut.candidate_iz!=0 || nc!=1000 || candidate.dut.height_command_seen || candidate.dut.state!=0 || new_pubs!=oldpubs)
   $fatal(1,"cancel did not discard staged work or allowed publication state=%0d kind=%0d",state_value,kind);
  enabled=1;rc_valid=1;height_valid=1;origin=0;pubs(3);
 end endtask
 integer j;
 initial begin
  if(!$value$plusargs("CASE=%d",test_case))$fatal(1,"CASE required");
  fd=$fopen("trace.csv","w");$fdisplay(fd,"logical_ms,ch3,new_collective,old_collective,target_mm,climb_mmps,new_iz_q16,old_iz_q16,bias_q16,upper_rejects,lower_rejects");
  case(test_case)
   1:begin
    ch3=1684;height_mm=300;reset_pair();wait(done);@(negedge clk);
    if(base_low_count!=419 || base_low_high!=419 || upper_rejects<100 || first_below1850<0 || first_below1850>1000 || first_below1250<0 || first_below1250>2000 || nt>=0 || ns!=-2500)
     $fatal(1,"upper/recovery coverage oldhigh=%0d/%0d reject=%0d first=%0d/%0d target=%0d speed=%0d",base_low_high,base_low_count,upper_rejects,first_below1850,first_below1250,nt,ns);
    $display("PASS natural upper windup: old1850=%0d/%0d first4600ms; new below1850=%0dms below1250=%0dms upper_rejects=%0d accepted_down=%0d",base_low_high,base_low_count,first_below1850,first_below1250,upper_rejects,accepted_down);
   end
   2:begin
    compare_unsat=1;ch3=1500;height_mm=1000;reset_pair();pubs(100);
    @(negedge clk);vz=-100*65536;pubs(100);
    @(negedge clk);vz=100*65536;pubs(150);
    @(negedge clk);vz=0;pubs(50);
    if(upper_rejects || lower_rejects || positive_i_steps<90 || negative_i_steps<140)$fatal(1,"unsat coverage failed");
    $display("PASS unsaturated old/new publication equivalence: publications=%0d positiveI=%0d negativeI=%0d delay=%0dclocks",new_pubs,positive_i_steps,negative_i_steps,max_pub_delay);
   end
   3:begin
    ch3=1002;height_mm=1000;reset_pair();pubs(400);
    if(lower_rejects<100 || nc!=1000)$fatal(1,"lower clamp not reached naturally");
    @(negedge clk);ch3=2000;reverse_phase=1;pubs(250);
    if(nc<=1000 || accepted_up<20 || ns<=0)$fatal(1,"lower saturation did not recover upward");
    $display("PASS natural lower saturation and positive recovery: lower_rejects=%0d accepted_up=%0d final_collective=%0d",lower_rejects,accepted_up,nc);
   end
   4:begin
    ch3=1684;height_mm=300;
    cancellation(22,0);cancellation(23,0);cancellation(24,0);cancellation(66,0);cancellation(67,0);
    cancellation(67,1);cancellation(67,2);cancellation(67,3);
    reset_pair();pubs(5);wait(candidate.dut.state==66);@(negedge clk);taking_off=0;
    #1;if(na)$fatal(1,"takingoff false mask");pubs(2);
    if(candidate.dut.iz!=0 || candidate.dut.collective_q16!=0 || nc!=1000)$fatal(1,"not-takingoff staged commit");
    $display("PASS eight staged cancel/reentry boundaries plus taking_off false; no stale publication; live safety mask retained");
   end
   5:begin
    ch3=1500;height_mm=1000;ival=0;pval=1000;vx=400*65536;vy=-600*65536;xy_enable=1;
    reset_pair();pubs(100);@(negedge clk);vz=-100*65536;pubs(50);
    if(new_xy_pubs<60 || candidate.dut.ix!=0 || candidate.dut.iy!=0 || candidate.dut.iz==0 || np<398 || np>402 || nr<598 || nr>602)
     $fatal(1,"XY I0/Z independence coverage pubs=%0d angles=%0d,%0d iz=%0d",new_xy_pubs,nr,np,candidate.dut.iz);
    $display("PASS XY I0 retains exact old angles/zeroXYintegral across %0d callbacks while Z I is nonzero",new_xy_pubs);
   end
   default:$fatal(1,"unknown case");
  endcase
  $display("PASS reachable I[-350,850] and bias[0,350] checked each active cycle");
  $display("PASS compact/v1 module outputs and persistent integrals match every active cycle");
  $display("PASS commit contract checked %0d times; every Z publication delayed exactly2clocks",checks);
  $fclose(fd);$finish;
 end
 initial begin #350000000;$fatal(1,"bounded simulation timeout");end
endmodule
