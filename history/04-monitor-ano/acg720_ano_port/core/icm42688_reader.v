// Production ICM42688 reader: independent configuration confirmation; initial bad raw stays rejected.
// CFG_CONFIRM_ENABLE=0 preserves the original record/soft-reset behavior.
// A bad initial readback is always published for rejection before confirmation.
// Confirmation never publishes or repairs that raw record.
// Diagnostic byte order: WHO/PWR/GYRO/ACCEL/GYRO1/ACCEL1/FILTER (MSB first).
// bad bits 6..0 follow that same order. Reset count includes initial soft reset.
// ANO adapter: ODR1kHz, UI bandwidth ODR/40 (nominal25Hz),2nd order.
// Source ICM20602 used20Hz; this is the nearest supported1kHz UI setting.
// Status without DRDY is waited out, never published as a corrupt sample.
module icm42688_reader #(
    // Disable AFSR with verified OFF-state RMW; zero keeps legacy wire timing.
    parameter integer AFSR_DISABLE_ENABLE=1,
    parameter integer CFG_CONFIRM_ENABLE=1,
    parameter integer BOOT_TICKS=5000000,
    parameter integer SETTLE_TICKS=2500000,
    parameter integer POLL_TICKS=50000
) (
    input wire clk, rst_n, miso,
    output wire sck, mosi, cs_n,
    output reg record_ready=0,
    output reg [95:0] record_raw=0,
    output reg [7:0] record_who=0,
    output reg [7:0] record_pwr=0,
    output reg [7:0] record_gyro=0,
    output reg [7:0] record_accel=0,
    output reg [7:0] record_gyro1=0,
    output reg [7:0] record_accel1=0,
    output reg [7:0] record_filter=0,
    output reg [7:0] record_status=0,
    output reg config_pair_update=0,
    output reg [55:0] config_initial=0,
    output reg [55:0] config_confirmed=0,
    output reg [6:0] config_initial_bad=0,
    output reg [6:0] config_confirmed_bad=0,
    output reg [15:0] config_confirm_count=0,
    output reg [15:0] config_transient_count=0,
    output reg [15:0] config_reset_count=0,
    // Optional diagnostics; declaring ports does not wire production telemetry.
    output reg afsr_expected_valid=0,
    output reg [7:0] afsr_expected=0,
    output reg afsr_diag_update=0,
    output reg [7:0] afsr_first_read=0,
    output reg [7:0] afsr_confirmed_read=0,
    output reg [1:0] afsr_fail_streak=0,
    output reg [15:0] afsr_reject_count=0,
    output reg [15:0] afsr_transient_count=0,
    output reg [15:0] afsr_init_error_count=0,
    output reg [15:0] afsr_init_transient_count=0,
    output reg [15:0] afsr_reset_count=0
);
    localparam BOOT=0, BANK=1, BANK_WAIT=2, RESET=3, RESET_WAIT=4,
        ID=5, ID_WAIT=6, WRITE_CFG=7, CFG_WAIT=8, SETTLE=9,
        STATUS=10, STATUS_WAIT=11, DATA=12, DATA_WAIT=13,
        WHO=14, WHO_WAIT=15, READ_CFG=16, READ_CFG_WAIT=17, DELAY=18,
        CONFIRM_WHO=19, CONFIRM_WHO_WAIT=20, CONFIRM_CFG=21, CONFIRM_CFG_WAIT=22,
        AFSR_INIT_A=23, AFSR_INIT_A_WAIT=24, AFSR_INIT_B=25, AFSR_INIT_B_WAIT=26,
        AFSR_INIT_WRITE=27, AFSR_INIT_WRITE_WAIT=28,
        AFSR_INIT_VERIFY=29, AFSR_INIT_VERIFY_WAIT=30,
        AFSR_CHECK=31, AFSR_CHECK_WAIT=32, AFSR_CONFIRM=33, AFSR_CONFIRM_WAIT=34,
        AFSR_INIT_RETRY=35, AFSR_INIT_VERIFY_CONFIRM=36, AFSR_INIT_VERIFY_CONFIRM_WAIT=37;
    reg [5:0] state=BOOT;
    reg [7:0] afsr_seed=0;
    reg [1:0] afsr_init_fail_streak=0;
    reg [31:0] wait_ticks=BOOT_TICKS;
    reg reset_done=0;
    reg [31:0] poll_age=0;
    reg [2:0] config_index=0;
    reg [1:0] config_fail_streak=0;
    reg [7:0] confirmation_who=0;
    reg spi_start=0;
    reg [7:0] command=0, write_byte=0;
    reg [3:0] byte_count=2;
    wire busy, done;
    wire [103:0] result;
    spi_mode3_master_1mhz spi(.clk(clk),.start(spi_start),.command(command),
        .write_byte(write_byte),.byte_count(byte_count),.miso(miso),
        .sck(sck),.mosi(mosi),.cs_n(cs_n),.busy(busy),.done(done),.result(result));
    function [6:0] mismatch_bitmap;
        input [55:0] bytes;
        begin mismatch_bitmap={bytes[55:48]!=8'h47,bytes[47:40]!=8'h0F,
            bytes[39:32]!=8'h06,bytes[31:24]!=8'h06,bytes[23:16]!=8'h16,
            bytes[15:8]!=8'h0D,bytes[7:0]!=8'h77};end
    endfunction
    wire [55:0] initial_bytes={record_who,result[47:40],result[39:32],result[31:24],
        result[23:16],result[7:0],result[15:8]};
    wire [55:0] confirmation_bytes={confirmation_who,result[47:40],result[39:32],result[31:24],
        result[23:16],result[7:0],result[15:8]};
    wire [6:0] initial_mismatch=mismatch_bitmap(initial_bytes);
    wire [6:0] confirmation_mismatch=mismatch_bitmap(confirmation_bytes);
    always @(posedge clk) begin
        spi_start <= 0; record_ready <= 0; config_pair_update<=0; afsr_diag_update<=0;
        if(poll_age!=32'hffffffff) poll_age<=poll_age+1'b1;
        if (!rst_n) begin
            state <= BOOT; wait_ticks <= BOOT_TICKS; poll_age<=0; reset_done <= 0; config_index <= 0; config_fail_streak <= 0;
            record_gyro1<=0;record_accel1<=0;
            afsr_expected_valid<=0;afsr_expected<=0;afsr_seed<=0;
            afsr_init_fail_streak<=0;afsr_fail_streak<=0;
            afsr_first_read<=0;afsr_confirmed_read<=0;
            afsr_reject_count<=0;afsr_transient_count<=0;
            afsr_init_error_count<=0;afsr_init_transient_count<=0;afsr_reset_count<=0;
            confirmation_who<=0;config_initial<=0;config_confirmed<=0;
            config_initial_bad<=0;config_confirmed_bad<=0;
            config_confirm_count<=0;config_transient_count<=0;config_reset_count<=0;
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
                if(config_reset_count!=16'hFFFF)config_reset_count<=config_reset_count+1'b1;
                reset_done <= 1; wait_ticks <= BOOT_TICKS; state <= BOOT;
                afsr_expected_valid<=0;afsr_init_fail_streak<=0;afsr_fail_streak<=0;
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
                    0: begin command <= 8'h4F; write_byte <= 8'h06; end // 2000 dps, 1kHz
                    1: begin command <= 8'h50; write_byte <= 8'h06; end // 16g, 1kHz
                    2: begin command <= 8'h51; write_byte <= 8'h16; end // reset2nd-order UI, preserve reserved/DEC2
                    3: begin command <= 8'h52; write_byte <= 8'h77; end // nominal25Hz at1kHz ODR
                    4: begin command <= 8'h53; write_byte <= 8'h0D; end // reset2nd-order accel UI
                    5: begin command <= 8'h65; write_byte <= 8'h08; end // UI DRDY -> INT1
                    6: begin command <= 8'h4E; write_byte <= 8'h0F; end // LN accel + gyro
                    default: begin command <= 8'h76; write_byte <= 0; end
                endcase
                spi_start <= 1; state <= CFG_WAIT;
            end
            CFG_WAIT: if (done) begin
                if (config_index == 6) begin wait_ticks<=SETTLE_TICKS;state<=SETTLE;end
                else if(AFSR_DISABLE_ENABLE && config_index==5)state<=AFSR_INIT_A;
                else begin config_index<=config_index+1'b1;state<=WRITE_CFG;end
            end
            SETTLE: if (wait_ticks == 0) state <= STATUS;
                    else wait_ticks <= wait_ticks-1'b1;
            STATUS: if (!busy) begin
                command <= 8'hAD; write_byte <= 0; byte_count <= 2;
                spi_start <= 1; poll_age<=0; state <= STATUS_WAIT;
            end
            STATUS_WAIT: if (done) begin
                record_status <= result[7:0];
                if(result[3]) state<=DATA;else state<=DELAY;
            end
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
                command <= 8'hCE; write_byte <= 0; byte_count <= 7;
                spi_start <= 1; state <= READ_CFG_WAIT;
            end
            READ_CFG_WAIT: if (done) begin
                record_pwr <= result[47:40]; record_gyro <= result[39:32];
                record_accel <= result[31:24];record_gyro1<=result[23:16];
                record_filter <= result[15:8];record_accel1<=result[7:0];
                // The original WHO/config rejection record is never repaired.
                // Only an entirely correct legacy record is held for AFSR check.
                if(!AFSR_DISABLE_ENABLE || initial_mismatch!=0) record_ready<=1;
                // Original error trigger is the six configuration fields.
                // WHO-only errors still follow the original guard rejection
                // path; WHO must also be correct in a positive confirmation.
                if (|initial_mismatch[5:0]) begin
                    config_initial<=initial_bytes;config_initial_bad<=initial_mismatch;
                    config_confirmed<=0;config_confirmed_bad<=7'h7F;
                    if(CFG_CONFIRM_ENABLE) state<=CONFIRM_WHO;
                    else begin
                        config_pair_update<=1;
                        if(config_fail_streak==2)begin
                            reset_done<=0;config_fail_streak<=0;
                            wait_ticks<=BOOT_TICKS;state<=BOOT;
                        end else begin
                            config_fail_streak<=config_fail_streak+1'b1;
                            wait_ticks<=POLL_TICKS;state<=DELAY;
                        end
                    end
                end else begin
                    config_fail_streak<=0;
                    if(AFSR_DISABLE_ENABLE && initial_mismatch==0) state<=AFSR_CHECK;
                    else begin wait_ticks<=POLL_TICKS;state<=DELAY;end
                end
            end
            CONFIRM_WHO: if(!busy)begin
                command<=8'hF5;write_byte<=0;byte_count<=2;
                spi_start<=1;state<=CONFIRM_WHO_WAIT;
            end
            CONFIRM_WHO_WAIT: if(done)begin confirmation_who<=result[7:0];state<=CONFIRM_CFG;end
            CONFIRM_CFG: if(!busy)begin
                command<=8'hCE;write_byte<=0;byte_count<=7;
                spi_start<=1;state<=CONFIRM_CFG_WAIT;
            end
            CONFIRM_CFG_WAIT: if(done)begin
                // Diagnostic only: never overwrite record_* or emit
                // record_ready here, even if this new readback is correct.
                config_confirmed<=confirmation_bytes;
                config_confirmed_bad<=confirmation_mismatch;config_pair_update<=1;
                if(config_confirm_count!=16'hFFFF)config_confirm_count<=config_confirm_count+1'b1;
                if(confirmation_mismatch==0)begin
                    if(config_transient_count!=16'hFFFF)config_transient_count<=config_transient_count+1'b1;
                    config_fail_streak<=0;wait_ticks<=POLL_TICKS;state<=DELAY;
                end else if(config_fail_streak==2)begin
                    // Preserve original OFF-before-reconfigure soft-reset
                    // sequence and both 100ms waits plus 50ms settling.
                    reset_done<=0;config_fail_streak<=0;wait_ticks<=BOOT_TICKS;state<=BOOT;
                end else begin
                    config_fail_streak<=config_fail_streak+1'b1;
                    wait_ticks<=POLL_TICKS;state<=DELAY;
                end
            end
            // Read the RMW seed twice independently. Never write reserved/other
            // low bits based on a disagreeing initial readback.
            AFSR_INIT_A: if(!busy)begin
                command<=8'hCD;write_byte<=0;byte_count<=2;
                spi_start<=1;state<=AFSR_INIT_A_WAIT;
            end
            AFSR_INIT_A_WAIT: if(done)begin
                afsr_seed<=result[7:0];afsr_first_read<=result[7:0];state<=AFSR_INIT_B;
            end
            AFSR_INIT_B: if(!busy)begin
                command<=8'hCD;write_byte<=0;byte_count<=2;
                spi_start<=1;state<=AFSR_INIT_B_WAIT;
            end
            AFSR_INIT_B_WAIT: if(done)begin
                afsr_confirmed_read<=result[7:0];afsr_diag_update<=1;
                // No external RTC on this target: retain normal CLKSEL=01,
                // RTC_MODE=0. Two agreeing all-0/all-FF reads are not trusted.
                // Bits5:3 remain unchanged; no reserved-bit value is invented.
                if(result[5:0]==afsr_seed[5:0] && result[2:0]==3'b001)begin
                    afsr_expected<={2'b01,afsr_seed[5:0]};state<=AFSR_INIT_WRITE;
                end else begin
                    if(afsr_init_error_count!=16'hFFFF)afsr_init_error_count<=afsr_init_error_count+1'b1;
                    if(afsr_init_fail_streak==2)begin
                        afsr_init_fail_streak<=0;afsr_fail_streak<=0;afsr_expected_valid<=0;
                        if(afsr_reset_count!=16'hFFFF)afsr_reset_count<=afsr_reset_count+1'b1;
                        reset_done<=0;wait_ticks<=BOOT_TICKS;state<=BOOT;
                    end else begin
                        afsr_init_fail_streak<=afsr_init_fail_streak+1'b1;
                        wait_ticks<=POLL_TICKS;state<=AFSR_INIT_RETRY;
                    end
                end
            end
            AFSR_INIT_WRITE: if(!busy)begin
                command<=8'h4D;write_byte<=afsr_expected;byte_count<=2;
                spi_start<=1;state<=AFSR_INIT_WRITE_WAIT;
            end
            AFSR_INIT_WRITE_WAIT: if(done)state<=AFSR_INIT_VERIFY;
            AFSR_INIT_VERIFY: if(!busy)begin
                command<=8'hCD;write_byte<=0;byte_count<=2;
                spi_start<=1;state<=AFSR_INIT_VERIFY_WAIT;
            end
            AFSR_INIT_VERIFY_WAIT: if(done)begin
                afsr_first_read<=result[7:0];afsr_diag_update<=1;
                if(result[7:0]==afsr_expected)begin
                    afsr_expected_valid<=1;afsr_init_fail_streak<=0;
                    // TDK OFF-write constraint: all RMW/verification completes
                    // before the original PWR_MGMT0=0x0F write and settle wait.
                    config_index<=6;state<=WRITE_CFG;
                end else begin
                    if(afsr_init_error_count!=16'hFFFF)afsr_init_error_count<=afsr_init_error_count+1'b1;
                    state<=AFSR_INIT_VERIFY_CONFIRM;
                end
            end
            AFSR_INIT_VERIFY_CONFIRM: if(!busy)begin
                command<=8'hCD;write_byte<=0;byte_count<=2;
                spi_start<=1;state<=AFSR_INIT_VERIFY_CONFIRM_WAIT;
            end
            AFSR_INIT_VERIFY_CONFIRM_WAIT: if(done)begin
                afsr_confirmed_read<=result[7:0];afsr_diag_update<=1;
                if(result[7:0]==afsr_expected)begin
                    if(afsr_init_transient_count!=16'hFFFF)afsr_init_transient_count<=afsr_init_transient_count+1'b1;
                    afsr_expected_valid<=1;afsr_init_fail_streak<=0;
                    config_index<=6;state<=WRITE_CFG;
                end else begin
                    if(afsr_init_fail_streak==2)begin
                        afsr_init_fail_streak<=0;afsr_fail_streak<=0;afsr_expected_valid<=0;
                        if(afsr_reset_count!=16'hFFFF)afsr_reset_count<=afsr_reset_count+1'b1;
                        reset_done<=0;wait_ticks<=BOOT_TICKS;state<=BOOT;
                    end else begin
                        afsr_init_fail_streak<=afsr_init_fail_streak+1'b1;
                        wait_ticks<=POLL_TICKS;state<=AFSR_INIT_RETRY;
                    end
                end
            end
            AFSR_INIT_RETRY: if(wait_ticks==0)state<=AFSR_INIT_A;
                else wait_ticks<=wait_ticks-1'b1;
            AFSR_CHECK: if(!busy)begin
                command<=8'hCD;write_byte<=0;byte_count<=2;
                spi_start<=1;state<=AFSR_CHECK_WAIT;
            end
            AFSR_CHECK_WAIT: if(done)begin
                afsr_first_read<=result[7:0];afsr_diag_update<=1;
                if(afsr_expected_valid && result[7:0]==afsr_expected)begin
                    // Exactly one publication for the original new-DRDY record.
                    record_ready<=1;afsr_fail_streak<=0;
                    wait_ticks<=POLL_TICKS;state<=DELAY;
                end else begin
                    // Drop this original raw permanently before any consumer.
                    // A confirming good read never repairs or republishes it.
                    if(afsr_reject_count!=16'hFFFF)afsr_reject_count<=afsr_reject_count+1'b1;
                    state<=AFSR_CONFIRM;
                end
            end
            AFSR_CONFIRM: if(!busy)begin
                command<=8'hCD;write_byte<=0;byte_count<=2;
                spi_start<=1;state<=AFSR_CONFIRM_WAIT;
            end
            AFSR_CONFIRM_WAIT: if(done)begin
                afsr_confirmed_read<=result[7:0];afsr_diag_update<=1;
                if(afsr_expected_valid && result[7:0]==afsr_expected)begin
                    if(afsr_transient_count!=16'hFFFF)afsr_transient_count<=afsr_transient_count+1'b1;
                    afsr_fail_streak<=0;wait_ticks<=POLL_TICKS;state<=DELAY;
                end else if(afsr_fail_streak==2)begin
                    afsr_fail_streak<=0;afsr_expected_valid<=0;
                    if(afsr_reset_count!=16'hFFFF)afsr_reset_count<=afsr_reset_count+1'b1;
                    // Same old finite BOOT/reset/configuration/settle recovery.
                    reset_done<=0;config_fail_streak<=0;wait_ticks<=BOOT_TICKS;state<=BOOT;
                end else begin
                    afsr_fail_streak<=afsr_fail_streak+1'b1;
                    wait_ticks<=POLL_TICKS;state<=DELAY;
                end
            end
            DELAY: if (poll_age>=POLL_TICKS-1) state<=STATUS;
            default: state <= BOOT;
        endcase
    end
endmodule
