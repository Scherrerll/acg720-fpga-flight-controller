`timescale 1ns/1ps
// Virtual bench arming state only. This module has no motor pins.
// At 50 MHz the defaults require 0.5 s continuously low, then 0.5 s high,
// with low throttle and healthy RC/sensor in both phases.
// Every fault or departure from CH5-high while armed clears the low-ready
// latch. A recovered system with the switch still high cannot re-arm.
module control_gate #(
    parameter integer LOW_HOLD_TICKS = 25000000,
    parameter integer HIGH_HOLD_TICKS = 25000000
) (
    input wire clk,
    input wire rst_n,
    input wire rc_valid,
    input wire sensor_ok,
    input wire [3:0] channel_count,
    input wire [15:0] ch3, ch5,
    output reg armed,
    output wire [7:0] inhibit_reason,
    // Event outputs describe the predicates BEFORE the clearing clock edge.
    // They are diagnostics only and never participate in gate decisions.
    output wire event_pulse,
    output wire [7:0] event_code,
    output reg [15:0] interruption_count,
    output reg [15:0] revoke_count,
    output reg [7:0] last_interruption_code,
    output reg [7:0] last_revoke_code
);
    wire ch3_bounds = ch3 >= 800 && ch3 <= 2200;
    wire ch5_bounds = ch5 >= 800 && ch5 <= 2200;
    wire rc_ok = rc_valid && channel_count >= 5 && channel_count <= 8 &&
                 ch3_bounds && ch5_bounds;
    wire throttle_low = ch3_bounds && ch3 <= 1100;
    wire switch_low = ch5 >= 800 && ch5 <= 1200;
    wire switch_high = ch5 >= 1800 && ch5 <= 2200;
    reg low_ready;
    reg [31:0] low_hold_count, high_hold_count;

    // bit 0: RC invalid, channel count outside 5..8, or CH3/CH5 out of bounds.
    // bit 1: CH5 is not high (also set during the intentional low preparation).
    // bit 2: sensor invalid. bit 3: disarmed, waiting for low/high confirmation.
    // Bits are independent reasons; a healthy switch-low preparation is not
    // an error, but it still inhibits virtual arming until high is confirmed.
    assign inhibit_reason = {4'b0000, !armed, !sensor_ok, !switch_high, !rc_ok};

    wire progress_present = armed || low_ready || (|low_hold_count) || (|high_hold_count);
    wire health_interrupt = (!rc_ok || !sensor_ok) && progress_present;
    wire armed_switch_interrupt = rc_ok && sensor_ok && armed && !switch_high;
    wire low_confirmation_interrupt = rc_ok && sensor_ok && !armed && !low_ready &&
        (|low_hold_count) && !(switch_low && throttle_low);
    wire preparation_interrupt = rc_ok && sensor_ok && !armed && low_ready &&
        !(switch_high && throttle_low) && !(switch_low && throttle_low);
    wire [1:0] event_stage = armed ? 2'd3 : low_ready ? 2'd2 : 2'd1;
    // bit 0 RC invalid, bit 1 sensor invalid, bit 2 switch departure,
    // bit 3 throttle not low during preparation, bits 5:4 interrupted stage
    // (1 low confirmation, 2 high-ready/confirmation, 3 armed), bits 7:6 zero.
    // Reasons follow FSM branch priority: a health clear records RC/sensor
    // only; switch/throttle reasons apply only to their normal clearing branch.
    // Expected switch-low preparation and an idle blocked startup are not events.
    assign event_pulse = rst_n &&
        (health_interrupt || armed_switch_interrupt || low_confirmation_interrupt || preparation_interrupt);
    assign event_code = event_pulse ? {2'b00, event_stage,
        ((low_confirmation_interrupt || preparation_interrupt) && !throttle_low),
        (armed_switch_interrupt || (low_confirmation_interrupt && !switch_low) ||
            (preparation_interrupt && !switch_low && !switch_high)),
        !sensor_ok, !rc_ok} : 8'd0;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            interruption_count <= 0;
            revoke_count <= 0;
            last_interruption_code <= 0;
            last_revoke_code <= 0;
        end else if (event_pulse) begin
            // Keep preparation interruptions and armed revocations separately.
            if (armed) begin
                if (revoke_count != 16'hFFFF) revoke_count <= revoke_count + 1'b1;
                last_revoke_code <= event_code;
            end else begin
                if (interruption_count != 16'hFFFF)
                    interruption_count <= interruption_count + 1'b1;
                last_interruption_code <= event_code;
            end
        end
    end

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            armed <= 0;
            low_ready <= 0;
            low_hold_count <= 0;
            high_hold_count <= 0;
        end else if (!rc_ok || !sensor_ok) begin
            armed <= 0;
            low_ready <= 0;
            low_hold_count <= 0;
            high_hold_count <= 0;
        end else if (armed) begin
            if (!switch_high) begin
                armed <= 0;
                low_ready <= 0;
                low_hold_count <= 0;
                high_hold_count <= 0;
            end
        end else if (!low_ready) begin
            high_hold_count <= 0;
            if (switch_low && throttle_low) begin
                if (LOW_HOLD_TICKS <= 1 || low_hold_count >= LOW_HOLD_TICKS-1) begin
                    low_ready <= 1;
                    low_hold_count <= 0;
                end else low_hold_count <= low_hold_count + 1'b1;
            end else low_hold_count <= 0;
        end else if (switch_high && throttle_low) begin
            if (HIGH_HOLD_TICKS <= 1 || high_hold_count >= HIGH_HOLD_TICKS-1) begin
                armed <= 1;
                high_hold_count <= 0;
            end else high_hold_count <= high_hold_count + 1'b1;
        end else if (switch_low && throttle_low) begin
            high_hold_count <= 0;
        end else begin
            low_ready <= 0;
            low_hold_count <= 0;
            high_hold_count <= 0;
        end
    end
endmodule
