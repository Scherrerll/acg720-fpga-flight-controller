// 共用串行底层：包含 SPI 模式 3 主机和 115200 波特 UART 发送器，均按固定 50 MHz 输入时钟设计。
// SPI：空闲时 start 锁存 command/write_byte，byte_count 为总字节数；result 为本次接收移位结果。
// SCK 空闲为高、下降沿更新 MOSI、上升沿采样 MISO；每半周期 25 拍，串行频率为 1 MHz。
// 此主机无运行复位端口，只使用上电初值；调用方须在 busy=0 时发起事务，并等片选保护期结束。
module spi_mode3_master_1mhz (
    input wire clk,
    input wire start,
    input wire [7:0] command,
    input wire [7:0] write_byte,
    input wire [3:0] byte_count,
    input wire miso,
    output reg sck = 1'b1,
    output wire mosi,
    output reg cs_n = 1'b1,
    output reg busy = 1'b0,
    output reg done = 1'b0,
    output reg [103:0] result = 104'd0
);
    // 每次 SPI 事务结束后，片选至少保持高电平 10 微秒。
    // 原有较短间隔并未被确认违反数据手册；此处保留 A/B 诊断方案，
    // 用于检查通信对事务间隔的敏感性。
    reg [2:0] state = 3'd0;
    reg [8:0] cs_high_count = 9'd0;
    reg [5:0] div = 6'd0;
    reg [7:0] bits_left = 8'd0;
    reg first_bit = 1'b0;
    reg [103:0] tx_shift = 104'd0, rx_shift = 104'd0;
    assign mosi = tx_shift[103];
    always @(posedge clk) begin
        done <= 1'b0;
        case (state)
            // 空闲态接收整笔请求；首位先保持，后续下降沿再移出下一位。
            3'd0: if (start) begin
                tx_shift <= {command, write_byte, 88'd0};
                rx_shift <= 104'd0;
                bits_left <= {1'b0, byte_count, 3'b000};
                div <= 6'd24;
                sck <= 1'b1;
                cs_n <= 1'b0;
                busy <= 1'b1;
                first_bit <= 1'b1;
                state <= 3'd1;
            end
            3'd1: if (div == 0) begin
                sck <= 1'b0;
                if (first_bit) first_bit <= 1'b0;
                else tx_shift <= {tx_shift[102:0], 1'b0};
                div <= 6'd24;
                state <= 3'd2;
            end else div <= div - 1'b1;
            // 每个上升沿接收一位，累计到 byte_count 指定的总位数后锁存结果并拉高片选。
            3'd2: if (div == 0) begin
                sck <= 1'b1;
                rx_shift <= {rx_shift[102:0], miso};
                div <= 6'd24;
                if (bits_left == 8'd1) state <= 3'd3;
                else begin
                    bits_left <= bits_left - 1'b1;
                    state <= 3'd1;
                end
            end else div <= div - 1'b1;
            3'd3: if (div == 0) begin
                result <= rx_shift;
                cs_n <= 1'b1;
                // 片选高电平保护间隔结束前持续置 busy，防止上层请求状态
                // 过早发出只持续一个时钟的 start 脉冲。
                busy <= 1'b1;
                done <= 1'b1;
                cs_high_count <= 9'd499;
                state <= 3'd4;
            end else div <= div - 1'b1;
            3'd4: if (cs_high_count == 0) begin
                busy <= 1'b0;
                state <= 3'd0;
            end else cs_high_count <= cs_high_count - 1'b1;
        endcase
    end
endmodule

// UART 单字节发送器：start 仅在空闲时接受，data 随请求锁存，busy 持续到停止位输出结束。
// 固定 50 MHz 时钟每位 434 拍，近似 115200 波特；格式为 1 起始位、8 数据位（低位先发）、1 停止位。
// 无运行复位端口，tx 上电为空闲高电平；忙时的新 start 不排队。
module uart_tx_115200 (
    input wire clk,
    input wire start,
    input wire [7:0] data,
    output reg tx = 1'b1,
    output reg busy = 1'b0
);
    reg [8:0] baud = 0;
    reg [3:0] bit_index = 0;
    reg [7:0] shift = 0;
    always @(posedge clk) begin
        if (!busy) begin
            tx <= 1'b1;
            if (start) begin
                busy <= 1'b1;
                tx <= 1'b0;
                baud <= 9'd433;
                bit_index <= 0;
                shift <= data;
            end
        end else if (baud != 0) baud <= baud - 1'b1;
        // 完成起始位计时后逐位发送，再维持一位停止高电平，最后释放 busy。
        else begin
            baud <= 9'd433;
            if (bit_index < 4'd8) begin
                tx <= shift[0];
                shift <= {1'b0, shift[7:1]};
                bit_index <= bit_index + 1'b1;
            end else if (bit_index == 4'd8) begin
                tx <= 1'b1;
                bit_index <= 4'd9;
            end else busy <= 1'b0;
        end
    end
endmodule
