`timescale 1ns/1ps
// Local relative odometry, not an absolute position sensor. Body X forward,
// Y right, Z down. Optical calibration maps counts into body translation
// angles (rad Q20). Rotation correction maps body angular increments into
// those same two angles. All six calibration bits must be explicitly verified.
// Default coefficients/mask intentionally forbid metric output and hold.
module relative_position #(
 parameter [7:0] CAL_MASK=0,
 parameter signed [31:0] FLOW_XX=0,FLOW_XY=0,FLOW_YX=0,FLOW_YY=0,
 parameter signed [31:0] ROT_XX=0,ROT_XY=0,ROT_XZ=0,
 parameter signed [31:0] ROT_YX=0,ROT_YY=0,ROT_YZ=0,
 parameter integer AGE_LIMIT=5000000,MIN_QUALITY=30,EXTERNAL_YAW=0
)(
 input wire clk,rst_n,origin_reset,
 input wire pose_update,pose_valid,input wire [31:0] pose_dt,pose_age,
 input wire signed [15:0] roll,pitch,
 input wire signed [15:0] yaw_reference_cdeg,
 input wire signed [16:0] gx,gy,gz,
 input wire flow_update,flow_link,input wire signed [15:0] dx,dy,
 input wire [7:0] quality,input wire [31:0] flow_dt,flow_age,
 input wire range_link,input wire [15:0] distance_cm,input wire [31:0] range_age,
 output wire calibrated,position_valid,height_valid,
 output reg qualified_position_valid=0,
 output reg update,output reg [15:0] reason,
 output reg signed [31:0] x_q8,y_q8,vx,vy,height_mm,vz,
 output reg signed [15:0] yaw_cdeg,
 output reg [31:0] sample_sequence,age);

 function signed [63:0] trunc_shift;
 input signed [63:0] value;input integer bits;
 begin trunc_shift=value<0 ? -((-value)>>>bits):(value>>>bits);end
 endfunction
 initial begin update=0;reason=0;x_q8=0;y_q8=0;vx=0;vy=0;height_mm=0;vz=0;sample_sequence=0;age=32'hffffffff; end

 assign calibrated=(CAL_MASK & 8'h3f)==8'h3f &&
    (FLOW_XX!=0 || FLOW_XY!=0) && (FLOW_YX!=0 || FLOW_YY!=0);
 localparam signed [31:0] GYRO_LIMIT=32'sd8200;
 wire pose_ok=gx>=-GYRO_LIMIT && gx<=GYRO_LIMIT && gy>=-GYRO_LIMIT && gy<=GYRO_LIMIT && gz>=-GYRO_LIMIT && gz<=GYRO_LIMIT && pose_valid && pose_age<3000000 && roll>=-1500 && roll<=1500 && pitch>=-1500 && pitch<=1500;
 wire sources_ok=pose_ok && flow_link && flow_age<AGE_LIMIT && range_link && range_age<AGE_LIMIT && distance_cm>=10 && distance_cm<=500;
 reg sources_ok_q=0;
 always @(posedge clk) if(!rst_n || origin_reset) sources_ok_q<=0;else sources_ok_q<=sources_ok;
 reg seen=0,continuity=0,transaction_epoch_ok=0;
 assign position_valid=calibrated && sources_ok && sources_ok_q && seen && age<AGE_LIMIT && !gyro_overrun;
 always @(posedge clk)begin
  if(!rst_n || origin_reset)qualified_position_valid<=0;
  else qualified_position_valid<=position_valid && quality>=MIN_QUALITY &&
   dx>=-2000 && dx<=2000 && dy>=-2000 && dy<=2000 && flow_dt>=50000 && flow_dt<=AGE_LIMIT;
 end
 // Height is only marked valid after tilt correction, with current source validity.
 assign height_valid=CAL_MASK[3] && CAL_MASK[4] && pose_ok && range_link && range_age<AGE_LIMIT && seen && age<AGE_LIMIT && !gyro_overrun;
 reg signed [63:0] rx=0,ry=0,rz=0;
 reg signed [63:0] yaw_q20=0;
 // ICM42688 configured +/-2000 dps, 16.4 counts/(deg/s).
 // rad Q20 = raw * ticks * (pi/180)*2^20/(16.4*50e6).
 // 18301/820000000 differs by <0.001%; accumulated at each accepted pose.
 wire signed [63:0] incx,incy,incz;
 // The exact same completed pose is used by gyro compensation and yaw.
 wire signed [63:0] updated_yaw_sum=yaw_q20+incz;
 wire signed [63:0] updated_yaw=updated_yaw_sum>3294199 ? updated_yaw_sum-6588398:
                              updated_yaw_sum< -3294199 ? updated_yaw_sum+6588398:updated_yaw_sum;
 wire gyro_done,gyro_busy,gyro_overrun;
 wire flow_fraction_cancel; // Declare before use for Gowin.
 position_gyro_increment gyro_math(.clk(clk),.rst_n(rst_n),.start(pose_update && pose_ok && pose_dt>0 && pose_dt<3000000),
 .cancel(origin_reset || !sources_ok || !sources_ok_q || flow_fraction_cancel),.gx(gx),.gy(gy),.gz(gz),.dt(pose_dt),
 .busy(gyro_busy),.done(gyro_done),.overrun(gyro_overrun),.ix(incx),.iy(incy),.iz(incz));
 wire signed [63:0] yaw_product;
 wire yaw_busy,yaw_done;
 // Low-rate display conversion shares a serial arithmetic unit, not a
 // full-width combinational constant multiplier on every clock.
 position_multiply yaw_math(.clk(clk),.rst_n(rst_n),.start(!yaw_busy),
 .cancel(origin_reset),.a(EXTERNAL_YAW ? $signed(yaw_reference_cdeg) : yaw_q20),.b(EXTERNAL_YAW ? 64'sd11993813 : 64'sd23468349),
 .busy(yaw_busy),.done(yaw_done),.result(yaw_product));
 reg signed [31:0] external_yaw_q20=0;
 reg signed [15:0] held_yaw_reference=0;
 initial yaw_cdeg=0;
 always @(posedge clk) begin
  if(!rst_n || origin_reset) begin yaw_cdeg<=0;external_yaw_q20<=0;held_yaw_reference<=0;end
  else begin
   if(!yaw_busy) held_yaw_reference<=yaw_reference_cdeg;
   if(yaw_done) begin
    if(EXTERNAL_YAW) begin external_yaw_q20<=trunc_shift(yaw_product,16);yaw_cdeg<=held_yaw_reference;end
    else yaw_cdeg<=trunc_shift(yaw_product,32);
   end
  end
 end
 reg [31:0] dt=0;
 reg [5:0] state=0;
 reg flow_pending=0;reg signed [15:0] held_dx=0,held_dy=0,held_roll=0,held_pitch=0;
 reg [7:0] held_quality=0;reg [31:0] held_dt=0;reg [15:0] held_range=0;
 reg signed [15:0] held_yaw=0;
 reg mul_start=0;reg signed [63:0] mul_a=0,mul_b=0,mul_temp=0;
 // Rejecting an optical interval also discards its sub-LSB gyro epoch.
 assign flow_fraction_cancel=flow_update && ((state!=0 || flow_pending) ||
  quality<MIN_QUALITY || flow_dt<50000 || flow_dt>AGE_LIMIT ||
  dx>2000 || dx< -2000 || dy>2000 || dy< -2000);
 wire math_cancel=origin_reset || !sources_ok_q || gyro_overrun || (flow_update && (state!=0 || flow_pending));
 wire mul_done,mul_busy;wire signed [63:0] mul_result;
 position_multiply flow_math(.clk(clk),.rst_n(rst_n),.start(mul_start),.cancel(math_cancel),
 .a(mul_a),.b(mul_b),.busy(mul_busy),.done(mul_done),.result(mul_result));
 reg div_start=0;reg signed [63:0] div_num=0;wire div_done,div_busy,div_error;wire signed [63:0] div_result;
 reg signed [63:0] nvx=0,nvy=0,nvz=0;
 position_divide divider(.clk(clk),.rst_n(rst_n),.start(div_start),.cancel(math_cancel),.numerator(div_num),.denominator(dt),.busy(div_busy),.done(div_done),.error(div_error),.quotient(div_result));
 reg trig_start=0;reg signed [31:0] trig_angle=0;
 wire trig_done,trig_busy;wire signed [17:0] sn,cs;
 position_sincos trig(.clk(clk),.rst_n(rst_n),.start(trig_start),.cancel(math_cancel),.angle_q20(trig_angle),.busy(trig_busy),.done(trig_done),.sin_q16(sn),.cos_q16(cs));
 reg signed [17:0] cr=65536,cp=65536,sy=0,cy=65536;
 reg signed [63:0] ax=0,ay=0,bx=0,by=0,lx=0,ly=0;
 wire signed [63:0] rotation_sum=$signed(mul_temp)+$signed(mul_result);
 reg signed [63:0] rotation_x=0,rotation_y=0,rotation_z=0;
 reg signed [63:0] optical_x=0,optical_y=0,compensate_x=0,compensate_y=0;
 reg [15:0] range_snapshot=0;
 reg signed [31:0] previous_height=0;
 reg signed [31:0] pitch_snapshot=0,yaw_snapshot=0;
 wire signed [63:0] next_x=$signed(x_q8)+lx;
 wire signed [63:0] next_y=$signed(y_q8)+ly;
 always @(posedge clk) begin
  update<=0;trig_start<=0;div_start<=0;mul_start<=0;
  if(!rst_n || origin_reset) begin
   x_q8<=0;y_q8<=0;vx<=0;vy<=0;height_mm<=0;previous_height<=0;vz<=0;
   
   
   
   
   rx<=0;ry<=0;rz<=0;yaw_q20<=0;seen<=0;continuity<=0;transaction_epoch_ok<=0;state<=0;age<=32'hffffffff;sample_sequence<=0;reason<=1;flow_pending<=0;
  end else begin
   if(age!=32'hffffffff) age<=age+1'b1;
   // Gaps, rejected callbacks and overruns end the fractional epoch.
   if(!sources_ok || flow_fraction_cancel || gyro_overrun) begin
    
    
    
   end
   if(gyro_done && !gyro_overrun) begin
    rx<=rx+incx;ry<=ry+incy;rz<=rz+incz;
    yaw_q20<=updated_yaw;
   end
   if(flow_update) begin
    flow_pending<=1;held_dx<=dx;held_dy<=dy;held_quality<=quality;held_dt<=flow_dt;
    held_range<=distance_cm;held_roll<=roll;held_pitch<=pitch;held_yaw<=yaw_reference_cdeg;
   end
   if(!sources_ok_q || gyro_overrun) begin
    state<=0;continuity<=0;seen<=0;transaction_epoch_ok<=0;rx<=0;ry<=0;rz<=0;vx<=0;vy<=0;vz<=0;flow_pending<=0;
    reason<=!pose_ok ? 16'd2 : !flow_link || flow_age>=AGE_LIMIT ? 16'd4 : 16'd8;
   end else if(flow_update && (state!=0 || flow_pending)) begin
    // Overrun invalidates the estimate; never silently join nonmatching intervals.
    state<=0;continuity<=0;seen<=0;transaction_epoch_ok<=0;reason<=16'd32;flow_pending<=0;
   end else case(state)
    0:if(flow_pending && !gyro_busy && !pose_update) begin
     flow_pending<=0;
     rx<=0;ry<=0;rz<=0;
     if(held_quality<MIN_QUALITY || held_dt<50000 || held_dt>AGE_LIMIT || held_dx>2000 || held_dx< -2000 || held_dy>2000 || held_dy< -2000) begin
      seen<=0;continuity<=0;reason<=16'd16;
     end else if(!continuity) begin continuity<=1;reason<=16'd64; end
     else begin
      // Include a simultaneous pose increment once, then clear interval sums.
      transaction_epoch_ok<=sources_ok && !origin_reset && !gyro_overrun;
      rotation_x<=rx+(gyro_done ? incx:0);rotation_y<=ry+(gyro_done ? incy:0);rotation_z<=rz+(gyro_done ? incz:0);
      dt<=held_dt;range_snapshot<=held_range;
      trig_angle<=trunc_shift($signed(held_roll)*64'sd11993813,16); // Launch only after serialized ROT completes.
      pitch_snapshot<=trunc_shift($signed(held_pitch)*64'sd11993813,16);yaw_snapshot<=gyro_done ? updated_yaw:yaw_q20;state<=20;
     end
    end
    20:begin
     optical_x<=$signed(held_dx)*FLOW_XX+$signed(held_dy)*FLOW_XY;
     optical_y<=$signed(held_dx)*FLOW_YX+$signed(held_dy)*FLOW_YY;
     // Reuse the idle serial multiplier. Preserve the original low64 product
     // and sum semantics, then arithmetic-shift the complete three-term sum.
     if(EXTERNAL_YAW) begin
      // Yaw, roll, pitch and range belong to the same optical callback.
      // The independently running display conversion is not a tuple source.
      mul_a<=$signed(held_yaw);mul_b<=64'sd11993813;mul_start<=1;state<=38;
     end else begin mul_a<=rotation_x;mul_b<=$signed(ROT_XX);mul_start<=1;state<=25;end
    end
    38:if(mul_done) begin
     yaw_snapshot<=trunc_shift(mul_result,16);
     mul_a<=rotation_x;mul_b<=$signed(ROT_XX);mul_start<=1;state<=25;
    end
    25:if(mul_done) begin mul_temp<=mul_result;mul_a<=rotation_y;mul_b<=$signed(ROT_XY);mul_start<=1;state<=26;end
    26:if(mul_done) begin mul_temp<=mul_temp+mul_result;mul_a<=rotation_z;mul_b<=$signed(ROT_XZ);mul_start<=1;state<=27;end
    27:if(mul_done) begin compensate_x<=rotation_sum>>>20;mul_a<=rotation_x;mul_b<=$signed(ROT_YX);mul_start<=1;state<=28;end
    28:if(mul_done) begin mul_temp<=mul_result;mul_a<=rotation_y;mul_b<=$signed(ROT_YY);mul_start<=1;state<=29;end
    29:if(mul_done) begin mul_temp<=mul_temp+mul_result;mul_a<=rotation_z;mul_b<=$signed(ROT_YZ);mul_start<=1;state<=30;end
    30:if(mul_done) begin compensate_y<=rotation_sum>>>20;state<=24;end
    // The roll angle snapshot remains unchanged during states20/25..30.
    // Starting CORDIC here prevents its one-cycle done pulse being lost.
    24:begin ax<=optical_x-compensate_x;ay<=optical_y-compensate_y;trig_start<=1;state<=1;end
    1:if(trig_done) begin cr<=cs;trig_angle<=pitch_snapshot;trig_start<=1;state<=2;end
    2:if(trig_done) begin cp<=cs;trig_angle<=yaw_snapshot;trig_start<=1;state<=3;end
    3:if(trig_done) begin sy<=sn;cy<=cs;state<=4;end
    4:begin mul_a<=$signed({1'b0,range_snapshot})*64'sd10;mul_b<=cr;mul_start<=1;state<=12;end
    12:if(mul_done) begin mul_a<=mul_result;mul_b<=cp;mul_start<=1;state<=13;end
    13:if(mul_done) begin height_mm<=mul_result>>>32;state<=5;end
    5:begin mul_a<=ax;mul_b<=height_mm;mul_start<=1;state<=14;end
    14:if(mul_done) begin bx<=mul_result>>>12;mul_a<=ay;mul_start<=1;state<=15;end
    15:if(mul_done) begin by<=mul_result>>>12;state<=6;end
    6:begin mul_a<=bx;mul_b<=cy;mul_start<=1;state<=16;end
    16:if(mul_done) begin mul_temp<=mul_result;mul_a<=by;mul_b<=sy;mul_start<=1;state<=17;end
    17:if(mul_done) begin lx<=(mul_temp-mul_result)>>>16;mul_a<=bx;mul_b<=sy;mul_start<=1;state<=18;end
    18:if(mul_done) begin mul_temp<=mul_result;mul_a<=by;mul_b<=cy;mul_start<=1;state<=19;end
    19:if(mul_done) begin ly<=(mul_temp+mul_result)>>>16;state<=7;end
    7:begin mul_a<=lx;mul_b<=50000000;mul_start<=1;state<=21;end
    21:if(mul_done) begin div_num<=mul_result;div_start<=1;state<=8;end
    8:if(div_done) begin nvx<=div_result/256;mul_a<=ly;mul_b<=50000000;mul_start<=1;state<=22;end
    22:if(mul_done) begin div_num<=mul_result;div_start<=1;state<=9;end
    9:if(div_done) begin nvy<=div_result/256;mul_a<=$signed(height_mm)-$signed(previous_height);mul_b<=50000000;mul_start<=1;state<=23;end
    23:if(mul_done) begin div_num<=mul_result;div_start<=1;state<=10;end
    10:if(div_done) begin nvz<=seen ? div_result:0;state<=11;end
    11:begin
     transaction_epoch_ok<=0;
     if(!sources_ok || origin_reset || gyro_overrun || !transaction_epoch_ok || quality<MIN_QUALITY || held_quality<MIN_QUALITY || held_dt<50000 || held_dt>AGE_LIMIT || held_dx>2000 || held_dx< -2000 || held_dy>2000 || held_dy< -2000)begin
      seen<=0;continuity<=0;reason<=16'd16;
     end else if(nvx>3000 || nvx< -3000 || nvy>3000 || nvy< -3000 || next_x>25600000 || next_x< -25600000 || next_y>25600000 || next_y< -25600000) begin
      seen<=0;continuity<=0;reason<=16'd128;
     end else begin
       if(calibrated) begin x_q8<=next_x;y_q8<=next_y;vx<=nvx;vy<=nvy;end
       else begin x_q8<=0;y_q8<=0;vx<=0;vy<=0;end
      vz<=nvz>3000 ? 3000 : nvz< -3000 ? -3000 : nvz;
      previous_height<=height_mm;seen<=1;age<=0;sample_sequence<=sample_sequence+1'b1;update<=1;reason<=calibrated ? 0:1;
     end
     state<=0;
    end
    default:state<=0;
   endcase
  end
 end
endmodule
