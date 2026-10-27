`timescale 1ns/1ps
`default_nettype none
module metric_tb;
 reg clk=0;always #5 clk=~clk;
 reg rst_n=0,sample_valid=0,link_fresh=0;
 reg [31:0] time_ms=0,distance_mm=0;reg [7:0] module_seq=0,tof_status=1,flow_status=1,quality=100;
 reg signed [15:0] flow_x=0,flow_y=0;
 wire range0,range1,flow0,flow1,integrated0,integrated1,saturated0,saturated1,predicate;
 wire [31:0] dt0,dt1,missing0,missing1,duplicates0,duplicates1,restarts0,restarts1,breaks0,breaks1;
 wire signed [31:0] vx0,vx1,vy0,vy1;wire signed [63:0] x0,x1,y0,y1;
 old_mtf_metric_observer old(.clk(clk),.rst_n(rst_n),.sample_valid(sample_valid),.link_fresh(link_fresh),
  .time_ms(time_ms),.distance_mm(distance_mm),.module_seq(module_seq),.tof_status(tof_status),.flow_status(flow_status),.quality(quality),.flow_x(flow_x),.flow_y(flow_y),
  .range_numeric_ok(range0),.flow_numeric_ok(flow0),.dt_ms(dt0),.missing(missing0),.duplicates(duplicates0),.restarts(restarts0),.integration_breaks(breaks0),
  .vx_x100(vx0),.vy_x100(vy0),.x_x100000(x0),.y_x100000(y0),.integrated(integrated0),.saturated(saturated0));
 new_mtf_metric_observer dut(.clk(clk),.rst_n(rst_n),.sample_valid(sample_valid),.link_fresh(link_fresh),
  .time_ms(time_ms),.distance_mm(distance_mm),.module_seq(module_seq),.tof_status(tof_status),.flow_status(flow_status),.quality(quality),.flow_x(flow_x),.flow_y(flow_y),
  .range_numeric_ok(range1),.flow_numeric_ok(flow1),.dt_ms(dt1),.missing(missing1),.duplicates(duplicates1),.restarts(restarts1),.integration_breaks(breaks1),
  .vx_x100(vx1),.vy_x100(vy1),.velocity_range_ok(predicate),.x_x100000(x1),.y_x100000(y1),.integrated(integrated1),.saturated(saturated1));
 integer cycles=0,samples=0,holds=0,resets=0,invalid_zero=0,unknown_trials=0,below=0,edge_value=0,outside=0;
 reg signed [63:0] expected_x=0,expected_y=0;
 reg expected_known=1,expected_predicate=1;
 reg [31:0] rng=32'hc05693a1;
 reg [95:0] previous_tuple=0;
 always @(posedge clk)begin
  cycles=cycles+1;
  if(!rst_n)begin expected_x=0;expected_y=0;expected_known=1;resets=resets+1;end
  else if(sample_valid)begin
   samples=samples+1;
   expected_known=!$isunknown({distance_mm,tof_status,flow_status,quality,link_fresh,flow_x,flow_y});
   if(expected_known)begin
    // Independent full-distance signed64 oracle; no DUT products or validity wires.
    if(link_fresh && tof_status==1 && distance_mm>=80 && distance_mm<=12000 && flow_status==1 && quality!=0)begin
     expected_x=$signed({{48{flow_x[15]}},flow_x})*$signed({32'd0,distance_mm});
     expected_y=$signed({{48{flow_y[15]}},flow_y})*$signed({32'd0,distance_mm});
    end else begin expected_x=0;expected_y=0;invalid_zero=invalid_zero+1;end
   end else unknown_trials=unknown_trials+1;
  end else holds=holds+1;
  expected_predicate=expected_x>=-64'sd1000000 && expected_x<=64'sd1000000 && expected_y>=-64'sd1000000 && expected_y<=64'sd1000000;
  #1;
  if({range0,flow0,dt0,missing0,duplicates0,restarts0,breaks0,vx0,vy0,x0,y0,integrated0,saturated0} !==
     {range1,flow1,dt1,missing1,duplicates1,restarts1,breaks1,vx1,vy1,x1,y1,integrated1,saturated1})
   $fatal(1,"metric actual old/new mismatch cycle=%0d",cycles);
  if(predicate !== (vx1>=-32'sd1000000 && vx1<=32'sd1000000 && vy1>=-32'sd1000000 && vy1<=32'sd1000000))
   $fatal(1,"metric same-word predicate invariant cycle=%0d vx=%h vy=%h predicate=%b",cycles,vx1,vy1,predicate);
  if(expected_known && ($signed({{32{vx1[31]}},vx1})!==expected_x || $signed({{32{vy1[31]}},vy1})!==expected_y || predicate!==expected_predicate))
   $fatal(1,"independent signed64 oracle mismatch cycle=%0d expected=%0d/%0d actual=%0d/%0d",cycles,expected_x,expected_y,vx1,vy1);
  if(vx1==999999 || vx1==-999999 || vy1==999999 || vy1==-999999)below=below+1;
  if(vx1==1000000 || vx1==-1000000 || vy1==1000000 || vy1==-1000000)edge_value=edge_value+1;
  if(vx1==1000001 || vx1==-1000001 || vy1==1000001 || vy1==-1000001)outside=outside+1;
 end
 task tick;begin @(negedge clk);end endtask
 task publish;input [31:0] d;input signed[15:0] fx,fy;begin
  distance_mm=d;flow_x=fx;flow_y=fy;sample_valid=1;time_ms=time_ms+10;module_seq=module_seq+1'b1;tick();
 end endtask
 integer k,j;
 function [31:0] sweep_distance;input integer j;begin case(j)
  0:sweep_distance=80;1:sweep_distance=99;2:sweep_distance=100;3:sweep_distance=101;
  4:sweep_distance=1000;5:sweep_distance=11999;default:sweep_distance=12000;
 endcase end endfunction
 initial begin
  repeat(4)tick();rst_n=1;link_fresh=1;
  // Every signed16 value on each axis at both numeric range ends and threshold factors.
  for(j=0;j<7;j=j+1)for(k=0;k<65536;k=k+1)publish(sweep_distance(j),k[15:0],~k[15:0]);
  publish(99,10101,0);publish(99,-10101,0);publish(99,0,10101);publish(99,0,-10101);
  publish(100,10000,0);publish(100,-10000,0);publish(100,0,10000);publish(100,0,-10000);
  publish(101,9901,0);publish(101,-9901,0);publish(101,0,9901);publish(101,0,-9901);
  // Duplicate timestamp still publishes changed words and predicate; sequence gaps/restarts unchanged.
  distance_mm=100;flow_x=10000;flow_y=0;sample_valid=1;tick();
  distance_mm=101;flow_x=9901;tick();flow_x=0;flow_y=-9901;tick();
  sample_valid=0;link_fresh=0;distance_mm=100;flow_x=0;flow_y=0;repeat(9)tick();
  sample_valid=1;tick();link_fresh=1;publish(12000,-32768,32767);
  publish(0,-32768,32767);publish(79,32767,-32768);publish(12001,-32768,32767);
  publish(32'h00004050,32767,-32768);publish(32'h80000050,-32768,32767);publish(32'hffffffff,-32768,32767);
  tof_status=0;publish(100,10000,-10000);tof_status=1;quality=0;publish(101,9901,9901);quality=100;
  flow_status=0;publish(100,10000,-10000);flow_status=1;
  time_ms=32'hfffffff9;publish(100,1,-1);publish(101,1,-1);time_ms=0;publish(99,1,-1);
  for(k=0;k<20000;k=k+1)begin
   rng=rng*32'd1664525+32'd1013904223;
   sample_valid=rng[0];link_fresh=rng[1];rst_n=(k%997)!=0;
   tof_status=rng[3] ?1:0;flow_status=rng[4] ?1:0;quality=rng[5] ?100:0;
   flow_x=rng[31:16];flow_y=rng[15:0];distance_mm=rng[6] ?rng[21:8]:rng;
   if(rng[7])time_ms=time_ms+10;module_seq=module_seq+rng[10:8];tick();
  end
  rst_n=1;sample_valid=1;link_fresh=1;tof_status=1;flow_status=1;quality=100;
  distance_mm=100;flow_x=10000;flow_y=0;tick();
  // Four-state ternary merging and Verilog if semantics must match exact published words.
  quality=8'bx;tick();quality=100;link_fresh=1'bx;flow_x=10001;tick();
  link_fresh=1;flow_x=16'bx;tick();sample_valid=1'bx;distance_mm=80;flow_x=12500;tick();
  sample_valid=0;rst_n=1'bx;tick();rst_n=0;tick();rst_n=1;sample_valid=0;repeat(3)tick();
  if(samples<458752 || holds<100 || invalid_zero<100 || unknown_trials<3 || below<4 || edge_value<4 || outside<4 || resets<5 || duplicates1==32'hxxxxxxxx)
   $fatal(1,"metric coverage missing samples=%0d holds=%0d invalid=%0d x=%0d boundary=%0d/%0d/%0d",samples,holds,invalid_zero,unknown_trials,below,edge_value,outside);
  $display("PASS metric actual_old_new=1 independent_signed64=1 exhaustive_signed16_distances=7 samples=%0d cycles=%0d holds=%0d invalid_zero=%0d unknown_payload_trials=%0d boundaries=%0d/%0d/%0d no_DUT_force=1",samples,cycles,holds,invalid_zero,unknown_trials,below,edge_value,outside);$finish;
 end
 initial begin #10000000;$fatal(1,"metric timeout");end
endmodule
`default_nettype wire
