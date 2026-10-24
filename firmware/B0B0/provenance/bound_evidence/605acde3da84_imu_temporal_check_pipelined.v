// Causal protection with a coherent input snapshot and three-clock computation
// pipeline. Thresholds and motion-onset confirmation are the original bench
// algorithm. Connect checked_raw/checked_base_ok to the matching downstream
// metadata snapshot; never combine checked_ready with live reader bytes.
module imu_temporal_check #(
    parameter integer TIMEOUT_TICKS=2500000,
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
    output reg [7:0] quiet_count=0,
    output reg candidate_pending=0,
    output reg [95:0] checked_raw=0,
    output reg checked_base_ok=0
);
    localparam IDLE=0, ARITHMETIC=1, REDUCE=2, DECIDE=3;
    localparam PIPELINE_DELAY=3;
    reg [1:0] state=IDLE;
    reg history_valid=0;
    reg [95:0] trusted=0,candidate=0;
    reg [31:0] age=TIMEOUT_TICKS;
    reg [95:0] held_raw=0,held_trusted=0,held_candidate=0;
    reg [47:0] held_bias=0;
    reg held_base_ok=0,held_calibrated=0,held_expired=0,held_pending=0;
    reg [7:0] held_quiet=0;
    reg [16:0] da_x=0,da_y=0,da_z=0,dg_x=0,dg_y=0,dg_z=0;
    reg [16:0] ca_x=0,ca_y=0,ca_z=0,cg_x=0,cg_y=0,cg_z=0;
    reg [16:0] bg_x=0,bg_y=0,bg_z=0;
    reg [31:0] ax_square=0,ay_square=0,az_square=0;
    reg [33:0] norm2=0;
    reg [7:0] suspicion=0;
    reg close_candidate=0,small_rate=0,quiet_distance=0;
    function [16:0] distance;
        input [15:0] a,b;
        reg signed [16:0] d;
        begin d=$signed({a[15],a})-$signed({b[15],b}); distance=d<0 ? -d : d; end
    endfunction
    wire signed [15:0] ax=held_raw[95:80],ay=held_raw[79:64],az=held_raw[63:48];
    wire held_quiet_active=held_quiet>=QUIET_SAMPLES;
    wire quiet_gyro_jump=held_quiet_active &&
        (dg_x>QUIET_GYRO_DELTA || dg_y>QUIET_GYRO_DELTA || dg_z>QUIET_GYRO_DELTA);
    wire quiet_accel_jump=held_quiet_active &&
        (da_x>QUIET_ACCEL_DELTA || da_y>QUIET_ACCEL_DELTA || da_z>QUIET_ACCEL_DELTA);
    wire motion_gyro_jump=!held_quiet_active &&
        (dg_x>MOTION_GYRO_DELTA || dg_y>MOTION_GYRO_DELTA || dg_z>MOTION_GYRO_DELTA);
    wire motion_accel_jump=!held_quiet_active &&
        (da_x>MOTION_ACCEL_DELTA || da_y>MOTION_ACCEL_DELTA || da_z>MOTION_ACCEL_DELTA);
    wire gyro_fill=(held_raw[47:0]==48'd0 || held_raw[47:0]=={48{1'b1}}) &&
        (dg_x>8 || dg_y>8 || dg_z>8);
    wire quiet_sample=small_rate && norm2>=34'd3783025 && norm2<=34'd4626801 && quiet_distance;
    always @(posedge clk) begin
        checked_ready<=0;
        if(!rst_n) begin
            state<=IDLE; history_valid<=0; candidate_pending<=0; reject_detail<=0;
            quiet_count<=0; trusted<=0; candidate<=0; age<=TIMEOUT_TICKS;
            checked_raw<=0; checked_base_ok<=0;
            held_raw<=0; held_trusted<=0; held_candidate<=0; held_bias<=0;
            held_base_ok<=0; held_calibrated<=0; held_expired<=0; held_pending<=0; held_quiet<=0;
            da_x<=0; da_y<=0; da_z<=0; dg_x<=0; dg_y<=0; dg_z<=0;
            ca_x<=0; ca_y<=0; ca_z<=0; cg_x<=0; cg_y<=0; cg_z<=0;
            bg_x<=0; bg_y<=0; bg_z<=0;
            ax_square<=0; ay_square<=0; az_square<=0; norm2<=0;
            suspicion<=0; close_candidate<=0; small_rate<=0; quiet_distance<=0;
        end else begin
            if(age!=32'hFFFFFFFF) age<=age+1'b1;
            if(age>=TIMEOUT_TICKS-1) begin
                history_valid<=0; candidate_pending<=0; quiet_count<=0;
            end
            if(record_ready && state!=IDLE) begin
                // A second frame cannot overwrite an unfinished snapshot.
                // Reject the current frame and abandon the old calculation.
                state<=IDLE; candidate_pending<=0;
                checked_ready<=1; checked_raw<=raw; checked_base_ok<=base_ok;
                reject_detail<=8'h80;
            end else case(state)
                IDLE: if(record_ready) begin
                    held_raw<=raw; held_trusted<=trusted; held_candidate<=candidate;
                    held_bias<={bias_x,bias_y,bias_z}; held_base_ok<=base_ok;
                    held_calibrated<=calibrated;
                    held_expired<=!history_valid || age>=TIMEOUT_TICKS-1;
                    held_pending<=candidate_pending; held_quiet<=quiet_count;
                    state<=ARITHMETIC;
                end
                ARITHMETIC: begin
                    da_x<=distance(held_raw[95:80],held_trusted[95:80]);
                    da_y<=distance(held_raw[79:64],held_trusted[79:64]);
                    da_z<=distance(held_raw[63:48],held_trusted[63:48]);
                    dg_x<=distance(held_raw[47:32],held_trusted[47:32]);
                    dg_y<=distance(held_raw[31:16],held_trusted[31:16]);
                    dg_z<=distance(held_raw[15:0],held_trusted[15:0]);
                    ca_x<=distance(held_raw[95:80],held_candidate[95:80]);
                    ca_y<=distance(held_raw[79:64],held_candidate[79:64]);
                    ca_z<=distance(held_raw[63:48],held_candidate[63:48]);
                    cg_x<=distance(held_raw[47:32],held_candidate[47:32]);
                    cg_y<=distance(held_raw[31:16],held_candidate[31:16]);
                    cg_z<=distance(held_raw[15:0],held_candidate[15:0]);
                    bg_x<=distance(held_raw[47:32],held_calibrated ? held_bias[47:32] : 16'd0);
                    bg_y<=distance(held_raw[31:16],held_calibrated ? held_bias[31:16] : 16'd0);
                    bg_z<=distance(held_raw[15:0],held_calibrated ? held_bias[15:0] : 16'd0);
                    ax_square<=ax*ax; ay_square<=ay*ay; az_square<=az*az;
                    state<=REDUCE;
                end
                REDUCE: begin
                    norm2<={2'b0,ax_square}+{2'b0,ay_square}+{2'b0,az_square};
                    suspicion<={3'b0,gyro_fill,motion_accel_jump,motion_gyro_jump,quiet_accel_jump,quiet_gyro_jump};
                    close_candidate<=ca_x<=CONFIRM_ACCEL_DELTA && ca_y<=CONFIRM_ACCEL_DELTA && ca_z<=CONFIRM_ACCEL_DELTA &&
                        cg_x<=CONFIRM_GYRO_DELTA && cg_y<=CONFIRM_GYRO_DELTA && cg_z<=CONFIRM_GYRO_DELTA;
                    small_rate<=held_calibrated ? (bg_x<=32 && bg_y<=32 && bg_z<=32) :
                        (bg_x<=164 && bg_y<=164 && bg_z<=164);
                    quiet_distance<=da_x<=12 && da_y<=12 && da_z<=12 && dg_x<=4 && dg_y<=4 && dg_z<=4;
                    state<=DECIDE;
                end
                DECIDE: begin
                    state<=IDLE; checked_ready<=1; reject_detail<=0;
                    checked_raw<=held_raw; checked_base_ok<=held_base_ok;
                    if(!held_base_ok) begin
                        candidate_pending<=0;
                    end else if(held_expired) begin
                        trusted<=held_raw; history_valid<=1; age<=PIPELINE_DELAY;
                        candidate_pending<=0; quiet_count<=0;
                    end else if(suspicion==0) begin
                        trusted<=held_raw; history_valid<=1; age<=PIPELINE_DELAY; candidate_pending<=0;
                        if(quiet_sample) begin
                            if(held_quiet!=255) quiet_count<=held_quiet+1'b1;
                            else quiet_count<=held_quiet;
                        end else quiet_count<=0;
                    end else if(held_pending && close_candidate) begin
                        trusted<=held_raw; history_valid<=1; age<=PIPELINE_DELAY;
                        candidate_pending<=0; quiet_count<=0;
                    end else begin
                        candidate<=held_raw;
                        // An untrusted frame does not refresh the source clock.
                        // Expiration during computation must still clear pending.
                        candidate_pending<=age<TIMEOUT_TICKS-1;
                        reject_detail<=suspicion;
                    end
                end
                default: begin state<=IDLE; history_valid<=0; candidate_pending<=0; quiet_count<=0; end
            endcase
        end
    end
endmodule
