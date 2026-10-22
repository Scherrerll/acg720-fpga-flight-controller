`timescale 1ns/1ps
// Receive-only PPM decoder; there are no motor outputs.
// A frame is committed atomically at a sync interval >3000 us. 5..8
// intervals in the inclusive 800..2200 us range form an accepted frame.
// A bad interval, ninth channel, short frame, or freshness timeout revokes
// valid. The last committed channel values are retained for diagnostics only.
module rc_ppm #(
    parameter integer CLK_HZ = 50000000,
    parameter integer FRESH_TICKS = 5000000
) (
    input wire clk,
    input wire rst_n,
    input wire ppm_in,
    output reg frame_update,
    output wire valid,
    output reg [3:0] channel_count,
    output reg [15:0] ch1, ch2, ch3, ch4, ch5,
    output reg [15:0] frame_sequence,
    output reg [15:0] ch6,ch7,ch8
);
    // CLK_HZ must be an integer multiple of 1 MHz (50 MHz on ACG720).
    localparam integer TICKS_PER_US = CLK_HZ / 1000000;
    localparam integer SUB_WIDTH = TICKS_PER_US > 1 ? $clog2(TICKS_PER_US) : 1;
    localparam [SUB_WIDTH-1:0] SUB_LAST = TICKS_PER_US - 1;

    reg [1:0] ppm_sync;
    reg ppm_last;
    // A short carry per clock replaces a 32-bit combinational divide by 50.
    // Saturating at 3001 us is enough: every longer gap is a sync interval.
    reg [11:0] interval_us;
    reg [SUB_WIDTH-1:0] interval_subticks;
    reg [31:0] fresh_ticks;
    reg frame_started, frame_bad;
    reg [3:0] slot_count;
    reg [15:0] work1, work2, work3, work4, work5, work6, work7, work8;

    wire ppm_rise = ppm_sync[1] && !ppm_last;
    // Stored counters describe N-1 clocks before an edge N clocks later.
    // Include the current clock's carry without rounding sub-us boundaries:
    // 799us+49ticks is invalid, 800us is valid, 2200us+1tick is invalid,
    // and 3000us+1tick is sync, while exactly 3000us is not sync (50 MHz).
    wire edge_exact_us = interval_subticks == SUB_LAST;
    wire [11:0] edge_us = interval_us + (edge_exact_us ? 12'd1 : 12'd0);
    wire channel_interval = edge_us >= 12'd800 &&
        (edge_us < 12'd2200 || (edge_us == 12'd2200 && edge_exact_us));
    wire sync_interval = edge_us > 12'd3000 ||
        (edge_us == 12'd3000 && !edge_exact_us);
    assign valid = fresh_ticks != 0;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            ppm_sync <= 0;
            ppm_last <= 0;
            interval_us <= 0;
            interval_subticks <= 0;
            fresh_ticks <= 0;
            frame_started <= 0;
            frame_bad <= 0;
            slot_count <= 0;
            work1 <= 0; work2 <= 0; work3 <= 0; work4 <= 0; work5 <= 0; work6 <= 0; work7 <= 0; work8 <= 0;
            ch1 <= 0; ch2 <= 0; ch3 <= 0; ch4 <= 0; ch5 <= 0; ch6 <= 0; ch7 <= 0; ch8 <= 0;
            channel_count <= 0;
            frame_sequence <= 0;
            frame_update <= 0;
        end else begin
            ppm_sync <= {ppm_sync[0], ppm_in};
            ppm_last <= ppm_sync[1];
            frame_update <= 0;
            if (interval_us < 12'd3001) begin
                if (edge_exact_us) begin
                    interval_us <= interval_us + 1'b1;
                    interval_subticks <= 0;
                end else interval_subticks <= interval_subticks + 1'b1;
            end
            if (fresh_ticks != 0) fresh_ticks <= fresh_ticks - 1'b1;

            if (ppm_rise) begin
                interval_us <= 0;
                interval_subticks <= 0;
                if (sync_interval) begin
                    if (frame_started && !frame_bad && slot_count >= 5 && slot_count <= 8) begin
                        ch1 <= work1; ch2 <= work2; ch3 <= work3;
                        ch4 <= work4; ch5 <= work5;
                        ch6 <= slot_count>=6 ? work6 : 16'd0;
                        ch7 <= slot_count>=7 ? work7 : 16'd0;
                        ch8 <= slot_count>=8 ? work8 : 16'd0;
                        channel_count <= slot_count;
                        frame_sequence <= frame_sequence + 1'b1;
                        frame_update <= 1;
                        fresh_ticks <= FRESH_TICKS;
                    end else if (frame_started) begin
                        fresh_ticks <= 0;
                        channel_count <= 0;
                    end
                    frame_started <= 1;
                    frame_bad <= 0;
                    slot_count <= 0;
                    work1 <= 0; work2 <= 0; work3 <= 0; work4 <= 0; work5 <= 0; work6 <= 0; work7 <= 0; work8 <= 0;
                end else if (frame_started) begin
                    if (channel_interval && slot_count < 8) begin
                        slot_count <= slot_count + 1'b1;
                        case (slot_count)
                            0: work1 <= {4'd0,edge_us};
                            1: work2 <= {4'd0,edge_us};
                            2: work3 <= {4'd0,edge_us};
                            3: work4 <= {4'd0,edge_us};
                            4: work5 <= {4'd0,edge_us};
                            5: work6 <= {4'd0,edge_us};
                            6: work7 <= {4'd0,edge_us};
                            7: work8 <= {4'd0,edge_us};
                            default: begin end
                        endcase
                    end else begin
                        frame_bad <= 1;
                        slot_count <= 9; // Saturate; never wrap to a good count.
                        fresh_ticks <= 0;
                        channel_count <= 0;
                    end
                end
            end
        end
    end
endmodule
