`timescale 1ns/1ps
// Adapted from PX4 RateControl; copyright and BSD-3-Clause terms in ../NOTICE_PX4.txt.
// PX4 RateControl arithmetic adapted to FPGA fixed point; not a flight tune.
// Inputs target/measured cdeg/s; output integer us, internal I/D Q16 us.
// P/I/D/FF gains Q16: us/(deg/s), us/deg, us/(deg/s^2), us/(deg/s).
// D uses the derivative of a first-order low-pass filtered measured rate.
// This is equivalent to low-pass filtering its finite difference, with
// alpha=dt/(tau+dt). First sample is seeded: no enable or setpoint D kick.
// Integrator follows PX4 error attenuation and directional allocator feedback.
module rate_pid_axis #(
    parameter integer CLK_HZ=50000000,
    parameter integer KP_US_Q16=32768,KI_US_Q16=16384,KD_US_Q16=0,KFF_US_Q16=0,
    parameter integer MAX_TARGET_CDEG_S=10000,MAX_MEASURED_CDEG_S=400000,
    parameter integer MAX_DT_TICKS=3000000,
    parameter integer D_FILTER_TAU_TICKS=795775,
    parameter integer MAX_OUTPUT_US=80,MAX_I_US=40,
    parameter integer I_ATTENUATION_ENABLE=1
)(
    input wire clk,rst_n,sample_update,enabled,
    input wire [31:0] dt_ticks,
    input wire signed [31:0] target_rate_cdeg_s,measured_rate_cdeg_s,
    input wire saturation_positive,saturation_negative,
    output reg update,busy,
    output reg signed [15:0] output_us,
    output wire signed [63:0] integral_q16,
    output reg signed [63:0] derivative_q16,
    output reg [7:0] fault
);
    initial begin update=0;busy=0;output_us=0;derivative_q16=0;fault=0;end
    localparam [5:0] IDLE=0, FILTER_PRODUCT=1,FILTER_START=2,FILTER_WAIT=3,
        DERIVATIVE_PRODUCT=4,DERIVATIVE_START=5,DERIVATIVE_WAIT=6,
        D_PRODUCT=7,D_START=8,D_WAIT=9,P_PRODUCT=10,P_START=11,P_WAIT=12,
        I_BASE=13,I_TIME=14,I_START=15,I_WAIT=16,
        WEIGHT_PRODUCT=17,WEIGHT_START=18,WEIGHT_WAIT=19,
        I_WEIGHT=20,I_ROUND=21,FF_PRODUCT=22,FF_START=23,FF_WAIT=24,
        PROPOSE=25,SUM_PFF=26,SUM_D=27,ANTI_WINDUP=28,PUBLISH=29,
        FILTER_DIFF=30,DERIVATIVE_DIFF=31,OUTPUT_CLIP=32,MULTIPLY_WAIT=33;
    localparam signed [63:0] OUTPUT_LIMIT=64'sd65536*MAX_OUTPUT_US;
    localparam signed [63:0] I_LIMIT=64'sd65536*MAX_I_US;
    // These limits prove all sequential signed64 products stay below 2^63.
    localparam PARAMS_OK=CLK_HZ>=1000000 && CLK_HZ<=100000000 &&
        MAX_TARGET_CDEG_S>=0 && MAX_TARGET_CDEG_S<=10000 &&
        MAX_MEASURED_CDEG_S>0 && MAX_MEASURED_CDEG_S<=400000 &&
        MAX_DT_TICKS>0 && MAX_DT_TICKS<=3000000 &&
        D_FILTER_TAU_TICKS>=CLK_HZ/1000 && D_FILTER_TAU_TICKS<=1000000000 &&
        KP_US_Q16>=0 && KP_US_Q16<=6553600 && KI_US_Q16>=0 && KI_US_Q16<=6553600 &&
        KD_US_Q16>=0 && KD_US_Q16<=65536 && KFF_US_Q16>=0 && KFF_US_Q16<=6553600 &&
        MAX_OUTPUT_US>0 && MAX_OUTPUT_US<=32767 && MAX_I_US>=0 && MAX_I_US<=32767;
    reg [5:0] state=IDLE;
    reg seeded=0,held_sat_positive=0,held_sat_negative=0;
    reg [21:0] held_dt=0; // Checked dt <= 3,000,000 fits unsigned22.
    reg signed [14:0] held_target=0; // Clamped +/-10000 cdeg/s.
    reg signed [19:0] held_rate=0,error_rate=0; // Checked rate/error <=400000/410000.
    // The validated input/parameter bounds below, rather than lost precision,
    // permit these sizes. +/-400000*65536 fits s36; its difference fits s37.
    // P<=410000us fits s36, FF<=10000us fits s31, D<8000010us fits s40.
    // I increment<=1230000us fits s38 (dt3s at minimum1MHz), I<=32767us s32.
    reg signed [35:0] filtered_rate=0,new_filtered_rate=0;
    reg signed [36:0] rate_difference=0;
    reg signed [42:0] i_base=0; // <=410000*6553600 fits s43.
    reg signed [46:0] derivative_slope=0; // Q16 cdeg/s^2, tau>=1ms.
    reg signed [63:0] product=0;
    reg mul_start=0,mul_to_integral=0;
    reg [5:0] mul_resume=IDLE;
    reg signed [63:0] mul_a=0;
    reg signed [31:0] mul_b=0;
    wire mul_done,mul_busy;wire signed [63:0] mul_result;
    pid_multiply_signed64_32 multiplier(.clk(clk),.rst_n(rst_n),
        .cancel(!enabled || fault!=0),.start(mul_start),.a(mul_a),.b(mul_b),
        .busy(mul_busy),.done(mul_done),.result(mul_result));
    task multiply_then;
        input signed [63:0] a;input signed [31:0] b;
        input [5:0] resume_state;input integral_destination;
        begin mul_a<=a;mul_b<=b;mul_resume<=resume_state;mul_to_integral<=integral_destination;
            mul_start<=1;state<=MULTIPLY_WAIT;end
    endtask
    reg signed [35:0] p_term=0;
    reg signed [37:0] i_increment=0;
    reg signed [39:0] d_term=0;
    reg signed [30:0] ff_term=0;
    reg signed [31:0] integral_state=0,proposed_i=0,clipped_command=0;
    reg signed [40:0] command=0,control_base=0;
    assign integral_q16={{32{integral_state[31]}},integral_state};
    reg [16:0] i_factor=65536;
    reg div_start=0;
    reg signed [63:0] div_numerator=0;
    reg [33:0] div_denominator=1; // <=100*CLK_HZ<=10^10 fits34 bits
    wire div_busy,div_done;
    wire signed [63:0] div_quotient;
    pid_divide_signed64 #(.DIVISOR_BITS(34)) divider(.clk(clk),.rst_n(rst_n && enabled && fault==0),
        .start(div_start),.numerator(div_numerator),.denominator({30'd0,div_denominator}),
        .busy(div_busy),.done(div_done),.quotient(div_quotient));
    wire signed [35:0] measured_q16={held_rate,16'b0};
    wire signed [41:0] trial=$signed(control_base)+$signed(proposed_i);
    wire signed [38:0] proposed_sum=$signed(integral_state)+$signed(i_increment);
    wire signed [36:0] filtered_sum=$signed(filtered_rate)+$signed(div_quotient[36:0]);
    function signed [31:0] target_clamp;
        input signed [31:0] value;
        begin target_clamp=value>MAX_TARGET_CDEG_S ? MAX_TARGET_CDEG_S :
            (value< -MAX_TARGET_CDEG_S ? -MAX_TARGET_CDEG_S : value);end
    endfunction
    function signed [63:0] clip;
        input signed [63:0] value,limit;
        begin clip=value>limit ? limit : (value< -limit ? -limit : value);end
    endfunction
    function signed [63:0] round_shift16;
        input signed [63:0] value;
        begin round_shift16=value<0 ? -((-value+32768)>>>16) : ((value+32768)>>>16);end
    endfunction
    task cancel_state;
        begin
            state<=IDLE;busy<=0;output_us<=0;integral_state<=0;derivative_q16<=0;
            seeded<=0;filtered_rate<=0;new_filtered_rate<=0;div_start<=0;
            p_term<=0;d_term<=0;ff_term<=0;i_increment<=0;proposed_i<=0;command<=0;control_base<=0;
            rate_difference<=0;i_base<=0;derivative_slope<=0;clipped_command<=0;mul_start<=0;
        end
    endtask
    always @(posedge clk) begin
        update<=0;div_start<=0;mul_start<=0;
        if(!rst_n || !enabled) begin cancel_state();fault<=0;end
        else if(sample_update && busy) begin cancel_state();fault<=8'h02;end
        else case(state)
            IDLE: if(sample_update) begin
                if(!PARAMS_OK) begin cancel_state();fault<=8'h08;end
                else if(dt_ticks==0 || dt_ticks>MAX_DT_TICKS) begin cancel_state();fault<=8'h01;end
                else if(measured_rate_cdeg_s>MAX_MEASURED_CDEG_S ||
                        measured_rate_cdeg_s< -MAX_MEASURED_CDEG_S) begin cancel_state();fault<=8'h04;end
                else begin
                    held_dt<=dt_ticks[21:0];held_rate<=measured_rate_cdeg_s[19:0];
                    held_target<=target_clamp(target_rate_cdeg_s);
                    error_rate<=target_clamp(target_rate_cdeg_s)-measured_rate_cdeg_s;
                    held_sat_positive<=saturation_positive;held_sat_negative<=saturation_negative;
                    busy<=1;fault<=0;
                    if(!seeded) begin
                        new_filtered_rate<=$signed(measured_rate_cdeg_s)*64'sd65536;
                        d_term<=0;state<=P_PRODUCT;
                    end else state<=FILTER_DIFF;
                end
            end
            FILTER_DIFF: begin rate_difference<=$signed(measured_q16)-$signed(filtered_rate);state<=FILTER_PRODUCT;end
            FILTER_PRODUCT: multiply_then(rate_difference,$signed({1'b0,held_dt}),FILTER_START,0);
            FILTER_START: begin
                div_numerator<=product;div_denominator<=64'd0+D_FILTER_TAU_TICKS+held_dt;
                div_start<=1;state<=FILTER_WAIT;
            end
            FILTER_WAIT: if(div_done) begin new_filtered_rate<=filtered_sum[35:0];state<=DERIVATIVE_DIFF;end
            DERIVATIVE_DIFF: begin rate_difference<=$signed(new_filtered_rate)-$signed(filtered_rate);state<=DERIVATIVE_PRODUCT;end
            DERIVATIVE_PRODUCT: multiply_then(rate_difference,CLK_HZ,DERIVATIVE_START,0);
            DERIVATIVE_START: begin div_numerator<=product;div_denominator<=held_dt;div_start<=1;state<=DERIVATIVE_WAIT;end
            DERIVATIVE_WAIT: if(div_done) begin derivative_slope<=div_quotient[46:0];state<=D_PRODUCT;end
            D_PRODUCT: multiply_then(derivative_slope,KD_US_Q16,D_START,0);
            D_START: begin div_numerator<=product;div_denominator<=6553600;div_start<=1;state<=D_WAIT;end
            D_WAIT: if(div_done) begin d_term<=div_quotient;state<=P_PRODUCT;end
            P_PRODUCT: multiply_then(error_rate,KP_US_Q16,P_START,0);
            P_START: begin div_numerator<=product;div_denominator<=100;div_start<=1;state<=P_WAIT;end
            P_WAIT: if(div_done) begin p_term<=div_quotient;state<=I_BASE;end
            I_BASE: multiply_then(error_rate,KI_US_Q16,I_TIME,1);
            I_TIME: multiply_then(i_base,$signed({1'b0,held_dt}),I_START,0);
            I_START: begin div_numerator<=product;div_denominator<=64'd100*CLK_HZ;div_start<=1;state<=I_WAIT;end
            I_WAIT: if(div_done) begin
                i_increment<=div_quotient;
                if(I_ATTENUATION_ENABLE!=0) state<=WEIGHT_PRODUCT;
                else begin i_factor<=65536;state<=I_WEIGHT;end
            end
            WEIGHT_PRODUCT: multiply_then($signed(error_rate)*64'sd65536,error_rate,WEIGHT_START,0);
            WEIGHT_START: begin div_numerator<=product;div_denominator<=1600000000;div_start<=1;state<=WEIGHT_WAIT;end
            WEIGHT_WAIT: if(div_done) begin
                i_factor<=div_quotient>=65536 ? 0 : 65536-div_quotient;
                state<=I_WEIGHT;
            end
            I_WEIGHT: multiply_then(i_increment,$signed({1'b0,i_factor}),I_ROUND,0);
            I_ROUND: begin i_increment<=round_shift16(product);state<=FF_PRODUCT;end
            FF_PRODUCT: multiply_then(held_target,KFF_US_Q16,FF_START,0);
            MULTIPLY_WAIT: if(mul_done) begin
                if(mul_to_integral) i_base<=mul_result[42:0];else product<=mul_result;
                state<=mul_resume;
            end
            FF_START: begin div_numerator<=product;div_denominator<=100;div_start<=1;state<=FF_WAIT;end
            FF_WAIT: if(div_done) begin ff_term<=div_quotient;state<=PROPOSE;end
            PROPOSE: begin
                // Only inhibit integration that pushes into the allocator's
                // unavailable direction; reverse error is allowed to unwind.
                if((held_sat_positive && error_rate>0) || (held_sat_negative && error_rate<0)) proposed_i<=integral_state;
                else proposed_i<=clip(proposed_sum,I_LIMIT);
                state<=SUM_PFF;
            end
            SUM_PFF: begin control_base<=p_term+ff_term;state<=SUM_D;end
            SUM_D: begin control_base<=control_base-d_term;state<=ANTI_WINDUP;end
            ANTI_WINDUP: begin
                if((trial>OUTPUT_LIMIT && error_rate>0) || (trial< -OUTPUT_LIMIT && error_rate<0))
                    command<=control_base+integral_state;
                else begin integral_state<=proposed_i;command<=trial;end
                state<=OUTPUT_CLIP;
            end
            OUTPUT_CLIP: begin clipped_command<=clip(command,OUTPUT_LIMIT);state<=PUBLISH;end
            PUBLISH: begin
                output_us<=round_shift16(clipped_command);
                derivative_q16<=d_term;filtered_rate<=new_filtered_rate;seeded<=1;
                update<=1;busy<=0;fault<=0;state<=IDLE;
            end
            default: begin cancel_state();fault<=8'h10;end
        endcase
    end
endmodule

// Exact signed64 x signed32 low64 product in32 clocks. The caller's validated
// bounds exclude overflow. The final multiplier sign bit subtracts its weight.
module pid_multiply_signed64_32(input wire clk,rst_n,cancel,start,
 input wire signed [63:0] a,input wire signed [31:0] b,
 output reg busy,done,output reg signed [63:0] result);
 initial begin busy=0;done=0;result=0;end
 reg [63:0] lhs=0,acc=0;reg [31:0] rhs=0;reg [5:0] left=0;
 wire [63:0] term=rhs[0] ? lhs:64'd0;
 wire [63:0] sum=left==1 ? acc-term:acc+term;
 always @(posedge clk) begin
  done<=0;
  if(!rst_n || cancel) begin busy<=0;left<=0;result<=0;acc<=0;end
  else if(start && !busy) begin lhs<=a;rhs<=b;acc<=0;left<=32;busy<=1;end
  else if(busy) begin
   acc<=sum;lhs<=lhs<<1;rhs<=rhs>>1;left<=left-1'b1;
   if(left==1) begin result<=sum;busy<=0;done<=1;end
  end
 end
endmodule
