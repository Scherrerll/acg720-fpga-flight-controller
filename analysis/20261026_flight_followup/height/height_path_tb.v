`timescale 1ns/1ps
// Constructed source tuples, not a replay of unrecorded 100Hz/1kHz flight data.
// Real metric observer, adapter, complete navigation math/FSM and fallback.
module height_path_tb;
 reg clk=0;always #10 clk=~clk;
 reg rst_n=0;integer cycle=0,scenario=0;
 reg pose_start=0,mtf_sample=0;
 reg [31:0] module_time=0;reg [7:0] module_seq=0;
 reg signed [31:0] input_az=0;
 reg [31:0] distance=250;
 reg [15:0] ch3=1500;
 wire acc_update,converted_valid,adapter_busy;wire [7:0] adapter_fault;
 wire [31:0] acc_dt;wire signed [31:0] ax,ay,az;
 pose_time_adapter adapter(.clk(clk),.rst_n(rst_n),.cancel(1'b0),.start(pose_start),.acc_valid(1'b1),
  .ticks(32'd50000),.ax(32'sd0),.ay(32'sd0),.az(input_az),.update(acc_update),.dt_us(acc_dt),
  .output_ax(ax),.output_ay(ay),.output_az(az),.output_acc_valid(converted_valid),.busy(adapter_busy),.fault(adapter_fault));
 wire range_ok,flow_ok,integrated,saturated;wire [31:0] dt_ms,missing,duplicates,restarts,breaks;
 wire signed [31:0] vx100,vy100;wire signed [63:0] ix,iy;
 mtf_metric_observer metric(.clk(clk),.rst_n(rst_n),.sample_valid(mtf_sample),.link_fresh(1'b1),
  .time_ms(module_time),.distance_mm(distance),.module_seq(module_seq),.tof_status(8'd1),.flow_status(8'd1),.quality(8'd100),
  .flow_x(16'sd0),.flow_y(16'sd0),.range_numeric_ok(range_ok),.flow_numeric_ok(flow_ok),
  .dt_ms(dt_ms),.missing(missing),.duplicates(duplicates),.restarts(restarts),.integration_breaks(breaks),
  .vx_x100(vx100),.vy_x100(vy100),.x_x100000(ix),.y_x100000(iy),.integrated(integrated),.saturated(saturated));
 reg metric_commit=0;always @(posedge clk)if(!rst_n)metric_commit<=0;else metric_commit<=mtf_sample;
 wire height_ready,core_tail,core_tail_noacc,core_state_tail;
 wire native_acc_valid=converted_valid && adapter_fault==0;
 wire available=core_state_tail && range_ok && native_acc_valid;
 wire fallback_active,fallback_latched,fallback_ready;
 wire [15:0] fallback_collective,z_collective,z_reason;
 wire z_active;wire [719:0] diagnostics;
 wire parameter_boundary;
 mtf_xyz_navigation_control #(.PROOF_CONTROLLER(1),.PRECHECKED_YAW_RANGE(1),
  .PRECHECKED_HEIGHT_TILT4500(1),.PRECHECKED_FLOW_TILT1500(1),.PRECHECKED_HEIGHT_ORIGIN(1)) nav(
  .clk(clk),.rst_n(rst_n),.origin_reset(1'b0),.diagnostic_hold(1'b0),.height_origin_ok(1'b1),
  .xy_p_value(16'd500),.xy_i_value(16'd0),.parameter_boundary(parameter_boundary),
  .sample_valid(metric_commit),.range_valid(range_ok),.flow_valid(flow_ok && integrated),
  .distance_mm(distance),.dt_ms(dt_ms),.source_age_ms(32'd0),.vx_x100(vx100),.vy_x100(vy100),
  .pose_valid(1'b1),.roll_cdeg(16'sd0),.pitch_cdeg(16'sd0),.yaw_cdeg(16'sd0),.yaw_range_ok(1'b1),
  .height_tilt4500_ok(1'b1),.flow_tilt1500_ok(1'b1),
  .acc_valid(native_acc_valid),.acc_update(acc_update),.acc_dt_us(acc_dt),.ax_mmps2(ax),.ay_mmps2(ay),.az_up_mmps2(az),
  .rc_valid(1'b1),.enabled(available && !fallback_latched),.taking_off(1'b1),.channel_count(4'd8),
  .ch1(16'd1500),.ch2(16'd1500),.ch3(ch3),.ch4(16'd1500),.ch7(16'd2000),.collective_us(16'd1658),.uptime_ms(64'd0),
  .diagnostic_body(diagnostics),.height_ready(height_ready),.core_height_tail(core_tail),
  .core_height_tail_without_acc(core_tail_noacc),.core_height_state_tail(core_state_tail),
  .z_active(z_active),.z_collective(z_collective),.z_reason(z_reason));
 height_loss_fallback fallback_control(.clk(clk),.rst_n(rst_n),.healthy(1'b1),.armed(1'b1),.taking_off(1'b1),
  .height_available(available),.automatic_valid(z_active),.automatic_collective_us(16'd1658),.ch3(ch3),
  .active(fallback_active),.latched_active(fallback_latched),.takeover_ready(fallback_ready),.collective_us(fallback_collective));
 integer first_ready=-1,first_drop=-1,recovered=-1,normal_drops=0,adapter_drops=0;
 integer valid_seen=0,seen_z=0,low_cycles=0;reg had_ready=0,previous_ready=0;
 initial begin
  if(!$value$plusargs("SCENARIO=%d",scenario))scenario=0;
  repeat(5)@(negedge clk);rst_n=1;
 end
 always @(negedge clk)if(rst_n)begin
  cycle=cycle+1;
  pose_start=(cycle%50000)==0;
  mtf_sample=(cycle%500000)==50000;
  if(mtf_sample)begin module_time=module_time+10;module_seq=module_seq+1'b1;end
  input_az=(scenario==1 && cycle>=2500000 && cycle<2550000) ?32'sd30001:32'sd0;
  distance=(scenario==2 && cycle>=2550000 && cycle<3050000) ?32'd5001:32'd250;
  if(cycle>=2000000)ch3=1000;
  if(cycle==4000000)begin
   if(!had_ready || !seen_z || !fallback_control.seen)$fatal(1,"bench did not establish actual nav/Z/last-good state");
   if(adapter_fault!=0 || adapter_drops!=0)$fatal(1,"normal adapter output validity fault/drop");
   if(missing!=0 || duplicates!=0 || restarts!=0 || breaks!=1)$fatal(1,"unexpected metric counters");
   if(scenario==0)begin
    if(normal_drops!=0 || fallback_active || first_drop!=-1)$fatal(1,"normal callbacks/low stick caused height withdrawal");
   end else begin
    if(first_drop<2500000 || recovered<first_drop || !height_ready || !fallback_latched || z_reason!=2)
     $fatal(1,"injected qualification failure did not reproduce recovered-ready/latched-fallback/reason2");
   end
   $display("PASS scenario=%0d cycles=%0d first_ready=%0d first_drop=%0d recovered=%0d low_stick_cycles=%0d adapter_drops=%0d normal_drops=%0d metric_breaks=%0d fallback_latched=%0d z_reason=%0d",scenario,cycle,first_ready,first_drop,recovered,low_cycles,adapter_drops,normal_drops,breaks,fallback_latched,z_reason);
   $finish;
  end
 end
 always @(posedge clk)if(rst_n)begin
  #1;
  if(native_acc_valid)valid_seen=1;else if(valid_seen)adapter_drops=adapter_drops+1;
  if(adapter_fault!=0)$fatal(1,"adapter fault");
  if(z_active)seen_z=1;
  if(available!==height_ready)$fatal(1,"partial height gate restoration mismatch");
  if(height_ready && !had_ready)begin had_ready=1;first_ready=cycle;end
  if(had_ready && previous_ready && !height_ready)begin
   if(first_drop==-1)first_drop=cycle;
   if(cycle<2500000 || scenario==0)normal_drops=normal_drops+1;
  end
  if(first_drop!=-1 && height_ready && recovered==-1)recovered=cycle;
  if(ch3==1000 && had_ready)low_cycles=low_cycles+1;
  previous_ready=height_ready;
 end
endmodule
