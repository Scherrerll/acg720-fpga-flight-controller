`timescale 1ns/1ps
// 仅接收的 PPM 解码器，不包含电机输出。
// 遇到严格大于 3000 微秒的同步间隔时，原子提交前一帧；
// 一帧含 5..8 个通道且每个间隔均在闭区间 800..2200 微秒，才可接受。
// 非法间隔、第九通道、通道不足或新鲜度超时均撤销 valid；
// 最近提交的通道值保留，仅供诊断。
// 接收端按相邻上升沿间隔解码 PPM；通道输出数值单位为微秒。
module rc_ppm #(
    parameter integer CLK_HZ = 50000000,
    // 新鲜度以 clk 周期计，默认 50 MHz 下最后有效帧可保持 500 毫秒。
    parameter integer FRESH_TICKS = 25000000 // 默认 50 MHz 下为 500 毫秒，沿用 P2 参考值。
) (
    input wire clk,
    input wire rst_n,
    input wire ppm_in,
    output reg frame_update,
    output wire valid,
    output reg [3:0] channel_count,
    // ch1..ch8 均为微秒；frame_update 表示完整有效帧同拍提交，frame_sequence 每次提交递增。
    output reg [15:0] ch1, ch2, ch3, ch4, ch5,
    output reg [15:0] frame_sequence,
    output reg [15:0] ch6,ch7,ch8
);
    // CLK_HZ 必须为 1 MHz 的整数倍；本 ACG720 工程为 50 MHz。
    // 每微秒细分为整数个时钟周期，因此 CLK_HZ 必须是 1 MHz 的整数倍。
    localparam integer TICKS_PER_US = CLK_HZ / 1000000;
    localparam integer SUB_WIDTH = TICKS_PER_US > 1 ? $clog2(TICKS_PER_US) : 1;
    localparam [SUB_WIDTH-1:0] SUB_LAST = TICKS_PER_US - 1;

    // 异步输入先经两级寄存器同步，再对同步后的上升沿计时。
    reg [1:0] ppm_sync;
    reg ppm_last;
    // 每拍只处理短进位，避免使用 32 位组合除以 50。
    // 间隔计时在 3001 微秒饱和已足够，因为更长间隔都属于同步间隔。
    reg [11:0] interval_us;
    reg [SUB_WIDTH-1:0] interval_subticks;
    reg [31:0] fresh_ticks;
    reg frame_started, frame_bad;
    reg [3:0] slot_count;
    // 工作寄存器收集当前帧，已提交的通道值在下一有效整帧前保持不变。
    reg [15:0] work1, work2, work3, work4, work5, work6, work7, work8;

    wire ppm_rise = ppm_sync[1] && !ppm_last;
    // 计数器在间隔 N 拍的采样沿之前保存的是 N-1 拍，
    // 因此须加入当前拍进位，且不能对不足 1 微秒的边界作舍入：
    // 以 50 MHz 为例，799 微秒+49 拍无效，800 微秒有效，2200 微秒+1 拍无效；
    // 3000 微秒+1 拍属于同步间隔，而恰好 3000 微秒不属于同步间隔。
    // 将当前采样沿的一拍计入间隔；800 与 2200 微秒端点有效。
    wire edge_exact_us = interval_subticks == SUB_LAST;
    wire [11:0] edge_us = interval_us + (edge_exact_us ? 12'd1 : 12'd0);
    wire channel_interval = edge_us >= 12'd800 &&
        (edge_us < 12'd2200 || (edge_us == 12'd2200 && edge_exact_us));
    wire sync_interval = edge_us > 12'd3000 ||
        (edge_us == 12'd3000 && !edge_exact_us);
    // valid 仅表示新鲜度倒计时非零，失效时旧通道值仍可用于诊断。
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
                // 严格大于 3000 微秒才是同步间隔，并在此检查、提交前一帧。
                if (sync_interval) begin
                    // 仅接受 5 至 8 个全部合规的通道，所有输出在同一时钟沿更新。
                    if (frame_started && !frame_bad && slot_count >= 5 && slot_count <= 8) begin
                        ch1 <= work1; ch2 <= work2; ch3 <= work3;
                        ch4 <= work4; ch5 <= work5;
                        // 有效短帧中不存在的第 6 至 8 通道显式输出零。
                        ch6 <= slot_count>=6 ? work6 : 16'd0;
                        ch7 <= slot_count>=7 ? work7 : 16'd0;
                        ch8 <= slot_count>=8 ? work8 : 16'd0;
                        channel_count <= slot_count;
                        frame_sequence <= frame_sequence + 1'b1;
                        frame_update <= 1;
                        fresh_ticks <= FRESH_TICKS;
                    // 已开始但未通过整帧检查时撤销有效性，不覆盖旧的通道数值。
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
                        // 非法间隔或第九通道立即使帧失效，并将通道计数饱和到 9。
                        frame_bad <= 1;
                        slot_count <= 9; // 饱和到 9，禁止回绕成合法通道数。
                        fresh_ticks <= 0;
                        channel_count <= 0;
                    end
                end
            end
        end
    end
endmodule
