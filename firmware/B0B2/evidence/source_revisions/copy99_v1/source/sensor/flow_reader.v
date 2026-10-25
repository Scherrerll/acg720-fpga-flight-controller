// PMW3901 raw-count reader extracted from the previously bench-tested diagnostic.
// Counts are NOT centimeters, velocity or position. No optical calibration or
// rotation compensation is performed. Zero counts remain valid new samples.
// SPI has no CRC: link_ok means startup IDs matched and completed samples are
// fresh; it does not prove the physical integrity of every SPI byte.
// error_count counts failed startup ID pairs / illegal state recovery only.
// Exact 73-entry Bitcraze initializer and original mode-3 timing are retained.
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

    // 73 performance-register writes from the upstream Bitcraze driver.
    reg [15:0] init_rom [0:72];
`include "sensor/pmw3901_init.vh"
    reg [6:0] init_index = 0;
    wire [15:0] init_entry = init_rom[init_index];

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
    // Stage individual SPI bytes, then publish one coherent sample at 0x07.
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
                wait_ticks <= 23'd250_000; // reset recovery 5 ms
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
                    wait_ticks <= 23'd50_000; // 1 ms before setup
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
                        23'd5_000_000 : 23'd10_000; // 100 ms, else 200 us
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
                    wait_ticks <= 23'd1_000_000; // ~50 Hz
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
                ticks <= 14'd2499; // 50 us before address
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
                        ticks <= 14'd4999; // 100 us before CS release
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

