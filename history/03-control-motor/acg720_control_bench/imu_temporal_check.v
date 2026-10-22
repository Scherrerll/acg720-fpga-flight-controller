// Causal plausibility check BEFORE samples are published. It does not average
// or rewrite suspect bytes. A sudden change is withheld; a following coherent
// sample can confirm a new motion regime. This adds one sample of onset delay.
// These configurable limits are BENCH limits, not validated aircraft dynamics.
module imu_temporal_check #(
    parameter integer TIMEOUT_TICKS=2500000,
    parameter integer QUIET_SAMPLES=16,
    parameter integer QUIET_GYRO_DELTA=12,
    parameter integer QUIET_ACCEL_DELTA=32,
    // At +/-2000 dps, 1024 counts is a 62.5 dps change between records.
    // Coherent faster changes can still resume on the following sample.
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
    output reg candidate_pending=0
);
    reg history_valid=0;
    reg [95:0] trusted=0,candidate=0;
    reg [31:0] age=TIMEOUT_TICKS;
    wire quiet_active=quiet_count>=QUIET_SAMPLES;
    function [16:0] distance;
        input [15:0] a,b;
        reg signed [16:0] d;
        begin d=$signed({a[15],a})-$signed({b[15],b}); distance=d<0 ? -d : d; end
    endfunction
    wire [16:0] da_x=distance(raw[95:80],trusted[95:80]);
    wire [16:0] da_y=distance(raw[79:64],trusted[79:64]);
    wire [16:0] da_z=distance(raw[63:48],trusted[63:48]);
    wire [16:0] dg_x=distance(raw[47:32],trusted[47:32]);
    wire [16:0] dg_y=distance(raw[31:16],trusted[31:16]);
    wire [16:0] dg_z=distance(raw[15:0],trusted[15:0]);
    wire quiet_gyro_jump=quiet_active &&
        (dg_x>QUIET_GYRO_DELTA || dg_y>QUIET_GYRO_DELTA || dg_z>QUIET_GYRO_DELTA);
    wire quiet_accel_jump=quiet_active &&
        (da_x>QUIET_ACCEL_DELTA || da_y>QUIET_ACCEL_DELTA || da_z>QUIET_ACCEL_DELTA);
    wire motion_gyro_jump=!quiet_active &&
        (dg_x>MOTION_GYRO_DELTA || dg_y>MOTION_GYRO_DELTA || dg_z>MOTION_GYRO_DELTA);
    wire motion_accel_jump=!quiet_active &&
        (da_x>MOTION_ACCEL_DELTA || da_y>MOTION_ACCEL_DELTA || da_z>MOTION_ACCEL_DELTA);
    // Zero/FF gyro triplets are legal values. Only a change to that pattern,
    // with a meaningful departure from trusted data, triggers confirmation.
    wire gyro_fill=(raw[47:0]==48'd0 || raw[47:0]=={48{1'b1}}) &&
        (dg_x>8 || dg_y>8 || dg_z>8);
    wire [7:0] suspicion={3'b0,gyro_fill,motion_accel_jump,motion_gyro_jump,
        quiet_accel_jump,quiet_gyro_jump};
    wire close_candidate=
        distance(raw[95:80],candidate[95:80])<=CONFIRM_ACCEL_DELTA &&
        distance(raw[79:64],candidate[79:64])<=CONFIRM_ACCEL_DELTA &&
        distance(raw[63:48],candidate[63:48])<=CONFIRM_ACCEL_DELTA &&
        distance(raw[47:32],candidate[47:32])<=CONFIRM_GYRO_DELTA &&
        distance(raw[31:16],candidate[31:16])<=CONFIRM_GYRO_DELTA &&
        distance(raw[15:0],candidate[15:0])<=CONFIRM_GYRO_DELTA;
    wire signed [15:0] ax=raw[95:80],ay=raw[79:64],az=raw[63:48];
    wire [31:0] ax2=ax*ax,ay2=ay*ay,az2=az*az;
    wire [33:0] norm2={2'b0,ax2}+{2'b0,ay2}+{2'b0,az2};
    wire small_rate=calibrated ?
        (distance(raw[47:32],bias_x)<=32 && distance(raw[31:16],bias_y)<=32 && distance(raw[15:0],bias_z)<=32) :
        (distance(raw[47:32],16'd0)<=164 && distance(raw[31:16],16'd0)<=164 && distance(raw[15:0],16'd0)<=164);
    wire quiet_sample=small_rate && norm2>=34'd3783025 && norm2<=34'd4626801 &&
        da_x<=12 && da_y<=12 && da_z<=12 && dg_x<=4 && dg_y<=4 && dg_z<=4;
    always @(posedge clk) begin
        checked_ready<=0;
        if(!rst_n) begin
            history_valid<=0; candidate_pending<=0; reject_detail<=0;
            quiet_count<=0; trusted<=0; candidate<=0; age<=TIMEOUT_TICKS;
        end else begin
            if(age!=32'hFFFFFFFF) age<=age+1'b1;
            if(age>=TIMEOUT_TICKS-1) begin
                history_valid<=0; candidate_pending<=0; quiet_count<=0;
            end
            if(record_ready) begin
                checked_ready<=1; reject_detail<=0;
                if(!base_ok) begin
                    // A bad register/status record cannot confirm a pending motion.
                    candidate_pending<=0;
                end else if(!history_valid || age>=TIMEOUT_TICKS-1) begin
                    trusted<=raw; history_valid<=1; age<=0;
                    candidate_pending<=0; quiet_count<=0;
                end else if(suspicion==0) begin
                    trusted<=raw; age<=0; candidate_pending<=0;
                    if(quiet_sample) begin
                        if(quiet_count!=255) quiet_count<=quiet_count+1'b1;
                    end else quiet_count<=0;
                end else if(candidate_pending && close_candidate) begin
                    // Confirm ONLY the current coherent frame. The held suspect
                    // frame is never released retrospectively or used as a sample.
                    trusted<=raw; age<=0; candidate_pending<=0; quiet_count<=0;
                end else begin
                    candidate<=raw; candidate_pending<=1; reject_detail<=suspicion;
                    // Do not let an untrusted frame move the baseline/window.
                end
            end
        end
    end
endmodule
