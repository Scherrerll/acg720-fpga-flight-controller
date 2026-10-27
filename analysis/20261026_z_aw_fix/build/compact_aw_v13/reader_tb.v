`timescale 1ns/1ps
`default_nettype none
module reader_tb;
 parameter MODE=0;
 localparam HZ=1152000,BIT=10;
 reg clk=0,rst_n=0,rx=1,hold=0;reg [63:0] uptime=0;
 always #5 clk=~clk;
 wire [975:0] diag0,diag1;
 wire [3:0] flags0,flags1;
 wire [31:0] dist0,dist1,dt0,dt1,age0,age1;
 wire signed [31:0] vx0,vx1,vy0,vy1;
 old_mtf01p_reader #(.CLOCK_HZ(HZ),.EXTERNAL_DIAGNOSTIC_HOLD(MODE),
  .DIAGNOSTIC_VERSION(MODE ? 3:1),.PHYSICAL_STOP_LOCK(!MODE),.CONTROL_PATH(MODE),
  .STARTUP_ONLY_DIAGNOSTIC_RESET(MODE)) d0(.clk(clk),.rst_n(rst_n),.rx(rx),.uptime_ms(uptime),.diagnostic_hold(hold),
  .diagnostic_body(diag0),.metric_sample_valid(flags0[0]),.metric_range_valid(flags0[1]),
  .metric_flow_valid(flags0[2]),.metric_interval_integrated(flags0[3]),.metric_distance_mm(dist0),
  .metric_dt_ms(dt0),.module_age_ms(age0),.metric_vx_x100(vx0),.metric_vy_x100(vy0));
 new_mtf01p_reader #(.CLOCK_HZ(HZ),.EXTERNAL_DIAGNOSTIC_HOLD(MODE),
  .DIAGNOSTIC_VERSION(MODE ? 3:1),.PHYSICAL_STOP_LOCK(!MODE),.CONTROL_PATH(MODE),
  .STARTUP_ONLY_DIAGNOSTIC_RESET(MODE)) d1(.clk(clk),.rst_n(rst_n),.rx(rx),.uptime_ms(uptime),.diagnostic_hold(hold),
  .diagnostic_body(diag1),.metric_sample_valid(flags1[0]),.metric_range_valid(flags1[1]),
  .metric_flow_valid(flags1[2]),.metric_interval_integrated(flags1[3]),.metric_distance_mm(dist1),
  .metric_dt_ms(dt1),.module_age_ms(age1),.metric_vx_x100(vx1),.metric_vy_x100(vy1));
 integer cycles=0,expiry200=0,expiry1000=0,restores=0,integrations=0,held=0;
 reg [31:0] last_age=32'hffffffff,rng=32'h12ecf39a;
 always @(negedge clk)begin
  rng=rng*32'd1664525+32'd1013904223;
  hold=(rng[3:0]<5);uptime=uptime+1'b1;
 end
 always @(posedge clk)begin
  cycles=cycles+1;#1;
  if({diag0,flags0,dist0,dt0,age0,vx0,vy0}!=={diag1,flags1,dist1,dt1,age1,vx1,vy1})
   $fatal(1,"reader public differential MODE=%0d cycle=%0d age=%h",MODE,cycles,age0);
  if(d1.age_below_1000!==(age0<1000) || d1.age_below_200!==(age0<200))
   $fatal(1,"same-age predicate MODE=%0d cycle=%0d age=%h",MODE,cycles,age0);
  if(d0.module_online!==d1.module_online || d0.link_fresh!==d1.link_fresh)
   $fatal(1,"internal freshness differential");
  if(last_age==199 && age0==200)begin
   if(d1.age_below_200 || d1.link_fresh || flags1[1] || flags1[2])$fatal(1,"extra 200ms freshness clock");
   expiry200=expiry200+1;
  end
  if(last_age==999 && age0==1000)begin
   if(d1.age_below_1000 || d1.module_online)$fatal(1,"extra 1000ms online clock");
   expiry1000=expiry1000+1;
  end
  if(last_age!=0 && age0==0)begin
   if(!d1.age_below_1000 || !d1.age_below_200)$fatal(1,"delayed publication freshness");
   restores=restores+1;
  end
  if(flags0[3])integrations=integrations+1;
  if(hold)held=held+1;
  last_age=age0;
  if(cycles>3500000)$fatal(1,"bounded UART differential timeout");
 end
 task clocks;input integer n;begin repeat(n)@(negedge clk);end endtask
 task tx_byte;input [7:0]b;input bad_stop;integer j;begin
  rx=0;clocks(BIT);
  for(j=0;j<8;j=j+1)begin rx=b[j];clocks(BIT);end
  rx=!bad_stop;clocks(BIT);rx=1;clocks(BIT);
 end endtask
 reg [7:0] frame[0:26];integer i,j;reg [7:0] checksum;
 task packet;input [31:0]stamp;input[7:0]seq;input corrupt;begin
  for(i=0;i<27;i=i+1)frame[i]=0;
  frame[0]=8'hef;frame[1]=1;frame[2]=0;frame[3]=8'h51;frame[4]=seq;frame[5]=20;
  frame[6]=stamp[7:0];frame[7]=stamp[15:8];frame[8]=stamp[23:16];frame[9]=stamp[31:24];
  frame[10]=8'he8;frame[11]=3;frame[14]=100;frame[15]=1;frame[16]=1;
  frame[18]=100;frame[20]=8'hce;frame[21]=8'hff;frame[22]=100;frame[23]=1;
  checksum=0;for(i=0;i<26;i=i+1)checksum=checksum+frame[i];frame[26]=checksum^corrupt;
  for(i=0;i<27;i=i+1)tx_byte(frame[i],0);
 end endtask
 initial begin
  clocks(8);rst_n=1;clocks(3000);
  if(age0!==32'hffffffff || d1.module_online || d1.link_fresh)$fatal(1,"unseeded age must remain saturated");
  packet(100,0,0);clocks(9000);packet(110,1,0);clocks(9000);packet(120,2,0);
  if(!d0.metric.integrated || vx0==0 || vy0==0)$fatal(1,"nonzero metric integration not exercised");
  packet(120,3,0);packet(130,4,1);
  tx_byte(8'h55,1);clocks(100);
  tx_byte(8'hef,0);tx_byte(1,0);tx_byte(0,0);tx_byte(8'h51,0);tx_byte(7,0);tx_byte(19,0);
  tx_byte(8'hef,0);clocks(8000);
  // Duplicate timestamps continue to arrive across the freshness threshold.
  for(j=0;j<30;j=j+1)begin packet(120,j+8,0);clocks(9000);end
  if(age0<200 || d1.link_fresh)$fatal(1,"duplicate timestamps refreshed age");
  while(age0<1001)clocks(100);
  if(expiry200!=1 || expiry1000!=1)$fatal(1,"first expiry coverage missing");
  packet(140,80,0);clocks(9000);packet(150,81,0);
  if(d0.metric.duplicates==0 || d0.checksum_errors==0 || d0.uart_errors==0 || d0.length_errors==0 || d0.timeouts==0)
   $fatal(1,"malformed/duplicate frame coverage missing");
  if(restores<4 || integrations==0 || held==0)$fatal(1,"publication/integration/hold coverage missing");
  clocks(500);rst_n=0;clocks(5);rst_n=1;clocks(10);
  if(age0!==32'hffffffff || d1.module_online || d1.link_fresh)$fatal(1,"reset age predicate mismatch");
  packet(7,0,0);clocks(50);
  $display("PASS UART MODE=%0d cycles=%0d public_bits=1140 expiry200=%0d expiry1000=%0d restores=%0d integrations=%0d hold_cycles=%0d no_DUT_force=1 CLOCK_HZ=%0d",MODE,cycles,expiry200,expiry1000,restores,integrations,held,HZ);
  $finish;
 end
endmodule
`default_nettype wire
