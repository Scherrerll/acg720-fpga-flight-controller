// Reject detectable transport/sentinel errors before consumers see a sample.
// This is not an SPI CRC and cannot detect every plausible corrupted value.
module imu_checked_guard_pipelined #(
    parameter integer TIMEOUT_TICKS = 2500000, // 50 ms at 50 MHz
    parameter integer MAX_BAD_STREAK = 3,
    parameter integer RECOVERY_SAMPLES = 5,
    parameter integer INPUT_DELAY_TICKS = 3,
    parameter integer USE_PRECHECKED = 0
) (
    input wire clk, input wire rst_n,
    input wire record_ready,
    // Original guard-consumption time: raw record_ready delayed one clock.
    input wire origin_record_ready,
    input wire [7:0] who, pwr,
    input wire [95:0] raw,
    input wire [7:0] extra_reason,
    // Registered base check from the same temporal snapshot; includes ID,
    // power/config/status and all raw sentinel checks. Temporal rejection
    // remains in extra_reason. Default keeps standalone legacy semantics.
    input wire checked_base_ok,
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
    reg [31:0] origin_dt=0,origin_recovery_count=0;
    reg origin_timeout=1,origin_qualified=0;
    reg [31:0] recovery_count = 0;
    wire invalid_axis = raw[95:80] == 16'h8000 ||
        raw[79:64] == 16'h8000 || raw[63:48] == 16'h8000 ||
        raw[47:32] == 16'h8000 || raw[31:16] == 16'h8000 ||
        raw[15:0] == 16'h8000;
    wire [7:0] base_reason = {3'b000, invalid_axis,
        (raw == {96{1'b1}}), (raw == 96'd0),
        (pwr != 8'h0F), (who != 8'h47)};
    wire [7:0] reason = base_reason | extra_reason;
    wire record_ok = USE_PRECHECKED ? (checked_base_ok && extra_reason == 0) : (reason == 0);
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
            origin_dt<=0; origin_recovery_count<=0; origin_timeout<=1; origin_qualified<=0;
        end else begin
            sample_valid <= 0;
            // Age saturates; an old sample never wraps around to look fresh.
            if (age_ticks != 32'hFFFFFFFF) age_ticks <= age_ticks + 1'b1;
            if (age_ticks >= TIMEOUT_TICKS - 1) begin
                qualified <= 0;
                recovery_count <= 0;
            end
            if (origin_record_ready) begin
                origin_timeout <= stale || age_ticks >= TIMEOUT_TICKS-1;
                origin_dt <= (stale || age_ticks >= TIMEOUT_TICKS-1) ? 32'd0 : age_ticks+1'b1;
                origin_qualified <= qualified; origin_recovery_count <= recovery_count;
            end
            if (record_ready) begin
                reject_reason <= reason;
                if (record_ok) begin
                    // The first sample / recovery after timeout has no valid dt.
                    sample_dt_ticks <= origin_dt;
                    accepted_raw <= raw;
                    sample_valid <= 1;
                    if (accepted_count != 32'hFFFFFFFF)
                        accepted_count <= accepted_count + 1'b1;
                    seen_good <= 1;
                    // Age includes the validation delay, so timeout stays at the source deadline.
                    age_ticks <= INPUT_DELAY_TICKS;
                    bad_streak <= 0;
                    qualified <= origin_qualified; recovery_count <= origin_recovery_count;
                    if (origin_timeout) begin
                        recovery_count <= 1;
                        qualified <= (RECOVERY_SAMPLES <= 1);
                    end else if (!origin_qualified) begin
                        if (origin_recovery_count < RECOVERY_SAMPLES)
                            recovery_count <= origin_recovery_count + 1'b1;
                        if (origin_recovery_count + 1 >= RECOVERY_SAMPLES)
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
