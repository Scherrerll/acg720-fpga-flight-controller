// 移植 ANO 默认增益控制器，保留安装后的机体轴定义及故障门控。
// 完整输出配置通过离线编译；板卡发布仍须完成停机状态下的板上检查。
// 飞行核心集成姿态估计、解锁门控、控制环、四电机PWM及独立水面推进接口。
// 时钟为50MHz；脉宽用us、姿态角用百分之一度、采样间隔用时钟数表示。
// 本层默认运行范围 1200..2000 微秒、飞行 PWM 帧 2500 微秒、校准 2048 样本；均为声明默认值，顶层可覆盖。
// ARM_LOW/HIGH_TICKS 默认各 25000000 拍（0.5 秒），CONTROL_TIMEOUT/MAX_DT 默认各 3000000 拍（60 毫秒）。
// LEVEL_TRIM 默认关闭且矩阵为 Q24 单位矩阵；上层启用时必须同时传入实际安装修正矩阵。
// pilot_norm 为 ±1 的 Q16 摇杆，采样间隔为微秒；高度为毫米，世界加速度为 mm/s²，陀螺精细口为 Q12 计数。
// TAKEOVER_PICKUP_TICKS 保留为兼容参数，当前油门接管状态输出固定为零；高度降级由 height_loss_fallback 独立处理。
module flight_core #(
// DIAG_TAP_BEGIN
    parameter integer diag_startup_only_tap_reset=0,
