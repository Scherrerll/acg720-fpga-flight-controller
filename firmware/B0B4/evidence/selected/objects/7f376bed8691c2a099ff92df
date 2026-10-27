
`timescale 1ns/1ps
module tb;
 parameter PRE=0;
 reg clk=0; always #10 clk=~clk;
 reg rst_n=0,origin=0,rv=1,av=1,au=0;
 reg [31:0] age=0;
 reg signed [31:0] refh=300,rawaz=0;
 integer cycles=0,pubs=0,mcons=0,dcons=0,acccons=0;
 integer numeric_pulses=0,ready_numeric_pulses=0,commit_vetoes=0,epoch_pulses=0;
 integer age_rejects=0,age_bypasses=0,seeds=0,ready_cycles=0;
 integer acc_cadence=0;
 // Real 11,000us integration dt retained; only sample admission cadence and
 // height timer are accelerated. 10,000 clocks leaves arithmetic time to finish.
 always @(negedge clk) begin
  if(!rst_n || origin || !rv || !av || rawaz>30000 || rawaz< -30000 || refh<0 || refh>5000 || (!PRE && age>=5000000))begin au=0;acc_cadence=0;end
  else if(acc_cadence==9999)begin au=1;acc_cadence=0;end
  else begin au=0;acc_cadence=acc_cadence+1;end
 end

 wire [1:0] ms,mc,ds,dc,mbusy,md,dbusy,dd,de,mg,dg;
 wire signed [63:0] ma[0:1],mb[0:1],dn[0:1],mr[0:1],dr[0:1];
 wire [31:0] den[0:1];
 wire [1:0] valid,ready,qr,qv,up,vqok,tail,vraw;
 wire signed [31:0] h[0:1],vz[0:1],az[0:1],vq[0:1];
 wire [15:0] reason[0:1];


 height_v7 #(.CLK_HZ(5000000),.AGE_LIMIT(5000000),.CAL_MASK(8'h18),.RANGE_AGE_PRECHECKED(PRE)) d0(
 .clk(clk),.rst_n(rst_n),.origin_reset(origin),.range_valid(rv),.acc_valid(av),.acc_update(au),
 .acc_dt_us(32'd11000),.range_age_ticks(age),.ref_height_mm(refh),.az_up_mmps2(rawaz),
 .math_mul_start(ms[0]),.math_mul_cancel(mc[0]),.math_mul_a(ma[0]),.math_mul_b(mb[0]),
 .math_mul_busy(mbusy[0]),.math_mul_done(md[0]),.math_mul_result(mr[0]),
 .math_div_start(ds[0]),.math_div_cancel(dc[0]),.math_div_numerator(dn[0]),.math_div_denominator(den[0]),
 .math_div_busy(dbusy[0]),.math_div_done(dd[0]),.math_div_error(de[0]),.math_div_result(dr[0]),
 .valid(valid[0]),.estimate_ready(ready[0]),.qualified_ready(qr[0]),.qualified_valid(qv[0]),.update(up[0]),
 .fused_height_mm(h[0]),.vz_mmps(vz[0]),.sample_az_mmps2(az[0]),.vz_q16(vq[0]),.vz_q16_valid(vqok[0]),
 .reason(reason[0]),.estimate_ready_state_numeric_tail(tail[0]),.vz_q16_range_raw(vraw[0]));
 nav_math_service #(.CLIENTS(1),.DIVIDE(0)) m0(.clk(clk),.rst_n(rst_n),.request(ms[0]),.cancel(mc[0]),
 .operand_a(ma[0]),.operand_b(mb[0]),.busy(mbusy[0]),.done(md[0]),.error(),.result(mr[0]),.grant(mg[0]));
 nav_math_service #(.CLIENTS(1),.DIVIDE(1)) q0(.clk(clk),.rst_n(rst_n),.request(ds[0]),.cancel(dc[0]),
 .operand_a(dn[0]),.operand_b({32'd0,den[0]}),.busy(dbusy[0]),.done(dd[0]),.error(de[0]),.result(dr[0]),.grant(dg[0]));

 height_v8 #(.CLK_HZ(5000000),.AGE_LIMIT(5000000),.CAL_MASK(8'h18),.RANGE_AGE_PRECHECKED(PRE),.PRECHECKED_AZ_RANGE(1)) d1(
 .clk(clk),.rst_n(rst_n),.origin_reset(origin),.range_valid(rv),.acc_valid(av),.acc_update(au),
 .acc_dt_us(32'd11000),.range_age_ticks(age),.ref_height_mm(refh),.az_up_mmps2(rawaz),.az_range_ok(rawaz>=-30000 && rawaz<=30000),
 .math_mul_start(ms[1]),.math_mul_cancel(mc[1]),.math_mul_a(ma[1]),.math_mul_b(mb[1]),
 .math_mul_busy(mbusy[1]),.math_mul_done(md[1]),.math_mul_result(mr[1]),
 .math_div_start(ds[1]),.math_div_cancel(dc[1]),.math_div_numerator(dn[1]),.math_div_denominator(den[1]),
 .math_div_busy(dbusy[1]),.math_div_done(dd[1]),.math_div_error(de[1]),.math_div_result(dr[1]),
 .valid(valid[1]),.estimate_ready(ready[1]),.qualified_ready(qr[1]),.qualified_valid(qv[1]),.update(up[1]),
 .fused_height_mm(h[1]),.vz_mmps(vz[1]),.sample_az_mmps2(az[1]),.vz_q16(vq[1]),.vz_q16_valid(vqok[1]),
 .reason(reason[1]),.estimate_ready_state_numeric_tail(tail[1]),.vz_q16_range_raw(vraw[1]));
 nav_math_service #(.CLIENTS(1),.DIVIDE(0)) m1(.clk(clk),.rst_n(rst_n),.request(ms[1]),.cancel(mc[1]),
 .operand_a(ma[1]),.operand_b(mb[1]),.busy(mbusy[1]),.done(md[1]),.error(),.result(mr[1]),.grant(mg[1]));
 nav_math_service #(.CLIENTS(1),.DIVIDE(1)) q1(.clk(clk),.rst_n(rst_n),.request(ds[1]),.cancel(dc[1]),
 .operand_a(dn[1]),.operand_b({32'd0,den[1]}),.busy(dbusy[1]),.done(dd[1]),.error(de[1]),.result(dr[1]),.grant(dg[1]));

 wire [151:0] pub0={valid[0],ready[0],qr[0],qv[0],up[0],h[0],vz[0],az[0],vq[0],vqok[0],reason[0],tail[0],vraw[0]};
 wire [151:0] pub1={valid[1],ready[1],qr[1],qv[1],up[1],h[1],vz[1],az[1],vq[1],vqok[1],reason[1],tail[1],vraw[1]};
 wire [227:0] req0={ms[0],mc[0],ma[0],mb[0],ds[0],dc[0],dn[0],den[0]};
 wire [227:0] req1={ms[1],mc[1],ma[1],mb[1],ds[1],dc[1],dn[1],den[1]};
 wire [134:0] svc0={mbusy[0],md[0],mr[0],dbusy[0],dd[0],de[0],dr[0],mg[0],dg[0]};
 wire [134:0] svc1={mbusy[1],md[1],mr[1],dbusy[1],dd[1],de[1],dr[1],mg[1],dg[1]};
 always @(posedge clk) begin
  cycles=cycles+1;
  if(rst_n && !d0.cleanup)begin
   if((d0.state==100 || d0.state==102) && md[0]) mcons=mcons+1;
   if(d0.state==101 && dd[0])begin
    dcons=dcons+1;
    if(de[0])$fatal(1,"unexpected real divider error");
    if(d0.return_state==70 || d0.return_state==72 || d0.return_state==73)acccons=acccons+1;
   end
   if(d0.state==80)seeds=seeds+1;
  end
  #1;
  if(pub0!==pub1 || req0!==req1 || svc0!==svc1 || d0.sources_ok!==d1.sources_ok)
   $fatal(1,"differential mismatch PRE=%0d cycle=%0d state=%0d/%0d pub=%h/%h req=%h/%h svc=%h/%h",PRE,cycles,d0.state,d1.state,pub0,pub1,req0,req1,svc0,svc1);
  if(up[0])pubs=pubs+1;
  if(ready[0])ready_cycles=ready_cycles+1;
  if(cycles>3000000)$fatal(1,"bounded global timeout");
 end
 task wait_ready;
 integer k;
 begin : wr
  for(k=0;k<90000;k=k+1)begin
   @(negedge clk);
   if(ready[0])disable wr;
  end
  $fatal(1,"no ready after legal source recovery PRE=%0d state=%0d fault=%0d",PRE,d0.state,d0.fault);
 end endtask
 task wait_publish_stage;
 integer k;
 begin : wp
  for(k=0;k<90000;k=k+1)begin
   @(negedge clk);
   if(d0.state==84 && ready[0])disable wp;
  end
  $fatal(1,"no live publish-stage boundary");
 end endtask
 task bad_numeric;
 input signed [31:0] x;
 begin
  wait_ready;wait_publish_stage;
  rawaz=x;numeric_pulses=numeric_pulses+1;
  #1;
  if(d0.sources_ok || d1.sources_ok || ready[0] || ready[1] || tail[0] || tail[1])$fatal(1,"bad az did not immediately revoke sources/tail");
  ready_numeric_pulses=ready_numeric_pulses+1;
  @(posedge clk);#2;
  if(up[0] || up[1] || !mc[0] || !mc[1] || !dc[0] || !dc[1])$fatal(1,"bad az publication veto/cancel failed");
  commit_vetoes=commit_vetoes+1;
  @(negedge clk);rawaz=0;
  wait_ready;
 end endtask
 task external_age;
 input [31:0] x;
 begin
  wait_ready;age=x;#1;
  if(PRE)begin
   if(!d0.sources_ok || !d1.sources_ok || !ready[0])$fatal(1,"prechecked range age unexpectedly checked");
   age_bypasses=age_bypasses+1;
  end else if(x>=5000000)begin
   if(d0.sources_ok || ready[0] || tail[0])$fatal(1,"range age threshold failed");
   age_rejects=age_rejects+1;
  end else if(!d0.sources_ok || !ready[0])$fatal(1,"age below threshold rejected");
  @(negedge clk);age=0;wait_ready;
 end endtask
 integer p0;
 initial begin
  repeat(8)@(negedge clk);rst_n=1;
  wait_ready;
  p0=pubs;repeat(330000)@(negedge clk);
  if(pubs-p0<5)$fatal(1,"normal zero-acc publications missing");
  rawaz=30000;refh=500;repeat(110000)@(negedge clk);
  if(!d0.sources_ok)$fatal(1,"+30000 not qualified");
  rawaz=-30000;refh=490;repeat(110000)@(negedge clk);
  if(!d0.sources_ok)$fatal(1,"-30000 not qualified");
  rawaz=0;repeat(55000)@(negedge clk);
  bad_numeric(30001);bad_numeric(-30001);bad_numeric(32'sh7fffffff);bad_numeric(32'sh80000000);
  wait_ready;origin=1;#1;if(ready[0])$fatal(1,"origin live revoke failed");
  @(posedge clk);#2;if(qr[0] || qv[0])$fatal(1,"origin qualified revoke failed");
  @(negedge clk);origin=0;epoch_pulses=epoch_pulses+1;wait_ready;
  rv=0;#1;if(d0.sources_ok || ready[0])$fatal(1,"range valid revoke failed");
  @(negedge clk);rv=1;epoch_pulses=epoch_pulses+1;wait_ready;
  av=0;#1;if(d0.sources_ok || ready[0])$fatal(1,"acc valid revoke failed");
  @(negedge clk);av=1;epoch_pulses=epoch_pulses+1;wait_ready;
  refh=-1;#1;if(d0.sources_ok || tail[0])$fatal(1,"negative height not rejected");
  @(negedge clk);refh=300;epoch_pulses=epoch_pulses+1;wait_ready;
  refh=5001;#1;if(d0.sources_ok || tail[0])$fatal(1,"excessive height not rejected");
  @(negedge clk);refh=300;epoch_pulses=epoch_pulses+1;wait_ready;
  // Legal height endpoints qualified combinationally, then restored before a clock.
  refh=0;#1;if(!d0.sources_ok)$fatal(1,"zero height rejected");
  refh=5000;#1;if(!d0.sources_ok)$fatal(1,"5000mm rejected");refh=300;
  external_age(4999999);external_age(5000000);external_age(5000001);external_age(32'hffffffff);
  // Reset during real arithmetic, followed by a fresh unforced seed/publication.
  while(!(d0.state==100 && mbusy[0]))@(negedge clk);
  rst_n=0;repeat(3)@(negedge clk);rst_n=1;wait_ready;
  repeat(110000)@(negedge clk);
  if(pubs<20 || seeds<8 || mcons<200 || dcons<200 || acccons<100 || numeric_pulses!=4 || commit_vetoes!=4 || epoch_pulses!=5)
   $fatal(1,"insufficient finite coverage pub=%0d seed=%0d mul=%0d div=%0d acc=%0d",pubs,seeds,mcons,dcons,acccons);
  if((!PRE && age_rejects!=3)||(PRE && age_bypasses!=4))$fatal(1,"age mode coverage missing");
  $display("PASS PRE=%0d cycles=%0d public_bits=152 request_bits=228 service_bits=135 publications=%0d seeds=%0d mul_consumed=%0d div_consumed=%0d acc_div_consumed=%0d numeric_pulses=%0d commit_vetoes=%0d epoch_pulses=%0d age_rejects=%0d age_bypasses=%0d ready_cycles=%0d",PRE,cycles,pubs,seeds,mcons,dcons,acccons,numeric_pulses,commit_vetoes,epoch_pulses,age_rejects,age_bypasses,ready_cycles);
  $finish;
 end
endmodule
