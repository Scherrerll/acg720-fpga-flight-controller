`timescale 1ns/1ps
module pipeline_policy;
 reg clk=0;always #10 clk=~clk;
 reg rst_n=0,stim=0;reg [95:0] raw={16'd0,16'd0,16'd2048,16'd1,16'd2,16'd3};
 reg [7:0] fault=0,who=8'h1e;
 wire nvalid,bvalid,nlink,blink,nupdate,bupdate;wire [31:0] na,ba,nr,ndt;
 wire [7:0] nf;
 integer np=0,bp=0,n,a0,r0,p0;
 imu_pipeline #(.CAL_SAMPLES(2)) actual(.clk50(clk),.rst_n(rst_n),.imu_miso(1'b0),
  .diag_taking_off(1'b0),.diag_gate_event(1'b0),.attitude_valid(nvalid),.link_usable(nlink),
  .attitude_update(nupdate),.accepted_count(na),.rejected_count(nr),.dt_ticks(ndt),.attitude_fault(nf));
 imu_pipeline_baseline #(.CAL_SAMPLES(2)) original(.clk50(clk),.rst_n(rst_n),.imu_miso(1'b0),
  .diag_taking_off(1'b0),.diag_gate_event(1'b0),.attitude_valid(bvalid),.link_usable(blink),
  .attitude_update(bupdate),.accepted_count(ba));
 always @(negedge clk)begin if(nupdate)np=np+1;if(bupdate)bp=bp+1;end
 task frame(input [95:0] value,input [7:0] bad);
 begin
  @(negedge clk);raw=value;fault=bad;stim=1;
  @(negedge clk);stim=0;fault=0;
  repeat(49998)@(negedge clk);
 end endtask
 task normal;begin frame({16'd0,16'd0,16'd2048,16'd1,16'd2,16'd3},0);end endtask
 initial begin
  force actual.record_ready=stim;force original.record_ready=stim;
  force actual.record_raw=raw;force original.record_raw=raw;
  force actual.reader_valid=1;force original.reader_valid=1;
  force actual.reader_config_ok=1;force original.reader_config_ok=1;
  force actual.reader_fault=fault;force original.reader_fault=fault;
  force actual.who=who;force original.who=who;
  force actual.pwr=8'h0f;force original.pwr=8'h0f;
  repeat(3)@(negedge clk);rst_n=1;
  for(n=0;n<24;n=n+1)normal();
  if(!nvalid || !bvalid || np<10 || np!=bp || na!=ba)$fatal(1,"startup/continuous A/B mismatch np=%0d bp=%0d",np,bp);
  $display("PASS pipeline normal A/B: accepted=%0d poses=%0d",na,np);
  a0=na;r0=nr;p0=np;
  frame(96'd0,0);frame({96{1'b1}},0);who=0;normal();who=8'h1e;
  frame({16'd0,16'd0,16'd2048,16'd1,16'd2,16'd3},8'h04);
  if(na!=a0 || nr!=r0+4 || np!=p0 || !nvalid)$fatal(1,"invalid records accepted or fabricated updates");
  normal();if(np!=p0+1 || ndt!=250000)$fatal(1,"real rejected-sample elapsed dt lost dt=%0d",ndt);
  a0=na;p0=np;
  // Jump only the measured source age to test the actual expiry branch.
  @(negedge clk);actual.guard.age_ticks=2999998;original.guard.age_ticks=2999998;
  repeat(10)@(negedge clk);
  if(!nlink || !nvalid || blink || bvalid || na!=a0 || np!=p0)$fatal(1,"silence policy A/B failed");
  if(actual.accepted_raw_age_ticks<3000000)$fatal(1,"age was hidden/reset");
  $display("PASS pipeline silence boundary: baseline invalid, candidate retains pose, no new sample/pose, diagnostic age=%0d",actual.accepted_raw_age_ticks);
  normal();
  if(ndt<=3000000 || nvalid || nf!=8'h10)$fatal(1,"long-gap numerical dt limit was bypassed dt=%0d fault=%0h",ndt,nf);
  for(n=0;n<10;n=n+1)normal();
  if(!nvalid || np<=p0)$fatal(1,"real fresh sample recovery failed");
  p0=np;frame({16'd0,16'd0,16'd4096,16'd1,16'd2,16'd167},0);
  if(!nvalid || np!=p0+1)$fatal(1,"legal 2g record stopped pose publication");
  $display("PASS pipeline_policy: real startup/math chain; bad ID/sentinel/transport rejection; source silence no longer revokes; real dt and long-gap numerical rejection/recovery retained");
  $finish;
 end
 initial begin #120000000;$fatal(1,"pipeline test timeout");end
endmodule
