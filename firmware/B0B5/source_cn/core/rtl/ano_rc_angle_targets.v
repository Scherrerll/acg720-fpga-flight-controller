`timescale 1ns/1ps
// 原 ANO 驾驶员 XY 通路：Flight_State_Task → Loc_1level_Ctrl
// 手动分支 → Att_2level_Ctrl；原 3 Hz 低通系数使用 6.28。
// 已接受样本按真实源 dt 更新滤波；角度及 ATT_STAB 微调在
// 原 6 毫秒外环节拍发布；CH2 的正向在 flight_core 中翻转。
// 原微调积分对象是驾驶员期望值，不是实测姿态误差。
// 本文件提供完整遥控角度通路及其开方子模块；当前 flight_core 使用共享摇杆的 ano_manual_angles 实例。
// ch1/ch2 为微秒，角度为百分之一度，dt/outer_dt 以 clk 拍计；滤波摇杆为 Q24，角度和微调为 Q16。
// 默认 50 MHz、最大样本间隔 3000000 拍（60 毫秒）、单次运算上限 2500 拍；合法覆盖范围由 initial 检查。
module ano_rc_angle_targets #(
    parameter integer CLK_HZ=50000000,
    parameter integer MAX_DT_TICKS=3000000,
    parameter integer MAX_COMPUTE_TICKS=2500
)(
    input wire clk,rst_n,sample_update,outer_update,enabled,att_stab,
    input wire [31:0] dt_ticks,outer_dt_ticks,
    input wire [15:0] ch1,ch2,
    input wire signed [15:0] roll_cdeg,pitch_cdeg,
    output wire signed [15:0] manual_roll_cdeg,manual_pitch_cdeg,
    output reg signed [15:0] snapshot_roll_cdeg=0,
    output reg signed [15:0] snapshot_pitch_cdeg=0,
    output reg update=0,
    output wire busy,
    output reg [7:0] fault=0
);
    localparam IDLE=0,ALPHA_MUL=1,ALPHA_DIV=2,ALPHA_DONE=3,
      R_INPUT_MUL=4,R_INPUT_DIV=5,R_FILTER_MUL=6,R_FILTER_DIV=7,R_FILTER_DONE=8,
      P_INPUT_MUL=9,P_INPUT_DIV=10,P_FILTER_MUL=11,P_FILTER_DIV=12,P_FILTER_DONE=13,
      R_SQUARE=14,R_SQUARE_DONE=15,P_SQUARE=16,P_SQUARE_DONE=17,
      ROOT_START=18,ROOT_WAIT=19,LIMIT_DECIDE=20,R_LIMIT_MUL=21,R_LIMIT_DIV=22,
      R_LIMIT_DONE=23,P_LIMIT_MUL=24,P_LIMIT_DIV=25,P_LIMIT_DONE=26,
      R_ANGLE_MUL=27,R_ANGLE_DONE=28,P_ANGLE_MUL=29,P_ANGLE_DONE=30,
      R_TRIM=31,R_TRIM_DIV=32,R_TRIM_DONE=33,P_TRIM=34,P_TRIM_DIV=35,P_TRIM_DONE=36,
      PUBLISH=37,MUL_WAIT=38,DIV_WAIT=39;
    localparam signed [63:0] ONE_Q24=64'sd16777216;
    localparam signed [63:0] TRIM_LIMIT=64'sd100*65536;
    localparam signed [63:0] TRIM_WINDOW=64'sd500*65536;
    localparam signed [63:0] ANGLE_LIMIT=64'sd2500*65536;
    reg [5:0] state=IDLE,resume_state=IDLE;
    reg outer_pending=0,outer_work=0,pending_att_stab=0;
    // 停用时捕获的外环回调可能在重新使能之后才完成，其微调状态
    // 仍可提交，但只有在使能期间捕获、且中途从未停用的回调
    // 才能发布目标角度和反馈快照。
    reg outer_publish_allowed=0;
    reg [31:0] held_dt=0,held_outer_dt=0,compute_age=0;
    reg signed [15:0] held_roll_cdeg=0,held_pitch_cdeg=0;
    reg signed [10:0] held_dead_roll=0,held_dead_pitch=0;
    reg signed [24:0] filtered_roll=0,filtered_pitch=0;
    reg signed [24:0] new_filtered_roll=0;
    reg signed [24:0] limited_roll=0,limited_pitch=0;
    reg [24:0] length_q24=0;
    reg signed [24:0] alpha_q24=0;
    reg [49:0] square_roll=0,square_sum=0;
    reg signed [28:0] angle_roll_q16=0,angle_pitch_q16=0;
    reg signed [23:0] trim_roll_q16=0,trim_pitch_q16=0;
    reg signed [23:0] next_trim_roll=0,next_trim_pitch=0;
    reg signed [15:0] published_roll=0,published_pitch=0;
    reg mul_start=0,div_start=0,root_start=0;
    reg signed [63:0] mul_a=0,div_numerator=0,result=0;
    reg signed [31:0] mul_b=0;
    reg [63:0] div_denominator=1;
    wire mul_done,div_done,root_done;
    wire signed [63:0] product,quotient;
    wire [24:0] root_result;
    assign busy=state!=IDLE || outer_pending;
    // 这里只对数值输出进行门控；实际电机通路仍须使用 flight_core 中
    // 独立的实时遥控、SWA、姿态和 PWM 许可门控。
    assign manual_roll_cdeg=enabled && fault==0 ? published_roll:16'sd0;
    assign manual_pitch_cdeg=enabled && fault==0 ? published_pitch:16'sd0;
    ano_multiply_signed64_32 multiplier(.clk(clk),.rst_n(rst_n),
      .cancel(fault!=0),.start(mul_start),.a(mul_a),.b(mul_b),
      .busy(),.done(mul_done),.result(product));
    pid_divide_signed64 #(.DIVISOR_BITS(32)) divider(.clk(clk),
      .rst_n(rst_n && fault==0),.start(div_start),.numerator(div_numerator),
      .denominator(div_denominator),.busy(),.done(div_done),.quotient(quotient));
    ano_rc_sqrt50 root(.clk(clk),.rst_n(rst_n),.start(root_start),.cancel(fault!=0),
      .radicand(square_sum),.busy(),.done(root_done),.result(root_result));
    initial begin
        if(CLK_HZ!=50000000 || MAX_DT_TICKS<1 || MAX_DT_TICKS>3000000 ||
           MAX_COMPUTE_TICKS<1800 || MAX_COMPUTE_TICKS>10000)
            $error("Unsupported source ANO RC bounds");
    end
    // 输入先限于 1000..2000 微秒，再以 1500 微秒为中心去除 ±50 微秒死区。
    function signed [10:0] channel_dead;
        input [15:0] channel;
        reg signed [11:0] deviation;
        begin
            deviation=channel<=1000 ? -12'sd500 : channel>=2000 ? 12'sd500 :
              $signed({1'b0,channel[10:0]})-12'sd1500;
            channel_dead=deviation>50 ? deviation-50 : deviation< -50 ? deviation+50:0;
        end
    endfunction
    function signed [63:0] clipped;
        input signed [63:0] value,limit;
        begin clipped=value>limit ? limit:value< -limit ? -limit:value;end
    endfunction
    function signed [15:0] integer_angle;
        input signed [63:0] value;
        reg signed [63:0] bounded;
        begin
            bounded=clipped(value,ANGLE_LIMIT);
            // 保持本工程转换为整数百分之一度时向零截断的规则。
            integer_angle=bounded<0 ? -((-bounded)>>>16) : bounded>>>16;
        end
    endfunction
    function signed [63:0] q24_to_q16;
        input signed [63:0] value;
        begin q24_to_q16=value<0 ? -((-value+128)>>>8) : (value+128)>>>8;end
    endfunction
    task multiply_then;
        input signed [63:0] a;
        input signed [31:0] b;
        input [5:0] destination;
        begin mul_a<=a;mul_b<=b;mul_start<=1;resume_state<=destination;state<=MUL_WAIT;end
    endtask
    task divide_then;
        input signed [63:0] numerator;
        input [63:0] denominator;
        input [5:0] destination;
        begin div_numerator<=numerator;div_denominator<=denominator;
          div_start<=1;resume_state<=destination;state<=DIV_WAIT;end
    endtask
    task clear_all;
        begin
            state<=IDLE;outer_pending<=0;outer_work<=0;outer_publish_allowed<=0;compute_age<=0;
            filtered_roll<=0;filtered_pitch<=0;trim_roll_q16<=0;trim_pitch_q16<=0;
            published_roll<=0;published_pitch<=0;snapshot_roll_cdeg<=0;snapshot_pitch_cdeg<=0;
        end
    endtask
    always @(posedge clk or negedge rst_n) begin
        // 高云综合要求所有异步复位赋值均放在复位分支内；
        // 在分支前无条件清除脉冲会造成复位语义不明确。
        // 高云综合约束：异步复位寄存器的清零赋值必须置于复位分支，故脉冲清零放在正常分支。
        if(!rst_n) begin
            clear_all();fault<=0;update<=0;mul_start<=0;div_start<=0;root_start<=0;
            resume_state<=IDLE;pending_att_stab<=0;held_dt<=0;held_outer_dt<=0;
            held_roll_cdeg<=0;held_pitch_cdeg<=0;held_dead_roll<=0;held_dead_pitch<=0;
            new_filtered_roll<=0;limited_roll<=0;limited_pitch<=0;length_q24<=0;
            alpha_q24<=0;square_roll<=0;square_sum<=0;
            angle_roll_q16<=0;angle_pitch_q16<=0;next_trim_roll<=0;next_trim_pitch<=0;
            mul_a<=0;mul_b<=0;div_numerator<=0;result<=0;div_denominator<=1;
        end else begin
        update<=0;mul_start<=0;div_start<=0;root_start<=0;
        if(fault!=0) begin
            clear_all();
            if(!enabled) fault<=0;
        // 样本/外环重入、非法 dt 或运算超时均清空事务并锁存故障；停用后允许清故障。
        end else if(sample_update && (state!=IDLE || dt_ticks==0 || dt_ticks>MAX_DT_TICKS)) begin
            clear_all();fault<=state!=IDLE ? 8'h02:8'h01;
        end else if(outer_update && (outer_pending || outer_work || outer_dt_ticks==0 || outer_dt_ticks>MAX_DT_TICKS)) begin
            clear_all();fault<=outer_pending || outer_work ? 8'h02:8'h01;
        end else if(state!=IDLE && compute_age>=MAX_COMPUTE_TICKS) begin
            clear_all();fault<=8'h04;
        end else begin
            // 停用时继续跟踪滤波和微调状态；重新使能后必须等待下一次完整
            // 外环发布，才能公开新目标，避免暴露旧目标。
            if(!enabled) begin
                published_roll<=0;published_pitch<=0;outer_publish_allowed<=0;
                snapshot_roll_cdeg<=0;snapshot_pitch_cdeg<=0;
            end
            if(state!=IDLE) compute_age<=compute_age+1'b1;
            if(outer_update) begin
                outer_pending<=1;held_outer_dt<=outer_dt_ticks;pending_att_stab<=att_stab;outer_publish_allowed<=enabled;
                held_roll_cdeg<=roll_cdeg;held_pitch_cdeg<=pitch_cdeg;
            end
            case(state)
              IDLE:begin
                compute_age<=0;
                // 同拍到达时，原 Loop_Task_0 先于 Loop_Task_2，因此样本处理优先。
                if(sample_update) begin
                    held_dt<=dt_ticks;held_dead_roll<=channel_dead(ch1);held_dead_pitch<=channel_dead(ch2);
                    state<=ALPHA_MUL;
                end else if(outer_pending) begin
                    outer_pending<=0;outer_work<=1;limited_roll<=filtered_roll;limited_pitch<=filtered_pitch;
                    state<=R_SQUARE;
                end
              end
              ALPHA_MUL:multiply_then(held_dt,32'sd471,ALPHA_DIV);
              ALPHA_DIV:divide_then(result<<<24,25*CLK_HZ+result[31:0],ALPHA_DONE);
              // 低通系数 alpha=3×6.28×dt/(1+3×6.28×dt)=471×ticks/(25×CLK_HZ+471×ticks)。
              ALPHA_DONE:begin alpha_q24<=result[24:0];state<=R_INPUT_MUL;end
              // 0.0022=11/5000，保持与原程序完全相同的输入系数。
              R_INPUT_MUL:multiply_then(held_dead_roll,32'sd184549376,R_INPUT_DIV);
              R_INPUT_DIV:divide_then(result,64'd5000,R_FILTER_MUL);
              R_FILTER_MUL:multiply_then(result-$signed(filtered_roll),alpha_q24,R_FILTER_DIV);
              R_FILTER_DIV:divide_then(result,64'd16777216,R_FILTER_DONE);
              R_FILTER_DONE:begin new_filtered_roll<=$signed(filtered_roll)+result;state<=P_INPUT_MUL;end
              P_INPUT_MUL:multiply_then(held_dead_pitch,32'sd184549376,P_INPUT_DIV);
              P_INPUT_DIV:divide_then(result,64'd5000,P_FILTER_MUL);
              P_FILTER_MUL:multiply_then(result-$signed(filtered_pitch),alpha_q24,P_FILTER_DIV);
              P_FILTER_DIV:divide_then(result,64'd16777216,P_FILTER_DONE);
              P_FILTER_DONE:begin
                filtered_roll<=new_filtered_roll;filtered_pitch<=$signed(filtered_pitch)+result;
                state<=IDLE;
              end
              // 外环先求滤波摇杆二维长度，超过单位圆时归一化，再映射为 ±25 度目标。
              R_SQUARE:multiply_then(limited_roll,limited_roll,R_SQUARE_DONE);
              R_SQUARE_DONE:begin square_roll<=result[49:0];state<=P_SQUARE;end
              P_SQUARE:multiply_then(limited_pitch,limited_pitch,P_SQUARE_DONE);
              P_SQUARE_DONE:begin square_sum<=square_roll+result[49:0];state<=ROOT_START;end
              ROOT_START:begin root_start<=1;state<=ROOT_WAIT;end
              ROOT_WAIT:if(root_done) begin length_q24<=root_result;state<=LIMIT_DECIDE;end
              LIMIT_DECIDE:state<=length_q24>ONE_Q24 ? R_LIMIT_MUL:R_ANGLE_MUL;
              R_LIMIT_MUL:multiply_then(limited_roll,32'sd16777216,R_LIMIT_DIV);
              R_LIMIT_DIV:divide_then(result,{39'd0,length_q24},R_LIMIT_DONE);
              R_LIMIT_DONE:begin limited_roll<=result[24:0];state<=P_LIMIT_MUL;end
              P_LIMIT_MUL:multiply_then(limited_pitch,32'sd16777216,P_LIMIT_DIV);
              P_LIMIT_DIV:divide_then(result,{39'd0,length_q24},P_LIMIT_DONE);
              P_LIMIT_DONE:begin limited_pitch<=result[24:0];state<=R_ANGLE_MUL;end
              R_ANGLE_MUL:multiply_then(limited_roll,32'sd2500,R_ANGLE_DONE);
              R_ANGLE_DONE:begin angle_roll_q16<=q24_to_q16(result);state<=P_ANGLE_MUL;end
              P_ANGLE_MUL:multiply_then(limited_pitch,32'sd2500,P_ANGLE_DONE);
              P_ANGLE_DONE:begin angle_pitch_q16<=q24_to_q16(result);state<=R_TRIM;end
              // ATT_STAB 仅在目标加微调位于 ±5 度窗口内积分，微调限制为 ±1 度。
              R_TRIM:begin
                if(!pending_att_stab) begin next_trim_roll<=0;state<=P_TRIM;end
                else if($signed(angle_roll_q16)+$signed(trim_roll_q16)<TRIM_WINDOW &&
                        $signed(angle_roll_q16)+$signed(trim_roll_q16)>-TRIM_WINDOW)
                    multiply_then(angle_roll_q16,$signed(held_outer_dt),R_TRIM_DIV);
                else begin next_trim_roll<=trim_roll_q16;state<=P_TRIM;end
              end
              R_TRIM_DIV:divide_then(result,5*CLK_HZ,R_TRIM_DONE);
              R_TRIM_DONE:begin next_trim_roll<=clipped($signed(trim_roll_q16)+result,TRIM_LIMIT);state<=P_TRIM;end
              P_TRIM:begin
                if(!pending_att_stab) begin next_trim_pitch<=0;state<=PUBLISH;end
                else if($signed(angle_pitch_q16)+$signed(trim_pitch_q16)<TRIM_WINDOW &&
                        $signed(angle_pitch_q16)+$signed(trim_pitch_q16)>-TRIM_WINDOW)
                    multiply_then(angle_pitch_q16,$signed(held_outer_dt),P_TRIM_DIV);
                else begin next_trim_pitch<=trim_pitch_q16;state<=PUBLISH;end
              end
              P_TRIM_DIV:divide_then(result,5*CLK_HZ,P_TRIM_DONE);
              P_TRIM_DONE:begin next_trim_pitch<=clipped($signed(trim_pitch_q16)+result,TRIM_LIMIT);state<=PUBLISH;end
              // 两轴目标和同一外环反馈快照原子提交；停用或中途停用过的事务只更新内部微调。
              PUBLISH:begin
                trim_roll_q16<=next_trim_roll;trim_pitch_q16<=next_trim_pitch;
                published_roll<=enabled && outer_publish_allowed ? integer_angle($signed(angle_roll_q16)+$signed(next_trim_roll)):16'sd0;
                published_pitch<=enabled && outer_publish_allowed ? integer_angle($signed(angle_pitch_q16)+$signed(next_trim_pitch)):16'sd0;
                snapshot_roll_cdeg<=enabled && outer_publish_allowed ? held_roll_cdeg:16'sd0;
                snapshot_pitch_cdeg<=enabled && outer_publish_allowed ? held_pitch_cdeg:16'sd0;
                update<=enabled && outer_publish_allowed;outer_publish_allowed<=0;outer_work<=0;state<=IDLE;
              end
              MUL_WAIT:if(mul_done)begin result<=product;state<=resume_state;end
              DIV_WAIT:if(div_done)begin result<=quotient;state<=resume_state;end
              default:begin clear_all();fault<=8'h08;end
            endcase
        end
        end
    end
endmodule

// 50 位无符号整数开方器，固定 25 次恢复迭代；减法通路为 27 位，
// 避免在目标角度发布路径中形成大型组合开方/除法链。
// start 只在空闲时锁存无符号被开方数，result 为向下取整平方根；cancel/复位中止事务，done 仅一拍。
module ano_rc_sqrt50(input wire clk,rst_n,start,cancel,
    input wire [49:0] radicand,output reg busy=0,output reg done=0,
    output reg [24:0] result=0);
    reg [49:0] bits=0;reg [26:0] remainder=0;reg [24:0] root_value=0;
    reg [4:0] left=0;
    wire [26:0] trial={remainder[24:0],bits[49:48]};
    wire [26:0] subtraction={root_value,2'b01};
    wire pass=trial>=subtraction;
    always @(posedge clk)begin
        done<=0;
        if(!rst_n || cancel)begin busy<=0;left<=0;result<=0;end
        else if(start && !busy)begin bits<=radicand;remainder<=0;root_value<=0;left<=25;busy<=1;end
        // 每次移入两位被开方数，以试减结果产生一位根；25 步后直接提交最后一位。
        else if(busy)begin
            remainder<=pass ? trial-subtraction:trial;
            root_value<={root_value[23:0],pass};bits<=bits<<2;left<=left-1'b1;
            if(left==1)begin result<={root_value[23:0],pass};busy<=0;done<=1;end
        end
    end
endmodule
