`include "calibration.vh"
// Bench default: 50Hz1000..1150us, uncalibrated point hold is unavailable.
// This image is NOT a flight release. See validation and calibration records.
module acg720_flight_monitor_bench(
 input wire clk50,imu_miso,rc_ppm_in,flow_miso,range_rx,
 output wire imu_sck,imu_mosi,imu_cs_n,flow_sck,flow_mosi,flow_cs_n,flow_pwr_en,
 output wire range_tx,uart_tx,led2,led3,
 output wire motor1_pwm,motor2_pwm,motor3_pwm,motor4_pwm
);
 localparam [7:0] CAL_MASK=`FLIGHT_CAL_MASK;
 reg [7:0] boot=0;always @(posedge clk50) if(boot!=255) boot<=boot+1'b1;
 wire rst_n=boot==255;
 assign range_tx=1'b1;
 wire rc_valid;wire [3:0] channels;wire [15:0] ch1,ch2,ch3,ch4,ch5,ch6,ch7,ch8;
 wire pose_update,pose_valid,armed,enabled,fresh;wire [31:0] pose_dt,pose_age;
 wire signed [15:0] roll,pitch;wire signed [16:0] gx,gy,gz;
 wire [863:0] core_body;
 wire requested,hold_ready,hold_active;wire [15:0] hold_reason;
 wire signed [15:0] hold_roll,hold_pitch,hold_throttle;
 flight_core core(.clk50(clk50),.imu_miso(imu_miso),.rc_ppm_in(rc_ppm_in),
  .hold_active(hold_active),.hold_roll_cdeg(hold_roll),.hold_pitch_cdeg(hold_pitch),.hold_throttle_delta_us(hold_throttle),
  .imu_sck(imu_sck),.imu_mosi(imu_mosi),.imu_cs_n(imu_cs_n),.led2(led2),.led3(led3),
  .motor1_pwm(motor1_pwm),.motor2_pwm(motor2_pwm),.motor3_pwm(motor3_pwm),.motor4_pwm(motor4_pwm),
  .rc_valid(rc_valid),.channel_count(channels),.ch1(ch1),.ch2(ch2),.ch3(ch3),.ch4(ch4),.ch5(ch5),.ch6(ch6),.ch7(ch7),.ch8(ch8),
  .pose_update(pose_update),.pose_valid(pose_valid),.pose_dt_ticks(pose_dt),.pose_age_ticks(pose_age),
  .body_roll_cdeg(roll),.body_pitch_cdeg(pitch),.body_gx(gx),.body_gy(gy),.body_gz(gz),
  .armed_usable(armed),.control_enabled(enabled),.command_fresh(fresh),.telemetry_body(core_body));
 wire signed [15:0] dx,dy;wire [7:0] quality,motion,flow_who;
 wire flow_configured,flow_link,flow_update;wire [31:0] flow_seq,flow_good,flow_age,flow_dt,flow_errors;
 flow_reader flow(.clk50(clk50),.rst_n(rst_n),.flow_miso(flow_miso),
  .flow_sck(flow_sck),.flow_mosi(flow_mosi),.flow_cs_n(flow_cs_n),.flow_pwr_en(flow_pwr_en),
  .flow_dx(dx),.flow_dy(dy),.squal(quality),.flow_motion(motion),.who(flow_who),
  .configured(flow_configured),.link_ok(flow_link),.sample_valid(flow_update),.sample_sequence(flow_seq),
  .good_count(flow_good),.source_age_ticks(flow_age),.source_dt_ticks(flow_dt),.error_count(flow_errors));
 wire [15:0] distance_cm,strength,temp_raw;wire range_update,range_link;
 wire [31:0] range_age,range_errors,range_seq,range_good;
 range_reader range_sensor(.clk50(clk50),.rst_n(rst_n),.range_rx(range_rx),.distance_cm(distance_cm),
  .strength(strength),.temp_raw(temp_raw),.sample_valid(range_update),.link_ok(range_link),
  .source_age_ticks(range_age),.error_count(range_errors),.sample_sequence(range_seq),.good_count(range_good));
 reg signed [31:0] total_x=0,total_y=0;
 wire signed [32:0] sum_x=$signed(total_x)+$signed(dx),sum_y=$signed(total_y)+$signed(dy);
 always @(posedge clk50) if(!rst_n) begin total_x<=0;total_y<=0;end
 else if(flow_update) begin
  total_x<=sum_x>2147483647 ? 32'sh7fffffff : sum_x< -33'sd2147483648 ? 32'sh80000000 : sum_x[31:0];
  total_y<=sum_y>2147483647 ? 32'sh7fffffff : sum_y< -33'sd2147483648 ? 32'sh80000000 : sum_y[31:0];
 end
 wire calibrated,position_valid,height_valid,position_update;
 wire [15:0] observer_reason;wire signed [31:0] x_q8,y_q8,vx,vy,height_mm,vz;
 wire signed [15:0] relative_yaw;wire [31:0] position_seq,position_age;
 generate if(CAL_MASK!=0) begin: calibrated_observer
 relative_position #(.CAL_MASK(CAL_MASK),.FLOW_XX(`FLOW_XX_Q20),.FLOW_XY(`FLOW_XY_Q20),.FLOW_YX(`FLOW_YX_Q20),.FLOW_YY(`FLOW_YY_Q20),.ROT_XX(`ROT_XX_Q20),.ROT_XY(`ROT_XY_Q20),.ROT_XZ(`ROT_XZ_Q20),.ROT_YX(`ROT_YX_Q20),.ROT_YY(`ROT_YY_Q20),.ROT_YZ(`ROT_YZ_Q20)) observer(.clk(clk50),.rst_n(rst_n),.origin_reset(1'b0),
  .pose_update(pose_update),.pose_valid(pose_valid),.pose_dt(pose_dt),.pose_age(pose_age),.roll(roll),.pitch(pitch),.gx(gx),.gy(gy),.gz(gz),
  .flow_update(flow_update),.flow_link(flow_link),.dx(dx),.dy(dy),.quality(quality),.flow_dt(flow_dt),.flow_age(flow_age),
  .range_link(range_link),.distance_cm(distance_cm),.range_age(range_age),.calibrated(calibrated),.position_valid(position_valid),
  .height_valid(height_valid),.update(position_update),.reason(observer_reason),.x_q8(x_q8),.y_q8(y_q8),.vx(vx),.vy(vy),
  .height_mm(height_mm),.vz(vz),.yaw_cdeg(relative_yaw),.sample_sequence(position_seq),.age(position_age));
 end else begin: uncalibrated_observer

 // Until physical optical calibration is supplied, only range-derived height
 // is computed. No synthetic XY or yaw is presented as a measurement.
 reg signed [31:0] tilt_squared=0;reg [42:0] tilt_scaled=0;reg [31:0] factor_q16=65536;
 reg [47:0] height_product=0;reg signed [31:0] h=0;
 always @(posedge clk50) begin
  tilt_squared<=$signed(roll)*$signed(roll)+$signed(pitch)*$signed(pitch);
  tilt_scaled<=(tilt_squared<4500000 ? tilt_squared : 32'd4500000)*11'd1049;
  factor_q16<=65536-(tilt_scaled>>20);
  height_product<=distance_cm*32'd10*factor_q16;
  h<=height_product>>16;
 end
 assign calibrated=0;assign position_valid=0;assign position_update=0;
 assign height_valid=CAL_MASK[4] && range_link && range_age<5000000 && pose_valid && pose_age<3000000 && roll>=-1500 && roll<=1500 && pitch>=-1500 && pitch<=1500;
 assign x_q8=0;assign y_q8=0;assign vx=0;assign vy=0;assign height_mm=h;assign vz=0;
 assign relative_yaw=0;assign position_seq=0;assign position_age=32'hffffffff;assign observer_reason=1;
 end endgenerate
 hold_control #(.CAL_MASK(CAL_MASK)) position_controller(.clk(clk50),.rst_n(rst_n),.rc_valid(rc_valid),.channel_count(channels),
  .ch1(ch1),.ch2(ch2),.ch4(ch4),.ch7(ch7),.enabled(enabled),.position_valid(position_valid),.height_valid(height_valid),
  .position_update(position_update),.position_age(position_age),.x_q8(x_q8),.y_q8(y_q8),.vx(vx),.vy(vy),.height_mm(height_mm),.vz(vz),
  .yaw_cdeg(relative_yaw),.requested(requested),.ready(hold_ready),.active(hold_active),.reason(hold_reason),
  .roll_target(hold_roll),.pitch_target(hold_pitch),.throttle_delta(hold_throttle));
 wire [7:0] system_flags={calibrated,height_valid,hold_active,hold_ready,position_valid,range_link,flow_link,flow_configured};
 wire [887:0] extension={ch6,ch7,ch8,{7'd0,requested},{7'd0,hold_active},hold_reason,system_flags,CAL_MASK,
  dx,dy,quality,motion,flow_who,flow_seq,flow_age,flow_dt,flow_errors,flow_good,total_x,total_y,
  distance_cm,strength,temp_raw,range_seq,range_age,range_errors,range_good,
  x_q8,y_q8,vx,vy,height_mm,vz,relative_yaw,observer_reason,hold_reason,position_seq,position_age,16'd1110,16'd1150};
 // Capture both buses together before the packet engine's enabled registers.
 // This preserves one common snapshot while removing its mux from status paths.
 wire [863:0] core_snapshot;wire [887:0] extension_snapshot;
 generate if(CAL_MASK!=0) begin: staged_telemetry
 reg [863:0] core_q=0;reg [887:0] extension_q=0;
 always @(posedge clk50) begin core_q<=core_body;extension_q<=extension;end
 assign core_snapshot=core_q;assign extension_snapshot=extension_q;
 end else begin: direct_telemetry
 assign core_snapshot=core_body;assign extension_snapshot=extension;
 end endgenerate
 telemetry_tx telemetry(.clk(clk50),.core_body(core_snapshot),.extension(extension_snapshot),.tx(uart_tx));
endmodule
