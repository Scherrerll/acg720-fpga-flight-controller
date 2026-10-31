`timescale 1ns/1ps
// 联合 XYZ 控制数据流：厂家 MTF 几何 → 原生 ANO XY/Z 融合，
// 再按真实 20ms 节拍计算相对位置，并使用原有共享 XYZ 控制算式。
// 只有 CH7 高档请求 XYZ，低档/中档保留确认或手动选择，没有独立 Z 档位。
// 本模块输出连接飞行核心，接口连接本身不代表完成实物资格验收。
// PROOF_CONTROLLER 只允许数值控制计算，不表示安装验收。
// control_permission 仅报告计算活动状态，实际输出许可仍由核心门控决定。
// 本模块内部没有永久停机锁，实物使用状态以独立版本与测试记录为准。
// 导航顶层依次连接测距/光流几何、惯性融合、相对位移和 XYZ 控制器。
// 距离为 mm，时间接口分别为 ms/us，姿态角为百分之一度；输入速度为 mm/s×100。
module mtf_xyz_navigation_control #(parameter integer PROOF_CONTROLLER=0,PRECHECKED_YAW_RANGE=0,STARTUP_ONLY_DIAGNOSTIC_RESET=0,PRECHECKED_HEIGHT_TILT4500=0,PRECHECKED_FLOW_TILT1500=0,PRECHECKED_HEIGHT_ORIGIN=0,PRECHECKED_AZ_RANGE=0,PRECHECKED_INPUT_VELOCITY=0)(
 input wire clk,rst_n,origin_reset,diagnostic_hold,
 input wire [15:0] xy_p_value,xy_i_value,
 output wire parameter_boundary,
 // 可选的最终高度掩码化简要求调用方保证：acc_valid
 // 蕴含 pose_valid，且 origin_reset 等于 !pose_valid || !height_origin_ok。
 // 其他使用 origin_reset 的路径仍保持原有的即时响应。
 input wire height_origin_ok,
 input wire sample_valid,range_valid,flow_valid,
 input wire [31:0] distance_mm,dt_ms,source_age_ms,
 input wire signed [31:0] vx_x100,vy_x100,
 input wire velocity_range_ok,
 input wire pose_valid,
 input wire signed [15:0] roll_cdeg,pitch_cdeg,yaw_cdeg,
 input wire yaw_range_ok,
 input wire acc_valid,acc_update,input wire [31:0] acc_dt_us,
 // 启用该选项时，调用方必须保证 az 范围标志与当前数据元组严格对应。
 input wire az_range_ok,
 input wire signed [31:0] ax_mmps2,ay_mmps2,az_up_mmps2,
 input wire rc_valid,enabled,taking_off,input wire [3:0] channel_count,
 input wire [15:0] ch1,ch2,ch3,ch4,ch7,collective_us,
 input wire [63:0] uptime_ms,
 output wire [719:0] diagnostic_body,
 output wire control_permission,
 output wire position_ready,height_ready,
 output wire core_height_tail,
 output wire core_height_tail_without_acc,
 output wire core_height_state_tail,
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
 output wire [15:0] z_collective,z_reason,
 input wire height_tilt4500_ok,flow_tilt1500_ok
);
 // 一个共享乘法器和一个独立仲裁的除法器只服务新增导航域，
 // 客户端 0 为几何、1 为 XY 融合、2 为 Z 融合，
 // 客户端 3 为联合 XYZ 外环；保留原四槽仲裁与每客户端单个待办位。
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
 localparam integer CONTROL_HEIGHT_AGE_LIMIT=5000000;
 // 姿态有效性由显式标志给出，不额外用姿态年龄判定资格。
 wire geometry_height_state_numeric_tail,height_estimate_state_numeric_tail;
 wire geometry_height_state_numeric_tail_without_live_flags;
 wire geometry_update,geometry_height_ready,geometry_flow_ready;
 wire [15:0] geometry_reason;
 wire signed [31:0] height_mm,bvx,bvy,wvx,wvy;
 wire [31:0] geometry_dt_us;
 wire mapping_verified,rotation_compensated,geometry_control_verified;
 // FMT 原生 Micolink 坐标约定为前向=-rawY、右向=rawX；本安装方向
 // 相对 FMT 图示旋转 180 度，对应前向=rawY、右向=-rawX。
 // 该映射的实物确认由标定状态单独表示，源码记录本身不置标定位。
 // 高度余弦修正在核心 45 度停机边界内保持有效。
 // 光流资格仍采用更严格的 15 度倾角范围；
 // 超出该范围只撤销 XY，不取消仍有效的垂向参考。
 mtf_shared_geometry #(.AGE_LIMIT(CONTROL_HEIGHT_AGE_LIMIT),.HEIGHT_TILT_LIMIT_CDEG(4500),.FLOW_TILT_LIMIT_CDEG(1500),.SWAP_AXES(1),.NEGATE_X(0),.NEGATE_Y(1),.MAPPING_VERIFIED(0),.PRECHECKED_YAW_RANGE(PRECHECKED_YAW_RANGE),.PRECHECKED_HEIGHT_TILT4500(PRECHECKED_HEIGHT_TILT4500),.PRECHECKED_FLOW_TILT1500(PRECHECKED_FLOW_TILT1500),.PRECHECKED_INPUT_VELOCITY(PRECHECKED_INPUT_VELOCITY)) geometry(
  .clk(clk),.rst_n(rst_n),.origin_reset(origin_reset),.sample_valid(sample_valid),
  .range_valid(range_valid),.flow_valid(flow_valid),.distance_mm(distance_mm),.dt_ms(dt_ms),
  .vx_x100(vx_x100),.vy_x100(vy_x100),.velocity_range_ok(velocity_range_ok),.pose_valid(pose_valid),
  .roll_cdeg(roll_cdeg),.pitch_cdeg(pitch_cdeg),.body_yaw_cdeg(yaw_cdeg),.body_yaw_range_ok(yaw_range_ok),.body_tilt4500_ok(height_tilt4500_ok),.body_tilt1500_ok(flow_tilt1500_ok),
  .update(geometry_update),.height_ready(geometry_height_ready),.height_ready_state_numeric_tail(geometry_height_state_numeric_tail),.flow_ready(geometry_flow_ready),
  .height_ready_state_numeric_tail_without_live_flags(geometry_height_state_numeric_tail_without_live_flags),
  .reason(geometry_reason),.height_mm(height_mm),.body_vx_q16(bvx),.body_vy_q16(bvy),
  .world_vx_q16(wvx),.world_vy_q16(wvy),.dt_us(geometry_dt_us),.busy(),
  .mapping_verified(mapping_verified),.rotation_compensated(rotation_compensated),.control_verified(geometry_control_verified),
  .math_mul_start(m_request[0]),.math_mul_cancel(m_cancel[0]),
  .math_mul_a(m_a[0 +:64]),.math_mul_b(m_b[0 +:64]),
  .math_mul_busy(m_busy[0]),.math_mul_done(m_done[0]),.math_mul_result(m_result));

 // 加速度须同时具备姿态有效与原点有效；测距用于控制时还要求源龄小于 100 ms。
 // 源龄按 50 MHz 转成时钟拍数，供高度融合与控制命令时效判断。
 wire live_acc=acc_valid && pose_valid && !origin_reset;
 wire live_az_range_ok=PRECHECKED_AZ_RANGE ?az_range_ok:(az_up_mmps2>=-30000 && az_up_mmps2<=30000);
 wire module_fresh=source_age_ms<100 && range_valid;
 wire [31:0] range_age_ticks=source_age_ms<100 ?source_age_ms[6:0]*32'd50000:32'hffffffff;
 wire flow_fusion_valid,flow_fusion_qualified,flow_fusion_update,flow_correction_update;
 wire signed [31:0] fused_vx,fused_vy;
 wire signed [30:0] fused_vx_q16,fused_vy_q16;
 wire [15:0] flow_reason;
 // 此处掩码只允许数值观测，不等同于飞控的实物标定资格；
 // 本参数只影响此实例的数值资格，不会修改飞行核心的标定掩码。
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
 // XY 融合发布 Q16 mm/s 速度；Z 融合发布 mm 高度及 Q16 mm/s 垂向速度。
 wire height_estimate_ready,height_qualified_ready,height_fusion_update;
 wire signed [31:0] fused_height,fused_vz,fused_vz_q16,height_sample_az;
 wire fused_vz_q16_valid;wire [15:0] height_reason;
 wire height_vz_q16_range_raw;
 mtf_shared_height_fusion #(.AGE_LIMIT(CONTROL_HEIGHT_AGE_LIMIT),.CAL_MASK(0),.RANGE_AGE_PRECHECKED(1),.PRECHECKED_AZ_RANGE(PRECHECKED_AZ_RANGE),.REF_HEIGHT_BOUNDED(1)) height_fusion(
  .clk(clk),.rst_n(rst_n),.origin_reset(origin_reset),.range_valid(geometry_height_ready && module_fresh),
  .acc_valid(live_acc),.acc_update(acc_update),.acc_dt_us(acc_dt_us),
  .range_age_ticks(range_age_ticks),.az_range_ok(az_range_ok),
  .ref_height_mm(height_mm),.az_up_mmps2(az_up_mmps2),.valid(),.estimate_ready(height_estimate_ready),.estimate_ready_state_numeric_tail(height_estimate_state_numeric_tail),
  .qualified_ready(height_qualified_ready),.qualified_valid(),.update(height_fusion_update),
  .fused_height_mm(fused_height),.vz_mmps(fused_vz),.sample_az_mmps2(height_sample_az),
  .vz_q16(fused_vz_q16),.vz_q16_valid(fused_vz_q16_valid),.vz_q16_range_raw(height_vz_q16_range_raw),.reason(height_reason),
  .math_mul_start(m_request[2]),.math_mul_cancel(m_cancel[2]),
  .math_mul_a(m_a[128 +:64]),.math_mul_b(m_b[128 +:64]),
  .math_mul_busy(m_busy[2]),.math_mul_done(m_done[2]),.math_mul_result(m_result),
  .math_div_start(d_request[2]),.math_div_cancel(d_cancel[2]),
  .math_div_numerator(d_a[128 +:64]),.math_div_denominator(d_b[128 +:32]),
  .math_div_busy(d_busy[2]),.math_div_done(d_done[2]),.math_div_error(d_error[2]),.math_div_result(d_result));
 // 即使 CAL_MASK=0，qualified_ready 仍表示数值观测就绪。
 // 原始 estimate_ready 还会对同拍距离或加速度越界立即撤销资格。
 // 展开原 Q&&E&&G&&module_fresh&&live_acc 条件，保留原 G/E/状态机路径。
 // 高度最终有效性合并已完成的数值状态与当前传感器标志，故障可立即撤销输出。
 wire final_height_origin_ok=PRECHECKED_HEIGHT_ORIGIN ?height_origin_ok:(!origin_reset && pose_valid);
 assign height_ready=height_qualified_ready && geometry_height_state_numeric_tail &&
  height_estimate_state_numeric_tail && rst_n && final_height_origin_ok && range_valid &&
  source_age_ms<100 && acc_valid;
 // 仅核心专用的条件化简：调用方在使用前必须恢复两个原始的当前有效标志；
 // 预检查参数采用 PRECHECKED_YAW_RANGE=1、PRECHECKED_HEIGHT_TILT4500=1，
 // 并配合几何模块 HEIGHT_TILT_LIMIT_CDEG=4500，才能保证标志精确对应。
 (* syn_keep = 1 *) wire core_height_tail_kept=height_qualified_ready &&
  geometry_height_state_numeric_tail_without_live_flags && height_estimate_state_numeric_tail &&
  rst_n && final_height_origin_ok && range_valid && source_age_ms<100 && acc_valid;
 assign core_height_tail=core_height_tail_kept;
 // 调用方在最终核心边界恢复原有 acc_valid 条件。
 (* syn_keep = 1 *) wire core_height_tail_without_acc_kept=height_qualified_ready &&
  geometry_height_state_numeric_tail_without_live_flags && height_estimate_state_numeric_tail &&
  rst_n && final_height_origin_ok && range_valid && source_age_ms<100;
 assign core_height_tail_without_acc=core_height_tail_without_acc_kept;
 // 调用方恢复实时 range_valid 和 source_age<100 的精确掩码。
 (* syn_keep = 1 *) wire core_height_state_tail_kept=height_qualified_ready &&
  geometry_height_state_numeric_tail_without_live_flags && height_estimate_state_numeric_tail &&
  rst_n && final_height_origin_ok;
 assign core_height_state_tail=core_height_state_tail_kept;
 wire live_velocity=flow_fusion_valid && flow_fusion_qualified && geometry_flow_ready && module_fresh && live_acc;
 // 采用两个独立代号：观测代号不受遥控、解锁或模式变化影响。
 // 失效状态只在采样到其上升沿时推进代号，不在每个失效时钟重复递增。
 // 观测代号跟随高度观测失效或原点重置，控制代号另跟随 RC/解锁失效，阻断旧事务续用。
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
  live_az_range_ok && live_yaw_range_ok;
 wire observation_bad=!height_ready || !height_vz_q16_range_raw;
 wire control_bad=observation_bad || !rc_valid || !enabled;
 reg observation_bad_d=1,control_bad_d=1,origin_d=0,manual_d=0;
 reg [7:0] observation_epoch=0,control_epoch=0;
 reg [15:0] observation_epoch_reason=0,control_revoke_reason=0;
 wire [15:0] raw_revoke_reason=origin_reset ?16'd1024:observation_bad || !position_internal_ready || !raw_numeric_ok ?16'd4:
  !rc_valid || channel_count<7 || !(raw_requested || raw_manual) ?16'd1:!enabled ?16'd2:!raw_centered ?16'd16:16'd1;
 wire observation_event=(observation_bad && !observation_bad_d) || (origin_reset && !origin_d);
 wire control_event=observation_event || (control_bad && !control_bad_d);
 // 事件是较晚到达的实时安全条件，先独立预计算固定增量，
 // 再按事件选择结果，保持模 256 的代号及捕获边沿一致。
 (* syn_keep = 1 *) wire [7:0] observation_incremented=observation_epoch+8'd1;
 (* syn_keep = 1 *) wire [7:0] control_incremented=control_epoch+8'd1;
 wire [7:0] next_observation_epoch=observation_event ? observation_incremented:observation_epoch;
 wire [7:0] next_control_epoch=control_event ? control_incremented:control_epoch;
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
 // P 级把全部上游元数据与速度一起锁存；本地计时器后移一拍，
 // 同时消费一拍前的速度，从而保留原回调对应的数据元组，
 // 随后用 P 级元数据让 C 级仍与同一原始回调样本对齐。
 // P 级将速度、姿态、RC 与有效性一并寄存，使后续积分使用同一拍的数据。
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
   p_live<=live_velocity;p_height_valid<=height_ready && height_vz_q16_range_raw;p_acc_valid<=live_acc;p_rc_valid<=rc_valid;p_enabled<=enabled;
   p_observation_epoch<=next_observation_epoch;p_control_epoch<=next_control_epoch;
   p_vx<=raw_fvx;p_vy<=raw_fvy;p_height<=fused_height;p_ax<=ax_mmps2;p_ay<=ay_mmps2;p_az<=height_sample_az;p_yaw<=yaw_cdeg;
   p_height_update<=height_fusion_update;p_sample_update<=acc_update;p_sample_dt<=acc_dt_us;p_vz<=fused_vz_q16;p_collective<=collective_us;
   p_channel_count<=channel_count;p_ch1<=ch1;p_ch2<=ch2;p_ch3<=ch3;p_ch4<=ch4;p_ch7<=ch7;
  end
 end
 wire position_stage_ok=p_live && p_observation_epoch==observation_epoch;
 // 真实 50MHz/20ms 计时器；源数据的公开原始掩码不直接驱动积分器使能。
 // 有效观测持续期间每 1000000 拍积分一次，即 50 MHz 下固定 20 ms。
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
 // 相对位置以 Q8 mm 发布；公开位置失效时归零，内部积分器另受原点/观测取消。
 assign position_internal_ready=integral_valid && position_stage_ok;
 assign position_ready=position_internal_ready && live_velocity && !origin_reset;
 assign position_x_q8=position_ready ?position_raw_x:32'sd0;
 assign position_y_q8=position_ready ?position_raw_y:32'sd0;
 // C 级将位置发布值、位置年龄与 P 级重定时后的元数据原子交接，
 // 控制器在不改算法的情况下，恰好晚两拍看到原回调元组，
 // 避免将当前元数据与旧位置混用。
 // C 级再锁存位置相关信息和 P 级元数据，避免旧速度搭配当前 RC 或姿态。
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
   // 光流控制消费速度，不依赖可选的遥测位置累加器；
   // 显示累加器的复位或溢出不应撤销光流速度 PI。
   c_position_valid<=position_stage_ok;c_position_update<=position_tick && position_stage_ok;
   c_observation_epoch<=p_observation_epoch;c_control_epoch<=p_control_epoch;
   c_position_age<=range_age_ticks;c_x<=position_internal_ready ?position_raw_x:0;c_y<=position_internal_ready ?position_raw_y:0;
   c_height_valid<=p_height_valid;c_acc_valid<=p_acc_valid;c_rc_valid<=p_rc_valid;c_enabled<=p_enabled;
   c_vx<=p_vx;c_vy<=p_vy;c_height<=p_height;c_ax<=p_ax;c_ay<=p_ay;c_az<=p_az;c_yaw<=p_yaw;
   c_height_update<=p_height_update;c_sample_update<=p_sample_update;c_sample_dt<=p_sample_dt;c_vz<=p_vz;c_collective<=p_collective;
   c_channel_count<=p_channel_count;c_ch1<=p_ch1;c_ch2<=p_ch2;c_ch3<=p_ch3;c_ch4<=p_ch4;c_ch7<=p_ch7;
  end
 end
 // 控制器只消费代号仍匹配的事务；代号变化会撤销流水线中的旧观测或旧控制请求。
 wire controller_observation_epoch_ok=c_observation_epoch==observation_epoch;
 wire controller_control_epoch_ok=c_control_epoch==control_epoch;
  wire controller_requested,controller_ready,controller_active;
 wire controller_z_requested,controller_z_ready,controller_z_active;
 wire signed [15:0]controller_delta;wire[15:0]controller_collective,controller_z_reason;
 wire signed [31:0]controller_target_height;
 wire signed [15:0] controller_roll,controller_pitch;wire [15:0] controller_reason;
 mtf_xyz_hold_control #(.CAL_MASK(PROOF_CONTROLLER ? 8'hff:8'h00),.VELOCITY_FRAC_BITS(16)) controller_proof(
  .xy_p_value(xy_p_value),.xy_i_value(xy_i_value),.parameter_boundary(parameter_boundary),
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
 // 公开有效性掩码即时生效，不反馈到内部两级流水线。
 // 数值就绪仍独立于遥控、使能和回中条件，保持原行为。
 // CH7 高档请求 XY，数值就绪与实际活动分别报告；活动还须 Z 环和实时权限成立。
 assign xy_requested=raw_requested;
 assign xy_ready=controller_ready && live_velocity && raw_numeric_ok && controller_observation_epoch_ok && !origin_reset;
 assign xy_active=controller_active && controller_z_active && controller_z_ready && xy_ready && controller_control_epoch_ok && raw_requested && rc_valid && enabled;
 // 源代号撤销复用原有原点输入，保存的原因描述最近一次观测代号，
 // 不会错误地引用旧控制元组中的原因。
 // 遥控或手动模式引起的控制代号事件不覆盖该源失效原因。
 // 公开诊断报告最近一次撤销；排空旧控制元组时的内部 enabled=0，
 // 不能把遥控或回中事件误标记为原因 2。
 wire [15:0] source_reason=(controller_reason &16'hfbff) |
  (controller_reason[10] ?observation_epoch_reason:16'd0);
 assign xy_reason=origin_reset ?16'd1024:!raw_requested ?16'd1:!enabled ?16'd2:!xy_ready ?16'd4:!taking_off ?16'd256:controller_reason;
 // 实时源资格撤销后，公开命令不能继续保留陈旧数值。
 // payload 保留控制器原始角度供同拍遥测；实际滚转/俯仰命令仅在 XY 活动时输出。
 assign xy_payload_roll=controller_roll;assign xy_payload_pitch=controller_pitch;
 assign xy_roll_target=xy_active ? controller_roll:16'sd0;
 assign xy_pitch_target=xy_active ? controller_pitch:16'sd0;
 // Z 输出单独经过当前高度、垂向速度范围、代号、RC 与解锁门控，失效即撤销。
 assign z_active=controller_z_active && controller_z_ready && height_ready && height_vz_q16_range_raw && controller_observation_epoch_ok && controller_control_epoch_ok && rc_valid && enabled && !origin_reset;
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
 // 诊断版本 V4 表示已连接 XYZ 控制通路；位 17 固定为零，表示不使用 height_disabled，
 // 位 19 保留资格未完成标志，高位原因字段保留 XY 原因。
 wire [31:0] reasons={xy_reason[11:0],1'b1,(position_reason!=0),1'b0,(flow_reason!=0),geometry_reason};
 wire [15:0] shadow_flags={position_reason[9:0],xy_active,z_active,xy_requested,
                          controller_z_requested,xy_ready,controller_z_ready};
 // 联合状态字段保持同拍一致；尾部按大端 >HHi 排列为：
 // collective_us、Z 原因和 target_height_mm；未活动时命令与目标为零。
 // 诊断包同时打包几何、融合、位置和命令；各定点字段沿用对应模块的原始尺度。
 wire [719:0] diagnostic_next={8'd5,{1'b1,1'b0,position_ready,live_velocity,height_ready,
  geometry_flow_ready,geometry_height_ready,module_fresh},8'd1,8'd0,uptime_ms,
  navigation_sequence,source_age_ms,geometry_dt_us,reasons,height_mm,bvx,bvy,wvx,wvy,
  {fused_vx_q16[30],fused_vx_q16},{fused_vy_q16[30],fused_vy_q16},fused_height,fused_vz_q16,
  position_x_q8,position_y_q8,controller_roll,controller_pitch,z_throttle_delta,shadow_flags,
  {7'd0,mapping_verified},{7'd0,rotation_compensated},z_collective,z_reason,z_target_height};
 // 调用方保持完整的 90 字节快照；hold 仅作用于遥测，
 // 源数据、数学计算、原始掩码和控制器输出继续独立更新。
 // 上方公开控制掩码仍为组合逻辑，只有遥测增加一拍延迟。
 localparam [719:0] RESET_DIAGNOSTIC={8'd5,8'h80,8'd1,8'd0,64'd0,
  32'd0,32'hffffffff,32'd0,32'h001d0080,{11{32'd0}},
  16'sd0,16'sd0,16'sd0,16'h0040,8'd0,8'd0,16'd0,16'd1,32'sd0};
 // diagnostic_hold 只冻结 90 字节诊断快照，不暂停传感器、融合计算和实时控制门控。
 reg [719:0] diagnostic_q=RESET_DIAGNOSTIC;
 always @(posedge clk)begin
  if(STARTUP_ONLY_DIAGNOSTIC_RESET)begin
   // 启用该快照模式时，调用方必须保证复位从低开始且释放后不再重入。
   // 复位释放前保留初始化载荷，不延后后续快照捕获。
   if(rst_n && !diagnostic_hold)diagnostic_q<=diagnostic_next;
  end else begin
   if(!rst_n)diagnostic_q<=RESET_DIAGNOSTIC;else if(!diagnostic_hold)diagnostic_q<=diagnostic_next;
  end
 end
 // XY 活动位为 shadow_flags[5]，即 diagnostic_q[85]；原始目标
 // 与活动位一起取快照，再在同一快照寄存器后进行掩码处理。
 // 各外部诊断位与原先寄存前掩码的形式保持一致。
 // 诊断角度与该快照内的 XY 活动位一起判定，避免冻结后混入当前活动状态。
 assign diagnostic_body={diagnostic_q[719:144],
  diagnostic_q[85] ?diagnostic_q[143:128]:16'd0,
  diagnostic_q[85] ?diagnostic_q[127:112]:16'd0,diagnostic_q[111:0]};
endmodule
