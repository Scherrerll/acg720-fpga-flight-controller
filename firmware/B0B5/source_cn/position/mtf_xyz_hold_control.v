`timescale 1ns/1ps
// ANO 参考控制器移植：两种模式均使用 Z 环，OF 分支使用 XY 速度 PI。
// 物理接口、FRD 坐标及单位适配约定见 CONTROL_CONTRACT.txt。
// 本控制器不采用油门居中进入、重新拨档确认锁存、位置外环、
// 进入时推力捕获或手动接管策略。
// 控制器以高度环为基础，CH7 高档再请求 XY 速度 PI；高度请求随 RC 有效性产生。
// 高度为 mm；速度按参数采用整数或 Q16 mm/s，角度为百分之一度，油门接口为 us。
module mtf_xyz_hold_control #(
 parameter integer ENTRY_TICKS=10000000,CLK_HZ=50000000,
 parameter [7:0] CAL_MASK=0,
 parameter integer VELOCITY_FRAC_BITS=0,
 parameter integer MAX_ANGLE=2500,MAX_DELTA_US=1000,
 parameter integer POSITION_KP_Q16=65536
)(
 input wire clk,rst_n,origin_reset,rc_valid,input wire [3:0] channel_count,
 input wire [15:0] ch1,ch2,ch3,ch4,ch7,
 // xy_p/i_value 为运行时参数线值，整对参数在空闲边界锁存；parameter_boundary 供参数库安全切换。
 input wire [15:0] xy_p_value,xy_i_value,
 output wire parameter_boundary,
 input wire enabled,taking_off,position_valid,height_valid,position_update,height_update,
 // sample_dt_us/position_dt_us 为 us，position_age 为 clk 拍；sample_update 驱动 1 ms 摇杆重放。
 input wire sample_update,input wire [31:0] sample_dt_us,
 input wire [31:0] position_age,position_dt_us,
 input wire signed [31:0] x_q8,y_q8,vx,vy,height_mm,vz,
 input wire signed [15:0] yaw_cdeg,
 input wire acc_valid,input wire signed [31:0] ax_mmps2,ay_mmps2,az_mmps2,
 input wire [15:0] collective_us,
 output wire requested,ready,active,height_requested,height_ready,height_active,auto_takeoff,
 output reg [15:0] reason,height_reason,
 output reg [15:0] collective_target_us,
 output reg signed [15:0] roll_target,pitch_target,throttle_delta,
 output reg signed [31:0] requested_climb_mmps,target_height_mm,
 output wire signed [17:0] pilot_norm_x,pilot_norm_y,
 output wire pilot_norm_update,pilot_norm_valid,output wire [15:0] pilot_norm_dt_us,
 // 共享服务接收一次乘除 start 后返回对应 done；math_cancel 同时取消当前控制事务与算术。
 output wire math_mul_start,math_mul_cancel,
 output wire signed [63:0] math_mul_a,math_mul_b,
 input wire math_mul_busy,math_mul_done,
 input wire signed [63:0] math_mul_result,
 output wire math_div_start,math_div_cancel,
 output wire signed [63:0] math_div_numerator,
 output wire [31:0] math_div_denominator,
 input wire math_div_busy,math_div_done,math_div_error,
 input wire signed [63:0] math_div_result
);
 // 位宽优化仅改变寄存器的存储表示；原名称仍作为
 // 64 位有符号别名使用，保留每次运算原有的位宽和符号语义。
 function signed [63:0] keep64;
 input signed [63:0] a;begin keep64=a;end endfunction
 // 命令超时阈值为 CLK_HZ/10 拍，即默认 100 ms；过期会取消控制事务。
 localparam AGE_LIMIT=CLK_HZ/10;
 localparam signed [31:0] INPUT_V_LIMIT=32'sd10000<<<VELOCITY_FRAC_BITS;
 initial if(VELOCITY_FRAC_BITS!=0 && VELOCITY_FRAC_BITS!=16)$error("Unsupported velocity fraction bits");
 reg tracking=0,xy_tracking=0,command_seen=0,height_command_seen=0,blocked=0,xy_blocked=0;
 reg [15:0] fault_reason=0;
 reg [31:0] prepare=0,xy_prepare=0,command_age=32'hffffffff,height_command_age=32'hffffffff;
 reg height_due=0,position_due=0,work_xy=0;
 reg height_stick_captured=0;reg signed [28:0] pending_z_speed=0;
 reg position_stick_captured=0;reg signed [17:0] pending_nx=0,pending_ny=0;
 assign requested=rc_valid && channel_count>=7 && ch7>=1800 && ch7<=2200;
 assign height_requested=rc_valid;
 // 这里只流水处理数值资格：先锁存输入，再在独立时钟拍比较。
 // 尤其避免上游世界 Y 轴有符号取反与 32 位边界比较、
 // 模式判断以及电机/遥测接收逻辑挤在同一条组合路径上。
 // 数值越界撤销最多延迟 2 拍（50 MHz 时为 40 ns）。
 // 下方通信/传感器实时有效性、RC/SWA/解锁、驾驶意图和时效检查
 // 仍为组合门控；上述紧急屏蔽条件均不经这条数值流水延迟。
 reg [15:0] check_collective=0,check_ch3=0;
 reg signed [31:0] check_height=0,check_vz=0,check_az=0;
 reg signed [31:0] check_vx=0,check_vy=0,check_ax=0,check_ay=0;
 reg signed [15:0] check_yaw=0;
 reg hbounds_q=0,xybounds_q=0;
 always @(posedge clk)begin
  if(!rst_n)begin
   check_collective<=0;check_ch3<=0;check_height<=0;check_vz<=0;check_az<=0;
   check_vx<=0;check_vy<=0;check_ax<=0;check_ay<=0;check_yaw<=0;
   hbounds_q<=0;xybounds_q<=0;
  end else begin
   check_collective<=collective_us;check_ch3<=ch3;check_height<=height_mm;check_vz<=vz;check_az<=az_mmps2;
   check_vx<=vx;check_vy<=vy;check_ax<=ax_mmps2;check_ay<=ay_mmps2;check_yaw<=yaw_cdeg;
   hbounds_q<=check_collective>=1000 && check_collective<=2000 && check_ch3>=900 && check_ch3<=2200 && check_height>=0 && check_height<=5000 && check_vz>=-INPUT_V_LIMIT && check_vz<=INPUT_V_LIMIT && check_az>=-30000 && check_az<=30000;
   xybounds_q<=check_vx>=-INPUT_V_LIMIT && check_vx<=INPUT_V_LIMIT && check_vy>=-INPUT_V_LIMIT && check_vy<=INPUT_V_LIMIT && check_ax>=-30000 && check_ax<=30000 && check_ay>=-30000 && check_ay<=30000 && check_yaw>=-18000 && check_yaw<=18000;
  end
 end
 wire z_stick_busy,z_stick_fault;
 wire signed [17:0] z_norm_q16;
 wire signed [28:0] z_speed_q16;
 // 公开就绪信号仅表示数值与时效资格，RC/解锁条件在活动门控中判断。
 // Z 轴数值资格保持独立，避免 ready 与 height_ready 相互反馈。
 // ready 仅表示传感器、标定掩码及数值资格；活动还须解锁、起飞阶段和完整命令成立。
 wire z_numeric_ready=(CAL_MASK &8'h98)==8'h98 && height_valid && acc_valid && hbounds_q && !z_stick_fault;
 assign ready=CAL_MASK==8'hff && position_valid && z_numeric_ready && xybounds_q && position_age<AGE_LIMIT && !origin_reset;
 assign height_ready=z_numeric_ready && !origin_reset;
 wire command_stale=(command_seen && command_age>=AGE_LIMIT) || (height_command_seen && height_command_age>=AGE_LIMIT);
 wire cancel_now=!rc_valid || !enabled || !height_ready || blocked || command_stale;
 ano_z_stick z_stick(.clk(clk),.rst_n(rst_n),.enabled(rc_valid && !origin_reset),.taking_off(taking_off),
  .sample_update(sample_update),.sample_dt_us(sample_dt_us),.ch3(ch3),
  .norm_q16(z_norm_q16),.speed_q16(z_speed_q16),.busy(z_stick_busy),.update(),.fault(z_stick_fault));
 wire xy_stick_busy,xy_stick_fault;wire signed [17:0] stick_nx,stick_ny;
 ano_xy_stick xy_stick(.clk(clk),.rst_n(rst_n),.enabled(rc_valid && !origin_reset),
  .sample_update(sample_update),.sample_dt_us(sample_dt_us),.ch1(ch1),.ch2(ch2),
  .nx(stick_nx),.ny(stick_ny),.busy(xy_stick_busy),.fault(xy_stick_fault),
  .update(pilot_norm_update),.valid(pilot_norm_valid),.output_dt_us(pilot_norm_dt_us));
 assign pilot_norm_x=stick_nx;assign pilot_norm_y=stick_ny;
 wire xy_cancel_now=cancel_now || !requested || !ready || xy_stick_fault || !tracking;
 assign active=requested && enabled && ready && taking_off && tracking && xy_tracking && command_seen && !command_stale && !blocked && !xy_stick_fault;
 assign height_active=enabled && height_ready && taking_off && tracking && height_command_seen && !command_stale && !blocked;
 reg cancel=1,xy_cancel=1;
 always @(posedge clk) if(!rst_n)begin cancel<=1;xy_cancel<=1;end else begin cancel<=cancel_now;xy_cancel<=xy_cancel_now;end
 wire math_cancel=cancel || origin_reset || work_xy && xy_cancel;
 reg signed [31:0] target_x=0,target_y=0;
 assign auto_takeoff=taking_off && auto_phase==1;
 reg [1:0] auto_phase=0;reg [15:0] auto_ms=0;
 reg signed [31:0] auto_speed=0,alt_speed=0,next_auto_speed=0;
 reg signed [63:0] inner_alt_speed=0;
 reg signed [31-1:0] target_z_q16_store=0;
 reg signed [30-1:0] height_feedback_old_store=0;
 reg signed [27-1:0] ix_store=0;
 reg signed [27-1:0] iy_store=0;
 reg signed [26:0] saved_ix=0,saved_iy=0;
 reg signed [32:0] saved_afx=0,saved_afy=0;
 reg signed [33-1:0] iz_store=0;
 // Z 条件积分按总油门最终输出的 0..850 电机单位范围判断；
 // 候选积分暂存在内部，等比例项 P 和更新后的偏置都已确定
 // 才提交；中途取消不会提交部分积分步骤。
 // 按生存期复用寄存器；每个值都先写入，再在其有效阶段使用。
 // 状态 22 先使用旧积分下界，再将同一存储复用于候选积分 I。
 wire signed [32:0] candidate_iz_store=iz_lower_q[32:0];
 wire signed [32:0] p_bias_store={{2{exz_store[30]}},exz_store};
 wire signed [32:0] candidate_collective_store=inner_alt_speed[32:0];
 wire signed [32:0] current_collective_store={{2{sample_vx_store[30]}},sample_vx_store};
 reg candidate_i_up=0,candidate_i_down=0;
 wire signed [63:0] candidate_iz={{31{candidate_iz_store[32]}},candidate_iz_store};
 wire signed [63:0] p_bias={{31{p_bias_store[32]}},p_bias_store};
 wire signed [63:0] candidate_collective={{31{candidate_collective_store[32]}},candidate_collective_store};
 wire signed [63:0] current_collective={{31{current_collective_store[32]}},current_collective_store};
 // 按源算法边界，两种求和都可放入 31 位有符号 Q16；先保持 64 位
 // 表达式语义，再显式截取并符号扩展对应位。
 wire signed [63:0] compact_candidate_sum=p_bias+candidate_iz;
 wire signed [30:0] compact_candidate_sum31=compact_candidate_sum[30:0];
 // 高度抗积分饱和按最终 P+偏置+I 候选值判断，输出范围为 Q16 的 0..850 电机单位。
 // 候选越上限且积分继续增大、或越下限且积分继续减小时，保留旧 I 与旧 I 对应总量。
 // 反向积分仍可提交，允许退出饱和；判断不只依据积分项自身的上下界。
 wire reject_z_i=(candidate_collective>64'sd55705600 && candidate_i_up) ||
                 (candidate_collective<0 && candidate_i_down);
 wire signed [63:0] selected_z_i=reject_z_i ? iz:candidate_iz;
 wire signed [63:0] selected_z_collective=reject_z_i ? current_collective:candidate_collective;
 reg signed [33-1:0] bias_store=0;
 // 等待共享算术返回时，锁存原有 64 位有符号候选积分上下界。
 // 状态 22 暂存候选值，状态 67 在最终 P+偏置+I
 // 饱和检查后才提交；实时安全屏蔽可在任一阶段取消。
 reg signed [63:0] iz_lower_q=0,iz_upper_q=0;
 reg signed [33-1:0] afx_store=0;
 reg signed [33-1:0] afy_store=0;
 reg signed [32-1:0] afz_store=0;
 reg signed [29-1:0] sx_store=0;
 reg signed [29-1:0] sy_store=0;
 reg signed [28-1:0] world_sx_store=0;
 reg signed [28-1:0] world_sy_store=0;
 reg signed [32-1:0] world_ax_store=0;
 reg signed [32-1:0] world_ay_store=0;
 reg signed [32-1:0] ex_store=0;
 reg signed [32-1:0] ey_store=0;
 reg signed [32-1:0] fixx_store=0;
 reg signed [32-1:0] fixy_store=0;
 // 运行时 P 最大为 1.0，对应内部增益 10；保留完整 P+I+前馈之和，
 // 再做最终 ±25 度限幅；旧 32 位有符号 Q16 在 32768 百分之一度时可能回绕。
 reg signed [35:0] ux_store=0;
 reg signed [35:0] uy_store=0;
 reg signed [33-1:0] hx_store=0;
 reg signed [33-1:0] hy_store=0;
 reg signed [31-1:0] sample_vx_store=0;
 reg signed [31-1:0] sample_vy_store=0;
 reg signed [17-1:0] alpha_store=0;
 reg signed [31-1:0] exz_store=0;
 reg signed [28-1:0] vsz_store=0;
 reg signed [29-1:0] speed_z_tick_store=0;
 reg signed [27-1:0] collective_q16_store=0;
 reg signed [31:0] pending_h=0,pending_vz=0,pending_az=0;
 reg signed [31:0] held_h=0,held_az=0;
 reg signed [31:0] px=0,py=0,pvx=0,pvy=0,pax=0,pay=0,ph=0;
 reg signed [15:0] pyaw=0;reg [31:0] pdt=20000;
 reg signed [24-1:0] angle_store=0;
 reg signed [33-1:0] rot_tmp_store=0;
 reg signed [33-1:0] position_ex_store=0;
 reg signed [33-1:0] position_ey_store=0;
 reg signed [((POSITION_KP_Q16==65536)?49:64)-1:0] position_px_store=0;
 reg signed [((POSITION_KP_Q16==65536)?49:64)-1:0] position_py_store=0;
 reg signed [((POSITION_KP_Q16==65536)?41:64)-1:0] position_qx_store=0;
 reg signed [((POSITION_KP_Q16==65536)?41:64)-1:0] position_qy_store=0;
 reg signed [31:0] publish_roll=0,publish_pitch=0,publish_height=0,publish_speed=0,publish_collective=0,publish_delta=0;
 reg [31:0] dt=20000,base=1000;
 wire signed [63:0] target_z_q16={{33{target_z_q16_store[30]}},target_z_q16_store};
 wire signed [63:0] height_feedback_old={{34{height_feedback_old_store[29]}},height_feedback_old_store};
 wire signed [63:0] ix={{37{ix_store[26]}},ix_store};
 wire signed [63:0] iy={{37{iy_store[26]}},iy_store};
 wire signed [63:0] iz={{31{iz_store[32]}},iz_store};
 wire signed [63:0] bias={{31{bias_store[32]}},bias_store};
 wire signed [63:0] afx={{31{afx_store[32]}},afx_store};
 wire signed [63:0] afy={{31{afy_store[32]}},afy_store};
 wire signed [63:0] afz={{32{afz_store[31]}},afz_store};
 wire signed [63:0] sx={{35{sx_store[28]}},sx_store};
 wire signed [63:0] sy={{35{sy_store[28]}},sy_store};
 wire signed [63:0] world_sx={{36{world_sx_store[27]}},world_sx_store};
 wire signed [63:0] world_sy={{36{world_sy_store[27]}},world_sy_store};
 wire signed [63:0] world_ax={{32{world_ax_store[31]}},world_ax_store};
 wire signed [63:0] world_ay={{32{world_ay_store[31]}},world_ay_store};
 wire signed [63:0] ex={{32{ex_store[31]}},ex_store};
 wire signed [63:0] ey={{32{ey_store[31]}},ey_store};
 wire signed [63:0] fixx={{32{fixx_store[31]}},fixx_store};
 wire signed [63:0] fixy={{32{fixy_store[31]}},fixy_store};
 wire signed [63:0] ux={{28{ux_store[35]}},ux_store};
 wire signed [63:0] uy={{28{uy_store[35]}},uy_store};
 wire signed [63:0] hx={{31{hx_store[32]}},hx_store};
 wire signed [63:0] hy={{31{hy_store[32]}},hy_store};
 wire signed [63:0] sample_vx={{33{sample_vx_store[30]}},sample_vx_store};
 wire signed [63:0] sample_vy={{33{sample_vy_store[30]}},sample_vy_store};
 wire signed [63:0] alpha={{47{alpha_store[16]}},alpha_store};
 wire signed [63:0] exz={{33{exz_store[30]}},exz_store};
 wire signed [63:0] vsz={{36{vsz_store[27]}},vsz_store};
 wire signed [63:0] norm_lpf={{46{z_norm_q16[17]}},z_norm_q16};
 wire signed [63:0] speed_z={{35{z_speed_q16[28]}},z_speed_q16};
 wire signed [63:0] speed_z_tick={{35{speed_z_tick_store[28]}},speed_z_tick_store};
 wire signed [63:0] collective_q16={{37{collective_q16_store[26]}},collective_q16_store};
 wire signed [63:0] angle={{40{angle_store[23]}},angle_store};
 wire signed [63:0] rot_tmp={{31{rot_tmp_store[32]}},rot_tmp_store};
 wire signed [63:0] position_ex={{31{position_ex_store[32]}},position_ex_store};
 wire signed [63:0] position_ey={{31{position_ey_store[32]}},position_ey_store};
 wire signed [63:0] position_px=$signed(position_px_store);
 wire signed [63:0] position_py=$signed(position_py_store);
 wire signed [63:0] position_qx=$signed(position_qx_store);
 wire signed [63:0] position_qy=$signed(position_qy_store);
 wire signed [63:0] horizontal_speed_limit_q16=clip($signed(ph)*64'sd98304,64'sd32768000,64'sd98304000);
 reg [7:0] state=0,return_state=0;
 // 停止或取消状态的空闲边界不会在参数库提交新参数对的同一拍
 // 启动仍使用旧系数的回调。
 // 参数仅在停止的空闲边界切换，每次回调锁定一对 P/I，避免两轴使用不同参数。
 assign parameter_boundary=state==0 && cancel;
 // 每次回调统一锁存整对 P/I 参数，不在两轴之间更换参数。
 reg [15:0] work_p=1000,work_i=350;
 always @(posedge clk) if(state==0)begin
  work_p<=xy_p_value;work_i<=xy_i_value;
  saved_ix<=ix_store;saved_iy<=iy_store;
 end
 reg mul_start=0,div_start=0,trig_start=0;
 reg signed [33:0] ma_store=0;
 wire signed [63:0] ma={{30{ma_store[33]}},ma_store};
 reg signed [27:0] mb_store=0;
 wire signed [63:0] mb={{36{mb_store[27]}},mb_store};
 reg signed [63:0] num=0;
 reg signed [47:0] value_store=0;
 wire signed [63:0] value={{16{value_store[47]}},value_store};
 // 三个 Z 加法在互斥状态下使用同一算术返回值，
 // 因此共享完整 64 位有符号加法器：状态 22 加 I，状态 23/24 加偏置。
 wire signed [63:0] z_add_rhs=state==22 ?iz:bias;
 wire signed [63:0] z_shared_sum=value+z_add_rhs;
 // 拆分原有 64 位有符号加法与限幅路径，保持算术位宽；
 // 通过四组 16 位比较保持有符号数从高位到低位的比较顺序；
 // 每次 11 ms 高度计算仅增加 2 拍，安全门控不增加延迟。
 reg signed [63:0] target_sum_q=0;
 reg signed [30:0] target_lo_store=0,target_hi_store=0;
 wire signed [63:0] target_lo_q={{33{target_lo_store[30]}},target_lo_store};
 wire signed [63:0] target_hi_q={{33{target_hi_store[30]}},target_hi_store};
 reg [3:0] target_lt_lo_q=0,target_eq_lo_q=0,target_gt_hi_q=0,target_eq_hi_q=0;
 wire target_below_lo=target_lt_lo_q[3] || (target_eq_lo_q[3] &&
  (target_lt_lo_q[2] || (target_eq_lo_q[2] &&
  (target_lt_lo_q[1] || (target_eq_lo_q[1] && target_lt_lo_q[0])))));
 wire target_above_hi=target_gt_hi_q[3] || (target_eq_hi_q[3] &&
  (target_gt_hi_q[2] || (target_eq_hi_q[2] &&
  (target_gt_hi_q[1] || (target_eq_hi_q[1] && target_gt_hi_q[0])))));
 reg [31:0] den=1,pending_den=1;
 wire md,mbusy,dd,dbusy,derr,trig_done,trig_busy;wire signed [63:0] product,quotient;wire signed [17:0] sn,cs;
 assign math_mul_start=mul_start;assign math_mul_cancel=math_cancel;
 assign math_mul_a=ma;assign math_mul_b=mb;
 assign mbusy=math_mul_busy;assign md=math_mul_done;assign product=math_mul_result;
 assign math_div_start=div_start;assign math_div_cancel=math_cancel;
 assign math_div_numerator=num;assign math_div_denominator=den;
 assign dbusy=math_div_busy;assign dd=math_div_done;assign derr=math_div_error;assign quotient=math_div_result;
 position_sincos t(.clk(clk),.rst_n(rst_n),.start(trig_start),.cancel(math_cancel),.angle_q20(angle[31:0]),.busy(trig_busy),.done(trig_done),.sin_q16(sn),.cos_q16(cs));
 function signed [63:0] clip;
 input signed [63:0] a,lo,hi;begin clip=a<lo ? lo:a>hi ? hi:a;end endfunction
 function signed [63:0] integer_q16;
 input signed [63:0] a;begin integer_q16=(a>>>16)+(a[63] && |a[15:0] ?64'sd1:64'sd0);end endfunction
 function signed [63:0] integer_q8;
 input signed [63:0] a;begin integer_q8=(a>>>8)+(a[63] && |a[7:0] ?64'sd1:64'sd0);end endfunction
 // 传感器高度资格为 0..5000 mm，除以 10 时保留已证明足够的 13 位输入。
 // 越界值仍视为不合格，禁止截位回绕成合法距离。
 // 高度反馈先截成整 cm 再还原为 Q16 mm，保持原参考控制器的量化边界。
 function [9:0] measured_cm;
 input signed [31:0] h;
 begin measured_cm=h<0 ?0:h>5000 ?500:h[12:0]/13'd10;end endfunction
 function signed [31:0] feedback_height_q16;
 input signed [31:0] h;
 reg [28:0] scaled;
 begin scaled=measured_cm(h)*29'd655360;feedback_height_q16=$signed({3'd0,scaled});end endfunction
 function signed [31:0] quantized_climb_q16;
 input signed [28:0] v;
 reg signed [13:0] whole_mm;
 reg signed [9:0] cm;
 begin
  whole_mm=$signed(v[28:16])+(v[28] && |v[15:0] ?14'sd1:14'sd0);
  cm=whole_mm/14'sd10;quantized_climb_q16=cm*32'sd655360;
 end endfunction
 wire signed [31:0] quantized_climb_logic_q16 /* synthesis syn_dspstyle="logic" */;
 assign quantized_climb_logic_q16=quantized_climb_q16(speed_z_tick_store);
 function [9:0] auto_takeoff_mmps;
 input signed [31:0] h;
 reg [10:0] twice_gap;reg [6:0] cmps;
 begin
  if(h>=600 || h<0)auto_takeoff_mmps=0;
  else if(h<=200)auto_takeoff_mmps=800;
  else begin twice_gap=(11'd600-{1'b0,h[9:0]})<<1;cmps=twice_gap/11'd10;auto_takeoff_mmps=cmps*10'd10;end
 end endfunction
 // calc 保存续算状态后先乘后除；100/101 统一处理算术等待、返回和故障锁存。
 task calc;
 input signed [63:0] a,b;input [31:0] denominator;input [7:0] dest;
 begin ma_store<=a;mb_store<=b;pending_den<=denominator;return_state<=dest;mul_start<=1;state<=100;end endtask
 initial begin reason=1;height_reason=1;roll_target=0;pitch_target=0;throttle_delta=0;collective_target_us=1000;requested_climb_mmps=0;target_height_mm=0;end
 always @(posedge clk) begin
  mul_start<=0;div_start<=0;trig_start<=0;
  if(!rst_n)begin
   state<=0;tracking<=0;xy_tracking<=0;command_seen<=0;height_command_seen<=0;blocked<=0;xy_blocked<=0;
   prepare<=0;xy_prepare<=0;height_due<=0;position_due<=0;work_xy<=0;command_age<=32'hffffffff;height_command_age<=32'hffffffff;fault_reason<=0;
   target_x<=0;target_y<=0;height_feedback_old_store<=keep64(0);
   ix_store<=keep64(0);iy_store<=keep64(0);iz_store<=keep64(0);bias_store<=keep64(0);iz_lower_q<=0;iz_upper_q<=0;candidate_i_up<=0;candidate_i_down<=0;afx_store<=keep64(0);afy_store<=keep64(0);afz_store<=keep64(0);vsz_store<=keep64(0);target_z_q16_store<=keep64(0);
   roll_target<=0;pitch_target<=0;throttle_delta<=0;collective_target_us<=1000;reason<=1;height_reason<=1;requested_climb_mmps<=0;target_height_mm<=0;
  end else begin
   if(command_age!=32'hffffffff)command_age<=command_age+1'b1;
   if(height_command_age!=32'hffffffff)height_command_age<=height_command_age+1'b1;
   // 故障终止当前计算；正常模式或传感器恢复不要求重新拨档确认。
   // 算术故障需在上锁时清除。
   if(!enabled || origin_reset)begin blocked<=0;xy_blocked<=0;fault_reason<=0;end
   // 总取消清除积分、滤波和目标；单独取消正在执行的 XY 事务时回滚到上次完整状态。
   if(cancel || origin_reset || blocked)begin
    state<=0;tracking<=0;xy_tracking<=0;command_seen<=0;height_command_seen<=0;prepare<=0;xy_prepare<=0;height_due<=0;position_due<=0;work_xy<=0;
    ix_store<=keep64(0);iy_store<=keep64(0);iz_store<=keep64(0);bias_store<=keep64(0);iz_lower_q<=0;iz_upper_q<=0;candidate_i_up<=0;candidate_i_down<=0;afx_store<=keep64(0);afy_store<=keep64(0);afz_store<=keep64(0);vsz_store<=keep64(0);target_z_q16_store<=keep64(0);
    target_x<=0;target_y<=0;height_feedback_old_store<=keep64(0);
    roll_target<=0;pitch_target<=0;throttle_delta<=0;collective_target_us<=1000;requested_climb_mmps<=0;target_height_mm<=0;
    reason<=origin_reset ?1024:!rc_valid ?1:!enabled ?2:!ready ?4:blocked ?fault_reason:64;
    height_reason<=origin_reset ?1024:!rc_valid ?1:!enabled ?2:!height_ready ?8:blocked ?fault_reason:64;
    auto_phase<=0;auto_ms<=0;auto_speed<=0;alt_speed<=0;next_auto_speed<=0;
   // 首个有效高度回调统一建立 X/Y/Z 跟踪状态；先按整 cm 反馈建高度目标，再等待完整新命令。
   end else if(!tracking)begin
    if(height_update)begin
     target_z_q16_store<=keep64(feedback_height_q16(height_mm));height_feedback_old_store<=keep64(feedback_height_q16(height_mm));target_height_mm<=measured_cm(height_mm)*32'd10;
     target_x<=x_q8;target_y<=y_q8;tracking<=1;xy_tracking<=1;
     command_seen<=0;height_command_seen<=0;command_age<=32'hffffffff;height_command_age<=32'hffffffff;
     bias_store<=keep64(0);reason<=64;height_reason<=64;
    end
   end else begin
    // 高度与 XY 各保留一个待办样本；旧待办尚未处理又来新样本时锁存事务溢出故障。
    if(height_update)begin
     if(height_due)begin blocked<=1;xy_blocked<=1;fault_reason<=128;height_reason<=128;end
     else begin height_due<=1;height_stick_captured<=0;pending_h<=height_mm;pending_vz<=vz;pending_az<=az_mmps2;end
    end
    // 每次 11 ms 回调都锁存已完成的 1 ms 摇杆状态，即便当时
    // 共享算术正被 XY 事务占用；后续 XY 运算延迟不得
    // 用更新的升降设定值替换旧高度数据组中的设定值。
    // 每个高度回调锁存已完成的摇杆速度，后续共享算术延迟不会换入更新的升降指令。
    if(height_due && !height_stick_captured && !z_stick_busy && !sample_update)begin
     pending_z_speed<=z_speed_q16;height_stick_captured<=1;
    end
    // 上方统一进入时已经捕获 X/Y/Z；CH7 高档下没有另一次 XY 等待，
    // 也没有独立活动的仅 Z 模式。
    if(xy_cancel)begin position_due<=0;command_seen<=0;end
    else if(position_update)begin
      if(position_due || position_dt_us<1000 || position_dt_us>100000)begin blocked<=1;xy_blocked<=1;fault_reason<=128;reason<=128;end
     else begin position_due<=1;position_stick_captured<=0;px<=x_q8;py<=y_q8;pvx<=vx;pvy<=vy;pax<=ax_mmps2;pay<=ay_mmps2;ph<=height_mm;pyaw<=yaw_cdeg;pdt<=position_dt_us;end
    end
    if(position_due && !position_stick_captured && !xy_stick_busy && !sample_update)begin
     pending_nx<=stick_nx;pending_ny<=stick_ny;position_stick_captured<=1;
    end
    if(work_xy && xy_cancel)begin
     state<=0;work_xy<=0;ix_store<=saved_ix;iy_store<=saved_iy;afx_store<=saved_afx;afy_store<=saved_afy;
    end
    else case(state)
     // 空闲时先处理高度事务，随后才处理 XY；乘除法通过共享服务逐步完成。
     0:if(height_due && height_stick_captured)begin
      height_due<=0;work_xy<=0;base<=collective_us;sample_vx_store<=keep64(($signed({{32{pending_vz[31]}},pending_vz})<<<(16-VELOCITY_FRAC_BITS)));
      held_h<=pending_h;held_az<=pending_az;speed_z_tick_store<=keep64(pending_z_speed);
      inner_alt_speed<=alt_speed;calc($signed(pending_az)*65536-afz,1,5,20);
     end else if(position_due && position_stick_captured && !xy_cancel)begin
      position_due<=0;work_xy<=1;
      // 源回调作为完整事务处理；若 FPGA 回调执行一半被取消则回滚，
      // 在 ATT_STAB 中保留上一次完整提交的 OF PI/滤波状态。
      saved_afx<=afx_store;saved_afy<=afy_store;
      position_ex_store<=keep64($signed(target_x)-$signed(px));position_ey_store<=keep64($signed(target_y)-$signed(py));
      sample_vx_store<=keep64(($signed({{32{pvx[31]}},pvx})<<<(16-VELOCITY_FRAC_BITS)));sample_vy_store<=keep64(($signed({{32{pvy[31]}},pvy})<<<(16-VELOCITY_FRAC_BITS)));
      world_ax_store<=keep64($signed(pax)*65536);world_ay_store<=keep64($signed(pay)*65536);dt<=pdt;angle_store<=keep64($signed(pyaw)*64'sd183);
      state<=43;
     end
     // 水平期望速度由归一化摇杆乘随高度限制的速度上限，后续在航向对齐机体坐标内运算。
     43:calc($signed(pending_nx),horizontal_speed_limit_q16,65536,44);
     44:begin sx_store<=keep64(value);calc($signed(pending_ny),horizontal_speed_limit_q16,65536,45);end
     45:begin sy_store<=keep64(value);world_sx_store<=0;world_sy_store<=0;calc($signed({1'b0,dt})*314,65536,10000000+dt*314,1);end
     1:begin alpha_store<=keep64(value);trig_start<=1;state<=30;end
     2:begin afx_store<=keep64(afx+value);calc(hy-afy,alpha,65536,3);end
     3:begin afy_store<=keep64(afy+value);calc(afx,3,100,4);end
     4:begin ex_store<=keep64(fixx-value);calc(afy,3,100,5);end
     5:begin ey_store<=keep64(fixy-value);calc(clip(fixx,-32768000,32768000),$signed({1'b0,dt}),1000000,6);end
     // 保留源误差与 dt 定义：误差限幅 ±500 mm/s，I 项限幅 ±1000 百分之一度。
     // 内部增益=公开增益×10=线值/1000；I=0 时清除积分累积。
     // XY 积分误差限幅为 ±500 mm/s，积分项限幅为 ±1000 百分之一度；I=0 时清积累。
     6:calc(value,$signed({1'b0,work_i}),1000,64);
     64:begin ix_store<=keep64(taking_off && work_i!=0 ?clip(ix+value,-65536000,65536000):0);calc(clip(fixy,-32768000,32768000),$signed({1'b0,dt}),1000000,7);end
     7:calc(value,$signed({1'b0,work_i}),1000,65);
     65:begin iy_store<=keep64(taking_off && work_i!=0 ?clip(iy+value,-65536000,65536000):0);calc(ex,$signed({1'b0,work_p}),1000,8);end
     8:begin ux_store<=keep64(value+ix);calc(ey,$signed({1'b0,work_p}),1000,9);end
     9:begin uy_store<=keep64(value+iy);calc(sx,1,5,10);end
     10:begin ux_store<=keep64(ux+value);calc(sy,1,5,11);end
     11:begin uy_store<=keep64(uy+value);state<=17;end
     17:begin
      // 源坐标 Y 向左时横滚=-Y；本项目改为 Y 向右，因此横滚=+Y。
      publish_roll<=integer_q16(uy);publish_pitch<=integer_q16(-ux);state<=46;
     end
     // XY 命令完整算完才发布；最终姿态限幅由 MAX_ANGLE 指定，默认 ±25 度。
     46:begin
      roll_target<=clip(publish_roll,-MAX_ANGLE,MAX_ANGLE);
      pitch_target<=clip(publish_pitch,-MAX_ANGLE,MAX_ANGLE);
      command_age<=0;command_seen<=1;reason<=0;state<=0;work_xy<=0;
     end
     // 源 OF 的 PI 与 5 Hz 加速度低通均在航向对齐的机体
     // HXYZ 坐标内运算；先旋转再滤波/积分，避免航向变化时
     // 将旧积分和滤波状态错误地带入新轴向。
     30:if(trig_done) calc(-sample_vx,cs,65536,35);
     31:begin rot_tmp_store<=keep64(value);calc(world_sy,sn,65536,32);end
     32:begin sx_store<=keep64(rot_tmp+value);calc(world_sx,sn,65536,33);end
     33:begin rot_tmp_store<=keep64(value);calc(world_sy,cs,65536,34);end
     34:begin sy_store<=keep64(-rot_tmp+value);calc(world_sx-sample_vx,cs,65536,35);end
     35:begin rot_tmp_store<=keep64(value);calc(world_sy-sample_vy,sn,65536,36);end
     36:begin fixx_store<=keep64(rot_tmp+value+sx);calc(world_sx-sample_vx,sn,65536,37);end
     37:begin rot_tmp_store<=keep64(value);calc(world_sy-sample_vy,cs,65536,38);end
     38:begin fixy_store<=keep64(-rot_tmp+value+sy);calc(world_ax,cs,65536,39);end
     39:begin rot_tmp_store<=keep64(value);calc(world_ay,sn,65536,40);end
     40:begin hx_store<=keep64(rot_tmp+value);calc(world_ax,sn,65536,41);end
     41:begin rot_tmp_store<=keep64(value);calc(world_ay,cs,65536,42);end
     42:begin hy_store<=keep64(-rot_tmp+value);calc(hx-afx,alpha,65536,2);end
     // Alt1、Alt2 仍依次按 11 ms 运行；speed_z_tick 为已完成的 1 ms 摇杆状态。
     20:begin afz_store<=keep64(afz+value);calc(afz+value,1,20,21);end
     21:begin exz_store<=keep64(vsz-sample_vx-value);calc(inner_alt_speed,3,5,53);end
     53:begin
      iz_lower_q<=-(64'sd131072000-bias);iz_upper_q<=64'sd131072000-bias;
      exz_store<=keep64(exz+value);calc(clip(exz+value,-65536000,65536000),11,10000,22);
     end
     // 先保存候选 Z 积分及变化方向，偏置和比例项完成后再做最终饱和判断。
     22:begin
      iz_lower_q<=keep64(taking_off ?clip(z_shared_sum,iz_lower_q,iz_upper_q):0);
      // 从复位开始，条件积分保证 I 保持在 [-350,850] 电机单位内。
      // 单步绝对值不超过 72090 Q16；原积分上下界至少为 ±1650 单位，
      // 因此限幅不会改变本步方向。taking_off 为假时以零作为候选，
      // 再按旧 I 的符号判断候选零相对旧 I 的变化方向。
      candidate_i_up<=taking_off ?value>0:iz<0;
      candidate_i_down<=taking_off ?value<0:iz>0;
      calc(22937600-bias,6908,106908,23);
     end
     // 按源算法 1 Hz 系数将偏置趋近 THR_START35，不捕获摇杆 PWM 作为偏置。
     23:begin bias_store<=keep64(taking_off ?z_shared_sum:0);calc(exz,1,5,24);end
     // 把候选值检查与加法拆成不同拍，限制 50 MHz 下的组合路径长度。
     // 每次 11 ms 回调只增加 2 拍；实时屏蔽条件仍可取消计算。
     24:begin exz_store<=keep64(z_shared_sum);state<=66;end
     66:begin
      inner_alt_speed<={{33{compact_candidate_sum31[30]}},compact_candidate_sum31};
      sample_vx_store<=keep64(p_bias+iz);
      // 变化方向已在状态 22 随积分步骤一同锁存。
      state<=67;
     end
     // 仅此阶段提交选定的 Z 积分和总量；中途取消不会提交部分计算结果。
     67:begin
      iz_store<=keep64(taking_off ?selected_z_i:0);
      collective_q16_store<=keep64(taking_off ?clip(selected_z_collective,0,55705600):0);
      state<=60;
     end
     // Auto_Take_Off_Land_Task 在 Alt1 之后、Alt2 之前执行，周期 11 ms。
     // 自动起飞在每次 11 ms 高度回调更新，目标接近 600 mm、超时或满足摇杆条件后结束。
     60:begin
      if(!taking_off)begin auto_phase<=0;auto_ms<=0;next_auto_speed<=0;end
      else if(auto_phase==0 || auto_phase==1)begin
       auto_ms<=auto_ms+16'd11;auto_phase<=1;
       next_auto_speed<=auto_takeoff_mmps(held_h);
       if(auto_ms+11>=5000 || 64'sd39321600-target_z_q16<64'sd1310720 ||
          (auto_ms+11>2000 && (ch3<=1406 || ch3>=1594)))auto_phase<=2;
      end else begin auto_ms<=0;next_auto_speed<=0;end
      state<=61;
     end
     61:begin
      // C 源码中 _flight_state_st.alt_ctrl_speed_set 为 s16，单位 cm/s。
      auto_speed<=next_auto_speed;
      alt_speed<=taking_off ?quantized_climb_logic_q16+next_auto_speed*32'sd65536:0;
      state<=62;
     end
     62:calc(alt_speed,11,1000,54);
     // 54/58/59 用分段比较完成高度目标限幅；55 以整 cm 高度反馈生成下一周期的垂速目标。
     54:begin
      target_sum_q<=target_z_q16+value;
      target_lo_store<=height_feedback_old-64'sd131072000;
      target_hi_store<=height_feedback_old+64'sd131072000;
      state<=58;
     end
     58:begin
      target_lt_lo_q<={$signed(target_sum_q[63:48])<$signed(target_lo_q[63:48]),
       target_sum_q[47:32]<target_lo_q[47:32],target_sum_q[31:16]<target_lo_q[31:16],target_sum_q[15:0]<target_lo_q[15:0]};
      target_eq_lo_q<={target_sum_q[63:48]==target_lo_q[63:48],target_sum_q[47:32]==target_lo_q[47:32],
       target_sum_q[31:16]==target_lo_q[31:16],target_sum_q[15:0]==target_lo_q[15:0]};
      target_gt_hi_q<={$signed(target_sum_q[63:48])>$signed(target_hi_q[63:48]),
       target_sum_q[47:32]>target_hi_q[47:32],target_sum_q[31:16]>target_hi_q[31:16],target_sum_q[15:0]>target_hi_q[15:0]};
      target_eq_hi_q<={target_sum_q[63:48]==target_hi_q[63:48],target_sum_q[47:32]==target_hi_q[47:32],
       target_sum_q[31:16]==target_hi_q[31:16],target_sum_q[15:0]==target_hi_q[15:0]};
      state<=59;
     end
     // 升降速度积分成高度目标，并限于上一高度反馈 ±2000 mm，约束目标与反馈的差距。
     59:begin
      target_z_q16_store<=keep64(target_below_lo ? target_lo_q:target_above_hi ? target_hi_q:target_sum_q);
      state<=55;
     end
     55:begin
      vsz_store<=keep64(taking_off ?clip(target_z_q16-feedback_height_q16(held_h),-98304000,98304000):0);
      if(!taking_off)target_z_q16_store<=keep64(feedback_height_q16(held_h));
      height_feedback_old_store<=keep64(feedback_height_q16(held_h));publish_height<=integer_q16(target_z_q16);publish_speed<=integer_q16(alt_speed);publish_collective<=integer_q16(collective_q16);state<=57;
     end
     57:begin publish_delta<=1000+publish_collective-$signed({1'b0,base});state<=25;end
     // 总油门为 1000 us 加 0..850 的计算量；增量另相对本次输入油门限幅。
     25:begin
      collective_target_us<=1000+publish_collective;
      throttle_delta<=clip(publish_delta,-MAX_DELTA_US,MAX_DELTA_US);
      height_command_seen<=1;height_command_age<=0;height_reason<=0;requested_climb_mmps<=publish_speed;target_height_mm<=publish_height;state<=0;
     end
     100:if(md)begin num<=product;den<=pending_den;div_start<=1;state<=101;end
     // 除法错误锁存算术故障并阻止活动，解锁关闭或原点重置后才清除该故障。
     101:if(dd)begin
      if(derr)begin blocked<=1;xy_blocked<=1;fault_reason<=512;reason<=512;height_reason<=512;state<=0;end
      else begin value_store<=quotient;state<=return_state;end
     end
     default:state<=0;
    endcase
   end
  end
 end
endmodule
