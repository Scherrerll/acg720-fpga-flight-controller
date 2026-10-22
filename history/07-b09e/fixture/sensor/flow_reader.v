// ATK/PixArt PMW3901MB DS R1.10 pages 29-32 initialization, 100 Hz burst.
// Raw X/Y remain signed integer counts (zero fractional bits). All twelve burst
// bytes publish atomically, including rejected samples for forensic telemetry.
// No SPI CRC exists. Faulted initialization requires an external sensor power
// cycle; this GPIO does not necessarily switch the board's fixed 3.3 V supply.
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
    output reg [31:0] source_dt_ticks = 0, output reg [31:0] error_count = 0,
    output reg [63:0] sensor_diagnostics = 0, output wire sample_usable
);
    reg spi_start = 0, spi_read = 1, spi_burst_read = 0;
    wire [95:0] spi_burst_result;
    reg [7:0] spi_address = 0, spi_write_data = 0;
    wire spi_busy, spi_done;
    wire [7:0] spi_result;
    pmw3901_spi_mode3 spi_unit (
        .clk(clk50), .rst_n(rst_n), .start(spi_start), .read_op(spi_read),
        .address(spi_address), .write_data(spi_write_data),
        .burst_read(spi_burst_read), .burst_result(spi_burst_result),
        .miso(flow_miso), .sck(flow_sck), .mosi(flow_mosi),
        .cs_n(flow_cs_n), .busy(spi_busy), .done(spi_done), .result(spi_result)
    );
    reg [15:0] init_rom [0:72];
