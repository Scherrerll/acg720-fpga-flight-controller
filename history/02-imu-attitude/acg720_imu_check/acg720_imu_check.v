// Bench-only ICM-42688-P SPI test. No ESC pins are assigned.
// IMU board: VCC/GND power (bench VCC currently 3.3 V into onboard LDO;
// not a final supply design), P7-1 SCK, P7-2 MOSI, P7-3 MISO, P7-4 CS.
// Board USB_UART (CH340E) TX pin M15, 115200 8N1.
module acg720_imu_check (
    input  wire clk50,
    input  wire imu_miso,
    output wire imu_sck,
    output wire imu_mosi,
    output wire imu_cs_n,
    output wire uart_tx,
    output reg  led2 = 1'b0,
    output wire led3
);
    reg [24:0] heartbeat = 0;
    always @(posedge clk50) begin
        if (heartbeat == 25'd24_999_999) begin
            heartbeat <= 0;
            led2 <= ~led2;
        end else heartbeat <= heartbeat + 1'b1;
    end

    reg spi_start = 0;
    reg [7:0] spi_command = 0, spi_write_byte = 0;
    reg [3:0] spi_bytes = 4'd2;
    wire spi_busy, spi_done;
    wire [103:0] spi_result;
    spi_mode3_master_1mhz spi_unit (
        .clk(clk50), .start(spi_start), .command(spi_command),
        .write_byte(spi_write_byte), .byte_count(spi_bytes),
        .miso(imu_miso), .sck(imu_sck), .mosi(imu_mosi), .cs_n(imu_cs_n),
        .busy(spi_busy), .done(spi_done), .result(spi_result)
    );

    localparam [3:0] BOOT=0, BANK_REQ=1, BANK_WAIT=2, ID_REQ=3,
        ID_WAIT=4, RETRY=5, PWR_REQ=6, PWR_WAIT=7,
        SENSOR_WAIT=8, DATA_REQ=9, DATA_WAIT=10, DATA_DELAY=11,
        PWR_VERIFY_REQ=12, PWR_VERIFY_WAIT=13,
        SOFT_RESET_REQ=14, SOFT_RESET_WAIT=15;
    reg [3:0] state = BOOT;
    reg [22:0] wait_ticks = 23'd5_000_000; // 100 ms power-up
    reg [7:0] who_am_i = 8'd0;
    reg reset_done = 1'b0;
    reg configured = 1'b0, sample_valid = 1'b0;
    reg [7:0] pwr_mgmt_read = 8'd0;
    reg [95:0] sensor_data = 96'd0;
    reg [7:0] sample_seq = 8'd0;
    assign led3 = (who_am_i == 8'h47) && configured && sample_valid;

    always @(posedge clk50) begin
        spi_start <= 1'b0;
        case (state)
            BOOT: if (wait_ticks == 0) state <= BANK_REQ;
                  else wait_ticks <= wait_ticks - 1'b1;
            BANK_REQ: if (!spi_busy) begin
                spi_command <= 8'h76; // REG_BANK_SEL write
                spi_write_byte <= 8'h00; // bank 0
                spi_bytes <= 4'd2;
                spi_start <= 1'b1;
                state <= BANK_WAIT;
            end
            BANK_WAIT: if (spi_done)
                state <= reset_done ? ID_REQ : SOFT_RESET_REQ;
            SOFT_RESET_REQ: if (!spi_busy) begin
                spi_command <= 8'h11; // DEVICE_CONFIG soft reset
                spi_write_byte <= 8'h01;
                spi_bytes <= 4'd2;
                spi_start <= 1'b1;
                state <= SOFT_RESET_WAIT;
            end
            SOFT_RESET_WAIT: if (spi_done) begin
                reset_done <= 1'b1;
                wait_ticks <= 23'd5_000_000; // >1 ms required; allow 100 ms
                state <= RETRY;
            end
            ID_REQ: if (!spi_busy) begin
                spi_command <= 8'hF5; // WHO_AM_I 0x75, read bit set
                spi_write_byte <= 8'h00;
                spi_bytes <= 4'd2;
                spi_start <= 1'b1;
                state <= ID_WAIT;
            end
            ID_WAIT: if (spi_done) begin
                who_am_i <= spi_result[7:0];
                if (spi_result[7:0] == 8'h47) state <= PWR_REQ;
                else begin
                    wait_ticks <= 23'd5_000_000;
                    state <= RETRY;
                end
            end
            RETRY: if (wait_ticks == 0) state <= BANK_REQ;
                   else wait_ticks <= wait_ticks - 1'b1;
            PWR_REQ: if (!spi_busy) begin
                spi_command <= 8'h4E; // PWR_MGMT0 write
                spi_write_byte <= 8'h0F; // gyro LN, accel LN
                spi_bytes <= 4'd2;
                spi_start <= 1'b1;
                state <= PWR_WAIT;
            end
            PWR_WAIT: if (spi_done) begin
                wait_ticks <= 23'd2_500_000; // 50 ms gyro startup
                state <= SENSOR_WAIT;
            end
            SENSOR_WAIT: if (wait_ticks == 0) state <= PWR_VERIFY_REQ;
                         else wait_ticks <= wait_ticks - 1'b1;
            PWR_VERIFY_REQ: if (!spi_busy) begin
                spi_command <= 8'hCE; // read PWR_MGMT0 0x4E
                spi_write_byte <= 8'h00;
                spi_bytes <= 4'd2;
                spi_start <= 1'b1;
                state <= PWR_VERIFY_WAIT;
            end
            PWR_VERIFY_WAIT: if (spi_done) begin
                pwr_mgmt_read <= spi_result[7:0];
                configured <= (spi_result[7:0] == 8'h0F);
                if (spi_result[7:0] == 8'h0F)
                    state <= DATA_REQ;
                else begin
                    sample_valid <= 1'b0;
                    wait_ticks <= 23'd5_000_000; // retry setup after 100 ms
                    state <= RETRY;
                end
            end
            DATA_REQ: if (!spi_busy) begin
                spi_command <= 8'h9F; // burst read from ACCEL_DATA_X1 0x1F
                spi_write_byte <= 8'h00;
                spi_bytes <= 4'd13; // address + 12 sensor bytes
                spi_start <= 1'b1;
                state <= DATA_WAIT;
            end
            DATA_WAIT: if (spi_done) begin
                sensor_data <= spi_result[95:0];
                sample_seq <= sample_seq + 1'b1;
                // Bench plausibility: at rest, gravity should exceed 0.25 g
                // on at least one axis at the default +/-16 g full scale.
                sample_valid <=
                    ($signed(spi_result[95:80]) > 16'sd512) ||
                    ($signed(spi_result[95:80]) < -16'sd512) ||
                    ($signed(spi_result[79:64]) > 16'sd512) ||
                    ($signed(spi_result[79:64]) < -16'sd512) ||
                    ($signed(spi_result[63:48]) > 16'sd512) ||
                    ($signed(spi_result[63:48]) < -16'sd512);
                wait_ticks <= 23'd500_000; // ~100 samples per second
                state <= DATA_DELAY;
            end
            DATA_DELAY: if (wait_ticks == 0) state <= DATA_REQ;
                        else wait_ticks <= wait_ticks - 1'b1;
            default: state <= BOOT;
        endcase
    end

    // 10 Hz UART reports: A5 5B status ID sequence 12 sensor bytes XOR.
    reg [22:0] report_div = 0;
    reg [1:0] send_state = 0;
    reg [4:0] send_idx = 0;
    reg [7:0] snap_status = 0, snap_id = 0, snap_seq = 0, snap_crc = 0;
    reg [95:0] snap_data = 0;
    reg tx_start = 0;
    reg [7:0] tx_data = 0;
    wire tx_busy;
    wire [7:0] status_now = {(who_am_i == 8'h47), configured, sample_valid,
                             pwr_mgmt_read[4:0]};
    wire [7:0] crc_now = status_now ^ who_am_i ^ sample_seq ^
        sensor_data[95:88] ^ sensor_data[87:80] ^
        sensor_data[79:72] ^ sensor_data[71:64] ^
        sensor_data[63:56] ^ sensor_data[55:48] ^
        sensor_data[47:40] ^ sensor_data[39:32] ^
        sensor_data[31:24] ^ sensor_data[23:16] ^
        sensor_data[15:8] ^ sensor_data[7:0];

    always @* begin
        case (send_idx)
            5'd0: tx_data=8'hA5; 5'd1: tx_data=8'h5B;
            5'd2: tx_data=snap_status;
            5'd3: tx_data=snap_id;
            5'd4: tx_data=snap_seq;
            5'd5: tx_data=snap_data[95:88];
            5'd6: tx_data=snap_data[87:80];
            5'd7: tx_data=snap_data[79:72];
            5'd8: tx_data=snap_data[71:64];
            5'd9: tx_data=snap_data[63:56];
            5'd10: tx_data=snap_data[55:48];
            5'd11: tx_data=snap_data[47:40];
            5'd12: tx_data=snap_data[39:32];
            5'd13: tx_data=snap_data[31:24];
            5'd14: tx_data=snap_data[23:16];
            5'd15: tx_data=snap_data[15:8];
            5'd16: tx_data=snap_data[7:0];
            5'd17: tx_data=snap_crc;
            default: tx_data=8'h00;
        endcase
    end

    always @(posedge clk50) begin
        tx_start <= 1'b0;
        if (report_div == 23'd4_999_999) report_div <= 0;
        else report_div <= report_div + 1'b1;
        case (send_state)
            2'd0: if (report_div == 23'd4_999_999) begin
                snap_status <= status_now;
                snap_id <= who_am_i;
                snap_seq <= sample_seq;
                snap_data <= sensor_data;
                snap_crc <= crc_now;
                send_idx <= 0;
                send_state <= 2'd1;
            end
            2'd1: if (!tx_busy) begin
                tx_start <= 1'b1;
                send_state <= 2'd2;
            end
            2'd2: if (tx_busy) send_state <= 2'd3;
            2'd3: if (!tx_busy) begin
                if (send_idx == 5'd17) send_state <= 2'd0;
                else begin
                    send_idx <= send_idx + 1'b1;
                    send_state <= 2'd1;
                end
            end
        endcase
    end
    uart_tx_115200 tx_unit (
        .clk(clk50), .start(tx_start), .data(tx_data),
        .tx(uart_tx), .busy(tx_busy)
    );
endmodule

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
    reg [1:0] state = 2'd0;
    reg [5:0] div = 6'd0;
    reg [7:0] bits_left = 8'd0;
    reg first_bit = 1'b0;
    reg [103:0] tx_shift = 104'd0, rx_shift = 104'd0;
    assign mosi = tx_shift[103];
    always @(posedge clk) begin
        done <= 1'b0;
        case (state)
            2'd0: if (start) begin
                tx_shift <= {command, write_byte, 88'd0};
                rx_shift <= 104'd0;
                bits_left <= {1'b0, byte_count, 3'b000};
                div <= 6'd24;
                sck <= 1'b1;
                cs_n <= 1'b0;
                busy <= 1'b1;
                first_bit <= 1'b1;
                state <= 2'd1;
            end
            2'd1: if (div == 0) begin
                sck <= 1'b0;
                if (first_bit) first_bit <= 1'b0;
                else tx_shift <= {tx_shift[102:0], 1'b0};
                div <= 6'd24;
                state <= 2'd2;
            end else div <= div - 1'b1;
            2'd2: if (div == 0) begin
                sck <= 1'b1;
                rx_shift <= {rx_shift[102:0], miso};
                div <= 6'd24;
                if (bits_left == 8'd1) state <= 2'd3;
                else begin
                    bits_left <= bits_left - 1'b1;
                    state <= 2'd1;
                end
            end else div <= div - 1'b1;
            2'd3: if (div == 0) begin
                result <= rx_shift;
                cs_n <= 1'b1;
                busy <= 1'b0;
                done <= 1'b1;
                state <= 2'd0;
            end else div <= div - 1'b1;
        endcase
    end
endmodule

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
