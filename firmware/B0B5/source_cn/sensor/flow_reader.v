// PMW3901 原始计数读取器，提取自此前通过台架验证的诊断程序。
// flow_dx/flow_dy 是有符号 16 位原始增量计数，不是厘米、速度或位置；
// 本层不做光学标定和旋转补偿，零增量也作为有效新样本发布。
// clk50 为 50 MHz，rst_n 为低有效异步复位；flow_* 为 SPI 与传感器电源接口。
// sample_valid 每份完整样本脉冲一拍；sample_sequence 按 32 位回绕，good_count 饱和计数。
// source_age_ticks、source_dt_ticks、STALE_TICKS 均以 20 ns 时钟拍为单位；首样本间隔为零。
// configured 表示初始化写表完成；who 为芯片 ID，squal/flow_motion 保留原始寄存器值。
// SPI 没有 CRC：link_ok 只说明启动 ID 正确且已完成样本足够新鲜，不能证明每字节物理传输无误。
// error_count 仅累计启动 ID 对不匹配和非法状态恢复，达到 32'hFFFFFFFF 后保持。
// 保留 Bitcraze 上游的完整 73 项初始化表及原 SPI 模式 3 时序。
module flow_reader #(
    parameter integer STALE_TICKS = 5_000_000
)(
    input wire clk50, input wire rst_n, input wire flow_miso,
    output wire flow_sck, output wire flow_mosi, output wire flow_cs_n,
    output reg flow_pwr_en = 0,
    output wire signed [15:0] flow_dx, output wire signed [15:0] flow_dy,
    output wire [7:0] squal, output wire [7:0] flow_motion, output wire [7:0] who,
    output wire configured, output wire link_ok,
    output reg sample_valid = 0, output wire [31:0] sample_sequence,
    output reg [31:0] good_count = 0,
    output reg [31:0] source_age_ticks = 32'hFFFFFFFF,
    output reg [31:0] source_dt_ticks = 0, output reg [31:0] error_count = 0
);
    reg spi_start = 0, spi_read = 1'b1;
    reg [7:0] spi_address = 0, spi_write_data = 0;
    wire spi_busy, spi_done;
    wire [7:0] spi_result;
    pmw3901_spi_mode3 spi_unit (
        .clk(clk50), .rst_n(rst_n), .start(spi_start), .read_op(spi_read),
        .address(spi_address), .write_data(spi_write_data),
        .miso(flow_miso), .sck(flow_sck), .mosi(flow_mosi),
        .cs_n(flow_cs_n), .busy(spi_busy), .done(spi_done),
        .result(spi_result)
    );

    // 按 Bitcraze 上游驱动的次序执行 73 次性能寄存器写入；表项高字节为地址、低字节为数据。
    reg [15:0] init_rom [0:72];
