`timescale 1ns/1ps
// Existing verified rotor order. Bounds here belong to the virtual bench only.
// Directional saturation prevents integration into an unavailable motor direction.
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
    assign saturation_negative[0]=enabled && (a<=MIN_US || d<=MIN_US || b>=MAX_US || c>=MAX_US);
    assign saturation_positive[1]=enabled && (a>=MAX_US || b>=MAX_US || c<=MIN_US || d<=MIN_US);
    assign saturation_negative[1]=enabled && (a<=MIN_US || b<=MIN_US || c>=MAX_US || d>=MAX_US);
    assign saturation_positive[2]=enabled && (b>=MAX_US || d>=MAX_US || a<=MIN_US || c<=MIN_US);
    assign saturation_negative[2]=enabled && (b<=MIN_US || d<=MIN_US || a>=MAX_US || c>=MAX_US);
endmodule
