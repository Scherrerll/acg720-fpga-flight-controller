// Reject detectable transport/sentinel errors before consumers see a sample.
// This is not an SPI CRC and cannot detect every plausible corrupted value.
module imu_checked_guard #(
    parameter integer TIMEOUT_TICKS = 2500000, // 50 ms at 50 MHz
    parameter integer MAX_BAD_STREAK = 3,
    parameter integer RECOVERY_SAMPLES = 5
) (
    input wire clk, input wire rst_n,
    input wire record_ready,
    input wire [7:0] who, pwr,
    input wire [95:0] raw,
    input wire [7:0] extra_reason,
    output reg sample_valid = 0,
    output reg [95:0] accepted_raw = 0,
    output reg [31:0] sample_dt_ticks = 0,
    output wire link_usable,
    output wire stale,
    output reg [7:0] reject_reason = 0,
    output reg [31:0] accepted_count = 0,
    output reg [31:0] rejected_count = 0,
    output reg [31:0] bad_streak = 0,
    output reg [31:0] age_ticks = TIMEOUT_TICKS
);
    reg seen_good = 0, qualified = 0;
    reg [31:0] recovery_count = 0;
    wire invalid_axis = raw[95:80] == 16'h8000 ||
        raw[79:64] == 16'h8000 || raw[63:48] == 16'h8000 ||
        raw[47:32] == 16'h8000 || raw[31:16] == 16'h8000 ||
        raw[15:0] == 16'h8000;
    wire [7:0] base_reason = {3'b000, invalid_axis,
        (raw == {96{1'b1}}), (raw == 96'd0),
        (pwr != 8'h0F), (who != 8'h47)};
    wire [7:0] reason = base_reason | extra_reason;
    assign stale = !seen_good || age_ticks >= TIMEOUT_TICKS;
    assign link_usable = qualified && !stale && bad_streak < MAX_BAD_STREAK;
    always @(posedge clk) begin
        if (!rst_n) begin
            sample_valid <= 0;
            accepted_raw <= 0;
            sample_dt_ticks <= 0;
            accepted_count <= 0;
            rejected_count <= 0;
            bad_streak <= 0;
            age_ticks <= TIMEOUT_TICKS;
            seen_good <= 0;
            qualified <= 0;
            recovery_count <= 0;
            reject_reason <= 0;
        end else begin
            sample_valid <= 0;
            // Age saturates; an old sample never wraps around to look fresh.
            if (age_ticks != 32'hFFFFFFFF) age_ticks <= age_ticks + 1'b1;
            if (age_ticks >= TIMEOUT_TICKS - 1) begin
                qualified <= 0;
                recovery_count <= 0;
            end
            if (record_ready) begin
                reject_reason <= reason;
                if (reason == 0) begin
                    // The first sample / recovery after timeout has no valid dt.
                    sample_dt_ticks <= (stale || age_ticks >= TIMEOUT_TICKS - 1)
                        ? 32'd0 : age_ticks + 1'b1;
                    accepted_raw <= raw;
                    sample_valid <= 1;
                    if (accepted_count != 32'hFFFFFFFF)
                        accepted_count <= accepted_count + 1'b1;
                    seen_good <= 1;
                    age_ticks <= 0;
                    bad_streak <= 0;
                    if (stale || age_ticks >= TIMEOUT_TICKS - 1) begin
                        recovery_count <= 1;
                        qualified <= (RECOVERY_SAMPLES <= 1);
                    end else if (!qualified) begin
                        if (recovery_count < RECOVERY_SAMPLES)
                            recovery_count <= recovery_count + 1'b1;
                        if (recovery_count + 1 >= RECOVERY_SAMPLES)
                            qualified <= 1;
                    end
                end else begin
                    // Keep the last good values, but never issue a new-sample pulse.
                    if (rejected_count != 32'hFFFFFFFF)
                        rejected_count <= rejected_count + 1'b1;
                    if (bad_streak != 32'hFFFFFFFF)
                        bad_streak <= bad_streak + 1'b1;
                    recovery_count <= 0;
                    if (bad_streak + 1 >= MAX_BAD_STREAK) qualified <= 0;
                end
            end
        end
    end
endmodule
