`timescale 1ns/1ps
module policy_boundaries;
 reg clk=0;always #10 clk=~clk;
 reg rst_n=0,pvalid=1,avalid=1;
 reg [31:0] source_age=99;
 wire height_ready;
 mtf_xyz_navigation_control #(.PROOF_CONTROLLER(1),.PRECHECKED_HEIGHT_TILT4500(1),.PRECHECKED_FLOW_TILT1500(1)) nav(
  .clk(clk),.rst_n(rst_n),.origin_reset(1'b0),.diagnostic_hold(1'b0),
  .sample_valid(1'b0),.range_valid(1'b1),.flow_valid(1'b1),.distance_mm(32'd1000),
  .dt_ms(32'd10),.source_age_ms(source_age),.vx_x100(32'sd0),.vy_x100(32'sd0),
  .pose_valid(pvalid),.roll_cdeg(16'sd0),.pitch_cdeg(16'sd0),.yaw_cdeg(16'sd0),
  .yaw_range_ok(1'b1),.height_tilt4500_ok(1'b1),.flow_tilt1500_ok(1'b1),
  .acc_valid(avalid),.acc_update(1'b0),.acc_dt_us(32'd11000),.ax_mmps2(32'sd0),.ay_mmps2(32'sd0),.az_up_mmps2(32'sd0),
  .rc_valid(1'b0),.enabled(1'b0),.taking_off(1'b0),.channel_count(4'd8),
  .ch1(16'd1500),.ch2(16'd1500),.ch3(16'd1000),.ch4(16'd1500),.ch7(16'd1000),
  .collective_us(16'd1000),.uptime_ms(64'd0),.height_ready(height_ready));
 flight_core core(.clk50(clk),.imu_miso(1'b0),.rc_ppm_in(1'b0));
 task tick;begin @(posedge clk);#2;end endtask
 initial begin
  force nav.height_qualified_ready=1;
  force nav.geometry_height_state_numeric_tail=1;
  force nav.height_estimate_state_numeric_tail=1;
  force core.rst_n=rst_n;
  repeat(3)tick();@(negedge clk);rst_n=1;tick();
  if(!height_ready)$fatal(1,"99ms control source unavailable");
  @(negedge clk);source_age=100;tick();if(height_ready)$fatal(1,"100ms control source not revoked");
  @(negedge clk);source_age=999;tick();if(height_ready)$fatal(1,"online indication replaced control freshness");
  @(negedge clk);source_age=0;pvalid=0;tick();if(height_ready)$fatal(1,"explicit invalid pose bypassed");
  @(negedge clk);pvalid=1;avalid=0;tick();if(height_ready)$fatal(1,"explicit invalid acceleration bypassed");
  @(negedge clk);avalid=1;tick();if(!height_ready)$fatal(1,"valid source did not recover");
  @(negedge clk);force core.request_age=32'd2999999;force core.command_age=32'd2999999;tick();
  if(core.request_expired_q || core.command_expired_q)$fatal(1,"watchdog early");
  @(negedge clk);force core.request_age=32'd3000000;force core.command_age=32'd3000000;tick();
  if(!core.request_expired_q || !core.command_expired_q)$fatal(1,"independent request/command watchdog removed");
  $display("PASS policy_boundaries: control source99/100ms; explicit invalidity; independent request/command2999999/3000000 ticks");$finish;
 end
 initial begin #100000;$fatal(1,"policy boundary timeout");end
endmodule
