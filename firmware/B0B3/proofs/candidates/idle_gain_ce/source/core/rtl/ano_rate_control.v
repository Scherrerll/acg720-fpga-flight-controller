`timescale 1ns/1ps
// Port of ANO Att_2level_Ctrl / Att_1level_Ctrl / PID_calculate, flight branch.
// Provenance and intentional body-coordinate / safety adaptations are recorded
// in tools/ano_control_trace.json. Rates and controller terms use signed Q16.
// Inputs gx/gy/gz already use the verified FPGA body frame: do not negate twice.
// PWM correction 1 unit = 1 us on a 1000..2000 us ESC range.
module ano_rate_control #(
    parameter integer CLK_HZ=50000000,
    parameter integer GYRO_FRAC_BITS=0, // Legacy counts or Q12 body counts.
    parameter integer MAX_DT_TICKS=3000000,
    parameter integer MAX_COMPUTE_TICKS=4096,
    parameter integer ANGLE_P=7,
    parameter integer ROLL_KP_MILLI=4000, ROLL_KI_MILLI=3000, ROLL_KD_MILLI=150,
    parameter integer PITCH_KP_MILLI=4000, PITCH_KI_MILLI=3000, PITCH_KD_MILLI=150,
    parameter integer YAW_KP_MILLI=6000, YAW_KI_MILLI=500, YAW_KD_MILLI=0,
    parameter integer FINAL_P_MILLI=350
)(
    input wire clk,rst_n,sample_update,enabled,auto_takeoff,
    input wire [31:0] dt_ticks,
    input wire signed [15:0] roll_cdeg,pitch_cdeg,target_roll_cdeg,target_pitch_cdeg,
    input wire signed [16+GYRO_FRAC_BITS:0] gx,gy,gz,
    input wire signed [31:0] target_yaw_rate_cdeg_s,
    input wire [2:0] saturation_positive,saturation_negative,
    output reg update=0,
    output wire busy,
    output reg signed [15:0] roll_us=0,
    output reg signed [15:0] pitch_us=0,
    output reg signed [15:0] yaw_us=0,
    output reg [7:0] fault=0
);
    localparam IDLE=0, SELECT_AXIS=1, ANGLE_ERROR=2, OUTER_MUL=3,
      OUTER_DIV=4, OUTER_DONE=5, GYRO_MUL=6, GYRO_DIV=7,
      GYRO_DONE=8, ERROR=9, P_MUL=10, P_DIV=11, P_DONE=12,
      I_ERROR=13, I_GAIN=14, I_TIME=15, I_DIV=16, I_MILLI_DIV=17,
      I_DONE=18, D_DELTA=19, D_GAIN=20, D_TIME=21, D_DIV=22,
      D_DONE=23, SUM_P_I=24, SUM_D=25, FINAL_MUL=26,
      FINAL_DIV=27, OUTPUT_CLIP=28, AXIS_COMMIT=29, COMMIT=30,
      MUL_WAIT=31, DIV_WAIT=32, I_REMAINDER_SCALE=33;
    localparam [63:0] I_DENOMINATOR=64'd1000*CLK_HZ;
    localparam [63:0] GYRO_DENOMINATOR=64'd82<<GYRO_FRAC_BITS;
    localparam signed [63:0] I_ERROR_LIMIT=64'sd200*65536;
    localparam signed [63:0] I_LIMIT=64'sd250*65536;
    localparam signed [63:0] RATE_LIMIT=64'sd1600*65536;
    reg [5:0] state=IDLE,resume_state=IDLE;
    reg [1:0] axis=0;
    // Source keeps feedback history running while not taking_off. Our disabled
    // datapath is stopped for safety, so seed it on the first complete valid
    // transaction rather than differentiating physical gyro against zero.
    reg history_seeded=0;reg held_auto_takeoff=0;
    reg [31:0] held_dt=0,age=0,compute_age=0;
    reg signed [15:0] held_roll=0,held_pitch=0,held_target_roll=0,held_target_pitch=0;
    reg signed [16+GYRO_FRAC_BITS:0] held_gyro[0:2];
    reg signed [31:0] held_yaw_target=0;
    reg [2:0] held_sat_pos=0,held_sat_neg=0;
    reg signed [31:0] integrals[0:2],previous_feedback[0:2];
    // Exact state is integrals + integral_remainders / I_DENOMINATOR.
    // Rounded quotient residues lie within +/-25,000,000,000 (< signed36).
    reg signed [35:0] integral_remainders[0:2];
    reg signed [35:0] current_i_remainder=0,new_i_remainder=0;
    // |rounded increment|<=2359297; |current_i+increment|<=18743297.
    // Retain all fractional I state. Saved N is only modulo-2^36 bookkeeping:
    // the full signed64 N still goes to the divider, and q*D remains signed64.
    // Since |N-q*D|<=25e9<2^35, signed low36 subtraction recovers r exactly.
    reg signed [35:0] integral_numerator=0;
    reg signed [22:0] integral_increment=0;
    wire signed [35:0] integral_residual=integral_numerator-$signed(arithmetic_result[35:0]);
    wire signed [25:0] integral_candidate=$signed(current_i[25:0])+
      $signed({{3{integral_increment[22]}},integral_increment});
    reg signed [15:0] pending_us[0:2];
    reg signed [16+GYRO_FRAC_BITS:0] raw_feedback=0;
    reg signed [16:0] angle_difference=0;
    reg signed [31:0] target_rate=0,feedback=0;
    // A valid full yaw outer-loop target can approach32767deg/s. Subtracting
    // measured body rate needs more than32 Q16 bits even though each input fits.
    reg signed [63:0] error_rate=0;
    reg signed [31:0] kp=0,ki=0,kd=0,old_feedback=0,current_i=0;
    reg sat_pos=0,sat_neg=0;
    reg signed [63:0] p_term=0,new_i=0,d_term=0,sum=0,arithmetic_result=0;
    // The source output clamp is at most1000 Q16 =65536000, which fits
    // signed27. Narrow only AFTER the exact clamp; no limit or gain changes.
    reg signed [26:0] clipped_control_q16=0;
    reg mul_start=0,div_start=0;
    reg signed [63:0] mul_a=0,div_numerator=0;
    reg signed [31:0] mul_b=0;
    reg [63:0] div_denominator=1;
    wire mul_done,div_done,mul_busy,div_busy;
    wire signed [63:0] mul_result,div_result;
    wire overlap=sample_update && state!=IDLE;
    wire math_reset_n=rst_n && enabled && fault==0;
    assign busy=state!=IDLE;

    initial begin
        for(integer j=0;j<3;j=j+1) begin
            held_gyro[j]=0;integrals[j]=0;integral_remainders[j]=0;previous_feedback[j]=0;pending_us[j]=0;
        end
        if((GYRO_FRAC_BITS!=0 && GYRO_FRAC_BITS!=12) || CLK_HZ!=50000000 || MAX_DT_TICKS<1 || MAX_DT_TICKS>3000000 ||
           MAX_COMPUTE_TICKS<2500 || MAX_COMPUTE_TICKS>65535 || ANGLE_P<0 || ANGLE_P>7 ||
           ROLL_KP_MILLI<0 || ROLL_KP_MILLI>6000 || PITCH_KP_MILLI<0 || PITCH_KP_MILLI>6000 ||
           YAW_KP_MILLI<0 || YAW_KP_MILLI>6000 || ROLL_KI_MILLI<0 || ROLL_KI_MILLI>3000 ||
           PITCH_KI_MILLI<0 || PITCH_KI_MILLI>3000 || YAW_KI_MILLI<0 || YAW_KI_MILLI>3000 ||
           ROLL_KD_MILLI<0 || ROLL_KD_MILLI>150 || PITCH_KD_MILLI<0 || PITCH_KD_MILLI>150 ||
           YAW_KD_MILLI<0 || YAW_KD_MILLI>150 || FINAL_P_MILLI<0 || FINAL_P_MILLI>1000)
            $error("Unsupported ANO arithmetic parameter bounds");
    end

    function signed [63:0] clip;
        input signed [63:0] value,limit;
        begin clip=value>limit ? limit : value < -limit ? -limit : value;end
    endfunction
    function signed [15:0] clip_angle;
        input signed [15:0] value;
        begin clip_angle=value>2500 ? 16'sd2500 : value < -2500 ? -16'sd2500 : value;end
    endfunction
    function signed [15:0] output_round;
        input signed [26:0] value;
        reg signed [27:0] extended,magnitude,rounded;
        begin
          extended=$signed({value[26],value});
          magnitude=value[26] ? -extended : extended;
          rounded=(magnitude+28'sd32768)>>>16;
          output_round=value[26] ? -$signed(rounded[15:0]) : rounded[15:0];
        end
    endfunction
    task multiply_then;
        input signed [63:0] a;
        input signed [31:0] b;
        input [5:0] destination;
        begin mul_a<=a;mul_b<=b;mul_start<=1;resume_state<=destination;state<=MUL_WAIT;end
    endtask
    task divide_then;
        input signed [63:0] numerator;
        input [63:0] denominator;
        input [5:0] destination;
        begin div_numerator<=numerator;div_denominator<=denominator;
          div_start<=1;resume_state<=destination;state<=DIV_WAIT;end
    endtask
    task clear_transaction;
        begin state<=IDLE;roll_us<=0;pitch_us<=0;yaw_us<=0;compute_age<=0;history_seeded<=0;clipped_control_q16<=0;
          current_i_remainder<=0;new_i_remainder<=0;integral_numerator<=0;integral_increment<=0;
          for(integer j=0;j<3;j=j+1) begin
              integrals[j]<=0;integral_remainders[j]<=0;previous_feedback[j]<=0;pending_us[j]<=0;
          end
        end
    endtask

    ano_multiply_signed64_32 multiplier(.clk(clk),.rst_n(rst_n),
      .cancel(!enabled || fault!=0 || overlap),.start(mul_start),.a(mul_a),.b(mul_b),
      .busy(mul_busy),.done(mul_done),.result(mul_result));
    // Exact I denominator is CLK_HZ*1000=50e9, which fits unsigned36.
    // Gyro and D denominators also fit. The existing serial divider retains
    // fixed latency; all signs still use nearest / half-away-from-zero.
    pid_divide_signed64 #(.DIVISOR_BITS(36)) divider(.clk(clk),.rst_n(math_reset_n),
      .start(div_start),.numerator(div_numerator),.denominator(div_denominator),
      .busy(div_busy),.done(div_done),.quotient(div_result));

    always @(posedge clk) begin
        update<=0;mul_start<=0;div_start<=0;
        if(!rst_n || !enabled) begin
            clear_transaction();fault<=0;age<=0;
        end else if(fault!=0) begin
            clear_transaction();
        end else if(overlap) begin
            clear_transaction();fault<=8'h02;
        end else if(age>=MAX_DT_TICKS) begin
            clear_transaction();fault<=8'h04;
        end else if(state!=IDLE && compute_age>=MAX_COMPUTE_TICKS) begin
            clear_transaction();fault<=8'h08;
        end else begin
            age<=age+1'b1;
            if(state!=IDLE) compute_age<=compute_age+1'b1;
            case(state)
              IDLE: if(sample_update) begin
                  if(dt_ticks==0 || dt_ticks>MAX_DT_TICKS) begin
                      clear_transaction();fault<=8'h01;
                  end else if(target_yaw_rate_cdeg_s>3276700 || target_yaw_rate_cdeg_s< -3276700) begin
                      // Digital Q16 conversion guard, not a flight-rate limit.
                      clear_transaction();fault<=8'h20;
                  end else begin
                      held_auto_takeoff<=auto_takeoff;held_dt<=dt_ticks;age<=0;compute_age<=0;axis<=0;
                      held_roll<=roll_cdeg;held_pitch<=pitch_cdeg;
                      held_target_roll<=clip_angle(target_roll_cdeg);
                      held_target_pitch<=clip_angle(target_pitch_cdeg);
                      held_gyro[0]<=gx;held_gyro[1]<=gy;held_gyro[2]<=gz;
                      held_yaw_target<=target_yaw_rate_cdeg_s;
                      held_sat_pos<=saturation_positive;held_sat_neg<=saturation_negative;
                      state<=SELECT_AXIS;
                  end
              end
              SELECT_AXIS: begin
                  raw_feedback<=held_gyro[axis];old_feedback<=previous_feedback[axis];
                  current_i<=integrals[axis];current_i_remainder<=integral_remainders[axis];
                  sat_pos<=held_sat_pos[axis];sat_neg<=held_sat_neg[axis];
                  case(axis)
                    0: begin kp<=ROLL_KP_MILLI;ki<=held_auto_takeoff ?0:ROLL_KI_MILLI;kd<=ROLL_KD_MILLI;end
                    1: begin kp<=PITCH_KP_MILLI;ki<=held_auto_takeoff ?0:PITCH_KI_MILLI;kd<=PITCH_KD_MILLI;end
                    2: begin kp<=YAW_KP_MILLI;ki<=YAW_KI_MILLI;kd<=YAW_KD_MILLI;end
                  endcase
                  state<=ANGLE_ERROR;
              end
              ANGLE_ERROR: begin
                  if(axis==0) angle_difference<=$signed({held_target_roll[15],held_target_roll})-$signed({held_roll[15],held_roll});
                  else if(axis==1) angle_difference<=$signed({held_target_pitch[15],held_target_pitch})-$signed({held_pitch[15],held_pitch});
                  state<=OUTER_MUL;
              end
              OUTER_MUL: if(axis==2) multiply_then(held_yaw_target,32'sd65536,OUTER_DIV);
                  else multiply_then(angle_difference,ANGLE_P*65536,OUTER_DIV);
              OUTER_DIV: divide_then(arithmetic_result,64'd100,OUTER_DONE);
              OUTER_DONE: begin
                  target_rate<=axis==2 ? arithmetic_result[31:0] : clip(arithmetic_result,RATE_LIMIT);
                  state<=GYRO_MUL;
              end
              GYRO_MUL: multiply_then(raw_feedback,32'sd327680,GYRO_DIV);
              GYRO_DIV: divide_then(arithmetic_result,GYRO_DENOMINATOR,GYRO_DONE);
              GYRO_DONE: begin feedback<=arithmetic_result[31:0];state<=ERROR;end
              ERROR: begin error_rate<=$signed({{32{target_rate[31]}},target_rate})-$signed({{32{feedback[31]}},feedback});state<=P_MUL;end
              P_MUL: multiply_then(error_rate,kp,P_DIV);
              P_DIV: divide_then(arithmetic_result,64'd1000,P_DONE);
              P_DONE: begin p_term<=arithmetic_result;state<=I_ERROR;end
              I_ERROR: begin arithmetic_result<=clip(error_rate,I_ERROR_LIMIT);state<=I_GAIN;end
              I_GAIN: multiply_then(arithmetic_result,ki,I_TIME);
              I_TIME: multiply_then(arithmetic_result,$signed(held_dt),I_DIV);
              I_DIV: begin
                  // Freeze the complete fractional state only toward allocator
                  // saturation; an error reversal can immediately unwind it.
                  if((sat_pos && error_rate>0) || (sat_neg && error_rate<0)) begin
                      new_i<=current_i;new_i_remainder<=current_i_remainder;state<=D_DELTA;
                  end else begin
                      integral_numerator<=arithmetic_result+$signed(current_i_remainder);
                      divide_then(arithmetic_result+$signed(current_i_remainder),I_DENOMINATOR,I_MILLI_DIV);
                  end
              end
              I_MILLI_DIV: begin
                  integral_increment<=arithmetic_result;
                  multiply_then(arithmetic_result,CLK_HZ,I_REMAINDER_SCALE);
              end
              I_REMAINDER_SCALE: multiply_then(arithmetic_result,32'sd1000,I_DONE);
              I_DONE: begin
                  // arithmetic_result is quotient*denominator, so the signed
                  // residue is exact. Compare the fractional part at a boundary
                  // as well: a rounded integer at the limit may still be inside.
                  if(integral_candidate>I_LIMIT ||
                     (integral_candidate==I_LIMIT && integral_residual>0)) begin
                      new_i<=I_LIMIT;new_i_remainder<=0;
                  end else if(integral_candidate< -I_LIMIT ||
                     (integral_candidate== -I_LIMIT && integral_residual<0)) begin
                      new_i<= -I_LIMIT;new_i_remainder<=0;
                  end else begin
                      new_i<=integral_candidate;new_i_remainder<=integral_residual[35:0];
                  end
                  state<=D_DELTA;
              end
              D_DELTA: begin arithmetic_result<=$signed(feedback)-$signed(old_feedback);state<=D_GAIN;end
              D_GAIN: if(kd==0 || !history_seeded) begin d_term<=0;state<=SUM_P_I;end
                  else multiply_then(arithmetic_result,kd,D_TIME);
              D_TIME: multiply_then(arithmetic_result,CLK_HZ,D_DIV);
              D_DIV: divide_then(arithmetic_result,$unsigned(held_dt)*64'd1000,D_DONE);
              D_DONE: begin d_term<=arithmetic_result;state<=SUM_P_I;end
              SUM_P_I: begin sum<=p_term+new_i;state<=SUM_D;end
              SUM_D: begin sum<=sum-d_term;state<=FINAL_MUL;end
              FINAL_MUL: multiply_then(sum,FINAL_P_MILLI,FINAL_DIV);
              FINAL_DIV: divide_then(arithmetic_result,64'd1000,OUTPUT_CLIP);
              OUTPUT_CLIP: begin
                  clipped_control_q16<=clip(arithmetic_result,axis==2 ? 64'sd400*65536 : 64'sd1000*65536);
                  state<=AXIS_COMMIT;
              end
              AXIS_COMMIT: begin
                  pending_us[axis]<=output_round(clipped_control_q16);
                  integrals[axis]<=new_i[31:0];integral_remainders[axis]<=new_i_remainder;previous_feedback[axis]<=feedback;
                  if(axis==2) state<=COMMIT;
                  else begin axis<=axis+1'b1;state<=SELECT_AXIS;end
              end
              COMMIT: begin roll_us<=pending_us[0];pitch_us<=pending_us[1];yaw_us<=pending_us[2];
                  history_seeded<=1;update<=1;state<=IDLE;end
              MUL_WAIT: if(mul_done) begin arithmetic_result<=mul_result;state<=resume_state;end
              DIV_WAIT: if(div_done) begin arithmetic_result<=div_result;state<=resume_state;end
              default: begin clear_transaction();fault<=8'h10;end
            endcase
        end
    end
endmodule

// One shared exact low64 product. All active default parameter products are
// proved within signed64 (worst derivative numerator < 3.94e18).
module ano_multiply_signed64_32(input wire clk,rst_n,cancel,start,
    input wire signed [63:0] a,input wire signed [31:0] b,
    output reg busy=0,output reg done=0,output reg signed [63:0] result=0);
    reg [63:0] lhs=0,acc=0;
    reg [31:0] rhs=0;
    reg [5:0] left=0;
    wire [63:0] term=rhs[0] ? lhs : 64'd0;
    wire [63:0] sum=left==1 ? acc-term : acc+term;
    always @(posedge clk) begin
        done<=0;
        if(!rst_n || cancel) begin busy<=0;left<=0;result<=0;acc<=0;end
        else if(start && !busy) begin lhs<=a;rhs<=b;acc<=0;left<=32;busy<=1;end
        else if(busy) begin acc<=sum;lhs<=lhs<<1;rhs<=rhs>>1;left<=left-1'b1;
            if(left==1) begin result<=sum;busy<=0;done<=1;end
        end
    end
endmodule
