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
    output wire imu_sck,imu_mosi,imu_cs_n,imu_gyro_cs_n,
    output wire yaw_range_ok,
    output wire calibrated,attitude_valid,attitude_update,link_usable,
    output wire [95:0] accepted_raw,
    output wire [31:0] dt_ticks,accepted_count,rejected_count,
    output wire [7:0] reason,who,pwr,attitude_fault,
    output wire [15:0] cal_count,
    output wire signed [15:0] roll,pitch,yaw,bias_x,bias_y,bias_z,
    output wire signed [15:0] filtered_gx,filtered_gy,filtered_gz,
    output wire signed [31:0] filtered_gx_q12,filtered_gy_q12,filtered_gz_q12,
    output wire signed [31:0] world_ax,world_ay,world_az_mmps2,
    output wire linear_accel_valid,
    output wire [31:0] accepted_raw_age_ticks,

// DIAG_TAP_BEGIN
 input wire diag_taking_off,diag_gate_event,
 output wire diag_raw_valid,diag_pose_valid,diag_fault_valid,
 output wire [207:0] diag_raw_body,
 output wire [223:0] diag_pose_body,
 output wire [703:0] diag_fault_body,
 output wire [31:0] diag_raw_tick,diag_pose_tick,diag_fault_tick,
 output wire [31:0] diag_clock_ticks,diag_max_accept_gap,diag_raw_count,diag_pose_count,
// DIAG_TAP_END
 output wire tilt4500_ok
);

// DIAG_TAP_BEGIN
    wire [31:0] diag_source_id,diag_source_tick,diag_recovery_count,diag_consumed_id,diag_held_dt;
    wire [9:0] diag_reader_meta;
    wire [95:0] diag_trusted,diag_candidate;
    wire diag_qualified,diag_stale,diag_initialized,diag_ready,diag_reseed;
    wire [7:0] diag_state,diag_resume,diag_reseed_count,diag_first_cause;
// DIAG_TAP_END
    wire record_ready;
    wire [95:0] record_raw;
    // WHO=actual accel ID; legacy PWR byte=actual gyro ID in this profile.
    // Records are normalized to2048counts/g and16.4counts/(deg/s).
    wire reader_valid,reader_config_ok;
    wire [7:0] reader_fault;
    bmi088_reader reader(.clk(clk50),.rst_n(rst_n),.miso(imu_miso),
        .sck(imu_sck),.mosi(imu_mosi),.accel_cs_n(imu_cs_n),.gyro_cs_n(imu_gyro_cs_n),
        .record_ready(record_ready),.record_raw(record_raw),.record_valid(reader_valid),
        .accel_id(who),.gyro_id(pwr),.config_ok(reader_config_ok),.record_fault(reader_fault));
    wire [7:0] base_extra=reader_fault | ((!reader_valid || !reader_config_ok) ? 8'h40 : 8'h00);
    // Native BMI signed endpoints are legal. The adapter explicitly rejects
    // only unrepresentable normalized values before the unchanged estimator.
    wire base_ok=reader_valid && reader_config_ok && base_extra==0 &&
        who==8'h1e && pwr==8'h0f && record_raw!=96'd0 && record_raw!={96{1'b1}};
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
        .checked_raw(checked_raw),.checked_base_ok(checked_base_ok)
// DIAG_TAP_BEGIN
 ,.diag_source_id_in(diag_raw_count+32'd1),.diag_tick_in(diag_clock_ticks),
 .diag_reader_meta_in({reader_fault,reader_config_ok,reader_valid}),
 .diag_source_id_out(diag_source_id),.diag_tick_out(diag_source_tick),
 .diag_reader_meta_out(diag_reader_meta),.diag_trusted_out(diag_trusted),.diag_candidate_out(diag_candidate)
// DIAG_TAP_END
);
    // A rejected raw record is not fresh data. Keep a qualified pose epoch
    // through short gaps; guard/core60ms source-age protection still revokes.
    // Independent configuration confirmation decides recovery after rejecting bad raw.
    // BMI reset/configuration settling is owned by the isolated reader.
    imu_checked_guard_pipelined #(.TIMEOUT_TICKS(DATA_TIMEOUT_TICKS),.USE_PRECHECKED(1),.BAD_STREAK_REVOKES_LINK(0)) guard(.clk(clk50),.rst_n(rst_n),.record_ready(checked_ready),.origin_record_ready(origin_record_ready),
        .checked_base_ok(checked_base_ok),
        .who(guard_who),.pwr(guard_pwr),.raw(checked_raw),.extra_reason(extra_reason),
        .sample_valid(sample_valid),.accepted_raw(accepted_raw),.sample_dt_ticks(dt_ticks),
        .link_usable(link_usable),.stale(),.reject_reason(reason),
        .accepted_count(accepted_count),.rejected_count(rejected_count),.bad_streak(),.age_ticks(accepted_raw_age_ticks)
// DIAG_TAP_BEGIN
 ,.diag_qualified(diag_qualified),.diag_recovery_count(diag_recovery_count)
