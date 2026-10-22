// Bench tilt estimator, SENSOR axes, not an aircraft mounting transform.
// +/-16 g: 2048 counts/g. +/-2000 dps: 32768 counts/2000 dps.
// Gravity vector prediction g_dot = g cross omega, accelerometer correction
// with ~1 second time constant. No absolute yaw, no motor/control outputs.
module tilt_estimator #(
    parameter integer CAL_SAMPLES = 256,
    parameter integer MAX_CAL_REJECTS = 8,
    parameter integer MAX_DT_TICKS = 1500000, // 30 ms at 50 MHz
    parameter integer RESEED_SAMPLES = 3
) (
    input wire clk, rst_n, sample_valid, link_usable, reject_event,
    input wire [95:0] raw,
    input wire [31:0] dt_ticks,
    output reg calibrated = 0,
    output wire attitude_valid,
    output reg update = 0,
    output reg signed [15:0] roll_cdeg = 0,
    output reg signed [15:0] pitch_cdeg = 0,
    output reg signed [15:0] bias_x = 0,
    output reg signed [15:0] bias_y = 0,
    output reg signed [15:0] bias_z = 0,
    output reg [15:0] cal_count = 0,
    output reg [7:0] fault = 0,
    output reg accel_correction = 0
);
    localparam IDLE=0, ANGLE=1, PRODUCTS=2, PREDICT=3, CORRECT=4,
        CHECK=5, ROLL_START=6, ROLL_WAIT=7, PITCH_START=8, PITCH_WAIT=9,
        CORRECT_ADD=10, CHECK_SQUARE=11, CHECK_SUM=12;
    reg [3:0] state = IDLE;
    reg initialized = 0, ready = 0;
    reg [7:0] reseed_count=0;
    reg [7:0] cal_rejects=0;
    assign attitude_valid = ready && initialized && calibrated && link_usable;
    wire signed [15:0] ax=raw[95:80], ay=raw[79:64], az=raw[63:48];
    wire signed [15:0] wx=raw[47:32], wy=raw[31:16], wz=raw[15:0];
    wire signed [31:0] ax2=ax*ax, ay2=ay*ay, az2=az*az;
    wire [33:0] acc_norm2 = {2'b0,ax2}+{2'b0,ay2}+{2'b0,az2};
    wire acc_ok = acc_norm2 >= 34'd3030081 && acc_norm2 <= 34'd5546025;
    wire cal_gravity = acc_norm2 >= 34'd3783025 && acc_norm2 <= 34'd4626801;
    reg signed [31:0] sum_x=0, sum_y=0, sum_z=0;
    wire signed [31:0] average_x=(sum_x+wx)/CAL_SAMPLES;
    wire signed [31:0] average_y=(sum_y+wy)/CAL_SAMPLES;
    wire signed [31:0] average_z=(sum_z+wz)/CAL_SAMPLES;
    wire signed [31:0] scaled_ax={{8{ax[15]}},ax,8'b0};
    wire signed [31:0] scaled_ay={{8{ay[15]}},ay,8'b0};
    wire signed [31:0] scaled_az={{8{az[15]}},az,8'b0};
    reg signed [15:0] low_x=0, high_x=0, low_y=0, high_y=0, low_z=0, high_z=0;
    reg signed [15:0] prev_ax=0, prev_ay=0, prev_az=0;
    wire signed [16:0] dax={ax[15],ax}-{prev_ax[15],prev_ax};
    wire signed [16:0] day={ay[15],ay}-{prev_ay[15],prev_ay};
    wire signed [16:0] daz={az[15],az}-{prev_az[15],prev_az};
    wire still = cal_gravity && wx >= -164 && wx <= 164 &&
        wy >= -164 && wy <= 164 && wz >= -164 && wz <= 164 &&
        (cal_count == 0 || (dax >= -64 && dax <= 64 && day >= -64 && day <= 64 &&
            daz >= -64 && daz <= 64 &&
            wx >= $signed({high_x[15],high_x})-17'sd32 &&
            wx <= $signed({low_x[15],low_x})+17'sd32 &&
            wy >= $signed({high_y[15],high_y})-17'sd32 &&
            wy <= $signed({low_y[15],low_y})+17'sd32 &&
            wz >= $signed({high_z[15],high_z})-17'sd32 &&
            wz <= $signed({low_z[15],low_z})+17'sd32 &&
            $signed({high_x[15],high_x})-$signed({low_x[15],low_x}) <= 17'sd32 &&
            $signed({high_y[15],high_y})-$signed({low_y[15],low_y}) <= 17'sd32 &&
            $signed({high_z[15],high_z})-$signed({low_z[15],low_z}) <= 17'sd32));
    // Gravity values are accelerometer counts * 256, 1 g = 524288.
    reg signed [31:0] vx=0, vy=0, vz=524288;
    reg signed [31:0] mx=0, my=0, mz=0, px=0, py=0, pz=0;
    reg signed [16:0] rx=0, ry=0, rz=0;
    reg [31:0] held_dt=0, gain=0;
    reg use_acc=0;
    reg signed [31:0] theta_x=0, theta_y=0, theta_z=0;
    // theta Q24 = corrected_count * clock_ticks * 5997 / 2^24.
    // 5997 is rounded from (2000/32768)*(pi/180)/50e6 * 2^48.
    wire signed [63:0] tx_product = rx * $signed({1'b0,held_dt}) * 64'sd5997;
    wire signed [63:0] ty_product = ry * $signed({1'b0,held_dt}) * 64'sd5997;
    wire signed [63:0] tz_product = rz * $signed({1'b0,held_dt}) * 64'sd5997;
    wire [63:0] gain_product = held_dt * 64'd1374; // dt/~1s, Q16
    reg signed [63:0] cyz=0, czy=0, czx=0, cxz=0, cxy=0, cyx=0;
    wire signed [63:0] cross_x=cyz-czy, cross_y=czx-cxz, cross_z=cxy-cyx;
    wire signed [31:0] delta_x=cross_x[55:24],delta_y=cross_y[55:24],delta_z=cross_z[55:24];
    wire signed [63:0] fix_x = (mx-px) * $signed({1'b0,gain});
    wire signed [63:0] fix_y = (my-py) * $signed({1'b0,gain});
    wire signed [63:0] fix_z = (mz-pz) * $signed({1'b0,gain});
    reg signed [31:0] correction_x=0, correction_y=0, correction_z=0;
    reg [63:0] vx2=0,vy2=0,vz2=0;
    reg [65:0] vector_norm2=0;
    reg c_start=0;
    reg signed [31:0] c_x=0, c_y=0;
    wire c_busy, c_done;
    wire signed [31:0] c_angle;
    wire [31:0] c_mag;
    reg signed [15:0] pending_roll=0;
    reg [31:0] yz_magnitude=0;
    wire signed [63:0] angle_cdeg = c_angle * 64'sd100;
    // Reset a partially computed angle when the sample pipeline is abandoned.
    cordic_atan2 angles(.clk(clk),.rst_n(rst_n && link_usable && state!=IDLE),.start(c_start),
        .x_in(c_x),.y_in(c_y),.busy(c_busy),.done(c_done),
        .angle_q16(c_angle),.magnitude(c_mag));
    always @(posedge clk) begin
        update <= 0; c_start <= 0;
        if (!rst_n) begin
            state <= IDLE; initialized <= 0; ready <= 0; calibrated <= 0;
            reseed_count <= 0;
            cal_rejects <= 0;
            cal_count <= 0; sum_x <= 0; sum_y <= 0; sum_z <= 0;
            bias_x <= 0; bias_y <= 0; bias_z <= 0; fault <= 0;
            roll_cdeg <= 0; pitch_cdeg <= 0; accel_correction <= 0;
            vx <= 0; vy <= 0; vz <= 524288;
            low_x <= 0; high_x <= 0; low_y <= 0; high_y <= 0; low_z <= 0; high_z <= 0;
            prev_ax <= 0; prev_ay <= 0; prev_az <= 0;
        end else if (!link_usable) begin
            state <= IDLE; initialized <= 0; ready <= 0; fault <= 8'h01;
            reseed_count <= 0;
            if (!calibrated) begin
                cal_count <= 0; sum_x <= 0; sum_y <= 0; sum_z <= 0; cal_rejects <= 0;
            end
        end else if (reject_event) begin
            // An isolated rejection preserves a previously usable estimate,
            // but cannot contribute to consecutive recovery samples or bias.
            // A bounded number of discarded frames can interrupt calibration;
            // too many rejects reset its window rather than poison the average.
            reseed_count <= 0;
            if (!calibrated && cal_count!=0) begin
                if(cal_rejects>=MAX_CAL_REJECTS) begin
                    cal_count<=0; sum_x<=0; sum_y<=0; sum_z<=0; cal_rejects<=0; fault<=8'h02;
                end else cal_rejects<=cal_rejects+1'b1;
            end
            if (state!=IDLE) begin state<=IDLE; initialized<=0; ready<=0; fault<=8'h08; end
        end else if (sample_valid && state != IDLE) begin
            // Never overwrite a sample being processed.
            state <= IDLE; initialized <= 0; ready <= 0; fault <= 8'h08;
            reseed_count <= 0;
        end else case(state)
            IDLE: if (sample_valid) begin
                if (!calibrated) begin
                    if (!still) begin
                        cal_count <= 0; sum_x <= 0; sum_y <= 0; sum_z <= 0;
                        cal_rejects <= 0;
                        fault <= 8'h02;
                    end else begin
                        prev_ax <= ax; prev_ay <= ay; prev_az <= az;
                        if (cal_count == 0) begin
                            low_x <= wx; high_x <= wx; low_y <= wy; high_y <= wy;
                            low_z <= wz; high_z <= wz;
                        end else begin
                            if (wx < low_x) low_x <= wx; if (wx > high_x) high_x <= wx;
                            if (wy < low_y) low_y <= wy; if (wy > high_y) high_y <= wy;
                            if (wz < low_z) low_z <= wz; if (wz > high_z) high_z <= wz;
                        end
                        sum_x <= sum_x+wx; sum_y <= sum_y+wy; sum_z <= sum_z+wz;
                        cal_count <= cal_count+1'b1; fault <= 0;
                        if (cal_count == CAL_SAMPLES-1) begin
                            // Signed division truncates toward zero, including negative bias.
                            bias_x <= average_x[15:0];
                            bias_y <= average_y[15:0];
                            bias_z <= average_z[15:0];
                            calibrated <= 1;
                        end
                    end
                end else if (!initialized || dt_ticks == 0) begin
                    ready <= 0;
                    if (acc_ok && reseed_count >= RESEED_SAMPLES-1) begin
                        vx <= scaled_ax; vy <= scaled_ay; vz <= scaled_az;
                        initialized <= 1; accel_correction <= 1; fault <= 0;
                        reseed_count <= 0; state <= CHECK_SQUARE;
                    end else if (acc_ok) begin
                        initialized <= 0; reseed_count <= reseed_count+1'b1; fault <= 8'h80;
                    end else begin initialized <= 0; reseed_count <= 0; fault <= 8'h04; end
                end else if (dt_ticks > MAX_DT_TICKS) begin
                    initialized <= 0; ready <= 0; fault <= 8'h10;
                    reseed_count <= 0;
                end else begin
                    mx <= scaled_ax; my <= scaled_ay; mz <= scaled_az;
                    rx <= {wx[15],wx}-{bias_x[15],bias_x};
                    ry <= {wy[15],wy}-{bias_y[15],bias_y};
                    rz <= {wz[15],wz}-{bias_z[15],bias_z};
                    held_dt <= dt_ticks; use_acc <= acc_ok;
                    state <= ANGLE;
                end
            end
            ANGLE: begin
                theta_x <= tx_product[55:24]; theta_y <= ty_product[55:24];
                theta_z <= tz_product[55:24]; gain <= gain_product[51:20];
                state <= PRODUCTS;
            end
            PRODUCTS: begin
                // Limit the first-order prediction to <~5 degrees per update.
                if (theta_x > 1464087 || theta_x < -1464087 ||
                    theta_y > 1464087 || theta_y < -1464087 ||
                    theta_z > 1464087 || theta_z < -1464087) begin
                    state <= IDLE; initialized <= 0; ready <= 0; fault <= 8'h20;
                    reseed_count <= 0;
                end else begin
                    cyz <= vy*theta_z; czy <= vz*theta_y;
                    czx <= vz*theta_x; cxz <= vx*theta_z;
                    cxy <= vx*theta_y; cyx <= vy*theta_x; state <= PREDICT;
                end
            end
            PREDICT: begin
                px <= vx+delta_x; py <= vy+delta_y;
                pz <= vz+delta_z; state <= CORRECT;
            end
            CORRECT: begin
                correction_x <= fix_x[47:16]; correction_y <= fix_y[47:16];
                correction_z <= fix_z[47:16]; state <= CORRECT_ADD;
            end
            CORRECT_ADD: begin
                vx <= use_acc ? px+correction_x : px;
                vy <= use_acc ? py+correction_y : py;
                vz <= use_acc ? pz+correction_z : pz;
                accel_correction <= use_acc; fault <= 0; state <= CHECK_SQUARE;
            end
            CHECK_SQUARE: begin vx2 <= vx*vx; vy2 <= vy*vy; vz2 <= vz*vz; state <= CHECK_SUM; end
            CHECK_SUM: begin vector_norm2 <= {2'b0,vx2}+{2'b0,vy2}+{2'b0,vz2}; state <= CHECK; end
            CHECK: begin
                if (vector_norm2 < 66'd68719476736 || vector_norm2 > 66'd618475290624) begin
                    initialized <= 0; ready <= 0; fault <= 8'h40; state <= IDLE;
                    reseed_count <= 0;
                end else state <= ROLL_START;
            end
            ROLL_START: begin c_x <= vz; c_y <= vy; c_start <= 1; state <= ROLL_WAIT; end
            ROLL_WAIT: if (c_done) begin
                pending_roll <= angle_cdeg[31:16]; yz_magnitude <= c_mag;
                state <= PITCH_START;
            end
            PITCH_START: begin c_x <= yz_magnitude; c_y <= -vx; c_start <= 1; state <= PITCH_WAIT; end
            PITCH_WAIT: if (c_done) begin
                roll_cdeg <= pending_roll; pitch_cdeg <= angle_cdeg[31:16];
                ready <= 1; update <= 1; state <= IDLE;
            end
            default: begin state <= IDLE; initialized <= 0; ready <= 0; end
        endcase
    end
endmodule