`include "sensor/pmw3901_init.vh"
    reg [6:0] init_index = 0;
    wire [15:0] init_entry = init_rom[init_index];
    localparam BOOT=0, POWER_WAIT=1, ID_REQ=2, ID_WAIT=3,
        INV_REQ=4, INV_WAIT=5, RETRY_WAIT=6, RESET_REQ=7,
        RESET_WAIT=8, RESET_DELAY=9, CLEAR_REQ=10, CLEAR_WAIT=11,
        CLEAR_DELAY=12, INIT_REQ=13, INIT_WAIT=14, INIT_GAP=15,
        MOTION_REQ=16, MOTION_WAIT=17, MOTION_GAP=18,
        REV_REQ=19, REV_WAIT=20, PRE_REQ=21, PRE_WAIT=22, PRE_GAP=23,
        OBS_WRITE_REQ=24, OBS_WRITE_WAIT=25, OBS_DELAY=26,
        OBS_READ_REQ=27, OBS_READ_WAIT=28, FAILED=29;
    reg [4:0] state = BOOT;
    reg [22:0] wait_ticks = 23'd50_000;
    reg [18:0] poll_ticks = 0;
    reg [4:0] pre_step = 0;
    reg [1:0] handshake_trials = 0;
    reg [7:0] trim_c1 = 0, trim_c2 = 0, selected_48 = 0;
    reg trim_applied = 0, handshake_ok = 0;
    reg [7:0] chip_id = 0, inverse_id = 0, revision_id = 0;
    reg [7:0] clear_addr = 8'h02;
    reg initialized = 0;
    reg [7:0] motion = 0, dx_lo = 0, dx_hi = 0,
              dy_lo = 0, dy_hi = 0, quality = 0;
    reg [31:0] sample_seq = 0;
    reg sample_seen = 0;
    reg zero_gray_tracking = 0;
    reg [25:0] zero_gray_ticks = 0;
    wire sustained_zero_gray = zero_gray_tracking && zero_gray_ticks >= 26'd50_000_000;
    wire id_ok = chip_id == 8'h49 && inverse_id == 8'hB6;
    assign who = chip_id;
    assign configured = initialized;
    assign flow_dx = $signed({dx_hi, dx_lo});
    assign flow_dy = $signed({dy_hi, dy_lo});
    assign squal = quality;
    assign flow_motion = motion;
    assign sample_sequence = sample_seq;
    assign sample_usable = initialized && sensor_diagnostics[14];
    assign link_ok = id_ok && initialized && sample_seen &&
                     source_age_ticks < STALE_TICKS &&
                     sensor_diagnostics[11] && !sustained_zero_gray;

    // Integer trim arithmetic. Widen C1 before addition so 0xFF cannot wrap.
    function [7:0] adjusted_c1(input [7:0] raw);
        reg [8:0] sum;
        begin
            sum = {1'b0,raw} + (raw <= 8'd28 ? 9'd14 : 9'd11);
            adjusted_c1 = sum > 9'd63 ? 8'd63 : sum[7:0];
        end
    endfunction
    function [7:0] adjusted_c2(input [7:0] raw);
        reg [15:0] product;
        begin product = raw * 16'd45; adjusted_c2 = product / 16'd100; end
    endfunction

    // Preamble order is the datasheet table, including conditional trim reads.
    reg pre_read;
    reg [7:0] pre_address, pre_data;
    always @* begin
        pre_read=0; pre_address=8'h7F; pre_data=0;
        case(pre_step)
            0: begin pre_address=8'h7F; pre_data=8'h00; end
            1: begin pre_address=8'h55; pre_data=8'h01; end
            2: begin pre_address=8'h50; pre_data=8'h07; end
            3: begin pre_address=8'h7F; pre_data=8'h0E; end
            4: begin pre_address=8'h43; pre_data=8'h10; end
            5: begin pre_read=1; pre_address=8'h47; end
            6: begin pre_read=1; pre_address=8'h67; end
            7: begin pre_address=8'h48; pre_data=selected_48; end
            8: begin pre_address=8'h7F; pre_data=8'h00; end
            9: begin pre_address=8'h51; pre_data=8'h7B; end
            10: begin pre_address=8'h50; pre_data=8'h00; end
            11: begin pre_address=8'h55; pre_data=8'h00; end
            12: begin pre_address=8'h7F; pre_data=8'h0E; end
            13: begin pre_read=1; pre_address=8'h73; end
            14: begin pre_read=1; pre_address=8'h70; end
            15: begin pre_read=1; pre_address=8'h71; end
            16: begin pre_address=8'h7F; pre_data=8'h00; end
            17: begin pre_address=8'h61; pre_data=8'hAD; end
            18: begin pre_address=8'h51; pre_data=8'h70; end
            19: begin pre_address=8'h7F; pre_data=8'h0E; end
            20: begin pre_address=8'h70; pre_data=trim_c1; end
            21: begin pre_address=8'h71; pre_data=trim_c2; end
            default: begin pre_address=8'h7F; pre_data=8'h00; end
        endcase
    end
    wire burst_observation_ok = spi_burst_result[87:80] == 8'hBF;
    wire burst_false_motion = spi_burst_result[47:40] < 8'd25 &&
                              spi_burst_result[15:8] == 8'h1F;
    wire burst_zero_gray = spi_burst_result[31:24] == 0 && spi_burst_result[23:16] == 0;
    // Include this commit edge's elapsed-clock increment in the new tuple.
    // The continuously visible monitor still asserts at exactly 50M ticks.
    wire burst_sustained_gray = burst_zero_gray && zero_gray_tracking &&
                                zero_gray_ticks >= 26'd49_999_999;
    wire burst_usable = initialized && burst_observation_ok &&
                        !burst_false_motion && !burst_sustained_gray;
    wire [7:0] burst_health = {1'b0, burst_usable, handshake_ok,
                              trim_applied, burst_observation_ok,
                              burst_sustained_gray, burst_zero_gray, burst_false_motion};
    always @(posedge clk50 or negedge rst_n) begin
        if (!rst_n) begin
            spi_start<=0; spi_read<=1; spi_burst_read<=0; spi_address<=0; spi_write_data<=0;
            state<=BOOT; wait_ticks<=23'd50_000; flow_pwr_en<=0;
            init_index<=0; chip_id<=0; inverse_id<=0; revision_id<=0; clear_addr<=8'h02;
            initialized<=0; motion<=0; dx_lo<=0; dx_hi<=0; dy_lo<=0; dy_hi<=0; quality<=0;
            sample_seq<=0; sample_valid<=0; sample_seen<=0;
            source_age_ticks<=32'hFFFFFFFF; source_dt_ticks<=0; error_count<=0; good_count<=0;
            sensor_diagnostics<=0; poll_ticks<=0; pre_step<=0; handshake_trials<=0;
            trim_c1<=0; trim_c2<=0; selected_48<=0; trim_applied<=0; handshake_ok<=0;
            zero_gray_tracking<=0; zero_gray_ticks<=0;
        end else begin
            sample_valid<=0; spi_start<=0; spi_burst_read<=0;
            if(source_age_ticks!=32'hFFFFFFFF) source_age_ticks<=source_age_ticks+1'b1;
            if(poll_ticks!=0) poll_ticks<=poll_ticks-1'b1;
            if(zero_gray_tracking && zero_gray_ticks<26'd50_000_000)
                zero_gray_ticks<=zero_gray_ticks+1'b1;
            case(state)
                BOOT: if(wait_ticks==0) begin flow_pwr_en<=1;wait_ticks<=23'd5_000_000;state<=POWER_WAIT;end
                      else wait_ticks<=wait_ticks-1'b1;
                POWER_WAIT: if(wait_ticks==0) state<=ID_REQ; else wait_ticks<=wait_ticks-1'b1;
                ID_REQ: if(!spi_busy) begin spi_read<=1;spi_address<=8'h00;spi_start<=1;state<=ID_WAIT;end
                ID_WAIT: if(spi_done) begin chip_id<=spi_result;state<=INV_REQ;end
                INV_REQ: if(!spi_busy) begin spi_read<=1;spi_address<=8'h5F;spi_start<=1;state<=INV_WAIT;end
                INV_WAIT: if(spi_done) begin
                    inverse_id<=spi_result;
                    if(chip_id==8'h49 && spi_result==8'hB6) state<=REV_REQ;
                    else begin
                        if(error_count!=32'hFFFFFFFF) error_count<=error_count+1'b1;
                        wait_ticks<=23'd5_000_000;state<=RETRY_WAIT;
                    end
                end
                RETRY_WAIT: if(wait_ticks==0) state<=ID_REQ; else wait_ticks<=wait_ticks-1'b1;
                REV_REQ: if(!spi_busy) begin spi_read<=1;spi_address<=8'h01;spi_start<=1;state<=REV_WAIT;end
                REV_WAIT: if(spi_done) begin revision_id<=spi_result;state<=RESET_REQ;end
                RESET_REQ: if(!spi_busy) begin spi_read<=0;spi_address<=8'h3A;spi_write_data<=8'h5A;spi_start<=1;state<=RESET_WAIT;end
                RESET_WAIT: if(spi_done) begin wait_ticks<=23'd250_000;state<=RESET_DELAY;end
                RESET_DELAY: if(wait_ticks==0) state<=CLEAR_REQ; else wait_ticks<=wait_ticks-1'b1;
                CLEAR_REQ: if(!spi_busy) begin spi_read<=1;spi_address<=clear_addr;spi_start<=1;state<=CLEAR_WAIT;end
                CLEAR_WAIT: if(spi_done) begin
                    if(clear_addr==8'h06) begin wait_ticks<=23'd50_000;state<=CLEAR_DELAY;end
                    else begin clear_addr<=clear_addr+1'b1;state<=CLEAR_REQ;end
                end
                CLEAR_DELAY: if(wait_ticks==0) state<=PRE_REQ;else wait_ticks<=wait_ticks-1'b1;
                PRE_REQ: if(!spi_busy) begin
                    spi_read<=pre_read;spi_address<=pre_address;spi_write_data<=pre_data;
                    spi_start<=1;state<=PRE_WAIT;
                end
                PRE_WAIT: if(spi_done) begin
                    wait_ticks<=23'd10_000;state<=PRE_GAP;
                    if(pre_step==5 && spi_result!=8'h08) begin
                        if(handshake_trials==2) begin
                            state<=FAILED;
                            if(error_count!=32'hFFFFFFFF) error_count<=error_count+1'b1;
                        end else begin handshake_trials<=handshake_trials+1'b1;pre_step<=4;end
                    end else if((pre_step==13 && spi_result!=0) || pre_step==21) begin
                        if(pre_step==21) trim_applied<=1;
                        state<=INIT_REQ;
                    end else begin
                        pre_step<=pre_step+1'b1;
                        if(pre_step==5) handshake_ok<=1;
                        if(pre_step==6) selected_48<=spi_result[7] ? 8'h04 : 8'h02;
                        if(pre_step==14) trim_c1<=adjusted_c1(spi_result);
                        if(pre_step==15) trim_c2<=adjusted_c2(spi_result);
                    end
                end
                PRE_GAP: if(wait_ticks==0) state<=PRE_REQ;else wait_ticks<=wait_ticks-1'b1;
                INIT_REQ: if(!spi_busy) begin
                    spi_read<=0;spi_address<=init_entry[15:8];spi_write_data<=init_entry[7:0];
                    spi_start<=1;state<=INIT_WAIT;
                end
                INIT_WAIT: if(spi_done) begin
                    if(init_index==72) state<=OBS_WRITE_REQ;
                    else begin
                        init_index<=init_index+1'b1;
                        wait_ticks<=init_index==58 ? 23'd500_000 : 23'd10_000;
                        state<=INIT_GAP;
                    end
                end
                INIT_GAP: if(wait_ticks==0) state<=INIT_REQ;else wait_ticks<=wait_ticks-1'b1;
                OBS_WRITE_REQ: if(!spi_busy) begin
                    spi_read<=0;spi_address<=8'h15;spi_write_data<=0;spi_start<=1;state<=OBS_WRITE_WAIT;
                end
                OBS_WRITE_WAIT: if(spi_done) begin wait_ticks<=23'd750_000;state<=OBS_DELAY;end
                OBS_DELAY: if(wait_ticks==0) state<=OBS_READ_REQ;else wait_ticks<=wait_ticks-1'b1;
                OBS_READ_REQ: if(!spi_busy) begin spi_read<=1;spi_address<=8'h15;spi_start<=1;state<=OBS_READ_WAIT;end
                OBS_READ_WAIT: if(spi_done) begin
                    if(spi_result==8'hBF && handshake_ok) begin initialized<=1;state<=MOTION_REQ;end
                    else begin
                        state<=FAILED;
                        if(error_count!=32'hFFFFFFFF) error_count<=error_count+1'b1;
                    end
                end
                MOTION_REQ: if(!spi_busy) begin
                    spi_read<=1;spi_address<=8'h16;spi_burst_read<=1;spi_start<=1;
                    poll_ticks<=19'd499_999;state<=MOTION_WAIT;
                end
                MOTION_WAIT: if(spi_done) begin
                    motion<=spi_burst_result[95:88];dx_lo<=spi_burst_result[79:72];dx_hi<=spi_burst_result[71:64];
                    dy_lo<=spi_burst_result[63:56];dy_hi<=spi_burst_result[55:48];quality<=spi_burst_result[47:40];
                    sensor_diagnostics<={spi_burst_result[87:80],spi_burst_result[39:0],burst_health,revision_id};
                    sample_seq<=sample_seq+1'b1;sample_valid<=1;sample_seen<=1;
                    if(good_count!=32'hFFFFFFFF) good_count<=good_count+1'b1;
                    source_dt_ticks<=sample_seen ? source_age_ticks+1'b1 : 32'd0;
                    source_age_ticks<=0;state<=MOTION_GAP;
                    if(burst_zero_gray) begin
                        if(!zero_gray_tracking) begin zero_gray_tracking<=1;zero_gray_ticks<=0;end
                    end else begin zero_gray_tracking<=0;zero_gray_ticks<=0;end
                    if((!burst_observation_ok && (!sample_seen || sensor_diagnostics[11])) ||
                       (burst_sustained_gray && !sensor_diagnostics[10]))
                        if(error_count!=32'hFFFFFFFF) error_count<=error_count+1'b1;
                end
                MOTION_GAP: if(poll_ticks<=1) state<=MOTION_REQ;
                FAILED: begin initialized<=0;end // external module power-cycle required
                default: begin
                    initialized<=0;state<=FAILED;
                    if(error_count!=32'hFFFFFFFF) error_count<=error_count+1'b1;
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
    input wire burst_read,
    output reg [95:0] burst_result = 0,
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
    reg [3:0] bytes_left = 1;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            sck <= 1; mosi <= 0; cs_n <= 1; busy <= 0; done <= 0; result <= 0;
            state <= IDLE; ticks <= 0; tx_shift <= 0; rx_shift <= 0;
            pending_data <= 0; bit_idx <= 0; data_phase <= 0; pending_read <= 1;
            burst_result <= 0; bytes_left <= 1;
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
                bytes_left <= burst_read && read_op ? 4'd12 : 4'd1;
                burst_result <= 0;
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
                        burst_result <= {burst_result[87:0], rx_shift[6:0], miso};
                        if (bytes_left > 1) begin
                            bytes_left <= bytes_left - 1'b1;
                            bit_idx <= 3'd7;
                            tx_shift <= 0;
                            ticks <= 14'd24;
                            state <= BETWEEN;
                        end else begin
                            ticks <= 14'd4999; // 100 us before CS release
                            state <= FINISH_DELAY;
                        end
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