// DIAG_TAP_END
);
    reg reject_event=0;
    always @(posedge clk50) reject_event <= rst_n && checked_ready && (!checked_base_ok || (|temporal_detail));


    ano_attitude_estimator #(.LEVEL_TRIM_ENABLE(LEVEL_TRIM_ENABLE),.LEVEL_R00_Q24(LEVEL_R00_Q24),.LEVEL_R01_Q24(LEVEL_R01_Q24),.LEVEL_R02_Q24(LEVEL_R02_Q24),.LEVEL_R10_Q24(LEVEL_R10_Q24),.LEVEL_R11_Q24(LEVEL_R11_Q24),.LEVEL_R12_Q24(LEVEL_R12_Q24),.LEVEL_R20_Q24(LEVEL_R20_Q24),.LEVEL_R21_Q24(LEVEL_R21_Q24),.LEVEL_R22_Q24(LEVEL_R22_Q24),.CAL_SAMPLES(CAL_SAMPLES),.MAX_DT_TICKS(DATA_TIMEOUT_TICKS)) estimator(.clk(clk50),.rst_n(rst_n),.sample_valid(sample_valid),
        .link_usable(link_usable),.raw(accepted_raw),.dt_ticks(dt_ticks),
        .reject_event(reject_event),
        .calibrated(calibrated),.attitude_valid(attitude_valid),.update(attitude_update),
        .roll_cdeg(roll),.pitch_cdeg(pitch),.yaw_cdeg(yaw),.yaw_range_ok(yaw_range_ok),.tilt4500_ok(tilt4500_ok),.bias_x(bias_x),.bias_y(bias_y),.bias_z(bias_z),
        .cal_count(cal_count),.fault(attitude_fault),.accel_correction(accel_correction),
        .filtered_gx(filtered_gx),.filtered_gy(filtered_gy),.filtered_gz(filtered_gz),
        .filtered_gx_q12(filtered_gx_q12),.filtered_gy_q12(filtered_gy_q12),.filtered_gz_q12(filtered_gz_q12),
        .world_ax_mmps2(world_ax),.world_ay_mmps2(world_ay),.world_az_mmps2(world_az_mmps2),.linear_accel_valid(linear_accel_valid)
// DIAG_TAP_BEGIN
 ,.diag_accepted_id(accepted_count),.diag_state(diag_state),.diag_resume_state(diag_resume),
 .diag_reseed_count(diag_reseed_count),.diag_initialized(diag_initialized),.diag_ready(diag_ready),
 .diag_reseed(diag_reseed),.diag_consumed_accepted_id(diag_consumed_id),.diag_held_dt(diag_held_dt),
 .diag_first_cause(diag_first_cause)
// DIAG_TAP_END
);


// DIAG_TAP_BEGIN
    // Diagnostics are one-way consumers. No tap output qualifies source/control.
    assign diag_stale=accepted_raw_age_ticks>=DATA_TIMEOUT_TICKS;
    imu_diagnostic_tap diagnostic_tap(.clk(clk50),.rst_n(rst_n),
      .taking_off(diag_taking_off),.gate_event(diag_gate_event),.record_ready(record_ready),
      .checked_ready(checked_ready),.checked_raw(checked_raw),.checked_base_ok(checked_base_ok),
      .source_id(diag_source_id),.source_tick(diag_source_tick),.reader_meta(diag_reader_meta),
      .trusted(diag_trusted),.candidate(diag_candidate),.temporal_detail(temporal_detail),
      .quiet_count(quiet_count),.candidate_pending(candidate_pending),
      .accepted(sample_valid),.accepted_count(accepted_count),.accepted_age(accepted_raw_age_ticks),
      .link_usable(link_usable),.guard_qualified(diag_qualified),.guard_stale(diag_stale),
      .recovery_count(diag_recovery_count),.attitude_update(attitude_update),.attitude_valid(attitude_valid),
      .linear_accel_valid(linear_accel_valid),.calibrated(calibrated),.initialized(diag_initialized),
      .ready(diag_ready),.reseed(diag_reseed),.reseed_count(diag_reseed_count),
      .estimator_state(diag_state),.resume_state(diag_resume),.first_cause(diag_first_cause),
      .consumed_id(diag_consumed_id),.held_dt(diag_held_dt),.attitude_fault(attitude_fault),
      .world_ax(world_ax),.world_ay(world_ay),.world_az(world_az_mmps2),
      .roll(roll),.pitch(pitch),.yaw(yaw),.raw_valid(diag_raw_valid),.raw_body(diag_raw_body),
      .raw_tick(diag_raw_tick),.pose_valid(diag_pose_valid),.pose_body(diag_pose_body),.pose_tick(diag_pose_tick),
      .fault_valid(diag_fault_valid),.fault_body(diag_fault_body),.fault_tick(diag_fault_tick),
      .clock_ticks(diag_clock_ticks),.max_accept_gap(diag_max_accept_gap),
      .raw_count(diag_raw_count),.pose_count(diag_pose_count));
// DIAG_TAP_END
endmodule
