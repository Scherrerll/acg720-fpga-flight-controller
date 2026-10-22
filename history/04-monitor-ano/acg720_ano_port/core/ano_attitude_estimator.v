// Adapted from ANO Quadrotor_TM_V1 Ano_Imu.c and Ano_Sensor_Basic.c.
// See reference_ano for original ANO copyright. FPGA port: Q24 quaternion,
// sequential in-place Hamilton update exactly as the C source, gravity PI,
// four cascaded 0.25 LPFs (real-dt adjusted), no magnetometer.
// Sensor axes X forward/Y left/Z up. Public sensor tilt signs match the prior
// checked estimator: roll=atan2(gY,gZ), pitch=-asin(gX). Matrix R(q) is sensor
// body -> relative world (initial yaw zero), world Y remains LEFT-positive.
// Sensor yaw=atan2(R10,R00), positive with sensor +Z gyro; body yaw is
// negative, preserving the existing mounting transform. Relative heading only.
// Published acceleration uses that world frame in mm/s^2, gravity removed.
// Gains: gkp=.2, gki=.01; initial/recovery gravity alignment uses kp=10,
// ki=0 for >=200ms of small gravity error, reproducing ANO G_reset.
// No actuation. Input is already transport-checked +/-16g, +/-2000dps data.
module ano_attitude_estimator #(
 parameter integer CAL_SAMPLES=256,
 parameter integer MAX_DT_TICKS=3000000,
 parameter integer RESEED_SAMPLES=3,
 parameter integer MAX_CAL_REJECTS=8,
 parameter integer LEVEL_TRIM_ENABLE=0,
 parameter signed [31:0] LEVEL_R00_Q24=32'sd16777216,
 parameter signed [31:0] LEVEL_R01_Q24=0,
 parameter signed [31:0] LEVEL_R02_Q24=0,
 parameter signed [31:0] LEVEL_R10_Q24=0,
 parameter signed [31:0] LEVEL_R11_Q24=32'sd16777216,
 parameter signed [31:0] LEVEL_R12_Q24=0,
 parameter signed [31:0] LEVEL_R20_Q24=0,
 parameter signed [31:0] LEVEL_R21_Q24=0,
 parameter signed [31:0] LEVEL_R22_Q24=32'sd16777216
)(
 input wire clk,rst_n,sample_valid,link_usable,reject_event,
 input wire [95:0] raw,input wire [31:0] dt_ticks,
 output reg calibrated=0,output wire attitude_valid,
 output reg update=0,
 output reg signed [15:0] roll_cdeg=0,output reg signed [15:0] pitch_cdeg=0,output reg signed [15:0] yaw_cdeg=0,
 output reg signed [15:0] bias_x=0,output reg signed [15:0] bias_y=0,output reg signed [15:0] bias_z=0,
 output reg [15:0] cal_count=0,output reg [7:0] fault=0,
 output reg accel_correction=0,
 output reg signed [15:0] filtered_gx=0,output reg signed [15:0] filtered_gy=0,output reg signed [15:0] filtered_gz=0,
 output reg signed [31:0] world_ax_mmps2=0,output reg signed [31:0] world_ay_mmps2=0,output reg signed [31:0] world_az_mmps2=0,
 output wire linear_accel_valid
);
 localparam signed [31:0] ONE=32'sd16777216;
 localparam IDLE=0,RAW_SQUARE=1,RAW_SUM=2,DECIDE=3,ALPHA=4,FILTER=5,
 FILTER_MUL=6,FILTER_NEXT=7,FILTER_DONE=8,ACC_SQUARE=9,ACC_SUM=10,
 ACC_ROOT=11,ACC_ROOT_DONE=12,ACC_NORMALIZE=13,ACC_DIV_DONE=14,
 SEED=15,NORM_SQUARE=16,NORM_SUM=17,NORM_ROOT=18,NORM_ROOT_DONE=19,
 NORM_DIV=20,NORM_DIV_DONE=21,MATRIX_MUL=22,MATRIX_STORE=23,MATRIX_FORM=24,
 MATRIX_CONT=25,CROSS_MUL=26,CROSS_STORE=27,CROSS_FORM=28,
 DT_DIV=29,DT_DONE=30,ERR_I_DT=31,ERR_I_DT_DONE=32,ERR_I_GAIN_DONE=33,
 CORRECT_GAIN_DONE=34,GYRO_SCALE_DONE=35,DANGLE_DONE=36,
 QUAT_SETUP=37,QUAT_TERM=38,WORLD_SETUP=39,WORLD_TERM=40,WORLD_SCALE=41,
 WORLD_SCALE_DONE=42,ROLL_START=43,ROLL_DONE=44,PITCH_START=45,PITCH_DONE=46,
 PUBLISH=47,MUL_WAIT=60,DIV_WAIT=61,ROOT_WAIT=62;
 // Static mounting rotation T: old sensor -> level-corrected virtual sensor.
 // The original quaternion/filter/gravity PI and world-acceleration matrix are
 // unchanged. Only published orientation Rs*T^T and gyro T*g are transformed.
 localparam TRIM_MATRIX_SETUP=63,TRIM_MATRIX_TERM=64,TRIM_MATRIX_STORE=65,
 TRIM_GYRO_SETUP=66,TRIM_GYRO_TERM=67,TRIM_GYRO_STORE=68;
 function signed [31:0] trim_coefficient;
  input [1:0] row,col;
  begin
   case({row,col})
    4'b0000:trim_coefficient=LEVEL_R00_Q24;
    4'b0001:trim_coefficient=LEVEL_R01_Q24;
    4'b0010:trim_coefficient=LEVEL_R02_Q24;
    4'b0100:trim_coefficient=LEVEL_R10_Q24;
    4'b0101:trim_coefficient=LEVEL_R11_Q24;
    4'b0110:trim_coefficient=LEVEL_R12_Q24;
    4'b1000:trim_coefficient=LEVEL_R20_Q24;
    4'b1001:trim_coefficient=LEVEL_R21_Q24;
    4'b1010:trim_coefficient=LEVEL_R22_Q24;
    default:trim_coefficient=0;
   endcase
  end
 endfunction
 function signed [63:0] trim_product;
  input signed [31:0] lhs,rhs;
  begin trim_product=$signed(lhs)*$signed(rhs);end
 endfunction
 function trim_near_zero;
  input signed [63:0] value;
  begin trim_near_zero=value>=-64'sd1073741824 && value<=64'sd1073741824;end
 endfunction
 function trim_matrix_ok;
  input integer unused;
  integer r,c;
  reg good;
  begin
   good=1;
   // All expressions are compile-time constants: no hardware multipliers.
   for(r=0;r<3;r=r+1)for(c=0;c<3;c=c+1)
    if(trim_coefficient(r,c)>32'sd16777248 || trim_coefficient(r,c)<-32'sd16777248)good=0;
   for(r=0;r<3;r=r+1)
    if(!trim_near_zero(trim_product(trim_coefficient(r,0),trim_coefficient(r,0))+
      trim_product(trim_coefficient(r,1),trim_coefficient(r,1))+
      trim_product(trim_coefficient(r,2),trim_coefficient(r,2))-64'sd281474976710656))good=0;
   for(r=0;r<3;r=r+1)for(c=r+1;c<3;c=c+1)
    if(!trim_near_zero(trim_product(trim_coefficient(r,0),trim_coefficient(c,0))+
      trim_product(trim_coefficient(r,1),trim_coefficient(c,1))+
      trim_product(trim_coefficient(r,2),trim_coefficient(c,2))))good=0;
   // Require right handedness, rejecting an orthogonal reflection as well.
   if(!trim_near_zero(trim_product(LEVEL_R01_Q24,LEVEL_R12_Q24)-trim_product(LEVEL_R02_Q24,LEVEL_R11_Q24)-trim_product(LEVEL_R20_Q24,32'sd16777216)))good=0;
   if(!trim_near_zero(trim_product(LEVEL_R02_Q24,LEVEL_R10_Q24)-trim_product(LEVEL_R00_Q24,LEVEL_R12_Q24)-trim_product(LEVEL_R21_Q24,32'sd16777216)))good=0;
   if(!trim_near_zero(trim_product(LEVEL_R00_Q24,LEVEL_R11_Q24)-trim_product(LEVEL_R01_Q24,LEVEL_R10_Q24)-trim_product(LEVEL_R22_Q24,32'sd16777216)))good=0;
   trim_matrix_ok=good;
  end
 endfunction
 localparam LEVEL_MATRIX_VALID=trim_matrix_ok(0);
 reg signed [31:0] trim_matrix[0:4];
 wire [1:0] trim_row=index==0 ? 2'd0:index==1 ? 2'd1:2'd2;
 wire [1:0] trim_col=index<3 ? 2'd0:index==3 ? 2'd1:2'd2;
 wire [3:0] trim_row_base=trim_row==0 ? 4'd0:trim_row==1 ? 4'd3:4'd6;
 wire [3:0] trim_matrix_index=trim_row_base+{2'b0,term};
 wire signed [31:0] angle_r00=LEVEL_TRIM_ENABLE ? trim_matrix[0]:matrix[0];
 wire signed [31:0] angle_r10=LEVEL_TRIM_ENABLE ? trim_matrix[1]:matrix[3];
 wire signed [31:0] angle_r20=LEVEL_TRIM_ENABLE ? trim_matrix[2]:matrix[6];
 wire signed [31:0] angle_r21=LEVEL_TRIM_ENABLE ? trim_matrix[3]:matrix[7];
 wire signed [31:0] angle_r22=LEVEL_TRIM_ENABLE ? trim_matrix[4]:matrix[8];
 reg [6:0] state=IDLE,resume_state=IDLE;
 reg ready=0,initialized=0,filter_seeded=0,reseed=0;
 reg [7:0] reseed_count=0,cal_rejects=0;
 reg [95:0] captured_raw=0;reg [31:0] held_dt=0;
 reg signed [31:0] ax=0,ay=0,az=2048,gx=0,gy=0,gz=0;
 reg signed [31:0] a[0:2],g[0:2],an[0:2],q[0:3],ei[0:2],err[0:2],da[0:2];
 reg signed [31:0] matrix[0:8],qprod[0:8],crossprod[0:5];
 // Explicit24-slot packed storage avoids power-of-two RAMREG padding.
 localparam integer LPF_STORE_BITS=25;
 reg [24*LPF_STORE_BITS-1:0] lpf_storage=0;
 wire signed [31:0] lpf[0:23];
 reg signed [31:0] filter_input[0:5];
 genvar lpf_word;
 generate for(lpf_word=0;lpf_word<24;lpf_word=lpf_word+1)begin:lpf_read_alias
  assign lpf[lpf_word]=$signed(lpf_storage[lpf_word*LPF_STORE_BITS+:LPF_STORE_BITS]);
 end endgenerate
 reg signed [31:0] sum_x=0,sum_y=0,sum_z=0;
 reg signed [15:0] low_x=0,high_x=0,low_y=0,high_y=0,low_z=0,high_z=0;
 reg signed [15:0] prev_ax=0,prev_ay=0,prev_az=0;
 reg [63:0] raw_norm2=0,acc_norm2=0,norm2=0;
 reg [31:0] denominator=1,dt_q24=0,alpha_remaining=0;
 reg [16:0] alpha_factor=65536,alpha_q16=16384;
 reg [24:0] aligned_ticks=0;reg alignment=1,use_acc=0,lin_ok=0;
 reg [25:0] gravity_abs_x=0,gravity_abs_y=0;reg [26:0] gravity_error_sum=0;
 reg [4:0] index=0;reg [1:0] axis=0,component=0,term=0;
 reg matrix_for_output=0;
 reg signed [63:0] accum=0,prod=0,quotient=0;
 reg signed [31:0] corrected_rate=0,pending_roll=0,pending_pitch=0,pending_yaw=0;
 reg signed [31:0] pending_world[0:2],pending_gyro[0:2];
 reg [31:0] yz_magnitude=0;
 // Preserve the original64-bit add and32-bit truncation in one shared adder.
 wire signed [31:0] next_lpf=lpf[index]+(prod>>>16);
 wire signed [15:0] raw_ax=captured_raw[95:80],raw_ay=captured_raw[79:64],raw_az=captured_raw[63:48];
 wire signed [15:0] raw_gx=captured_raw[47:32],raw_gy=captured_raw[31:16],raw_gz=captured_raw[15:0];
 wire signed [16:0] dax={raw_ax[15],raw_ax}-{prev_ax[15],prev_ax};
 wire signed [16:0] day={raw_ay[15],raw_ay}-{prev_ay[15],prev_ay};
 wire signed [16:0] daz={raw_az[15],raw_az}-{prev_az[15],prev_az};
 wire raw_ok=captured_raw!=0 && captured_raw!={96{1'b1}} &&
 raw_ax!=-32768 && raw_ay!=-32768 && raw_az!=-32768 &&
 raw_gx!=-32768 && raw_gy!=-32768 && raw_gz!=-32768;
 wire raw_gravity=raw_norm2>=64'd3783025 && raw_norm2<=64'd4626801;
 wire reseed_gravity=raw_norm2>=64'd3530262 && raw_norm2<=64'd4897040;
 wire still=raw_gravity && raw_gx>=-164 && raw_gx<=164 && raw_gy>=-164 && raw_gy<=164 && raw_gz>=-164 && raw_gz<=164 &&
 (cal_count==0 || (dax>=-64 && dax<=64 && day>=-64 && day<=64 && daz>=-64 && daz<=64 &&
 $signed({raw_gx[15],raw_gx}) >= $signed({high_x[15],high_x})-17'sd32 &&
 $signed({raw_gx[15],raw_gx}) <= $signed({low_x[15],low_x})+17'sd32 &&
 $signed({raw_gy[15],raw_gy}) >= $signed({high_y[15],high_y})-17'sd32 &&
 $signed({raw_gy[15],raw_gy}) <= $signed({low_y[15],low_y})+17'sd32 &&
 $signed({raw_gz[15],raw_gz}) >= $signed({high_z[15],high_z})-17'sd32 &&
 $signed({raw_gz[15],raw_gz}) <= $signed({low_z[15],low_z})+17'sd32));
 assign attitude_valid=calibrated && initialized && ready && link_usable && (!LEVEL_TRIM_ENABLE || LEVEL_MATRIX_VALID);
 assign linear_accel_valid=attitude_valid && lin_ok;
 // A later rejected raw record does not belong to the already checked,
 // locked candidate in a stable pose epoch. Let that candidate and its
 // one-clock math completion pulses finish. Startup/recovery still require
 // consecutive checked records and retain the original rejection semantics.
 wire stable_pose_epoch=calibrated && initialized && ready;
 wire reject_cancels_candidate=reject_event && !stable_pose_epoch;
 wire cancel_math=!rst_n || !link_usable || reject_cancels_candidate || (sample_valid && state!=IDLE);
 reg m_start=0,d_start=0,s_start=0,c_start=0;
 reg signed [31:0] m_a=0,m_b=0,c_x=0,c_y=0;
 reg signed [63:0] d_n=0;reg [31:0] d_d=1;reg [63:0] s_n=0;
 wire m_done,m_busy,d_done,d_busy,d_error,s_done,s_busy,c_done,c_busy;
 wire signed [63:0] m_result,d_result;wire [31:0] s_result,c_mag;
 wire signed [31:0] c_angle;
 ano_attitude_mul32 mul(.clk(clk),.rst_n(rst_n),.cancel(cancel_math),.start(m_start),.a(m_a),.b(m_b),.busy(m_busy),.done(m_done),.result(m_result));
 ano_attitude_div64 div(.clk(clk),.rst_n(rst_n),.cancel(cancel_math),.start(d_start),.numerator(d_n),.denominator(d_d),.busy(d_busy),.done(d_done),.error(d_error),.quotient(d_result));
 ano_attitude_sqrt64 sqrt(.clk(clk),.rst_n(rst_n),.cancel(cancel_math),.start(s_start),.radicand(s_n),.busy(s_busy),.done(s_done),.result(s_result));
 cordic_atan2 angle(.clk(clk),.rst_n(rst_n && !cancel_math),.start(c_start),.x_in(c_x),.y_in(c_y),.busy(c_busy),.done(c_done),.angle_q16(c_angle),.magnitude(c_mag));
 wire signed [63:0] cdeg_scaled=c_angle*64'sd100;
 wire signed [63:0] quaternion_term=(component==0 || (component==1 && term==2) || (component==2 && term==1) || (component==3 && term==2)) ? -prod:prod;
 // Keep the three original arithmetic/rounding boundaries but separate
 // negation,64-bit accumulation,and the final shifted quaternion add.
 reg signed [63:0] quaternion_term_q=0,quaternion_sum_q=0;
 wire signed [63:0] next_quaternion=$signed(q[component])+(quaternion_sum_q>>>24);
 function signed [15:0] sat16;input signed [31:0] v;begin sat16=v>32767 ? 16'sd32767 : v< -32767 ? -16'sd32767:v[15:0];end endfunction
 function signed [31:0] clip_error;input signed [31:0] v;begin clip_error=v>1677722 ? 1677722:v< -1677722 ? -1677722:v;end endfunction
 task multiply;input signed [31:0] lhs,rhs;input [6:0] next;begin m_a<=lhs;m_b<=rhs;m_start<=1;resume_state<=next;state<=MUL_WAIT;end endtask
 task divide;input signed [63:0] numerator;input [31:0] divisor;input [6:0] next;begin d_n<=numerator;d_d<=divisor;d_start<=1;resume_state<=next;state<=DIV_WAIT;end endtask
 task root;input [63:0] value;input [6:0] next;begin s_n<=value;s_start<=1;resume_state<=next;state<=ROOT_WAIT;end endtask
 task invalidate;input [7:0] code;begin state<=IDLE;ready<=0;initialized<=0;lin_ok<=0;reseed_count<=0;filter_seeded<=0;filtered_gx<=0;filtered_gy<=0;filtered_gz<=0;world_ax_mmps2<=0;world_ay_mmps2<=0;world_az_mmps2<=0;fault<=code;end endtask
 integer i,j;
 initial begin
  for(i=0;i<3;i=i+1) begin a[i]=0;g[i]=0;an[i]=0;ei[i]=0;err[i]=0;da[i]=0;pending_world[i]=0;pending_gyro[i]=0;end
  a[2]=2048;
  q[0]=ONE;q[1]=0;q[2]=0;q[3]=0;
  for(i=0;i<9;i=i+1) begin matrix[i]=0;qprod[i]=0;end
  for(i=0;i<6;i=i+1) begin crossprod[i]=0;filter_input[i]=0;end
  // lpf_storage has the same zero powerup values; recovery still seeds all24slots.
 end
 always @(posedge clk) begin
  update<=0;m_start<=0;d_start<=0;s_start<=0;c_start<=0;
  if(!rst_n) begin
   state<=IDLE;ready<=0;initialized<=0;calibrated<=0;filter_seeded<=0;lin_ok<=0;
   cal_count<=0;cal_rejects<=0;reseed_count<=0;sum_x<=0;sum_y<=0;sum_z<=0;
   bias_x<=0;bias_y<=0;bias_z<=0;fault<=0;accel_correction<=0;
   roll_cdeg<=0;pitch_cdeg<=0;yaw_cdeg<=0;filtered_gx<=0;filtered_gy<=0;filtered_gz<=0;
   world_ax_mmps2<=0;world_ay_mmps2<=0;world_az_mmps2<=0;
   alignment<=1;aligned_ticks<=0;
   for(i=0;i<3;i=i+1) begin ei[i]<=0;err[i]<=0;da[i]<=0;end
   q[0]<=ONE;q[1]<=0;q[2]<=0;q[3]<=0;
  end else if(LEVEL_TRIM_ENABLE && !LEVEL_MATRIX_VALID) begin
   invalidate(8'h40);calibrated<=0;cal_count<=0;cal_rejects<=0;
   sum_x<=0;sum_y<=0;sum_z<=0;
  end else if(!link_usable) begin
   invalidate(8'h01);
   if(!calibrated) begin cal_count<=0;cal_rejects<=0;sum_x<=0;sum_y<=0;sum_z<=0;end
  end else if(reject_cancels_candidate) begin
   reseed_count<=0;
   if(!calibrated && cal_count!=0) begin
    if(cal_rejects>=MAX_CAL_REJECTS) begin cal_count<=0;cal_rejects<=0;sum_x<=0;sum_y<=0;sum_z<=0;fault<=8'h02;end
    else cal_rejects<=cal_rejects+1'b1;
   end
   if(state!=IDLE) invalidate(8'h08);
  end else if(sample_valid && state!=IDLE) invalidate(8'h08);
  else case(state)
   IDLE:if(sample_valid) begin captured_raw<=raw;held_dt<=dt_ticks;axis<=0;raw_norm2<=0;state<=RAW_SQUARE;end
   RAW_SQUARE:case(axis)
    0:multiply($signed(raw_ax),$signed(raw_ax),RAW_SUM);
    1:multiply($signed(raw_ay),$signed(raw_ay),RAW_SUM);
    2:multiply($signed(raw_az),$signed(raw_az),RAW_SUM);
   endcase
   RAW_SUM:begin raw_norm2<=raw_norm2+prod;if(axis==2) state<=DECIDE;else begin axis<=axis+1'b1;state<=RAW_SQUARE;end end
   DECIDE:begin
    state<=IDLE;
    if(!raw_ok) invalidate(8'h04);
    else if(!calibrated) begin
     if(!still) begin cal_count<=0;sum_x<=0;sum_y<=0;sum_z<=0;cal_rejects<=0;fault<=8'h02;end
     else begin
      // Count consecutive rejected frames, not all rejects over the complete
      // 2048-sample mean. A transport-checked stationary sample ends the streak.
      cal_rejects<=0;
      prev_ax<=raw_ax;prev_ay<=raw_ay;prev_az<=raw_az;
      if(cal_count==0) begin low_x<=raw_gx;high_x<=raw_gx;low_y<=raw_gy;high_y<=raw_gy;low_z<=raw_gz;high_z<=raw_gz;end
      else begin
       if(raw_gx<low_x) low_x<=raw_gx;if(raw_gx>high_x) high_x<=raw_gx;
       if(raw_gy<low_y) low_y<=raw_gy;if(raw_gy>high_y) high_y<=raw_gy;
       if(raw_gz<low_z) low_z<=raw_gz;if(raw_gz>high_z) high_z<=raw_gz;
      end
      sum_x<=sum_x+raw_gx;sum_y<=sum_y+raw_gy;sum_z<=sum_z+raw_gz;cal_count<=cal_count+1'b1;fault<=0;
      if(cal_count==CAL_SAMPLES-1) begin
       bias_x<=($signed(sum_x)+$signed(raw_gx))/CAL_SAMPLES;
       bias_y<=($signed(sum_y)+$signed(raw_gy))/CAL_SAMPLES;
       bias_z<=($signed(sum_z)+$signed(raw_gz))/CAL_SAMPLES;
       calibrated<=1;
      end
     end
    end else if(held_dt>MAX_DT_TICKS) invalidate(8'h10);
    else if(!initialized || held_dt==0) begin
     ready<=0;initialized<=0;lin_ok<=0;
     if(!reseed_gravity) begin reseed_count<=0;fault<=8'h04;end
     else if(reseed_count<RESEED_SAMPLES-1) begin reseed_count<=reseed_count+1'b1;fault<=8'h80;end
     else begin reseed_count<=0;reseed<=1;filter_seeded<=0;state<=FILTER;index<=0;end
    end else begin
     reseed<=0;alpha_remaining<=held_dt+25000;alpha_factor<=65536;state<=ALPHA;
    end
   end
   ALPHA:if(alpha_remaining>=50000) begin alpha_remaining<=alpha_remaining-50000;alpha_factor<=(alpha_factor*3)>>2;end
    else begin alpha_q16<=65536-alpha_factor;index<=0;state<=FILTER;end
   FILTER:begin
    filter_input[0]<=$signed(raw_ax)<<<8;filter_input[1]<=$signed(raw_ay)<<<8;filter_input[2]<=$signed(raw_az)<<<8;
    filter_input[3]<=($signed(raw_gx)-$signed(bias_x))<<<8;
    filter_input[4]<=($signed(raw_gy)-$signed(bias_y))<<<8;
    filter_input[5]<=($signed(raw_gz)-$signed(bias_z))<<<8;
    state<=FILTER_NEXT;
   end
   FILTER_NEXT:if(!filter_seeded) begin
    for(i=0;i<6;i=i+1) for(j=0;j<4;j=j+1) lpf_storage[(4*i+j)*LPF_STORE_BITS+:LPF_STORE_BITS]<=filter_input[i];
    filter_seeded<=1;state<=FILTER_DONE;
   end else state<=FILTER_MUL;
   FILTER_MUL:begin
    // index 0 is stage closest to raw. The source updates 3,2,1,0 in place;
    // this storage uses 0,1,2,3 but exactly the same cascade ordering.
    if(index[1:0]==0) multiply(filter_input[index>>2]-lpf[index],$signed({15'b0,alpha_q16}),49);
    else multiply(lpf[index-1]-lpf[index],$signed({15'b0,alpha_q16}),49);
   end
   49:begin
    for(i=0;i<24;i=i+1)
     if(index==i)lpf_storage[i*LPF_STORE_BITS+:LPF_STORE_BITS]<=next_lpf;
    if(index==23) state<=FILTER_DONE;else begin index<=index+1'b1;state<=FILTER_MUL;end
   end
   FILTER_DONE:begin
    for(i=0;i<3;i=i+1) begin a[i]<=lpf[4*i+3]>>>8;g[i]<=lpf[4*(i+3)+3]>>>8;pending_gyro[i]<=lpf[4*(i+3)+3]>>>8;end
    axis<=0;acc_norm2<=0;state<=ACC_SQUARE;
   end
   ACC_SQUARE:multiply(a[axis],a[axis],ACC_SUM);
   ACC_SUM:begin acc_norm2<=acc_norm2+prod;if(axis==2) state<=ACC_ROOT;else begin axis<=axis+1'b1;state<=ACC_SQUARE;end end
   ACC_ROOT:begin use_acc<=acc_norm2>=64'd3530262 && acc_norm2<=64'd4897040;root(acc_norm2,ACC_ROOT_DONE);end
   ACC_ROOT_DONE:if(s_result==0) begin
    if(reseed) invalidate(8'h04);
    else begin an[0]<=0;an[1]<=0;an[2]<=0;use_acc<=0;matrix_for_output<=0;index<=0;state<=MATRIX_MUL;end
   end else begin denominator<=s_result;axis<=0;state<=ACC_NORMALIZE;end
   ACC_NORMALIZE:divide($signed(a[axis])*64'sd16777216,denominator,ACC_DIV_DONE);
   ACC_DIV_DONE:begin
    an[axis]<=quotient;
    if(axis==2) begin if(reseed) state<=SEED;else begin matrix_for_output<=0;index<=0;state<=MATRIX_MUL;end end
    else begin axis<=axis+1'b1;state<=ACC_NORMALIZE;end
   end
   SEED:begin
    if(an[2]< -32'sd16777000) begin q[0]<=0;q[1]<=ONE;q[2]<=0;q[3]<=0;end
    else begin q[0]<=ONE+an[2];q[1]<=an[1];q[2]<=-an[0];q[3]<=0;end
    ei[0]<=0;ei[1]<=0;ei[2]<=0;alignment<=1;aligned_ticks<=0;index<=0;norm2<=0;state<=NORM_SQUARE;
   end
   NORM_SQUARE:multiply(q[index],q[index],NORM_SUM);
   NORM_SUM:begin norm2<=norm2+prod;if(index==3) state<=NORM_ROOT;else begin index<=index+1'b1;state<=NORM_SQUARE;end end
   NORM_ROOT:root(norm2,NORM_ROOT_DONE);
   NORM_ROOT_DONE:if(s_result<1000 || s_result>67108864) invalidate(8'h40);else begin denominator<=s_result;index<=0;state<=NORM_DIV;end
   NORM_DIV:divide($signed(q[index])*64'sd16777216,denominator,NORM_DIV_DONE);
   NORM_DIV_DONE:begin q[index]<=quotient;if(index==3) begin matrix_for_output<=1;index<=0;state<=MATRIX_MUL;end else begin index<=index+1'b1;state<=NORM_DIV;end end
   MATRIX_MUL:case(index)
    0:multiply(q[0],q[1],MATRIX_STORE);1:multiply(q[0],q[2],MATRIX_STORE);
    2:multiply(q[1],q[1],MATRIX_STORE);3:multiply(q[1],q[3],MATRIX_STORE);
    4:multiply(q[2],q[2],MATRIX_STORE);5:multiply(q[2],q[3],MATRIX_STORE);
    6:multiply(q[3],q[3],MATRIX_STORE);7:multiply(q[1],q[2],MATRIX_STORE);
    8:multiply(q[0],q[3],MATRIX_STORE);
   endcase
   MATRIX_STORE:begin qprod[index]<=prod>>>24;if(index==8) state<=MATRIX_FORM;else begin index<=index+1'b1;state<=MATRIX_MUL;end end
   MATRIX_FORM:begin
    matrix[0]<=ONE-2*(qprod[4]+qprod[6]);matrix[1]<=2*(qprod[7]-qprod[8]);matrix[2]<=2*(qprod[3]+qprod[1]);
    matrix[3]<=2*(qprod[7]+qprod[8]);matrix[4]<=ONE-2*(qprod[2]+qprod[6]);matrix[5]<=2*(qprod[5]-qprod[0]);
    matrix[6]<=2*(qprod[3]-qprod[1]);matrix[7]<=2*(qprod[5]+qprod[0]);matrix[8]<=ONE-2*(qprod[2]+qprod[4]);
    state<=MATRIX_CONT;
   end
   MATRIX_CONT:begin index<=0;if(matrix_for_output) begin component<=0;term<=0;accum<=0;state<=WORLD_SETUP;end else state<=CROSS_MUL;end
   CROSS_MUL:case(index)
    0:multiply(an[1],matrix[8],CROSS_STORE);1:multiply(matrix[7],an[2],CROSS_STORE);
    2:multiply(matrix[6],an[2],CROSS_STORE);3:multiply(an[0],matrix[8],CROSS_STORE);
    4:multiply(matrix[7],an[0],CROSS_STORE);5:multiply(an[1],matrix[6],CROSS_STORE);
   endcase
   CROSS_STORE:begin crossprod[index]<=prod>>>24;if(index==5) state<=CROSS_FORM;else begin index<=index+1'b1;state<=CROSS_MUL;end end
   CROSS_FORM:begin
    err[0]<=use_acc ? crossprod[0]-crossprod[1]:0;
    err[1]<=use_acc ? crossprod[2]-crossprod[3]:0;
    err[2]<=use_acc ? crossprod[4]-crossprod[5]:0;
    state<=52;
   end
   52:begin gravity_abs_x<=err[0]<0 ? -err[0]:err[0];gravity_abs_y<=err[1]<0 ? -err[1]:err[1];state<=53;end
   53:begin gravity_error_sum<={1'b0,gravity_abs_x}+{1'b0,gravity_abs_y};state<=DT_DIV;end
   DT_DIV:begin
    if(alignment && use_acc && gravity_error_sum<335544) begin
     if(aligned_ticks+held_dt>10000000) begin alignment<=0;aligned_ticks<=0;end else aligned_ticks<=aligned_ticks+held_dt;
    end else aligned_ticks<=0;
    divide($signed({1'b0,held_dt})*64'sd16777216,32'd50000000,DT_DONE);
   end
   DT_DONE:begin dt_q24<=quotient;axis<=0;state<=ERR_I_DT;end
   ERR_I_DT:multiply(clip_error(err[axis]),$signed(dt_q24),ERR_I_DT_DONE);
   ERR_I_DT_DONE:begin if(alignment) begin prod<=0;state<=ERR_I_GAIN_DONE;end else multiply(prod>>>24,32'sd167772,ERR_I_GAIN_DONE);end
   ERR_I_GAIN_DONE:begin ei[axis]<=ei[axis]+(prod>>>24);state<=48;end
   48:multiply(err[axis]+ei[axis],alignment ? 32'sd167772160:32'sd3355443,CORRECT_GAIN_DONE);
   CORRECT_GAIN_DONE:begin corrected_rate<=prod>>>24;multiply(g[axis],32'sd17855,GYRO_SCALE_DONE);end
   GYRO_SCALE_DONE:multiply((prod>>>0)+$signed(corrected_rate),$signed(dt_q24),DANGLE_DONE);
   DANGLE_DONE:begin
    da[axis]<=prod>>>25;
    if((prod>>>25)>731998 || (prod>>>25)< -731998) invalidate(8'h20);
    else if(axis==2) begin component<=0;term<=0;accum<=0;state<=QUAT_SETUP;end
    else begin axis<=axis+1'b1;state<=ERR_I_DT;end
   end
   QUAT_SETUP:case(component)
    0:case(term) 0:multiply(q[1],da[0],QUAT_TERM);1:multiply(q[2],da[1],QUAT_TERM);2:multiply(q[3],da[2],QUAT_TERM);endcase
    1:case(term) 0:multiply(q[0],da[0],QUAT_TERM);1:multiply(q[2],da[2],QUAT_TERM);2:multiply(q[3],da[1],QUAT_TERM);endcase
    2:case(term) 0:multiply(q[0],da[1],QUAT_TERM);1:multiply(q[1],da[2],QUAT_TERM);2:multiply(q[3],da[0],QUAT_TERM);endcase
    3:case(term) 0:multiply(q[0],da[2],QUAT_TERM);1:multiply(q[1],da[1],QUAT_TERM);2:multiply(q[2],da[0],QUAT_TERM);endcase
   endcase
   QUAT_TERM:begin quaternion_term_q<=quaternion_term;state<=54;end
   54:begin quaternion_sum_q<=accum+quaternion_term_q;state<=55;end
   55:if(term==2) begin
    q[component]<=next_quaternion;term<=0;accum<=0;
    if(component==3) begin index<=0;norm2<=0;state<=NORM_SQUARE;end else begin component<=component+1'b1;state<=QUAT_SETUP;end
   end else begin accum<=quaternion_sum_q;term<=term+1'b1;state<=QUAT_SETUP;end
   WORLD_SETUP:multiply(matrix[3*component+term],a[term],WORLD_TERM);
   WORLD_TERM:begin
    if(term==2) begin accum<=accum+prod;state<=WORLD_SCALE;end
    else begin accum<=accum+prod;term<=term+1'b1;state<=WORLD_SETUP;end
   end
   WORLD_SCALE:multiply(accum>>>16,32'sd9810,WORLD_SCALE_DONE);
   WORLD_SCALE_DONE:begin
    // (Q24 matrix * raw-counts * 9810/2048) -> mm/s^2.
    pending_world[component]<=($signed(prod)>>>19)-(component==2 ? 32'sd9810:0);
    if(component==2) begin
     if(LEVEL_TRIM_ENABLE) begin axis<=0;term<=0;accum<=0;state<=TRIM_GYRO_SETUP;end
     else state<=ROLL_START;
    end else begin component<=component+1'b1;term<=0;accum<=0;state<=WORLD_SETUP;end
   end
   TRIM_GYRO_SETUP:if(LEVEL_TRIM_ENABLE)multiply(trim_coefficient(axis,term),g[term],TRIM_GYRO_TERM);else invalidate(8'h40);
   TRIM_GYRO_TERM:if(LEVEL_TRIM_ENABLE)begin
    accum<=accum+prod;
    if(term==2)state<=TRIM_GYRO_STORE;
    else begin term<=term+1'b1;state<=TRIM_GYRO_SETUP;end
   end else invalidate(8'h40);
   TRIM_GYRO_STORE:if(LEVEL_TRIM_ENABLE)begin
    pending_gyro[axis]<=accum>>>24;
    term<=0;accum<=0;
    if(axis==2)begin index<=0;state<=TRIM_MATRIX_SETUP;end
    else begin axis<=axis+1'b1;state<=TRIM_GYRO_SETUP;end
   end else invalidate(8'h40);
   // Only five entries of Rs*T^T are needed for exact ZYX Euler extraction.
   // The original matrix is never overwritten: world acceleration and the
   // next gravity feedback step retain the original quaternion coordinates.
   TRIM_MATRIX_SETUP:if(LEVEL_TRIM_ENABLE)multiply(matrix[trim_matrix_index],trim_coefficient(trim_col,term),TRIM_MATRIX_TERM);else invalidate(8'h40);
   TRIM_MATRIX_TERM:if(LEVEL_TRIM_ENABLE)begin
    accum<=accum+prod;
    if(term==2)state<=TRIM_MATRIX_STORE;
    else begin term<=term+1'b1;state<=TRIM_MATRIX_SETUP;end
   end else invalidate(8'h40);
   TRIM_MATRIX_STORE:if(LEVEL_TRIM_ENABLE)begin
    trim_matrix[index]<=accum>>>24;
    term<=0;accum<=0;
    if(index==4)state<=ROLL_START;
    else begin index<=index+1'b1;state<=TRIM_MATRIX_SETUP;end
   end else invalidate(8'h40);
   ROLL_START:begin c_x<=angle_r22;c_y<=angle_r21;c_start<=1;state<=ROLL_DONE;end
   ROLL_DONE:if(c_done) begin pending_roll<=cdeg_scaled>>>16;yz_magnitude<=c_mag;state<=PITCH_START;end
   PITCH_START:begin c_x<=yz_magnitude;c_y<=-angle_r20;c_start<=1;state<=PITCH_DONE;end
   PITCH_DONE:if(c_done) begin pending_pitch<=cdeg_scaled>>>16;state<=50;end
   50:begin c_x<=angle_r00;c_y<=angle_r10;c_start<=1;state<=51;end
   51:if(c_done) begin pending_yaw<=cdeg_scaled>>>16;state<=PUBLISH;end
   PUBLISH:begin
    roll_cdeg<=pending_roll;pitch_cdeg<=pending_pitch;yaw_cdeg<=pending_yaw;
    filtered_gx<=sat16(pending_gyro[0]);filtered_gy<=sat16(pending_gyro[1]);filtered_gz<=sat16(pending_gyro[2]);
    world_ax_mmps2<=pending_world[0];world_ay_mmps2<=pending_world[1];world_az_mmps2<=pending_world[2];
    initialized<=1;ready<=1;lin_ok<=1;update<=1;accel_correction<=use_acc;fault<=0;state<=IDLE;
   end
   MUL_WAIT:if(m_done) begin prod<=m_result;state<=resume_state;end
   DIV_WAIT:if(d_done) begin if(d_error) invalidate(8'h40);else begin quotient<=d_result;state<=resume_state;end end
   ROOT_WAIT:if(s_done) state<=resume_state;
   default:invalidate(8'h40);
  endcase
 end
endmodule

// Shared exact signed32 x signed32 product, one 64-bit add per clock.
module ano_attitude_mul32(input wire clk,rst_n,start,cancel,
 input wire signed [31:0] a,b,output reg busy=0,output reg done=0,
 output reg signed [63:0] result=0);
 reg [63:0] lhs=0,acc=0;reg [31:0] rhs=0;reg [5:0] left=0;
 wire [63:0] sum=left==1 ? acc-(rhs[0]?lhs:64'd0):acc+(rhs[0]?lhs:64'd0);
 always @(posedge clk) begin
  done<=0;
  if(!rst_n || cancel) begin busy<=0;left<=0;result<=0;end
  else if(start && !busy) begin lhs<={{32{a[31]}},a};rhs<=b;acc<=0;left<=32;busy<=1;end
  else if(busy) begin acc<=sum;lhs<=lhs<<1;rhs<=rhs>>1;left<=left-1'b1;if(left==1) begin result<=sum;busy<=0;done<=1;end end
 end
endmodule
// Exact truncation-toward-zero signed64 / unsigned32 restoring divider.
module ano_attitude_div64(input wire clk,rst_n,start,cancel,
 input wire signed [63:0] numerator,input wire [31:0] denominator,
 output reg busy=0,output reg done=0,output reg error=0,output reg signed [63:0] quotient=0);
 reg [63:0] work=0;reg [31:0] remainder=0,divisor=1;reg [6:0] left=0;reg negative=0;
 wire [32:0] trial={remainder,work[63]};wire subtract=trial>={1'b0,divisor};
 wire [32:0] reduced=subtract ? trial-{1'b0,divisor}:trial;
 wire [63:0] next={work[62:0],subtract};
 always @(posedge clk) begin
  done<=0;
  if(!rst_n || cancel) begin busy<=0;left<=0;error<=0;quotient<=0;end
  else if(start && !busy) begin
   if(denominator==0 || numerator==64'sh8000000000000000) begin error<=1;done<=1;quotient<=0;end
   else begin work<=numerator<0 ? -numerator:numerator;negative<=numerator<0;divisor<=denominator;remainder<=0;left<=64;busy<=1;error<=0;end
  end else if(busy) begin
   remainder<=reduced[31:0];work<=next;left<=left-1'b1;
   if(left==1) begin quotient<=negative ? -$signed(next):$signed(next);busy<=0;done<=1;end
  end
 end
endmodule
// Unsigned floor(sqrt(u64)), 32 restoring steps, no divide/DSP block.
module ano_attitude_sqrt64(input wire clk,rst_n,start,cancel,
 input wire [63:0] radicand,output reg busy=0,output reg done=0,
 output reg [31:0] result=0);
 reg [63:0] bits=0;reg [65:0] rem=0;reg [31:0] root_value=0;reg [5:0] left=0;
 wire [65:0] trial_rem={rem[63:0],bits[63:62]};
 wire [65:0] trial_sub={32'b0,root_value,2'b01};
 wire pass=trial_rem>=trial_sub;
 always @(posedge clk) begin
  done<=0;
  if(!rst_n || cancel) begin busy<=0;left<=0;result<=0;end
  else if(start && !busy) begin bits<=radicand;rem<=0;root_value<=0;left<=32;busy<=1;end
  else if(busy) begin
   rem<=pass ? trial_rem-trial_sub:trial_rem;root_value<={root_value[30:0],pass};bits<=bits<<2;left<=left-1'b1;
   if(left==1) begin result<={root_value[30:0],pass};busy<=0;done<=1;end
  end
 end
endmodule
