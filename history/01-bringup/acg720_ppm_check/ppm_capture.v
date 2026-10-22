// Bench-only PPM frame capture for a 50 MHz FPGA clock.
// Measures rising-edge to rising-edge spacing, so normal/inverted PPM
// pulses both work as long as there is exactly one rising edge per slot.
// This does NOT prove that the RF link is healthy: a receiver may keep
// emitting programmed failsafe values after the transmitter is turned off.
module ppm_capture (
    input  wire       clk50,
    input  wire       ppm_in,
    output reg        frame_valid = 1'b0,
    output reg [5:0]  channel_high = 6'b0
);
    // 50 ticks/us. A channel slot is accepted from 0.8 to 2.2 ms;
    // a gap above 3 ms marks the start of the next frame.
    localparam [19:0] CH_MIN_TICKS   = 20'd40_000;
    localparam [19:0] CH_MID_TICKS   = 20'd75_000;
    localparam [19:0] CH_MAX_TICKS   = 20'd110_000;
    localparam [19:0] SYNC_MIN_TICKS = 20'd150_000;
    localparam [19:0] EDGE_SAT_TICKS = 20'd1_000_000;
    localparam [21:0] FRAME_TIMEOUT  = 22'd2_500_000; // 50 ms

    reg [1:0] ppm_sync = 2'b00;
    reg ppm_prev = 1'b0;
    reg [19:0] edge_ticks = 20'd0;
    reg [21:0] frame_age = 22'd0;
    reg [2:0] slot_index = 3'd0;
    reg [5:0] pending_high = 6'b0;
    reg frame_good = 1'b0;

    wire rising_edge = ppm_sync[1] && !ppm_prev;
    wire channel_slot_ok = (edge_ticks >= CH_MIN_TICKS) &&
                           (edge_ticks <= CH_MAX_TICKS);

    always @(posedge clk50) begin
        ppm_sync <= {ppm_sync[0], ppm_in};
        ppm_prev <= ppm_sync[1];

        if (edge_ticks < EDGE_SAT_TICKS)
            edge_ticks <= edge_ticks + 1'b1;

        if (frame_age < FRAME_TIMEOUT)
            frame_age <= frame_age + 1'b1;
        else
            frame_valid <= 1'b0;

        if (rising_edge) begin
            edge_ticks <= 20'd0;

            if (edge_ticks > SYNC_MIN_TICKS) begin
                // A complete frame is published only at the next sync gap.
                if ((slot_index >= 3'd6) && frame_good) begin
                    channel_high <= pending_high;
                    frame_valid <= 1'b1;
                    frame_age <= 22'd0;
                end else begin
                    frame_valid <= 1'b0;
                end
                slot_index <= 3'd0;
                pending_high <= 6'b0;
                frame_good <= 1'b1;
            end else if (slot_index < 3'd6) begin
                pending_high[slot_index] <= (edge_ticks > CH_MID_TICKS);
                slot_index <= slot_index + 1'b1;
                if (!channel_slot_ok)
                    frame_good <= 1'b0;
            end else begin
                // Ignore optional additional channels, but reject bad slots.
                if (slot_index < 3'd7)
                    slot_index <= slot_index + 1'b1;
                if (!channel_slot_ok)
                    frame_good <= 1'b0;
            end
        end
    end
endmodule
