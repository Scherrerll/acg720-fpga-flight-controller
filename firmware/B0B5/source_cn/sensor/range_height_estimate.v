`timescale 1ns/1ps
// 独立的激光测距/姿态几何适配层，保持 ANO 控制增益不变。
// 以 h=距离(mm)×cos(横滚)×cos(俯仰) 计算垂直高度，并在多周期计算完成后一致提交。
// clk 仅支持 50 MHz，rst_n 为低有效同步复位；pose_update 启动一次观测，busy 期间不得重入。
// roll/pitch 为 0.01 度，限 ±45 度；distance_cm 为厘米，限 1..500 cm，height_mm 输出为毫米。
// range_age/RANGE_AGE_LIMIT/MAX_COMPUTE_TICKS 单位为时钟拍；测距自己的龄门控一直生效，
// 姿态更新不能刷新激光测距龄。update 仅在高度提交时脉冲一拍。
// estimate_ready 为计算结果可用；height_valid 还要求 CAL_MASK[3]/[4] 的标定资格。
module range_height_estimate #(
    parameter integer CLK_HZ=50000000,
    parameter [7:0] CAL_MASK=0,
    parameter integer RANGE_AGE_LIMIT=5000000,
    parameter integer MAX_COMPUTE_TICKS=512
)(
    input wire clk,rst_n,pose_update,pose_valid,
    input wire signed [15:0] roll,pitch,
    input wire range_link,
    input wire [15:0] distance_cm,
    input wire [31:0] range_age,
    output reg signed [31:0] height_mm=0,
    output wire estimate_ready,height_valid,
    output reg qualified_ready=0,
    output reg update=0,
    output wire busy,
    output wire [15:0] reason
);
    // 依次换算横滚/俯仰为弧度 Q20、求 Q16 余弦、完成两次乘法并舍入毫米高度。
    // MUL_WAIT 复用单一乘法器，resume_state 保存乘积应返回的状态。
    localparam IDLE=0,ROLL_MUL=1,ROLL_ANGLE=2,ROLL_TRIG=3,
      PITCH_MUL=4,PITCH_ANGLE=5,PITCH_TRIG=6,DISTANCE_MUL=7,
      SECOND_COS=8,ROUND=9,COMMIT=10,MUL_WAIT=11;
    reg [3:0] state=IDLE,resume_state=IDLE;
    reg seen=0,transaction_epoch_ok=0;
    reg [7:0] fault=0;
    reg [31:0] compute_age=0;
    reg signed [15:0] held_roll=0,held_pitch=0;
    reg [15:0] held_distance=0;
    reg signed [17:0] roll_cos=65536,pitch_cos=65536;
    reg signed [31:0] trig_angle=0,pending_height=0;
    reg mul_start=0,trig_start=0;
    reg signed [63:0] mul_a=0,mul_b=0,result=0;
    wire md,mbusy,td,tbusy;
    wire signed [63:0] product;
    wire signed [17:0] sn,cs;
    wire pose_ok=pose_valid &&
      roll>= -4500 && roll<=4500 && pitch>= -4500 && pitch<=4500;
    wire range_ok=range_link && range_age<RANGE_AGE_LIMIT && distance_cm>0 && distance_cm<=500;
    wire sources_ok=pose_ok && range_ok;
    wire overlap=pose_update && state!=IDLE;
    wire cancel=!sources_ok || fault!=0 || overlap;
    assign busy=state!=IDLE;
    assign estimate_ready=sources_ok && seen && fault==0;
    assign height_valid=CAL_MASK[3] && CAL_MASK[4] && estimate_ready;
    // qualified_ready 将处理资格寄存一拍，构成真实时钟边界；下游须同时组合自己的
    // 实时传输/看门狗门控。estimate_ready/height_valid 保持组合即时资格语义。
    always @(posedge clk) if(!rst_n) qualified_ready<=0;else qualified_ready<=estimate_ready;
    // reason 按优先级选择单一原因：姿态 2、测距 4、内部故障、未见结果 1、标定不足 32。
    // fault=0x08 表示重入，0x10 表示超时/范围/非法状态；源失效或复位后才能清除。
    assign reason=!pose_ok ? 16'd2 : !range_ok ? 16'd4 : fault!=0 ? {8'd0,fault} :
      !seen ? 16'd1 : !(CAL_MASK[3] && CAL_MASK[4]) ? 16'd32 : 16'd0;
    position_multiply m(.clk(clk),.rst_n(rst_n),.start(mul_start),.cancel(cancel),
      .a(mul_a),.b(mul_b),.busy(mbusy),.done(md),.result(product));
    position_sincos trig(.clk(clk),.rst_n(rst_n),.start(trig_start),.cancel(cancel),
      .angle_q20(trig_angle),.busy(tbusy),.done(td),.sin_q16(sn),.cos_q16(cs));
    // 有符号右移按向零截断，供百分之一度到弧度 Q20 的定点换算使用。
    function signed [63:0] trunc_shift;
        input signed [63:0] value;
        input integer bits;
        begin trunc_shift=value<0 ? -((-value)>>>bits) : value>>>bits;end
    endfunction
    task multiply_then;
        input signed [63:0] a,b;
        input [3:0] destination;
        begin mul_a<=a;mul_b<=b;mul_start<=1;resume_state<=destination;state<=MUL_WAIT;end
    endtask
    // 任一源失效立即撤销本次事务及旧结果；transaction_epoch_ok 防止跨源失效提交。
    task clear_estimate;
        begin state<=IDLE;seen<=0;transaction_epoch_ok<=0;compute_age<=0;height_mm<=0;end
    endtask
    initial begin
        if(CLK_HZ!=50000000 || RANGE_AGE_LIMIT<1 ||
           MAX_COMPUTE_TICKS<400 || MAX_COMPUTE_TICKS>65535)
            $error("Unsupported range-height geometry bounds");
    end
    // 先处理复位/源失效/锁存故障/重入/运算超时，再推进状态，避免提交混合历元高度。
    always @(posedge clk) begin
        update<=0;mul_start<=0;trig_start<=0;
        if(!rst_n) begin clear_estimate();fault<=0;end
        else if(!sources_ok) begin clear_estimate();fault<=0;end
        else if(fault!=0) clear_estimate();
        else if(overlap) begin clear_estimate();fault<=8'h08;end
        else if(state!=IDLE && compute_age>=MAX_COMPUTE_TICKS) begin clear_estimate();fault<=8'h10;end
        else begin
            if(state!=IDLE) compute_age<=compute_age+1'b1;
            case(state)
              IDLE:if(pose_update) begin held_roll<=roll;held_pitch<=pitch;held_distance<=distance_cm;transaction_epoch_ok<=sources_ok;
                  compute_age<=0;state<=ROLL_MUL;end
              // 11993813/65536 将 0.01 度输入缩放为弧度 Q20，再调用三角单元。
              ROLL_MUL:multiply_then(held_roll,64'sd11993813,ROLL_ANGLE);
              ROLL_ANGLE:begin trig_angle<=trunc_shift(result,16);trig_start<=1;state<=ROLL_TRIG;end
              ROLL_TRIG:if(td) begin roll_cos<=cs;state<=PITCH_MUL;end
              PITCH_MUL:multiply_then(held_pitch,64'sd11993813,PITCH_ANGLE);
              PITCH_ANGLE:begin trig_angle<=trunc_shift(result,16);trig_start<=1;state<=PITCH_TRIG;end
              PITCH_TRIG:if(td) begin pitch_cos<=cs;state<=DISTANCE_MUL;end
              // 厘米先乘 10 变为毫米，连续乘两个 Q16 余弦，最终加半单位并右移 32 位。
              DISTANCE_MUL:multiply_then($signed({1'b0,held_distance})*64'sd10,roll_cos,SECOND_COS);
              SECOND_COS:multiply_then(result,pitch_cos,ROUND);
              ROUND:begin
                  pending_height<=(result+64'sd2147483648)>>>32;
                  state<=COMMIT;
              end
              // 提交前再次核对实时源与锁存输入/结果范围，全部通过才置 seen 和 update。
              COMMIT:begin
                  if(!sources_ok || !transaction_epoch_ok || held_roll< -4500 || held_roll>4500 || held_pitch< -4500 || held_pitch>4500 || held_distance==0 || held_distance>500 || pending_height<0 || pending_height>5000) begin clear_estimate();fault<=8'h10;end
                  else begin height_mm<=pending_height;seen<=1;transaction_epoch_ok<=0;update<=1;state<=IDLE;end
              end
              MUL_WAIT:if(md) begin result<=product;state<=resume_state;end
              default:begin clear_estimate();fault<=8'h10;end
            endcase
        end
    end
endmodule
