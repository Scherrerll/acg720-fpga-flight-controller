// 在样本交付给使用方之前，拒收可检测的传输、配置及整帧哨兵错误。
// 本检查不等同于 SPI 的 CRC，无法识别所有仍落在合法数值范围内的损坏。
// raw 为 ax/ay/az/gx/gy/gz 六个 16 位字段；sample_valid 为单拍事件，dt 和 age 均以 clk 周期计。
// 默认连续拒收上限 3、恢复样本数 5、输入流水延迟 3 拍；flight_core 的流水线将
// USE_PRECHECKED 覆盖为 1、BAD_STREAK_REVOKES_LINK 覆盖为 0，其他参数使用声明默认值。
module imu_checked_guard_pipelined #(
    parameter integer MAX_BAD_STREAK = 3,
    parameter integer RECOVERY_SAMPLES = 5,
    parameter integer INPUT_DELAY_TICKS = 3,
    parameter integer USE_PRECHECKED = 0,
    // 独立使用时，默认连续短串拒收会撤销链路资格；飞行集成可允许拒收记录
    // 而保持既有链路资格。源端静默不再撤销链路资格，
    // 但无论哪种模式，拒收都不发布样本，也不刷新样本年龄。
    parameter integer BAD_STREAK_REVOKES_LINK = 1
) (
    input wire clk, input wire rst_n,
    input wire record_ready,
    // 原始记录的消费时刻：原始 record_ready 延迟一个时钟，供真实 dt 快照使用。
    input wire origin_record_ready,
    input wire [7:0] who, pwr,
    input wire [95:0] raw,
    input wire [7:0] extra_reason,
    // 与时间检查快照对应的已寄存基础检查结果，涵盖芯片标识、
    // 电源/配置/状态以及原始整帧哨兵检查；时间检查拒收原因仍在
    // extra_reason 中。USE_PRECHECKED 默认 0，保留独立使用时的原有检查语义。
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

// DIAG_TAP_BEGIN
    output wire diag_qualified,
    output wire [31:0] diag_recovery_count,
// DIAG_TAP_END
    output reg [31:0] age_ticks = 32'hffffffff
);

// DIAG_TAP_BEGIN
    assign diag_qualified=qualified;
    assign diag_recovery_count=recovery_count;
// DIAG_TAP_END
    reg seen_good = 0, qualified = 0;
    // 不设置基于年龄的过期状态；源端静默期间也不发布新的已接受样本。

    reg [31:0] origin_dt=0,origin_recovery_count=0;
    reg origin_timeout=1,origin_qualified=0;
    reg [31:0] recovery_count = 0;
    // BMI 原生有符号端点是合法测量值，不能当作 ICM 的哨兵编码。
    wire invalid_axis=1'b0;
    wire [7:0] base_reason = {3'b000, invalid_axis,
        (raw == {96{1'b1}}), (raw == 96'd0),
        (pwr != 8'h0F), (who != 8'h1e)};
    wire [7:0] reason = base_reason | extra_reason;
    wire record_ok = USE_PRECHECKED ? (checked_base_ok && extra_reason == 0) : (reason == 0);
    // 源端静默不撤销已初始化的样本时期；上电后尚未见合格样本时仍无资格。
    assign stale = !seen_good;
    // 原有模式下，只要阈值非零，qualified 成立就意味着 bad_streak 尚未达到阈值：
    // 合格记录会清空连续拒收计数，达到上限的拒收记录会在同一时钟沿
    // 清除 qualified；资格快照只在合格记录到来时恢复。
    // 保留阈值为零的接口语义：链路始终不可用。
    assign link_usable = (MAX_BAD_STREAK != 0) && qualified && !stale;
    always @(posedge clk) begin
        if (!rst_n) begin
            sample_valid <= 0;
            accepted_raw <= 0;
            sample_dt_ticks <= 0;
            accepted_count <= 0;
            rejected_count <= 0;
            bad_streak <= 0;
            age_ticks <= 32'hffffffff;
            seen_good <= 0;
            qualified <= 0;
            recovery_count <= 0;
            reject_reason <= 0;
            origin_dt<=0; origin_recovery_count<=0; origin_timeout<=1; origin_qualified<=0;
        end else begin
            sample_valid <= 0;
            // 年龄计数饱和，防止旧样本因计数回绕而被误认为新样本。
            if (age_ticks != 32'hFFFFFFFF) age_ticks <= age_ticks + 1'b1;
            // 年龄仅用于诊断元数据和真实积分间隔，不再作为链路许可门控。
            if (origin_record_ready) begin
                origin_timeout <= !seen_good;
                origin_dt <= !seen_good ? 32'd0 :
                    age_ticks == 32'hffffffff ? 32'hffffffff : age_ticks+1'b1;
                origin_qualified <= qualified; origin_recovery_count <= recovery_count;
            end
            // 按到达源记录时保存的资格/时间快照处理本次结果，防止验证延迟改变恢复计数和 dt。
            if (record_ready) begin
                reject_reason <= reason;
                if (record_ok) begin
                    // 只有首个已接受源样本没有前一间隔；发生间断后绝不伪造 dt。
                    sample_dt_ticks <= origin_dt;
                    accepted_raw <= raw;
                    sample_valid <= 1;
                    if (accepted_count != 32'hFFFFFFFF)
                        accepted_count <= accepted_count + 1'b1;
                    seen_good <= 1;
                    // 将验证流水线延迟计入诊断年龄与后续真实样本间隔。
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
                    // 拒收时保持最近合格值，但绝不产生新的 sample_valid 脉冲。
                    if (rejected_count != 32'hFFFFFFFF)
                        rejected_count <= rejected_count + 1'b1;
                    if (bad_streak != 32'hFFFFFFFF)
                        bad_streak <= bad_streak + 1'b1;
                    recovery_count <= 0;
                    if (BAD_STREAK_REVOKES_LINK && bad_streak + 1 >= MAX_BAD_STREAK) qualified <= 0;
                end
            end
        end
    end
endmodule
