// Development bench: four motor commands exist ONLY as numbers in UART.
// No motor/ESC pins, PWM peripheral or power-enable signal in this top.
// Mounted-airframe directions measured 2026-10-11; see airframe_mapping_20261011.json.
// Flight gains, rotor directions and physical closed-loop behavior remain unverified.
module acg720_control_bench #(
    parameter integer CAL_SAMPLES=256,
    parameter integer ARM_LOW_TICKS=25000000,
    parameter integer ARM_HIGH_TICKS=25000000,
    parameter integer REPORT_TICKS=5000000,
    parameter integer POSE_TIMEOUT_TICKS=3000000 // 60 ms at 50 MHz; bench experiment
)(
    input wire clk50,imu_miso,rc_ppm_in,
    output wire imu_sck,imu_mosi,imu_cs_n,uart_tx,
    output reg led2=0,
    output wire led3
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
    wire [15:0] ch1,ch2,ch3,ch4,ch5,rc_sequence;
    wire [3:0] channel_count;
    wire rc_valid,rc_update;
    rc_ppm receiver(.clk(clk50),.rst_n(rst_n),.ppm_in(rc_ppm_in),
        .frame_update(rc_update),.valid(rc_valid),.channel_count(channel_count),
        .ch1(ch1),.ch2(ch2),.ch3(ch3),.ch4(ch4),.ch5(ch5),
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
    function [15:0] throttle_target;
        input [15:0] channel;
        reg [9:0] deviation;
        reg [7:0] scaled;
        begin
            if(channel<=1000) throttle_target=1000;
            else if(channel>=2000) throttle_target=1200;
            else begin
                // This branch permits only 1..999, so a 10-bit divide suffices.
                deviation=channel-16'd1000;
                scaled=deviation/10'd5;
                throttle_target=16'd1000+{8'd0,scaled};
            end
        end
    endfunction
    wire signed [15:0] target_roll=angle_target(ch1);
    // Measured radio: CH2 increases when pushing forward (nose down).
    // Body pitch is nose-up positive; angle_target is bounded to +/-2000.
    wire signed [15:0] target_pitch=-angle_target(ch2);
    wire signed [31:0] target_yaw=yaw_target(ch4);
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
    wire armed_usable=armed && rc_valid && sensor_ok && channel_count>=5 && channel_count<=8 &&
        ch3>=800 && ch3<=2200 && ch5>=1800 && ch5<=2200;
    wire controller_enabled=armed_usable && ch3>1100;
    // A local registered enable limits the control datapath's fanout and depth.
    // Live validity still masks published commands immediately. Cancellation
    // of internal state may take one additional 20 ns clock; re-enabling cannot
    // expose a command left over from before that cancellation.
    reg controller_run=0;
    always @(posedge clk50) begin
        if(!rst_n) controller_run<=0;
        else controller_run<=controller_enabled;
    end
    rate_control #(.MAX_DT_TICKS(POSE_TIMEOUT_TICKS)) controller(.clk(clk50),.rst_n(rst_n),
        .sample_update(attitude_update && attitude_valid),.enabled(controller_run),
        .dt_ticks(dt_ticks),.roll_cdeg(roll),.pitch_cdeg(pitch),
        .target_roll_cdeg(target_roll),.target_pitch_cdeg(target_pitch),
        .gx(gx),.gy(gy),.gz(gz),.target_yaw_rate_cdeg_s(target_yaw),
        .update(controller_update),.busy(controller_busy),
        .roll_us(correction_roll),.pitch_us(correction_pitch),.yaw_us(correction_yaw),
        .fault(controller_fault));
    reg [15:0] pending_throttle=1000;
    wire [15:0] mix1,mix2,mix3,mix4;
    wire saturated;
    quad_mixer mixer(.enabled(controller_run),.throttle_us(pending_throttle),
        .roll_us(correction_roll),.pitch_us(correction_pitch),.yaw_us(correction_yaw),
        .m1_us(mix1),.m2_us(mix2),.m3_us(mix3),.m4_us(mix4),.saturated(saturated));
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
        if(!rst_n || !controller_run) begin
            request_age<=0; command_age<=32'hFFFFFFFF; command_seen<=0;
            m1<=1000; m2<=1000; m3<=1000; m4<=1000; mix_saturated<=0;
            committed_roll<=0; committed_pitch<=0; committed_yaw<=0;
            pending_throttle<=1000; measuring<=0; latency_counter<=0;
            if(!rst_n) begin command_count<=0; last_latency<=0; end
        end else begin
            if(request_age!=32'hFFFFFFFF) request_age<=request_age+1'b1;
            if(command_age!=32'hFFFFFFFF) command_age<=command_age+1'b1;
            if(attitude_update && attitude_valid && !controller_busy) begin
                pending_throttle<=throttle_target(ch3);
                latency_counter<=0; measuring<=1;
            end else if(measuring && latency_counter!=16'hFFFF) latency_counter<=latency_counter+1'b1;
            if(controller_update) begin
                // All four command numbers are committed on the same clock.
                m1<=mix1; m2<=mix2; m3<=mix3; m4<=mix4; mix_saturated<=saturated;
                committed_roll<=correction_roll; committed_pitch<=correction_pitch; committed_yaw<=correction_yaw;
                command_count<=command_count+1'b1; command_age<=0; command_seen<=1;
                last_latency<=latency_counter+1'b1; measuring<=0;
            end
        end
    end
    wire command_fresh=controller_enabled && controller_run && command_seen && command_age<POSE_TIMEOUT_TICKS;
    wire [15:0] published_m1=command_fresh ? m1 : 16'd1000;
    wire [15:0] published_m2=command_fresh ? m2 : 16'd1000;
    wire [15:0] published_m3=command_fresh ? m3 : 16'd1000;
    wire [15:0] published_m4=command_fresh ? m4 : 16'd1000;
    assign led3=sensor_ok;

    // 104 bytes, 10 Hz. A5 72 retains BODY-frame values and appends separate
    // gate preparation/revoke records. A5 71 had no retained gate causes;
    // A5 70 used sensor-frame values. Old versions must not be mixed in.
    // All integers big-endian; final XOR.
    // The corrections and all motor commands refer to the same committed batch.
    // RC/attitude/targets are live snapshot values; byte7 is retained last fault.
    // Offsets are documented and checked by monitor_control.py.
    reg [31:0] report_div=0;
    reg [15:0] report_sequence=0;
    reg [831:0] packet=0;
    reg [6:0] send_index=0;
    reg [2:0] send_state=0;
    reg tx_start=0;
    wire tx_busy;
    wire [7:0] flags={(mix_saturated && command_fresh),command_fresh,controller_enabled,armed_usable,
        sensor_ok,attitude_valid,calibrated,rc_valid};
    wire [831:0] new_packet={16'hA572,report_sequence,flags,inhibit_reason,imu_reason,last_controller_fault,
        ch1,ch2,ch3,ch4,ch5,roll,pitch,target_roll,target_pitch,target_yaw,
        {{15{gx[16]}},gx},{{15{gy[16]}},gy},{{15{gz[16]}},gz},
        (command_fresh ? committed_roll : 16'sd0),(command_fresh ? committed_pitch : 16'sd0),
        (command_fresh ? committed_yaw : 16'sd0),published_m1,published_m2,published_m3,published_m4,
        accepted_count,rejected_count,command_count,controller_fault_count,pose_age,last_latency,cal_count,
        who,pwr,attitude_fault,
        gate_interruption_count,gate_revoke_count,gate_last_interruption_code,gate_last_revoke_code,
        gate_last_interruption_sensor_mask,gate_last_interruption_pose_age,
        gate_last_interruption_imu_reason,gate_last_interruption_attitude_fault,
        gate_last_revoke_sensor_mask,gate_last_revoke_pose_age,
        gate_last_revoke_imu_reason,gate_last_revoke_attitude_fault,8'h00};
    function [7:0] checksum;
        input [831:0] bytes;
        integer i;
        begin
            checksum=0;
            for(i=8;i<816;i=i+8) checksum=checksum^bytes[i+:8];
        end
    endfunction
    uart_tx_115200 uart(.clk(clk50),.start(tx_start),.data(packet[831:824]),
        .tx(uart_tx),.busy(tx_busy));
    always @(posedge clk50) begin
        tx_start<=0;
        if(!rst_n) begin
            report_div<=0; report_sequence<=0; packet<=0; send_index<=0; send_state<=0;
        end else begin
            if(report_div==REPORT_TICKS-1) report_div<=0;
            else report_div<=report_div+1'b1;
            case(send_state)
                0: if(report_div==REPORT_TICKS-1) begin
                    // Capture one coherent batch before the checksum tree.
                    packet<=new_packet;
                    report_sequence<=report_sequence+1'b1; send_index<=0; send_state<=4;
                end
                4: begin packet[7:0]<=checksum(packet); send_state<=1; end
                1: if(!tx_busy) begin tx_start<=1; send_state<=2; end
                2: if(tx_busy) send_state<=3;
                3: if(!tx_busy) begin
                    if(send_index==103) send_state<=0;
                    else begin packet<={packet[823:0],8'b0}; send_index<=send_index+1'b1; send_state<=1; end
                end
            endcase
        end
    end
endmodule
