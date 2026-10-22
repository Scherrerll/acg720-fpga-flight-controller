// Bench angle-P / rate-PI controller; these gains are not flight tuning.
// Angles and commanded/measured rates: cdeg and cdeg/s (100 units per degree).
// ANGLE_KP_Q8: (degree/s)/degree. RATE_KP_Q8: us/(degree/s).
// RATE_KI_Q8: us/(degree/s * second). Integral state retains Q16 microseconds.
// Corrected gyro counts use +/-2000 dps: cdeg/s = counts*3125/512.
// All signed divisions round to nearest, with exact half cases away from zero.
// Six parallel restoring divisions avoid a long combinational wide divider.
// The transaction is cancelled on disable/reset, invalid dt or a busy overrun.
module rate_control #(
    parameter integer CLK_HZ=50000000,
    parameter integer ANGLE_KP_Q8=512,
    parameter integer RATE_KP_Q8=128,
    parameter integer RATE_KI_Q8=64,
    parameter integer MAX_RATE_CDEG_S=10000,
    parameter integer MAX_CORRECTION_US=80,
    parameter integer MAX_INTEGRAL_US=40,
    parameter integer MAX_DT_TICKS=3000000 // 60 ms at 50 MHz
) (
    input wire clk,rst_n,sample_update,enabled,
    input wire [31:0] dt_ticks,
    input wire signed [15:0] roll_cdeg,pitch_cdeg,target_roll_cdeg,target_pitch_cdeg,
    input wire signed [16:0] gx,gy,gz,
    input wire signed [31:0] target_yaw_rate_cdeg_s,
    output reg update,busy,
    output reg signed [15:0] roll_us,pitch_us,yaw_us,
    output reg [7:0] fault
);
    localparam IDLE=0,SCALE=1,NORMALIZE=2,ERRORS=3,BASE_PRODUCT=4,
        TIME_PRODUCT=5,DIV_INIT=6,DIVIDE=7,PROPOSE=8,ANTI_WINDUP=9,PUBLISH=10;
    localparam [63:0] I_DEN=64'd100*CLK_HZ;
    localparam integer I_REM_BITS=$clog2(I_DEN);
    localparam [I_REM_BITS:0] I_DEN_REMAINDER=I_DEN[I_REM_BITS:0];
    // Corrected signed17 gyro counts have |rate| <= 400000 cdeg/s, including
    // signed rounding. Nonnegative rate limits therefore bound the rate error.
    // Keep the original full-width fallback for a negative rate/gain parameter.
    localparam [63:0] ERROR_MAG_MAX=MAX_RATE_CDEG_S>=0 ?
        64'd400000+MAX_RATE_CDEG_S : 64'd4294967295;
    localparam integer ERROR_BITS=MAX_RATE_CDEG_S>=0 ? $clog2(ERROR_MAG_MAX+1)+1 : 33;
    localparam integer DT_BITS=MAX_DT_TICKS<1 ? 1 : $clog2(64'd1+MAX_DT_TICKS);
    localparam [63:0] I_BASE_MAX=ERROR_MAG_MAX*RATE_KI_Q8;
    localparam integer I_BASE_BITS=(RATE_KI_Q8<0 || MAX_RATE_CDEG_S<0) ? 64 :
        (I_BASE_MAX==0 ? 1 : $clog2(I_BASE_MAX+1));
    localparam integer I_TIME_BITS=I_BASE_BITS+DT_BITS<64 ? I_BASE_BITS+DT_BITS : 64;
    localparam signed [63:0] RATE_LIMIT=MAX_RATE_CDEG_S;
    localparam signed [63:0] U_LIMIT=64'sd65536*MAX_CORRECTION_US;
    localparam signed [63:0] I_LIMIT=64'sd65536*MAX_INTEGRAL_US;
    reg [3:0] state=IDLE;
    reg signed [16:0] angle_error_r=0,angle_error_p=0,held_gx=0,held_gy=0,held_gz=0;
    reg signed [31:0] held_yaw_target=0;
    reg [DT_BITS-1:0] held_dt=0;
    reg signed [63:0] angle_product_r=0,angle_product_p=0,
        gyro_product_r=0,gyro_product_p=0,gyro_product_y=0;
    reg signed [31:0] target_r=0,target_p=0,target_y=0,rate_r=0,rate_p=0,rate_y=0;
    reg signed [ERROR_BITS-1:0] error_r=0,error_p=0,error_y=0;
    reg negative_r=0,negative_p=0,negative_y=0;
    reg [I_BASE_BITS-1:0] i_base_r=0,i_base_p=0,i_base_y=0;
    reg [I_TIME_BITS-1:0] i_time_r=0,i_time_p=0,i_time_y=0;
    wire [63:0] i_time_r_extended={{(64-I_TIME_BITS){1'b0}},i_time_r},
        i_time_p_extended={{(64-I_TIME_BITS){1'b0}},i_time_p},
        i_time_y_extended={{(64-I_TIME_BITS){1'b0}},i_time_y};
    reg [63:0] p_quot_r=0,p_quot_p=0,p_quot_y=0,i_quot_r=0,i_quot_p=0,i_quot_y=0;
    reg [6:0] p_rem_r=0,p_rem_p=0,p_rem_y=0;
    reg [I_REM_BITS-1:0] i_rem_r=0,i_rem_p=0,i_rem_y=0;
    reg [6:0] division_left=0;
    reg signed [63:0] integral_r=0,integral_p=0,integral_y=0;
    reg signed [63:0] proposed_r=0,proposed_p=0,proposed_y=0;
    reg signed [63:0] proportional_r=0,proportional_p=0,proportional_y=0;
    reg signed [63:0] command_r=0,command_p=0,command_y=0;
    wire [7:0] p_trial_r={p_rem_r,p_quot_r[63]},p_trial_p={p_rem_p,p_quot_p[63]},
        p_trial_y={p_rem_y,p_quot_y[63]};
    wire [I_REM_BITS:0] i_trial_r={i_rem_r,i_quot_r[63]},
        i_trial_p={i_rem_p,i_quot_p[63]},i_trial_y={i_rem_y,i_quot_y[63]};
    wire [7:0] p_difference_r=p_trial_r-8'd100,p_difference_p=p_trial_p-8'd100,
        p_difference_y=p_trial_y-8'd100;
    wire [I_REM_BITS:0] i_difference_r=i_trial_r-I_DEN_REMAINDER,
        i_difference_p=i_trial_p-I_DEN_REMAINDER,i_difference_y=i_trial_y-I_DEN_REMAINDER;
    wire signed [63:0] trial_u_r=proportional_r+proposed_r,
        trial_u_p=proportional_p+proposed_p,trial_u_y=proportional_y+proposed_y;

    function signed [63:0] rounded_shift;
        input signed [63:0] value;
        input integer bits;
        reg signed [63:0] half;
        begin
            half=64'sd1 << (bits-1);
            rounded_shift=value<0 ? -((-value+half) >>> bits) : ((value+half) >>> bits);
        end
    endfunction
    function signed [31:0] clamp_rate;
        input signed [63:0] value;
        begin
            if(value>RATE_LIMIT) clamp_rate=MAX_RATE_CDEG_S;
            else if(value< -RATE_LIMIT) clamp_rate=-MAX_RATE_CDEG_S;
            else clamp_rate=value[31:0];
        end
    endfunction
    function signed [31:0] gyro_rate;
        input signed [63:0] product;
        reg signed [63:0] rounded;
        begin
            // Full corrected +/-65536 counts convert to at most 400000 cdeg/s.
            rounded=rounded_shift(product,9); gyro_rate=rounded[31:0];
        end
    endfunction
    function [63:0] absolute_error;
        input signed [ERROR_BITS-1:0] value;
        reg signed [63:0] extended;
        begin
            extended={{(64-ERROR_BITS){value[ERROR_BITS-1]}},value};
            absolute_error=extended<0 ? -extended : extended;
        end
    endfunction

    initial begin update=0; busy=0; roll_us=0; pitch_us=0; yaw_us=0; fault=0; end
    function signed [63:0] clamp_integral;
        input signed [63:0] value;
        begin
            if(value>I_LIMIT) clamp_integral=I_LIMIT;
            else if(value< -I_LIMIT) clamp_integral=-I_LIMIT;
            else clamp_integral=value;
        end
    endfunction
    function signed [15:0] output_us;
        input signed [63:0] value;
        reg signed [63:0] rounded;
        begin
            if(value>U_LIMIT) output_us=MAX_CORRECTION_US;
            else if(value< -U_LIMIT) output_us=-MAX_CORRECTION_US;
            else begin rounded=rounded_shift(value,16); output_us=rounded[15:0]; end
        end
    endfunction

    always @(posedge clk) begin
        update<=0;
        if(!rst_n || !enabled) begin
            state<=IDLE; busy<=0; fault<=0;
            integral_r<=0; integral_p<=0; integral_y<=0;
            roll_us<=0; pitch_us<=0; yaw_us<=0;
            division_left<=0;
        end else if(sample_update && busy) begin
            // Fault bit 1: overlap. Clear rather than publish a stale transaction.
            state<=IDLE; busy<=0; fault<=8'h02;
            integral_r<=0; integral_p<=0; integral_y<=0;
            roll_us<=0; pitch_us<=0; yaw_us<=0;
            division_left<=0;
        end else case(state)
            IDLE: if(sample_update) begin
                if(dt_ticks==0 || dt_ticks>MAX_DT_TICKS) begin
                    // Fault bit 0: invalid interval. No update is published.
                    integral_r<=0; integral_p<=0; integral_y<=0;
                    roll_us<=0; pitch_us<=0; yaw_us<=0; busy<=0; fault<=8'h01;
                end else begin
                    angle_error_r<=$signed({target_roll_cdeg[15],target_roll_cdeg})-
                        $signed({roll_cdeg[15],roll_cdeg});
                    angle_error_p<=$signed({target_pitch_cdeg[15],target_pitch_cdeg})-
                        $signed({pitch_cdeg[15],pitch_cdeg});
                    held_gx<=gx; held_gy<=gy; held_gz<=gz;
                    held_yaw_target<=target_yaw_rate_cdeg_s; held_dt<=dt_ticks[DT_BITS-1:0];
                    busy<=1; fault<=0; state<=SCALE;
                end
            end
            SCALE: begin
                angle_product_r<=angle_error_r*$signed(ANGLE_KP_Q8);
                angle_product_p<=angle_error_p*$signed(ANGLE_KP_Q8);
                gyro_product_r<=held_gx*64'sd3125;
                gyro_product_p<=held_gy*64'sd3125;
                gyro_product_y<=held_gz*64'sd3125;
                state<=NORMALIZE;
            end
            NORMALIZE: begin
                target_r<=clamp_rate(rounded_shift(angle_product_r,8));
                target_p<=clamp_rate(rounded_shift(angle_product_p,8));
                target_y<=clamp_rate({{32{held_yaw_target[31]}},held_yaw_target});
                rate_r<=gyro_rate(gyro_product_r);
                rate_p<=gyro_rate(gyro_product_p);
                rate_y<=gyro_rate(gyro_product_y);
                state<=ERRORS;
            end
            ERRORS: begin
                error_r<=$signed({target_r[31],target_r})-$signed({rate_r[31],rate_r});
                error_p<=$signed({target_p[31],target_p})-$signed({rate_p[31],rate_p});
                error_y<=$signed({target_y[31],target_y})-$signed({rate_y[31],rate_y});
                state<=BASE_PRODUCT;
            end
            BASE_PRODUCT: begin
                negative_r<=error_r[ERROR_BITS-1]; negative_p<=error_p[ERROR_BITS-1];
                negative_y<=error_y[ERROR_BITS-1];
                // P Q16 us = abs(cdeg/s)*KP_Q8*256/100.
                // I Q16 increment = abs(cdeg/s)*KI_Q8*dt_ticks*256/(100*CLK_HZ).
                p_quot_r<=absolute_error(error_r)*RATE_KP_Q8*64'd256+64'd50;
                p_quot_p<=absolute_error(error_p)*RATE_KP_Q8*64'd256+64'd50;
                p_quot_y<=absolute_error(error_y)*RATE_KP_Q8*64'd256+64'd50;
                i_base_r<=absolute_error(error_r)*RATE_KI_Q8;
                i_base_p<=absolute_error(error_p)*RATE_KI_Q8;
                i_base_y<=absolute_error(error_y)*RATE_KI_Q8;
                state<=TIME_PRODUCT;
            end
            TIME_PRODUCT: begin
                i_time_r<=i_base_r*held_dt; i_time_p<=i_base_p*held_dt; i_time_y<=i_base_y*held_dt;
                state<=DIV_INIT;
            end
            DIV_INIT: begin
                // Default product is unsigned25 x unsigned22 -> unsigned47.
                // Expand before shifting so the Q16 numerator loses no bits.
                i_quot_r<=(i_time_r_extended<<8)+(I_DEN>>1);
                i_quot_p<=(i_time_p_extended<<8)+(I_DEN>>1);
                i_quot_y<=(i_time_y_extended<<8)+(I_DEN>>1);
                p_rem_r<=0; p_rem_p<=0; p_rem_y<=0;
                i_rem_r<=0; i_rem_p<=0; i_rem_y<=0;
                division_left<=64; state<=DIVIDE;
            end
            DIVIDE: begin
                if(p_trial_r>=100) begin p_rem_r<=p_difference_r[6:0]; p_quot_r<={p_quot_r[62:0],1'b1}; end
                else begin p_rem_r<=p_trial_r[6:0]; p_quot_r<={p_quot_r[62:0],1'b0}; end
                if(p_trial_p>=100) begin p_rem_p<=p_difference_p[6:0]; p_quot_p<={p_quot_p[62:0],1'b1}; end
                else begin p_rem_p<=p_trial_p[6:0]; p_quot_p<={p_quot_p[62:0],1'b0}; end
                if(p_trial_y>=100) begin p_rem_y<=p_difference_y[6:0]; p_quot_y<={p_quot_y[62:0],1'b1}; end
                else begin p_rem_y<=p_trial_y[6:0]; p_quot_y<={p_quot_y[62:0],1'b0}; end
                if(i_trial_r>=I_DEN_REMAINDER) begin i_rem_r<=i_difference_r[I_REM_BITS-1:0]; i_quot_r<={i_quot_r[62:0],1'b1}; end
                else begin i_rem_r<=i_trial_r[I_REM_BITS-1:0]; i_quot_r<={i_quot_r[62:0],1'b0}; end
                if(i_trial_p>=I_DEN_REMAINDER) begin i_rem_p<=i_difference_p[I_REM_BITS-1:0]; i_quot_p<={i_quot_p[62:0],1'b1}; end
                else begin i_rem_p<=i_trial_p[I_REM_BITS-1:0]; i_quot_p<={i_quot_p[62:0],1'b0}; end
                if(i_trial_y>=I_DEN_REMAINDER) begin i_rem_y<=i_difference_y[I_REM_BITS-1:0]; i_quot_y<={i_quot_y[62:0],1'b1}; end
                else begin i_rem_y<=i_trial_y[I_REM_BITS-1:0]; i_quot_y<={i_quot_y[62:0],1'b0}; end
                division_left<=division_left-1'b1;
                if(division_left==1) state<=PROPOSE;
            end
            PROPOSE: begin
                proportional_r<=negative_r ? -$signed(p_quot_r) : $signed(p_quot_r);
                proportional_p<=negative_p ? -$signed(p_quot_p) : $signed(p_quot_p);
                proportional_y<=negative_y ? -$signed(p_quot_y) : $signed(p_quot_y);
                proposed_r<=clamp_integral(integral_r+(negative_r ? -$signed(i_quot_r) : $signed(i_quot_r)));
                proposed_p<=clamp_integral(integral_p+(negative_p ? -$signed(i_quot_p) : $signed(i_quot_p)));
                proposed_y<=clamp_integral(integral_y+(negative_y ? -$signed(i_quot_y) : $signed(i_quot_y)));
                state<=ANTI_WINDUP;
            end
            ANTI_WINDUP: begin
                // Conditional integration: do not push farther into PI saturation.
                // Reverse error may unwind existing integral; no mixer feedback is provided.
                if((trial_u_r>U_LIMIT && error_r>0) || (trial_u_r< -U_LIMIT && error_r<0))
                    command_r<=proportional_r+integral_r;
                else begin integral_r<=proposed_r; command_r<=trial_u_r; end
                if((trial_u_p>U_LIMIT && error_p>0) || (trial_u_p< -U_LIMIT && error_p<0))
                    command_p<=proportional_p+integral_p;
                else begin integral_p<=proposed_p; command_p<=trial_u_p; end
                if((trial_u_y>U_LIMIT && error_y>0) || (trial_u_y< -U_LIMIT && error_y<0))
                    command_y<=proportional_y+integral_y;
                else begin integral_y<=proposed_y; command_y<=trial_u_y; end
                state<=PUBLISH;
            end
            PUBLISH: begin
                roll_us<=output_us(command_r); pitch_us<=output_us(command_p); yaw_us<=output_us(command_y);
                update<=1; busy<=0; fault<=0; state<=IDLE;
            end
            default: begin
                state<=IDLE; busy<=0; fault<=8'h04;
                integral_r<=0; integral_p<=0; integral_y<=0;
                roll_us<=0; pitch_us<=0; yaw_us<=0;
            end
        endcase
    end
endmodule
