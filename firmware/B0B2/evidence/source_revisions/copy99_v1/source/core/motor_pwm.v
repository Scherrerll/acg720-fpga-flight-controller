`timescale 1ns/1ps
// No-prop bench output only. Frame commands are coherent and bounded.
// Losing enable latches idle until the next frame. A pulse already started
// finishes at least its 1000-us idle prefix; it cannot restart in that frame.
module motor_pwm #(
    parameter integer TICKS_PER_US=50,
    parameter integer FRAME_US=20000,
    parameter integer MAX_US=1150,
    parameter integer EXTERNAL_TICKS=0
)(
    input wire clk,rst_n,enabled,
    input wire [15:0] m1_us,m2_us,m3_us,m4_us,
    input wire [31:0] pre_ticks1,pre_ticks2,pre_ticks3,pre_ticks4,
    output wire motor1_pwm,motor2_pwm,motor3_pwm,motor4_pwm,
    output wire [15:0] effective1_us,effective2_us,effective3_us,effective4_us,
    output wire [15:0] frame_latched1_us,frame_latched2_us,frame_latched3_us,frame_latched4_us,
    output wire frame_active,limited
);
    localparam integer FRAME_TICKS=TICKS_PER_US*FRAME_US;
    localparam integer MIN_TICKS=TICKS_PER_US*1000;
    localparam integer COUNTER_BITS=$clog2(FRAME_TICKS);
    reg [COUNTER_BITS-1:0] phase=0;
    reg blocked=1;
    reg [15:0] latched1=1000,latched2=1000,latched3=1000,latched4=1000;
    reg [COUNTER_BITS-1:0] ticks1=MIN_TICKS,ticks2=MIN_TICKS,ticks3=MIN_TICKS,ticks4=MIN_TICKS;
    reg latched_limited=0;
    function [15:0] clamp;
        input [15:0] value;
        begin
            if(value<1000) clamp=1000;
            else if(value>MAX_US) clamp=MAX_US;
            else clamp=value;
        end
    endfunction
    always @(posedge clk) begin
        if(!rst_n) begin
            phase<=0; blocked<=1; latched_limited<=0;
            latched1<=1000;latched2<=1000;latched3<=1000;latched4<=1000;
            ticks1<=MIN_TICKS;ticks2<=MIN_TICKS;ticks3<=MIN_TICKS;ticks4<=MIN_TICKS;
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
    assign frame_active=rst_n && enabled && !blocked;
    assign limited=frame_active && latched_limited;
    assign effective1_us=frame_active ? latched1 : 16'd1000;
    assign effective2_us=frame_active ? latched2 : 16'd1000;
    assign effective3_us=frame_active ? latched3 : 16'd1000;
    assign effective4_us=frame_active ? latched4 : 16'd1000;
    // All four channels start together. Enable loss can only shorten a pulse
    // to idle or the already elapsed width, never to less than 1000 us.
    assign motor1_pwm=rst_n && ((phase<MIN_TICKS) || (frame_active && phase<ticks1));
    assign motor2_pwm=rst_n && ((phase<MIN_TICKS) || (frame_active && phase<ticks2));
    assign motor3_pwm=rst_n && ((phase<MIN_TICKS) || (frame_active && phase<ticks3));
    assign motor4_pwm=rst_n && ((phase<MIN_TICKS) || (frame_active && phase<ticks4));
endmodule
