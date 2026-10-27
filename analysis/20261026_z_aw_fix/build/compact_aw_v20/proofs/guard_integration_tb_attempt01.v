`timescale 1ns/1ps
// Actual producers + merged navigation consumer. Ordinary input stimulus only.
module nav_guard #(parameter integer ON=1)(
 input clk,rst_n,cancel,au,av,sample,rv,fv,zok,vok,
 input [31:0] adt,distance,dt,
 input signed [31:0] az,vx,vy,
 output az_gate,height_az_gate,velocity_gate
);
 mtf_xyz_navigation_control #(.PRECHECKED_AZ_RANGE(ON),.PRECHECKED_INPUT_VELOCITY(ON)) dut(
  .clk(clk),.rst_n(rst_n),.origin_reset(cancel),.diagnostic_hold(1'b0),
  .xy_p_value(16'd1000),.xy_i_value(16'd350),.height_origin_ok(1'b1),
  .sample_valid(sample),.range_valid(rv),.flow_valid(fv),.distance_mm(distance),.dt_ms(dt),.source_age_ms(32'd0),
  .vx_x100(vx),.vy_x100(vy),.velocity_range_ok(ON ?vok:~vok),
  .pose_valid(1'b1),.roll_cdeg(16'sd0),.pitch_cdeg(16'sd0),.yaw_cdeg(16'sd0),.yaw_range_ok(1'b1),
  .acc_valid(av),.acc_update(au),.acc_dt_us(adt),.az_range_ok(ON ?zok:~zok),
  .ax_mmps2(32'sd0),.ay_mmps2(32'sd0),.az_up_mmps2(az),
  .rc_valid(1'b0),.enabled(1'b0),.taking_off(1'b0),.channel_count(4'd8),
  .ch1(16'd1500),.ch2(16'd1500),.ch3(16'd1000),.ch4(16'd1500),.ch7(16'd1000),.collective_us(16'd1000),
  .uptime_ms(64'd0),.height_tilt4500_ok(1'b1),.flow_tilt1500_ok(1'b1));
 assign az_gate=dut.live_az_range_ok;
 assign height_az_gate=dut.height_fusion.az_numeric_ok;
 assign velocity_gate=dut.geometry.input_velocity_ok;
endmodule

module guard_integration_tb;
 reg clk=0;always #10 clk=~clk;
 reg rst_n=0,cancel=0,start=0,acc_valid=1;
 reg signed [31:0] az_in=0;reg [31:0] ticks=550000;
 wire update,valid,busy,zok;wire [31:0] adt;wire signed [31:0] az;wire [7:0] fault;
 pose_time_adapter adapter(.clk(clk),.rst_n(rst_n),.cancel(cancel),.start(start),.acc_valid(acc_valid),.ticks(ticks),
  .ax(32'sd0),.ay(32'sd0),.az(az_in),.update(update),.dt_us(adt),.output_ax(),.output_ay(),.output_az(az),
  .output_az_range_ok(zok),.output_acc_valid(valid),.busy(busy),.fault(fault));
 reg sample=0,link=1;reg [31:0] time_ms=100,distance=1000;reg [7:0] seq=0,tof=1,flow=1,quality=1;
 reg signed [15:0] flow_x=0,flow_y=0;
 wire rv,fv,vok;wire [31:0] dt;wire signed [31:0] vx,vy;
 mtf_metric_observer metric(.clk(clk),.rst_n(rst_n),.sample_valid(sample),.link_fresh(link),
  .time_ms(time_ms),.distance_mm(distance),.module_seq(seq),.tof_status(tof),.flow_status(flow),.quality(quality),
  .flow_x(flow_x),.flow_y(flow_y),.range_numeric_ok(rv),.flow_numeric_ok(fv),.dt_ms(dt),
  .vx_x100(vx),.vy_x100(vy),.velocity_range_ok(vok));
 wire onaz,onheight,onvel,defaz,defheight,defvel;
 nav_guard #(.ON(1)) enabled(clk,rst_n,cancel,update,valid,sample,rv,fv,zok,vok,adt,distance,dt,az,vx,vy,onaz,onheight,onvel);
 nav_guard #(.ON(0)) defaults(clk,rst_n,cancel,update,valid,sample,rv,fv,zok,vok,adt,distance,dt,az,vx,vy,defaz,defheight,defvel);
 integer cycles=0,publications=0,metric_publications=0,checks=0,n;reg [3:0] combinations=0;
 wire az_numeric=az>=-30000 && az<=30000;
 wire velocity_numeric=vx>=-1000000 && vx<=1000000 && vy>=-1000000 && vy<=1000000;
 always @(posedge clk)begin
  #2;cycles=cycles+1;
  if(zok!==az_numeric || vok!==velocity_numeric)$fatal(1,"producer tuple predicate mismatch");
  if(onaz!==zok || onheight!==zok || onvel!==vok)$fatal(1,"merged enabled consumer route mismatch");
  if(defaz!==az_numeric || defheight!==az_numeric || defvel!==velocity_numeric)$fatal(1,"default-off consumer used deliberately wrong supplied predicate");
  checks=checks+1;
  if(rst_n && (^ {zok,vok})!==1'bx)combinations[{zok,vok}]=1;
  if(update)publications=publications+1;if(sample)metric_publications=metric_publications+1;
 end
 task clocks;input integer count;integer k;begin for(k=0;k<count;k=k+1)@(negedge clk);end endtask
 task metric_publish;input signed [15:0] x,y;input [31:0] dist;begin
  flow_x=x;flow_y=y;distance=dist;sample=1;clocks(1);sample=0;clocks(2);
 end endtask
 task az_publish;input signed [31:0] value;begin
  az_in=value;start=1;clocks(1);start=0;az_in=32'sh76543210;clocks(34);
  if(busy || fault || az!==value)$fatal(1,"AZ ordinary publication failed");
 end endtask
 reg signed [31:0] held_az,held_vx,held_vy;reg held_zok,held_vok;
 initial begin
  clocks(4);rst_n=1;clocks(3);
  for(n=0;n<8;n=n+1)begin
   time_ms=time_ms+10;seq=seq+1;link=1;quality=1;tof=1;flow=1;
   metric_publish(n[0] ?16'sd1001:16'sd1000,-16'sd1000,1000);
   az_publish(n[1] ?32'sd30001:32'sd30000);
  end
  az_publish(-32'sd30000);metric_publish(-16'sd1000,16'sd1000,1000);
  az_publish(-32'sd30001);metric_publish(-16'sd1001,16'sd1000,1000);
  held_az=az;held_zok=zok;held_vx=vx;held_vy=vy;held_vok=vok;
  link=0;flow_x=32767;flow_y=-32768;az_in=0;clocks(7);
  if({az,zok,vx,vy,vok}!=={held_az,held_zok,held_vx,held_vy,held_vok})$fatal(1,"no-publication hold/link-loss mismatch");
  link=1;metric_publish(32767,-32768,32'h800003e8);
  if(vx!==0 || vy!==0 || vok!==1)$fatal(1,"full32 invalid distance did not publish zero/true");
  metric_publish(32767,-32768,12000);quality=0;metric_publish(32767,-32768,12000);
  if(vx!==0 || vy!==0 || vok!==1)$fatal(1,"invalid quality publication mismatch");
  quality=1;metric_publish(1001,-1001,1000);metric_publish(1000,-1000,1000);
  az_in=7;start=1;clocks(1);start=0;clocks(3);start=1;clocks(1);start=0;clocks(2);
  if(fault!==1 || valid!==0)$fatal(1,"busy overlap did not retain original fault/valid behavior");
  cancel=1;clocks(1);cancel=0;clocks(2);
  if(az!==0 || zok!==1 || fault!==0)$fatal(1,"AZ cancel tuple mismatch");
  rst_n=0;clocks(2);rst_n=1;clocks(2);
  if(az!==0 || zok!==1 || vx!==0 || vy!==0 || vok!==1)$fatal(1,"reset tuples mismatch");
  if(combinations!==4'b1111 || publications<10 || metric_publications<15 || checks<300)$fatal(1,"insufficient combined finite coverage");
  $display("PASS combined_guard cycles=%0d checks=%0d AZ_publications=%0d metric_publications=%0d combinations=%b default_wrong_flags_ignored=1 no_DUT_force_preload=1",cycles,checks,publications,metric_publications,combinations);$finish;
 end
 initial begin #1000000;$fatal(1,"combined guard test timeout");end
endmodule
