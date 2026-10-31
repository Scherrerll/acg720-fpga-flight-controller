// 姿态估计模块：四元数融合与世界加速度发布；下方保留第三方原始来源声明。
// Adapted from ANO Quadrotor_TM_V1 Ano_Imu.c and Ano_Sensor_Basic.c.
// See reference_ano for original ANO copyright. FPGA port: Q24 quaternion,
// 来源及版权说明保持上方英文原文；实现改编自 ANO Quadrotor_TM_V1 的惯导和基础传感器代码。
// FPGA 移植采用 Q24 四元数、与 C 原程序一致的顺序就地 Hamilton 更新及重力 PI，
// 并串联四级 0.25 低通（按真实 dt 调整），无磁力计。
// 传感器坐标为 X 前/Y 左/Z 上；公开倾角符号沿用既有检查估计器：
// 横滚为 atan2(gY,gZ)，俯仰为 -asin(gX)。旋转矩阵 R(q) 将传感器
// 机体系变换到初始偏航为零的相对世界系，世界 Y 仍以左向为正。
// 传感器偏航为 atan2(R10,R00)，与传感器 +Z 陀螺同向为正；机体偏航取反，
// 以保留现有安装方向变换。航向只表示相对角度。
// 发布加速度位于上述世界系，单位为 mm/s²，已扣除重力。
// 正常增益为 gkp=0.2、gki=0.01；初始/恢复重力对齐使用 kp=10、
// ki=0，重力误差足够小持续至少约 200 毫秒后退出对齐，对应 ANO G_reset。
// 本模块不驱动执行器；输入为已做传输检查、量程约 ±16g/±2000 度每秒的归一化数据。
// 本模块从已通过传输检查的 IMU 样本估计姿态和去重力加速度，不直接产生执行器命令。
// raw 从高到低依次为 ax、ay、az、gx、gy、gz 六个有符号 16 位计数；加速度 2048 计数为 1g。
// dt_ticks 以 50 MHz 时钟拍计时；角度输出为百分之一度，世界加速度为 mm/s²。
module ano_attitude_estimator #(
 // 本模块默认校准 256 个静止样本、恢复重建 3 个样本、最大 dt 3000000 拍（60 毫秒）；
 // flight_core 默认把 CAL_SAMPLES 覆盖为 2048。LEVEL_TRIM_ENABLE 默认 0，Q24 安装矩阵默认为单位矩阵。
 parameter integer CAL_SAMPLES=256,
 parameter integer MAX_DT_TICKS=3000000,
 parameter integer RESEED_SAMPLES=3,
 parameter integer MAX_CAL_REJECTS=8,
 parameter integer LEVEL_TRIM_ENABLE=0,
 parameter signed [31:0] LEVEL_R00_Q24=32'sd16777216,
 parameter signed [31:0] LEVEL_R01_Q24=0,
 parameter signed [31:0] LEVEL_R02_Q24=0,
 parameter signed [31:0] LEVEL_R10_Q24=0,
 parameter signed [31:0] LEVEL_R11_Q24=32'sd16777216,
 parameter signed [31:0] LEVEL_R12_Q24=0,
 parameter signed [31:0] LEVEL_R20_Q24=0,
 parameter signed [31:0] LEVEL_R21_Q24=0,
 parameter signed [31:0] LEVEL_R22_Q24=32'sd16777216
)(
 input wire clk,rst_n,sample_valid,link_usable,reject_event,
 input wire [95:0] raw,input wire [31:0] dt_ticks,
 output reg calibrated=0,output wire attitude_valid,
 output reg update=0,
 output reg signed [15:0] roll_cdeg=0,output reg signed [15:0] pitch_cdeg=0,output reg signed [15:0] yaw_cdeg=0,
 output reg signed [15:0] bias_x=0,output reg signed [15:0] bias_y=0,output reg signed [15:0] bias_z=0,
 output reg [15:0] cal_count=0,output reg [7:0] fault=0,
 // 下方实际发布 16 位偏航值的范围元数据，不反馈到数值估计。
 output reg yaw_range_ok=1'b1,
 output reg accel_correction=0,
 output reg signed [15:0] filtered_gx=0,output reg signed [15:0] filtered_gy=0,output reg signed [15:0] filtered_gz=0,
 // 独立的相干控制输出，以计数为单位并保留 12 位小数。
 // 本工程中的原有整数陀螺端口只供显示与遥测。
 output reg signed [31:0] filtered_gx_q12=0,output reg signed [31:0] filtered_gy_q12=0,output reg signed [31:0] filtered_gz_q12=0,
 output reg signed [31:0] world_ax_mmps2=0,output reg signed [31:0] world_ay_mmps2=0,output reg signed [31:0] world_az_mmps2=0,
 output wire linear_accel_valid,

// DIAG_TAP_BEGIN
 input wire [31:0] diag_accepted_id,
 output wire [7:0] diag_state,diag_resume_state,diag_reseed_count,
 output wire diag_initialized,diag_ready,diag_reseed,
 output reg [31:0] diag_consumed_accepted_id=0,
 output wire [31:0] diag_held_dt,
 output wire [7:0] diag_first_cause,
// DIAG_TAP_END
 output reg tilt4500_ok=1'b1,
 output reg tilt1500_ok=1'b1
);
 // Q24 最近舍入，恰好半单位时远离零。仅使用算术右移会
 // 把负数向负无穷舍入，使零均值重力噪声积累出虚假积分。
 // 此处仅修正舍入规则，增益常量和估计方程保持原样。
 function signed [31:0] integral_round_q24;
  input signed [63:0] value;
  begin
   integral_round_q24=(value>>>24)+
    ((value[23:0]>24'h800000 ||
      (value[23:0]==24'h800000 && !value[63])) ? 32'sd1:32'sd0);
  end
 endfunction
 // 保存小于最低有效位的积分增量，不在每个样本上将其丢弃。
 // 每轴独立保存 24 位无符号分数，并与有符号 ei 共同表示完整状态：
 // total_Q48=ei×2^24+fraction。算术右移产生的进位对正负数均精确，
 // 使公开误差小于一个 Q24 计数，并能精确抵消平衡的正负误差。
 // 增加的提交状态将 64 位加法与 ei 更新分开执行。
 reg [71:0] integral_fraction=0;
 reg signed [63:0] integral_sum_q=0;
 localparam ERR_I_COMMIT=56;
 localparam signed [31:0] ONE=32'sd16777216;
 // 融合路径持续保留 Q12 计数；原整数公开值是独立视图，
 // 供既有遥测/控制接口和安装修正使用。
 reg signed [31:0] gyro_x_q12=0,gyro_y_q12=0,gyro_z_q12=0;
 reg signed [31:0] bias_x_q12=0,bias_y_q12=0,bias_z_q12=0;
 // 校准均值保留到 Q12 计数，融合陀螺路径保留分数，整数陀螺输出另作显示。
 function signed [31:0] calibration_mean_q12;
  input signed [31:0] accumulated;
  input signed [15:0] last_sample;
  reg signed [63:0] total;
  begin
   total=$signed({{32{accumulated[31]}},accumulated})+
         $signed({{48{last_sample[15]}},last_sample});
   calibration_mean_q12=(total*64'sd4096)/$signed(CAL_SAMPLES);
  end
 endfunction
 function signed [31:0] selected_fusion_gyro;
  input [1:0] coordinate;
  begin case(coordinate)
   0:selected_fusion_gyro=gyro_x_q12;1:selected_fusion_gyro=gyro_y_q12;
   2:selected_fusion_gyro=gyro_z_q12;default:selected_fusion_gyro=32'bx;
  endcase end
 endfunction
 // 主状态机依次执行原始值检查、校准/重建、低通、重力反馈、四元数更新和统一发布。
 localparam IDLE=0,RAW_SQUARE=1,RAW_SUM=2,DECIDE=3,ALPHA=4,FILTER=5,
 FILTER_MUL=6,FILTER_NEXT=7,FILTER_DONE=8,ACC_SQUARE=9,ACC_SUM=10,
 ACC_ROOT=11,ACC_ROOT_DONE=12,ACC_NORMALIZE=13,ACC_DIV_DONE=14,
 SEED=15,NORM_SQUARE=16,NORM_SUM=17,NORM_ROOT=18,NORM_ROOT_DONE=19,
 NORM_DIV=20,NORM_DIV_DONE=21,MATRIX_MUL=22,MATRIX_STORE=23,MATRIX_FORM=24,
 MATRIX_CONT=25,CROSS_MUL=26,CROSS_STORE=27,CROSS_FORM=28,
 DT_DIV=29,DT_DONE=30,ERR_I_DT=31,ERR_I_DT_DONE=32,ERR_I_GAIN_DONE=33,
 CORRECT_GAIN_DONE=34,GYRO_SCALE_DONE=35,DANGLE_DONE=36,
 QUAT_SETUP=37,QUAT_TERM=38,WORLD_SETUP=39,WORLD_TERM=40,WORLD_SCALE=41,
 WORLD_SCALE_DONE=42,ROLL_START=43,ROLL_DONE=44,PITCH_START=45,PITCH_DONE=46,
 PUBLISH=47,MUL_WAIT=60,DIV_WAIT=61,ROOT_WAIT=62;
 // 固定安装旋转 T：将原传感器系映射到水平修正后的虚拟传感器系。
 // 原四元数、低通、重力 PI 及世界加速度矩阵保持原样；
 // 仅公开姿态 Rs×T 转置及陀螺 T×g 经过安装修正。
 localparam TRIM_MATRIX_SETUP=63,TRIM_MATRIX_TERM=64,TRIM_MATRIX_STORE=65,
 TRIM_GYRO_SETUP=66,TRIM_GYRO_TERM=67,TRIM_GYRO_STORE=68;
 function signed [31:0] trim_coefficient;
  input [1:0] row,col;
  begin
   case({row,col})
    4'b0000:trim_coefficient=LEVEL_R00_Q24;
    4'b0001:trim_coefficient=LEVEL_R01_Q24;
    4'b0010:trim_coefficient=LEVEL_R02_Q24;
    4'b0100:trim_coefficient=LEVEL_R10_Q24;
    4'b0101:trim_coefficient=LEVEL_R11_Q24;
    4'b0110:trim_coefficient=LEVEL_R12_Q24;
    4'b1000:trim_coefficient=LEVEL_R20_Q24;
    4'b1001:trim_coefficient=LEVEL_R21_Q24;
    4'b1010:trim_coefficient=LEVEL_R22_Q24;
    default:trim_coefficient=0;
   endcase
  end
 endfunction
 function signed [63:0] trim_product;
  input signed [31:0] lhs,rhs;
  begin trim_product=$signed(lhs)*$signed(rhs);end
 endfunction
 function trim_near_zero;
  input signed [63:0] value;
  begin trim_near_zero=value>=-64'sd1073741824 && value<=64'sd1073741824;end
 endfunction
 function trim_matrix_ok;
  input integer unused;
  integer r,c;
  reg good;
  begin
   good=1;
   // 这些表达式均为编译期常量，不产生运行时硬件乘法器。
   for(r=0;r<3;r=r+1)for(c=0;c<3;c=c+1)
    if(trim_coefficient(r,c)>32'sd16777248 || trim_coefficient(r,c)<-32'sd16777248)good=0;
   for(r=0;r<3;r=r+1)
    if(!trim_near_zero(trim_product(trim_coefficient(r,0),trim_coefficient(r,0))+
      trim_product(trim_coefficient(r,1),trim_coefficient(r,1))+
      trim_product(trim_coefficient(r,2),trim_coefficient(r,2))-64'sd281474976710656))good=0;
   for(r=0;r<3;r=r+1)for(c=r+1;c<3;c=c+1)
    if(!trim_near_zero(trim_product(trim_coefficient(r,0),trim_coefficient(c,0))+
      trim_product(trim_coefficient(r,1),trim_coefficient(c,1))+
      trim_product(trim_coefficient(r,2),trim_coefficient(c,2))))good=0;
   // 还要求矩阵为右手旋转，拒绝虽正交但构成镜像反射的矩阵。
   if(!trim_near_zero(trim_product(LEVEL_R01_Q24,LEVEL_R12_Q24)-trim_product(LEVEL_R02_Q24,LEVEL_R11_Q24)-trim_product(LEVEL_R20_Q24,32'sd16777216)))good=0;
   if(!trim_near_zero(trim_product(LEVEL_R02_Q24,LEVEL_R10_Q24)-trim_product(LEVEL_R00_Q24,LEVEL_R12_Q24)-trim_product(LEVEL_R21_Q24,32'sd16777216)))good=0;
   if(!trim_near_zero(trim_product(LEVEL_R00_Q24,LEVEL_R11_Q24)-trim_product(LEVEL_R01_Q24,LEVEL_R10_Q24)-trim_product(LEVEL_R22_Q24,32'sd16777216)))good=0;
   trim_matrix_ok=good;
  end
 endfunction
 // 可选安装矩阵在常量阶段校验正交性与右手性；不合格时姿态资格被撤销。
 localparam LEVEL_MATRIX_VALID=trim_matrix_ok(0);
 reg signed [31:0] trim_matrix[0:4];
 wire [1:0] trim_row=index==0 ? 2'd0:index==1 ? 2'd1:2'd2;
 wire [1:0] trim_col=index<3 ? 2'd0:index==3 ? 2'd1:2'd2;
 wire [3:0] trim_row_base=trim_row==0 ? 4'd0:trim_row==1 ? 4'd3:4'd6;
 wire [3:0] trim_matrix_index=trim_row_base+{2'b0,term};
 wire signed [31:0] angle_r00=LEVEL_TRIM_ENABLE ? trim_matrix[0]:matrix[0];
 wire signed [31:0] angle_r10=LEVEL_TRIM_ENABLE ? trim_matrix[1]:matrix[3];
 wire signed [31:0] angle_r20=LEVEL_TRIM_ENABLE ? trim_matrix[2]:matrix[6];
 wire signed [31:0] angle_r21=LEVEL_TRIM_ENABLE ? trim_matrix[3]:matrix[7];
 wire signed [31:0] angle_r22=LEVEL_TRIM_ENABLE ? trim_matrix[4]:matrix[8];
 reg [6:0] state=IDLE,resume_state=IDLE;
 reg ready=0,initialized=0,filter_seeded=0,reseed=0;
 reg [7:0] reseed_count=0,cal_rejects=0;
 reg [95:0] captured_raw=0;reg [31:0] held_dt=0;
 reg signed [31:0] ax=0,ay=0,az=2048,gx=0,gy=0,gz=0;
 reg signed [31:0] accel_x_word=0,accel_y_word=0,accel_z_word=2048;
 reg signed [31:0] gyro_x_word=0,gyro_y_word=0,gyro_z_word=0;
 function signed [31:0] selected_accel;
  input [1:0] coordinate;
  begin case(coordinate)
   0:selected_accel=accel_x_word;1:selected_accel=accel_y_word;
   2:selected_accel=accel_z_word;default:selected_accel=32'bx;
  endcase end
 endfunction
 function signed [31:0] selected_gyro;
  input [1:0] coordinate;
  begin case(coordinate)
   0:selected_gyro=gyro_x_word;1:selected_gyro=gyro_y_word;
   2:selected_gyro=gyro_z_word;default:selected_gyro=32'bx;
  endcase end
 endfunction
 reg signed [31:0] an[0:2],q[0:3],ei[0:2],err[0:2],da[0:2];
 reg signed [31:0] matrix[0:8],qprod[0:8],crossprod[0:5];
 // 显式保存 24 个滤波状态槽，避免按二次幂推断 RAMREG 时产生填充。
 // C 原程序 sensor.Acc 为 s16，浮点转整数向零截断；
 // 仅算术右移会把负数错误地向负无穷截断。
 function signed [31:0] accel_trunc_q8;
  input signed [31:0] value;
  begin accel_trunc_q8=(value>>>8)+(value[31] && |value[7:0] ? 32'sd1:32'sd0);end
 endfunction
 reg signed [31:0] pending_fine_x=0,pending_fine_y=0,pending_fine_z=0;
 localparam TRIM_FINE_SETUP=69,TRIM_FINE_TERM=70,TRIM_FINE_STORE=71;
 localparam integer LPF_STORE_BITS=29; // 加速度状态为 Q8 计数，陀螺状态为 Q12 计数。
 reg [24*LPF_STORE_BITS-1:0] lpf_storage=0;
 // 每个轴独立保留 Q16 乘积缩位后的余数预算，
 // 相同 alpha 的四级串联滤波依次使用该预算，轴之间不传递进位。
 // 在恒定 alpha 的周期稳态，把四级递推相加时中间级增量相消，
 // 从而输出直流分量与输入直流分量完全一致。
 // 这属于有界误差反馈量化，不是把全部滤波状态扩成更宽位数。
 localparam integer LPF_REMAINDER_BANKS=6;
 reg [LPF_REMAINDER_BANKS*16-1:0] lpf_remainder_storage=0;
 wire [15:0] lpf_remainder=lpf_remainder_storage[index[4:2]*16+:16];
 wire [16:0] lpf_remainder_sum={1'b0,prod[15:0]}+{1'b0,lpf_remainder};
 // 在已接受输入和校准零偏范围内，30 位有符号缩位值足以覆盖 ±269778944，
 // 把余数进位并入同一个字加法器中。
 // 恒等式：(2×old+1+2×floor(product/65536)+carry)>>1=old+floor+carry。
 wire signed [30:0] lpf_carry_sum=$signed({lpf[index],1'b1})+
  $signed({prod[45:16],lpf_remainder_sum[16]});
 wire signed [31:0] lpf[0:23];
 reg signed [31:0] filter_input[0:5];
 genvar lpf_word;
 generate for(lpf_word=0;lpf_word<24;lpf_word=lpf_word+1)begin:lpf_read_alias
  assign lpf[lpf_word]=$signed(lpf_storage[lpf_word*LPF_STORE_BITS+:LPF_STORE_BITS]);
 end endgenerate
 reg signed [31:0] sum_x=0,sum_y=0,sum_z=0;
 reg signed [15:0] low_x=0,high_x=0,low_y=0,high_y=0,low_z=0,high_z=0;
 reg signed [15:0] prev_ax=0,prev_ay=0,prev_az=0;
 reg [63:0] raw_norm2=0,acc_norm2=0,norm2=0;
 reg [31:0] denominator=1,dt_q24=0,alpha_remaining=0;
 reg [16:0] alpha_factor=65536,alpha_q16=16384;
 reg [24:0] aligned_ticks=0;reg alignment=1,use_acc=0,lin_ok=0;
 reg [25:0] gravity_abs_x=0,gravity_abs_y=0;reg [26:0] gravity_error_sum=0;
 reg [4:0] index=0;reg [1:0] axis=0,component=0,term=0;
 reg matrix_for_output=0;
 reg signed [63:0] accum=0,prod=0,quotient=0;
 reg signed [31:0] corrected_rate=0,pending_roll=0,pending_pitch=0,pending_yaw=0;
 wire signed [15:0] publication_roll_word=pending_roll[15:0],publication_pitch_word=pending_pitch[15:0];
 wire publication_tilt4500=(publication_roll_word>=-4500 && publication_roll_word<=4500 && publication_pitch_word>=-4500 && publication_pitch_word<=4500);
 wire publication_tilt1500=(publication_roll_word>=-1500 && publication_roll_word<=1500 && publication_pitch_word>=-1500 && publication_pitch_word<=1500);
 wire signed [15:0] publication_yaw_word=pending_yaw[15:0];
 wire publication_yaw_range=(publication_yaw_word>=-18000 && publication_yaw_word<=18000);
 reg signed [31:0] pending_world[0:2],pending_gyro[0:2];
 reg [31:0] yz_magnitude=0;
 // 在一个共用加法器内保留原有 64 位加法及 32 位截断结果。
 wire signed [31:0] next_lpf=lpf_carry_sum>>>1;
 wire signed [15:0] raw_ax=captured_raw[95:80],raw_ay=captured_raw[79:64],raw_az=captured_raw[63:48];
 wire signed [15:0] raw_gx=captured_raw[47:32],raw_gy=captured_raw[31:16],raw_gz=captured_raw[15:0];
 wire signed [16:0] dax={raw_ax[15],raw_ax}-{prev_ax[15],prev_ax};
 wire signed [16:0] day={raw_ay[15],raw_ay}-{prev_ay[15],prev_ay};
 wire signed [16:0] daz={raw_az[15],raw_az}-{prev_az[15],prev_az};
 // 排除整帧全零/全一及 -32768 哨兵值；静止校准还限制重力模长、陀螺幅值与帧间变化。
 wire raw_ok=captured_raw!=0 && captured_raw!={96{1'b1}} &&
 raw_ax!=-32768 && raw_ay!=-32768 && raw_az!=-32768 &&
 raw_gx!=-32768 && raw_gy!=-32768 && raw_gz!=-32768;
 wire raw_gravity=raw_norm2>=64'd3783025 && raw_norm2<=64'd4626801;
 wire reseed_gravity=raw_norm2>=64'd3530262 && raw_norm2<=64'd4897040;
 wire still=raw_gravity && raw_gx>=-164 && raw_gx<=164 && raw_gy>=-164 && raw_gy<=164 && raw_gz>=-164 && raw_gz<=164 &&
 (cal_count==0 || (dax>=-64 && dax<=64 && day>=-64 && day<=64 && daz>=-64 && daz<=64 &&
 $signed({raw_gx[15],raw_gx}) >= $signed({high_x[15],high_x})-17'sd32 &&
 $signed({raw_gx[15],raw_gx}) <= $signed({low_x[15],low_x})+17'sd32 &&
 $signed({raw_gy[15],raw_gy}) >= $signed({high_y[15],high_y})-17'sd32 &&
 $signed({raw_gy[15],raw_gy}) <= $signed({low_y[15],low_y})+17'sd32 &&
 $signed({raw_gz[15],raw_gz}) >= $signed({high_z[15],high_z})-17'sd32 &&
 $signed({raw_gz[15],raw_gz}) <= $signed({low_z[15],low_z})+17'sd32));
 // 公开有效性同时要求已校准、已初始化、已完成计算、链路可用以及安装矩阵合格。
 assign attitude_valid=calibrated && initialized && ready && link_usable && (!LEVEL_TRIM_ENABLE || LEVEL_MATRIX_VALID);
 assign linear_accel_valid=attitude_valid && lin_ok;
 // 在稳定姿态时期，随后被拒收的原始记录不属于已经检查并锁定的候选样本，
 // 因此允许该候选样本及其共享算术单拍完成事件继续结束。
 // 启动/恢复阶段仍要求连续合格记录，
 // 并保留原有拒收导致取消的语义。
 // 稳定姿态期间后到的拒收记录不取消已锁存候选；启动和恢复期间仍要求连续合格记录。
 wire stable_pose_epoch=calibrated && initialized && ready;
 wire reject_cancels_candidate=reject_event && !stable_pose_epoch;
 // 链路失效或计算未结束又来新样本会取消共享算术，防止混用不同样本的数据。
 wire cancel_math=!rst_n || !link_usable || reject_cancels_candidate || (sample_valid && state!=IDLE);
 reg m_start=0,d_start=0,s_start=0,c_start=0;
 reg signed [31:0] m_a=0,m_b=0,c_x=0,c_y=0;
 reg signed [63:0] d_n=0;reg [31:0] d_d=1;reg [63:0] s_n=0;
 wire m_done,m_busy,d_done,d_busy,d_error,s_done,s_busy,c_done,c_busy;
 wire signed [63:0] m_result,d_result;wire [31:0] s_result,c_mag;
 wire signed [31:0] c_angle;
 ano_attitude_mul32 mul(.clk(clk),.rst_n(rst_n),.cancel(cancel_math),.start(m_start),.a(m_a),.b(m_b),.busy(m_busy),.done(m_done),.result(m_result));
 ano_attitude_div64 div(.clk(clk),.rst_n(rst_n),.cancel(cancel_math),.start(d_start),.numerator(d_n),.denominator(d_d),.busy(d_busy),.done(d_done),.error(d_error),.quotient(d_result));
 ano_attitude_sqrt64 sqrt(.clk(clk),.rst_n(rst_n),.cancel(cancel_math),.start(s_start),.radicand(s_n),.busy(s_busy),.done(s_done),.result(s_result));
 cordic_atan2 angle(.clk(clk),.rst_n(rst_n && !cancel_math),.start(c_start),.x_in(c_x),.y_in(c_y),.busy(c_busy),.done(c_done),.angle_q16(c_angle),.magnitude(c_mag));
 wire signed [63:0] cdeg_scaled=c_angle*64'sd100;
 wire signed [63:0] quaternion_term=(component==0 || (component==1 && term==2) || (component==2 && term==1) || (component==3 && term==2)) ? -prod:prod;
 // 保留原先三个算术/舍入边界，但把取反、
 // 64 位累加及最终移位后的四元数加法分拍执行。
 reg signed [63:0] quaternion_term_q=0,quaternion_sum_q=0;
 // 误差反馈跨更新保留旋转分数增量；
 // 四元数 q 及归一化仍为 Q24，此额外状态只是尚未提交的增量余数，
 // 不能据此将归一化理解为使用完整 Q56 四元数。
 reg [127:0] quaternion_fraction=0;
 reg signed [63:0] quaternion_delta_q=0;
 wire signed [63:0] next_quaternion=$signed(q[component])+(quaternion_delta_q>>>32);
 function signed [15:0] sat16;input signed [31:0] v;begin sat16=v>32767 ? 16'sd32767 : v< -32767 ? -16'sd32767:v[15:0];end endfunction
 function signed [31:0] clip_error;input signed [31:0] v;begin clip_error=v>1677722 ? 1677722:v< -1677722 ? -1677722:v;end endfunction
 task multiply;input signed [31:0] lhs,rhs;input [6:0] next;begin m_a<=lhs;m_b<=rhs;m_start<=1;resume_state<=next;state<=MUL_WAIT;end endtask
 task divide;input signed [63:0] numerator;input [31:0] divisor;input [6:0] next;begin d_n<=numerator;d_d<=divisor;d_start<=1;resume_state<=next;state<=DIV_WAIT;end endtask
 task root;input [63:0] value;input [6:0] next;begin s_n<=value;s_start<=1;resume_state<=next;state<=ROOT_WAIT;end endtask

// DIAG_TAP_BEGIN
 assign diag_state={1'b0,state};assign diag_resume_state={1'b0,resume_state};
 assign diag_initialized=initialized;assign diag_ready=ready;assign diag_reseed=reseed;
 assign diag_reseed_count=reseed_count;assign diag_held_dt=held_dt;
 reg [7:0] diag_first_cause_latched=0;
 // 被动原因分类只映射既有分支，任何分类输出都不是控制条件。
 wire [7:0] diag_cause_now=(LEVEL_TRIM_ENABLE && !LEVEL_MATRIX_VALID) ?8'd8:
  !link_usable ?8'd1:reject_cancels_candidate ?8'd2:
  sample_valid && state!=IDLE ?8'd3:
  state==DECIDE && !raw_ok ?8'd4:
  state==DECIDE && !calibrated && !still ?8'd9:
  state==DECIDE && calibrated && held_dt>MAX_DT_TICKS ?8'd5:
  state==DECIDE && calibrated && (!initialized || held_dt==0) && !reseed_gravity ?8'd6:
  state==ACC_ROOT_DONE && s_result==0 && reseed ?8'd7:
  (state==NORM_ROOT_DONE && (s_result<1000 || s_result>67108864)) ||
  (state==DANGLE_DONE && ((prod>>>25)>731998 || (prod>>>25)< -731998)) ||
  (state==DIV_WAIT && d_done && d_error) ?8'd8:8'd0;
 // 故障捕获可能与首次撤销有效性发生在同一时钟沿；
 // 直接暴露当前原因，避免为冻结诊断包额外延迟一拍。
 assign diag_first_cause=diag_first_cause_latched!=0 ?diag_first_cause_latched:diag_cause_now;
 always @(posedge clk) begin
  if(!rst_n)begin diag_consumed_accepted_id<=0;diag_first_cause_latched<=0;end
  else begin
   if(sample_valid && state==IDLE && link_usable &&
      !(LEVEL_TRIM_ENABLE && !LEVEL_MATRIX_VALID) && !reject_cancels_candidate)
    diag_consumed_accepted_id<=diag_accepted_id;
   if(update)diag_first_cause_latched<=diag_cause_now;
   else if(diag_first_cause_latched==0 && diag_cause_now!=0)diag_first_cause_latched<=diag_cause_now;
  end
 end
// DIAG_TAP_END
 // invalidate 撤销姿态/线加速度资格并清陀螺与加速度输出，保留已完成零偏以便重建恢复。
 task invalidate;input [7:0] code;begin lpf_remainder_storage<=0;state<=IDLE;ready<=0;initialized<=0;lin_ok<=0;reseed_count<=0;filter_seeded<=0;filtered_gx<=0;filtered_gy<=0;filtered_gz<=0;filtered_gx_q12<=0;filtered_gy_q12<=0;filtered_gz_q12<=0;world_ax_mmps2<=0;world_ay_mmps2<=0;world_az_mmps2<=0;fault<=code;end endtask
 integer i,j;
 initial begin
  for(i=0;i<3;i=i+1) begin an[i]=0;ei[i]=0;err[i]=0;da[i]=0;pending_world[i]=0;pending_gyro[i]=0;end
  // 滤波加速度 Z 标量已在上方初始化为 2048 计数。
  q[0]=ONE;q[1]=0;q[2]=0;q[3]=0;
  for(i=0;i<9;i=i+1) begin matrix[i]=0;qprod[i]=0;end
  for(i=0;i<6;i=i+1) begin crossprod[i]=0;filter_input[i]=0;end
  // lpf_storage 上电值仍全零；恢复时仍会重建全部 24 个状态槽。
 end
 always @(posedge clk) begin
  update<=0;m_start<=0;d_start<=0;s_start<=0;c_start<=0;
  if(!rst_n) begin
   state<=IDLE;ready<=0;initialized<=0;calibrated<=0;filter_seeded<=0;lin_ok<=0;
   cal_count<=0;cal_rejects<=0;reseed_count<=0;sum_x<=0;sum_y<=0;sum_z<=0;
   bias_x<=0;bias_y<=0;bias_z<=0;fault<=0;accel_correction<=0;
   bias_x_q12<=0;bias_y_q12<=0;bias_z_q12<=0;
   roll_cdeg<=0;pitch_cdeg<=0;yaw_cdeg<=0;yaw_range_ok<=1'b1;tilt4500_ok<=1'b1;tilt1500_ok<=1'b1;filtered_gx<=0;filtered_gy<=0;filtered_gz<=0;filtered_gx_q12<=0;filtered_gy_q12<=0;filtered_gz_q12<=0;
   world_ax_mmps2<=0;world_ay_mmps2<=0;world_az_mmps2<=0;
   alignment<=1;aligned_ticks<=0;lpf_remainder_storage<=0;
   integral_fraction<=0;integral_sum_q<=0;
   quaternion_fraction<=0;quaternion_delta_q<=0;
   for(i=0;i<3;i=i+1) begin ei[i]<=0;err[i]<=0;da[i]<=0;end
   q[0]<=ONE;q[1]<=0;q[2]<=0;q[3]<=0;
  end else if(LEVEL_TRIM_ENABLE && !LEVEL_MATRIX_VALID) begin
   invalidate(8'h40);calibrated<=0;cal_count<=0;cal_rejects<=0;
   sum_x<=0;sum_y<=0;sum_z<=0;
  end else if(!link_usable) begin
   invalidate(8'h01);
   if(!calibrated) begin cal_count<=0;cal_rejects<=0;sum_x<=0;sum_y<=0;sum_z<=0;end
  end else if(reject_cancels_candidate) begin
   reseed_count<=0;
   if(!calibrated && cal_count!=0) begin
    if(cal_rejects>=MAX_CAL_REJECTS) begin cal_count<=0;cal_rejects<=0;sum_x<=0;sum_y<=0;sum_z<=0;fault<=8'h02;end
    else cal_rejects<=cal_rejects+1'b1;
   end
   if(state!=IDLE) invalidate(8'h08);
  end else if(sample_valid && state!=IDLE) invalidate(8'h08);
  else case(state)
   // 仅空闲状态锁存整组原始值和 dt，后续所有算术都基于该候选样本。
   IDLE:if(sample_valid) begin captured_raw<=raw;held_dt<=dt_ticks;axis<=0;raw_norm2<=0;state<=RAW_SQUARE;end
   RAW_SQUARE:case(axis)
    0:multiply($signed(raw_ax),$signed(raw_ax),RAW_SUM);
    1:multiply($signed(raw_ay),$signed(raw_ay),RAW_SUM);
    2:multiply($signed(raw_az),$signed(raw_az),RAW_SUM);
   endcase
   RAW_SUM:begin raw_norm2<=raw_norm2+prod;if(axis==2) state<=DECIDE;else begin axis<=axis+1'b1;state<=RAW_SQUARE;end end
   DECIDE:begin
    state<=IDLE;
    if(!raw_ok) invalidate(8'h04);
    else if(!calibrated) begin
     if(!still) begin cal_count<=0;sum_x<=0;sum_y<=0;sum_z<=0;cal_rejects<=0;fault<=8'h02;end
     else begin
      // 统计连续拒收帧，而不是整个 CAL_SAMPLES 校准窗口内的累计拒收；
      // 一个已通过传输检查的静止样本即结束连续拒收计数。
      cal_rejects<=0;
      prev_ax<=raw_ax;prev_ay<=raw_ay;prev_az<=raw_az;
      if(cal_count==0) begin low_x<=raw_gx;high_x<=raw_gx;low_y<=raw_gy;high_y<=raw_gy;low_z<=raw_gz;high_z<=raw_gz;end
      else begin
       if(raw_gx<low_x) low_x<=raw_gx;if(raw_gx>high_x) high_x<=raw_gx;
       if(raw_gy<low_y) low_y<=raw_gy;if(raw_gy>high_y) high_y<=raw_gy;
       if(raw_gz<low_z) low_z<=raw_gz;if(raw_gz>high_z) high_z<=raw_gz;
      end
      sum_x<=sum_x+raw_gx;sum_y<=sum_y+raw_gy;sum_z<=sum_z+raw_gz;cal_count<=cal_count+1'b1;fault<=0;
      // 达到 CAL_SAMPLES 后一次性提交三轴零偏；默认窗口为 256 个合格静止样本。
      if(cal_count==CAL_SAMPLES-1) begin
       bias_x<=($signed(sum_x)+$signed(raw_gx))/CAL_SAMPLES;
       bias_y<=($signed(sum_y)+$signed(raw_gy))/CAL_SAMPLES;
       bias_z<=($signed(sum_z)+$signed(raw_gz))/CAL_SAMPLES;
       bias_x_q12<=calibration_mean_q12(sum_x,raw_gx);
       bias_y_q12<=calibration_mean_q12(sum_y,raw_gy);
       bias_z_q12<=calibration_mean_q12(sum_z,raw_gz);
       calibrated<=1;
      end
     end
    end else if(held_dt>MAX_DT_TICKS) invalidate(8'h10);
    // 未初始化或零 dt 时，用连续 RESEED_SAMPLES 个近重力样本重建倾角与滤波初值。
    else if(!initialized || held_dt==0) begin
     ready<=0;initialized<=0;lin_ok<=0;
     if(!reseed_gravity) begin reseed_count<=0;fault<=8'h04;end
     else if(reseed_count<RESEED_SAMPLES-1) begin reseed_count<=reseed_count+1'b1;fault<=8'h80;end
     else begin reseed_count<=0;reseed<=1;filter_seeded<=0;state<=FILTER;index<=0;end
    end else begin
     reseed<=0;alpha_remaining<=held_dt+25000;alpha_factor<=65536;state<=ALPHA;
    end
   end
   // 按真实 dt 调整四级低通系数；每轴保留乘法余数，减少长期量化偏差。
   ALPHA:if(alpha_remaining>=50000) begin alpha_remaining<=alpha_remaining-50000;alpha_factor<=(alpha_factor*3)>>2;end
    else begin alpha_q16<=65536-alpha_factor;index<=0;state<=FILTER;end
   FILTER:begin
    filter_input[0]<=$signed(raw_ax)<<<8;filter_input[1]<=$signed(raw_ay)<<<8;filter_input[2]<=$signed(raw_az)<<<8;
    filter_input[3]<=($signed({{16{raw_gx[15]}},raw_gx})<<<12)-bias_x_q12;
    filter_input[4]<=($signed({{16{raw_gy[15]}},raw_gy})<<<12)-bias_y_q12;
    filter_input[5]<=($signed({{16{raw_gz[15]}},raw_gz})<<<12)-bias_z_q12;
    state<=FILTER_NEXT;
   end
   FILTER_NEXT:if(!filter_seeded) begin
    lpf_remainder_storage<=0;
    for(i=0;i<6;i=i+1) for(j=0;j<4;j=j+1) lpf_storage[(4*i+j)*LPF_STORE_BITS+:LPF_STORE_BITS]<=filter_input[i];
    filter_seeded<=1;state<=FILTER_DONE;
   end else state<=FILTER_MUL;
   FILTER_MUL:begin
    // index=0 表示最靠近原始输入的一级；原程序就地更新顺序为 3、2、1、0，
    // 本存储改记为 0、1、2、3，但串联滤波的实际依赖顺序完全相同。
    if(index[1:0]==0) multiply(filter_input[index>>2]-lpf[index],$signed({15'b0,alpha_q16}),49);
    else multiply(lpf[index-1]-lpf[index],$signed({15'b0,alpha_q16}),49);
   end
   49:begin
    for(j=0;j<LPF_REMAINDER_BANKS;j=j+1)
     if(index[4:2]==j)lpf_remainder_storage[j*16+:16]<=lpf_remainder_sum[15:0];
    for(i=0;i<24;i=i+1)
     if(index==i)lpf_storage[i*LPF_STORE_BITS+:LPF_STORE_BITS]<=next_lpf;
    if(index==23) state<=FILTER_DONE;else begin index<=index+1'b1;state<=FILTER_MUL;end
   end
   FILTER_DONE:begin
    accel_x_word<=accel_trunc_q8(lpf[3]);accel_y_word<=accel_trunc_q8(lpf[7]);accel_z_word<=accel_trunc_q8(lpf[11]);
    gyro_x_word<=lpf[15]>>>12;gyro_y_word<=lpf[19]>>>12;gyro_z_word<=lpf[23]>>>12;
    gyro_x_q12<=lpf[15];gyro_y_q12<=lpf[19];gyro_z_q12<=lpf[23];
    pending_fine_x<=lpf[15];pending_fine_y<=lpf[19];pending_fine_z<=lpf[23];
    for(i=0;i<3;i=i+1) pending_gyro[i]<=lpf[4*(i+3)+3]>>>12;
    axis<=0;acc_norm2<=0;state<=ACC_SQUARE;
   end
   ACC_SQUARE:multiply(selected_accel(axis),selected_accel(axis),ACC_SUM);
   ACC_SUM:begin acc_norm2<=acc_norm2+prod;if(axis==2) state<=ACC_ROOT;else begin axis<=axis+1'b1;state<=ACC_SQUARE;end end
   // 仅近 1g 的滤波加速度参与重力反馈；机动加速度越界时继续依靠陀螺积分。
   ACC_ROOT:begin use_acc<=acc_norm2>=64'd3530262 && acc_norm2<=64'd4897040;root(acc_norm2,ACC_ROOT_DONE);end
   ACC_ROOT_DONE:if(s_result==0) begin
    if(reseed) invalidate(8'h04);
    else begin an[0]<=0;an[1]<=0;an[2]<=0;use_acc<=0;matrix_for_output<=0;index<=0;state<=MATRIX_MUL;end
   end else begin denominator<=s_result;axis<=0;state<=ACC_NORMALIZE;end
   ACC_NORMALIZE:divide($signed(selected_accel(axis))*64'sd16777216,denominator,ACC_DIV_DONE);
   ACC_DIV_DONE:begin
    an[axis]<=quotient;
    if(axis==2) begin if(reseed) state<=SEED;else begin matrix_for_output<=0;index<=0;state<=MATRIX_MUL;end end
    else begin axis<=axis+1'b1;state<=ACC_NORMALIZE;end
   end
   // 重建以归一化重力初始化 Q24 四元数，航向采用相对零点；无磁力计绝对航向约束。
   SEED:begin
    if(an[2]< -32'sd16777000) begin q[0]<=0;q[1]<=ONE;q[2]<=0;q[3]<=0;end
    else begin q[0]<=ONE+an[2];q[1]<=an[1];q[2]<=-an[0];q[3]<=0;end
    integral_fraction<=0;integral_sum_q<=0;
    quaternion_fraction<=0;quaternion_delta_q<=0;
    ei[0]<=0;ei[1]<=0;ei[2]<=0;alignment<=1;aligned_ticks<=0;index<=0;norm2<=0;state<=NORM_SQUARE;
   end
   NORM_SQUARE:multiply(q[index],q[index],NORM_SUM);
   NORM_SUM:begin norm2<=norm2+prod;if(index==3) state<=NORM_ROOT;else begin index<=index+1'b1;state<=NORM_SQUARE;end end
   NORM_ROOT:root(norm2,NORM_ROOT_DONE);
   NORM_ROOT_DONE:if(s_result<1000 || s_result>67108864) invalidate(8'h40);else begin denominator<=s_result;index<=0;state<=NORM_DIV;end
   NORM_DIV:divide($signed(q[index])*64'sd16777216,denominator,NORM_DIV_DONE);
   NORM_DIV_DONE:begin q[index]<=quotient;if(index==3) begin matrix_for_output<=1;index<=0;state<=MATRIX_MUL;end else begin index<=index+1'b1;state<=NORM_DIV;end end
   MATRIX_MUL:case(index)
    0:multiply(q[0],q[1],MATRIX_STORE);1:multiply(q[0],q[2],MATRIX_STORE);
    2:multiply(q[1],q[1],MATRIX_STORE);3:multiply(q[1],q[3],MATRIX_STORE);
    4:multiply(q[2],q[2],MATRIX_STORE);5:multiply(q[2],q[3],MATRIX_STORE);
    6:multiply(q[3],q[3],MATRIX_STORE);7:multiply(q[1],q[2],MATRIX_STORE);
    8:multiply(q[0],q[3],MATRIX_STORE);
   endcase
   MATRIX_STORE:begin qprod[index]<=prod>>>24;if(index==8) state<=MATRIX_FORM;else begin index<=index+1'b1;state<=MATRIX_MUL;end end
   // 由归一化四元数构造完整传感器至世界旋转矩阵，分别供重力误差和世界加速度通路复用。
   MATRIX_FORM:begin
    matrix[0]<=ONE-2*(qprod[4]+qprod[6]);matrix[1]<=2*(qprod[7]-qprod[8]);matrix[2]<=2*(qprod[3]+qprod[1]);
    matrix[3]<=2*(qprod[7]+qprod[8]);matrix[4]<=ONE-2*(qprod[2]+qprod[6]);matrix[5]<=2*(qprod[5]-qprod[0]);
    matrix[6]<=2*(qprod[3]-qprod[1]);matrix[7]<=2*(qprod[5]+qprod[0]);matrix[8]<=ONE-2*(qprod[2]+qprod[4]);
    state<=MATRIX_CONT;
   end
   MATRIX_CONT:begin index<=0;if(matrix_for_output) begin component<=0;term<=0;accum<=0;state<=WORLD_SETUP;end else state<=CROSS_MUL;end
   CROSS_MUL:case(index)
    0:multiply(an[1],matrix[8],CROSS_STORE);1:multiply(matrix[7],an[2],CROSS_STORE);
    2:multiply(matrix[6],an[2],CROSS_STORE);3:multiply(an[0],matrix[8],CROSS_STORE);
    4:multiply(matrix[7],an[0],CROSS_STORE);5:multiply(an[1],matrix[6],CROSS_STORE);
   endcase
   CROSS_STORE:begin crossprod[index]<=prod>>>24;if(index==5) state<=CROSS_FORM;else begin index<=index+1'b1;state<=CROSS_MUL;end end
   CROSS_FORM:begin
    err[0]<=use_acc ? crossprod[0]-crossprod[1]:0;
    err[1]<=use_acc ? crossprod[2]-crossprod[3]:0;
    err[2]<=use_acc ? crossprod[4]-crossprod[5]:0;
    state<=52;
   end
   52:begin gravity_abs_x<=err[0]<0 ? -err[0]:err[0];gravity_abs_y<=err[1]<0 ? -err[1]:err[1];state<=53;end
   53:begin gravity_error_sum<={1'b0,gravity_abs_x}+{1'b0,gravity_abs_y};state<=DT_DIV;end
   // 初始/恢复对齐阶段使用较大比例增益，重力误差持续足够小时转入正常 PI 增益。
   DT_DIV:begin
    if(alignment && use_acc && gravity_error_sum<335544) begin
     if(aligned_ticks+held_dt>10000000) begin alignment<=0;aligned_ticks<=0;end else aligned_ticks<=aligned_ticks+held_dt;
    end else aligned_ticks<=0;
    divide($signed({1'b0,held_dt})*64'sd16777216,32'd50000000,DT_DONE);
   end
   DT_DONE:begin dt_q24<=quotient;axis<=0;state<=ERR_I_DT;end
   ERR_I_DT:multiply(clip_error(err[axis]),$signed(dt_q24),ERR_I_DT_DONE);
   ERR_I_DT_DONE:begin if(alignment) begin prod<=0;state<=ERR_I_GAIN_DONE;end else multiply(integral_round_q24(prod),32'sd167772,ERR_I_GAIN_DONE);end
   // 重力积分逐轴先乘真实 dt 和积分增益，再将保留分数与整数状态一起提交。
   ERR_I_GAIN_DONE:begin
    case(axis)
     0:integral_sum_q<=prod+$signed({40'd0,integral_fraction[23:0]});
     1:integral_sum_q<=prod+$signed({40'd0,integral_fraction[47:24]});
     2:integral_sum_q<=prod+$signed({40'd0,integral_fraction[71:48]});
     default:integral_sum_q<=64'bx;
    endcase
    state<=ERR_I_COMMIT;
   end
   ERR_I_COMMIT:begin
    ei[axis]<=ei[axis]+(integral_sum_q>>>24);
    case(axis)
     0:integral_fraction[23:0]<=integral_sum_q[23:0];
     1:integral_fraction[47:24]<=integral_sum_q[23:0];
     2:integral_fraction[71:48]<=integral_sum_q[23:0];
    endcase
    state<=48;
   end
   48:multiply(err[axis]+ei[axis],alignment ? 32'sd167772160:32'sd3355443,CORRECT_GAIN_DONE);
   CORRECT_GAIN_DONE:begin corrected_rate<=prod>>>24;multiply(selected_fusion_gyro(axis),32'sd17855,GYRO_SCALE_DONE);end
   // Q12 计数乘 Q24 弧度/计数得到 Q36 角速度；先完成缩放，
   // 再在此缩为 Q24，因此不足一个计数的角速度也可参与四元数积分。
   GYRO_SCALE_DONE:multiply((prod>>>12)+$signed(corrected_rate),$signed(dt_q24),DANGLE_DONE);
   DANGLE_DONE:begin
    da[axis]<=prod>>>17; // Q32 半角增量，保留不足一个计数所产生的微小转动。
    if((prod>>>25)>731998 || (prod>>>25)< -731998) invalidate(8'h20);
    else if(axis==2) begin component<=0;term<=0;accum<=0;state<=QUAT_SETUP;end
    else begin axis<=axis+1'b1;state<=ERR_I_DT;end
   end
   // 四元数按顺序更新并保留分数增量，随后重新归一化，再生成本次输出旋转矩阵。
   QUAT_SETUP:case(component)
    0:case(term) 0:multiply(q[1],da[0],QUAT_TERM);1:multiply(q[2],da[1],QUAT_TERM);2:multiply(q[3],da[2],QUAT_TERM);endcase
    1:case(term) 0:multiply(q[0],da[0],QUAT_TERM);1:multiply(q[2],da[2],QUAT_TERM);2:multiply(q[3],da[1],QUAT_TERM);endcase
    2:case(term) 0:multiply(q[0],da[1],QUAT_TERM);1:multiply(q[1],da[2],QUAT_TERM);2:multiply(q[3],da[0],QUAT_TERM);endcase
    3:case(term) 0:multiply(q[0],da[2],QUAT_TERM);1:multiply(q[1],da[1],QUAT_TERM);2:multiply(q[2],da[0],QUAT_TERM);endcase
   endcase
   QUAT_TERM:begin quaternion_term_q<=quaternion_term;state<=54;end
   54:begin quaternion_sum_q<=accum+quaternion_term_q;state<=term==2 ? 57:55;end
   57:begin
    case(component)
     0:quaternion_delta_q<=quaternion_sum_q+$signed({32'd0,quaternion_fraction[31:0]});
     1:quaternion_delta_q<=quaternion_sum_q+$signed({32'd0,quaternion_fraction[63:32]});
     2:quaternion_delta_q<=quaternion_sum_q+$signed({32'd0,quaternion_fraction[95:64]});
     3:quaternion_delta_q<=quaternion_sum_q+$signed({32'd0,quaternion_fraction[127:96]});
    endcase
    state<=55;
   end
   55:if(term==2) begin
    q[component]<=next_quaternion;term<=0;accum<=0;
    case(component)
     0:quaternion_fraction[31:0]<=quaternion_delta_q[31:0];
     1:quaternion_fraction[63:32]<=quaternion_delta_q[31:0];
     2:quaternion_fraction[95:64]<=quaternion_delta_q[31:0];
     3:quaternion_fraction[127:96]<=quaternion_delta_q[31:0];
    endcase
    if(component==3) begin index<=0;norm2<=0;state<=NORM_SQUARE;end else begin component<=component+1'b1;state<=QUAT_SETUP;end
   end else begin accum<=quaternion_sum_q;term<=term+1'b1;state<=QUAT_SETUP;end
   // 世界加速度由旋转矩阵乘机体系加速度得到，Z 分量扣除 9810 mm/s² 的重力。
   WORLD_SETUP:multiply(matrix[3*component+term],selected_accel(term),WORLD_TERM);
   WORLD_TERM:begin
    if(term==2) begin accum<=accum+prod;state<=WORLD_SCALE;end
    else begin accum<=accum+prod;term<=term+1'b1;state<=WORLD_SETUP;end
   end
   WORLD_SCALE:multiply(accum>>>16,32'sd9810,WORLD_SCALE_DONE);
   WORLD_SCALE_DONE:begin
    // Q24 旋转矩阵×原始计数×9810/2048，换算到 mm/s²。
    pending_world[component]<=($signed(prod)>>>19)-(component==2 ? 32'sd9810:0);
    if(component==2) begin
     if(LEVEL_TRIM_ENABLE) begin axis<=0;term<=0;accum<=0;state<=TRIM_GYRO_SETUP;end
     else state<=ROLL_START;
    end else begin component<=component+1'b1;term<=0;accum<=0;state<=WORLD_SETUP;end
   end
   TRIM_GYRO_SETUP:if(LEVEL_TRIM_ENABLE)multiply(trim_coefficient(axis,term),selected_gyro(term),TRIM_GYRO_TERM);else invalidate(8'h40);
   TRIM_GYRO_TERM:if(LEVEL_TRIM_ENABLE)begin
    accum<=accum+prod;
    if(term==2)state<=TRIM_GYRO_STORE;
    else begin term<=term+1'b1;state<=TRIM_GYRO_SETUP;end
   end else invalidate(8'h40);
   TRIM_GYRO_STORE:if(LEVEL_TRIM_ENABLE)begin
    pending_gyro[axis]<=accum>>>24;
    term<=0;accum<=0;
    if(axis==2)begin axis<=0;state<=TRIM_FINE_SETUP;end
    else begin axis<=axis+1'b1;state<=TRIM_GYRO_SETUP;end
   end else invalidate(8'h40);
   TRIM_FINE_SETUP:if(LEVEL_TRIM_ENABLE)multiply(trim_coefficient(axis,term),selected_fusion_gyro(term),TRIM_FINE_TERM);else invalidate(8'h40);
   TRIM_FINE_TERM:if(LEVEL_TRIM_ENABLE)begin
    accum<=accum+prod;
    if(term==2)state<=TRIM_FINE_STORE;
    else begin term<=term+1'b1;state<=TRIM_FINE_SETUP;end
   end else invalidate(8'h40);
   TRIM_FINE_STORE:if(LEVEL_TRIM_ENABLE)begin
    // Q24 旋转乘 Q12 计数得到 Q36；只舍入回 Q12，不舍入成整数计数。
    // 三个有界 32×32 位乘积及其和均适合有符号 64 位。
    case(axis)
     0:pending_fine_x<=integral_round_q24(accum);
     1:pending_fine_y<=integral_round_q24(accum);
     2:pending_fine_z<=integral_round_q24(accum);
    endcase
    term<=0;accum<=0;
    if(axis==2)begin index<=0;state<=TRIM_MATRIX_SETUP;end
    else begin axis<=axis+1'b1;state<=TRIM_FINE_SETUP;end
   end else invalidate(8'h40);
   // 精确提取 ZYX 欧拉角只需 Rs×T 转置的五个元素。
   // 原矩阵从不被覆盖，世界加速度与下一次重力反馈
   // 仍在原四元数坐标系中计算。
   TRIM_MATRIX_SETUP:if(LEVEL_TRIM_ENABLE)multiply(matrix[trim_matrix_index],trim_coefficient(trim_col,term),TRIM_MATRIX_TERM);else invalidate(8'h40);
   TRIM_MATRIX_TERM:if(LEVEL_TRIM_ENABLE)begin
    accum<=accum+prod;
    if(term==2)state<=TRIM_MATRIX_STORE;
    else begin term<=term+1'b1;state<=TRIM_MATRIX_SETUP;end
   end else invalidate(8'h40);
   TRIM_MATRIX_STORE:if(LEVEL_TRIM_ENABLE)begin
    trim_matrix[index]<=accum>>>24;
    term<=0;accum<=0;
    if(index==4)state<=ROLL_START;
    else begin index<=index+1'b1;state<=TRIM_MATRIX_SETUP;end
   end else invalidate(8'h40);
   // 依次用 CORDIC 提取横滚、俯仰和相对偏航；角度“度 Q16”乘 100 后转换为百分之一度。
   ROLL_START:begin c_x<=angle_r22;c_y<=angle_r21;c_start<=1;state<=ROLL_DONE;end
   ROLL_DONE:if(c_done) begin pending_roll<=cdeg_scaled>>>16;yz_magnitude<=c_mag;state<=PITCH_START;end
   PITCH_START:begin c_x<=yz_magnitude;c_y<=-angle_r20;c_start<=1;state<=PITCH_DONE;end
   PITCH_DONE:if(c_done) begin pending_pitch<=cdeg_scaled>>>16;state<=50;end
   50:begin c_x<=angle_r00;c_y<=angle_r10;c_start<=1;state<=51;end
   51:if(c_done) begin pending_yaw<=cdeg_scaled>>>16;state<=PUBLISH;end
   // 角度、陀螺、世界加速度和范围标志在 PUBLISH 同拍提交，update 仅脉冲一个时钟。
   PUBLISH:begin
    roll_cdeg<=pending_roll;pitch_cdeg<=pending_pitch;yaw_cdeg<=pending_yaw;yaw_range_ok<=publication_yaw_range;tilt4500_ok<=publication_tilt4500;tilt1500_ok<=publication_tilt1500;
    filtered_gx<=sat16(pending_gyro[0]);filtered_gy<=sat16(pending_gyro[1]);filtered_gz<=sat16(pending_gyro[2]);
    filtered_gx_q12<=pending_fine_x;filtered_gy_q12<=pending_fine_y;filtered_gz_q12<=pending_fine_z;
    world_ax_mmps2<=pending_world[0];world_ay_mmps2<=pending_world[1];world_az_mmps2<=pending_world[2];
    initialized<=1;ready<=1;lin_ok<=1;update<=1;accel_correction<=use_acc;fault<=0;state<=IDLE;
   end
   MUL_WAIT:if(m_done) begin prod<=m_result;state<=resume_state;end
   DIV_WAIT:if(d_done) begin if(d_error) invalidate(8'h40);else begin quotient<=d_result;state<=resume_state;end end
   ROOT_WAIT:if(s_done) state<=resume_state;
   default:invalidate(8'h40);
  endcase
 end
endmodule

// 共用精确有符号 32×32 位乘法器，每时钟最多一次 64 位加法。
// a/b 的定点或物理单位由调用方决定；result 为完整 64 位乘积，start 仅空闲接受，cancel 优先中止。
module ano_attitude_mul32(input wire clk,rst_n,start,cancel,
 input wire signed [31:0] a,b,output reg busy=0,output reg done=0,
 output reg signed [63:0] result=0);
 reg [63:0] lhs=0,acc=0;reg [31:0] rhs=0;reg [5:0] left=0;
 wire [63:0] sum=left==1 ? acc-(rhs[0]?lhs:64'd0):acc+(rhs[0]?lhs:64'd0);
 // 移位累加共执行 32 步，最后一位按乘数符号作减法；完成时 result 与 done 同拍提交。
 always @(posedge clk) begin
  done<=0;
  if(!rst_n || cancel) begin busy<=0;left<=0;result<=0;end
  else if(start && !busy) begin lhs<={{32{a[31]}},a};rhs<=b;acc<=0;left<=32;busy<=1;end
  else if(busy) begin acc<=sum;lhs<=lhs<<1;rhs<=rhs>>1;left<=left-1'b1;if(left==1) begin result<=sum;busy<=0;done<=1;end end
 end
endmodule
// 有符号 64 位分子除以无符号 32 位分母的恢复除法器，结果精确向零截断。
// start 空闲时锁存输入，busy 表示正在处理，done 为单拍；除零或 INT64_MIN 立即以 error 报错。
module ano_attitude_div64(input wire clk,rst_n,start,cancel,
 input wire signed [63:0] numerator,input wire [31:0] denominator,
 output reg busy=0,output reg done=0,output reg error=0,output reg signed [63:0] quotient=0);
 reg [63:0] work=0;reg [31:0] remainder=0,divisor=1;reg [6:0] left=0;reg negative=0;
 wire [32:0] trial={remainder,work[63]};wire subtract=trial>={1'b0,divisor};
 wire [32:0] reduced=subtract ? trial-{1'b0,divisor}:trial;
 wire [63:0] next={work[62:0],subtract};
 always @(posedge clk) begin
  done<=0;
  if(!rst_n || cancel) begin busy<=0;left<=0;error<=0;quotient<=0;end
  else if(start && !busy) begin
   if(denominator==0 || numerator==64'sh8000000000000000) begin error<=1;done<=1;quotient<=0;end
   else begin work<=numerator<0 ? -numerator:numerator;negative<=numerator<0;divisor<=denominator;remainder<=0;left<=64;busy<=1;error<=0;end
  // 按绝对值逐位试减生成商，64 步后恢复符号；不会进行最近舍入。
  end else if(busy) begin
   remainder<=reduced[31:0];work<=next;left<=left-1'b1;
   if(left==1) begin quotient<=negative ? -$signed(next):$signed(next);busy<=0;done<=1;end
  end
 end
endmodule
// 无符号 64 位整数向下取整开方，32 次恢复迭代，无除法或 DSP 模块。
// radicand/result 均为整数，输出满足 result²≤输入；输入和输出单位分别为所求物理量的平方与本量。
module ano_attitude_sqrt64(input wire clk,rst_n,start,cancel,
 input wire [63:0] radicand,output reg busy=0,output reg done=0,
 output reg [31:0] result=0);
 reg [63:0] bits=0;reg [65:0] rem=0;reg [31:0] root_value=0;reg [5:0] left=0;
 wire [65:0] trial_rem={rem[63:0],bits[63:62]};
 wire [65:0] trial_sub={32'b0,root_value,2'b01};
 wire pass=trial_rem>=trial_sub;
 always @(posedge clk) begin
  done<=0;
  if(!rst_n || cancel) begin busy<=0;left<=0;result<=0;end
  else if(start && !busy) begin bits<=radicand;rem<=0;root_value<=0;left<=32;busy<=1;end
  // 每拍移入两位被开方数，试减生成一位根，32 步完成并发出单拍 done；cancel 取消在途结果。
  else if(busy) begin
   rem<=pass ? trial_rem-trial_sub:trial_rem;root_value<={root_value[30:0],pass};bits<=bits<<2;left<=left-1'b1;
   if(left==1) begin result<={root_value[30:0],pass};busy<=0;done<=1;end
  end
 end
endmodule
