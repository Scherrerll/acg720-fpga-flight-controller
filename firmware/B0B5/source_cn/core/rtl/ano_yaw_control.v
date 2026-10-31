`timescale 1ns/1ps
// ANO Att_2level_Ctrl 的相对偏航飞行分支及角度 PID_calculate。
// 保留原反馈赋值顺序：误差使用上一次外环的偏航反馈，
// 随后才保存本事务四元数偏航，作为下一次反馈。
// 原偏航角度参数为 P=5、kd_ex=0.5、kd_fb=0.5；PID 反馈为零，故只有 kd_ex 起作用。
// 相对偏航由陀螺四元数得到，不构造磁力计或绝对航向约束。
// 角度、航向误差为百分之一度；摇杆和目标角速度为百分之一度/秒；dt_ticks 以 clk 周期计。
// 默认主频 50 MHz、最大 dt 为 60 毫秒、运算期限 512 拍；摇杆最大 ±200 度/秒。
// 默认每次回调最多变化 30 度/秒（固定每更新量，并非每秒加速度）；参数覆盖须满足 initial 中限制。
module ano_yaw_control #(
    parameter integer CLK_HZ=50000000,
    parameter integer MAX_DT_TICKS=3000000,
    parameter integer MAX_COMPUTE_TICKS=512,
    parameter integer MAX_STICK_RATE_CDEG_S=20000,
    parameter integer SLEW_CDEG_S_PER_UPDATE=3000
)(
    input wire clk,rst_n,sample_update,enabled,yaw_valid,
    input wire [31:0] dt_ticks,
    input wire signed [15:0] yaw_cdeg,
    input wire signed [31:0] stick_yaw_rate_cdeg_s,
    output reg update=0,
    output wire busy,
    output reg signed [31:0] target_yaw_rate_cdeg_s=0,
    output reg signed [15:0] heading_target_cdeg=0,
    output reg signed [15:0] yaw_error_cdeg=0,
    output reg signed [31:0] slewed_rate_cdeg_s=0,
    output reg [7:0] fault=0
);
    localparam IDLE=0,CLIP_COMMAND=1,ERROR_INHIBIT=2,SLEW=3,
      INCREMENT_TIME=4,INCREMENT_Q16=5,INCREMENT_DIV=6,INTEGRATE=7,
      WRAP_TARGET=8,ERROR=9,WRAP_ERROR=10,P_TERM=11,D_DELTA=12,
      D_TIME=13,D_DIV=14,SUM=15,ROUND=16,PUBLISH=17,
      MUL_WAIT=18,DIV_WAIT=19;
    localparam signed [63:0] HALF_TURN=64'sd18000*65536;
    localparam signed [63:0] FULL_TURN=64'sd36000*65536;
    localparam signed [63:0] ERROR_INHIBIT_LIMIT=64'sd9000*65536;
    reg [4:0] state=IDLE,resume_state=IDLE;
    reg [31:0] held_dt=0,age=0,compute_age=0;
    reg signed [15:0] held_yaw=0;
    reg signed [31:0] held_command=0,command=0,next_slew=0;
    // Q16 百分之一度，保留积分航向的小数部分。
    reg signed [63:0] expected_heading=0,feedback_old=0,error_old=0;
    reg signed [63:0] integrated=0,new_heading=0,new_error=0,p_term=0,d_term=0,result=0;
    reg signed [31:0] pending_rate=0;
    reg mul_start=0,div_start=0;
    reg signed [63:0] mul_a=0,div_numerator=0;
    reg signed [31:0] mul_b=0;
    reg [63:0] div_denominator=1;
    wire md,dd,mbusy,dbusy;
    wire signed [63:0] product,quotient;
    wire overlap=sample_update && state!=IDLE;
    wire usable_yaw=yaw_valid && yaw_cdeg>= -18000 && yaw_cdeg<=18000;
    assign busy=state!=IDLE;
    ano_multiply_signed64_32 multiply(.clk(clk),.rst_n(rst_n),
      .cancel(!enabled || !usable_yaw || fault!=0 || overlap),.start(mul_start),
      .a(mul_a),.b(mul_b),.busy(mbusy),.done(md),.result(product));
    // 偏航支持的分母为 CLK_HZ=50000000 或 2×dt≤6000000，
    // 26 位无符号数可精确表示；分子、商及舍入仍用 64 位，固定延迟仍为 66 拍。
    pid_divide_signed64 #(.DIVISOR_BITS(26)) divide(.clk(clk),
      .rst_n(rst_n && enabled && usable_yaw && fault==0),.start(div_start),
      .numerator(div_numerator),.denominator(div_denominator),.busy(dbusy),.done(dd),.quotient(quotient));
    initial begin
        if(CLK_HZ!=50000000 || MAX_DT_TICKS<1 || MAX_DT_TICKS>3000000 ||
           MAX_COMPUTE_TICKS<400 || MAX_COMPUTE_TICKS>65535 ||
           MAX_STICK_RATE_CDEG_S<1 || MAX_STICK_RATE_CDEG_S>25000 ||
           SLEW_CDEG_S_PER_UPDATE!=3000) $error("Unsupported ANO yaw bounds");
    end
    function signed [63:0] wrap180;
        input signed [63:0] value;
        begin wrap180=value< -HALF_TURN ? value+FULL_TURN : value>HALF_TURN ? value-FULL_TURN : value;end
    endfunction
    function signed [63:0] rounded_q16;
        input signed [63:0] value;
        begin rounded_q16=value<0 ? -((-value+32768)>>>16) : ((value+32768)>>>16);end
    endfunction
    function signed [31:0] clip_command;
        input signed [31:0] value;
        begin clip_command=value>MAX_STICK_RATE_CDEG_S ? MAX_STICK_RATE_CDEG_S :
          value< -MAX_STICK_RATE_CDEG_S ? -MAX_STICK_RATE_CDEG_S : value;end
    endfunction
    task multiply_then;
        input signed [63:0] a;
        input signed [31:0] b;
        input [4:0] destination;
        begin mul_a<=a;mul_b<=b;mul_start<=1;resume_state<=destination;state<=MUL_WAIT;end
    endtask
    task divide_then;
        input signed [63:0] numerator;
        input [63:0] denominator;
        input [4:0] destination;
        begin div_numerator<=numerator;div_denominator<=denominator;
          div_start<=1;resume_state<=destination;state<=DIV_WAIT;end
    endtask
    // 复位、停用或故障时以当前合法偏航重建目标和历史，清除旧角速度命令，避免恢复时追赶旧航向。
    task seed_current_yaw;
        begin
            state<=IDLE;compute_age<=0;target_yaw_rate_cdeg_s<=0;slewed_rate_cdeg_s<=0;
            expected_heading<=usable_yaw ? $signed(yaw_cdeg)*64'sd65536 : 64'sd0;
            feedback_old<=usable_yaw ? $signed(yaw_cdeg)*64'sd65536 : 64'sd0;
            heading_target_cdeg<=usable_yaw ? yaw_cdeg : 16'sd0;
            error_old<=0;yaw_error_cdeg<=0;
        end
    endtask
    always @(posedge clk) begin
        update<=0;mul_start<=0;div_start<=0;
        if(!rst_n || !enabled) begin seed_current_yaw();age<=0;fault<=0;end
        else if(fault!=0) seed_current_yaw();
        else if(!usable_yaw) begin seed_current_yaw();fault<=8'h04;end
        else if(overlap) begin seed_current_yaw();fault<=8'h02;end
        else if(age>=MAX_DT_TICKS) begin seed_current_yaw();fault<=8'h08;end
        else if(state!=IDLE && compute_age>=MAX_COMPUTE_TICKS) begin seed_current_yaw();fault<=8'h10;end
        else begin
            age<=age+1'b1;
            if(state!=IDLE) compute_age<=compute_age+1'b1;
            case(state)
              // 只在空闲时锁存本次偏航、摇杆命令与真实 dt；忙时重入和数据/运算超时均锁存故障。
              IDLE:if(sample_update) begin
                  if(dt_ticks==0 || dt_ticks>MAX_DT_TICKS) begin seed_current_yaw();fault<=8'h01;end
                  else begin held_yaw<=yaw_cdeg;held_dt<=dt_ticks;held_command<=stick_yaw_rate_cdeg_s;
                    age<=0;compute_age<=0;state<=CLIP_COMMAND;end
              end
              CLIP_COMMAND:begin command<=clip_command(held_command);state<=ERROR_INHIBIT;end
              ERROR_INHIBIT:begin
                  // 沿用原程序上一笔 yaw_err，禁止驾驶员输入继续增大
                  // 已经超过 90 度的同向航向误差，同时允许反向输入使其恢复。
                  if((error_old>ERROR_INHIBIT_LIMIT && command>0) ||
                     (error_old< -ERROR_INHIBIT_LIMIT && command<0)) command<=0;
                  state<=SLEW;
              end
              // 对摇杆角速度逐回调限变化率，再按真实 dt 积分相对目标航向。
              SLEW:begin
                  if(command-slewed_rate_cdeg_s>SLEW_CDEG_S_PER_UPDATE) next_slew<=slewed_rate_cdeg_s+SLEW_CDEG_S_PER_UPDATE;
                  else if(command-slewed_rate_cdeg_s< -SLEW_CDEG_S_PER_UPDATE) next_slew<=slewed_rate_cdeg_s-SLEW_CDEG_S_PER_UPDATE;
                  else next_slew<=command;
                  state<=INCREMENT_TIME;
              end
              INCREMENT_TIME:multiply_then(next_slew,$signed(held_dt),INCREMENT_Q16);
              INCREMENT_Q16:multiply_then(result,32'sd65536,INCREMENT_DIV);
              INCREMENT_DIV:divide_then(result,CLK_HZ,INTEGRATE);
              // 目标航向和误差分别回绕到 ±180 度，避免跨越周界时出现接近整周的伪误差。
              INTEGRATE:begin integrated<=expected_heading+result;state<=WRAP_TARGET;end
              WRAP_TARGET:begin new_heading<=wrap180(integrated);state<=ERROR;end
              ERROR:begin new_error<=new_heading-feedback_old;state<=WRAP_ERROR;end
              WRAP_ERROR:begin new_error<=wrap180(new_error);state<=P_TERM;end
              // 先计算比例项，再按误差变化和真实 dt 计算 kd_ex 微分项；最近舍入为整数百分之一度/秒。
              P_TERM:multiply_then(new_error,32'sd5,D_DELTA);
              D_DELTA:begin p_term<=result;result<=new_error-error_old;state<=D_TIME;end
              D_TIME:multiply_then(result,CLK_HZ,D_DIV);
              D_DIV:divide_then(result,$unsigned(held_dt)*64'd2,SUM);
              SUM:begin d_term<=result;result<=p_term+result;state<=ROUND;end
              ROUND:begin
                  if(rounded_q16(result)>3276700 || rounded_q16(result)< -3276700) begin
                      // 此数字范围溢出只会在偏离原程序 6 毫秒工作节奏时发生，
                      // 例如传入极短 dt；此时清事务并锁存故障。
                      seed_current_yaw();fault<=8'h20;
                  end else begin pending_rate<=rounded_q16(result);state<=PUBLISH;end
              end
              // 一次性提交新目标航向、旧反馈历史、误差及角速度输出；update 仅持续一个时钟。
              PUBLISH:begin
                  expected_heading<=new_heading;feedback_old<=$signed(held_yaw)*64'sd65536;
                  error_old<=new_error;slewed_rate_cdeg_s<=next_slew;
                  heading_target_cdeg<=rounded_q16(new_heading);yaw_error_cdeg<=rounded_q16(new_error);
                  target_yaw_rate_cdeg_s<=pending_rate;update<=1;state<=IDLE;
              end
              MUL_WAIT:if(md) begin result<=product;state<=resume_state;end
              DIV_WAIT:if(dd) begin result<=quotient;state<=resume_state;end
              default:begin seed_current_yaw();fault<=8'h40;end
            endcase
        end
    end
endmodule
