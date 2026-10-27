`timescale 1ns/1ps
`default_nettype none
module uart_reader_tb;
 parameter MODE=0;
 localparam HZ=1152000,BIT=10;
 reg clk=0,rst_n=0,rx=1,hold=0;reg [63:0] uptime=0;
 always #5 clk=~clk;
 wire [975:0] diag0,diag1;wire [3:0] flags0,flags1;
 wire [31:0] dist0,dist1,dt0,dt1,age0,age1;wire signed [31:0] vx0,vx1,vy0,vy1;wire predicate;
 old_mtf01p_reader #(.CLOCK_HZ(HZ),.EXTERNAL_DIAGNOSTIC_HOLD(MODE),
  .DIAGNOSTIC_VERSION(MODE ?3:1),.PHYSICAL_STOP_LOCK(!MODE),.CONTROL_PATH(MODE),.STARTUP_ONLY_DIAGNOSTIC_RESET(MODE)) d0(
  .clk(clk),.rst_n(rst_n),.rx(rx),.uptime_ms(uptime),.diagnostic_hold(hold),.diagnostic_body(diag0),
  .metric_sample_valid(flags0[0]),.metric_range_valid(flags0[1]),.metric_flow_valid(flags0[2]),.metric_interval_integrated(flags0[3]),
  .metric_distance_mm(dist0),.metric_dt_ms(dt0),.module_age_ms(age0),.metric_vx_x100(vx0),.metric_vy_x100(vy0));
 new_mtf01p_reader #(.CLOCK_HZ(HZ),.EXTERNAL_DIAGNOSTIC_HOLD(MODE),
  .DIAGNOSTIC_VERSION(MODE ?3:1),.PHYSICAL_STOP_LOCK(!MODE),.CONTROL_PATH(MODE),.STARTUP_ONLY_DIAGNOSTIC_RESET(MODE)) d1(
  .clk(clk),.rst_n(rst_n),.rx(rx),.uptime_ms(uptime),.diagnostic_hold(hold),.diagnostic_body(diag1),
  .metric_sample_valid(flags1[0]),.metric_range_valid(flags1[1]),.metric_flow_valid(flags1[2]),.metric_interval_integrated(flags1[3]),
  .metric_distance_mm(dist1),.metric_dt_ms(dt1),.module_age_ms(age1),.metric_vx_x100(vx1),.metric_vy_x100(vy1),.metric_velocity_range_ok(predicate));
 integer cycles=0,expiry200=0,expiry1000=0,restores=0,integrations=0,held=0,commits=0,invalid_zero=0,stale_holds=0;
 reg [31:0] last_age=32'hffffffff,rng=32'h12ecf39a;reg [11:0] boundaries=0;
 reg signed [63:0] expected_x,expected_y;
 reg [64:0] previous_tuple=65'd1;
 always @(negedge clk)begin rng=rng*32'd1664525+32'd1013904223;hold=(rng[3:0]<5);uptime=uptime+1'b1;end
 always @(posedge clk)begin
  cycles=cycles+1;#1;
  if({diag0,flags0,dist0,dt0,age0,vx0,vy0}!=={diag1,flags1,dist1,dt1,age1,vx1,vy1})
   $fatal(1,"UART public differential MODE=%0d cycle=%0d age=%h",MODE,cycles,age0);
  if(predicate!==(vx1>=-32'sd1000000 && vx1<=32'sd1000000 && vy1>=-32'sd1000000 && vy1<=32'sd1000000))
   $fatal(1,"UART same-published-word predicate mismatch MODE=%0d cycle=%0d",MODE,cycles);
  if(d0.module_online!==d1.module_online || d0.link_fresh!==d1.link_fresh)$fatal(1,"UART freshness mismatch");
  if(last_age==199 && age0==200)begin
   if(d1.link_fresh || flags1[1] || flags1[2])$fatal(1,"UART extra 200ms freshness clock");expiry200=expiry200+1;
  end
  if(last_age==999 && age0==1000)begin if(d1.module_online)$fatal(1,"UART extra 1000ms online clock");expiry1000=expiry1000+1;end
  if(last_age!=0 && age0==0)restores=restores+1;
  if(flags1[0])begin
   commits=commits+1;
   // The reader intentionally admits a validated frame on its commit after stale gaps.
   // Independent full-distance signed64 oracle uses decoded inputs, never DUT products.
   if(d1.tof_status==1 && dist1>=80 && dist1<=12000 && d1.flow_status==1 && d1.quality!=0)begin
    expected_x=$signed({{48{d1.flow_x[15]}},d1.flow_x})*$signed({32'd0,dist1});
    expected_y=$signed({{48{d1.flow_y[15]}},d1.flow_y})*$signed({32'd0,dist1});
   end else begin expected_x=0;expected_y=0;invalid_zero=invalid_zero+1;end
   if($signed({{32{vx1[31]}},vx1})!==expected_x || $signed({{32{vy1[31]}},vy1})!==expected_y ||
      predicate!==(expected_x>=-64'sd1000000 && expected_x<=64'sd1000000 && expected_y>=-64'sd1000000 && expected_y<=64'sd1000000))
    $fatal(1,"UART independent signed64 oracle MODE=%0d vx=%0d vy=%0d expected=%0d/%0d",MODE,vx1,vy1,expected_x,expected_y);
  end
  if(rst_n && !d1.sample_valid && !flags1[0] && age1>=200 && last_age>=200)begin
   if({vx1,vy1,predicate}!==previous_tuple)$fatal(1,"UART stale tuple changed without publication");stale_holds=stale_holds+1;
  end
  case(vx1)999999:boundaries[0]=1;-999999:boundaries[1]=1;1000000:boundaries[2]=1;-1000000:boundaries[3]=1;1000001:boundaries[4]=1;-1000001:boundaries[5]=1;endcase
  case(vy1)999999:boundaries[6]=1;-999999:boundaries[7]=1;1000000:boundaries[8]=1;-1000000:boundaries[9]=1;1000001:boundaries[10]=1;-1000001:boundaries[11]=1;endcase
  if(flags0[3])integrations=integrations+1;if(hold)held=held+1;last_age=age0;previous_tuple={vx1,vy1,predicate};
  if(cycles>3500000)$fatal(1,"bounded UART timeout");
 end
 task clocks;input integer n;begin repeat(n)@(negedge clk);end endtask
 task tx_byte;input[7:0]b;input bad_stop;integer j;begin
  rx=0;clocks(BIT);for(j=0;j<8;j=j+1)begin rx=b[j];clocks(BIT);end
  rx=!bad_stop;clocks(BIT);rx=1;clocks(BIT);
 end endtask
 reg [31:0] packet_distance=1000;reg signed[15:0] packet_x=100,packet_y=-50;
 reg [7:0] packet_tof=1,packet_quality=100,packet_flow=1;
 reg [7:0] frame[0:26];integer i,j;reg [7:0] checksum;
 task packet;input[31:0]stamp;input[7:0]seq;input corrupt;begin
  for(i=0;i<27;i=i+1)frame[i]=0;
  frame[0]=8'hef;frame[1]=1;frame[2]=0;frame[3]=8'h51;frame[4]=seq;frame[5]=20;
  frame[6]=stamp[7:0];frame[7]=stamp[15:8];frame[8]=stamp[23:16];frame[9]=stamp[31:24];
  frame[10]=packet_distance[7:0];frame[11]=packet_distance[15:8];frame[12]=packet_distance[23:16];frame[13]=packet_distance[31:24];
  frame[14]=100;frame[15]=1;frame[16]=packet_tof;
  frame[18]=packet_x[7:0];frame[19]=packet_x[15:8];frame[20]=packet_y[7:0];frame[21]=packet_y[15:8];frame[22]=packet_quality;frame[23]=packet_flow;
  checksum=0;for(i=0;i<26;i=i+1)checksum=checksum+frame[i];frame[26]=checksum^corrupt;
  for(i=0;i<27;i=i+1)tx_byte(frame[i],0);
 end endtask
 reg[31:0]stamp=200;reg[7:0]seq=90;
 task boundary_packet;input[31:0]d;input signed[15:0]fx,fy;begin
  packet_distance=d;packet_x=fx;packet_y=fy;stamp=stamp+10;seq=seq+1'b1;packet(stamp,seq,0);clocks(50);
 end endtask
 initial begin
  clocks(8);rst_n=1;clocks(3000);
  if(age0!==32'hffffffff || d1.module_online || d1.link_fresh || !predicate)$fatal(1,"UART initial state");
  packet(100,0,0);clocks(9000);packet(110,1,0);clocks(9000);packet(120,2,0);
  if(!d0.metric.integrated || vx0==0 || vy0==0)$fatal(1,"UART integration not exercised");
  packet(120,3,0);packet(130,4,1);tx_byte(8'h55,1);clocks(100);
  tx_byte(8'hef,0);tx_byte(1,0);tx_byte(0,0);tx_byte(8'h51,0);tx_byte(7,0);tx_byte(19,0);tx_byte(8'hef,0);clocks(8000);
  for(j=0;j<30;j=j+1)begin packet(120,j+8,0);clocks(9000);end
  if(age0<200 || d1.link_fresh)$fatal(1,"UART duplicates refreshed freshness");
  while(age0<1001)clocks(100);
  if(expiry200!=1 || expiry1000!=1)$fatal(1,"UART expiry coverage missing");
  packet(140,80,0);clocks(9000);packet(150,81,0);
  boundary_packet(99,10101,0);boundary_packet(99,-10101,0);boundary_packet(99,0,10101);boundary_packet(99,0,-10101);
  boundary_packet(100,10000,0);boundary_packet(100,-10000,0);boundary_packet(100,0,10000);boundary_packet(100,0,-10000);
  boundary_packet(101,9901,0);boundary_packet(101,-9901,0);boundary_packet(101,0,9901);boundary_packet(101,0,-9901);
  // Same timestamp with changed velocity must still publish the new predicate.
  packet_distance=100;packet_x=10000;packet_y=0;packet(stamp,seq,0);clocks(50);
  packet_distance=101;packet_x=9901;packet(stamp,seq,0);clocks(50);if(predicate)$fatal(1,"UART duplicate velocity predicate not published");
  boundary_packet(80,-32768,32767);boundary_packet(12000,32767,-32768);
  boundary_packet(0,-32768,32767);boundary_packet(79,32767,-32768);boundary_packet(12001,32767,-32768);
  boundary_packet(32'h80000050,-32768,32767);boundary_packet(32'hffffffff,32767,-32768);
  packet_quality=0;boundary_packet(101,9901,-9901);packet_quality=100;packet_tof=0;boundary_packet(100,10000,-10000);packet_tof=1;
  packet_flow=0;boundary_packet(99,10101,-10101);packet_flow=1;
  if(d0.metric.duplicates==0 || d0.checksum_errors==0 || d0.uart_errors==0 || d0.length_errors==0 || d0.timeouts==0)$fatal(1,"UART error coverage missing");
  if(restores<4 || integrations==0 || held==0 || boundaries!==12'hfff || invalid_zero<8 || stale_holds<1000)$fatal(1,"UART coverage incomplete boundaries=%h invalid=%0d stale=%0d",boundaries,invalid_zero,stale_holds);
  clocks(500);rst_n=0;clocks(5);rst_n=1;clocks(10);
  if(age0!==32'hffffffff || d1.module_online || d1.link_fresh || !predicate || vx1!==0 || vy1!==0)$fatal(1,"UART reset tuple mismatch");
  packet(7,0,0);clocks(50);
  $display("PASS UART MODE=%0d cycles=%0d public_bits=1140 new_predicate_invariant=1 independent_signed64=1 expiry200=%0d expiry1000=%0d commits=%0d boundaries=%h invalid_zero=%0d stale_hold_cycles=%0d no_DUT_force=1 CLOCK_HZ=%0d",MODE,cycles,expiry200,expiry1000,commits,boundaries,invalid_zero,stale_holds,HZ);$finish;
 end
endmodule
`default_nettype wire
