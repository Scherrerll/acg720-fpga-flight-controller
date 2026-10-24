`timescale 1ns/1ps
// Experimental joint XYZ control path: factory MTF geometry -> native ANO XY/Z fusion
// -> real20ms relative position and the shared existing XYZ equations.
// Only high CH7 requests XYZ; low/mid acknowledges/manual, no separate Z mode.
// This candidate connects its outputs to flight_core; no physical qualification is earned.
// PROOF_CONTROLLER permits the existing numeric controller, never installation acceptance.
// control_permission reports active calculation only, not physical release authority.
// This isolated candidate remains DO_NOT_PROGRAM; it has no physical stop lock.
module mtf_xyz_navigation_control #(parameter integer PROOF_CONTROLLER=0,PRECHECKED_YAW_RANGE=0)(
 input wire clk,rst_n,origin_reset,diagnostic_hold,
 input wire sample_valid,range_valid,flow_valid,
 input wire [31:0] distance_mm,dt_ms,source_age_ms,
 input wire signed [31:0] vx_x100,vy_x100,
 input wire pose_valid,input wire [31:0] pose_age_ticks,
 input wire signed [15:0] roll_cdeg,pitch_cdeg,yaw_cdeg,
 input wire yaw_range_ok,
 input wire acc_valid,acc_update,input wire [31:0] acc_dt_us,
 input wire signed [31:0] ax_mmps2,ay_mmps2,az_up_mmps2,
 input wire rc_valid,enabled,taking_off,input wire [3:0] channel_count,
 input wire [15:0] ch1,ch2,ch3,ch4,ch7,collective_us,
 input wire [63:0] uptime_ms,
 output wire [719:0] diagnostic_body,
 output wire control_permission,
 output wire position_ready,height_ready,
 output wire signed [31:0] position_x_q8,position_y_q8,
 output wire xy_requested,xy_ready,xy_active,
 output wire signed [15:0] xy_roll_target,xy_pitch_target,
 output wire signed [15:0] xy_payload_roll,xy_payload_pitch,
 output wire [15:0] xy_reason,
 output wire signed [31:0] z_feedback_height,z_target_height_out,
 output wire signed [17:0] pilot_norm_x,pilot_norm_y,
 output wire pilot_norm_update,pilot_norm_valid,output wire [15:0] pilot_norm_dt_us,
 output wire auto_takeoff,
 output wire z_active,output wire signed [15:0] z_throttle_delta,
 output wire [15:0] z_collective,z_reason
);
 // One shared multiply and one independently arbitrated divide serve only
 // this added navigation domain. Client0=geometry,1=XY fusion,2=Z fusion,
 //3=joint XYZ outer. The proven4-slot service/one-deep pending is unchanged.
 wire [3:0] m_request,m_cancel,m_busy,m_done,m_error;
 wire [3:0] d_request,d_cancel,d_busy,d_done,d_error;
 wire [255:0] m_a,m_b,d_a,d_b;
 wire signed [63:0] m_result,d_result;
 assign d_request[0]=1'b0;assign d_cancel[0]=1'b1;
 assign d_a[63:0]=64'd0;assign d_b[63:0]=64'd0;
 assign d_b[127:96]=0;assign d_b[191:160]=0;assign d_b[255:224]=0;
 nav_math_service #(.DIVIDE(0),.CLIENTS(4)) multiply_service(
  .clk(clk),.rst_n(rst_n),.request(m_request),.cancel(m_cancel),.operand_a(m_a),.operand_b(m_b),
  .busy(m_busy),.done(m_done),.error(m_error),.result(m_result),.grant());
 nav_math_service #(.DIVIDE(1),.CLIENTS(4)) divide_service(
  .clk(clk),.rst_n(rst_n),.request(d_request),.cancel(d_cancel),.operand_a(d_a),.operand_b(d_b),
  .busy(d_busy),.done(d_done),.error(d_error),.result(d_result),.grant());
 wire geometry_update,geometry_height_ready,geometry_flow_ready;
 wire [15:0] geometry_reason;
 wire signed [31:0] height_mm,bvx,bvy,wvx,wvy;
 wire [31:0] geometry_dt_us;
 wire mapping_verified,rotation_compensated,geometry_control_verified;
 // FMT native Micolink: body forward=-rawY, right=rawX. Our mount is
 // mechanically 180deg from the FMT drawing: forward=rawY, right=-rawX.
 // This documented mapping remains provisional; no calibration bit is earned.
 // Height cosine correction stays valid through the core's45deg stop bound.
 // The provisional optical-flow qualification retains its tighter15deg bound;
 // leaving that bound withdraws XY, without cancelling the vertical reference.
 mtf_shared_geometry #(.HEIGHT_TILT_LIMIT_CDEG(4500),.FLOW_TILT_LIMIT_CDEG(1500),.SWAP_AXES(1),.NEGATE_X(0),.NEGATE_Y(1),.MAPPING_VERIFIED(0),.PRECHECKED_YAW_RANGE(PRECHECKED_YAW_RANGE)) geometry(
  .clk(clk),.rst_n(rst_n),.origin_reset(origin_reset),.sample_valid(sample_valid),
  .range_valid(range_valid),.flow_valid(flow_valid),.distance_mm(distance_mm),.dt_ms(dt_ms),
  .vx_x100(vx_x100),.vy_x100(vy_x100),.pose_valid(pose_valid),.pose_age_ticks(pose_age_ticks),
  .roll_cdeg(roll_cdeg),.pitch_cdeg(pitch_cdeg),.body_yaw_cdeg(yaw_cdeg),.body_yaw_range_ok(yaw_range_ok),
  .update(geometry_update),.height_ready(geometry_height_ready),.flow_ready(geometry_flow_ready),
  .reason(geometry_reason),.height_mm(height_mm),.body_vx_q16(bvx),.body_vy_q16(bvy),
  .world_vx_q16(wvx),.world_vy_q16(wvy),.dt_us(geometry_dt_us),.busy(),
  .mapping_verified(mapping_verified),.rotation_compensated(rotation_compensated),.control_verified(geometry_control_verified),
  .math_mul_start(m_request[0]),.math_mul_cancel(m_cancel[0]),
  .math_mul_a(m_a[0 +:64]),.math_mul_b(m_b[0 +:64]),
  .math_mul_busy(m_busy[0]),.math_mul_done(m_done[0]),.math_mul_result(m_result));

 wire live_acc=acc_valid && pose_valid && pose_age_ticks<3000000 && !origin_reset;
 wire module_fresh=source_age_ms<100 && range_valid;
 wire [31:0] range_age_ticks=source_age_ms<100 ?source_age_ms*32'd50000:32'hffffffff;
 wire flow_fusion_valid,flow_fusion_qualified,flow_fusion_update,flow_correction_update;
 wire signed [31:0] fused_vx,fused_vy;
 wire signed [30:0] fused_vx_q16,fused_vy_q16;
 wire [15:0] flow_reason;
 // The mask here enables numerical observation only; it is NOT the physical
 // qualification mask of the flight controller. No output feeds that controller.
 mtf_shared_flow_fusion #(.CAL_MASK(8'h3f),.VELOCITY_FRAC_BITS(16)) velocity_fusion(
  .clk(clk),.rst_n(rst_n),.origin_reset(origin_reset),.acc_update(acc_update),.acc_valid(live_acc),
  .acc_dt_us(acc_dt_us),.ax_mmps2(ax_mmps2),.ay_mmps2(ay_mmps2),
  .flow_update(geometry_update && geometry_flow_ready),.flow_valid(geometry_flow_ready && module_fresh),
  .flow_dt_us(geometry_dt_us),.observed_vx(wvx),.observed_vy(wvy),
  .valid(flow_fusion_valid),.qualified_valid(flow_fusion_qualified),.update(flow_fusion_update),
  .flow_correction_update(flow_correction_update),.fused_vx(fused_vx),.fused_vy(fused_vy),
  .fused_vx_q16(fused_vx_q16),.fused_vy_q16(fused_vy_q16),.reason(flow_reason),
  .math_mul_start(m_request[1]),.math_mul_cancel(m_cancel[1]),
  .math_mul_a(m_a[64 +:64]),.math_mul_b(m_b[64 +:64]),
  .math_mul_busy(m_busy[1]),.math_mul_done(m_done[1]),.math_mul_result(m_result),
  .math_div_start(d_request[1]),.math_div_cancel(d_cancel[1]),
  .math_div_numerator(d_a[64 +:64]),.math_div_denominator(d_b[64 +:32]),
  .math_div_busy(d_busy[1]),.math_div_done(d_done[1]),.math_div_error(d_error[1]),.math_div_result(d_result));
 wire height_estimate_ready,height_qualified_ready,height_fusion_update;
 wire signed [31:0] fused_height,fused_vz,fused_vz_q16,height_sample_az;
 wire fused_vz_q16_valid;wire [15:0] height_reason;
 mtf_shared_height_fusion #(.CAL_MASK(0)) height_fusion(
  .clk(clk),.rst_n(rst_n),.origin_reset(origin_reset),.range_valid(geometry_height_ready && module_fresh),
  .acc_valid(live_acc),.acc_update(acc_update),.acc_dt_us(acc_dt_us),
  .range_age_ticks(range_age_ticks),.acc_age_ticks(pose_age_ticks),
  .ref_height_mm(height_mm),.az_up_mmps2(az_up_mmps2),.valid(),.estimate_ready(height_estimate_ready),
  .qualified_ready(height_qualified_ready),.qualified_valid(),.update(height_fusion_update),
  .fused_height_mm(fused_height),.vz_mmps(fused_vz),.sample_az_mmps2(height_sample_az),
  .vz_q16(fused_vz_q16),.vz_q16_valid(fused_vz_q16_valid),.reason(height_reason),
  .math_mul_start(m_request[2]),.math_mul_cancel(m_cancel[2]),
  .math_mul_a(m_a[128 +:64]),.math_mul_b(m_b[128 +:64]),
  .math_mul_busy(m_busy[2]),.math_mul_done(m_done[2]),.math_mul_result(m_result),
  .math_div_start(d_request[2]),.math_div_cancel(d_cancel[2]),
  .math_div_numerator(d_a[128 +:64]),.math_div_denominator(d_b[128 +:32]),
  .math_div_busy(d_busy[2]),.math_div_done(d_done[2]),.math_div_error(d_error[2]),.math_div_result(d_result));
 // qualified_ready is numerical observation even with CAL_MASK=0.
 // Raw estimate_ready additionally revokes same-cycle range/acc bounds faults.
 assign height_ready=height_qualified_ready && height_estimate_ready && geometry_height_ready && module_fresh && live_acc;
 wire live_velocity=flow_fusion_valid && flow_fusion_qualified && geometry_flow_ready && module_fresh && live_acc;
 // Two independent epochs: observation ignores all RC/arm/mode changes.
 // Bad levels advance only on their sampled rising edge, not every bad tick.
 wire position_internal_ready;
 wire raw_manual=rc_valid && channel_count>=7 && ch7>=900 && ch7<=1700;
 wire raw_requested=rc_valid && channel_count>=7 && ch7>=1800 && ch7<=2200;
 wire raw_centered=ch1>=1450 && ch1<=1550 && ch2>=1450 && ch2<=1550 && ch4>=1450 && ch4<=1550;
 wire signed [31:0] raw_fvx={fused_vx_q16[30],fused_vx_q16};
 wire signed [31:0] raw_fvy={fused_vy_q16[30],fused_vy_q16};
 wire live_yaw_range_ok=PRECHECKED_YAW_RANGE ?yaw_range_ok:(yaw_cdeg>=-18000 && yaw_cdeg<=18000);
 wire raw_numeric_ok=collective_us>=1000 && collective_us<=2000 && ch3>=900 && ch3<=2200 &&
  fused_height>=0 && fused_height<=5000 && fused_vz_q16>=-655360000 && fused_vz_q16<=655360000 &&
  height_sample_az>=-30000 && height_sample_az<=30000 &&
  raw_fvx>=-655360000 && raw_fvx<=655360000 && raw_fvy>=-655360000 && raw_fvy<=655360000 &&
  ax_mmps2>=-30000 && ax_mmps2<=30000 && ay_mmps2>=-30000 && ay_mmps2<=30000 &&
  az_up_mmps2>=-30000 && az_up_mmps2<=30000 && live_yaw_range_ok;
 wire observation_bad=!height_ready || !fused_vz_q16_valid;
 wire control_bad=observation_bad || !rc_valid || !enabled;
 reg observation_bad_d=1,control_bad_d=1,origin_d=0,manual_d=0;
 reg [7:0] observation_epoch=0,control_epoch=0;
 reg [15:0] observation_epoch_reason=0,control_revoke_reason=0;
 wire [15:0] raw_revoke_reason=origin_reset ?16'd1024:observation_bad || !height_ready || !fused_vz_q16_valid || !position_internal_ready || !raw_numeric_ok ?16'd4:
  !rc_valid || channel_count<7 || !(raw_requested || raw_manual) ?16'd1:!enabled ?16'd2:!raw_centered ?16'd16:16'd1;
 wire observation_event=(observation_bad && !observation_bad_d) || (origin_reset && !origin_d);
 wire control_event=observation_event || (control_bad && !control_bad_d);
 wire [7:0] next_observation_epoch=observation_epoch+{7'd0,observation_event};
 wire [7:0] next_control_epoch=control_epoch+{7'd0,control_event};
 always @(posedge clk)begin
  if(!rst_n)begin
   observation_epoch<=0;control_epoch<=0;observation_bad_d<=1;control_bad_d<=1;origin_d<=0;manual_d<=0;observation_epoch_reason<=0;control_revoke_reason<=0;
  end else begin
   observation_bad_d<=observation_bad;control_bad_d<=control_bad;origin_d<=origin_reset;manual_d<=raw_manual;
   observation_epoch<=next_observation_epoch;control_epoch<=next_control_epoch;
   if(observation_event)observation_epoch_reason<=origin_reset ?16'd1024:16'd4;
   if(control_event)control_revoke_reason<=raw_revoke_reason;
  end
 end
 // P captures ALL upstream metadata with velocity. Moving the local timer one
 // tick later and consuming this one-tick-old velocity preserves the original
 // callback sample. P metadata later aligns C to that same original callback.
 reg p_live=0,p_height_valid=0,p_acc_valid=0,p_rc_valid=0,p_enabled=0;
 reg p_height_update=0,p_sample_update=0;reg [31:0]p_sample_dt=0;
 reg signed [31:0]p_vz=0;reg [15:0]p_collective=0;
 reg [7:0] p_observation_epoch=0,p_control_epoch=0;
 reg signed [31:0] p_vx=0,p_vy=0,p_height=0,p_ax=0,p_ay=0,p_az=0;
 reg signed [15:0] p_yaw=0;
 reg [3:0] p_channel_count=0;
 reg [15:0] p_ch1=0,p_ch2=0,p_ch3=0,p_ch4=0,p_ch7=0;
 always @(posedge clk)begin
  if(!rst_n)begin
   p_live<=0;p_height_valid<=0;p_acc_valid<=0;p_rc_valid<=0;p_enabled<=0;p_observation_epoch<=0;p_control_epoch<=0;
   p_vx<=0;p_vy<=0;p_height<=0;p_ax<=0;p_ay<=0;p_az<=0;p_yaw<=0;p_channel_count<=0;
   p_ch1<=0;p_ch2<=0;p_ch3<=0;p_ch4<=0;p_ch7<=0;
   p_height_update<=0;p_sample_update<=0;p_sample_dt<=0;p_vz<=0;p_collective<=0;
  end else begin
   p_live<=live_velocity;p_height_valid<=height_ready && fused_vz_q16_valid;p_acc_valid<=live_acc;p_rc_valid<=rc_valid;p_enabled<=enabled;
   p_observation_epoch<=next_observation_epoch;p_control_epoch<=next_control_epoch;
   p_vx<=raw_fvx;p_vy<=raw_fvy;p_height<=fused_height;p_ax<=ax_mmps2;p_ay<=ay_mmps2;p_az<=height_sample_az;p_yaw<=yaw_cdeg;
   p_height_update<=height_fusion_update;p_sample_update<=acc_update;p_sample_dt<=acc_dt_us;p_vz<=fused_vz_q16;p_collective<=collective_us;
   p_channel_count<=channel_count;p_ch1<=ch1;p_ch2<=ch2;p_ch3<=ch3;p_ch4<=ch4;p_ch7<=ch7;
  end
 end
 wire position_stage_ok=p_live && p_observation_epoch==observation_epoch;
 // True50MHz/20ms timer; no source/raw public mask feeds the integrator CE.
 reg [19:0] position_timer=0;reg position_tick=0;
 always @(posedge clk)begin
  position_tick<=0;
  if(!rst_n || !position_stage_ok)position_timer<=0;
  else if(position_timer==999999)begin position_timer<=0;position_tick<=1;end
  else position_timer<=position_timer+1'b1;
 end
 wire position_update,integral_valid;wire [31:0] position_age;wire [15:0] position_reason;
 wire signed [31:0] position_raw_x,position_raw_y;
 mtf_position_integrator position(
  .clk(clk),.rst_n(rst_n),.cancel(origin_reset || !position_stage_ok),.update_in(position_tick),.sources_valid(position_stage_ok),
  .dt_us(32'd20000),.vx_q16(p_vx),.vy_q16(p_vy),
  .update(position_update),.busy(),.valid(integral_valid),.x_q8(position_raw_x),.y_q8(position_raw_y),
  .age_ticks(position_age),.reason(position_reason));
 assign position_internal_ready=integral_valid && position_stage_ok;
 assign position_ready=position_internal_ready && live_velocity && !origin_reset;
 assign position_x_q8=position_ready ?position_raw_x:32'sd0;
 assign position_y_q8=position_ready ?position_raw_y:32'sd0;
 // C consumes the position publication and its age atomically, with P's
 // retimed metadata. The unchanged controller sees the old callback tuple
 // exactly two clocks later, rather than current metadata with old position.
 reg c_position_valid=0,c_position_update=0,c_height_valid=0,c_acc_valid=0,c_rc_valid=0,c_enabled=0;
 reg c_height_update=0,c_sample_update=0;reg [31:0]c_sample_dt=0;
 reg signed [31:0]c_vz=0;reg [15:0]c_collective=0;
 reg [7:0] c_observation_epoch=0,c_control_epoch=0;
 reg [31:0] c_position_age=32'hffffffff;
 reg signed [31:0] c_x=0,c_y=0,c_vx=0,c_vy=0,c_height=0,c_ax=0,c_ay=0,c_az=0;
 reg signed [15:0] c_yaw=0;reg [3:0] c_channel_count=0;
 reg [15:0] c_ch1=0,c_ch2=0,c_ch3=0,c_ch4=0,c_ch7=0;
 always @(posedge clk)begin
  if(!rst_n)begin
   c_position_valid<=0;c_position_update<=0;c_height_valid<=0;c_acc_valid<=0;c_rc_valid<=0;c_enabled<=0;
   c_observation_epoch<=0;c_control_epoch<=0;c_position_age<=32'hffffffff;
   c_x<=0;c_y<=0;c_vx<=0;c_vy<=0;c_height<=0;c_ax<=0;c_ay<=0;c_az<=0;c_yaw<=0;c_channel_count<=0;
   c_ch1<=0;c_ch2<=0;c_ch3<=0;c_ch4<=0;c_ch7<=0;
   c_height_update<=0;c_sample_update<=0;c_sample_dt<=0;c_vz<=0;c_collective<=0;
  end else begin
   // OF control consumes velocity, not the optional telemetry position
   // accumulator. A display accumulator reset/overflow must not revoke OF PI.
   c_position_valid<=position_stage_ok;c_position_update<=position_tick && position_stage_ok;
   c_observation_epoch<=p_observation_epoch;c_control_epoch<=p_control_epoch;
   c_position_age<=source_age_ms<100 ?source_age_ms*32'd50000:32'hffffffff;c_x<=position_internal_ready ?position_raw_x:0;c_y<=position_internal_ready ?position_raw_y:0;
   c_height_valid<=p_height_valid;c_acc_valid<=p_acc_valid;c_rc_valid<=p_rc_valid;c_enabled<=p_enabled;
   c_vx<=p_vx;c_vy<=p_vy;c_height<=p_height;c_ax<=p_ax;c_ay<=p_ay;c_az<=p_az;c_yaw<=p_yaw;
   c_height_update<=p_height_update;c_sample_update<=p_sample_update;c_sample_dt<=p_sample_dt;c_vz<=p_vz;c_collective<=p_collective;
   c_channel_count<=p_channel_count;c_ch1<=p_ch1;c_ch2<=p_ch2;c_ch3<=p_ch3;c_ch4<=p_ch4;c_ch7<=p_ch7;
  end
 end
 wire controller_observation_epoch_ok=c_observation_epoch==observation_epoch;
 wire controller_control_epoch_ok=c_control_epoch==control_epoch;
  wire controller_requested,controller_ready,controller_active;
 wire controller_z_requested,controller_z_ready,controller_z_active;
 wire signed [15:0]controller_delta;wire[15:0]controller_collective,controller_z_reason;
 wire signed [31:0]controller_target_height;
 wire signed [15:0] controller_roll,controller_pitch;wire [15:0] controller_reason;
 mtf_xyz_hold_control #(.CAL_MASK(PROOF_CONTROLLER ? 8'hff:8'h00),.VELOCITY_FRAC_BITS(16)) controller_proof(
  .clk(clk),.rst_n(rst_n),.origin_reset(origin_reset || !controller_observation_epoch_ok),.rc_valid(c_rc_valid),.channel_count(c_channel_count),
  .ch1(c_ch1),.ch2(c_ch2),.ch3(c_ch3),.ch4(c_ch4),.ch7(c_ch7),.enabled(c_enabled && controller_control_epoch_ok),.taking_off(taking_off),
  .position_valid(c_position_valid),.height_valid(c_height_valid),.position_update(c_position_update),
  .height_update(c_height_update),.sample_update(c_sample_update),.sample_dt_us(c_sample_dt),
  .position_age(c_position_age),.position_dt_us(32'd20000),
  .x_q8(c_x),.y_q8(c_y),.vx(c_vx),.vy(c_vy),.height_mm(c_height),.vz(c_vz),.yaw_cdeg(c_yaw),
  .acc_valid(c_acc_valid),.ax_mmps2(c_ax),.ay_mmps2(c_ay),.az_mmps2(c_az),
  .collective_us(c_collective),.requested(controller_requested),.ready(controller_ready),.active(controller_active),
  .height_requested(controller_z_requested),.height_ready(controller_z_ready),.height_active(controller_z_active),
  .auto_takeoff(auto_takeoff),.pilot_norm_x(pilot_norm_x),.pilot_norm_y(pilot_norm_y),
  .pilot_norm_update(pilot_norm_update),.pilot_norm_valid(pilot_norm_valid),.pilot_norm_dt_us(pilot_norm_dt_us),
  .height_reason(controller_z_reason),.collective_target_us(controller_collective),.throttle_delta(controller_delta),
  .requested_climb_mmps(),.target_height_mm(controller_target_height),
  .reason(controller_reason),.roll_target(controller_roll),.pitch_target(controller_pitch),
  .math_mul_start(m_request[3]),.math_mul_cancel(m_cancel[3]),
  .math_mul_a(m_a[192 +:64]),.math_mul_b(m_b[192 +:64]),
  .math_mul_busy(m_busy[3]),.math_mul_done(m_done[3]),.math_mul_result(m_result),
  .math_div_start(d_request[3]),.math_div_cancel(d_cancel[3]),
  .math_div_numerator(d_a[192 +:64]),.math_div_denominator(d_b[192 +:32]),
  .math_div_busy(d_busy[3]),.math_div_done(d_done[3]),.math_div_error(d_error[3]),.math_div_result(d_result));
 // Public masks are immediate and never feed either internal pipeline stage.
 // Numerical ready stays independent of RC/enable/centering, as before.
 assign xy_requested=raw_requested;
 assign xy_ready=controller_ready && live_velocity && raw_numeric_ok && controller_observation_epoch_ok && !origin_reset;
 assign xy_active=controller_active && controller_z_active && controller_z_ready && xy_ready && controller_control_epoch_ok && raw_requested && rc_valid && enabled;
 // Source-epoch destruction reuses the unchanged origin input. The saved
 // reason describes the latest OBSERVATION epoch, never an old control tuple.
 // RC/manual control-epoch events do not overwrite this source cause.
 // Public diagnosis reports the latest revoke epoch. Synthetic enabled=0
 // for draining an old control tuple must not mislabel RC/centering as2.
 wire [15:0] source_reason=(controller_reason &16'hfbff) |
  (controller_reason[10] ?observation_epoch_reason:16'd0);
 assign xy_reason=origin_reset ?16'd1024:!raw_requested ?16'd1:!enabled ?16'd2:!xy_ready ?16'd4:!taking_off ?16'd256:controller_reason;
 // Public commands cannot retain stale values after a live source revoke.
 assign xy_payload_roll=controller_roll;assign xy_payload_pitch=controller_pitch;
 assign xy_roll_target=xy_active ? controller_roll:16'sd0;
 assign xy_pitch_target=xy_active ? controller_pitch:16'sd0;
 assign z_active=controller_z_active && controller_z_ready && height_ready && fused_vz_q16_valid && controller_observation_epoch_ok && controller_control_epoch_ok && rc_valid && enabled && !origin_reset;
 assign z_throttle_delta=z_active ?controller_delta:16'sd0;
 assign z_collective=z_active ?controller_collective:16'd0;
 wire signed [31:0] z_target_height=z_active ?controller_target_height:32'sd0;
 wire [15:0] z_source_reason=(controller_z_reason &16'hfbff) |
  (controller_z_reason[10] ?observation_epoch_reason:16'd0);
 assign z_reason=origin_reset ?16'd1024:!rc_valid ?16'd1:!enabled ?16'd2:!height_ready ?16'd8:!taking_off ?16'd256:controller_z_reason;
 assign z_feedback_height=fused_height;assign z_target_height_out=z_target_height;
 assign control_permission=xy_active;
 reg [31:0] navigation_sequence=0;
 always @(posedge clk)if(!rst_n)navigation_sequence<=0;else if(geometry_update)navigation_sequence<=navigation_sequence+1'b1;
 // V4 declares the connected XYZ control path. Bit17 is zero (never height_disabled);
 // bit19 remains qualification incomplete. High reason bits retain XY cause.
 wire [31:0] reasons={xy_reason[11:0],1'b1,(position_reason!=0),1'b0,(flow_reason!=0),geometry_reason};
 wire [15:0] shadow_flags={position_reason[9:0],xy_active,z_active,xy_requested,
                          controller_z_requested,xy_ready,controller_z_ready};
 // All joint state pairs are identical. The tail is big-endian >HHi:
 // collective_us, Z reason, target_height_mm. Inactive commands/target are0.
 wire [719:0] diagnostic_next={8'd5,{1'b1,1'b0,position_ready,live_velocity,height_ready,
  geometry_flow_ready,geometry_height_ready,module_fresh},8'd1,8'd0,uptime_ms,
  navigation_sequence,source_age_ms,geometry_dt_us,reasons,height_mm,bvx,bvy,wvx,wvy,
  {fused_vx_q16[30],fused_vx_q16},{fused_vy_q16[30],fused_vy_q16},fused_height,fused_vz_q16,
  position_x_q8,position_y_q8,controller_roll,controller_pitch,z_throttle_delta,shadow_flags,
  {7'd0,mapping_verified},{7'd0,rotation_compensated},z_collective,z_reason,z_target_height};
 // One complete90-byte caller-held snapshot. Hold affects telemetry only;
 // sources, math, raw masks and controller outputs continue independently.
 // Physical public masks above remain combinational; only telemetry adds1tick.
 localparam [719:0] RESET_DIAGNOSTIC={8'd5,8'h80,8'd1,8'd0,64'd0,
  32'd0,32'hffffffff,32'd0,32'h001d0080,{11{32'd0}},
  16'sd0,16'sd0,16'sd0,16'h0040,8'd0,8'd0,16'd0,16'd1,32'sd0};
 reg [719:0] diagnostic_q=RESET_DIAGNOSTIC;
 always @(posedge clk)begin
  if(!rst_n)diagnostic_q<=RESET_DIAGNOSTIC;else if(!diagnostic_hold)diagnostic_q<=diagnostic_next;
 end
 // XY-active is shadow_flags[5], diagnostic_q[85]. Capture raw targets
 // and their flag together, then mask after the SAME snapshot register.
 // Every external diagnostic bit equals the old mask-before-register form.
 assign diagnostic_body={diagnostic_q[719:144],
  diagnostic_q[85] ?diagnostic_q[143:128]:16'd0,
  diagnostic_q[85] ?diagnostic_q[127:112]:16'd0,diagnostic_q[111:0]};
endmodule
