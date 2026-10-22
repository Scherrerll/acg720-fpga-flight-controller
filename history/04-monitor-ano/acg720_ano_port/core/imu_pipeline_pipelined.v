// Copied from the measured attitude bench by generate_project.py.
// Sensor coordinates only; the control top converts measured mounting directions.
module imu_pipeline #(
    parameter integer LEVEL_TRIM_ENABLE=0,
    parameter signed [31:0] LEVEL_R00_Q24=16777216,
    parameter signed [31:0] LEVEL_R01_Q24=0,
    parameter signed [31:0] LEVEL_R02_Q24=0,
    parameter signed [31:0] LEVEL_R10_Q24=0,
    parameter signed [31:0] LEVEL_R11_Q24=16777216,
    parameter signed [31:0] LEVEL_R12_Q24=0,
    parameter signed [31:0] LEVEL_R20_Q24=0,
    parameter signed [31:0] LEVEL_R21_Q24=0,
    parameter signed [31:0] LEVEL_R22_Q24=16777216,
    parameter integer CAL_SAMPLES=256,
    parameter integer DATA_TIMEOUT_TICKS=3000000)(
    input wire clk50,rst_n,imu_miso,
    output wire imu_sck,imu_mosi,imu_cs_n,
    output wire calibrated,attitude_valid,attitude_update,link_usable,
    output wire [95:0] accepted_raw,
    output wire [31:0] dt_ticks,accepted_count,rejected_count,
    output wire [7:0] reason,who,pwr,attitude_fault,
    output wire [15:0] cal_count,
    output wire signed [15:0] roll,pitch,yaw,bias_x,bias_y,bias_z,
    output wire signed [15:0] filtered_gx,filtered_gy,filtered_gz,
    output wire signed [31:0] world_ax,world_ay,world_az_mmps2,
    output wire linear_accel_valid,
    output wire [31:0] accepted_raw_age_ticks
);
    wire record_ready;
    wire [95:0] record_raw;
    wire [7:0] gyro_cfg,accel_cfg,gyro1_cfg,accel1_cfg,filter_cfg,int_status;
    icm42688_reader reader(.clk(clk50),.rst_n(rst_n),.miso(imu_miso),
        .sck(imu_sck),.mosi(imu_mosi),.cs_n(imu_cs_n),
        .record_ready(record_ready),.record_raw(record_raw),.record_who(who),
        .record_pwr(pwr),.record_gyro(gyro_cfg),.record_accel(accel_cfg),
        .record_gyro1(gyro1_cfg),.record_accel1(accel1_cfg),
        .record_filter(filter_cfg),.record_status(int_status));
    wire [7:0] base_extra={1'b0,!int_status[3],
        (gyro_cfg!=8'h06 || accel_cfg!=8'h06 || gyro1_cfg!=8'h16 ||
         accel1_cfg!=8'h0D || filter_cfg!=8'h77),5'b0};
    // Reset INTF_CONFIG0=30 uses mode0; FSYNC_CONFIG=10 tags temperature.
    // Both8000 and8001 are unusable axis encodings in this sensor mode.
    // Reject before temporal candidates, calibration, LPF or quaternion work.
    // 8002 and7FFF remain digitally legal endpoints.
    wire invalid_axis=record_raw[95:81]==15'h4000 || record_raw[79:65]==15'h4000 ||
        record_raw[63:49]==15'h4000 || record_raw[47:33]==15'h4000 ||
        record_raw[31:17]==15'h4000 || record_raw[15:1]==15'h4000;
    wire base_ok=who==8'h47 && pwr==8'h0F && base_extra==0 &&
        record_raw!=96'd0 && record_raw!={96{1'b1}} && !invalid_axis;
    wire checked_ready,candidate_pending;
    wire [95:0] checked_raw;
    wire checked_base_ok;
    reg origin_record_ready=0;
    reg [7:0] guard_who=0,guard_pwr=0,guard_base_extra=0;
    always @(posedge clk50) begin
        if(!rst_n) begin origin_record_ready<=0; guard_who<=0; guard_pwr<=0; guard_base_extra<=0; end
        else begin
            origin_record_ready<=record_ready;
            if(record_ready) begin guard_who<=who; guard_pwr<=pwr; guard_base_extra<=base_extra; end
        end
    end
    wire [7:0] temporal_detail,quiet_count;
    wire [7:0] extra_reason=guard_base_extra | ((|temporal_detail) ? 8'h80 : 8'h00);
    wire sample_valid;



    wire accel_correction;

    imu_temporal_check #(.TIMEOUT_TICKS(DATA_TIMEOUT_TICKS)) temporal(.clk(clk50),.rst_n(rst_n),.record_ready(record_ready),
        .base_ok(base_ok),.calibrated(calibrated),.raw(record_raw),
        .bias_x(bias_x),.bias_y(bias_y),.bias_z(bias_z),
        .checked_ready(checked_ready),.reject_detail(temporal_detail),
        .quiet_count(quiet_count),.candidate_pending(candidate_pending),
        .checked_raw(checked_raw),.checked_base_ok(checked_base_ok));
    // A rejected raw record is not fresh data. Keep a qualified pose epoch
    // through short gaps; guard/core60ms source-age protection still revokes.
    // Independent configuration confirmation decides recovery after rejecting bad raw.
    // Soft reset still keeps the original OFF-safe 100/100/50ms recovery timing.
    imu_checked_guard_pipelined #(.TIMEOUT_TICKS(DATA_TIMEOUT_TICKS),.USE_PRECHECKED(1),.BAD_STREAK_REVOKES_LINK(0)) guard(.clk(clk50),.rst_n(rst_n),.record_ready(checked_ready),.origin_record_ready(origin_record_ready),
        .checked_base_ok(checked_base_ok),
        .who(guard_who),.pwr(guard_pwr),.raw(checked_raw),.extra_reason(extra_reason),
        .sample_valid(sample_valid),.accepted_raw(accepted_raw),.sample_dt_ticks(dt_ticks),
        .link_usable(link_usable),.stale(),.reject_reason(reason),
        .accepted_count(accepted_count),.rejected_count(rejected_count),.bad_streak(),.age_ticks(accepted_raw_age_ticks));
    reg reject_event=0;
    always @(posedge clk50) reject_event <= rst_n && checked_ready && (!checked_base_ok || (|temporal_detail));


    ano_attitude_estimator #(.LEVEL_TRIM_ENABLE(LEVEL_TRIM_ENABLE),.LEVEL_R00_Q24(LEVEL_R00_Q24),.LEVEL_R01_Q24(LEVEL_R01_Q24),.LEVEL_R02_Q24(LEVEL_R02_Q24),.LEVEL_R10_Q24(LEVEL_R10_Q24),.LEVEL_R11_Q24(LEVEL_R11_Q24),.LEVEL_R12_Q24(LEVEL_R12_Q24),.LEVEL_R20_Q24(LEVEL_R20_Q24),.LEVEL_R21_Q24(LEVEL_R21_Q24),.LEVEL_R22_Q24(LEVEL_R22_Q24),.CAL_SAMPLES(CAL_SAMPLES),.MAX_DT_TICKS(DATA_TIMEOUT_TICKS)) estimator(.clk(clk50),.rst_n(rst_n),.sample_valid(sample_valid),
        .link_usable(link_usable),.raw(accepted_raw),.dt_ticks(dt_ticks),
        .reject_event(reject_event),
        .calibrated(calibrated),.attitude_valid(attitude_valid),.update(attitude_update),
        .roll_cdeg(roll),.pitch_cdeg(pitch),.yaw_cdeg(yaw),.bias_x(bias_x),.bias_y(bias_y),.bias_z(bias_z),
        .cal_count(cal_count),.fault(attitude_fault),.accel_correction(accel_correction),
        .filtered_gx(filtered_gx),.filtered_gy(filtered_gy),.filtered_gz(filtered_gz),
        .world_ax_mmps2(world_ax),.world_ay_mmps2(world_ay),.world_az_mmps2(world_az_mmps2),.linear_accel_valid(linear_accel_valid));

endmodule
