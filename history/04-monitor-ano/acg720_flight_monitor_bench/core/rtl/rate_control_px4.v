`timescale 1ns/1ps
// Adapted from PX4 RateControl; copyright and BSD-3-Clause terms in ../NOTICE_PX4.txt.
// Fixed-point three-axis candidate. No motor/pin interface.
// Same measured body mounting/gyro scale as existing verified bench.
// angle cdeg; gx/gy/gz signed17 corrected counts at +/-2000 dps.
module rate_control_px4 #(
    parameter integer CLK_HZ=50000000,
    parameter integer ANGLE_ROLL_P_Q16=131072,ANGLE_PITCH_P_Q16=131072,
    parameter integer ROLL_P_Q16=32768,ROLL_I_Q16=16384,ROLL_D_Q16=0,ROLL_FF_Q16=0,
    parameter integer PITCH_P_Q16=32768,PITCH_I_Q16=16384,PITCH_D_Q16=0,PITCH_FF_Q16=0,
    parameter integer YAW_P_Q16=32768,YAW_I_Q16=16384,YAW_D_Q16=0,YAW_FF_Q16=0,
    parameter integer MAX_RATE_CDEG_S=10000,MAX_CORRECTION_US=80,MAX_INTEGRAL_US=40,
    parameter integer MAX_DT_TICKS=3000000,D_FILTER_TAU_TICKS=795775,I_ATTENUATION_ENABLE=1
)(
    input wire clk,rst_n,sample_update,enabled,
    input wire [31:0] dt_ticks,
    input wire signed [15:0] roll_cdeg,pitch_cdeg,target_roll_cdeg,target_pitch_cdeg,
    input wire signed [16:0] gx,gy,gz,
    input wire signed [31:0] target_yaw_rate_cdeg_s,
    input wire [2:0] saturation_positive,saturation_negative,
    output reg update=0,
    output wire busy,
    output reg signed [15:0] roll_us=0,
    output reg signed [15:0] pitch_us=0,
    output reg signed [15:0] yaw_us=0,
    output wire [7:0] fault
);
    localparam IDLE=0,PRODUCTS=1,NORMALIZE=2,LAUNCH=3,WAIT=4,ANGLE_DIFFERENCE=5;
    reg [2:0] state=IDLE;
    reg [7:0] wrapper_fault=0;
    reg signed [16:0] held_gx=0,held_gy=0,held_gz=0,angle_error_roll=0,angle_error_pitch=0;
    reg signed [15:0] held_roll=0,held_pitch=0,held_roll_target=0,held_pitch_target=0;
    reg signed [31:0] held_yaw_target=0,target_roll=0,target_pitch=0,rate_roll=0,rate_pitch=0,rate_yaw=0;
    reg [31:0] held_dt=0;
    reg [2:0] held_saturation_positive=0,held_saturation_negative=0;
    reg signed [63:0] gyro_product_roll=0,gyro_product_pitch=0,gyro_product_yaw=0,
        angle_product_roll=0,angle_product_pitch=0;
    function signed [31:0] rounded_scale;
        input signed [63:0] value;
        input integer shift;
        reg signed [63:0] half,result;
        begin half=64'sd1<<(shift-1);result=value<0 ? -((-value+half)>>>shift) : ((value+half)>>>shift);rounded_scale=result[31:0];end
    endfunction
    wire [2:0] updates,busies;
    wire [7:0] fault_roll,fault_pitch,fault_yaw;
    wire [7:0] axis_fault=fault_roll|fault_pitch|fault_yaw;
    wire axis_start=state==LAUNCH && enabled && wrapper_fault==0;
    // Only registered state drives the large axis enable fanout. An overlapping
    // sample is cancelled by the wrapper priority branch below before publication;
    // wrapper_fault disables the axes on the next cycle.
    wire axis_enabled=enabled && wrapper_fault==0;
    wire signed [15:0] axis_roll_us,axis_pitch_us,axis_yaw_us;
    assign busy=state!=IDLE;
    assign fault=wrapper_fault|axis_fault;
    // Axis control states have equal latency, even for KD=0. The first seed,
    // disable/interval/overlap resets occur together, so publication is coherent.
    // Snapshot first, multiply second, round third, then launch. This prevents
    // body-mount subtraction + gyro conversion + PID input logic sharing a path.
    always @(posedge clk) begin
        update<=0;
        if(!rst_n || !enabled) begin
            state<=IDLE;wrapper_fault<=0;roll_us<=0;pitch_us<=0;yaw_us<=0;
        end else if(sample_update && state!=IDLE) begin
            state<=IDLE;wrapper_fault<=8'h02;roll_us<=0;pitch_us<=0;yaw_us<=0;
        end else if(axis_fault!=0 && wrapper_fault==0) begin
            state<=IDLE;wrapper_fault<=axis_fault;roll_us<=0;pitch_us<=0;yaw_us<=0;
        end else case(state)
            IDLE: if(sample_update) begin
                if(dt_ticks==0 || dt_ticks>MAX_DT_TICKS) begin
                    wrapper_fault<=8'h01;roll_us<=0;pitch_us<=0;yaw_us<=0;
                end else begin
                    held_gx<=gx;held_gy<=gy;held_gz<=gz;held_dt<=dt_ticks;
                    held_roll<=roll_cdeg;held_pitch<=pitch_cdeg;
                    held_roll_target<=target_roll_cdeg;held_pitch_target<=target_pitch_cdeg;
                    held_yaw_target<=target_yaw_rate_cdeg_s;
                    held_saturation_positive<=saturation_positive;held_saturation_negative<=saturation_negative;
                    wrapper_fault<=0;state<=ANGLE_DIFFERENCE;
                end
            end
            ANGLE_DIFFERENCE: begin
                angle_error_roll<=$signed({held_roll_target[15],held_roll_target})-$signed({held_roll[15],held_roll});
                angle_error_pitch<=$signed({held_pitch_target[15],held_pitch_target})-$signed({held_pitch[15],held_pitch});
                state<=PRODUCTS;
            end
            PRODUCTS: begin
                gyro_product_roll<=$signed(held_gx)*64'sd3125;
                gyro_product_pitch<=$signed(held_gy)*64'sd3125;
                gyro_product_yaw<=$signed(held_gz)*64'sd3125;
                angle_product_roll<=$signed(angle_error_roll)*$signed(ANGLE_ROLL_P_Q16);
                angle_product_pitch<=$signed(angle_error_pitch)*$signed(ANGLE_PITCH_P_Q16);
                state<=NORMALIZE;
            end
            NORMALIZE: begin
                rate_roll<=rounded_scale(gyro_product_roll,9);
                rate_pitch<=rounded_scale(gyro_product_pitch,9);
                rate_yaw<=rounded_scale(gyro_product_yaw,9);
                target_roll<=rounded_scale(angle_product_roll,16);
                target_pitch<=rounded_scale(angle_product_pitch,16);state<=LAUNCH;
            end
            LAUNCH: state<=WAIT;
            WAIT: if(&updates) begin
                roll_us<=axis_roll_us;pitch_us<=axis_pitch_us;yaw_us<=axis_yaw_us;
                update<=1;state<=IDLE;
            end
            default: begin state<=IDLE;wrapper_fault<=8'h10;roll_us<=0;pitch_us<=0;yaw_us<=0;end
        endcase
    end
    rate_pid_axis #(.CLK_HZ(CLK_HZ),.KP_US_Q16(ROLL_P_Q16),.KI_US_Q16(ROLL_I_Q16),.KD_US_Q16(ROLL_D_Q16),.KFF_US_Q16(ROLL_FF_Q16),
        .MAX_TARGET_CDEG_S(MAX_RATE_CDEG_S),.MAX_DT_TICKS(MAX_DT_TICKS),.D_FILTER_TAU_TICKS(D_FILTER_TAU_TICKS),
        .MAX_OUTPUT_US(MAX_CORRECTION_US),.MAX_I_US(MAX_INTEGRAL_US),.I_ATTENUATION_ENABLE(I_ATTENUATION_ENABLE)) roll_axis(
        .clk(clk),.rst_n(rst_n),.sample_update(axis_start),.enabled(axis_enabled),.dt_ticks(held_dt),
        .target_rate_cdeg_s(target_roll),.measured_rate_cdeg_s(rate_roll),.saturation_positive(held_saturation_positive[0]),.saturation_negative(held_saturation_negative[0]),
        .update(updates[0]),.busy(busies[0]),.output_us(axis_roll_us),.integral_q16(),.derivative_q16(),.fault(fault_roll));
    rate_pid_axis #(.CLK_HZ(CLK_HZ),.KP_US_Q16(PITCH_P_Q16),.KI_US_Q16(PITCH_I_Q16),.KD_US_Q16(PITCH_D_Q16),.KFF_US_Q16(PITCH_FF_Q16),
        .MAX_TARGET_CDEG_S(MAX_RATE_CDEG_S),.MAX_DT_TICKS(MAX_DT_TICKS),.D_FILTER_TAU_TICKS(D_FILTER_TAU_TICKS),
        .MAX_OUTPUT_US(MAX_CORRECTION_US),.MAX_I_US(MAX_INTEGRAL_US),.I_ATTENUATION_ENABLE(I_ATTENUATION_ENABLE)) pitch_axis(
        .clk(clk),.rst_n(rst_n),.sample_update(axis_start),.enabled(axis_enabled),.dt_ticks(held_dt),
        .target_rate_cdeg_s(target_pitch),.measured_rate_cdeg_s(rate_pitch),.saturation_positive(held_saturation_positive[1]),.saturation_negative(held_saturation_negative[1]),
        .update(updates[1]),.busy(busies[1]),.output_us(axis_pitch_us),.integral_q16(),.derivative_q16(),.fault(fault_pitch));
    rate_pid_axis #(.CLK_HZ(CLK_HZ),.KP_US_Q16(YAW_P_Q16),.KI_US_Q16(YAW_I_Q16),.KD_US_Q16(YAW_D_Q16),.KFF_US_Q16(YAW_FF_Q16),
        .MAX_TARGET_CDEG_S(MAX_RATE_CDEG_S),.MAX_DT_TICKS(MAX_DT_TICKS),.D_FILTER_TAU_TICKS(D_FILTER_TAU_TICKS),
        .MAX_OUTPUT_US(MAX_CORRECTION_US),.MAX_I_US(MAX_INTEGRAL_US),.I_ATTENUATION_ENABLE(I_ATTENUATION_ENABLE)) yaw_axis(
        .clk(clk),.rst_n(rst_n),.sample_update(axis_start),.enabled(axis_enabled),.dt_ticks(held_dt),
        .target_rate_cdeg_s(held_yaw_target),.measured_rate_cdeg_s(rate_yaw),.saturation_positive(held_saturation_positive[2]),.saturation_negative(held_saturation_negative[2]),
        .update(updates[2]),.busy(busies[2]),.output_us(axis_yaw_us),.integral_q16(),.derivative_q16(),.fault(fault_yaw));
endmodule
