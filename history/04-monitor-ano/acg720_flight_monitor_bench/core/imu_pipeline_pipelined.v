// Copied from the measured attitude bench by generate_project.py.
// Sensor coordinates only; the control top converts measured mounting directions.
module imu_pipeline #(parameter integer CAL_SAMPLES=256,
    parameter integer DATA_TIMEOUT_TICKS=3000000)(
    input wire clk50,rst_n,imu_miso,
    output wire imu_sck,imu_mosi,imu_cs_n,
    output wire calibrated,attitude_valid,attitude_update,link_usable,
    output wire [95:0] accepted_raw,
    output wire [31:0] dt_ticks,accepted_count,rejected_count,
    output wire [7:0] reason,who,pwr,attitude_fault,
    output wire [15:0] cal_count,
    output wire signed [15:0] roll,pitch,bias_x,bias_y,bias_z
);
    wire record_ready;
    wire [95:0] record_raw;
    wire [7:0] gyro_cfg,accel_cfg,filter_cfg,int_status;
    icm42688_reader reader(.clk(clk50),.rst_n(rst_n),.miso(imu_miso),
        .sck(imu_sck),.mosi(imu_mosi),.cs_n(imu_cs_n),
        .record_ready(record_ready),.record_raw(record_raw),.record_who(who),
        .record_pwr(pwr),.record_gyro(gyro_cfg),.record_accel(accel_cfg),
        .record_filter(filter_cfg),.record_status(int_status));
    wire [7:0] base_extra={1'b0,!int_status[3],
        (gyro_cfg!=8'h07 || accel_cfg!=8'h07 || filter_cfg!=8'h44),5'b0};
    wire invalid_axis=record_raw[95:80]==16'h8000 || record_raw[79:64]==16'h8000 ||
        record_raw[63:48]==16'h8000 || record_raw[47:32]==16'h8000 ||
        record_raw[31:16]==16'h8000 || record_raw[15:0]==16'h8000;
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
    imu_checked_guard_pipelined #(.TIMEOUT_TICKS(DATA_TIMEOUT_TICKS),.USE_PRECHECKED(1)) guard(.clk(clk50),.rst_n(rst_n),.record_ready(checked_ready),.origin_record_ready(origin_record_ready),
        .checked_base_ok(checked_base_ok),
        .who(guard_who),.pwr(guard_pwr),.raw(checked_raw),.extra_reason(extra_reason),
        .sample_valid(sample_valid),.accepted_raw(accepted_raw),.sample_dt_ticks(dt_ticks),
        .link_usable(link_usable),.stale(),.reject_reason(reason),
        .accepted_count(accepted_count),.rejected_count(rejected_count),.bad_streak(),.age_ticks());
    reg reject_event=0;
    always @(posedge clk50) reject_event <= rst_n && checked_ready && (!checked_base_ok || (|temporal_detail));


    tilt_estimator #(.CAL_SAMPLES(CAL_SAMPLES),.MAX_DT_TICKS(DATA_TIMEOUT_TICKS)) estimator(.clk(clk50),.rst_n(rst_n),.sample_valid(sample_valid),
        .link_usable(link_usable),.raw(accepted_raw),.dt_ticks(dt_ticks),
        .reject_event(reject_event),
        .calibrated(calibrated),.attitude_valid(attitude_valid),.update(attitude_update),
        .roll_cdeg(roll),.pitch_cdeg(pitch),.bias_x(bias_x),.bias_y(bias_y),.bias_z(bias_z),
        .cal_count(cal_count),.fault(attitude_fault),.accel_correction(accel_correction));

endmodule
