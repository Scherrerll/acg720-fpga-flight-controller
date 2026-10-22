// First receiver-input check. No ESC outputs exist in this top module.
module acg720_ppm_check (
    input  wire clk50,
    input  wire rc_ppm_in,
    output wire led2,
    output wire led3,
    output wire led4,
    output wire led5,
    output wire led6,
    output wire led7
);
    wire frame_valid;
    wire [5:0] channel_high;

    ppm_capture receiver (
        .clk50(clk50),
        .ppm_in(rc_ppm_in),
        .frame_valid(frame_valid),
        .channel_high(channel_high)
    );

    assign led2 = frame_valid;
    assign led3 = frame_valid && channel_high[0]; // CH1
    assign led4 = frame_valid && channel_high[1]; // CH2
    assign led5 = frame_valid && channel_high[2]; // CH3
    assign led6 = frame_valid && channel_high[3]; // CH4
    assign led7 = frame_valid && channel_high[4]; // CH5
    // CH6 is decoded and available internally for the later flight logic.
endmodule
