`timescale 1ns/1ps
// 用于无桨台架的四路相干、有界 PWM 输出。
// 使能丢失后将本帧锁定到怠速，直到下一帧才可重新启用；
// 已经开始的脉冲至少完成 1000 微秒怠速前缀，本帧中途不能重新启动。
// 四路 PWM：模块默认帧长 20 毫秒、命令范围 1000 至 1150 微秒，集成时可由参数覆盖。
module motor_pwm #(
    // TICKS_PER_US 默认 50 对应 50 MHz，EXTERNAL_TICKS 默认 0 表示内部换算微秒命令。
    // flight_core 将 FRAME_US 覆盖为 OUTPUT_FRAME_US（默认 2500），MAX_US 覆盖为 RUN_MAX_US（默认 2000），
    // 并将 EXTERNAL_TICKS 置为 1，使用上层已限幅且预换算的时钟拍数。
    parameter integer TICKS_PER_US=50,
    parameter integer FRAME_US=20000,
    parameter integer MAX_US=1150,
    parameter integer EXTERNAL_TICKS=0
)(
    input wire clk,rst_n,enabled,
    // m*_us 为微秒命令；四路在同一帧边界锁存。
    input wire [15:0] m1_us,m2_us,m3_us,m4_us,
    // 外部计时模式直接使用预计算时钟数，本模块不会再次对 pre_ticks 限幅。
    input wire [31:0] pre_ticks1,pre_ticks2,pre_ticks3,pre_ticks4,
    output wire motor1_pwm,motor2_pwm,motor3_pwm,motor4_pwm,
    output wire [15:0] effective1_us,effective2_us,effective3_us,effective4_us,
    output wire [15:0] frame_latched1_us,frame_latched2_us,frame_latched3_us,frame_latched4_us,
    output wire frame_active,limited
);
    // phase 的单位为 clk 周期；每帧从零开始计数，低于阈值时输出高电平。
    localparam integer FRAME_TICKS=TICKS_PER_US*FRAME_US;
    localparam integer MIN_TICKS=TICKS_PER_US*1000;
    localparam integer COUNTER_BITS=$clog2(FRAME_TICKS);
    reg [COUNTER_BITS-1:0] phase=0;
    // 使能丢失后 blocked 保持到下一帧边界，禁止在本帧中途重新启动。
    reg blocked=1;
    reg [15:0] latched1=1000,latched2=1000,latched3=1000,latched4=1000;
    reg [COUNTER_BITS-1:0] ticks1=MIN_TICKS,ticks2=MIN_TICKS,ticks3=MIN_TICKS,ticks4=MIN_TICKS;
    reg latched_limited=0;
    // 微秒命令统一限幅；在外部计时模式下该结果仍用于状态回读。
    function [15:0] clamp;
        input [15:0] value;
        begin
            if(value<1000) clamp=1000;
            else if(value>MAX_US) clamp=MAX_US;
            else clamp=value;
        end
    endfunction
    always @(posedge clk) begin
        // 内部寄存器同步复位；输出组合逻辑同时受 rst_n 直接抑制。
        if(!rst_n) begin
            phase<=0; blocked<=1; latched_limited<=0;
            latched1<=1000;latched2<=1000;latched3<=1000;latched4<=1000;
            ticks1<=MIN_TICKS;ticks2<=MIN_TICKS;ticks3<=MIN_TICKS;ticks4<=MIN_TICKS;
        // 帧末同时装载四路命令、脉宽计数和限幅标记，下一拍进入新帧。
        end else if(phase==FRAME_TICKS-1) begin
            phase<=0;blocked<=!enabled;
            latched1<=clamp(m1_us);latched2<=clamp(m2_us);
            latched3<=clamp(m3_us);latched4<=clamp(m4_us);
            ticks1<=EXTERNAL_TICKS ?pre_ticks1:(clamp(m1_us)*TICKS_PER_US);ticks2<=EXTERNAL_TICKS ?pre_ticks2:(clamp(m2_us)*TICKS_PER_US);
            ticks3<=EXTERNAL_TICKS ?pre_ticks3:(clamp(m3_us)*TICKS_PER_US);ticks4<=EXTERNAL_TICKS ?pre_ticks4:(clamp(m4_us)*TICKS_PER_US);
            latched_limited<=m1_us<1000 || m1_us>MAX_US || m2_us<1000 || m2_us>MAX_US ||
                             m3_us<1000 || m3_us>MAX_US || m4_us<1000 || m4_us>MAX_US;
        end else begin
            phase<=phase+1'b1;
            if(!enabled) blocked<=1;
        end
    end
    assign frame_latched1_us=latched1;assign frame_latched2_us=latched2;
    assign frame_latched3_us=latched3;assign frame_latched4_us=latched4;
    // 只有当前帧未被封锁且使能有效时，才报告命令有效和限幅状态。
    assign frame_active=rst_n && enabled && !blocked;
    assign limited=frame_active && latched_limited;
    // 失能时有效值回报 1000 微秒，帧锁存回读值仍保留上次装载命令。
    assign effective1_us=frame_active ? latched1 : 16'd1000;
    assign effective2_us=frame_active ? latched2 : 16'd1000;
    assign effective3_us=frame_active ? latched3 : 16'd1000;
    assign effective4_us=frame_active ? latched4 : 16'd1000;
    // 四路脉冲同拍起始；使能丢失只能把脉冲截短为怠速前缀
    // 或已经输出的宽度，不会将非复位脉冲缩到 1000 微秒以下。
    // 非复位时每帧至少输出 1000 微秒前缀；失能可截短后续扩展部分。
    assign motor1_pwm=rst_n && ((phase<MIN_TICKS) || (frame_active && phase<ticks1));
    assign motor2_pwm=rst_n && ((phase<MIN_TICKS) || (frame_active && phase<ticks2));
    assign motor3_pwm=rst_n && ((phase<MIN_TICKS) || (frame_active && phase<ticks3));
    assign motor4_pwm=rst_n && ((phase<MIN_TICKS) || (frame_active && phase<ticks4));
endmodule
