`timescale 1ns/1ps
// 沿用已验证电机顺序的四旋翼混控；声明默认限幅仅供虚拟台架配置。
// 按轴输出正向/负向饱和反馈，防止控制器继续向不可用的电机推力方向积分。
// 总油门、三轴修正和四路输出均以微秒为单位；组合逻辑直接反映输入，enabled=0 时四路为 1000 微秒。
// 默认 MIN_US=1000、MAX_US=1200；flight_core 以 RUN_MIN_US/RUN_MAX_US 覆盖，默认集成为 1200..2000 微秒。
// saturation_* 的位 0/1/2 分别为横滚/俯仰/偏航；达到边界即反馈方向饱和，saturated 仅在越界时置位。
module quad_mixer_feedback #(
    parameter integer MIN_US=1000, MAX_US=1200
)(
    input wire enabled,
    input wire [15:0] throttle_us,
    input wire signed [15:0] roll_us,pitch_us,yaw_us,
    output wire [15:0] m1_us,m2_us,m3_us,m4_us,
    output wire saturated,
    output wire [2:0] saturation_positive,saturation_negative
);
    wire signed [31:0] t=$signed({1'b0,throttle_us});
    wire signed [31:0] r=roll_us,p=pitch_us,y=yaw_us;
    wire signed [31:0] a=(r+p-y)+t, b=(p-r+y)+t, c=(-r-p-y)+t, d=(r-p+y)+t;
    // 按项目电机编号分配总油门与三轴修正，再逐路限幅；使用有符号 32 位和避免负修正回绕。
    function [15:0] clamp;
        input signed [31:0] value;
        begin
            if(value<MIN_US) clamp=MIN_US;
            else if(value>MAX_US) clamp=MAX_US;
            else clamp=value[15:0];
        end
    endfunction
    assign m1_us=enabled ? clamp(a) : 16'd1000;
    assign m2_us=enabled ? clamp(b) : 16'd1000;
    assign m3_us=enabled ? clamp(c) : 16'd1000;
    assign m4_us=enabled ? clamp(d) : 16'd1000;
    assign saturated=enabled && (a<MIN_US || b<MIN_US || c<MIN_US || d<MIN_US ||
                                a>MAX_US || b>MAX_US || c>MAX_US || d>MAX_US);
    assign saturation_positive[0]=enabled && (a>=MAX_US || d>=MAX_US || b<=MIN_US || c<=MIN_US);
    // 各轴分别检查推力增减将受哪些电机边界约束，正负方向独立反馈以支持积分退饱和。
    assign saturation_negative[0]=enabled && (a<=MIN_US || d<=MIN_US || b>=MAX_US || c>=MAX_US);
    assign saturation_positive[1]=enabled && (a>=MAX_US || b>=MAX_US || c<=MIN_US || d<=MIN_US);
    assign saturation_negative[1]=enabled && (a<=MIN_US || b<=MIN_US || c>=MAX_US || d>=MAX_US);
    assign saturation_positive[2]=enabled && (b>=MAX_US || d>=MAX_US || a<=MIN_US || c<=MIN_US);
    assign saturation_negative[2]=enabled && (b<=MIN_US || d<=MIN_US || a>=MAX_US || c>=MAX_US);
endmodule
