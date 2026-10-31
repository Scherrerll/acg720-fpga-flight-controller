`timescale 1ns/1ps
// 虚拟台架解锁状态机；本模块没有电机输出引脚。
// 在 50 MHz 下，默认要求 CH5 连续低位 0.5 秒，再连续高位 0.5 秒；
// 两个确认阶段都必须保持低油门、有效遥控和健康传感器。
// 任何健康故障，或解锁后 CH5 离开高位，都会清除已完成低位确认的记忆；
// 因此故障恢复时开关若仍在高位，系统不会自动重新解锁。
// 飞行解锁门控：生成解锁状态、禁止原因和中断诊断，不在本模块直接输出 PWM。
// 输入 ch3、ch5 为微秒脉宽；保持时间参数以 clk 周期计，实例可分别覆盖两个默认确认时长。
module control_gate #(
    // 保持时长以 clk 周期计；50 MHz 下默认低位、高位各连续保持 0.5 秒。
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
    // 事件输出描述清除状态的时钟沿到来之前已成立的中断条件。
    // 事件仅供诊断，不参与解锁门控决策。
    output wire event_pulse,
    output wire [7:0] event_code,
    output reg [15:0] interruption_count,
    output reg [15:0] revoke_count,
    output reg [7:0] last_interruption_code,
    output reg [7:0] last_revoke_code
);
    // CH3 为油门、CH5 为解锁开关，输入数值单位均为微秒。
    wire ch3_bounds = ch3 >= 800 && ch3 <= 2200;
    wire ch5_bounds = ch5 >= 800 && ch5 <= 2200;
    wire rc_ok = rc_valid && channel_count >= 5 && channel_count <= 8 &&
                 ch3_bounds && ch5_bounds;
    // 低油门只参与解锁准备；解锁后仍由 RC、传感器和 CH5 高位维持门控。
    wire throttle_low = ch3_bounds && ch3 <= 1100;
    wire switch_low = ch5 >= 800 && ch5 <= 1200;
    wire switch_high = ch5 >= 1800 && ch5 <= 2200;
    // low_ready 记住已完成的低位确认；必须先低位确认，再高位确认。
    reg low_ready;
    reg [31:0] low_hold_count, high_hold_count;

    // 位 0：遥控无效、通道数不在 5..8，或 CH3/CH5 越界。
    // 位 1：CH5 不在高位；正常低位准备期间也会置位。
    // 位 2：传感器无效；位 3：尚未解锁，等待低位/高位确认。
    // 各位分别表示禁止解锁的原因；健康状态下的低位准备并非故障，
    // 但在高位确认完成前仍会禁止虚拟解锁。
    // 各禁止原因独立置位，包含正常准备阶段尚未完成解锁的情况。
    assign inhibit_reason = {4'b0000, !armed, !sensor_ok, !switch_high, !rc_ok};

    // 只有已有准备进度或已经解锁时，清除条件才形成中断事件。
    wire progress_present = armed || low_ready || (|low_hold_count) || (|high_hold_count);
    wire health_interrupt = (!rc_ok || !sensor_ok) && progress_present;
    wire armed_switch_interrupt = rc_ok && sensor_ok && armed && !switch_high;
    wire low_confirmation_interrupt = rc_ok && sensor_ok && !armed && !low_ready &&
        (|low_hold_count) && !(switch_low && throttle_low);
    wire preparation_interrupt = rc_ok && sensor_ok && !armed && low_ready &&
        !(switch_high && throttle_low) && !(switch_low && throttle_low);
    wire [1:0] event_stage = armed ? 2'd3 : low_ready ? 2'd2 : 2'd1;
    // 事件码位 0：遥控无效；位 1：传感器无效；位 2：开关离开要求位置；
    // 位 3：准备期间油门不低；位 5:4：被中断的阶段，
    // 其中 1=低位确认、2=等待/确认高位、3=已解锁；位 7:6 固定为零。
    // 事件原因遵循状态机分支优先级：健康故障清除时只记录遥控/传感器原因，
    // 开关和油门原因只在各自的正常清除分支中记录。
    // 预期的低位准备以及启动后尚无准备进度的阻塞状态不产生事件。
    // 事件编码取清除时钟沿之前的条件，仅供诊断，不反向参与门控。
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
            // 准备中断与已解锁撤销分开计数；计数到 65535 后饱和。
            // 准备中断与已解锁后的撤销分别统计，便于追溯发生阶段。
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

    // 解锁顺序依次为低位确认、等待高位和高位确认；健康故障优先清空所有阶段进度。
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            armed <= 0;
            low_ready <= 0;
            low_hold_count <= 0;
            high_hold_count <= 0;
        // 健康条件丢失会清空全部准备记忆，恢复后仍需重新完成低位确认。
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
        // 低位确认期间任一准备条件不满足，连续计时立即归零。
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
        // 低位准备完成后可继续停留在低位；仅将高位确认计时清零。
        end else if (switch_low && throttle_low) begin
            high_hold_count <= 0;
        end else begin
            low_ready <= 0;
            low_hold_count <= 0;
            high_hold_count <= 0;
        end
    end
endmodule
