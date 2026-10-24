// ANO default-gain controller port; mounted body axes and fault gates retained.
// Full output profile is compiled offline; board release requires stopped-board checks.
module flight_core #(
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
    parameter integer RUN_MAX_US=2000,
    parameter integer RUN_MIN_US=1200, // ANO default idle_speed_pwm20% =>1000+200us
    parameter integer CAL_SAMPLES=2048,
    parameter integer OUTPUT_FRAME_US=2500,
    parameter integer ARM_LOW_TICKS=25000000,
    parameter integer ARM_HIGH_TICKS=25000000,
    parameter integer FLIGHT_STATE_TICKS_PER_MS=50000,
    parameter integer POSE_TIMEOUT_TICKS=3000000, // 60 ms at 50 MHz; bench experiment
    parameter integer TAKEOVER_PICKUP_TICKS=5000000,
    parameter integer RAW_TELEMETRY_COMMANDS=0 // Display snapshot transport only.
)(
    input wire clk50,imu_miso,rc_ppm_in,
    input wire hold_active,altitude_active,vertical_available,auto_takeoff,
    input wire signed [17:0] pilot_norm_x,pilot_norm_y,
    input wire pilot_norm_update,pilot_norm_valid,input wire [15:0] pilot_norm_dt_us,
    output wire taking_off_out,
    output wire height_fallback_active,
    output wire [3:0] flight_state_flags,
    input wire signed [31:0] vertical_height_mm,
    input wire signed [15:0] hold_roll_cdeg,hold_pitch_cdeg,hold_throttle_delta_us,
    input wire [15:0] hold_collective_us,
    output wire imu_sck,imu_mosi,imu_cs_n,imu_gyro_cs_n,
    output reg led2=0,
    output wire led3,
    output wire motor1_pwm,motor2_pwm,motor3_pwm,motor4_pwm,
    output wire rc_valid,
    output wire [3:0] channel_count,
    output wire [15:0] ch1,ch2,ch3,ch4,ch5,ch6,ch7,ch8,
    output wire body_yaw_range_ok,
    output wire pose_update,pose_valid,
    output wire [31:0] pose_dt_ticks,pose_age_ticks,
    output wire signed [15:0] body_roll_cdeg,body_pitch_cdeg,body_yaw_cdeg,
    output wire signed [16:0] body_gx,body_gy,body_gz,
    output wire signed [28:0] body_gx_q12,body_gy_q12,body_gz_q12,
    output wire armed_usable,control_enabled,command_fresh,
    output wire armed_raw,hold_consumed,altitude_consumed,
    output wire [15:0] base_throttle_us,
    output wire throttle_takeover_active,
    output wire [15:0] throttle_pickup_us,
    output wire [7:0] sticky_yaw_fault,
    output wire signed [31:0] world_ax_mmps2,world_ay_mmps2,world_az_up_mmps2,
    output wire linear_accel_valid,
    output wire signed [15:0] raw_ax_counts,raw_ay_counts,raw_az_counts,
    output wire raw_accel_valid,
    output wire [31:0] raw_accel_age_ticks,
    output wire [863:0] telemetry_body
);
    reg [7:0] boot=0;
    always @(posedge clk50) if(boot!=8'hFF) boot<=boot+1'b1;
    wire rst_n=boot==8'hFF;
    reg [24:0] heartbeat=0;
    always @(posedge clk50) begin
        if(heartbeat==24999999) begin heartbeat<=0; led2<=~led2; end
        else heartbeat<=heartbeat+1'b1;
    end
    wire calibrated,attitude_valid,attitude_update,link_usable;
    wire [95:0] accepted_raw;
    wire [31:0] dt_ticks,accepted_count,rejected_count;
    wire [7:0] imu_reason,who,pwr,attitude_fault;
    wire [15:0] cal_count;
    wire signed [15:0] sensor_roll,sensor_pitch,sensor_yaw,bias_x,bias_y,bias_z,filtered_gx,filtered_gy,filtered_gz;
    wire signed [31:0] sensor_world_ax,sensor_world_ay,sensor_world_az;
    wire signed [31:0] fine_gx,fine_gy,fine_gz;
    // Normalized raw +/-32767, startup bias <=164 counts, orthonormal
    // mounting: sqrt(3)*(32767+164)<57039 counts fits signed29 Q12.
    wire signed [28:0] gx_q12=fine_gx;
    wire signed [28:0] gy_q12=-$signed(fine_gy);
    wire signed [28:0] gz_q12=-$signed(fine_gz);
    imu_pipeline #(.LEVEL_TRIM_ENABLE(LEVEL_TRIM_ENABLE),.LEVEL_R00_Q24(LEVEL_R00_Q24),.LEVEL_R01_Q24(LEVEL_R01_Q24),.LEVEL_R02_Q24(LEVEL_R02_Q24),.LEVEL_R10_Q24(LEVEL_R10_Q24),.LEVEL_R11_Q24(LEVEL_R11_Q24),.LEVEL_R12_Q24(LEVEL_R12_Q24),.LEVEL_R20_Q24(LEVEL_R20_Q24),.LEVEL_R21_Q24(LEVEL_R21_Q24),.LEVEL_R22_Q24(LEVEL_R22_Q24),.CAL_SAMPLES(CAL_SAMPLES),.DATA_TIMEOUT_TICKS(POSE_TIMEOUT_TICKS)) imu(
        .clk50(clk50),.rst_n(rst_n),.imu_miso(imu_miso),
        .imu_sck(imu_sck),.imu_mosi(imu_mosi),.imu_cs_n(imu_cs_n),.imu_gyro_cs_n(imu_gyro_cs_n),
        .calibrated(calibrated),.attitude_valid(attitude_valid),
        .attitude_update(attitude_update),.link_usable(link_usable),
        .accepted_raw(accepted_raw),.dt_ticks(dt_ticks),
        .accepted_count(accepted_count),.rejected_count(rejected_count),
        .reason(imu_reason),.who(who),.pwr(pwr),.attitude_fault(attitude_fault),
        .cal_count(cal_count),.roll(sensor_roll),.pitch(sensor_pitch),.yaw(sensor_yaw),.yaw_range_ok(body_yaw_range_ok),
        .filtered_gx(filtered_gx),.filtered_gy(filtered_gy),.filtered_gz(filtered_gz),
        .filtered_gx_q12(fine_gx),.filtered_gy_q12(fine_gy),.filtered_gz_q12(fine_gz),
        .world_ax(sensor_world_ax),.world_ay(sensor_world_ay),.world_az_mmps2(sensor_world_az),.linear_accel_valid(linear_accel_valid),
        .accepted_raw_age_ticks(raw_accel_age_ticks),
        .bias_x(bias_x),.bias_y(bias_y),.bias_z(bias_z));
    // Keep the checked observer in its established sensor frame. Convert its
    // derived tilt and corrected gyro TOGETHER at the control interface.
    // Body: X forward/Y right/Z down; roll right-side-down, pitch nose-up,
    // clockwise yaw viewed from above are positive. Current fixed mounting:
    // gyro_body=diag(+1,-1,-1)*gyro_sensor (proper rotation, determinant +1).
    wire signed [15:0] roll=sensor_roll;
    wire signed [15:0] pitch=-sensor_pitch;
    wire signed [15:0] raw_gx=accepted_raw[47:32];
    wire signed [15:0] raw_gy=accepted_raw[31:16];
    wire signed [15:0] raw_gz=accepted_raw[15:0];
    wire signed [16:0] gx={filtered_gx[15],filtered_gx};
    // bias-raw equals -(raw-bias), without a second adder or 16-bit negation.
    // Full corrected range is -65535..65535, retained in signed17.
    wire signed [16:0] gy=-$signed({filtered_gy[15],filtered_gy});
    wire signed [16:0] gz=-$signed({filtered_gz[15],filtered_gz});
    wire [15:0] rc_sequence;
    wire rc_update;
    rc_ppm receiver(.clk(clk50),.rst_n(rst_n),.ppm_in(rc_ppm_in),
        .frame_update(rc_update),.valid(rc_valid),.channel_count(channel_count),
        .ch1(ch1),.ch2(ch2),.ch3(ch3),.ch4(ch4),.ch5(ch5),.ch6(ch6),.ch7(ch7),.ch8(ch8),
        .frame_sequence(rc_sequence));

    // Targets and feedback use the same BODY frame. Stick polarity, rotor
    // directions and gains still require physical verification before flight.
    function signed [31:0] yaw_target;
        input [15:0] channel;
        reg signed [31:0] deviation;
        begin
            deviation=$signed({1'b0,channel})-32'sd1500;
            if(deviation>500) deviation=500;
            if(deviation< -500) deviation=-500;
            deviation=deviation>65 ? deviation-65 : deviation< -65 ? deviation+65 : 0;
            yaw_target=(deviation*46/100)*100; // source truncates integer deg/s before scaling
            if(yaw_target>20000) yaw_target=20000;
            if(yaw_target< -20000) yaw_target=-20000;
        end
    endfunction
    localparam RUN_RANGE_OK=RUN_MIN_US>=1000 && RUN_MIN_US<RUN_MAX_US && RUN_MAX_US<=2000;
    // Invalid configuration fails closed in synthesis and is rejected in simulation.
    generate if(!RUN_RANGE_OK) begin : invalid_run_min
        initial $fatal(1,"require 1000 <= RUN_MIN_US < RUN_MAX_US <= 2000");
    end endgenerate
    function signed [15:0] bounded_hold_angle;
        input signed [15:0] angle;
        begin bounded_hold_angle=angle>16'sd2500 ? 16'sd2500 :
            angle< -16'sd2500 ? -16'sd2500 : angle;end
    endfunction
    // Register mode selection before target muxes. Public motor validity is
    // still masked by live RC/sensor predicates, independently of this.
    reg hold_override=0,altitude_override=0;
    reg controller_run=0;
    wire controller_enabled;
    reg yaw_sample_update=0;
    reg [31:0] yaw_dt_accum=0,yaw_dt_ticks=0;
    // Source Att_2level_Ctrl updates ATT_STAB trim before taking_off clears
    // its public angle target. Keep that6ms callback alive while stopped;
    // yaw/inner control retain their separate enable/reset schedules.
    reg manual_outer_update=0;
    reg [31:0] manual_outer_dt_accum=0,manual_outer_dt_ticks=0;
    always @(posedge clk50) begin
        if(!rst_n) begin hold_override<=0;altitude_override<=0;end
        else begin hold_override<=hold_active && control_enabled && !height_fallback_active;altitude_override<=altitude_active && control_enabled && !height_fallback_active;end
    end
    wire signed [15:0] manual_roll_cdeg,manual_pitch_cdeg;
    wire manual_angle_update,manual_angle_busy;
    wire [7:0] manual_angle_fault;
    // Warm independent RC path: native-height loss must not freeze pilot input.
    reg [19:0] fallback_stick_phase=0;
    reg fallback_stick_tick=0;
    always @(posedge clk50)begin
        fallback_stick_tick<=0;
        if(!rst_n || !rc_valid)fallback_stick_phase<=0;
        else if(fallback_stick_phase==499999)begin fallback_stick_phase<=0;fallback_stick_tick<=1;end
        else fallback_stick_phase<=fallback_stick_phase+1'b1;
    end
    wire signed [17:0] fallback_norm_x,fallback_norm_y;
    wire fallback_norm_update,fallback_norm_valid,fallback_norm_fault;
    wire [15:0] fallback_norm_dt;
    ano_xy_stick fallback_sticks(.clk(clk50),.rst_n(rst_n),.enabled(rc_valid),
        .sample_update(fallback_stick_tick),.sample_dt_us(32'd10000),.ch1(ch1),.ch2(ch2),
        .nx(fallback_norm_x),.ny(fallback_norm_y),.busy(),.fault(fallback_norm_fault),
        .update(fallback_norm_update),.valid(fallback_norm_valid),.output_dt_us(fallback_norm_dt));
    wire selected_norm_update=height_fallback_active ?fallback_norm_update:pilot_norm_update;
    wire selected_norm_valid=height_fallback_active ?fallback_norm_valid:pilot_norm_valid;
    wire [15:0] selected_norm_dt=height_fallback_active ?fallback_norm_dt:pilot_norm_dt_us;
    wire signed [17:0] selected_norm_x=height_fallback_active ?fallback_norm_x:pilot_norm_x;
    wire signed [17:0] selected_norm_y=height_fallback_active ?fallback_norm_y:pilot_norm_y;
    wire source_loc_selected=rc_valid && channel_count>=7 && ch7>=1800 && ch7<=2200;
    wire signed [15:0] manual_snapshot_roll,manual_snapshot_pitch;
    ano_manual_angles manual_angles(.clk(clk50),.rst_n(rst_n),
        .sample_update(selected_norm_update),.norm_valid(selected_norm_valid),.norm_dt_us(selected_norm_dt),
        .norm_roll_q16(selected_norm_y),.norm_pitch_q16(selected_norm_x),
        .loc_override(hold_active && !height_fallback_active),.loc_roll_cdeg(hold_roll_cdeg),.loc_pitch_cdeg(hold_pitch_cdeg),
        .outer_update(manual_outer_update),.outer_dt_ticks(manual_outer_dt_ticks),
        .enabled(controller_enabled),.att_stab(!source_loc_selected || height_fallback_active),
        .roll_cdeg(roll),.pitch_cdeg(pitch),
        .update(manual_angle_update),.busy(manual_angle_busy),.fault(manual_angle_fault),
        .snapshot_roll_cdeg(manual_snapshot_roll),.snapshot_pitch_cdeg(manual_snapshot_pitch),
        .manual_roll_cdeg(manual_roll_cdeg),.manual_pitch_cdeg(manual_pitch_cdeg));
    wire signed [15:0] target_roll=hold_override ? bounded_hold_angle(hold_roll_cdeg) : manual_roll_cdeg;
    // Measured radio: CH2 increases when pushing forward (nose down).
    // Body pitch is nose-up positive; source angle limit is +/-25 degrees.
    wire signed [15:0] target_pitch=hold_override ? bounded_hold_angle(hold_pitch_cdeg) : -manual_pitch_cdeg;
    // Bounded source stick conversion has separate clocks for deadzone,
    // multiply, integer-deg/s division and cdeg/s conversion. Radio updates
    // are far slower; health/stop predicates remain immediate.
    reg signed [10:0] yaw_deviation_q=0;
    reg signed [9:0] yaw_dead_q=0;
    reg signed [15:0] yaw_product_q=0;
    reg signed [8:0] yaw_dps_q=0;
    reg signed [31:0] stick_yaw=0;
    always @(posedge clk50) begin
        yaw_deviation_q<=ch4<=1000 ? -11'sd500:ch4>=2000 ? 11'sd500:$signed({1'b0,ch4})-17'sd1500;
        yaw_dead_q<=yaw_deviation_q>65 ? yaw_deviation_q-11'sd65:yaw_deviation_q< -65 ? yaw_deviation_q+11'sd65:0;
        yaw_product_q<=yaw_dead_q*16'sd46;
        yaw_dps_q<=yaw_product_q/16'sd100;
        stick_yaw<=yaw_dps_q*32'sd100;
    end
    wire signed [31:0] target_yaw;
    wire yaw_update,yaw_busy;wire [7:0] yaw_fault;
    wire [32:0] manual_outer_elapsed={1'b0,manual_outer_dt_accum}+{1'b0,dt_ticks};
    always @(posedge clk50) begin
        manual_outer_update<=0;
        if(!rst_n || !attitude_valid || !rc_valid) begin
            manual_outer_dt_accum<=0;manual_outer_dt_ticks<=0;
        end else if(attitude_update) begin
            if(manual_outer_elapsed>=300000 && !manual_angle_busy) begin
                manual_outer_dt_ticks<=manual_outer_elapsed>32'hffffffff ? 32'hffffffff:manual_outer_elapsed[31:0];
                manual_outer_dt_accum<=0;manual_outer_update<=1;
            end else manual_outer_dt_accum<=manual_outer_elapsed>32'hffffffff ? 32'hffffffff:manual_outer_elapsed[31:0];
        end
    end
    wire [32:0] yaw_elapsed={1'b0,yaw_dt_accum}+{1'b0,dt_ticks};
    always @(posedge clk50) begin
        yaw_sample_update<=0;
        if(!rst_n || !controller_run) begin yaw_dt_accum<=0;yaw_dt_ticks<=0;end
        else if(attitude_update && attitude_valid) begin
            if(yaw_elapsed>=300000 && !yaw_busy) begin
                yaw_dt_ticks<=yaw_elapsed>32'hffffffff ? 32'hffffffff:yaw_elapsed[31:0];
                yaw_dt_accum<=0;yaw_sample_update<=1;
            end else yaw_dt_accum<=yaw_elapsed>32'hffffffff ? 32'hffffffff:yaw_elapsed[31:0];
        end
    end
    ano_yaw_control yaw_controller(.clk(clk50),.rst_n(rst_n),.sample_update(yaw_sample_update),
        .enabled(controller_run),.yaw_valid(attitude_valid),.dt_ticks(yaw_dt_ticks),.yaw_cdeg(-sensor_yaw),
        .stick_yaw_rate_cdeg_s(stick_yaw),.update(yaw_update),.busy(yaw_busy),
        .target_yaw_rate_cdeg_s(target_yaw),.heading_target_cdeg(),.yaw_error_cdeg(),.slewed_rate_cdeg_s(),.fault(yaw_fault));
    // Source attitude outer-loop cadence is6ms, independent of the2ms
    // rate loop. Hold a coherent feedback/target snapshot between updates.
    reg outer_seeded=0;
    reg signed [15:0] outer_roll=0,outer_pitch=0,outer_target_roll=0,outer_target_pitch=0;
    always @(posedge clk50) begin
        if(!rst_n || !controller_run) begin
            outer_seeded<=0;outer_roll<=0;outer_pitch<=0;outer_target_roll<=0;outer_target_pitch<=0;
        end else if(hold_override && (!outer_seeded || yaw_sample_update)) begin
            outer_roll<=roll;outer_pitch<=pitch;outer_target_roll<=target_roll;outer_target_pitch<=target_pitch;outer_seeded<=1;
        end else if(!hold_override && manual_angle_update) begin
            outer_roll<=manual_snapshot_roll;outer_pitch<=manual_snapshot_pitch;
            outer_target_roll<=manual_roll_cdeg;outer_target_pitch<=-manual_pitch_cdeg;outer_seeded<=1;
        end
    end
    reg signed [15:0] reported_target_roll=0,reported_target_pitch=0;
    always @(posedge clk50) begin reported_target_roll<=target_roll;reported_target_pitch<=target_pitch;end
    reg pose_seen=0;
    reg [31:0] pose_age=32'hFFFFFFFF;
    always @(posedge clk50) begin
        if(!rst_n) begin pose_seen<=0; pose_age<=32'hFFFFFFFF; end
        else if(attitude_update && attitude_valid) begin pose_seen<=1; pose_age<=0; end
        else if(pose_age!=32'hFFFFFFFF) pose_age<=pose_age+1'b1;
    end
    wire controller_update,controller_busy;
    wire signed [15:0] correction_roll,correction_pitch,correction_yaw;
    wire [7:0] rate_controller_fault;
    // Bit5 records a manual target transaction fault. Existing rate fault
    // bits and the immediate public health/output masks retain their meaning.
    wire [7:0] controller_fault=rate_controller_fault | (manual_angle_fault!=0 ? 8'h20 : 8'h00);
    wire armed;
    wire [7:0] inhibit_reason;
    wire gate_event_pulse;
    wire [7:0] gate_event_code,gate_last_interruption_code,gate_last_revoke_code;
    wire [15:0] gate_interruption_count,gate_revoke_count;
    reg [31:0] request_age=0,command_age=32'hFFFFFFFF;
    reg command_seen=0;
    // Register parallel watchdog predicates before combining them with the
    // sensor/gate checks. The public command age check below stays immediate.
    reg throttle_active_q=0,request_expired_q=0,command_expired_q=1;
    always @(posedge clk50) begin
        if(!rst_n) begin throttle_active_q<=0; request_expired_q<=0; command_expired_q<=1; end
        else begin
            throttle_active_q<=taking_off && (altitude_active || height_fallback_active);
            request_expired_q<=request_age>=POSE_TIMEOUT_TICKS;
            command_expired_q<=command_age>=POSE_TIMEOUT_TICKS;
        end
    end
    wire request_active=armed && rc_valid && throttle_active_q;
    wire controller_stale=request_active && request_expired_q && command_expired_q;
    // Test symmetric tilt bounds directly in the sensor's two's-complement
    // bits. The negative half uses unsigned low15>=32768-4500; no body-pitch
    // negation/carry chain participates in this live, unregistered stop gate.
    function tilt_within_limit;
        input [15:0] sensor_angle;
        begin tilt_within_limit=sensor_angle[15] ?
            sensor_angle[14:0]>=15'd28268 : sensor_angle[14:0]<=15'd4500;end
    endfunction
    wire roll_tilt_ok=tilt_within_limit(sensor_roll);
    wire pitch_tilt_ok=tilt_within_limit(sensor_pitch);
    wire sensor_ok=attitude_valid && calibrated && pose_seen && pose_age<POSE_TIMEOUT_TICKS &&
        roll_tilt_ok && pitch_tilt_ok &&
        controller_fault==0 && yaw_fault==0 && !controller_stale;
    // Diagnostics mirror the existing validity terms without changing them.
    // Latch on the same edge that clears gate preparation/arming; a recovered
    // sensor before the next 10 Hz report must not erase the original cause.
    wire [7:0] sensor_failure_mask={controller_stale,(controller_fault!=0 || yaw_fault!=0),
        !pitch_tilt_ok,!roll_tilt_ok,
        (pose_age>=POSE_TIMEOUT_TICKS),!pose_seen,!calibrated,!attitude_valid};
    reg [7:0] gate_last_interruption_sensor_mask=0,gate_last_revoke_sensor_mask=0;
    reg [31:0] gate_last_interruption_pose_age=0,gate_last_revoke_pose_age=0;
    reg [7:0] gate_last_interruption_imu_reason=0,gate_last_revoke_imu_reason=0;
    reg [7:0] gate_last_interruption_attitude_fault=0,gate_last_revoke_attitude_fault=0;
    always @(posedge clk50) begin
        if(!rst_n) begin
            gate_last_interruption_sensor_mask<=0; gate_last_revoke_sensor_mask<=0;
            gate_last_interruption_pose_age<=0; gate_last_revoke_pose_age<=0;
            gate_last_interruption_imu_reason<=0; gate_last_revoke_imu_reason<=0;
            gate_last_interruption_attitude_fault<=0; gate_last_revoke_attitude_fault<=0;
        end else if(gate_event_pulse) begin
            if(gate_event_code[5:4]==2'b11) begin
                gate_last_revoke_sensor_mask<=sensor_failure_mask;
                gate_last_revoke_pose_age<=pose_age;
                gate_last_revoke_imu_reason<=imu_reason;
                gate_last_revoke_attitude_fault<=attitude_fault;
            end else begin
                gate_last_interruption_sensor_mask<=sensor_failure_mask;
                gate_last_interruption_pose_age<=pose_age;
                gate_last_interruption_imu_reason<=imu_reason;
                gate_last_interruption_attitude_fault<=attitude_fault;
            end
        end
    end
    // Migration-stage hardware lock: new mounting and units not yet measured.
    // Keep the actual estimator/telemetry alive; all motor PWM remains1000us.
    wire installation_verified=1'b1; // B089 PROPS-OFF HARDWARE BENCH; not flight accepted.
    control_gate #(.LOW_HOLD_TICKS(ARM_LOW_TICKS),.HIGH_HOLD_TICKS(ARM_HIGH_TICKS)) gate(
        .clk(clk50),.rst_n(rst_n),.rc_valid(rc_valid),.sensor_ok(sensor_ok && installation_verified && (vertical_available || height_fallback_active) && !land_lock),
        .channel_count(channel_count),.ch3(ch3),.ch5(ch5),
        .armed(armed),.inhibit_reason(inhibit_reason),
        .event_pulse(gate_event_pulse),.event_code(gate_event_code),
        .interruption_count(gate_interruption_count),.revoke_count(gate_revoke_count),
        .last_interruption_code(gate_last_interruption_code),.last_revoke_code(gate_last_revoke_code));
    assign armed_usable=installation_verified && armed && rc_valid && sensor_ok && (vertical_available || height_fallback_active) && !land_lock && channel_count>=5 && channel_count<=8 &&
        ch3>=800 && ch3<=2200 && ch5>=1800 && ch5<=2200;
    // Export only the existing gate state to the hold FSM. Live health still
    // masks command/PWM validity below; do not use this raw state for motors.
    assign armed_raw=installation_verified && armed;
    // In altitude modes low stick requests descent. SWA and live health still
    // revoke output; the mode can only be entered through its centered gate.
    assign controller_enabled=RUN_RANGE_OK && armed_usable && taking_off && (altitude_active || height_fallback_active);
    assign control_enabled=controller_enabled;
    // Actual consumed mode follows the latched target selection, but a live
    // stop hides it on the same cycle as physical command validity.
    assign hold_consumed=hold_override && controller_enabled;
    assign altitude_consumed=altitude_override && controller_enabled;
    // A local registered enable limits the control datapath's fanout and depth.
    // Live validity still masks published commands immediately. Cancellation
    // of internal state may take one additional 20 ns clock; re-enabling cannot
    // expose a command left over from before that cancellation.
    always @(posedge clk50) begin
        if(!rst_n) controller_run<=0;
        else controller_run<=controller_enabled;
    end
    wire [2:0] allocation_sat_positive,allocation_sat_negative;
    // Inner loop runs on the first fresh pose whose accumulated source dt
    // reaches2ms. Never integrate repeated held samples; rejected gaps remain
    // part of the next real dt and are bounded by the existing watchdog.
    reg rate_sample_update=0;
    reg [31:0] control_dt_accum=0,control_dt_ticks=0;
    wire [32:0] control_elapsed={1'b0,control_dt_accum}+{1'b0,dt_ticks};
    always @(posedge clk50) begin
        rate_sample_update<=0;
        if(!rst_n || !controller_run) begin control_dt_accum<=0;control_dt_ticks<=0;end
        else if(attitude_update && attitude_valid) begin
            if(control_elapsed>=100000 && !controller_busy) begin
                control_dt_ticks<=control_elapsed>32'hffffffff ? 32'hffffffff:control_elapsed[31:0];
                control_dt_accum<=0;rate_sample_update<=1;
            end else control_dt_accum<=control_elapsed>32'hffffffff ? 32'hffffffff:control_elapsed[31:0];
        end
    end
    ano_rate_control #(.GYRO_FRAC_BITS(12),.MAX_DT_TICKS(POSE_TIMEOUT_TICKS)) controller(
        .clk(clk50),.rst_n(rst_n),.sample_update(rate_sample_update),.enabled(controller_run),.auto_takeoff(auto_takeoff && !height_fallback_active),
        .dt_ticks(control_dt_ticks),.roll_cdeg(outer_roll),.pitch_cdeg(outer_pitch),
        .target_roll_cdeg(outer_target_roll),.target_pitch_cdeg(outer_target_pitch),
        .gx(gx_q12),.gy(gy_q12),.gz(gz_q12),.target_yaw_rate_cdeg_s(target_yaw),
        .saturation_positive(allocation_sat_positive),.saturation_negative(allocation_sat_negative),
        .update(controller_update),.busy(controller_busy),.roll_us(correction_roll),.pitch_us(correction_pitch),.yaw_us(correction_yaw),.fault(rate_controller_fault));
    reg [15:0] pending_throttle=1000;
    wire motor_prepared,taking_off,flying,land_lock;wire [3:0] preparation_mask;
    ano_flight_state #(.TICKS_PER_MS(FLIGHT_STATE_TICKS_PER_MS)) flight_state(.clk(clk50),.rst_n(rst_n),.armed(armed_usable),
     .ch3(ch3),.collective_us(selected_throttle),.motor_prepared(motor_prepared),
     .taking_off(taking_off),.flying(flying),.land_lock(land_lock),.preparation_mask(preparation_mask));
    assign taking_off_out=taking_off;
    assign flight_state_flags={auto_takeoff,flying,motor_prepared,taking_off};
    assign throttle_takeover_active=1'b0;assign throttle_pickup_us=16'd0;
    wire [15:0] fallback_collective;
    height_loss_fallback fallback_control(.clk(clk50),.rst_n(rst_n),
     .healthy(sensor_ok && rc_valid && ch5>=1800 && ch5<=2200 && fallback_norm_valid && !land_lock),
     .armed(armed),.taking_off(taking_off),.height_available(vertical_available),
     .automatic_valid(rate_fresh && altitude_active && !height_fallback_active),
     .automatic_collective_us(pending_throttle),.ch3(ch3),
     .active(height_fallback_active),.prior_collective_valid(),.collective_us(fallback_collective));
    wire [15:0] selected_throttle=height_fallback_active ?fallback_collective:hold_collective_us;
    wire [15:0] mixed_collective=pending_throttle;
    // Latch the exact yaw code before the safety gate clears the controller.
    reg [7:0] last_yaw_fault=0;
    assign sticky_yaw_fault=last_yaw_fault;
    always @(posedge clk50)
     if(!rst_n)last_yaw_fault<=0;
     else if(yaw_fault!=0)last_yaw_fault<=yaw_fault;
    // Separate RC scaling from hold offset/clipping. Both are committed long
    // before the approximately500-clock rate-controller result is available.
    reg [15:0] throttle_base=1000;
    reg signed [15:0] captured_hold_delta=0;
    reg [15:0] captured_hold_collective=1000;
    reg captured_hold=0,captured_active=0,throttle_commit=0;
    wire signed [17:0] adjusted_base=$signed({1'b0,throttle_base})+$signed(captured_hold_delta);
    wire [15:0] mix1,mix2,mix3,mix4;
    wire saturated;
    quad_mixer_feedback #(.MIN_US(RUN_MIN_US),.MAX_US(RUN_MAX_US)) mixer(.enabled(controller_run),.throttle_us(mixed_collective),
        .roll_us(correction_roll),.pitch_us(correction_pitch),.yaw_us(correction_yaw),
        .m1_us(mix1),.m2_us(mix2),.m3_us(mix3),.m4_us(mix4),.saturated(saturated),
        .saturation_positive(allocation_sat_positive),.saturation_negative(allocation_sat_negative));
    reg [15:0] m1=1000,m2=1000,m3=1000,m4=1000;
    reg signed [15:0] committed_roll=0,committed_pitch=0,committed_yaw=0;
    reg mix_saturated=0;
    reg [31:0] command_count=0;
    reg [31:0] controller_fault_count=0;
    reg [7:0] last_controller_fault=0,previous_controller_fault=0;
    always @(posedge clk50) begin
        if(!rst_n) begin
            controller_fault_count<=0; last_controller_fault<=0; previous_controller_fault<=0;
        end else begin
            previous_controller_fault<=controller_fault;
            if(controller_fault!=0) last_controller_fault<=controller_fault;
            if(controller_fault!=0 && previous_controller_fault==0)
                controller_fault_count<=controller_fault_count+1'b1;
        end
    end
    reg [15:0] latency_counter=0,last_latency=0;
    reg measuring=0;
    always @(posedge clk50) begin
        throttle_commit<=0;
        if(!rst_n || !controller_run) begin
            request_age<=0; command_age<=32'hFFFFFFFF; command_seen<=0;
            m1<=1000; m2<=1000; m3<=1000; m4<=1000; mix_saturated<=0;
            committed_roll<=0; committed_pitch<=0; committed_yaw<=0;
            pending_throttle<=1000; measuring<=0; latency_counter<=0;
            throttle_base<=1000;captured_hold<=0;captured_hold_delta<=0;captured_active<=0;
            if(!rst_n) begin command_count<=0; last_latency<=0; end
        end else begin
            if(request_age!=32'hFFFFFFFF) request_age<=request_age+1'b1;
            if(command_age!=32'hFFFFFFFF) command_age<=command_age+1'b1;
            if(rate_sample_update && !controller_busy) begin
                throttle_base<=selected_throttle;captured_hold<=altitude_override;
                captured_hold_delta<=hold_throttle_delta_us;captured_hold_collective<=hold_collective_us;captured_active<=RUN_RANGE_OK && taking_off && (altitude_active || height_fallback_active);
                throttle_commit<=1;
                latency_counter<=0; measuring<=1;
            end else if(measuring && latency_counter!=16'hFFFF) latency_counter<=latency_counter+1'b1;
            if(throttle_commit) begin
                if(!captured_active) pending_throttle<=1000;
                else pending_throttle<=throttle_base;
            end
            if(controller_update) begin
                // All four command numbers are committed on the same clock.
                m1<=mix1; m2<=mix2; m3<=mix3; m4<=mix4; mix_saturated<=saturated;
                committed_roll<=correction_roll; committed_pitch<=correction_pitch; committed_yaw<=correction_yaw;
                command_count<=command_count+1'b1; command_age<=0; command_seen<=1;
                last_latency<=latency_counter+1'b1; measuring<=0;
            end
        end
    end
    wire rate_fresh=controller_enabled && controller_run && command_seen && command_age<POSE_TIMEOUT_TICKS;
    wire idle_running=armed_usable && (!taking_off || !motor_prepared);
    assign command_fresh=rate_fresh || idle_running;
    wire [15:0] published_m1=rate_fresh ?m1:idle_running && preparation_mask[0] ?RUN_MIN_US:16'd1000;
    wire [15:0] published_m2=rate_fresh ?m2:idle_running && preparation_mask[1] ?RUN_MIN_US:16'd1000;
    wire [15:0] published_m3=rate_fresh ?m3:idle_running && preparation_mask[2] ?RUN_MIN_US:16'd1000;
    wire [15:0] published_m4=rate_fresh ?m4:idle_running && preparation_mask[3] ?RUN_MIN_US:16'd1000;
    wire [15:0] effective1_us,effective2_us,effective3_us,effective4_us;
    wire [15:0] frame_latched1_us,frame_latched2_us,frame_latched3_us,frame_latched4_us;
    wire pwm_frame_active,pwm_limited;
    // f(select(c,a,b))=select(c,f(a),f(b)); keep the same published data,
    // frame latch and live enable. Only move the us-to-ticks conversion
    // ahead of validity selection, removing the long health->DSP path.
    function [31:0] pwm_width_ticks;
        input [15:0] value;
        reg [15:0] bounded;
        begin
            bounded=value<1000 ?16'd1000:value>RUN_MAX_US ?RUN_MAX_US:value;
            pwm_width_ticks=bounded*32'd50;
        end
    endfunction
    wire [31:0] pwm_ticks1=rate_fresh ?pwm_width_ticks(m1):idle_running && preparation_mask[0] ?pwm_width_ticks(RUN_MIN_US):pwm_width_ticks(16'd1000);
    wire [31:0] pwm_ticks2=rate_fresh ?pwm_width_ticks(m2):idle_running && preparation_mask[1] ?pwm_width_ticks(RUN_MIN_US):pwm_width_ticks(16'd1000);
    wire [31:0] pwm_ticks3=rate_fresh ?pwm_width_ticks(m3):idle_running && preparation_mask[2] ?pwm_width_ticks(RUN_MIN_US):pwm_width_ticks(16'd1000);
    wire [31:0] pwm_ticks4=rate_fresh ?pwm_width_ticks(m4):idle_running && preparation_mask[3] ?pwm_width_ticks(RUN_MIN_US):pwm_width_ticks(16'd1000);

    motor_pwm #(.TICKS_PER_US(50),.FRAME_US(OUTPUT_FRAME_US),.MAX_US(RUN_MAX_US),.EXTERNAL_TICKS(1)) outputs(.clk(clk50),.rst_n(rst_n),.enabled(command_fresh),
        // The enabled input already masks pulses/effective telemetry immediately.
        // Feed committed numbers directly so health logic is not duplicated
        // through the width clamp and us-to-clock arithmetic.
        .m1_us(published_m1),.m2_us(published_m2),.m3_us(published_m3),.m4_us(published_m4),
        .pre_ticks1(pwm_ticks1),.pre_ticks2(pwm_ticks2),.pre_ticks3(pwm_ticks3),.pre_ticks4(pwm_ticks4),
        .motor1_pwm(motor1_pwm),.motor2_pwm(motor2_pwm),.motor3_pwm(motor3_pwm),.motor4_pwm(motor4_pwm),
        .effective1_us(effective1_us),.effective2_us(effective2_us),
        .effective3_us(effective3_us),.effective4_us(effective4_us),
        .frame_latched1_us(frame_latched1_us),.frame_latched2_us(frame_latched2_us),
        .frame_latched3_us(frame_latched3_us),.frame_latched4_us(frame_latched4_us),
        .frame_active(pwm_frame_active),.limited(pwm_limited));
    wire [7:0] physical_flags={5'd0,pwm_limited,pwm_frame_active,command_fresh};
    assign led3=sensor_ok;

    // The exact108byte body of original A577 [871:8], no UART state/sequence/checksum.
    // Joint top owns packet framing. Fields and live/committed semantics unchanged.
    wire [7:0] flags={(mix_saturated && command_fresh),command_fresh,controller_enabled,armed_usable,
        sensor_ok,attitude_valid,calibrated,rc_valid};
    assign telemetry_body={flags,inhibit_reason,imu_reason,last_controller_fault,
        ch1,ch2,ch3,ch4,ch5,roll,pitch,reported_target_roll,reported_target_pitch,target_yaw,
        {{15{gx[16]}},gx},{{15{gy[16]}},gy},{{15{gz[16]}},gz},
        (RAW_TELEMETRY_COMMANDS ? committed_roll : (command_fresh ? committed_roll : 16'sd0)),(RAW_TELEMETRY_COMMANDS ? committed_pitch : (command_fresh ? committed_pitch : 16'sd0)),
        (RAW_TELEMETRY_COMMANDS ? committed_yaw : (command_fresh ? committed_yaw : 16'sd0)),published_m1,published_m2,published_m3,published_m4,
        accepted_count,rejected_count,command_count,controller_fault_count,pose_age,last_latency,cal_count,
        who,pwr,attitude_fault,
        gate_interruption_count,gate_revoke_count,gate_last_interruption_code,gate_last_revoke_code,
        gate_last_interruption_sensor_mask,gate_last_interruption_pose_age,
        gate_last_interruption_imu_reason,gate_last_interruption_attitude_fault,
        gate_last_revoke_sensor_mask,gate_last_revoke_pose_age,
        gate_last_revoke_imu_reason,gate_last_revoke_attitude_fault,(RAW_TELEMETRY_COMMANDS ? frame_latched1_us : effective1_us),(RAW_TELEMETRY_COMMANDS ? frame_latched2_us : effective2_us),(RAW_TELEMETRY_COMMANDS ? frame_latched3_us : effective3_us),(RAW_TELEMETRY_COMMANDS ? frame_latched4_us : effective4_us),physical_flags};
    assign pose_update=attitude_update;
    assign pose_valid=attitude_valid;
    assign pose_dt_ticks=dt_ticks;
    assign pose_age_ticks=pose_age;
    assign body_roll_cdeg=roll;
    assign body_pitch_cdeg=pitch;
    assign body_yaw_cdeg=-sensor_yaw;
    assign base_throttle_us=altitude_active ?hold_collective_us:16'd1000;
    assign world_ax_mmps2=sensor_world_ax;
    assign world_ay_mmps2=-sensor_world_ay;
    assign world_az_up_mmps2=sensor_world_az;
    // Display-only latest accepted sensor-frame acceleration, including gravity.
    // It may be newer than the published world-acceleration pose sample.
    assign raw_ax_counts=accepted_raw[95:80];
    assign raw_ay_counts=accepted_raw[79:64];
    assign raw_az_counts=accepted_raw[63:48];
    assign raw_accel_valid=accepted_count!=0;
    assign body_gx=gx;assign body_gy=gy;assign body_gz=gz;
    assign body_gx_q12=gx_q12;assign body_gy_q12=gy_q12;assign body_gz_q12=gz_q12;
endmodule
