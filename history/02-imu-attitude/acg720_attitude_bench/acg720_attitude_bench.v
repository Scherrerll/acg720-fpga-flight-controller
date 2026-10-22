// ONLY clock, IMU SPI, UART and two LEDs. No motor pins in this top level.
module acg720_attitude_bench #(
    parameter integer CAL_SAMPLES=256
) (
    input wire clk50, imu_miso,
    output wire imu_sck, imu_mosi, imu_cs_n, uart_tx,
    output reg led2=0,
    output wire led3
);
    reg [7:0] boot=0;
    always @(posedge clk50) if (boot != 8'hFF) boot <= boot+1'b1;
    wire rst_n=boot==8'hFF;
    reg [24:0] heartbeat=0;
    always @(posedge clk50) begin
        if (heartbeat == 24999999) begin heartbeat <= 0; led2 <= ~led2; end
        else heartbeat <= heartbeat+1'b1;
    end
    wire record_ready;
    wire [95:0] record_raw;
    wire [7:0] who,pwr,gyro_cfg,accel_cfg,filter_cfg,int_status;
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
    wire [7:0] temporal_detail,quiet_count;
    wire [7:0] extra_reason=base_extra | ((|temporal_detail) ? 8'h80 : 8'h00);
    wire sample_valid,link_usable;
    wire [95:0] accepted_raw;
    wire [31:0] dt_ticks,accepted_count,rejected_count;
    wire [7:0] reason;
    wire calibrated,attitude_valid,attitude_update,accel_correction;
    wire signed [15:0] roll,pitch,bias_x,bias_y,bias_z;
    imu_temporal_check temporal(.clk(clk50),.rst_n(rst_n),.record_ready(record_ready),
        .base_ok(base_ok),.calibrated(calibrated),.raw(record_raw),
        .bias_x(bias_x),.bias_y(bias_y),.bias_z(bias_z),
        .checked_ready(checked_ready),.reject_detail(temporal_detail),
        .quiet_count(quiet_count),.candidate_pending(candidate_pending));
    imu_checked_guard guard(.clk(clk50),.rst_n(rst_n),.record_ready(checked_ready),
        .who(who),.pwr(pwr),.raw(record_raw),.extra_reason(extra_reason),
        .sample_valid(sample_valid),.accepted_raw(accepted_raw),.sample_dt_ticks(dt_ticks),
        .link_usable(link_usable),.stale(),.reject_reason(reason),
        .accepted_count(accepted_count),.rejected_count(rejected_count),.bad_streak(),.age_ticks());
    reg reject_event=0;
    always @(posedge clk50) reject_event <= rst_n && checked_ready && (!base_ok || (|temporal_detail));
    wire [15:0] cal_count;
    wire [7:0] attitude_fault;
    tilt_estimator #(.CAL_SAMPLES(CAL_SAMPLES)) estimator(.clk(clk50),.rst_n(rst_n),.sample_valid(sample_valid),
        .link_usable(link_usable),.raw(accepted_raw),.dt_ticks(dt_ticks),
        .reject_event(reject_event),
        .calibrated(calibrated),.attitude_valid(attitude_valid),.update(attitude_update),
        .roll_cdeg(roll),.pitch_cdeg(pitch),.bias_x(bias_x),.bias_y(bias_y),.bias_z(bias_z),
        .cal_count(cal_count),.fault(attitude_fault),.accel_correction(accel_correction));
    assign led3=attitude_valid;
    // Publish AFTER guard + estimator finish. Every record (even rejected)
    // gets a report. Live status and angles are a coherent delayed snapshot.
    reg [9:0] report_delay=0;
    reg [15:0] seq_count=0;
    reg [5:0] send_index=0;
    reg [1:0] send_state=0;
    reg [351:0] packet=0;
    reg record_updated=0;
    always @(posedge clk50) begin
        if(!rst_n || record_ready) record_updated<=0;
        else if(attitude_update) record_updated<=1;
    end
    reg tx_start=0;
    wire tx_busy;
    wire [7:0] tx_data=packet[351:344];
    wire [7:0] flags={1'b0,(quiet_count>=16),candidate_pending,record_updated,
        accel_correction,attitude_valid,calibrated,link_usable};
    wire [351:0] new_packet={16'hA56E,seq_count,flags,reason,temporal_detail,quiet_count,who,pwr,
        gyro_cfg,accel_cfg,filter_cfg,int_status,record_raw,dt_ticks,
        roll,pitch,bias_x,bias_y,bias_z,cal_count,attitude_fault,8'b0};
    // 44 bytes: A5 6E | sequence BE16 | flags | reason | temporal | quiet | ID | PWR |
    // gyro | accel | filter | status | raw12 | dt BE32 | roll/pitch i16 |
    // bias xyz i16 | calibration count u16 | attitude fault | XOR.
    function [7:0] checksum;
        input [351:0] bytes;
        integer i;
        begin
            checksum=0;
            for(i=8;i<336;i=i+8) checksum=checksum^bytes[i+:8];
        end
    endfunction
    uart_tx_115200 uart(.clk(clk50),.start(tx_start),.data(tx_data),.tx(uart_tx),.busy(tx_busy));
    always @(posedge clk50) begin
        tx_start <= 0;
        if (!rst_n) begin
            report_delay <= 0; seq_count <= 0; send_state <= 0; send_index <= 0; packet <= 0;
        end else begin
            if(record_ready) begin report_delay <= 10'd127; seq_count<=seq_count+1'b1; end
            else if(report_delay != 0) report_delay <= report_delay-1'b1;
            case(send_state)
                0: if(report_delay == 1) begin
                    packet <= new_packet | checksum(new_packet);
                    send_index <= 0; send_state <= 1;
                end
                1: if(!tx_busy) begin tx_start <= 1; send_state <= 2; end
                2: if(tx_busy) send_state <= 3;
                3: if(!tx_busy) begin
                    if(send_index==43) send_state <= 0;
                    else begin packet <= {packet[343:0],8'b0}; send_index <= send_index+1'b1; send_state <= 1; end
                end
            endcase
        end
    end
endmodule
