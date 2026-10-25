`timescale 1ns/1ps
module timeout_boundaries;
 reg clk=0;always #10 clk=~clk;
 reg rst_n=0,ppm=0;
 wire valid,frame_update;
 rc_ppm rc(.clk(clk),.rst_n(rst_n),.ppm_in(ppm),.valid(valid),.frame_update(frame_update));
 wire [975:0] diag;
 mtf01p_reader mtf(.clk(clk),.rst_n(rst_n),.rx(1'b1),.uptime_ms(64'd0),
                   .diagnostic_hold(1'b0),.diagnostic_body(diag));
 task edge_wait;begin @(posedge clk);#1;end endtask
 task pulse_after(input integer us);
 begin #(us*1000-20000);ppm=1;#20000;ppm=0;end
 endtask
 integer i;
 initial begin
  repeat(3)edge_wait();rst_n=1;edge_wait();
  if(valid || mtf.module_online)$fatal(1,"startup must be invalid/offline");
  if(rc.FRESH_TICKS!=25000000 || rc.CLK_HZ!=50000000)$fatal(1,"RC must be 500 ms");
  pulse_after(4000);for(i=0;i<5;i=i+1)pulse_after(1500);pulse_after(4000);
  if(!valid || rc.frame_sequence!=1)$fatal(1,"valid frame not accepted");
  // Jump the otherwise linear 25-million-clock countdown to its final clocks.
  @(negedge clk);rc.fresh_ticks=2;
  edge_wait();if(!valid || rc.fresh_ticks!=1)$fatal(1,"RC expired early");
  edge_wait();if(valid || rc.fresh_ticks!=0)$fatal(1,"RC deadline missed");
  pulse_after(1500);for(i=1;i<5;i=i+1)pulse_after(1500);pulse_after(4000);
  if(!valid)$fatal(1,"RC recovery failed");
  pulse_after(700);if(valid)$fatal(1,"malformed frame must still revoke immediately");
  force mtf.samples=1;force mtf.age_ms=999;
  repeat(2)edge_wait();
  if(!mtf.module_online || !diag[960])$fatal(1,"offline before 1 s");
  if(mtf.link_fresh || mtf.range_ok || mtf.flow_ok)$fatal(1,"online indication made stale metrics usable");
  force mtf.age_ms=1000;repeat(2)edge_wait();
  if(mtf.module_online || diag[960])$fatal(1,"offline deadline missed");
  force mtf.age_ms=199;edge_wait();if(!mtf.link_fresh)$fatal(1,"metric limit changed");
  force mtf.age_ms=200;edge_wait();if(mtf.link_fresh)$fatal(1,"metric expired late");
  release mtf.age_ms;
  force mtf.time_ms=1;force mtf.sample_valid=1;
  edge_wait();release mtf.sample_valid;repeat(2)edge_wait();
  if(mtf.age_ms!=0 || !mtf.module_online || !diag[960])$fatal(1,"new frame recovery failed");
  @(negedge clk);mtf.age_ms=999;
  force mtf.sample_valid=1;edge_wait();release mtf.sample_valid;
  if(mtf.age_ms!=999)$fatal(1,"duplicate timestamp refreshed age");
  force mtf.samples=0;force mtf.age_ms=0;edge_wait();
  if(mtf.module_online)$fatal(1,"unseen source online");
  $display("PASS timeout_alignment: RC default=500ms, accepted frame/recovery, countdown boundary, invalid-frame rejection; module offline=1000ms boundary/recovery, duplicate timestamp rejected, metric freshness remains 200ms");
  $finish;
 end
 initial begin #100000000;$fatal(1,"test timeout");end
endmodule
