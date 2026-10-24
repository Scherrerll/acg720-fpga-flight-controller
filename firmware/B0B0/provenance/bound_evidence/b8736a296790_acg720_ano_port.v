`include "calibration.vh"
`include "level_calibration.vh"
// Experimental XYZ control-path candidate:400Hz PWM,1200..2000us active.
// Physical installation/rotation qualification is incomplete. DO_NOT_PROGRAM.
module acg720_ano_port(
 input wire clk50,imu_miso,rc_ppm_in,range_rx,
 output wire imu_sck,imu_mosi,imu_cs_n,imu_gyro_cs_n,
 output wire range_tx,uart_tx,radio_tx,led2,led3,
 output wire motor1_pwm,motor2_pwm,motor3_pwm,motor4_pwm
);
 localparam [7:0] CAL_MASK=`FLIGHT_CAL_MASK;
 reg [7:0] boot=0;always @(posedge clk50) if(boot!=255) boot<=boot+1'b1;
 wire rst_n=boot==255;
 assign range_tx=1'b1;
 assign radio_tx=uart_tx; // Passive SiK copy; never feeds control.
 wire rc_valid;wire [3:0] channels;wire [15:0] ch1,ch2,ch3,ch4,ch5,ch6,ch7,ch8;
 wire pose_update,pose_valid,armed,armed_raw,enabled,fresh,hold_consumed,altitude_consumed;wire [31:0] pose_dt,pose_age;
 wire [15:0] base_throttle_us;
 wire throttle_takeover_active;wire [15:0] throttle_pickup_us;
 wire [7:0] sticky_yaw_fault;
 wire signed [17:0] pilot_norm_x,pilot_norm_y;
 wire pilot_norm_update,pilot_norm_valid;wire [15:0] pilot_norm_dt_us;
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
 wire body_yaw_range_ok;
 wire signed [15:0] roll,pitch,body_yaw;
 wire [15:0] hold_collective;wire signed [16:0] gx,gy,gz;
 wire signed [28:0] gx_q12,gy_q12,gz_q12;
 wire [863:0] core_body;
 wire nav_xy_requested,nav_xy_ready,nav_xy_active;
 wire signed [15:0] nav_xy_roll,nav_xy_pitch;wire [15:0] nav_xy_reason;
 wire signed [15:0] nav_xy_payload_roll,nav_xy_payload_pitch;
 wire nav_z_active;wire signed [15:0] nav_z_throttle;
 wire [15:0] nav_z_collective,nav_z_reason;
 // Break the navigation/control combinational round trip. Capture mode
 // and all target fields together; normal mode/command handoff adds20ns.
 // Original core RC/SWA/IMU gates still mask physical commands directly.
 wire raw_xyz_joint_active=nav_xy_active;
 wire taking_off,nav_vertical_ready,nav_auto_takeoff,height_fallback_active;wire [3:0] flight_state_flags;wire signed [31:0] nav_feedback_height,nav_target_height;
 reg z_handoff_active=0;
 always @(posedge clk50)if(!rst_n)z_handoff_active<=0;else z_handoff_active<=nav_z_active;
 wire xyz_joint_active;
 wire signed [15:0] handoff_roll,handoff_pitch,handoff_delta;
 wire signed [15:0] handoff_raw_roll,handoff_raw_pitch;
 assign handoff_roll=xyz_joint_active ?handoff_raw_roll:16'sd0;
 assign handoff_pitch=xyz_joint_active ?handoff_raw_pitch:16'sd0;
 wire [15:0] handoff_collective;
 nav_control_handoff command_handoff(.clk(clk50),.rst_n(rst_n),
  .command_in({raw_xyz_joint_active,nav_xy_payload_roll,nav_xy_payload_pitch,nav_z_throttle,nav_z_collective}),
  .command_out({xyz_joint_active,handoff_raw_roll,handoff_raw_pitch,handoff_delta,handoff_collective}));
 wire requested,hold_ready,hold_active,altitude_active;wire [15:0] hold_reason;
 wire altitude_requested,altitude_ready;wire [15:0] altitude_reason;
 wire [1:0] mode_requested=requested ? 2'd2:altitude_requested ? 2'd1:2'd0;
 wire [1:0] mode_active=hold_consumed ? 2'd2:altitude_consumed ? 2'd1:2'd0;
 wire [15:0] mode_reason=(requested || altitude_requested) && !enabled ? 16'd2:
  requested && !hold_consumed ? hold_reason:altitude_requested ? altitude_reason:16'd1;
 wire signed [15:0] hold_roll,hold_pitch,hold_throttle;
 flight_core #(.RAW_TELEMETRY_COMMANDS(1),.LEVEL_TRIM_ENABLE(`LEVEL_TRIM_ENABLE),.LEVEL_R00_Q24(`LEVEL_R00_Q24),.LEVEL_R01_Q24(`LEVEL_R01_Q24),.LEVEL_R02_Q24(`LEVEL_R02_Q24),.LEVEL_R10_Q24(`LEVEL_R10_Q24),.LEVEL_R11_Q24(`LEVEL_R11_Q24),.LEVEL_R12_Q24(`LEVEL_R12_Q24),.LEVEL_R20_Q24(`LEVEL_R20_Q24),.LEVEL_R21_Q24(`LEVEL_R21_Q24),.LEVEL_R22_Q24(`LEVEL_R22_Q24)) core(.clk50(clk50),.imu_miso(imu_miso),.rc_ppm_in(rc_ppm_in),
  .hold_active(xyz_joint_active),.altitude_active(z_handoff_active),.vertical_available(nav_vertical_ready),.auto_takeoff(nav_auto_takeoff),.taking_off_out(taking_off),.height_fallback_active(height_fallback_active),.flight_state_flags(flight_state_flags),.vertical_height_mm(nav_feedback_height),.hold_roll_cdeg(handoff_roll),.hold_pitch_cdeg(handoff_pitch),.hold_throttle_delta_us(handoff_delta),.hold_collective_us(handoff_collective),
  .pilot_norm_x(pilot_norm_x),.pilot_norm_y(pilot_norm_y),.pilot_norm_update(pilot_norm_update),.pilot_norm_valid(pilot_norm_valid),.pilot_norm_dt_us(pilot_norm_dt_us),
  .imu_sck(imu_sck),.imu_mosi(imu_mosi),.imu_cs_n(imu_cs_n),.imu_gyro_cs_n(imu_gyro_cs_n),.led2(led2),.led3(led3),
  .motor1_pwm(motor1_pwm),.motor2_pwm(motor2_pwm),.motor3_pwm(motor3_pwm),.motor4_pwm(motor4_pwm),
  .rc_valid(rc_valid),.channel_count(channels),.ch1(ch1),.ch2(ch2),.ch3(ch3),.ch4(ch4),.ch5(ch5),.ch6(ch6),.ch7(ch7),.ch8(ch8),
  .pose_update(pose_update),.pose_valid(pose_valid),.pose_dt_ticks(pose_dt),.pose_age_ticks(pose_age),
  .base_throttle_us(base_throttle_us),
  .throttle_takeover_active(throttle_takeover_active),.throttle_pickup_us(throttle_pickup_us),
  .sticky_yaw_fault(sticky_yaw_fault),.world_ax_mmps2(world_ax),.world_ay_mmps2(world_ay),.world_az_up_mmps2(world_azup),.linear_accel_valid(accel_valid),
  .raw_ax_counts(raw_ax),.raw_ay_counts(raw_ay),.raw_az_counts(raw_az),.raw_accel_valid(raw_accel_valid),.raw_accel_age_ticks(raw_accel_age),
  .body_roll_cdeg(roll),.body_pitch_cdeg(pitch),.body_yaw_cdeg(body_yaw),.body_yaw_range_ok(body_yaw_range_ok),.body_gx(gx),.body_gy(gy),.body_gz(gz),
  .body_gx_q12(gx_q12),.body_gy_q12(gy_q12),.body_gz_q12(gz_q12),
  .armed_usable(armed),.armed_raw(armed_raw),.hold_consumed(hold_consumed),.altitude_consumed(altitude_consumed),
  .control_enabled(enabled),.command_fresh(fresh),.telemetry_body(core_body));
 wire signed [15:0] dx,dy;wire [7:0] quality,motion,flow_who;
 wire flow_configured,flow_link,flow_update;wire [31:0] flow_seq,flow_good,flow_age,flow_dt,flow_errors;
 // MTF observer does not synthesize fake PMW3901 counts or old range packets.
 assign dx=0;assign dy=0;assign quality=0;assign motion=0;assign flow_who=0;
 assign flow_configured=0;assign flow_link=0;assign flow_update=0;
 assign flow_seq=0;assign flow_good=0;assign flow_age=32'hffffffff;assign flow_dt=0;assign flow_errors=0;
 wire [15:0] distance_cm=0,strength=0,temp_raw=0;wire range_update=0,range_link=0;
 wire [31:0] range_age=32'hffffffff,range_errors=0,range_seq=0,range_good=0;
 wire [199:0] range_diagnostics=0;
 // Actual protected-core PWM drives the four GPIOs; this candidate has no stop lock.
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
 wire signed [30:0] fused_vx_q16,fused_vy_q16;
 ano_flow_fusion #(.CAL_MASK(CAL_MASK),.VELOCITY_FRAC_BITS(0)) fusion(.clk(clk50),.rst_n(rst_n),.origin_reset(observer_reset),
  .acc_update(acceleration_update),.acc_valid(accel_valid && converted_acc_valid && time_adapter_fault==0),
  .acc_dt_us(converted_dt_us),.ax_mmps2(converted_ax),.ay_mmps2(converted_ay),
  .flow_update(flow_control_tick),.flow_valid(position_valid),.flow_dt_us(32'd20000),
  .observed_vx(vx),.observed_vy(vy),.valid(),.qualified_valid(fusion_qualified),.update(fusion_update),.flow_correction_update(fusion_flow_update),
  .fused_vx(fused_vx),.fused_vy(fused_vy),.fused_vx_q16(fused_vx_q16),.fused_vy_q16(fused_vy_q16),.reason(fusion_reason));
 wire fused_height_valid,fused_height_ready,fused_height_update;
 wire height_qualified_valid,height_qualified_ready;
 assign fused_height_valid=height_qualified_valid && live_height_ok;
 assign fused_height_ready=height_qualified_ready && live_height_ok;wire [15:0] height_fusion_reason;
 wire signed [31:0] fused_height,fused_vz,height_sample_az;
 wire signed [31:0] fused_vz_q16;wire fused_vz_q16_valid;
 ano_height_fusion #(.CAL_MASK(CAL_MASK)) height_fusion(.clk(clk50),.rst_n(rst_n),.origin_reset(observer_reset),
  .acc_update(acceleration_update),.acc_dt_us(converted_dt_us),
  .range_valid(laser_height_ready),.acc_valid(accel_valid && converted_acc_valid && time_adapter_fault==0),.range_age_ticks(range_age),.acc_age_ticks(pose_age),
  .ref_height_mm(laser_height_mm),.az_up_mmps2(converted_az),.valid(),.estimate_ready(),.qualified_valid(height_qualified_valid),.qualified_ready(height_qualified_ready),
  .update(fused_height_update),.fused_height_mm(fused_height),.vz_mmps(fused_vz),.vz_q16(fused_vz_q16),.vz_q16_valid(fused_vz_q16_valid),.sample_az_mmps2(height_sample_az),.reason(height_fusion_reason));
 // JointXYZ observer; low and middle CH7 remain manual self-level.
 // Both physical core overrides and the independent1000us lock stay disabled.
 assign requested=nav_xy_requested;assign hold_ready=nav_xy_ready;assign hold_active=nav_xy_active;
 assign hold_reason=nav_xy_reason;assign hold_roll=nav_xy_roll;assign hold_pitch=nav_xy_pitch;
 assign hold_throttle=nav_z_throttle;assign hold_collective=nav_z_collective;
 assign altitude_requested=nav_xy_requested;assign altitude_ready=nav_xy_ready;assign altitude_active=nav_z_active;
 assign altitude_reason=nav_z_reason;
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
 wire telemetry_snapshot_hold;
 generate begin: staged_telemetry
 reg [343:0] range_diagnostic_q=0;
 reg [863:0] core_q=0;reg core_initialized=0;reg [887:0] extension_q=0;reg [215:0] acceleration_q=0;
 always @(posedge clk50) if(!telemetry_snapshot_hold) begin core_initialized<=1;core_q<=core_body;extension_q<=extension;acceleration_q<=acceleration_body;range_diagnostic_q<=range_diagnostic_body;end
 assign range_diagnostic_snapshot=range_diagnostic_q;
 assign core_snapshot={core_q[863:560],
  (core_q[862] ? core_q[559:512] : 48'd0),
  (core_q[862] ? core_q[511:448] : (core_initialized ? {4{16'd1000}} : 64'd0)),core_q[447:72],
  (core_q[1] ? core_q[71:8] : {4{16'd1000}}),core_q[7:0]};assign extension_snapshot=extension_q;assign acceleration_snapshot=acceleration_q;
 end endgenerate

 // Read-only flight evidence; core/control arithmetic remains byte-identical.
 reg [15:0] millisecond_phase=0;
 reg [63:0] uptime_ms=0,event_time_ms=0;
 reg [15:0] event_sequence=0,previous_revokes=0,previous_interruptions=0;
 reg [7:0] event_code=0,event_mask=0,event_imu=0,event_attitude=0;
 reg [31:0] event_pose_age=0;
 wire [15:0] revokes=core_body[215:200];
 wire [15:0] interruptions=core_body[231:216];
 always @(posedge clk50) begin
  if(!rst_n) begin
   millisecond_phase<=0;uptime_ms<=0;event_time_ms<=0;event_sequence<=0;
   previous_revokes<=0;previous_interruptions<=0;
   event_code<=0;event_mask<=0;event_imu<=0;event_attitude<=0;event_pose_age<=0;
  end else begin
   if(millisecond_phase==49999) begin millisecond_phase<=0;uptime_ms<=uptime_ms+1'b1;end
   else millisecond_phase<=millisecond_phase+1'b1;
   previous_revokes<=revokes;previous_interruptions<=interruptions;
   if(revokes!=previous_revokes || interruptions!=previous_interruptions) begin
    event_sequence<=event_sequence+1'b1;event_time_ms<=uptime_ms;
    event_code<=revokes!=previous_revokes ? core_body[191:184]:core_body[199:192];
    event_mask<=revokes!=previous_revokes ? core_body[127:120]:core_body[183:176];
    event_imu<=revokes!=previous_revokes ? core_body[87:80]:core_body[143:136];
    event_attitude<=revokes!=previous_revokes ? core_body[79:72]:core_body[135:128];
    event_pose_age<=revokes!=previous_revokes ? core_body[119:88]:core_body[175:144];
   end
  end
 end
 // A580/40B: primary sequence, v1, flags, build ID, uptime, sticky event.
 wire [271:0] flight_info={8'd4,{3'd0,height_fallback_active,flight_state_flags},32'h0000B0B0,uptime_ms,event_sequence,event_time_ms,
  event_code,event_mask,event_imu,event_attitude,event_pose_age,core_body[839:832],sticky_yaw_fault};
 reg [271:0] flight_info_q=0;
 always @(posedge clk50) if(!telemetry_snapshot_hold) flight_info_q<=flight_info;
 wire [975:0] mtf_body;
 wire mtf_sample,mtf_range_ok,mtf_flow_ok,mtf_integrated;
 wire [31:0] mtf_distance_mm,mtf_dt_ms,mtf_age_ms;
 wire signed [31:0] mtf_vx_x100,mtf_vy_x100;
 mtf01p_reader #(.EXTERNAL_DIAGNOSTIC_HOLD(1),.DIAGNOSTIC_VERSION(2),.PHYSICAL_STOP_LOCK(0),.CONTROL_PATH(1),.STARTUP_ONLY_DIAGNOSTIC_RESET(1)) mtf(.clk(clk50),.rst_n(rst_n),.rx(range_rx),.uptime_ms(uptime_ms),.diagnostic_hold(telemetry_snapshot_hold),.diagnostic_body(mtf_body),
  .metric_sample_valid(mtf_sample),.metric_range_valid(mtf_range_ok),.metric_flow_valid(mtf_flow_ok),
  .metric_interval_integrated(mtf_integrated),.metric_distance_mm(mtf_distance_mm),.metric_dt_ms(mtf_dt_ms),
  .module_age_ms(mtf_age_ms),.metric_vx_x100(mtf_vx_x100),.metric_vy_x100(mtf_vy_x100));
 // A583 pairs factory metric values with latest valid body gyro at HOST
 // receive time. It is a diagnostic snapshot, NOT an exposure-time gyro
 // integral and NOT permission to apply unverified rotation compensation.
 reg [15:0] pair_sequence=0;
 reg [335:0] rotation_pair=0,rotation_pair_q=0;
 always @(posedge clk50)begin
  if(!rst_n)begin pair_sequence<=0;rotation_pair<=0;end
  else if(mtf_sample)begin
   pair_sequence<=pair_sequence+1'b1;
   rotation_pair<={8'd1,{4'd0,mtf_integrated,mtf_flow_ok,mtf_range_ok,pose_valid},
    pair_sequence+16'd1,uptime_ms[31:0],mtf_distance_mm,mtf_dt_ms[15:0],pose_age,
    mtf_vx_x100,mtf_vy_x100,{{3{gx_q12[28]}},gx_q12},
    {{3{gy_q12[28]}},gy_q12},{{3{gz_q12[28]}},gz_q12},16'd0,throttle_pickup_us};
  end
  if(!telemetry_snapshot_hold)rotation_pair_q<={rotation_pair[335:16],throttle_pickup_us};
 end
 wire [719:0] navigation_body;
 mtf_xyz_navigation_control #(.PROOF_CONTROLLER(1),.PRECHECKED_YAW_RANGE(1),.STARTUP_ONLY_DIAGNOSTIC_RESET(1)) native_navigation(
  .clk(clk50),.rst_n(rst_n),.origin_reset(observer_reset),.sample_valid(mtf_sample),
  .range_valid(mtf_range_ok),.flow_valid(mtf_flow_ok && mtf_integrated),
  .distance_mm(mtf_distance_mm),.dt_ms(mtf_dt_ms),.source_age_ms(mtf_age_ms),
  .vx_x100(mtf_vx_x100),.vy_x100(mtf_vy_x100),
  .pose_valid(pose_valid),.pose_age_ticks(pose_age),.roll_cdeg(roll),.pitch_cdeg(pitch),.yaw_cdeg(body_yaw),.yaw_range_ok(body_yaw_range_ok),
  .acc_valid(accel_valid && converted_acc_valid && time_adapter_fault==0),
  .acc_update(acceleration_update),.acc_dt_us(converted_dt_us),.ax_mmps2(converted_ax),.ay_mmps2(converted_ay),.az_up_mmps2(converted_az),
  .rc_valid(rc_valid),.enabled(armed && !height_fallback_active),.taking_off(taking_off),.channel_count(channels),.ch1(ch1),.ch2(ch2),.ch3(ch3),.ch4(ch4),.ch7(ch7),
  .collective_us(base_throttle_us),.uptime_ms(uptime_ms),.diagnostic_hold(telemetry_snapshot_hold),.diagnostic_body(navigation_body),
  .control_permission(),.position_ready(),.height_ready(nav_vertical_ready),.auto_takeoff(nav_auto_takeoff),.z_feedback_height(nav_feedback_height),.z_target_height_out(nav_target_height),.position_x_q8(),.position_y_q8(),
  .xy_requested(nav_xy_requested),.xy_ready(nav_xy_ready),.xy_active(nav_xy_active),
  .xy_roll_target(nav_xy_roll),.xy_pitch_target(nav_xy_pitch),.xy_reason(nav_xy_reason),
  .xy_payload_roll(nav_xy_payload_roll),.xy_payload_pitch(nav_xy_payload_pitch),
  .z_active(nav_z_active),.z_throttle_delta(nav_z_throttle),.z_collective(nav_z_collective),.z_reason(nav_z_reason),
  .pilot_norm_x(pilot_norm_x),.pilot_norm_y(pilot_norm_y),.pilot_norm_update(pilot_norm_update),.pilot_norm_valid(pilot_norm_valid),.pilot_norm_dt_us(pilot_norm_dt_us));
 telemetry_tx #(.ROTATION_INFO(1),.PERIOD(10000000),.MTF_INFO(1),.MTF_CALLER_SNAPSHOT(1),.INFO_CALLER_SNAPSHOT(1),.NAV_INFO(1),.NAV_CALLER_SNAPSHOT(1),.FLIGHT_INFO(1),.RANGE_DIAGNOSTICS(0),.EXTERNAL_SNAPSHOT(1)) telemetry(.clk(clk50),.core_body(core_snapshot),.extension(extension_snapshot),.acceleration_body(acceleration_snapshot),.range_diagnostic_body(range_diagnostic_snapshot),.flight_info_body(flight_info_q),.rotation_body(rotation_pair_q),.mtf_body(mtf_body),.nav_body(navigation_body),.tx(uart_tx),.snapshot_hold(telemetry_snapshot_hold));
endmodule

// One coherent65-bit command record: exactly one20ns handoff stage.
// No scaling, saturation, qualification, arbitration or safety logic here.
module nav_control_handoff(input wire clk,rst_n,input wire [64:0] command_in,
 output wire [64:0] command_out);
 reg [64:0] command_q=65'd0;
 always @(posedge clk)if(!rst_n)command_q<=65'd0;else command_q<=command_in;
 assign command_out=command_q;
endmodule
