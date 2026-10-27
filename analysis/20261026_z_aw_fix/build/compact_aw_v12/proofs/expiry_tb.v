`default_nettype none

`timescale 1ns/1ps
module tb;
 parameter PRE=0,AGE=31;
 reg stall=0;
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
  if(stall || !rst_n || origin || !rv || !av || rawaz>30000 || rawaz< -30000 || refh<0 || refh>5000 || (!PRE && age>=5000000))begin au=0;acc_cadence=0;end
  else if(acc_cadence==9999)begin au=1;acc_cadence=0;end
  else begin au=0;acc_cadence=acc_cadence+1;end
 end

 wire [1:0] ms,mc,ds,dc,mbusy,md,dbusy,dd,de,mg,dg;
 wire signed [63:0] ma[0:1],mb[0:1],dn[0:1],mr[0:1],dr[0:1];
 wire [31:0] den[0:1];
 wire [1:0] valid,ready,qr,qv,up,vqok,tail,vraw;
 wire signed [31:0] h[0:1],vz[0:1],az[0:1],vq[0:1];
 wire [15:0] reason[0:1];


 height_old #(.CLK_HZ(5000000),.AGE_LIMIT(AGE),.CAL_MASK(8'h18),.RANGE_AGE_PRECHECKED(PRE),.PRECHECKED_AZ_RANGE(1)) d0(
 .clk(clk),.rst_n(rst_n),.origin_reset(origin),.range_valid(rv),.acc_valid(av),.acc_update(au),
 .acc_dt_us(32'd11000),.range_age_ticks(age),.ref_height_mm(refh),.az_up_mmps2(rawaz),.az_range_ok(rawaz>=-30000 && rawaz<=30000),
 .math_mul_start(ms[0]),.math_mul_cancel(mc[0]),.math_mul_a(ma[0]),.math_mul_b(mb[0]),
 .math_mul_busy(mbusy[0]|stall),.math_mul_done(md[0]&&!stall),.math_mul_result(mr[0]),
 .math_div_start(ds[0]),.math_div_cancel(dc[0]),.math_div_numerator(dn[0]),.math_div_denominator(den[0]),
 .math_div_busy(dbusy[0]|stall),.math_div_done(dd[0]&&!stall),.math_div_error(de[0]),.math_div_result(dr[0]),
 .valid(valid[0]),.estimate_ready(ready[0]),.qualified_ready(qr[0]),.qualified_valid(qv[0]),.update(up[0]),
 .fused_height_mm(h[0]),.vz_mmps(vz[0]),.sample_az_mmps2(az[0]),.vz_q16(vq[0]),.vz_q16_valid(vqok[0]),
 .reason(reason[0]),.estimate_ready_state_numeric_tail(tail[0]),.vz_q16_range_raw(vraw[0]));
 nav_math_service #(.CLIENTS(1),.DIVIDE(0)) m0(.clk(clk),.rst_n(rst_n),.request(ms[0]),.cancel(mc[0]),
 .operand_a(ma[0]),.operand_b(mb[0]),.busy(mbusy[0]),.done(md[0]),.error(),.result(mr[0]),.grant(mg[0]));
 nav_math_service #(.CLIENTS(1),.DIVIDE(1)) q0(.clk(clk),.rst_n(rst_n),.request(ds[0]),.cancel(dc[0]),
 .operand_a(dn[0]),.operand_b({32'd0,den[0]}),.busy(dbusy[0]),.done(dd[0]),.error(de[0]),.result(dr[0]),.grant(dg[0]));

 height_new #(.CLK_HZ(5000000),.AGE_LIMIT(AGE),.CAL_MASK(8'h18),.RANGE_AGE_PRECHECKED(PRE),.PRECHECKED_AZ_RANGE(1)) d1(
 .clk(clk),.rst_n(rst_n),.origin_reset(origin),.range_valid(rv),.acc_valid(av),.acc_update(au),
 .acc_dt_us(32'd11000),.range_age_ticks(age),.ref_height_mm(refh),.az_up_mmps2(rawaz),.az_range_ok(rawaz>=-30000 && rawaz<=30000),
 .math_mul_start(ms[1]),.math_mul_cancel(mc[1]),.math_mul_a(ma[1]),.math_mul_b(mb[1]),
 .math_mul_busy(mbusy[1]|stall),.math_mul_done(md[1]&&!stall),.math_mul_result(mr[1]),
 .math_div_start(ds[1]),.math_div_cancel(dc[1]),.math_div_numerator(dn[1]),.math_div_denominator(den[1]),
 .math_div_busy(dbusy[1]|stall),.math_div_done(dd[1]&&!stall),.math_div_error(de[1]),.math_div_result(dr[1]),
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

 integer expiry_edges=0,last_good=0,pub_count=0,checks=0;
 always @(posedge clk)begin
  cycles=cycles+1;#1;checks=checks+1;
  if(pub0!==pub1 || req0!==req1 || svc0!==svc1 || d0.sources_ok!==d1.sources_ok || d0.publication_age!==d1.publication_age)
   $fatal(1,"full-module expiry differential AGE=%0d PRE=%0d cycle=%0d",AGE,PRE,cycles);
  if(d1.publication_fresh!==(d0.publication_age<AGE))$fatal(1,"same-age predicate AGE=%0d age=%h flag=%b",AGE,d0.publication_age,d1.publication_fresh);
  if(up[0])begin
   pub_count=pub_count+1;
   if(d0.publication_age!==0 || d1.publication_fresh!==1 || ready[0]!==1 || ready[1]!==1)$fatal(1,"publication must restore freshness same clock");
  end
  if(d0.publication_age==AGE-1 && d0.seen && !d0.cleanup && !d0.fault)begin
   if(!ready[0] || !ready[1] || !d1.publication_fresh)$fatal(1,"freshness revoked early AGE=%0d",AGE);
   last_good=last_good+1;
  end
  if(d0.publication_age==AGE && d0.seen && !d0.cleanup && !d0.fault)begin
   if(ready[0] || ready[1] || tail[0] || tail[1] || d1.publication_fresh)$fatal(1,"timeout granted an extra clock AGE=%0d",AGE);
   expiry_edges=expiry_edges+1;
  end
  if(cycles>700000)$fatal(1,"bounded expiry fixture timeout");
 end
 initial begin
  repeat(8)@(negedge clk);rst_n=1;
  while(!up[0])@(negedge clk);
  if(AGE>=65536)stall=1;
  repeat(AGE+10000)@(negedge clk);
  if(expiry_edges!=1 || last_good!=1 || pub_count!=1)$fatal(1,"expiry coverage AGE=%0d lastgood=%0d expiry=%0d pub=%0d",AGE,last_good,expiry_edges,pub_count);
  origin=1;repeat(3)@(negedge clk);origin=0;stall=0;
  while(!up[0])@(negedge clk);
  if(pub_count<2)$fatal(1,"no unforced republish after epoch cancellation");
  $display("PASS expiry AGE=%0d PRE=%0d cycles=%0d same_age_checks=%0d exact_expiry_edges=%0d last_good_edges=%0d publications=%0d no_DUT_state_force=1",AGE,PRE,cycles,checks,expiry_edges,last_good,pub_count);$finish;
 end
endmodule
`default_nettype wire
