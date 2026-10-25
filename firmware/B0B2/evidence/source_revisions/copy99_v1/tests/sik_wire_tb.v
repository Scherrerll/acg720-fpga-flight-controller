`timescale 1ns/1ps
module sik_wire_tb;
 reg clk=0;always #10 clk=~clk;
 reg [863:0] core_body=0;reg [887:0] extension=0;reg [215:0] acceleration_body=0;
 reg [343:0] range_diagnostic_body=0;reg [335:0] rotation_body=0;
 reg [271:0] flight_info_body=0;reg [975:0] mtf_body=0;reg [719:0] nav_body=0;
 reg [511:0] diagnostic_body=0;reg [31:0] diagnostic_tick=32'h12345678;
 wire tx,golden_tx,hold_new,hold_golden;
 telemetry_tx #(.DIAGNOSTIC_INFO(1),.ROTATION_INFO(1),.PERIOD(100),.MTF_INFO(1),.MTF_CALLER_SNAPSHOT(1),.INFO_CALLER_SNAPSHOT(1),.NAV_INFO(1),.NAV_CALLER_SNAPSHOT(1),.FLIGHT_INFO(1),.EXTERNAL_SNAPSHOT(1)) d(.clk(clk),.core_body(core_body),.extension(extension),.acceleration_body(acceleration_body),.range_diagnostic_body(range_diagnostic_body),.rotation_body(rotation_body),.flight_info_body(flight_info_body),.mtf_body(mtf_body),.nav_body(nav_body),.diagnostic_body(diagnostic_body),.diagnostic_tick(diagnostic_tick),.tx(tx),.snapshot_hold(hold_new));
 telemetry_tx_golden #(.ROTATION_INFO(1),.PERIOD(100),.MTF_INFO(1),.MTF_CALLER_SNAPSHOT(1),.INFO_CALLER_SNAPSHOT(1),.NAV_INFO(1),.NAV_CALLER_SNAPSHOT(1),.FLIGHT_INFO(1),.EXTERNAL_SNAPSHOT(1)) g(.clk(clk),.core_body(core_body),.extension(extension),.acceleration_body(acceleration_body),.range_diagnostic_body(range_diagnostic_body),.rotation_body(rotation_body),.flight_info_body(flight_info_body),.mtf_body(mtf_body),.nav_body(nav_body),.tx(golden_tx),.snapshot_hold(hold_golden));
 integer f,gf,i;reg [4095:0] path,gpath;reg [7:0] b,gb;
 initial begin
  if(!$value$plusargs("WIRE=%s",path) || !$value$plusargs("GOLDEN=%s",gpath))$fatal(1,"output paths");
  f=$fopen(path,"w");gf=$fopen(gpath,"w");
  for(i=0;i<108;i=i+1)core_body[863-i*8-:8]=i;
  for(i=0;i<111;i=i+1)extension[887-i*8-:8]=i+7;
  for(i=0;i<27;i=i+1)acceleration_body[215-i*8-:8]=i+19;
  for(i=0;i<42;i=i+1)rotation_body[335-i*8-:8]=i+23;
  for(i=0;i<34;i=i+1)flight_info_body[271-i*8-:8]=i+41;
  for(i=0;i<122;i=i+1)mtf_body[975-i*8-:8]=i+53;
  for(i=0;i<90;i=i+1)nav_body[719-i*8-:8]=i+61;
  // Legal B0B2 A585 payload; legacy payload deliberately arbitrary to prove bytes.
  diagnostic_body={64'h0102030405060708,32'hb0b2,32'd100,32'd90,32'd80,32'd7,32'd3000000,32'd89,32'd50000,32'd2000000,
    8'h40,8'h80,8'h20,8'h0f,8'd4,8'd1,8'd0,8'd0,32'd123456,8'h32,8'h04,8'h80,8'd4,32'd3000000};
 end
 task read_new;begin
  @(negedge tx);repeat(217)@(posedge clk);#1;if(tx!==0)$fatal(1,"new start");
  for(integer j=0;j<8;j=j+1)begin repeat(434)@(posedge clk);#1;b[j]=tx;end
  repeat(434)@(posedge clk);#1;if(tx!==1)$fatal(1,"new stop");
  $fdisplay(f,"%02x",b);
 end endtask
 task read_golden;begin
  @(negedge golden_tx);repeat(217)@(posedge clk);#1;if(golden_tx!==0)$fatal(1,"old start");
  for(integer j=0;j<8;j=j+1)begin repeat(434)@(posedge clk);#1;gb[j]=golden_tx;end
  repeat(434)@(posedge clk);#1;if(golden_tx!==1)$fatal(1,"old stop");
  $fdisplay(gf,"%02x",gb);
 end endtask
 initial begin wait(f!=0);repeat(644)read_new;$fclose(f);$display("PASS sik_wire 644 sampled bytes");#100;$finish;end
 initial begin wait(gf!=0);repeat(568)read_golden;$fclose(gf);end
 initial begin #100000000;$fatal(1,"wire timeout");end
endmodule
