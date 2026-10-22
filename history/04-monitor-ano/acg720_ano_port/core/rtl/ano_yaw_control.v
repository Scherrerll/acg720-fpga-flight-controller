`timescale 1ns/1ps
// ANO Att_2level_Ctrl relative-yaw flight branch and angle PID_calculate.
// Source feedback assignment order is retained: error uses previous outer-loop
// yaw, then stores this transaction's quaternion yaw as next feedback.
// Source ANGLE yaw P5 / kd_ex.5 / kd_fb.5; PID feedback is zero so only kd_ex acts.
// Relative yaw comes from the gyro quaternion; no magnetometer is synthesized.
module ano_yaw_control #(
    parameter integer CLK_HZ=50000000,
    parameter integer MAX_DT_TICKS=3000000,
    parameter integer MAX_COMPUTE_TICKS=512,
    parameter integer MAX_STICK_RATE_CDEG_S=20000,
    parameter integer SLEW_CDEG_S_PER_UPDATE=3000
)(
    input wire clk,rst_n,sample_update,enabled,yaw_valid,
    input wire [31:0] dt_ticks,
    input wire signed [15:0] yaw_cdeg,
    input wire signed [31:0] stick_yaw_rate_cdeg_s,
    output reg update=0,
    output wire busy,
    output reg signed [31:0] target_yaw_rate_cdeg_s=0,
    output reg signed [15:0] heading_target_cdeg=0,
    output reg signed [15:0] yaw_error_cdeg=0,
    output reg signed [31:0] slewed_rate_cdeg_s=0,
    output reg [7:0] fault=0
);
    localparam IDLE=0,CLIP_COMMAND=1,ERROR_INHIBIT=2,SLEW=3,
      INCREMENT_TIME=4,INCREMENT_Q16=5,INCREMENT_DIV=6,INTEGRATE=7,
      WRAP_TARGET=8,ERROR=9,WRAP_ERROR=10,P_TERM=11,D_DELTA=12,
      D_TIME=13,D_DIV=14,SUM=15,ROUND=16,PUBLISH=17,
      MUL_WAIT=18,DIV_WAIT=19;
    localparam signed [63:0] HALF_TURN=64'sd18000*65536;
    localparam signed [63:0] FULL_TURN=64'sd36000*65536;
    localparam signed [63:0] ERROR_INHIBIT_LIMIT=64'sd9000*65536;
    reg [4:0] state=IDLE,resume_state=IDLE;
    reg [31:0] held_dt=0,age=0,compute_age=0;
    reg signed [15:0] held_yaw=0;
    reg signed [31:0] held_command=0,command=0,next_slew=0;
    // Q16 centidegrees, including fractional integrated heading.
    reg signed [63:0] expected_heading=0,feedback_old=0,error_old=0;
    reg signed [63:0] integrated=0,new_heading=0,new_error=0,p_term=0,d_term=0,result=0;
    reg signed [31:0] pending_rate=0;
    reg mul_start=0,div_start=0;
    reg signed [63:0] mul_a=0,div_numerator=0;
    reg signed [31:0] mul_b=0;
    reg [63:0] div_denominator=1;
    wire md,dd,mbusy,dbusy;
    wire signed [63:0] product,quotient;
    wire overlap=sample_update && state!=IDLE;
    wire usable_yaw=yaw_valid && yaw_cdeg>= -18000 && yaw_cdeg<=18000;
    assign busy=state!=IDLE;
    ano_multiply_signed64_32 multiply(.clk(clk),.rst_n(rst_n),
      .cancel(!enabled || !usable_yaw || fault!=0 || overlap),.start(mul_start),
      .a(mul_a),.b(mul_b),.busy(mbusy),.done(md),.result(product));
    pid_divide_signed64 #(.DIVISOR_BITS(32)) divide(.clk(clk),
      .rst_n(rst_n && enabled && usable_yaw && fault==0),.start(div_start),
      .numerator(div_numerator),.denominator(div_denominator),.busy(dbusy),.done(dd),.quotient(quotient));
    initial begin
        if(CLK_HZ!=50000000 || MAX_DT_TICKS<1 || MAX_DT_TICKS>3000000 ||
           MAX_COMPUTE_TICKS<400 || MAX_COMPUTE_TICKS>65535 ||
           MAX_STICK_RATE_CDEG_S<1 || MAX_STICK_RATE_CDEG_S>25000 ||
           SLEW_CDEG_S_PER_UPDATE!=3000) $error("Unsupported ANO yaw bounds");
    end
    function signed [63:0] wrap180;
        input signed [63:0] value;
        begin wrap180=value< -HALF_TURN ? value+FULL_TURN : value>HALF_TURN ? value-FULL_TURN : value;end
    endfunction
    function signed [63:0] rounded_q16;
        input signed [63:0] value;
        begin rounded_q16=value<0 ? -((-value+32768)>>>16) : ((value+32768)>>>16);end
    endfunction
    function signed [31:0] clip_command;
        input signed [31:0] value;
        begin clip_command=value>MAX_STICK_RATE_CDEG_S ? MAX_STICK_RATE_CDEG_S :
          value< -MAX_STICK_RATE_CDEG_S ? -MAX_STICK_RATE_CDEG_S : value;end
    endfunction
    task multiply_then;
        input signed [63:0] a;
        input signed [31:0] b;
        input [4:0] destination;
        begin mul_a<=a;mul_b<=b;mul_start<=1;resume_state<=destination;state<=MUL_WAIT;end
    endtask
    task divide_then;
        input signed [63:0] numerator;
        input [63:0] denominator;
        input [4:0] destination;
        begin div_numerator<=numerator;div_denominator<=denominator;
          div_start<=1;resume_state<=destination;state<=DIV_WAIT;end
    endtask
    task seed_current_yaw;
        begin
            state<=IDLE;compute_age<=0;target_yaw_rate_cdeg_s<=0;slewed_rate_cdeg_s<=0;
            expected_heading<=usable_yaw ? $signed(yaw_cdeg)*64'sd65536 : 64'sd0;
            feedback_old<=usable_yaw ? $signed(yaw_cdeg)*64'sd65536 : 64'sd0;
            heading_target_cdeg<=usable_yaw ? yaw_cdeg : 16'sd0;
            error_old<=0;yaw_error_cdeg<=0;
        end
    endtask
    always @(posedge clk) begin
        update<=0;mul_start<=0;div_start<=0;
        if(!rst_n || !enabled) begin seed_current_yaw();age<=0;fault<=0;end
        else if(fault!=0) seed_current_yaw();
        else if(!usable_yaw) begin seed_current_yaw();fault<=8'h04;end
        else if(overlap) begin seed_current_yaw();fault<=8'h02;end
        else if(age>=MAX_DT_TICKS) begin seed_current_yaw();fault<=8'h08;end
        else if(state!=IDLE && compute_age>=MAX_COMPUTE_TICKS) begin seed_current_yaw();fault<=8'h10;end
        else begin
            age<=age+1'b1;
            if(state!=IDLE) compute_age<=compute_age+1'b1;
            case(state)
              IDLE:if(sample_update) begin
                  if(dt_ticks==0 || dt_ticks>MAX_DT_TICKS) begin seed_current_yaw();fault<=8'h01;end
                  else begin held_yaw<=yaw_cdeg;held_dt<=dt_ticks;held_command<=stick_yaw_rate_cdeg_s;
                    age<=0;compute_age<=0;state<=CLIP_COMMAND;end
              end
              CLIP_COMMAND:begin command<=clip_command(held_command);state<=ERROR_INHIBIT;end
              ERROR_INHIBIT:begin
                  // Source previous yaw_err prevents an input from adding to
                  // an already >90deg heading error, while allowing recovery.
                  if((error_old>ERROR_INHIBIT_LIMIT && command>0) ||
                     (error_old< -ERROR_INHIBIT_LIMIT && command<0)) command<=0;
                  state<=SLEW;
              end
              SLEW:begin
                  if(command-slewed_rate_cdeg_s>SLEW_CDEG_S_PER_UPDATE) next_slew<=slewed_rate_cdeg_s+SLEW_CDEG_S_PER_UPDATE;
                  else if(command-slewed_rate_cdeg_s< -SLEW_CDEG_S_PER_UPDATE) next_slew<=slewed_rate_cdeg_s-SLEW_CDEG_S_PER_UPDATE;
                  else next_slew<=command;
                  state<=INCREMENT_TIME;
              end
              INCREMENT_TIME:multiply_then(next_slew,$signed(held_dt),INCREMENT_Q16);
              INCREMENT_Q16:multiply_then(result,32'sd65536,INCREMENT_DIV);
              INCREMENT_DIV:divide_then(result,CLK_HZ,INTEGRATE);
              INTEGRATE:begin integrated<=expected_heading+result;state<=WRAP_TARGET;end
              WRAP_TARGET:begin new_heading<=wrap180(integrated);state<=ERROR;end
              ERROR:begin new_error<=new_heading-feedback_old;state<=WRAP_ERROR;end
              WRAP_ERROR:begin new_error<=wrap180(new_error);state<=P_TERM;end
              P_TERM:multiply_then(new_error,32'sd5,D_DELTA);
              D_DELTA:begin p_term<=result;result<=new_error-error_old;state<=D_TIME;end
              D_TIME:multiply_then(result,CLK_HZ,D_DIV);
              D_DIV:divide_then(result,$unsigned(held_dt)*64'd2,SUM);
              SUM:begin d_term<=result;result<=p_term+result;state<=ROUND;end
              ROUND:begin
                  if(rounded_q16(result)>3276700 || rounded_q16(result)< -3276700) begin
                      // Numeric-domain overflow can only occur outside the
                      // source's6ms operating cadence, e.g. microscopic dt.
                      seed_current_yaw();fault<=8'h20;
                  end else begin pending_rate<=rounded_q16(result);state<=PUBLISH;end
              end
              PUBLISH:begin
                  expected_heading<=new_heading;feedback_old<=$signed(held_yaw)*64'sd65536;
                  error_old<=new_error;slewed_rate_cdeg_s<=next_slew;
                  heading_target_cdeg<=rounded_q16(new_heading);yaw_error_cdeg<=rounded_q16(new_error);
                  target_yaw_rate_cdeg_s<=pending_rate;update<=1;state<=IDLE;
              end
              MUL_WAIT:if(md) begin result<=product;state<=resume_state;end
              DIV_WAIT:if(dd) begin result<=quotient;state<=resume_state;end
              default:begin seed_current_yaw();fault<=8'h40;end
            endcase
        end
    end
endmodule
