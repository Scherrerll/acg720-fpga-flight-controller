// B0B2 input policy: transport/configuration validation belongs to the reader
// and base_ok. A change in a legal accelerometer or gyro value is not evidence
// of a corrupt SPI transfer. Do not select vibration phases by rejecting the
// complete six-axis record. The unchanged estimator gates gravity correction
// by acceleration magnitude while continuing gyro integration.
//
// Preserve the original three-clock snapshot delay and explicit overrun fault.
// The guard still owns source-age expiry and qualified recovery; this stage
// does not refresh either deadline, fabricate samples, or substitute old gyro.
module imu_temporal_check #(
    parameter integer TIMEOUT_TICKS=2500000,
    // Deprecated source-compatible parameters; none controls acceptance in B0B2.
    parameter integer QUIET_SAMPLES=16,
    parameter integer QUIET_GYRO_DELTA=12,
    parameter integer QUIET_ACCEL_DELTA=32,
    parameter integer MOTION_GYRO_DELTA=1024,
    parameter integer MOTION_ACCEL_DELTA=1024,
    parameter integer CONFIRM_GYRO_DELTA=1024,
    parameter integer CONFIRM_ACCEL_DELTA=256
) (
    input wire clk,rst_n,record_ready,base_ok,calibrated,
    input wire [95:0] raw,
    input wire signed [15:0] bias_x,bias_y,bias_z,
    output reg checked_ready=0,
    output reg [7:0] reject_detail=0,
    // Retained diagnostic ABI: the removed motion-candidate policy is inactive.
    output wire [7:0] quiet_count,
    output wire candidate_pending,
    output reg [95:0] checked_raw=0,
    input wire [31:0] diag_source_id_in,diag_tick_in,
    input wire [9:0] diag_reader_meta_in,
    output reg [31:0] diag_source_id_out=0,
    output reg [31:0] diag_tick_out=0,
    output reg [9:0] diag_reader_meta_out=0,
    output reg [95:0] diag_trusted_out=0,
    output wire [95:0] diag_candidate_out,
    output reg checked_base_ok=0
);
    localparam IDLE=0, WAIT_ONE=1, WAIT_TWO=2, DECIDE=3;
    reg [1:0] state=IDLE;
    reg [95:0] held_raw=0,held_trusted=0,trusted=0;
    reg held_base_ok=0;
    reg [31:0] held_source_id=0,held_tick=0;
    reg [9:0] held_reader_meta=0;
    assign quiet_count=0;
    assign candidate_pending=0;
    assign diag_candidate_out=0;

    always @(posedge clk) begin
        checked_ready<=0;
        if(!rst_n) begin
            state<=IDLE;reject_detail<=0;checked_raw<=0;checked_base_ok<=0;
            held_raw<=0;held_base_ok<=0;held_trusted<=0;trusted<=0;
            held_source_id<=0;held_tick<=0;held_reader_meta<=0;
            diag_source_id_out<=0;diag_tick_out<=0;diag_reader_meta_out<=0;
            diag_trusted_out<=0;
        end else if(record_ready && state!=IDLE) begin
            // Preserve fail-closed behavior for an impossible input cadence:
            // discard the unfinished snapshot and identify the colliding input.
            state<=IDLE;checked_ready<=1;checked_raw<=raw;
            checked_base_ok<=base_ok;reject_detail<=8'h80;
            diag_source_id_out<=diag_source_id_in;diag_tick_out<=diag_tick_in;
            diag_reader_meta_out<=diag_reader_meta_in;diag_trusted_out<=trusted;
        end else case(state)
            IDLE:if(record_ready) begin
                held_raw<=raw;held_base_ok<=base_ok;held_trusted<=trusted;
                held_source_id<=diag_source_id_in;held_tick<=diag_tick_in;
                held_reader_meta<=diag_reader_meta_in;state<=WAIT_ONE;
            end
            WAIT_ONE:state<=WAIT_TWO;
            WAIT_TWO:state<=DECIDE;
            DECIDE:begin
                state<=IDLE;checked_ready<=1;checked_raw<=held_raw;
                checked_base_ok<=held_base_ok;reject_detail<=0;
                diag_source_id_out<=held_source_id;diag_tick_out<=held_tick;
                diag_reader_meta_out<=held_reader_meta;
                diag_trusted_out<=held_trusted;
                if(held_base_ok)trusted<=held_raw;
            end
            default:state<=IDLE;
        endcase
    end
endmodule
