`timescale 1ns/1ps
// Native MTF -> provisional world observation -> existing ANO fusion -> position.
// This is an observation branch. Nothing returned here drives flight_core/PWM.
// PROOF_CONTROLLER only permits synthetic bench tests of the existing outer loop.
// The production top instantiates zero, and control_permission is always false.
module mtf_navigation_shadow #(parameter integer PROOF_CONTROLLER=0)(
 input wire clk,rst_n,origin_reset,
 input wire sample_valid,range_valid,flow_valid,
 input wire [31:0] distance_mm,dt_ms,source_age_ms,
 input wire signed [31:0] vx_x100,vy_x100,
 input wire pose_valid,input wire [31:0] pose_age_ticks,
 input wire signed [15:0] roll_cdeg,pitch_cdeg,yaw_cdeg,
 input wire acc_valid,acc_update,input wire [31:0] acc_dt_us,
 input wire signed [31:0] ax_mmps2,ay_mmps2,az_up_mmps2,
 input wire rc_valid,enabled,input wire [3:0] channel_count,
 input wire [15:0] ch1,ch2,ch3,ch4,ch7,collective_us,
 input wire [63:0] uptime_ms,
 output wire [719:0] diagnostic_body,
 output wire control_permission,
 output wire position_ready,height_ready,
 output wire signed [31:0] position_x_q8,position_y_q8
);
 // One shared multiply and one independently arbitrated divide serve only
 // this added navigation domain. Client0=geometry,1=XY,2=Z,3=outer loop.
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
 mtf_shared_geometry #(.SWAP_AXES(1),.NEGATE_X(0),.NEGATE_Y(1),.MAPPING_VERIFIED(0)) geometry(
  .clk(clk),.rst_n(rst_n),.origin_reset(origin_reset),.sample_valid(sample_valid),
  .range_valid(range_valid),.flow_valid(flow_valid),.distance_mm(distance_mm),.dt_ms(dt_ms),
  .vx_x100(vx_x100),.vy_x100(vy_x100),.pose_valid(pose_valid),.pose_age_ticks(pose_age_ticks),
  .roll_cdeg(roll_cdeg),.pitch_cdeg(pitch_cdeg),.body_yaw_cdeg(yaw_cdeg),
  .update(geometry_update),.height_ready(geometry_height_ready),.flow_ready(geometry_flow_ready),
  .reason(geometry_reason),.height_mm(height_mm),.body_vx_q16(bvx),.body_vy_q16(bvy),
  .world_vx_q16(wvx),.world_vy_q16(wvy),.dt_us(geometry_dt_us),.busy(),
  .mapping_verified(mapping_verified),.rotation_compensated(rotation_compensated),.control_verified(geometry_control_verified),
  .math_mul_start(m_request[0]),.math_mul_cancel(m_cancel[0]),
  .math_mul_a(m_a[0 +:64]),.math_mul_b(m_b[0 +:64]),
  .math_mul_busy(m_busy[0]),.math_mul_done(m_done[0]),.math_mul_result(m_result));

 wire live_acc=acc_valid && pose_valid && pose_age_ticks<3000000 && !origin_reset;
 wire module_fresh=source_age_ms<100 && range_valid;
 wire [31:0] range_age_ticks=source_age_ms<100 ? source_age_ms*32'd50000:32'hffffffff;
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
 assign height_ready=height_qualified_ready && geometry_height_ready && module_fresh && live_acc;
 wire live_velocity=flow_fusion_valid && flow_fusion_qualified && geometry_flow_ready && module_fresh && live_acc;
 // Use a real 20ms local-clock interval, not the radio's 5Hz arrival period.
 reg [19:0] position_timer=0;reg position_tick=0;
 always @(posedge clk)begin
  position_tick<=0;
  if(!rst_n || origin_reset || !live_velocity)position_timer<=0;
  else if(position_timer==999999)begin position_timer<=0;position_tick<=1;end
  else position_timer<=position_timer+1'b1;
 end
 wire position_update,integral_valid;wire [31:0] position_age;wire [15:0] position_reason;
 mtf_position_integrator position(
  .clk(clk),.rst_n(rst_n),.cancel(origin_reset),.update_in(position_tick),.sources_valid(live_velocity),
  .dt_us(32'd20000),.vx_q16({fused_vx_q16[30],fused_vx_q16}),.vy_q16({fused_vy_q16[30],fused_vy_q16}),
  .update(position_update),.busy(),.valid(integral_valid),.x_q8(position_x_q8),.y_q8(position_y_q8),
  .age_ticks(position_age),.reason(position_reason));
 assign position_ready=integral_valid && live_velocity;

 wire shadow_requested,shadow_ready,shadow_active,shadow_height_requested,shadow_height_ready,shadow_height_active;
 wire signed [15:0] shadow_roll,shadow_pitch,shadow_throttle;
 wire [15:0] shadow_collective,shadow_reason,shadow_height_reason;
 mtf_shared_hold_control #(.CAL_MASK(PROOF_CONTROLLER ? 8'hff:8'h00),.VELOCITY_FRAC_BITS(16)) controller_proof(
  .clk(clk),.rst_n(rst_n),.rc_valid(rc_valid),.channel_count(channel_count),
  .ch1(ch1),.ch2(ch2),.ch3(ch3),.ch4(ch4),.ch7(ch7),.enabled(enabled),
  .position_valid(position_ready),.height_valid(height_ready && fused_vz_q16_valid),
  .position_update(position_update),.height_update(height_fusion_update),
  .sample_update(acc_update),.sample_dt_us(acc_dt_us),.position_age(position_age),.position_dt_us(32'd20000),
  .x_q8(position_x_q8),.y_q8(position_y_q8),.vx({fused_vx_q16[30],fused_vx_q16}),
  .vy({fused_vy_q16[30],fused_vy_q16}),.height_mm(fused_height),.vz(fused_vz_q16),.yaw_cdeg(yaw_cdeg),
  .acc_valid(live_acc),.ax_mmps2(ax_mmps2),.ay_mmps2(ay_mmps2),.az_mmps2(height_sample_az),
  .collective_us(collective_us),.requested(shadow_requested),.ready(shadow_ready),.active(shadow_active),
  .height_requested(shadow_height_requested),.height_ready(shadow_height_ready),.height_active(shadow_height_active),
  .reason(shadow_reason),.height_reason(shadow_height_reason),.collective_target_us(shadow_collective),
  .roll_target(shadow_roll),.pitch_target(shadow_pitch),.throttle_delta(shadow_throttle),
  .requested_climb_mmps(),.target_height_mm(),
  .math_mul_start(m_request[3]),.math_mul_cancel(m_cancel[3]),
  .math_mul_a(m_a[192 +:64]),.math_mul_b(m_b[192 +:64]),
  .math_mul_busy(m_busy[3]),.math_mul_done(m_done[3]),.math_mul_result(m_result),
  .math_div_start(d_request[3]),.math_div_cancel(d_cancel[3]),
  .math_div_numerator(d_a[192 +:64]),.math_div_denominator(d_b[192 +:32]),
  .math_div_busy(d_busy[3]),.math_div_done(d_done[3]),.math_div_error(d_error[3]),.math_div_result(d_result));
 assign control_permission=1'b0;
 reg [31:0] navigation_sequence=0;
 always @(posedge clk)if(!rst_n)navigation_sequence<=0;else if(geometry_update)navigation_sequence<=navigation_sequence+1'b1;
 wire [31:0] reasons={12'd0,1'b1,(position_reason!=0),(height_reason!=0),(flow_reason!=0),geometry_reason};
 wire [15:0] shadow_flags={position_reason[9:0],shadow_active,shadow_height_active,shadow_requested,
                          shadow_height_requested,shadow_ready,shadow_height_ready};
 assign diagnostic_body={8'd1,{1'b0,1'b1,position_ready,live_velocity,height_ready,
  geometry_flow_ready,geometry_height_ready,module_fresh},8'd1,8'd0,uptime_ms,
  navigation_sequence,source_age_ms,geometry_dt_us,reasons,height_mm,bvx,bvy,wvx,wvy,
  {fused_vx_q16[30],fused_vx_q16},{fused_vy_q16[30],fused_vy_q16},fused_height,fused_vz_q16,
  position_x_q8,position_y_q8,shadow_roll,shadow_pitch,shadow_throttle,shadow_flags,
  {7'd0,mapping_verified},{7'd0,rotation_compensated},64'd0};
endmodule
