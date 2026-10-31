`timescale 1ns/1ps
// 固定中位按约定的驱动接口定义；不能把该常量当作电调测量结果。
// 撤销使能后先完成当前完整脉冲（最长 2ms），再在下一个
// 20ms 帧边界输出中位，禁止在同一帧拼接正反向脉宽。
// 双路水面电调PWM：同一帧边界锁存左右脉宽，并对整对输出执行换向中位等待。
// 默认50个时钟为1us、每帧20000us；按配套驱动协议以1500us作为中位。
module water_pwm_pair #(
    parameter integer TICKS_PER_US=50,
    parameter integer FRAME_US=20000,
    parameter integer REVERSE_NEUTRAL_FRAMES=15
)(
    input wire clk,rst_n,enable,
    input wire [15:0] left_us,right_us,
    output reg left_pwm=0,
    output reg right_pwm=0,
    output reg [15:0] latched_left_us=0,
    output reg [15:0] latched_right_us=0,
    output reg frame_active=0,
    output wire neutral_output
);
    // sub为微秒内分频计数，phase为帧内微秒计数，两路共用同一时间基准。
    localparam integer SUB_BITS=TICKS_PER_US>1?$clog2(TICKS_PER_US):1;
    localparam integer PHASE_BITS=$clog2(FRAME_US);
    reg [SUB_BITS-1:0] sub=0;
    reg [PHASE_BITS-1:0] phase=0;
    // 任意时钟发现使能撤销即记住中断，避免帧内短暂失效后直接沿用旧推力。
    // 中断后的帧边界先输出中位，重新使能也须经过该边界处理。
    reg interrupted=1;
    reg [4:0] neutral_frames=0;
    // 保存各侧最近非零方向；短暂回中位不会立即遗忘原方向。
    reg [1:0] last_left_dir=0,last_right_dir=0;
    // 输入先限制到1000..2000us；小于/大于1500us分别表示两个逻辑方向。
    function [15:0] clamp;
        input [15:0] c;
        begin clamp=c<1000?16'd1000:c>2000?16'd2000:c; end
    endfunction
    function [1:0] direction;
        input [15:0] c;
        begin direction=c<1500?2'd1:c>1500?2'd2:2'd0; end
    endfunction
    wire [15:0] next_left=clamp(left_us),next_right=clamp(right_us);
    wire [1:0] left_dir=direction(next_left),right_dir=direction(next_right);
    // 任意一侧请求反向时，左右整对进入中位等待，避免两侧换向时序不一致。
    wire reversing=(left_dir!=0 && last_left_dir!=0 && left_dir!=last_left_dir) ||
        (right_dir!=0 && last_right_dir!=0 && right_dir!=last_right_dir);
    // 此状态仅表示锁存目标均为1500us，不表示已实测推进器机械停止。
    assign neutral_output=latched_left_us==1500 && latched_right_us==1500;
    // 默认门限为15个完整中位帧；计数结果在后续帧边界用于换向放行。
    wire reverse_ready=neutral_frames>=REVERSE_NEUTRAL_FRAMES;
    // 目标仅在帧结束时更新；帧中撤销许可仍完成当前脉冲，随后使用中位帧。
    // 只有完整结束的双路中位帧才累计等待时间，非中位输出会清零该计数。
    always @(posedge clk) begin
        if(!rst_n) begin
            sub<=0;phase<=0;interrupted<=1;frame_active<=0;
            latched_left_us<=0;latched_right_us<=0;
            neutral_frames<=0;last_left_dir<=0;last_right_dir<=0;
        end else begin
            if(!enable) interrupted<=1;
            if(sub==TICKS_PER_US-1) begin
                sub<=0;
                if(phase==FRAME_US-1) begin
                    phase<=0;
                    // 仅统计已完成的完整中位帧，不把已经过的部分脉冲算作一帧。
                    if(neutral_output) begin
                        if(!reverse_ready) neutral_frames<=neutral_frames+1'b1;
                    end else neutral_frames<=0;
                    if(reverse_ready) begin last_left_dir<=0;last_right_dir<=0;end
                    // 正常使能、没有待处理的中断且换向等待满足时，才锁存新的整对目标。
                    if(enable && !interrupted && (!reversing || reverse_ready)) begin
                        latched_left_us<=next_left;latched_right_us<=next_right;
                        last_left_dir<=left_dir==0 ? (reverse_ready?2'd0:last_left_dir):left_dir;
                        last_right_dir<=right_dir==0 ? (reverse_ready?2'd0:last_right_dir):right_dir;
                        frame_active<=1;
                        if(left_dir!=0 || right_dir!=0) neutral_frames<=0;
                    end else begin
                        latched_left_us<=1500;latched_right_us<=1500;frame_active<=0;
                    end
                    interrupted<=!enable;
                end else phase<=phase+1'b1;
            end else sub<=sub+1'b1;
        end
    end
    // 独立输出触发器避免二进制计数器组合译码毛刺传到电调引脚；
    // 复位异步拉低输出，复位释放后仍需等待首个完整帧边界，
    // 才允许产生新的上升沿。
    // 输出用专用触发器生成，避免二进制计数器组合译码毛刺到达电调引脚。
    // 复位异步拉低输出；释放复位后等待首个完整帧边界才产生脉冲上升沿。
    always @(posedge clk or negedge rst_n) begin
        if(!rst_n) begin left_pwm<=0;right_pwm<=0;end
        else if(sub==TICKS_PER_US-1) begin
            // 每帧两路同时拉高，再按各自锁存脉宽独立拉低，帧内不拼接新旧脉宽。
            if(phase==FRAME_US-1) begin left_pwm<=1;right_pwm<=1;end
            else begin
                if(phase==latched_left_us-1'b1)left_pwm<=0;
                if(phase==latched_right_us-1'b1)right_pwm<=0;
            end
        end
    end
endmodule
