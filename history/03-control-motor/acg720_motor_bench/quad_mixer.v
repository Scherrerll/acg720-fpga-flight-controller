// Bench X quad request mix, microseconds. Body axes X forward/Y right/Z down.
// M1 front-left, M2 front-right, M3 rear-right, M4 rear-left.
// Verified M1/M3 CW, M2/M4 CCW from above: positive yaw increases M2/M4.
// Per-channel clamps only: no desaturation or allocation feedback to PI integrals.
// Disabled requests are fixed at 1000 us. This module does not drive physical pins.
module quad_mixer #(
    parameter integer MIN_US=1000,
    parameter integer MAX_US=1200
) (
    input wire enabled,
    input wire [15:0] throttle_us,
    input wire signed [15:0] roll_us,pitch_us,yaw_us,
    output wire [15:0] m1_us,m2_us,m3_us,m4_us,
    output wire saturated
);
    wire signed [31:0] thrust=$signed({1'b0,throttle_us});
    wire signed [31:0] roll=roll_us,pitch=pitch_us,yaw=yaw_us;
    wire signed [31:0] mix1=thrust+roll+pitch-yaw;
    wire signed [31:0] mix2=thrust-roll+pitch+yaw;
    wire signed [31:0] mix3=thrust-roll-pitch-yaw;
    wire signed [31:0] mix4=thrust+roll-pitch+yaw;
    function [15:0] clamp;
        input signed [31:0] value;
        begin
            if(value<MIN_US) clamp=MIN_US;
            else if(value>MAX_US) clamp=MAX_US;
            else clamp=value[15:0];
        end
    endfunction
    assign m1_us=enabled ? clamp(mix1) : 16'd1000;
    assign m2_us=enabled ? clamp(mix2) : 16'd1000;
    assign m3_us=enabled ? clamp(mix3) : 16'd1000;
    assign m4_us=enabled ? clamp(mix4) : 16'd1000;
    assign saturated=enabled && (mix1<MIN_US || mix1>MAX_US || mix2<MIN_US || mix2>MAX_US ||
                                 mix3<MIN_US || mix3>MAX_US || mix4<MIN_US || mix4>MAX_US);
endmodule
