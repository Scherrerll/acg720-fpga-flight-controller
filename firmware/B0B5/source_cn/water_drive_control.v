`timescale 1ns/1ps
// B0B5 水面控制逻辑；电调中位和反向行为的实测范围另见版本记录。
// 仅停机时接纳 CH6 模式请求，飞行已解锁时拨动 CH6 不切换模式。
// 水面推进控制：仲裁水面/飞行模式，完成独立解锁并生成左右推进目标。
// 遥控通道和输出目标均以微秒表示；本模块只生成数值，不直接输出PWM。
module water_drive_control #(
    parameter integer TIMER_DIVISOR=50000, // 50MHz 下共用的 1ms 计时使能
    parameter integer FRESH_TICKS=5000000, // 真实 50MHz 时钟下对应 100ms
    parameter integer MODE_HOLD_TICKS=1250000, // 25ms，超过十个飞行 PWM 帧
    parameter integer LOW_HOLD_TICKS=25000000,
    parameter integer HIGH_HOLD_TICKS=25000000
)(
    input wire clk,rst_n,rc_update,rc_valid,
    input wire [3:0] channel_count,
    input wire [15:0] ch1,ch2,ch3,ch4,ch5,ch6,ch7,ch8,
    input wire flight_armed,flight_stopped,
    output wire flight_permitted,
    output reg water_mode=0,
    output wire water_enabled,
    output wire [15:0] left_us,right_us,
    output wire rc_fresh
);
    // 参数仍用标称时钟周期定义；失效期限向下取整，最短保持时间
    // 向上取整并计入完整首间隔；故障条件仍逐时钟清状态，
    // 包括发生在两次毫秒计时使能之间的短暂故障。
    // 时长参数以输入时钟周期定义；默认50MHz下共享计时使能每1ms产生一次。
    // 新鲜度向下取整，最短保持时间向上取整；非法参数使功能失效并在仿真报错。
    localparam integer TIMER_OK=TIMER_DIVISOR>=1 && FRESH_TICKS>=TIMER_DIVISOR &&
        MODE_HOLD_TICKS>=1 && LOW_HOLD_TICKS>=1 && HIGH_HOLD_TICKS>=1;
    localparam integer DIV=TIMER_DIVISOR<1 ? 1:TIMER_DIVISOR;
    localparam integer FRESH_LIMIT=FRESH_TICKS/DIV<1 ? 1:FRESH_TICKS/DIV;
    localparam integer MODE_LIMIT=(MODE_HOLD_TICKS+DIV-1)/DIV;
    localparam integer LOW_LIMIT=(LOW_HOLD_TICKS+DIV-1)/DIV;
    localparam integer HIGH_LIMIT=(HIGH_HOLD_TICKS+DIV-1)/DIV;
    localparam integer MODE_TERMINAL=DIV==1 ? MODE_LIMIT-1:MODE_LIMIT;
    localparam integer LOW_TERMINAL=DIV==1 ? LOW_LIMIT-1:LOW_LIMIT;
    localparam integer HIGH_TERMINAL=DIV==1 ? HIGH_LIMIT-1:HIGH_LIMIT;
    localparam integer HOLD_LIMIT=LOW_LIMIT>HIGH_LIMIT ? LOW_LIMIT:HIGH_LIMIT;
    localparam integer PHASE_BITS=DIV<=1 ? 1:$clog2(DIV);
    localparam integer AGE_BITS=FRESH_LIMIT<1 ? 1:$clog2(FRESH_LIMIT+1);
    localparam integer MODE_BITS=MODE_LIMIT<1 ? 1:$clog2(MODE_LIMIT+1);
    localparam integer HOLD_BITS=HOLD_LIMIT<1 ? 1:$clog2(HOLD_LIMIT+1);
    reg [PHASE_BITS-1:0] timer_phase=0;
    wire timer_tick=DIV==1 || timer_phase==DIV-1;
    always @(posedge clk) begin
        if(!rst_n || timer_tick) timer_phase<=0;
        else timer_phase<=timer_phase+1'b1;
    end
    generate if(!TIMER_OK) begin : invalid_timer_configuration
        initial $fatal(1,"invalid water timer divisor or nominal duration");
    end endgenerate
    // 通道有效范围为800..2200us，中位判定包含1470..1530us两个端点。
    function bounds;
        input [15:0] c;
        begin bounds=c>=800 && c<=2200; end
    endfunction
    function centered;
        input [15:0] c;
        begin centered=c>=1470 && c<=1530; end
    endfunction
    wire channels_ok=channel_count>=7 && channel_count<=8 &&
        bounds(ch1)&&bounds(ch2)&&bounds(ch3)&&bounds(ch4)&&bounds(ch5)&&
        bounds(ch6)&&bounds(ch7)&&(channel_count!=8 || bounds(ch8));
    // 仅完整有效的遥控更新清零年龄；失效或通道越界在任意时钟立即使数据过期。
    // 默认新鲜度上限为100ms，达到上限后不能保持水面驱动许可。
    reg [AGE_BITS-1:0] age=FRESH_LIMIT;
    always @(posedge clk) begin
        if(!rst_n || !rc_valid || !channels_ok) age<=FRESH_LIMIT;
        else if(rc_update) age<=0;
        else if(timer_tick && age<FRESH_LIMIT) age<=age+1'b1;
    end
    assign rc_fresh=TIMER_OK && rc_valid && channels_ok && age<FRESH_LIMIT;
    // CH5低/高位分别用于解除与解锁；CH6低位选飞行，高位选水面。
    // 中位要求检查CH1、CH2、CH4；CH3必须保持800..1100us低油门。
    wire switch_low=ch5>=800 && ch5<=1200;
    wire switch_high=ch5>=1800 && ch5<=2200;
    wire want_water=ch6>=1800 && ch6<=2200;
    wire want_flight=ch6>=800 && ch6<=1200;
    wire neutral=centered(ch1)&&centered(ch2)&&centered(ch4);
    wire throttle_low=ch3>=800 && ch3<=1100;
    // 地面水面请求即使未被接受，也不能随后意外解锁飞行。
    // 阻止状态保持到满足停机条件并明确请求飞行模式为止。
    // 地面收到水面请求后保留飞行阻止状态，须安全完成飞行模式请求才能解除。
    reg flight_blocked=0;
    reg [MODE_BITS-1:0] mode_hold=0;
    reg previous_request=0;
    // 模式切换只在未解锁、飞行输出已停止、摇杆中位及CH5低位时计时。
    // 默认连续确认25ms；飞行已解锁时改变CH6不会切换到水面模式。
    wire mode_safe=rc_fresh && switch_low && neutral && throttle_low &&
        !flight_armed && flight_stopped && (want_water || want_flight);
    assign flight_permitted=!water_mode && !flight_blocked;
    always @(posedge clk) begin
        if(!rst_n) begin
            water_mode<=0;flight_blocked<=0;mode_hold<=0;previous_request<=0;
        end else begin
            if(rc_fresh && switch_low && want_water && !flight_armed)
                flight_blocked<=1;
            previous_request<=want_water;
            if(!mode_safe || previous_request!=want_water) mode_hold<=0;
            else if(timer_tick) begin
                if(mode_hold>=MODE_TERMINAL) begin
                    water_mode<=want_water;
                    flight_blocked<=want_water;
                    mode_hold<=0;
                end else mode_hold<=mode_hold+1'b1;
            end
        end
    end
    // 水面解锁依次确认CH5低位和高位，两个阶段均须摇杆中位，默认各保持0.5s。
    // 中途不满足阶段条件会清除相应计时或准备状态，不能累加零散的保持片段。
    reg armed=0,low_ready=0;
    reg [HOLD_BITS-1:0] hold_count=0; // 低位确认与高位确认互斥，共用一个计时器
    // 水面模式、遥控新鲜度、CH6、低油门和飞行停止条件共同约束水面健康状态。
    wire healthy=water_mode && rc_fresh && want_water && throttle_low &&
        !flight_armed && flight_stopped;
    // 最终使能同时检查复位、已解锁状态及CH5高位；健康条件失效立即撤销许可。
    assign water_enabled=TIMER_OK && rst_n && armed && healthy && switch_high;
    always @(posedge clk) begin
        if(!rst_n || !healthy) begin
            armed<=0;low_ready<=0;hold_count<=0;
        end else if(armed) begin
            if(!switch_high) begin armed<=0;low_ready<=0;hold_count<=0;end
        end else if(!low_ready) begin
            if(switch_low && neutral) begin
                if(timer_tick) begin
                    if(hold_count>=LOW_TERMINAL) begin
                        low_ready<=1;hold_count<=0;
                    end else hold_count<=hold_count+1'b1;
                end
            end else hold_count<=0;
        end else if(switch_high && neutral) begin
            if(timer_tick) begin
                if(hold_count>=HIGH_TERMINAL) begin
                    armed<=1;hold_count<=0;
                end else hold_count<=hold_count+1'b1;
            end
        end else if(switch_low && neutral) hold_count<=0;
        else begin low_ready<=0;hold_count<=0;end
    end
    // 先使用 ±30 微秒硬死区，再把未缩放偏差限于 ±500 微秒。
    // 逻辑正方向表示朝机头推力；CH4 正偏差使左侧命令更大。
    // 硬死区内输出零，死区外保留相对1500us的原始偏差，再限制为正负500us。
    function signed [11:0] stick;
        input [15:0] c;
        begin
            if(c>=1470 && c<=1530) stick=0;
            else if(c<1000) stick=-12'sd500;
            else if(c>2000) stick=12'sd500;
            else stick=$signed({1'b0,c[10:0]})-12'sd1500;
        end
    endfunction
    function [15:0] limit;
        input signed [12:0] c;
        begin
            if(c>500) limit=2000;
            else if(c< -500) limit=1000;
            else limit=13'sd1500+c;
        end
    endfunction
    // CH2控制纵向推力，CH4控制差速转向：左=推力+转向，右=推力-转向。
    // 混控后分别限制到1000..2000us，不为保留比例而同时缩放两侧。
    wire signed [11:0] thrust=stick(ch2),turn=stick(ch4);
    reg signed [12:0] mixed_left=0,mixed_right=0;
    // 混控与限幅各使用一级寄存器；停机和换向保护由后级水面PWM模块执行。
    reg [15:0] bounded_left=1500,bounded_right=1500;
    always @(posedge clk) begin
        if(!rst_n) begin
            mixed_left<=0;mixed_right<=0;
            bounded_left<=1500;bounded_right<=1500;
        end else begin
            mixed_left<=$signed({thrust[11],thrust})+$signed({turn[11],turn});
            mixed_right<=$signed({thrust[11],thrust})-$signed({turn[11],turn});
            bounded_left<=limit(mixed_left);bounded_right<=limit(mixed_right);
        end
    end
    assign left_us=bounded_left;
    assign right_us=bounded_right;
endmodule
