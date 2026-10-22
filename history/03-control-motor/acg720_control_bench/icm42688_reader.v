// Explicitly configured, polling bench reader. Internal ODR 200 Hz, UI LPF
// bandwidth 40 Hz, output polling ~100 Hz. Not a flight-rate FIFO driver.
module icm42688_reader #(
    parameter integer BOOT_TICKS=5000000,
    parameter integer SETTLE_TICKS=2500000,
    parameter integer POLL_TICKS=500000
) (
    input wire clk, rst_n, miso,
    output wire sck, mosi, cs_n,
    output reg record_ready=0,
    output reg [95:0] record_raw=0,
    output reg [7:0] record_who=0,
    output reg [7:0] record_pwr=0,
    output reg [7:0] record_gyro=0,
    output reg [7:0] record_accel=0,
    output reg [7:0] record_filter=0,
    output reg [7:0] record_status=0
);
    localparam BOOT=0, BANK=1, BANK_WAIT=2, RESET=3, RESET_WAIT=4,
        ID=5, ID_WAIT=6, WRITE_CFG=7, CFG_WAIT=8, SETTLE=9,
        STATUS=10, STATUS_WAIT=11, DATA=12, DATA_WAIT=13,
        WHO=14, WHO_WAIT=15, READ_CFG=16, READ_CFG_WAIT=17, DELAY=18;
    reg [4:0] state=BOOT;
    reg [31:0] wait_ticks=BOOT_TICKS;
    reg reset_done=0;
    reg [2:0] config_index=0;
    reg [1:0] config_fail_streak=0;
    reg spi_start=0;
    reg [7:0] command=0, write_byte=0;
    reg [3:0] byte_count=2;
    wire busy, done;
    wire [103:0] result;
    spi_mode3_master_1mhz spi(.clk(clk),.start(spi_start),.command(command),
        .write_byte(write_byte),.byte_count(byte_count),.miso(miso),
        .sck(sck),.mosi(mosi),.cs_n(cs_n),.busy(busy),.done(done),.result(result));
    always @(posedge clk) begin
        spi_start <= 0; record_ready <= 0;
        if (!rst_n) begin
            state <= BOOT; wait_ticks <= BOOT_TICKS; reset_done <= 0; config_index <= 0; config_fail_streak <= 0;
            record_raw <= 0; record_who <= 0; record_pwr <= 0;
            record_gyro <= 0; record_accel <= 0; record_filter <= 0; record_status <= 0;
        end else case(state)
            BOOT: if (wait_ticks == 0) state <= BANK;
                  else wait_ticks <= wait_ticks-1'b1;
            BANK: if (!busy) begin
                command <= 8'h76; write_byte <= 0; byte_count <= 2;
                spi_start <= 1; state <= BANK_WAIT;
            end
            BANK_WAIT: if (done) state <= reset_done ? ID : RESET;
            RESET: if (!busy) begin
                command <= 8'h11; write_byte <= 1; byte_count <= 2;
                spi_start <= 1; state <= RESET_WAIT;
            end
            RESET_WAIT: if (done) begin
                reset_done <= 1; wait_ticks <= BOOT_TICKS; state <= BOOT;
            end
            ID: if (!busy) begin
                command <= 8'hF5; write_byte <= 0; byte_count <= 2;
                spi_start <= 1; state <= ID_WAIT;
            end
            ID_WAIT: if (done) begin
                if (result[7:0] == 8'h47) begin config_index <= 0; state <= WRITE_CFG; end
                else begin wait_ticks <= BOOT_TICKS; state <= BOOT; end
            end
            WRITE_CFG: if (!busy) begin
                byte_count <= 2;
                case(config_index)
                    0: begin command <= 8'h4F; write_byte <= 8'h07; end // 2000 dps, 200 Hz
                    1: begin command <= 8'h50; write_byte <= 8'h07; end // 16 g, 200 Hz
                    2: begin command <= 8'h52; write_byte <= 8'h44; end // 40 Hz at 200 Hz ODR
                    3: begin command <= 8'h65; write_byte <= 8'h08; end // UI DRDY -> INT1
                    4: begin command <= 8'h4E; write_byte <= 8'h0F; end // LN accel + gyro
                    default: begin command <= 8'h76; write_byte <= 0; end
                endcase
                spi_start <= 1; state <= CFG_WAIT;
            end
            CFG_WAIT: if (done) begin
                if (config_index == 4) begin wait_ticks <= SETTLE_TICKS; state <= SETTLE; end
                else begin config_index <= config_index+1'b1; state <= WRITE_CFG; end
            end
            SETTLE: if (wait_ticks == 0) state <= STATUS;
                    else wait_ticks <= wait_ticks-1'b1;
            STATUS: if (!busy) begin
                command <= 8'hAD; write_byte <= 0; byte_count <= 2;
                spi_start <= 1; state <= STATUS_WAIT;
            end
            STATUS_WAIT: if (done) begin record_status <= result[7:0]; state <= DATA; end
            DATA: if (!busy) begin
                command <= 8'h9F; write_byte <= 0; byte_count <= 13;
                spi_start <= 1; state <= DATA_WAIT;
            end
            DATA_WAIT: if (done) begin record_raw <= result[95:0]; state <= WHO; end
            WHO: if (!busy) begin
                command <= 8'hF5; write_byte <= 0; byte_count <= 2;
                spi_start <= 1; state <= WHO_WAIT;
            end
            WHO_WAIT: if (done) begin record_who <= result[7:0]; state <= READ_CFG; end
            READ_CFG: if (!busy) begin
                command <= 8'hCE; write_byte <= 0; byte_count <= 6;
                spi_start <= 1; state <= READ_CFG_WAIT;
            end
            READ_CFG_WAIT: if (done) begin
                record_pwr <= result[39:32]; record_gyro <= result[31:24];
                record_accel <= result[23:16]; record_filter <= result[7:0];
                record_ready <= 1;
                if (result[39:32]!=8'h0F || result[31:24]!=8'h07 ||
                    result[23:16]!=8'h07 || result[7:0]!=8'h44) begin
                    if (config_fail_streak == 2) begin
                        // Re-enter through soft reset so both sensors are OFF
                        // before filter/interrupt configuration is rewritten
                        // (ICM-42688-P DS-000347 section 12.9).
                        reset_done <= 0;
                        config_fail_streak <= 0; wait_ticks <= BOOT_TICKS; state <= BOOT;
                    end else begin
                        config_fail_streak <= config_fail_streak+1'b1;
                        wait_ticks <= POLL_TICKS; state <= DELAY;
                    end
                end else begin config_fail_streak <= 0; wait_ticks <= POLL_TICKS; state <= DELAY; end
            end
            DELAY: if (wait_ticks == 0) state <= STATUS;
                   else wait_ticks <= wait_ticks-1'b1;
            default: state <= BOOT;
        endcase
    end
endmodule
