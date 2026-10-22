`include "calibration.vh"
`include "level_calibration.vh"
// ANO port:400Hz PWM,1000us stop,1200..2000us active.
// Physical flow calibration required before CH7 point hold can engage.
module acg720_ano_port(
 input wire clk50,imu_miso,rc_ppm_in,flow_miso,range_rx,
 output wire imu_sck,imu_mosi,imu_cs_n,flow_sck,flow_mosi,flow_cs_n,flow_pwr_en,
 output wire range_tx,uart_tx,led2,led3,
 output wire motor1_pwm,motor2_pwm,motor3_pwm,motor4_pwm
);
 localparam [7:0] CAL_MASK=`FLIGHT_CAL_MASK;
 reg [7:0] boot=0;always @(posedge clk50) if(boot!=255) boot<=boot+1'b1;
 wire rst_n=boot==255;
 assign range_tx=1'b1;
 wire rc_valid;wire [3:0] channels;wire [15:0] ch1,ch2,ch3,ch4,ch5,ch6,ch7,ch8;
 wire pose_update,pose_valid,armed,armed_raw,enabled,fresh,hold_consumed,altitude_consumed;wire [31:0] pose_dt,pose_age;
 wire [15:0] base_throttle_us;
 wire signed [31:0] world_ax,world_ay,world_azup;wire accel_valid;
 wire signed [15:0] raw_ax,raw_ay,raw_az;wire raw_accel_valid;wire [31:0] raw_accel_age;
 reg previous_pose_valid=0;
 always @(posedge clk50) if(!rst_n) previous_pose_valid<=0;else previous_pose_valid<=pose_valid;
 wire observer_reset=!pose_valid || !previous_pose_valid;
 wire acceleration_update,converted_acc_valid;
 wire [31:0] converted_dt_us;wire [7:0] time_adapter_fault;
 wire signed [31:0] converted_ax,converted_ay,converted_az;
 pose_time_adapter acc_time(.clk(clk50),.rst_n(rst_n),.cancel(observer_reset),.start(pose_update),
  .acc_valid(accel_valid),.ticks(pose_dt),.ax(world_ax),.ay(world_ay),.az(world_azup),
  .update(acceleration_update),.dt_us(converted_dt_us),.output_ax(converted_ax),.output_ay(converted_ay),.output_az(converted_az),
  .output_acc_valid(converted_acc_valid),.busy(),.fault(time_adapter_fault));
 wire signed [15:0] roll,pitch,body_yaw;
 wire [15:0] hold_collective;wire signed [16:0] gx,gy,gz;
 wire [863:0] core_body;
 wire requested,hold_ready,hold_active,altitude_active;wire [15:0] hold_reason;
 wire altitude_requested,altitude_ready;wire [15:0] altitude_reason;
 wire [1:0] mode_requested=requested ? 2'd2:altitude_requested ? 2'd1:2'd0;
 wire [1:0] mode_active=hold_consumed ? 2'd2:altitude_consumed ? 2'd1:2'd0;
 wire [15:0] mode_reason=(requested || altitude_requested) && !enabled ? 16'd2:
  requested && !hold_consumed ? hold_reason:altitude_requested ? altitude_reason:16'd1;
 wire signed [15:0] hold_roll,hold_pitch,hold_throttle;
 flight_core #(.LEVEL_TRIM_ENABLE(`LEVEL_TRIM_ENABLE),.LEVEL_R00_Q24(`LEVEL_R00_Q24),.LEVEL_R01_Q24(`LEVEL_R01_Q24),.LEVEL_R02_Q24(`LEVEL_R02_Q24),.LEVEL_R10_Q24(`LEVEL_R10_Q24),.LEVEL_R11_Q24(`LEVEL_R11_Q24),.LEVEL_R12_Q24(`LEVEL_R12_Q24),.LEVEL_R20_Q24(`LEVEL_R20_Q24),.LEVEL_R21_Q24(`LEVEL_R21_Q24),.LEVEL_R22_Q24(`LEVEL_R22_Q24)) core(.clk50(clk50),.imu_miso(imu_miso),.rc_ppm_in(rc_ppm_in),
  .hold_active(hold_active),.altitude_active(altitude_active),.hold_roll_cdeg(hold_roll),.hold_pitch_cdeg(hold_pitch),.hold_throttle_delta_us(hold_throttle),.hold_collective_us(hold_collective),
  .imu_sck(imu_sck),.imu_mosi(imu_mosi),.imu_cs_n(imu_cs_n),.led2(led2),.led3(led3),
  .motor1_pwm(motor1_pwm),.motor2_pwm(motor2_pwm),.motor3_pwm(motor3_pwm),.motor4_pwm(motor4_pwm),
  .rc_valid(rc_valid),.channel_count(channels),.ch1(ch1),.ch2(ch2),.ch3(ch3),.ch4(ch4),.ch5(ch5),.ch6(ch6),.ch7(ch7),.ch8(ch8),
  .pose_update(pose_update),.pose_valid(pose_valid),.pose_dt_ticks(pose_dt),.pose_age_ticks(pose_age),
  .base_throttle_us(base_throttle_us),.world_ax_mmps2(world_ax),.world_ay_mmps2(world_ay),.world_az_up_mmps2(world_azup),.linear_accel_valid(accel_valid),
  .raw_ax_counts(raw_ax),.raw_ay_counts(raw_ay),.raw_az_counts(raw_az),.raw_accel_valid(raw_accel_valid),.raw_accel_age_ticks(raw_accel_age),
  .body_roll_cdeg(roll),.body_pitch_cdeg(pitch),.body_yaw_cdeg(body_yaw),.body_gx(gx),.body_gy(gy),.body_gz(gz),
  .armed_usable(armed),.armed_raw(armed_raw),.hold_consumed(hold_consumed),.altitude_consumed(altitude_consumed),
  .control_enabled(enabled),.command_fresh(fresh),.telemetry_body(core_body));
 wire signed [15:0] dx,dy;wire [7:0] quality,motion,flow_who;
 wire flow_configured,flow_link,flow_update;wire [31:0] flow_seq,flow_good,flow_age,flow_dt,flow_errors;
 flow_reader flow(.clk50(clk50),.rst_n(rst_n),.flow_miso(flow_miso),
  .flow_sck(flow_sck),.flow_mosi(flow_mosi),.flow_cs_n(flow_cs_n),.flow_pwr_en(flow_pwr_en),
  .flow_dx(dx),.flow_dy(dy),.squal(quality),.flow_motion(motion),.who(flow_who),
  .configured(flow_configured),.link_ok(flow_link),.sample_valid(flow_update),.sample_sequence(flow_seq),
  .good_count(flow_good),.source_age_ticks(flow_age),.source_dt_ticks(flow_dt),.error_count(flow_errors));
 wire [15:0] distance_cm,strength,temp_raw;wire range_update,range_link;
 wire [31:0] range_age,range_errors,range_seq,range_good;wire [199:0] range_diagnostics;
 range_reader range_sensor(.clk50(clk50),.rst_n(rst_n),.range_rx(range_rx),.distance_cm(distance_cm),
  .strength(strength),.temp_raw(temp_raw),.sample_valid(range_update),.link_ok(range_link),
  .source_age_ticks(range_age),.error_count(range_errors),.sample_sequence(range_seq),.good_count(range_good),.diagnostics(range_diagnostics));
 reg signed [31:0] total_x=0,total_y=0;
 wire signed [32:0] sum_x=$signed(total_x)+$signed(dx),sum_y=$signed(total_y)+$signed(dy);
 always @(posedge clk50) if(!rst_n) begin total_x<=0;total_y<=0;end
 else if(flow_update) begin
  total_x<=sum_x>2147483647 ? 32'sh7fffffff : sum_x< -33'sd2147483648 ? 32'sh80000000 : sum_x[31:0];
  total_y<=sum_y>2147483647 ? 32'sh7fffffff : sum_y< -33'sd2147483648 ? 32'sh80000000 : sum_y[31:0];
 end
 // Registered processing qualifications cut across slow math blocks. Current
 // source health/age still withdraws control immediately at this boundary.
 wire live_range_pose_ok=pose_valid && range_link && distance_cm>0 && distance_cm<=500 &&
  range_age<5000000 && pose_age<3000000 && !observer_reset;
 wire live_height_ok=live_range_pose_ok && accel_valid && time_adapter_fault==0;
 wire live_xy_ok=live_height_ok && flow_link && flow_age<5000000 && quality>=30;
 // Mathematical scheduling consumes registered source qualifications. Keep
 // the current-source masks above on public validity; the independent core
 // pose/RC/SWA/60ms gates still stop PWM immediately. Auxiliary-mode selection
 // cancellation takes at most three clocks (60ns), without accepting bad math.
 reg control_acc_qualified=0;
 always @(posedge clk50) if(!rst_n || observer_reset) control_acc_qualified<=0;
 else control_acc_qualified<=accel_valid && converted_acc_valid && time_adapter_fault==0;
 wire calibrated,position_valid,height_valid,position_update,position_qualified;
 assign position_valid=position_qualified && live_xy_ok;
 wire [15:0] observer_reason;wire signed [31:0] x_q8,y_q8,vx,vy,height_mm,vz;
 wire signed [15:0] relative_yaw;wire [31:0] position_seq,position_age;
 wire signed [31:0] laser_height_mm;
 wire laser_height_ready,laser_height_valid,laser_height_update,laser_height_qualified;
 assign laser_height_ready=laser_height_qualified && live_range_pose_ok;
 assign laser_height_valid=CAL_MASK[3] && CAL_MASK[4] && laser_height_ready;
 wire [15:0] laser_height_reason;
 range_height_estimate #(.CAL_MASK(CAL_MASK)) laser_geometry(.clk(clk50),.rst_n(rst_n),
  .pose_update(pose_update),.pose_valid(pose_valid),.pose_age(pose_age),.roll(roll),.pitch(pitch),
  .range_link(range_link),.distance_cm(distance_cm),.range_age(range_age),
  .height_mm(laser_height_mm),.estimate_ready(),.height_valid(),.qualified_ready(laser_height_qualified),
  .update(laser_height_update),.busy(),.reason(laser_height_reason));
 generate if(CAL_MASK!=0) begin: calibrated_observer
 relative_position #(.EXTERNAL_YAW(1),.CAL_MASK(CAL_MASK),.FLOW_XX(`FLOW_XX_Q20),.FLOW_XY(`FLOW_XY_Q20),.FLOW_YX(`FLOW_YX_Q20),.FLOW_YY(`FLOW_YY_Q20),.ROT_XX(`ROT_XX_Q20),.ROT_XY(`ROT_XY_Q20),.ROT_XZ(`ROT_XZ_Q20),.ROT_YX(`ROT_YX_Q20),.ROT_YY(`ROT_YY_Q20),.ROT_YZ(`ROT_YZ_Q20)) observer(.clk(clk50),.rst_n(rst_n),.origin_reset(observer_reset),
  .pose_update(pose_update),.pose_valid(pose_valid),.pose_dt(pose_dt),.pose_age(pose_age),.roll(roll),.pitch(pitch),.yaw_reference_cdeg(body_yaw),.gx(gx),.gy(gy),.gz(gz),
  .flow_update(flow_update),.flow_link(flow_link),.dx(dx),.dy(dy),.quality(quality),.flow_dt(flow_dt),.flow_age(flow_age),
  .range_link(range_link),.distance_cm(distance_cm),.range_age(range_age),.calibrated(calibrated),.position_valid(),.qualified_position_valid(position_qualified),
  .height_valid(height_valid),.update(position_update),.reason(observer_reason),.x_q8(x_q8),.y_q8(y_q8),.vx(vx),.vy(vy),
  .height_mm(height_mm),.vz(vz),.yaw_cdeg(relative_yaw),.sample_sequence(position_seq),.age(position_age));
 end else begin: uncalibrated_observer

 // Physical optical calibration is required for XY. Laser geometry is
 // independently scheduled above, so fresh range cannot mask held flow data.
 assign calibrated=0;assign position_qualified=0;assign position_update=0;
 assign height_valid=laser_height_valid;
 assign x_q8=0;assign y_q8=0;assign vx=0;assign vy=0;assign height_mm=laser_height_mm;assign vz=0;
 assign relative_yaw=0;assign position_seq=0;assign position_age=32'hffffffff;assign observer_reason=1;
 end endgenerate
 // Source scheduling:velocity correction and XY controller every20ms.
 // Reuse only a still-valid current metric tuple; upstream age stays live.
 reg [19:0] flow_control_counter=0;reg flow_control_tick=0;
 always @(posedge clk50) begin
  flow_control_tick<=0;
  if(!rst_n || observer_reset) flow_control_counter<=0;
  else if(flow_control_counter==999999) begin flow_control_counter<=0;flow_control_tick<=1;end
  else flow_control_counter<=flow_control_counter+1'b1;
 end
 wire fusion_valid,fusion_qualified,fusion_update,fusion_flow_update;
 assign fusion_valid=fusion_qualified && live_xy_ok;wire [15:0] fusion_reason;
 wire signed [31:0] fused_vx,fused_vy;
 ano_flow_fusion #(.CAL_MASK(CAL_MASK)) fusion(.clk(clk50),.rst_n(rst_n),.origin_reset(observer_reset),
  .acc_update(acceleration_update),.acc_valid(accel_valid && converted_acc_valid && time_adapter_fault==0),
  .acc_dt_us(converted_dt_us),.ax_mmps2(converted_ax),.ay_mmps2(converted_ay),
  .flow_update(flow_control_tick),.flow_valid(position_valid),.flow_dt_us(32'd20000),
  .observed_vx(vx),.observed_vy(vy),.valid(),.qualified_valid(fusion_qualified),.update(fusion_update),.flow_correction_update(fusion_flow_update),
  .fused_vx(fused_vx),.fused_vy(fused_vy),.reason(fusion_reason));
 wire fused_height_valid,fused_height_ready,fused_height_update;
 wire height_qualified_valid,height_qualified_ready;
 assign fused_height_valid=height_qualified_valid && live_height_ok;
 assign fused_height_ready=height_qualified_ready && live_height_ok;wire [15:0] height_fusion_reason;
 wire signed [31:0] fused_height,fused_vz,height_sample_az;
 ano_height_fusion #(.CAL_MASK(CAL_MASK)) height_fusion(.clk(clk50),.rst_n(rst_n),.origin_reset(observer_reset),
  .acc_update(acceleration_update),.acc_dt_us(converted_dt_us),
  .range_valid(laser_height_ready),.acc_valid(accel_valid && converted_acc_valid && time_adapter_fault==0),.range_age_ticks(range_age),.acc_age_ticks(pose_age),
  .ref_height_mm(laser_height_mm),.az_up_mmps2(converted_az),.valid(),.estimate_ready(),.qualified_valid(height_qualified_valid),.qualified_ready(height_qualified_ready),
  .update(fused_height_update),.fused_height_mm(fused_height),.vz_mmps(fused_vz),.sample_az_mmps2(height_sample_az),.reason(height_fusion_reason));
 ano_hold_control #(.CAL_MASK(CAL_MASK)) position_controller(.clk(clk50),.rst_n(rst_n),.rc_valid(rc_valid),.channel_count(channels),
  // The arm FSM register schedules automatic math. Live health/RC/SWA still
  // gates physical outputs inside core; do not feed control_enabled here,
  // because it depends on height_active at low stick in altitude mode.
  .ch1(ch1),.ch2(ch2),.ch3(ch3),.ch4(ch4),.ch7(ch7),.enabled(armed_raw),.position_valid(position_qualified && fusion_qualified),.height_valid(height_qualified_valid),
  .position_update(fusion_flow_update),.height_update(fused_height_update),.position_age(position_age),.position_dt_us(32'd20000),
  .sample_update(acceleration_update),.sample_dt_us(converted_dt_us),
  .acc_valid(control_acc_qualified),
  .ax_mmps2(converted_ax),.ay_mmps2(converted_ay),.az_mmps2(height_sample_az),.collective_us(base_throttle_us),
  .x_q8(x_q8),.y_q8(y_q8),.vx(fused_vx),.vy(fused_vy),.height_mm(fused_height),.vz(fused_vz),
  .yaw_cdeg(body_yaw),.requested(requested),.ready(hold_ready),.active(hold_active),.reason(hold_reason),
  .height_requested(altitude_requested),.height_ready(altitude_ready),.height_active(altitude_active),.height_reason(altitude_reason),
  .requested_climb_mmps(),.target_height_mm(),
  .roll_target(hold_roll),.pitch_target(hold_pitch),.throttle_delta(hold_throttle),.collective_target_us(hold_collective));
 wire [7:0] system_flags={calibrated,fused_height_valid,hold_consumed,(requested ? hold_ready:altitude_ready),position_valid,range_link,flow_link,flow_configured};
 wire [887:0] extension={ch6,ch7,ch8,{6'd0,mode_requested},{6'd0,mode_active},mode_reason,system_flags,CAL_MASK,
  dx,dy,quality,motion,flow_who,flow_seq,flow_age,flow_dt,flow_errors,flow_good,total_x,total_y,
  distance_cm,strength,temp_raw,range_seq,range_age,range_errors,range_good,
  x_q8,y_q8,fused_vx,fused_vy,(fused_height_ready ? fused_height:laser_height_mm),fused_vz,body_yaw,observer_reason|fusion_reason|height_fusion_reason|laser_height_reason|{(fused_height_ready || laser_height_ready),15'd0},mode_reason,position_seq,position_age,16'd1200,16'd2000};
 // Latest raw sensor X forward/Y left/Z up includes gravity at2048counts/g.
 // World acceleration uses the published Main pose and its independent age.
 wire [215:0] acceleration_body={{6'd0,(raw_accel_valid && raw_accel_age<3000000),
  (accel_valid && pose_valid && pose_age<3000000)},pose_age,raw_accel_age,
  world_ax,world_ay,world_azup,raw_ax,raw_ay,raw_az};
 // Capture all three buses together before the packet engine's enabled registers.
 // This preserves one common snapshot while removing its mux from status paths.
 // A57B diagnostics share the same source snapshot; never feed control.
 wire [343:0] range_diagnostic_body={7'd0,range_link,range_diagnostics[199:40],
  range_errors,range_good,range_age,range_diagnostics[39:0],40'd0};
 wire [343:0] range_diagnostic_snapshot;
 wire [863:0] core_snapshot;wire [887:0] extension_snapshot;wire [215:0] acceleration_snapshot;
 // Snapshot all three telemetry buses on the same clock in every configuration.
 // This stage is display-only: live control and motor protection remain direct.
 generate begin: staged_telemetry
 reg [343:0] range_diagnostic_q=0;
 reg [863:0] core_q=0;reg [887:0] extension_q=0;reg [215:0] acceleration_q=0;
 always @(posedge clk50) begin core_q<=core_body;extension_q<=extension;acceleration_q<=acceleration_body;range_diagnostic_q<=range_diagnostic_body;end
 assign range_diagnostic_snapshot=range_diagnostic_q;
 assign core_snapshot=core_q;assign extension_snapshot=extension_q;assign acceleration_snapshot=acceleration_q;
 end endgenerate
 telemetry_tx #(.RANGE_DIAGNOSTICS(1)) telemetry(.clk(clk50),.core_body(core_snapshot),.extension(extension_snapshot),.acceleration_body(acceleration_snapshot),.range_diagnostic_body(range_diagnostic_snapshot),.tx(uart_tx));
endmodule
