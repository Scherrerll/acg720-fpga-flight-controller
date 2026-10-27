`timescale 1ns/1ps
`default_nettype none
module age_tb;
 reg clk=0,rst_n=1,sample_valid=0,tick_ms=0,seed=0,seed_seen=0;
 reg[31:0]time_ms=0,seed_age=0,seed_previous=0,rng=32'h876c2bd9;
 always #5 clk=~clk;
 wire[31:0]a0,a1,p0,p1;wire s0,s1,b0,b1,c0,c1;
 age_old d0(.*,.age(a0),.previous(p0),.seen(s0),.f1000(b0),.f200(c0));
 age_new d1(.*,.age(a1),.previous(p1),.seen(s1),.f1000(b1),.f200(c1));
 integer checks=0,n,j;
 task trial;input[31:0]a;input integer mode;begin
  @(negedge clk);seed=1;seed_age=a;seed_previous=rng;seed_seen=mode[0];
  @(negedge clk);seed=0;rst_n=mode[1];sample_valid=mode[2];tick_ms=mode[3];time_ms=mode[4] ? seed_previous:~seed_previous;
  if(mode[5])sample_valid=1'bx;if(mode[6])tick_ms=1'bx;
  if(mode[7])rst_n=1'bx;if(mode[8])time_ms=32'hxxxxxxxx;
  @(posedge clk);#1;
  if({a0,p0,s0,b0,c0}!=={a1,p1,s1,b1,c1})$fatal(1,"age transition mismatch age=%h mode=%h",a,mode);
  if(b1!==(a1<1000) || c1!==(a1<200))$fatal(1,"age transition invariant failed");
  checks=checks+1;
 end endtask
 initial begin
  for(j=0;j<512;j=j+1)begin
   trial(0,j);trial(198,j);trial(199,j);trial(200,j);trial(998,j);trial(999,j);trial(1000,j);
   trial(32'hfffffffe,j);trial(32'hffffffff,j);trial(32'h0000ffff,j);trial(32'h7fffffff,j);
  end
  for(n=0;n<100000;n=n+1)begin rng=rng*32'd1664525+32'd1013904223;trial(rng,n%512);end
  $display("PASS inductive vectors=%0d known_age32=1 four_state_control=1 arbitrary_invariant_state_fixture=1 no_full_reader_DUT_force=1",checks);$finish;
 end
endmodule
`default_nettype wire