// DIAG_TAP_END
    parameter integer LEVEL_TRIM_ENABLE=0,
    parameter signed [31:0] LEVEL_R00_Q24=16777216,
    parameter signed [31:0] LEVEL_R01_Q24=0,
    parameter signed [31:0] LEVEL_R02_Q24=0,
    parameter signed [31:0] LEVEL_R10_Q24=0,
    parameter signed [31:0] LEVEL_R11_Q24=16777216,
    parameter signed [31:0] LEVEL_R12_Q24=0,
    parameter signed [31:0] LEVEL_R20_Q24=0,
    parameter signed [31:0] LEVEL_R21_Q24=0,
    parameter signed [31:0] LEVEL_R22_Q24=16777216,
    parameter integer RUN_MAX_US=2000,
    parameter integer RUN_MIN_US=1200, // ANO 默认 idle_speed_pwm=20%，对应 1000+200 微秒。
    parameter integer CAL_SAMPLES=2048,
    parameter integer OUTPUT_FRAME_US=2500,
    parameter integer ARM_LOW_TICKS=25000000,
    parameter integer ARM_HIGH_TICKS=25000000,
    parameter integer FLIGHT_STATE_TICKS_PER_MS=50000,
    parameter integer CONTROL_TIMEOUT_TICKS=3000000, // 请求与控制命令各自独立的看门狗期限，以时钟拍计。
    parameter integer MAX_DT_TICKS=3000000, // 数值积分真实步长的上限，以时钟拍计。
    parameter integer TAKEOVER_PICKUP_TICKS=5000000,
    parameter integer RAW_TELEMETRY_COMMANDS=0 // 仅改变显示快照的传输取值，不改变执行器命令。
)(
    input wire clk50,imu_miso,rc_ppm_in,
    input wire hold_active,altitude_active,vertical_available,auto_takeoff,
    input wire signed [17:0] pilot_norm_x,pilot_norm_y,
    input wire pilot_norm_update,pilot_norm_valid,input wire [15:0] pilot_norm_dt_us,
    output wire taking_off_out,
    output wire height_fallback_active,
    output wire [3:0] flight_state_flags,
    input wire signed [31:0] vertical_height_mm,
    input wire signed [15:0] hold_roll_cdeg,hold_pitch_cdeg,hold_throttle_delta_us,
    input wire [15:0] hold_collective_us,
    output wire imu_sck,imu_mosi,imu_cs_n,imu_gyro_cs_n,
    output reg led2=0,
    output wire led3,
    output wire motor1_pwm,motor2_pwm,motor3_pwm,motor4_pwm,
    output wire water_left_pwm,water_right_pwm,
    output wire rc_valid,
    output wire [3:0] channel_count,
    output wire [15:0] ch1,ch2,ch3,ch4,ch5,ch6,ch7,ch8,
    output wire body_yaw_range_ok,
    output wire pose_update,pose_valid,
    output wire [31:0] pose_dt_ticks,
    output wire signed [15:0] body_roll_cdeg,body_pitch_cdeg,body_yaw_cdeg,
    output wire signed [16:0] body_gx,body_gy,body_gz,
    output wire signed [28:0] body_gx_q12,body_gy_q12,body_gz_q12,
    output wire armed_usable,control_enabled,command_fresh,
    output wire navigation_enabled,
    output wire parameter_write_safe,
    output wire armed_raw,hold_consumed,altitude_consumed,
    output wire [15:0] base_throttle_us,
    output wire throttle_takeover_active,
    output wire [15:0] throttle_pickup_us,
    output wire [7:0] sticky_yaw_fault,
    output wire signed [31:0] world_ax_mmps2,world_ay_mmps2,world_az_up_mmps2,
    output wire linear_accel_valid,
    output wire signed [15:0] raw_ax_counts,raw_ay_counts,raw_az_counts,
    output wire raw_accel_valid,
    output wire [31:0] raw_accel_age_ticks,
    output wire [863:0] telemetry_body,
 output wire body_tilt4500_ok,body_tilt1500_ok,
    output wire diag_raw_valid,diag_pose_valid,diag_fault_valid,
    output wire [207:0] diag_raw_body,
    output wire [223:0] diag_pose_body,
    output wire [703:0] diag_fault_body,
    output wire [31:0] diag_raw_tick,diag_pose_tick,diag_fault_tick,
    output wire [31:0] diag_clock_ticks,diag_max_accept_gap,diag_raw_count,diag_pose_count
);
    // 上电计数饱和后释放核心复位，其他功能块共享该启动基准。
    reg [7:0] boot=0;
    always @(posedge clk50) if(boot!=8'hFF) boot<=boot+1'b1;
    wire rst_n=boot==8'hFF;
    reg [24:0] heartbeat=0;
    always @(posedge clk50) begin
        if(heartbeat==24999999) begin heartbeat<=0; led2<=~led2; end
        else heartbeat<=heartbeat+1'b1;
    end
    wire calibrated,attitude_valid,attitude_update,link_usable;
    wire [95:0] accepted_raw;
    wire [31:0] dt_ticks,accepted_count,rejected_count;
    wire [7:0] imu_reason,who,pwr,attitude_fault;
    wire [15:0] cal_count;
    wire signed [15:0] sensor_roll,sensor_pitch,sensor_yaw,bias_x,bias_y,bias_z,filtered_gx,filtered_gy,filtered_gz;
    wire signed [31:0] sensor_world_ax,sensor_world_ay,sensor_world_az;
    wire signed [31:0] fine_gx,fine_gy,fine_gz;
    // 归一化原始范围 ±32767、启动零偏不超过 164 计数，并使用正交安装矩阵时，
    // sqrt(3)×(32767+164)<57039 计数，带 Q12 小数后适合 29 位有符号数。
    // 角速度精细值保留Q12小数；Y、Z轴符号与下方姿态一起转换到机体坐标系。
    wire signed [28:0] gx_q12=fine_gx;
    wire signed [28:0] gy_q12=-$signed(fine_gy);
    wire signed [28:0] gz_q12=-$signed(fine_gz);
    // IMU流水线提供已校准姿态、去偏角速度、世界加速度以及接受/拒绝样本诊断。
    imu_pipeline #(
// DIAG_TAP_BEGIN
.diag_startup_only_tap_reset(diag_startup_only_tap_reset),
// DIAG_TAP_END
.LEVEL_TRIM_ENABLE(LEVEL_TRIM_ENABLE),.LEVEL_R00_Q24(LEVEL_R00_Q24),.LEVEL_R01_Q24(LEVEL_R01_Q24),.LEVEL_R02_Q24(LEVEL_R02_Q24),.LEVEL_R10_Q24(LEVEL_R10_Q24),.LEVEL_R11_Q24(LEVEL_R11_Q24),.LEVEL_R12_Q24(LEVEL_R12_Q24),.LEVEL_R20_Q24(LEVEL_R20_Q24),.LEVEL_R21_Q24(LEVEL_R21_Q24),.LEVEL_R22_Q24(LEVEL_R22_Q24),.CAL_SAMPLES(CAL_SAMPLES),.MAX_DT_TICKS(MAX_DT_TICKS)) imu(
        .clk50(clk50),.rst_n(rst_n),.imu_miso(imu_miso),
        .imu_sck(imu_sck),.imu_mosi(imu_mosi),.imu_cs_n(imu_cs_n),.imu_gyro_cs_n(imu_gyro_cs_n),
        .calibrated(calibrated),.attitude_valid(attitude_valid),
        .attitude_update(attitude_update),.link_usable(link_usable),
        .accepted_raw(accepted_raw),.dt_ticks(dt_ticks),
        .accepted_count(accepted_count),.rejected_count(rejected_count),
        .reason(imu_reason),.who(who),.pwr(pwr),.attitude_fault(attitude_fault),
        .cal_count(cal_count),.roll(sensor_roll),.pitch(sensor_pitch),.yaw(sensor_yaw),.yaw_range_ok(body_yaw_range_ok),.tilt4500_ok(body_tilt4500_ok),.tilt1500_ok(body_tilt1500_ok),
        .filtered_gx(filtered_gx),.filtered_gy(filtered_gy),.filtered_gz(filtered_gz),
        .filtered_gx_q12(fine_gx),.filtered_gy_q12(fine_gy),.filtered_gz_q12(fine_gz),
        .world_ax(sensor_world_ax),.world_ay(sensor_world_ay),.world_az_mmps2(sensor_world_az),.linear_accel_valid(linear_accel_valid),
        .accepted_raw_age_ticks(raw_accel_age_ticks),
        .bias_x(bias_x),.bias_y(bias_y),.bias_z(bias_z),
        .diag_taking_off(taking_off),.diag_gate_event(gate_event_pulse),
        .diag_raw_valid(diag_raw_valid),.diag_raw_body(diag_raw_body),.diag_raw_tick(diag_raw_tick),
        .diag_pose_valid(diag_pose_valid),.diag_pose_body(diag_pose_body),.diag_pose_tick(diag_pose_tick),
        .diag_fault_valid(diag_fault_valid),.diag_fault_body(diag_fault_body),.diag_fault_tick(diag_fault_tick),
        .diag_clock_ticks(diag_clock_ticks),.diag_max_accept_gap(diag_max_accept_gap),
        .diag_raw_count(diag_raw_count),.diag_pose_count(diag_pose_count));
    // 估计器保持既定传感器坐标系；在控制接口同时变换
    // 其倾角和校正后的陀螺，避免反馈使用不同坐标系。
    // 机体系为 X 前/Y 右/Z 下：右侧下沉横滚、机头上仰俯仰、
    // 俯视顺时针偏航为正。当前固定安装变换为
    // gyro_body=diag(+1,-1,-1)×gyro_sensor，为行列式 +1 的正常旋转。
    wire signed [15:0] roll=sensor_roll;
    wire signed [15:0] pitch=-sensor_pitch;
    wire signed [15:0] raw_gx=accepted_raw[47:32];
    wire signed [15:0] raw_gy=accepted_raw[31:16];
    wire signed [15:0] raw_gz=accepted_raw[15:0];
    wire signed [16:0] gx={filtered_gx[15],filtered_gx};
    // bias-raw 等价于 -(raw-bias)，无需第二个加法器或 16 位取反。
    // 完整校正范围 -65535..65535，以 17 位有符号数保留。
    wire signed [16:0] gy=-$signed({filtered_gy[15],filtered_gy});
    wire signed [16:0] gz=-$signed({filtered_gz[15],filtered_gz});
    wire [15:0] rc_sequence;
    wire rc_update;
    wire flight_permitted,water_mode,water_enabled,water_neutral,water_rc_fresh;
    wire [15:0] water_left_us,water_right_us;
    // 水面模式切换同时检查解锁、起飞、命令和PWM帧状态，以及四路有效脉宽均为1000us。
    // 该判断依据飞行输出状态，不能用遥测快照代替。
    wire flight_stopped=!armed_raw && !taking_off && !command_fresh && !pwm_frame_active &&
        effective1_us==1000 && effective2_us==1000 && effective3_us==1000 && effective4_us==1000;
    // 水面仲裁器共用当前PPM数据，独立检查遥控新鲜度，并以flight_permitted约束飞行解锁。
    water_drive_control water_control(.clk(clk50),.rst_n(rst_n),
        .rc_update(rc_update),.rc_valid(rc_valid),.channel_count(channel_count),
        .ch1(ch1),.ch2(ch2),.ch3(ch3),.ch4(ch4),.ch5(ch5),.ch6(ch6),.ch7(ch7),.ch8(ch8),
        .flight_armed(armed_raw),.flight_stopped(flight_stopped),
        .flight_permitted(flight_permitted),.water_mode(water_mode),.water_enabled(water_enabled),
        .left_us(water_left_us),.right_us(water_right_us),.rc_fresh(water_rc_fresh));
    // 水面PWM使用独立20ms帧和换向中位等待；飞行四路默认使用2.5ms帧。
    water_pwm_pair water_outputs(.clk(clk50),.rst_n(rst_n),.enable(water_enabled),
        .left_us(water_left_us),.right_us(water_right_us),
        .left_pwm(water_left_pwm),.right_pwm(water_right_pwm),
        .latched_left_us(),.latched_right_us(),.frame_active(),.neutral_output(water_neutral));
    // 完整遥控帧的更新脉冲同时供水面新鲜度计时使用，各通道脉宽单位为us。
    rc_ppm receiver(.clk(clk50),.rst_n(rst_n),.ppm_in(rc_ppm_in),
        .frame_update(rc_update),.valid(rc_valid),.channel_count(channel_count),
        .ch1(ch1),.ch2(ch2),.ch3(ch3),.ch4(ch4),.ch5(ch5),.ch6(ch6),.ch7(ch7),.ch8(ch8),
        .frame_sequence(rc_sequence));

    // 目标与反馈使用同一机体系；摇杆极性、旋翼转向及增益
    // 仍须在实际飞行前进行物理验证。
    function signed [31:0] yaw_target;
        input [15:0] channel;
        reg signed [31:0] deviation;
        begin
            deviation=$signed({1'b0,channel})-32'sd1500;
            if(deviation>500) deviation=500;
            if(deviation< -500) deviation=-500;
            deviation=deviation>65 ? deviation-65 : deviation< -65 ? deviation+65 : 0;
            yaw_target=(deviation*46/100)*100; // 原程序先截断为整数度/秒，再放大为百分之一度/秒。
            if(yaw_target>20000) yaw_target=20000;
            if(yaw_target< -20000) yaw_target=-20000;
        end
    endfunction
    // 飞行运行脉宽配置必须位于1000..2000us，默认运行范围为1200..2000us。
    localparam RUN_RANGE_OK=RUN_MIN_US>=1000 && RUN_MIN_US<RUN_MAX_US && RUN_MAX_US<=2000;
    // 非法参数在综合实现中保持禁止输出，并在仿真阶段报错。
    // 运行上下限配置不合法时，综合后的许可也保持关闭，仿真则通过下方 fatal 直接拒绝配置。
    generate if(!RUN_RANGE_OK) begin : invalid_run_min
        initial $fatal(1,"require 1000 <= RUN_MIN_US < RUN_MAX_US <= 2000");
    end endgenerate
    function signed [15:0] bounded_hold_angle;
        input signed [15:0] angle;
        begin bounded_hold_angle=angle>16'sd2500 ? 16'sd2500 :
            angle< -16'sd2500 ? -16'sd2500 : angle;end
    endfunction
    // 先寄存模式选择，再进行目标多路选择；
    // 公开电机有效性另由实时遥控/传感器条件直接屏蔽。
    // 导航模式先寄存再选择目标，最终公开命令仍由实时健康和停机条件直接屏蔽。
    reg hold_override=0,altitude_override=0;
    reg controller_run=0;
    wire controller_enabled;
    reg yaw_sample_update=0;
    reg [31:0] yaw_dt_accum=0,yaw_dt_ticks=0;
    // 原 Att_2level_Ctrl 在 taking_off 清除公开角度目标之前更新 ATT_STAB 微调；
    // 因此停机时仍保持该 6 毫秒回调运行，
    // 偏航及角速度内环继续使用各自独立的使能和复位调度。
    reg manual_outer_update=0;
    reg [31:0] manual_outer_dt_accum=0,manual_outer_dt_ticks=0;
    always @(posedge clk50) begin
        if(!rst_n) begin hold_override<=0;altitude_override<=0;end
        else begin hold_override<=hold_active && control_enabled && !height_fallback_active;altitude_override<=altitude_active && control_enabled && !height_fallback_active;end
    end
    wire signed [15:0] manual_roll_cdeg,manual_pitch_cdeg;
    wire manual_angle_update,manual_angle_busy;
    wire [7:0] manual_angle_fault;
    // 独立遥控分支持续更新；原生高度丢失不得冻结驾驶员摇杆输入。
    // 独立10ms摇杆通路持续更新，高度丢失后的接管不会依赖被冻结的导航输入。
    reg [19:0] fallback_stick_phase=0;
    reg fallback_stick_tick=0;
    always @(posedge clk50)begin
        fallback_stick_tick<=0;
        if(!rst_n || !rc_valid)fallback_stick_phase<=0;
        else if(fallback_stick_phase==499999)begin fallback_stick_phase<=0;fallback_stick_tick<=1;end
        else fallback_stick_phase<=fallback_stick_phase+1'b1;
    end
    wire signed [17:0] fallback_norm_x,fallback_norm_y;
    wire fallback_norm_update,fallback_norm_valid,fallback_norm_fault;
    wire [15:0] fallback_norm_dt;
    ano_xy_stick fallback_sticks(.clk(clk50),.rst_n(rst_n),.enabled(rc_valid),
        .sample_update(fallback_stick_tick),.sample_dt_us(32'd10000),.ch1(ch1),.ch2(ch2),
        .nx(fallback_norm_x),.ny(fallback_norm_y),.busy(),.fault(fallback_norm_fault),
        .update(fallback_norm_update),.valid(fallback_norm_valid),.output_dt_us(fallback_norm_dt));
    wire selected_norm_update=height_fallback_active ?fallback_norm_update:pilot_norm_update;
    wire selected_norm_valid=height_fallback_active || pilot_norm_valid;
    wire [15:0] selected_norm_dt=height_fallback_active ?fallback_norm_dt:pilot_norm_dt_us;
    wire signed [17:0] selected_norm_x=height_fallback_active ?fallback_norm_x:pilot_norm_x;
    wire signed [17:0] selected_norm_y=height_fallback_active ?fallback_norm_y:pilot_norm_y;
    wire source_loc_selected=rc_valid && channel_count>=7 && ch7>=1800 && ch7<=2200;
    wire signed [15:0] manual_snapshot_roll,manual_snapshot_pitch;
    ano_manual_angles manual_angles(.clk(clk50),.rst_n(rst_n),
        .sample_update(selected_norm_update),.norm_valid(selected_norm_valid),.norm_dt_us(selected_norm_dt),
        .norm_roll_q16(selected_norm_y),.norm_pitch_q16(selected_norm_x),
        .loc_override(hold_active && !height_fallback_active),.loc_roll_cdeg(hold_roll_cdeg),.loc_pitch_cdeg(hold_pitch_cdeg),
        .outer_update(manual_outer_update),.outer_dt_ticks(manual_outer_dt_ticks),
        .enabled(controller_enabled),.att_stab(!source_loc_selected || height_fallback_active),
        .roll_cdeg(roll),.pitch_cdeg(pitch),
        .update(manual_angle_update),.busy(manual_angle_busy),.fault(manual_angle_fault),
        .snapshot_roll_cdeg(manual_snapshot_roll),.snapshot_pitch_cdeg(manual_snapshot_pitch),
        .manual_roll_cdeg(manual_roll_cdeg),.manual_pitch_cdeg(manual_pitch_cdeg));
    wire signed [15:0] target_roll=hold_override ? bounded_hold_angle(hold_roll_cdeg) : manual_roll_cdeg;
    // 实测遥控器 CH2 在前推、机头下俯时增大。
    // 机体俯仰以上仰为正，原程序目标角限制为 ±25 度。
    wire signed [15:0] target_pitch=hold_override ? bounded_hold_angle(hold_pitch_cdeg) : -manual_pitch_cdeg;
    // 有界摇杆偏航转换分拍处理死区、
    // 乘法、整数度/秒除法和百分之一度/秒换算；遥控更新远慢于此流水线，
    // 健康与停机条件仍立即生效。
    reg signed [10:0] yaw_deviation_q=0;
    reg signed [9:0] yaw_dead_q=0;
    reg signed [15:0] yaw_product_q=0;
    reg signed [8:0] yaw_dps_q=0;
    reg signed [31:0] stick_yaw=0;
    always @(posedge clk50) begin
        yaw_deviation_q<=ch4<=1000 ? -11'sd500:ch4>=2000 ? 11'sd500:$signed({1'b0,ch4})-17'sd1500;
        yaw_dead_q<=yaw_deviation_q>65 ? yaw_deviation_q-11'sd65:yaw_deviation_q< -65 ? yaw_deviation_q+11'sd65:0;
        yaw_product_q<=yaw_dead_q*16'sd46;
        yaw_dps_q<=yaw_product_q/16'sd100;
        stick_yaw<=yaw_dps_q*32'sd100;
    end
    wire signed [31:0] target_yaw;
    wire yaw_update,yaw_busy;wire [7:0] yaw_fault;
    wire [32:0] manual_outer_elapsed={1'b0,manual_outer_dt_accum}+{1'b0,dt_ticks};
    // 手动角度外环只在新姿态完成时累计真实 dt，达到 6 毫秒且上次角度事务空闲后触发。
    always @(posedge clk50) begin
        manual_outer_update<=0;
        if(!rst_n || !attitude_valid || !rc_valid) begin
            manual_outer_dt_accum<=0;manual_outer_dt_ticks<=0;
        end else if(attitude_update) begin
            if(manual_outer_elapsed>=300000 && !manual_angle_busy) begin
                manual_outer_dt_ticks<=manual_outer_elapsed>32'hffffffff ? 32'hffffffff:manual_outer_elapsed[31:0];
                manual_outer_dt_accum<=0;manual_outer_update<=1;
            end else manual_outer_dt_accum<=manual_outer_elapsed>32'hffffffff ? 32'hffffffff:manual_outer_elapsed[31:0];
        end
    end
    // 偏航按新姿态样本累计6ms调度；角速度内环另按累计2ms调度，均不重复积分旧样本。
    wire [32:0] yaw_elapsed={1'b0,yaw_dt_accum}+{1'b0,dt_ticks};
    always @(posedge clk50) begin
        yaw_sample_update<=0;
        if(!rst_n || !controller_run) begin yaw_dt_accum<=0;yaw_dt_ticks<=0;end
        else if(attitude_update && attitude_valid) begin
            if(yaw_elapsed>=300000 && !yaw_busy) begin
                yaw_dt_ticks<=yaw_elapsed>32'hffffffff ? 32'hffffffff:yaw_elapsed[31:0];
                yaw_dt_accum<=0;yaw_sample_update<=1;
            end else yaw_dt_accum<=yaw_elapsed>32'hffffffff ? 32'hffffffff:yaw_elapsed[31:0];
        end
    end
    ano_yaw_control yaw_controller(.clk(clk50),.rst_n(rst_n),.sample_update(yaw_sample_update),
        .enabled(controller_run),.yaw_valid(attitude_valid),.dt_ticks(yaw_dt_ticks),.yaw_cdeg(-sensor_yaw),
        .stick_yaw_rate_cdeg_s(stick_yaw),.update(yaw_update),.busy(yaw_busy),
        .target_yaw_rate_cdeg_s(target_yaw),.heading_target_cdeg(),.yaw_error_cdeg(),.slewed_rate_cdeg_s(),.fault(yaw_fault));
    // 原姿态外环周期为 6 毫秒，与 2 毫秒角速度环独立。
    // 两次更新之间保持同一时刻的反馈和目标快照。
    reg outer_seeded=0;
    reg signed [15:0] outer_roll=0,outer_pitch=0,outer_target_roll=0,outer_target_pitch=0;
    always @(posedge clk50) begin
        if(!rst_n || !controller_run) begin
            outer_seeded<=0;outer_roll<=0;outer_pitch<=0;outer_target_roll<=0;outer_target_pitch<=0;
        end else if(hold_override && (!outer_seeded || yaw_sample_update)) begin
            outer_roll<=roll;outer_pitch<=pitch;outer_target_roll<=target_roll;outer_target_pitch<=target_pitch;outer_seeded<=1;
        end else if(!hold_override && manual_angle_update) begin
            outer_roll<=manual_snapshot_roll;outer_pitch<=manual_snapshot_pitch;
            outer_target_roll<=manual_roll_cdeg;outer_target_pitch<=-manual_pitch_cdeg;outer_seeded<=1;
        end
    end
    reg signed [15:0] reported_target_roll=0,reported_target_pitch=0;
    always @(posedge clk50) begin reported_target_roll<=target_roll;reported_target_pitch<=target_pitch;end
    reg pose_seen=0;
    always @(posedge clk50)begin
        if(!rst_n)pose_seen<=0;
        else if(attitude_update && attitude_valid)pose_seen<=1;
    end
    wire controller_update,controller_busy;
    wire signed [15:0] correction_roll,correction_pitch,correction_yaw;
    wire [7:0] rate_controller_fault;
    // 位 5 记录手动目标事务故障；既有角速度故障位
    // 以及实时公开健康/输出屏蔽条件的含义保持原样。
    wire [7:0] controller_fault=rate_controller_fault | (manual_angle_fault!=0 ? 8'h20 : 8'h00);
    wire armed;
    wire [7:0] inhibit_reason;
    wire gate_event_pulse;
    wire [7:0] gate_event_code,gate_last_interruption_code,gate_last_revoke_code;
    wire [15:0] gate_interruption_count,gate_revoke_count;
    wire motor_prepared,taking_off,flying,land_lock;wire [3:0] preparation_mask;
    reg [31:0] request_age=0,command_age=32'hFFFFFFFF;
    reg command_seen=0;
    // 并行看门狗条件先寄存，再与传感器及解锁条件合并；
    // 下方公开命令年龄检查仍立即生效。
    reg throttle_active_q=0,request_expired_q=0,command_expired_q=1;
    always @(posedge clk50) begin
        if(!rst_n) begin throttle_active_q<=0; request_expired_q<=0; command_expired_q<=1; end
        else begin
            throttle_active_q<=taking_off && (altitude_active || height_fallback_active);
            request_expired_q<=request_age>=CONTROL_TIMEOUT_TICKS;
            command_expired_q<=command_age>=CONTROL_TIMEOUT_TICKS;
        end
    end
    wire request_active=armed && rc_valid && throttle_active_q;
    wire controller_stale=request_active && request_expired_q && command_expired_q;
    // 直接在传感器角度的补码位上检查对称倾角范围；
    // 负数半区使用无符号低 15 位≥32768-4500，
    // 避免在这个未寄存的实时停机门控中引入机体俯仰取反进位链。
    function tilt_within_limit;
        input [15:0] sensor_angle;
        begin tilt_within_limit=sensor_angle[15] ?
            sensor_angle[14:0]>=15'd28268 : sensor_angle[14:0]<=15'd4500;end
    endfunction
    wire roll_tilt_ok=tilt_within_limit(sensor_roll);
    wire pitch_tilt_ok=tilt_within_limit(sensor_pitch);
    // 飞行健康要求姿态有效、校准完成、已见有效样本、倾角合格且控制器无故障或超时。
    wire sensor_ok=attitude_valid && calibrated && pose_seen &&
        body_tilt4500_ok &&
        controller_fault==0 && yaw_fault==0 && !controller_stale;
    // 诊断仅映射既有有效性条件，不改变门控。
    // 在清除准备/解锁状态的同一沿锁存原因，避免传感器在
    // 下一次 10 Hz 遥测之前恢复而擦掉最初故障。
    wire [7:0] sensor_failure_mask={controller_stale,(controller_fault!=0 || yaw_fault!=0),
        !pitch_tilt_ok,!roll_tilt_ok,
        1'b0,!pose_seen,!calibrated,!attitude_valid}; // 原姿态年龄故障位已移除，此位固定为零。
    reg [7:0] gate_last_interruption_sensor_mask=0,gate_last_revoke_sensor_mask=0;
    reg [7:0] gate_last_interruption_imu_reason=0,gate_last_revoke_imu_reason=0;
    reg [7:0] gate_last_interruption_attitude_fault=0,gate_last_revoke_attitude_fault=0;
    always @(posedge clk50) begin
        if(!rst_n) begin
            gate_last_interruption_sensor_mask<=0; gate_last_revoke_sensor_mask<=0;
            gate_last_interruption_imu_reason<=0; gate_last_revoke_imu_reason<=0;
            gate_last_interruption_attitude_fault<=0; gate_last_revoke_attitude_fault<=0;
        end else if(gate_event_pulse) begin
            if(gate_event_code[5:4]==2'b11) begin
                gate_last_revoke_sensor_mask<=sensor_failure_mask;
                gate_last_revoke_imu_reason<=imu_reason;
                gate_last_revoke_attitude_fault<=attitude_fault;
            end else begin
                gate_last_interruption_sensor_mask<=sensor_failure_mask;
                gate_last_interruption_imu_reason<=imu_reason;
                gate_last_interruption_attitude_fault<=attitude_fault;
            end
        end
    end
    // installation_verified当前是代码中的配置常量1，不是本次硬件验收证据。
    // 实际电机输出仍由后续解锁、健康状态、模式和命令新鲜度门控决定。
    wire installation_verified=1'b1; // B089 无桨硬件台架配置，不能视为已通过飞行验收。
    wire fallback_latched_active,fallback_takeover_ready;
    // 布尔恒等式：V || K×(L || T×S×!V) = V || K×(L || T×S)。
    // 此处仅作组合逻辑因式提取，不延迟健康检查或实时停机条件。
    wire vertical_or_fallback_ready=vertical_available || fallback_takeover_ready;
    // 飞行解锁把水面互斥许可纳入传感器门控；CH5低位和高位默认分别确认0.5s。
    control_gate #(.LOW_HOLD_TICKS(ARM_LOW_TICKS),.HIGH_HOLD_TICKS(ARM_HIGH_TICKS)) gate(
        .clk(clk50),.rst_n(rst_n),.rc_valid(rc_valid),.sensor_ok(sensor_ok && installation_verified && vertical_or_fallback_ready && !land_lock && flight_permitted),
        .channel_count(channel_count),.ch3(ch3),.ch5(ch5),
        .armed(armed),.inhibit_reason(inhibit_reason),
        .event_pulse(gate_event_pulse),.event_code(gate_event_code),
        .interruption_count(gate_interruption_count),.revoke_count(gate_revoke_count),
        .last_interruption_code(gate_last_interruption_code),.last_revoke_code(gate_last_revoke_code));
    // 模式禁止条件进入正式解锁门控；仲裁器只在 CH5 低位、armed_raw=0 时
    // 才可禁止飞行，且禁止期间门控不能解锁，
    // 所以在所有可达时钟沿上，!flight_permitted 都意味着 !armed_raw。
    // 已锁存解锁状态仍须通过当前遥控、传感器、CH5高位与着陆锁条件才能使用。
    wire live_armed_conditions=installation_verified && armed && rc_valid && sensor_ok && !land_lock && channel_count>=5 && channel_count<=8 &&
        ch3>=800 && ch3<=2200 && ch5>=1800 && ch5<=2200;
    assign armed_usable=live_armed_conditions && vertical_or_fallback_ready;
    // 布尔恒等式：H×(V||F)×!F = H×V×!LA；高度可用时不可能触发仅入口型降级。
    // 保留原有立即生效的实时屏蔽，不跨越降级入口状态。
    assign navigation_enabled=live_armed_conditions && vertical_available && !fallback_latched_active;
    // 这里只向定点保持状态机导出既有解锁状态；下方命令/PWM
    // 仍由实时健康条件屏蔽，不得使用此原始状态直接驱动电机。
    assign armed_raw=installation_verified && armed;
    // 高度模式中，低摇杆表示请求下降；SWA 与实时健康条件仍会撤销输出，
    // 模式只能通过其中位确认门控进入。
    // 对高度可用性 V 作香农展开：高度可用且未锁存降级时必须有 altitude_active，
    // 高度不可用的入口分支则预先计算。
    // 起飞后按高度可用性选择自动高度控制或已准备的降级接管，公开命令保持实时门控。
    assign controller_enabled=RUN_RANGE_OK && live_armed_conditions && taking_off &&
        (fallback_latched_active || (vertical_available ? altitude_active:fallback_takeover_ready));
    assign control_enabled=controller_enabled;
    // 实际消费模式取决于寄存的目标选择，但实时停机会
    // 在物理命令有效性撤销的同一周期屏蔽模式消费标志。
    assign hold_consumed=hold_override && controller_enabled;
    assign altitude_consumed=altitude_override && controller_enabled;
    // 局部寄存使能用于降低控制通路扇出和组合深度；
    // 实时许可仍立即屏蔽已发布命令。内部状态取消
    // 可晚一个 20 纳秒时钟，但重新使能不能
    // 重新暴露取消之前遗留的命令。
    always @(posedge clk50) begin
        if(!rst_n) controller_run<=0;
        else controller_run<=controller_enabled;
    end
    wire [2:0] allocation_sat_positive,allocation_sat_negative;
    // 内环在新鲜姿态的累计源 dt 首次达到 2 毫秒时运行。
    // 不重复积分保持中的旧样本；拒收期间的间隔仍计入
    // 下一次真实 dt，并受既有看门狗约束。
    reg rate_sample_update=0;
    reg [31:0] control_dt_accum=0,control_dt_ticks=0;
    wire [32:0] control_elapsed={1'b0,control_dt_accum}+{1'b0,dt_ticks};
    always @(posedge clk50) begin
        rate_sample_update<=0;
        if(!rst_n || !controller_run) begin control_dt_accum<=0;control_dt_ticks<=0;end
        else if(attitude_update && attitude_valid) begin
            if(control_elapsed>=100000 && !controller_busy) begin
                control_dt_ticks<=control_elapsed>32'hffffffff ? 32'hffffffff:control_elapsed[31:0];
                control_dt_accum<=0;rate_sample_update<=1;
            end else control_dt_accum<=control_elapsed>32'hffffffff ? 32'hffffffff:control_elapsed[31:0];
        end
    end
    wire rate_fresh;
    wire [15:0] selected_throttle;
    ano_rate_control #(.GYRO_FRAC_BITS(12),.MAX_DT_TICKS(MAX_DT_TICKS)) controller(
        .clk(clk50),.rst_n(rst_n),.sample_update(rate_sample_update),.enabled(controller_run),.auto_takeoff(auto_takeoff && !height_fallback_active),
        .dt_ticks(control_dt_ticks),.roll_cdeg(outer_roll),.pitch_cdeg(outer_pitch),
        .target_roll_cdeg(outer_target_roll),.target_pitch_cdeg(outer_target_pitch),
        .gx(gx_q12),.gy(gy_q12),.gz(gz_q12),.target_yaw_rate_cdeg_s(target_yaw),
        .saturation_positive(allocation_sat_positive),.saturation_negative(allocation_sat_negative),
        .update(controller_update),.busy(controller_busy),.roll_us(correction_roll),.pitch_us(correction_pitch),.yaw_us(correction_yaw),.fault(rate_controller_fault));
    reg [15:0] pending_throttle=1000;
    // 飞行状态机沿用 1 毫秒/2 毫秒准备调度；集成选择预计算的着陆总油门比较结果。
    ano_flight_state #(.TICKS_PER_MS(FLIGHT_STATE_TICKS_PER_MS),.PRECHECKED_COLLECTIVE(1)) flight_state(.clk(clk50),.rst_n(rst_n),.armed(armed_usable),
     .ch3(ch3),.collective_us(selected_throttle),.collective_below_landing(selected_collective_below_landing),.motor_prepared(motor_prepared),
     .taking_off(taking_off),.flying(flying),.land_lock(land_lock),.preparation_mask(preparation_mask));
    assign taking_off_out=taking_off;
    assign flight_state_flags={auto_takeoff,flying,motor_prepared,taking_off};
    assign throttle_takeover_active=1'b0;assign throttle_pickup_us=16'd0;
    wire [15:0] fallback_collective,fallback_unmasked_collective;
    // 在较晚的实时高度可用性选择之前，先分别比较两个数值分支；
    // 不增加状态或时钟延迟，降级 active 时公开值与未屏蔽数值相同。
    (* syn_keep = 1 *) wire fallback_collective_below_landing=fallback_unmasked_collective<1250;
    (* syn_keep = 1 *) wire auto_collective_below_landing=hold_collective_us<1250;
    wire selected_collective_below_landing=height_fallback_active ?fallback_collective_below_landing:auto_collective_below_landing;
    // 高度丢失处理保留最近有效自动总油门，后续按该模块的接管状态选择油门。
    // 此实例未覆盖降级器上下限，故降级曲线仍为其默认 1200..1850 微秒，不能等同于主混控运行上限。
    height_loss_fallback fallback_control(.clk(clk50),.rst_n(rst_n),
     .healthy(sensor_ok && rc_valid && ch5>=1800 && ch5<=2200 && fallback_norm_valid && !land_lock),
     .armed(armed),.taking_off(taking_off),.height_available(vertical_available),
     .automatic_valid(controller_update && controller_enabled && controller_run && altitude_active && !height_fallback_active),
     .automatic_collective_us(pending_throttle),.ch3(ch3),
     .active(height_fallback_active),.prior_collective_valid(),
     .latched_active(fallback_latched_active),.takeover_ready(fallback_takeover_ready),.collective_us(fallback_collective),
     .unmasked_collective_us(fallback_unmasked_collective));
    assign selected_throttle=height_fallback_active ?fallback_collective:hold_collective_us;
    wire [15:0] mixed_collective=height_fallback_active ?fallback_collective:pending_throttle;
    // 在许可门控清除偏航控制器之前，锁存精确的偏航故障码。
    reg [7:0] last_yaw_fault=0;
    assign sticky_yaw_fault=last_yaw_fault;
    always @(posedge clk50)
     if(!rst_n)last_yaw_fault<=0;
     else if(yaw_fault!=0)last_yaw_fault<=yaw_fault;
    // 把遥控缩放与定点保持偏移/限幅分开处理；
    // 总油门数据在角速度控制器结果发布之前已完成提交。
    reg [15:0] throttle_base=1000;
    reg signed [15:0] captured_hold_delta=0;
    reg [15:0] captured_hold_collective=1000;
    reg captured_hold=0,captured_active=0,throttle_commit=0;
    wire signed [17:0] adjusted_base=$signed({1'b0,throttle_base})+$signed(captured_hold_delta);
    wire [15:0] mix1,mix2,mix3,mix4;
    wire saturated;
    // 布尔选择与纯算术可交换：M(F ? 降级 : 自动)=F ? M(降级) : M(自动)。
    // 两个纯算术混控分支并行计算；最后使用实时降级状态
    // 统一选择完整电机数值及所有方向饱和反馈位。
    wire [15:0] auto_mix1,auto_mix2,auto_mix3,auto_mix4;
    wire [15:0] fallback_mix1,fallback_mix2,fallback_mix3,fallback_mix4;
    wire auto_saturated,fallback_saturated;
    wire [2:0] auto_sat_positive,auto_sat_negative,fallback_sat_positive,fallback_sat_negative;
    quad_mixer_feedback #(.MIN_US(RUN_MIN_US),.MAX_US(RUN_MAX_US)) mixer(.enabled(controller_run),.throttle_us(pending_throttle),
        .roll_us(correction_roll),.pitch_us(correction_pitch),.yaw_us(correction_yaw),
        .m1_us(auto_mix1),.m2_us(auto_mix2),.m3_us(auto_mix3),.m4_us(auto_mix4),.saturated(auto_saturated),
        .saturation_positive(auto_sat_positive),.saturation_negative(auto_sat_negative));
    quad_mixer_feedback #(.MIN_US(RUN_MIN_US),.MAX_US(RUN_MAX_US)) fallback_mixer(.enabled(controller_run),.throttle_us(fallback_unmasked_collective),
        .roll_us(correction_roll),.pitch_us(correction_pitch),.yaw_us(correction_yaw),
        .m1_us(fallback_mix1),.m2_us(fallback_mix2),.m3_us(fallback_mix3),.m4_us(fallback_mix4),.saturated(fallback_saturated),
        .saturation_positive(fallback_sat_positive),.saturation_negative(fallback_sat_negative));
    assign mix1=height_fallback_active ?fallback_mix1:auto_mix1;
    assign mix2=height_fallback_active ?fallback_mix2:auto_mix2;
    assign mix3=height_fallback_active ?fallback_mix3:auto_mix3;
    assign mix4=height_fallback_active ?fallback_mix4:auto_mix4;
    assign saturated=height_fallback_active ?fallback_saturated:auto_saturated;
    assign allocation_sat_positive=height_fallback_active ?fallback_sat_positive:auto_sat_positive;
    assign allocation_sat_negative=height_fallback_active ?fallback_sat_negative:auto_sat_negative;
    // 自动与高度降级两路混控同时计算，按当前降级状态统一选择四路数值及饱和反馈。
    reg [15:0] m1=1000,m2=1000,m3=1000,m4=1000;
    reg signed [15:0] committed_roll=0,committed_pitch=0,committed_yaw=0;
    reg mix_saturated=0;
    reg [31:0] command_count=0;
    reg [31:0] controller_fault_count=0;
    reg [7:0] last_controller_fault=0,previous_controller_fault=0;
    // 统计控制器非零故障的进入次数，并保留最近故障码；该记录不会反向授予控制许可。
    always @(posedge clk50) begin
        if(!rst_n) begin
            controller_fault_count<=0; last_controller_fault<=0; previous_controller_fault<=0;
        end else begin
            previous_controller_fault<=controller_fault;
            if(controller_fault!=0) last_controller_fault<=controller_fault;
            if(controller_fault!=0 && previous_controller_fault==0)
                controller_fault_count<=controller_fault_count+1'b1;
        end
    end
    reg [15:0] latency_counter=0,last_latency=0;
    reg measuring=0;
    // 每次角速度请求捕获油门与模式快照；结果完成时再原子提交四电机命令，年龄仅由真实完成事件刷新。
    always @(posedge clk50) begin
        throttle_commit<=0;
        if(!rst_n || !controller_run) begin
            request_age<=0; command_age<=32'hFFFFFFFF; command_seen<=0;
            m1<=1000; m2<=1000; m3<=1000; m4<=1000; mix_saturated<=0;
            committed_roll<=0; committed_pitch<=0; committed_yaw<=0;
            pending_throttle<=1000; measuring<=0; latency_counter<=0;
            throttle_base<=1000;captured_hold<=0;captured_hold_delta<=0;captured_active<=0;
            if(!rst_n) begin command_count<=0; last_latency<=0; end
        end else begin
            if(request_age!=32'hFFFFFFFF) request_age<=request_age+1'b1;
            if(command_age!=32'hFFFFFFFF) command_age<=command_age+1'b1;
            if(rate_sample_update && !controller_busy) begin
                throttle_base<=selected_throttle;captured_hold<=altitude_override;
                captured_hold_delta<=hold_throttle_delta_us;captured_hold_collective<=hold_collective_us;captured_active<=RUN_RANGE_OK && taking_off && (altitude_active || height_fallback_active);
                throttle_commit<=1;
                latency_counter<=0; measuring<=1;
            end else if(measuring && latency_counter!=16'hFFFF) latency_counter<=latency_counter+1'b1;
            if(throttle_commit) begin
                if(!captured_active) pending_throttle<=1000;
                else pending_throttle<=throttle_base;
            end
            if(controller_update) begin
                // 四路电机命令数值在同一时钟沿提交。
                m1<=mix1; m2<=mix2; m3<=mix3; m4<=mix4; mix_saturated<=saturated;
                committed_roll<=correction_roll; committed_pitch<=correction_pitch; committed_yaw<=correction_yaw;
                command_count<=command_count+1'b1; command_age<=0; command_seen<=1;
                last_latency<=latency_counter+1'b1; measuring<=0;
            end
        end
    end
    // 新控制结果须在默认60ms看门狗内；时长可由CONTROL_TIMEOUT_TICKS覆盖。预备怠速按掩码发布，否则回到1000us。
    assign rate_fresh=controller_enabled && controller_run && command_seen && command_age<CONTROL_TIMEOUT_TICKS;
    wire idle_running=armed_usable && (!taking_off || !motor_prepared);
    assign command_fresh=rate_fresh || idle_running;
    wire [15:0] published_m1=rate_fresh ?m1:idle_running && preparation_mask[0] ?RUN_MIN_US:16'd1000;
    wire [15:0] published_m2=rate_fresh ?m2:idle_running && preparation_mask[1] ?RUN_MIN_US:16'd1000;
    wire [15:0] published_m3=rate_fresh ?m3:idle_running && preparation_mask[2] ?RUN_MIN_US:16'd1000;
    wire [15:0] published_m4=rate_fresh ?m4:idle_running && preparation_mask[3] ?RUN_MIN_US:16'd1000;
    wire [15:0] effective1_us,effective2_us,effective3_us,effective4_us;
    wire [15:0] frame_latched1_us,frame_latched2_us,frame_latched3_us,frame_latched4_us;
    wire pwm_frame_active,pwm_limited;
    // 恒等式 f(select(c,a,b))=select(c,f(a),f(b)) 保持公开数据、
    // 帧锁存和实时使能不变；仅把微秒到时钟拍的换算
    // 前移至有效性选择之前，移除健康条件到 DSP 的长路径。
    function [31:0] pwm_width_ticks;
        input [15:0] value;
        reg [15:0] bounded;
        begin
            bounded=value<1000 ?16'd1000:value>RUN_MAX_US ?RUN_MAX_US:value;
            pwm_width_ticks=bounded*32'd50;
        end
    endfunction
    wire [31:0] pwm_ticks1=rate_fresh ?pwm_width_ticks(m1):idle_running && preparation_mask[0] ?pwm_width_ticks(RUN_MIN_US):pwm_width_ticks(16'd1000);
    wire [31:0] pwm_ticks2=rate_fresh ?pwm_width_ticks(m2):idle_running && preparation_mask[1] ?pwm_width_ticks(RUN_MIN_US):pwm_width_ticks(16'd1000);
    wire [31:0] pwm_ticks3=rate_fresh ?pwm_width_ticks(m3):idle_running && preparation_mask[2] ?pwm_width_ticks(RUN_MIN_US):pwm_width_ticks(16'd1000);
    wire [31:0] pwm_ticks4=rate_fresh ?pwm_width_ticks(m4):idle_running && preparation_mask[3] ?pwm_width_ticks(RUN_MIN_US):pwm_width_ticks(16'd1000);

    // 使用实际已选 PWM 宽度以及原始解锁/控制门控；即使控制器停滞
    // 或已解锁，也不能通过遥测延迟取得参数写权限。
    // 还禁止解锁前 CH5 高位确认窗口内写参数；解锁触发器
    // 上升沿时其他同步过程看到的旧 Q 仍为零，
    // 而 CH5 高位意图已在整个默认 0.5 秒确认期间持续存在。
    wire parameter_arm_intent=rc_valid && ch5>=1800 && ch5<=2200;
    // 参数写入还须水面处于中位、两种驱动均未使能且无CH5高位解锁意图。
    assign parameter_write_safe=water_neutral && !water_enabled && !parameter_arm_intent && !armed_raw && !control_enabled && !taking_off &&
     !command_fresh && pwm_ticks1==50000 && pwm_ticks2==50000 && pwm_ticks3==50000 && pwm_ticks4==50000;
    // 四路飞行命令在同一帧边界锁存；有效值回读受当前使能门控。
    // RAW_TELEMETRY_COMMANDS=1时遥测使用帧锁存原始值，失能后仍可能保留上一帧数值。
    motor_pwm #(.TICKS_PER_US(50),.FRAME_US(OUTPUT_FRAME_US),.MAX_US(RUN_MAX_US),.EXTERNAL_TICKS(1)) outputs(.clk(clk50),.rst_n(rst_n),.enabled(command_fresh),
        // enabled 已立即屏蔽扩展脉宽及有效遥测值；
        // 直接输入已提交数值，避免把健康逻辑重复展开到
        // 脉宽限幅及微秒到时钟拍换算通路。
        .m1_us(published_m1),.m2_us(published_m2),.m3_us(published_m3),.m4_us(published_m4),
        .pre_ticks1(pwm_ticks1),.pre_ticks2(pwm_ticks2),.pre_ticks3(pwm_ticks3),.pre_ticks4(pwm_ticks4),
        .motor1_pwm(motor1_pwm),.motor2_pwm(motor2_pwm),.motor3_pwm(motor3_pwm),.motor4_pwm(motor4_pwm),
        .effective1_us(effective1_us),.effective2_us(effective2_us),
        .effective3_us(effective3_us),.effective4_us(effective4_us),
        .frame_latched1_us(frame_latched1_us),.frame_latched2_us(frame_latched2_us),
        .frame_latched3_us(frame_latched3_us),.frame_latched4_us(frame_latched4_us),
        .frame_active(pwm_frame_active),.limited(pwm_limited));
    wire [7:0] physical_flags={5'd0,pwm_limited,pwm_frame_active,command_fresh};
    assign led3=sensor_ok;

    // A586 包体不再包含年龄数据；移除的年龄字段保留为固定常量，
    // 解码器明确标记为不可用，不再设置相应年龄计数器或锁存。
    // 联合顶层负责封装报文；现有字段及实时/已提交语义保持原样。
    wire [7:0] flags={(mix_saturated && command_fresh),command_fresh,controller_enabled,armed_usable,
        sensor_ok,attitude_valid,calibrated,rc_valid};
    // 遥测同时携带实时许可、已提交控制数值及故障快照；显示数据不能反向授予控制许可。
    assign telemetry_body={flags,inhibit_reason,imu_reason,last_controller_fault,
        ch1,ch2,ch3,ch4,ch5,roll,pitch,reported_target_roll,reported_target_pitch,target_yaw,
        {{15{gx[16]}},gx},{{15{gy[16]}},gy},{{15{gz[16]}},gz},
        (RAW_TELEMETRY_COMMANDS ? committed_roll : (command_fresh ? committed_roll : 16'sd0)),(RAW_TELEMETRY_COMMANDS ? committed_pitch : (command_fresh ? committed_pitch : 16'sd0)),
        (RAW_TELEMETRY_COMMANDS ? committed_yaw : (command_fresh ? committed_yaw : 16'sd0)),published_m1,published_m2,published_m3,published_m4,
        accepted_count,rejected_count,command_count,controller_fault_count,32'd0,last_latency,cal_count,
        who,pwr,attitude_fault,
        gate_interruption_count,gate_revoke_count,gate_last_interruption_code,gate_last_revoke_code,
        gate_last_interruption_sensor_mask,32'd0,
        gate_last_interruption_imu_reason,gate_last_interruption_attitude_fault,
        gate_last_revoke_sensor_mask,32'd0,
        gate_last_revoke_imu_reason,gate_last_revoke_attitude_fault,(RAW_TELEMETRY_COMMANDS ? frame_latched1_us : effective1_us),(RAW_TELEMETRY_COMMANDS ? frame_latched2_us : effective2_us),(RAW_TELEMETRY_COMMANDS ? frame_latched3_us : effective3_us),(RAW_TELEMETRY_COMMANDS ? frame_latched4_us : effective4_us),physical_flags};
    assign pose_update=attitude_update;
    assign pose_valid=attitude_valid;
    assign pose_dt_ticks=dt_ticks;
    assign body_roll_cdeg=roll;
    assign body_pitch_cdeg=pitch;
    assign body_yaw_cdeg=-sensor_yaw;
    assign base_throttle_us=altitude_active ?hold_collective_us:16'd1000;
    assign world_ax_mmps2=sensor_world_ax;
    assign world_ay_mmps2=-sensor_world_ay;
    assign world_az_up_mmps2=sensor_world_az;
    // 仅供显示的最近已接受传感器系加速度，包含重力；
    // 它可能比已发布世界加速度对应的姿态样本更新。
    assign raw_ax_counts=accepted_raw[95:80];
    assign raw_ay_counts=accepted_raw[79:64];
    assign raw_az_counts=accepted_raw[63:48];
    assign raw_accel_valid=accepted_count!=0;
    assign body_gx=gx;assign body_gy=gy;assign body_gz=gz;
    assign body_gx_q12=gx_q12;assign body_gy_q12=gy_q12;assign body_gz_q12=gz_q12;
endmodule
