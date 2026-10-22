`include "core/rtl/initial_profile.vh"
// No-prop PX4-inspired motor bench. Physical outputs: 50 Hz, 1000..1150 us.
// PID gains are unvalidated initial values; this is not a flight image.
// Active allocator bounds RUN_MIN_US..1150; idle/fault PWM remains1000us.
// Initial RUN_MIN_US1110 adds10us to one observed1100us run; true minimum remains unmeasured.
// Mounted-airframe directions measured 2026-10-11; see airframe_mapping_20261011.json.
// Flight gains, rotor directions and physical closed-loop behavior remain unverified.
module flight_core #(
    parameter integer RUN_MAX_US=1150, // Full-range offline profile may use2000; never auto-enable on hardware.
    parameter integer RUN_MIN_US=1110, // Initial no-prop candidate, not flight idle confirmation
    parameter integer CAL_SAMPLES=256,
    parameter integer ARM_LOW_TICKS=25000000,
    parameter integer ARM_HIGH_TICKS=25000000,
    parameter integer POSE_TIMEOUT_TICKS=3000000 // 60 ms at 50 MHz; bench experiment
)(
    input wire clk50,imu_miso,rc_ppm_in,
    input wire hold_active,
    input wire signed [15:0] hold_roll_cdeg,hold_pitch_cdeg,hold_throttle_delta_us,
    output wire imu_sck,imu_mosi,imu_cs_n,
    output reg led2=0,
    output wire led3,
    output wire motor1_pwm,motor2_pwm,motor3_pwm,motor4_pwm,
    output wire rc_valid,
    output wire [3:0] channel_count,
    output wire [15:0] ch1,ch2,ch3,ch4,ch5,ch6,ch7,ch8,
    output wire pose_update,pose_valid,
    output wire [31:0] pose_dt_ticks,pose_age_ticks,
    output wire signed [15:0] body_roll_cdeg,body_pitch_cdeg,
    output wire signed [16:0] body_gx,body_gy,body_gz,
    output wire armed_usable,control_enabled,command_fresh,
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
    wire signed [15:0] sensor_roll,sensor_pitch,bias_x,bias_y,bias_z;
    imu_pipeline #(.CAL_SAMPLES(CAL_SAMPLES),.DATA_TIMEOUT_TICKS(POSE_TIMEOUT_TICKS)) imu(
        .clk50(clk50),.rst_n(rst_n),.imu_miso(imu_miso),
        .imu_sck(imu_sck),.imu_mosi(imu_mosi),.imu_cs_n(imu_cs_n),
        .calibrated(calibrated),.attitude_valid(attitude_valid),
        .attitude_update(attitude_update),.link_usable(link_usable),
        .accepted_raw(accepted_raw),.dt_ticks(dt_ticks),
        .accepted_count(accepted_count),.rejected_count(rejected_count),
        .reason(imu_reason),.who(who),.pwr(pwr),.attitude_fault(attitude_fault),
        .cal_count(cal_count),.roll(sensor_roll),.pitch(sensor_pitch),
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
    wire signed [16:0] gx={raw_gx[15],raw_gx}-{bias_x[15],bias_x};
    // bias-raw equals -(raw-bias), without a second adder or 16-bit negation.
    // Full corrected range is -65535..65535, retained in signed17.
    wire signed [16:0] gy={bias_y[15],bias_y}-{raw_gy[15],raw_gy};
    wire signed [16:0] gz={bias_z[15],bias_z}-{raw_gz[15],raw_gz};
    wire [15:0] rc_sequence;
    wire rc_update;
    rc_ppm receiver(.clk(clk50),.rst_n(rst_n),.ppm_in(rc_ppm_in),
        .frame_update(rc_update),.valid(rc_valid),.channel_count(channel_count),
        .ch1(ch1),.ch2(ch2),.ch3(ch3),.ch4(ch4),.ch5(ch5),.ch6(ch6),.ch7(ch7),.ch8(ch8),
        .frame_sequence(rc_sequence));

    // Targets and feedback use the same BODY frame. Stick polarity, rotor
    // directions and gains still require physical verification before flight.
    function signed [15:0] angle_target;
        input [15:0] channel;
        reg signed [31:0] deviation,scaled;
        begin
            deviation=$signed({1'b0,channel})-32'sd1500;
            if(deviation>500) deviation=500;
            if(deviation< -500) deviation=-500;
            if(deviation>= -10 && deviation<=10) deviation=0;
            scaled=deviation*4;
            angle_target=scaled[15:0]; // +/-20 degrees at 1000..2000 us
        end
    endfunction
    function signed [31:0] yaw_target;
        input [15:0] channel;
        reg signed [31:0] deviation;
        begin
            deviation=$signed({1'b0,channel})-32'sd1500;
            if(deviation>500) deviation=500;
            if(deviation< -500) deviation=-500;
            if(deviation>= -10 && deviation<=10) deviation=0;
            yaw_target=deviation*20; // +/-100 deg/s, not absolute heading
        end
    endfunction
    localparam RUN_RANGE_OK=RUN_MIN_US>=1000 && RUN_MIN_US<RUN_MAX_US && RUN_MAX_US<=2000;
    // Invalid configuration fails closed in synthesis and is rejected in simulation.
    generate if(!RUN_RANGE_OK) begin : invalid_run_min
        initial $fatal(1,"require 1000 <= RUN_MIN_US < RUN_MAX_US <= 2000");
    end endgenerate
    function [15:0] throttle_target;
        input [15:0] channel;
        reg [9:0] deviation;
        reg [19:0] numerator;
        begin
            if(!RUN_RANGE_OK || channel<=1100) throttle_target=1000;
            else if(channel>=2000) throttle_target=RUN_MAX_US;
            else begin
                // Active RC range1100..2000 maps to RUN_MIN_US..1150.
                // Difference1..899 and span1..1000 fit the unsigned20 product.
                deviation=channel-16'd1100;
                numerator={10'd0,deviation}*(RUN_MAX_US-RUN_MIN_US);
                throttle_target=RUN_MIN_US+numerator/20'd900;
            end
        end
    endfunction
    function signed [15:0] bounded_hold_angle;
        input signed [15:0] angle;
        begin bounded_hold_angle=angle>16'sd1000 ? 16'sd1000 :
            angle< -16'sd1000 ? -16'sd1000 : angle;end
    endfunction
    // Register mode selection before target muxes. Public motor validity is
    // still masked by live RC/sensor predicates, independently of this.
    reg hold_override=0;
    always @(posedge clk50) if(!rst_n) hold_override<=0;else hold_override<=hold_active && control_enabled;
    wire signed [15:0] target_roll=hold_override ? bounded_hold_angle(hold_roll_cdeg) : angle_target(ch1);
    // Measured radio: CH2 increases when pushing forward (nose down).
    // Body pitch is nose-up positive; angle_target is bounded to +/-2000.
    wire signed [15:0] target_pitch=hold_override ? bounded_hold_angle(hold_pitch_cdeg) : -angle_target(ch2);
    wire signed [31:0] target_yaw=yaw_target(ch4);
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
    wire [7:0] controller_fault;
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
            throttle_active_q<=ch3>1100;
            request_expired_q<=request_age>=POSE_TIMEOUT_TICKS;
            command_expired_q<=command_age>=POSE_TIMEOUT_TICKS;
        end
    end
    wire request_active=armed && rc_valid && throttle_active_q;
    wire controller_stale=request_active && request_expired_q && command_expired_q;
    wire sensor_ok=attitude_valid && calibrated && pose_seen && pose_age<POSE_TIMEOUT_TICKS &&
        roll>= -4500 && roll<=4500 && sensor_pitch>= -4500 && sensor_pitch<=4500 &&
        controller_fault==0 && !controller_stale;
    // Diagnostics mirror the existing validity terms without changing them.
    // Latch on the same edge that clears gate preparation/arming; a recovered
    // sensor before the next 10 Hz report must not erase the original cause.
    wire [7:0] sensor_failure_mask={controller_stale,(controller_fault!=0),
        (sensor_pitch< -4500 || sensor_pitch>4500),(roll< -4500 || roll>4500),
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
    control_gate #(.LOW_HOLD_TICKS(ARM_LOW_TICKS),.HIGH_HOLD_TICKS(ARM_HIGH_TICKS)) gate(
        .clk(clk50),.rst_n(rst_n),.rc_valid(rc_valid),.sensor_ok(sensor_ok),
        .channel_count(channel_count),.ch3(ch3),.ch5(ch5),
        .armed(armed),.inhibit_reason(inhibit_reason),
        .event_pulse(gate_event_pulse),.event_code(gate_event_code),
        .interruption_count(gate_interruption_count),.revoke_count(gate_revoke_count),
        .last_interruption_code(gate_last_interruption_code),.last_revoke_code(gate_last_revoke_code));
    assign armed_usable=armed && rc_valid && sensor_ok && channel_count>=5 && channel_count<=8 &&
        ch3>=800 && ch3<=2200 && ch5>=1800 && ch5<=2200;
    wire controller_enabled=RUN_RANGE_OK && armed_usable && ch3>1100;
    assign control_enabled=controller_enabled;
    // A local registered enable limits the control datapath's fanout and depth.
    // Live validity still masks published commands immediately. Cancellation
    // of internal state may take one additional 20 ns clock; re-enabling cannot
    // expose a command left over from before that cancellation.
    reg controller_run=0;
    always @(posedge clk50) begin
        if(!rst_n) controller_run<=0;
        else controller_run<=controller_enabled;
    end
    wire [2:0] allocation_sat_positive,allocation_sat_negative;
    rate_control_px4 #(
        .MAX_DT_TICKS(POSE_TIMEOUT_TICKS),
        .ROLL_P_Q16(`INITIAL_ROLL_P_Q16),
        .ROLL_I_Q16(`INITIAL_ROLL_I_Q16),
        .ROLL_D_Q16(`INITIAL_ROLL_D_Q16),
        .ROLL_FF_Q16(`INITIAL_ROLL_FF_Q16),
        .PITCH_P_Q16(`INITIAL_PITCH_P_Q16),
        .PITCH_I_Q16(`INITIAL_PITCH_I_Q16),
        .PITCH_D_Q16(`INITIAL_PITCH_D_Q16),
        .PITCH_FF_Q16(`INITIAL_PITCH_FF_Q16),
        .YAW_P_Q16(`INITIAL_YAW_P_Q16),
        .YAW_I_Q16(`INITIAL_YAW_I_Q16),
        .YAW_D_Q16(`INITIAL_YAW_D_Q16),
        .YAW_FF_Q16(`INITIAL_YAW_FF_Q16),
        .ANGLE_ROLL_P_Q16(`INITIAL_ANGLE_ROLL_P_Q16),
        .ANGLE_PITCH_P_Q16(`INITIAL_ANGLE_PITCH_P_Q16),
        .MAX_CORRECTION_US(80),
        .MAX_INTEGRAL_US(40),
        .D_FILTER_TAU_TICKS(795775)) controller(.clk(clk50),.rst_n(rst_n),
        .sample_update(attitude_update && attitude_valid),.enabled(controller_run),
        .dt_ticks(dt_ticks),.roll_cdeg(roll),.pitch_cdeg(pitch),
        .target_roll_cdeg(target_roll),.target_pitch_cdeg(target_pitch),
        .gx(gx),.gy(gy),.gz(gz),.target_yaw_rate_cdeg_s(target_yaw),
        .saturation_positive(allocation_sat_positive),.saturation_negative(allocation_sat_negative),
        .update(controller_update),.busy(controller_busy),
        .roll_us(correction_roll),.pitch_us(correction_pitch),.yaw_us(correction_yaw),
        .fault(controller_fault));
    function [15:0] control_throttle_target;
        input [15:0] channel;
        input use_hold;
        input signed [15:0] delta;
        reg signed [17:0] sum;
        begin
            if(!RUN_RANGE_OK || channel<=1100) control_throttle_target=1000;
            else if(!use_hold) control_throttle_target=throttle_target(channel);
            else begin
                sum=$signed({1'b0,throttle_target(channel)})+$signed(delta);
                if(sum<RUN_MIN_US) control_throttle_target=RUN_MIN_US;
                else if(sum>RUN_MAX_US) control_throttle_target=RUN_MAX_US;
                else control_throttle_target=sum[15:0];
            end
        end
    endfunction
    reg [15:0] pending_throttle=1000;
    // RC subtraction, multiply, and divide occupy separate clocks. Live low
    // throttle still cancels outputs immediately; this value is arithmetic only.
    reg [9:0] throttle_deviation=0;
    reg [19:0] throttle_numerator=0;
    reg throttle_idle_q=1,throttle_idle_qq=1;
    reg [15:0] mapped_throttle=1000;
    always @(posedge clk50) begin
        throttle_deviation<=ch3<=1100 ? 0 : ch3>=2000 ? 900 : ch3-16'd1100;
        throttle_idle_q<=!RUN_RANGE_OK || ch3<=1100;
        throttle_numerator<={10'd0,throttle_deviation}*(RUN_MAX_US-RUN_MIN_US);
        throttle_idle_qq<=throttle_idle_q;
        mapped_throttle<=throttle_idle_qq ? 16'd1000 : RUN_MIN_US+throttle_numerator/20'd900;
    end
    // Separate RC scaling from hold offset/clipping. Both are committed long
    // before the approximately500-clock rate-controller result is available.
    reg [15:0] throttle_base=1000;
    reg signed [15:0] captured_hold_delta=0;
    reg captured_hold=0,captured_active=0,throttle_commit=0;
    wire signed [17:0] adjusted_base=$signed({1'b0,throttle_base})+$signed(captured_hold_delta);
    wire [15:0] mix1,mix2,mix3,mix4;
    wire saturated;
    quad_mixer_feedback #(.MIN_US(RUN_MIN_US),.MAX_US(RUN_MAX_US)) mixer(.enabled(controller_run),.throttle_us(pending_throttle),
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
            if(attitude_update && attitude_valid && !controller_busy) begin
                throttle_base<=mapped_throttle;captured_hold<=hold_override;
                captured_hold_delta<=hold_throttle_delta_us;captured_active<=RUN_RANGE_OK && ch3>1100;
                throttle_commit<=1;
                latency_counter<=0; measuring<=1;
            end else if(measuring && latency_counter!=16'hFFFF) latency_counter<=latency_counter+1'b1;
            if(throttle_commit) begin
                if(!captured_active) pending_throttle<=1000;
                else if(!captured_hold) pending_throttle<=throttle_base;
                else if(adjusted_base<RUN_MIN_US) pending_throttle<=RUN_MIN_US;
                else if(adjusted_base>RUN_MAX_US) pending_throttle<=RUN_MAX_US;
                else pending_throttle<=adjusted_base[15:0];
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
    assign command_fresh=controller_enabled && controller_run && command_seen && command_age<POSE_TIMEOUT_TICKS;
    wire [15:0] published_m1=command_fresh ? m1 : 16'd1000;
    wire [15:0] published_m2=command_fresh ? m2 : 16'd1000;
    wire [15:0] published_m3=command_fresh ? m3 : 16'd1000;
    wire [15:0] published_m4=command_fresh ? m4 : 16'd1000;
    wire [15:0] effective1_us,effective2_us,effective3_us,effective4_us;
    wire pwm_frame_active,pwm_limited;
    motor_pwm #(.TICKS_PER_US(50),.FRAME_US(20000),.MAX_US(RUN_MAX_US)) outputs(.clk(clk50),.rst_n(rst_n),.enabled(command_fresh),
        // The enabled input already masks pulses/effective telemetry immediately.
        // Feed committed numbers directly so health logic is not duplicated
        // through the width clamp and us-to-clock arithmetic.
        .m1_us(m1),.m2_us(m2),.m3_us(m3),.m4_us(m4),
        .motor1_pwm(motor1_pwm),.motor2_pwm(motor2_pwm),.motor3_pwm(motor3_pwm),.motor4_pwm(motor4_pwm),
        .effective1_us(effective1_us),.effective2_us(effective2_us),
        .effective3_us(effective3_us),.effective4_us(effective4_us),
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
        (command_fresh ? committed_roll : 16'sd0),(command_fresh ? committed_pitch : 16'sd0),
        (command_fresh ? committed_yaw : 16'sd0),published_m1,published_m2,published_m3,published_m4,
        accepted_count,rejected_count,command_count,controller_fault_count,pose_age,last_latency,cal_count,
        who,pwr,attitude_fault,
        gate_interruption_count,gate_revoke_count,gate_last_interruption_code,gate_last_revoke_code,
        gate_last_interruption_sensor_mask,gate_last_interruption_pose_age,
        gate_last_interruption_imu_reason,gate_last_interruption_attitude_fault,
        gate_last_revoke_sensor_mask,gate_last_revoke_pose_age,
        gate_last_revoke_imu_reason,gate_last_revoke_attitude_fault,effective1_us,effective2_us,effective3_us,effective4_us,physical_flags};
    assign pose_update=attitude_update;
    assign pose_valid=attitude_valid;
    assign pose_dt_ticks=dt_ticks;
    assign pose_age_ticks=pose_age;
    assign body_roll_cdeg=roll;
    assign body_pitch_cdeg=pitch;
    assign body_gx=gx;assign body_gy=gy;assign body_gz=gz;
endmodule