`include "sensor/pmw3901_init.vh"
    reg [6:0] init_index = 0;
    wire [15:0] init_entry = init_rom[init_index];

    // 主状态机依次执行上电等待、双 ID 检查、软复位、清读、初始化表和周期采样。
    // ID 错误等待 100 ms 后重试；正常采样轮之间等待 20 ms。
    localparam BOOT=0, POWER_WAIT=1, ID_REQ=2, ID_WAIT=3,
        INV_REQ=4, INV_WAIT=5, RETRY_WAIT=6, RESET_REQ=7,
        RESET_WAIT=8, RESET_DELAY=9, CLEAR_REQ=10, CLEAR_WAIT=11,
        CLEAR_DELAY=12, INIT_REQ=13, INIT_WAIT=14, INIT_GAP=15,
        MOTION_REQ=16, MOTION_WAIT=17, MOTION_GAP=18;
    reg [4:0] state = BOOT;
    reg [22:0] wait_ticks = 23'd50_000;
    reg [7:0] chip_id = 0, inverse_id = 0;
    reg [7:0] clear_addr = 8'h02, motion_addr = 8'h02;
    reg initialized = 1'b0;
    reg [7:0] motion = 0, dx_lo = 0, dx_hi = 0,
              dy_lo = 0, dy_hi = 0, quality = 0;
    reg [31:0] sample_seq = 0;
    // 先暂存 0x02..0x06 的运动及 X/Y 字节，读到 0x07 质量值后一次性发布同一组样本。
    reg [7:0] pending_motion = 0, pending_xlo = 0, pending_xhi = 0,
              pending_ylo = 0, pending_yhi = 0;
    wire id_ok = chip_id == 8'h49 && inverse_id == 8'hB6;
    assign who = chip_id;
    assign configured = initialized;
    assign flow_dx = $signed({dx_hi, dx_lo});
    assign flow_dy = $signed({dy_hi, dy_lo});
    assign squal = quality;
    assign flow_motion = motion;
    assign sample_sequence = sample_seq;
    reg sample_seen = 0;
    // 只在已见完整样本、初始化完成、ID 匹配且样本龄未超限时声明链路可用。
    assign link_ok = id_ok && initialized && sample_seen &&
                     source_age_ticks < STALE_TICKS;

    always @(posedge clk50 or negedge rst_n) begin
        if (!rst_n) begin
            spi_start <= 0; spi_read <= 1; spi_address <= 0; spi_write_data <= 0;
            state <= BOOT; wait_ticks <= 23'd50_000; flow_pwr_en <= 0;
            init_index <= 0; chip_id <= 0; inverse_id <= 0; clear_addr <= 8'h02;
            motion_addr <= 8'h02; initialized <= 0; motion <= 0;
            dx_lo <= 0; dx_hi <= 0; dy_lo <= 0; dy_hi <= 0; quality <= 0;
            pending_motion <= 0; pending_xlo <= 0; pending_xhi <= 0;
            pending_ylo <= 0; pending_yhi <= 0; sample_seq <= 0;
            sample_valid <= 0; sample_seen <= 0; source_age_ticks <= 32'hFFFFFFFF;
            source_dt_ticks <= 0; error_count <= 0; good_count <= 0;
        end else begin
        sample_valid <= 0;
        if (source_age_ticks != 32'hFFFFFFFF) source_age_ticks <= source_age_ticks + 1'b1;
        spi_start <= 1'b0;
        case (state)
            BOOT: if (wait_ticks == 0) begin
                flow_pwr_en <= 1'b1;
                wait_ticks <= 23'd5_000_000;
                state <= POWER_WAIT;
            end else wait_ticks <= wait_ticks - 1'b1;
            POWER_WAIT: if (wait_ticks == 0) state <= ID_REQ;
                        else wait_ticks <= wait_ticks - 1'b1;
            ID_REQ: if (!spi_busy) begin
                spi_read <= 1'b1;
                spi_address <= 8'h00;
                spi_start <= 1'b1;
                state <= ID_WAIT;
            end
            ID_WAIT: if (spi_done) begin
                chip_id <= spi_result;
                state <= INV_REQ;
            end
            INV_REQ: if (!spi_busy) begin
                spi_read <= 1'b1;
                spi_address <= 8'h5F;
                spi_start <= 1'b1;
                state <= INV_WAIT;
            end
            INV_WAIT: if (spi_done) begin
                inverse_id <= spi_result;
                if (chip_id == 8'h49 && spi_result == 8'hB6)
                    state <= RESET_REQ;
                else begin
                    if (error_count != 32'hFFFFFFFF) error_count <= error_count + 1'b1;
                    wait_ticks <= 23'd5_000_000;
                    state <= RETRY_WAIT;
                end
            end
            RETRY_WAIT: if (wait_ticks == 0) state <= ID_REQ;
                        else wait_ticks <= wait_ticks - 1'b1;
            RESET_REQ: if (!spi_busy) begin
                spi_read <= 1'b0;
                spi_address <= 8'h3A;
                spi_write_data <= 8'h5A;
                spi_start <= 1'b1;
                state <= RESET_WAIT;
            end
            RESET_WAIT: if (spi_done) begin
                wait_ticks <= 23'd250_000; // 软复位恢复等待 5 ms
                state <= RESET_DELAY;
            end
            RESET_DELAY: if (wait_ticks == 0) state <= CLEAR_REQ;
                         else wait_ticks <= wait_ticks - 1'b1;
            CLEAR_REQ: if (!spi_busy) begin
                spi_read <= 1'b1;
                spi_address <= clear_addr;
                spi_start <= 1'b1;
                state <= CLEAR_WAIT;
            end
            CLEAR_WAIT: if (spi_done) begin
                if (clear_addr == 8'h06) begin
                    wait_ticks <= 23'd50_000; // 清读后等待 1 ms 再开始配置
                    state <= CLEAR_DELAY;
                end else begin
                    clear_addr <= clear_addr + 1'b1;
                    state <= CLEAR_REQ;
                end
            end
            CLEAR_DELAY: if (wait_ticks == 0) state <= INIT_REQ;
                         else wait_ticks <= wait_ticks - 1'b1;
            INIT_REQ: if (!spi_busy) begin
                spi_read <= 1'b0;
                spi_address <= init_entry[15:8];
                spi_write_data <= init_entry[7:0];
                spi_start <= 1'b1;
                state <= INIT_WAIT;
            end
            INIT_WAIT: if (spi_done) begin
                if (init_index == 7'd72) begin
                    initialized <= 1'b1;
                    motion_addr <= 8'h02;
                    wait_ticks <= 23'd1_000_000;
                    state <= MOTION_GAP;
                end else begin
                    init_index <= init_index + 1'b1;
                    wait_ticks <= init_index == 7'd58 ?
                        23'd5_000_000 : 23'd10_000; // 表项 58 后等待 100 ms，其余项后等待 200 us
                    state <= INIT_GAP;
                end
            end
            INIT_GAP: if (wait_ticks == 0) state <= INIT_REQ;
                      else wait_ticks <= wait_ticks - 1'b1;
            MOTION_REQ: if (!spi_busy) begin
                spi_read <= 1'b1;
                spi_address <= motion_addr;
                spi_start <= 1'b1;
                state <= MOTION_WAIT;
            end
            // 各寄存器分次 SPI 读取；仅末地址完成时更新公开数据、新鲜度和样本计数。
            MOTION_WAIT: if (spi_done) begin
                case (motion_addr)
                    8'h02: pending_motion <= spi_result;
                    8'h03: pending_xlo <= spi_result;
                    8'h04: pending_xhi <= spi_result;
                    8'h05: pending_ylo <= spi_result;
                    8'h06: pending_yhi <= spi_result;
                    8'h07: begin
                        motion <= pending_motion;
                        dx_lo <= pending_xlo;
                        dx_hi <= pending_xhi;
                        dy_lo <= pending_ylo;
                        dy_hi <= pending_yhi;
                        quality <= spi_result;
                    end
                endcase
                if (motion_addr == 8'h07) begin
                    motion_addr <= 8'h02;
                    sample_seq <= sample_seq + 1'b1;
                    sample_valid <= 1'b1;
                    sample_seen <= 1'b1;
                    if (good_count != 32'hFFFFFFFF) good_count <= good_count + 1'b1;
                    source_dt_ticks <= sample_seen ? source_age_ticks + 1'b1 : 32'd0;
                    source_age_ticks <= 0;
                    wait_ticks <= 23'd1_000_000; // 轮询间隔 20 ms，整体采样率约 50 Hz
                    state <= MOTION_GAP;
                end else begin
                    motion_addr <= motion_addr + 1'b1;
                    state <= MOTION_REQ;
                end
            end
            MOTION_GAP: if (wait_ticks == 0) state <= MOTION_REQ;
                        else wait_ticks <= wait_ticks - 1'b1;
            default: begin
                state <= BOOT; wait_ticks <= 23'd50_000; initialized <= 0;
                sample_seen <= 0; source_age_ticks <= 32'hFFFFFFFF;
                init_index <= 0; clear_addr <= 8'h02;
                if (error_count != 32'hFFFFFFFF) error_count <= error_count + 1'b1;
            end
        endcase
        end
    end

endmodule

// PMW3901 单寄存器 SPI 模式 3 主机：SCK 空闲高，下降沿送位、上升沿采 MISO，最高位先行。
// clk 取 50 MHz；仅 IDLE 接受 start，read_op=1 读、=0 写，地址只使用低 7 位。
// 一次事务发送地址字节和数据字节；读操作的数据阶段发零，result 保存收到的数据字节。
// busy 覆盖整个片选有效期，done 在片选释放时脉冲一拍；rst_n 为低有效异步复位。
module pmw3901_spi_mode3 (
    input wire clk,
    input wire rst_n,
    input wire start,
    input wire read_op,
    input wire [7:0] address,
    input wire [7:0] write_data,
    input wire miso,
    output reg sck = 1'b1,
    output reg mosi = 1'b0,
    output reg cs_n = 1'b1,
    output reg busy = 1'b0,
    output reg done = 1'b0,
    output reg [7:0] result = 0
);
    // 片选建立、地址/数据间隔各约 50 us；数据结束后约 100 us 才释放片选。
    // 位时序通过 FALL/RISE/BETWEEN 的计数等待产生，保持原模式 3 的边沿次序。
    localparam IDLE=0, SETUP=1, FALL=2, RISE=3,
               ADDRESS_DELAY=4, FINISH_DELAY=5, BETWEEN=6;
    reg [2:0] state = IDLE;
    reg [13:0] ticks = 0;
    reg [7:0] tx_shift = 0, rx_shift = 0, pending_data = 0;
    reg [2:0] bit_idx = 0;
    reg data_phase = 0, pending_read = 1;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            sck <= 1; mosi <= 0; cs_n <= 1; busy <= 0; done <= 0; result <= 0;
            state <= IDLE; ticks <= 0; tx_shift <= 0; rx_shift <= 0;
            pending_data <= 0; bit_idx <= 0; data_phase <= 0; pending_read <= 1;
        end else begin
        done <= 1'b0;
        case (state)
            IDLE: if (start) begin
                cs_n <= 1'b0;
                sck <= 1'b1;
                mosi <= 1'b0;
                tx_shift <= {~read_op, address[6:0]};
                pending_data <= write_data;
                pending_read <= read_op;
                rx_shift <= 0;
                data_phase <= 1'b0;
                bit_idx <= 3'd7;
                ticks <= 14'd2499; // 拉低片选后等待 50 us 再发送地址
                busy <= 1'b1;
                state <= SETUP;
            end
            SETUP: if (ticks == 0) state <= FALL;
                   else ticks <= ticks - 1'b1;
            FALL: begin
                sck <= 1'b0;
                mosi <= tx_shift[7];
                ticks <= 14'd24;
                state <= RISE;
            end
            RISE: if (ticks == 0) begin
                sck <= 1'b1;
                rx_shift <= {rx_shift[6:0], miso};
                tx_shift <= {tx_shift[6:0], 1'b0};
                if (bit_idx == 0) begin
                    if (!data_phase) begin
                        data_phase <= 1'b1;
                        bit_idx <= 3'd7;
                        tx_shift <= pending_read ? 8'h00 : pending_data;
                        ticks <= 14'd2499;
                        state <= ADDRESS_DELAY;
                    end else begin
                        result <= {rx_shift[6:0], miso};
                        ticks <= 14'd4999; // 数据完成后等待 100 us 再释放片选
                        state <= FINISH_DELAY;
                    end
                end else begin
                    bit_idx <= bit_idx - 1'b1;
                    ticks <= 14'd24;
                    state <= BETWEEN;
                end
            end else ticks <= ticks - 1'b1;
            BETWEEN: if (ticks == 0) state <= FALL;
                     else ticks <= ticks - 1'b1;
            ADDRESS_DELAY: if (ticks == 0) state <= FALL;
                           else ticks <= ticks - 1'b1;
            FINISH_DELAY: if (ticks == 0) begin
                cs_n <= 1'b1;
                busy <= 1'b0;
                done <= 1'b1;
                state <= IDLE;
            end else ticks <= ticks - 1'b1;
            default: state <= IDLE;
        endcase
        end
    end
endmodule

