module candidate_side(input wire clk,rst_n,enabled,rc_valid,height_valid,origin,taking_off,
input wire sample_update,height_update,position_update,input wire[15:0]ch3,pval,ival,
input wire signed[31:0]height_mm,vz,vx,vy,output wire[15:0]collective,
output wire signed[31:0]target,climb,output wire signed[15:0]roll,pitch,output wire hactive);
wire mreq,mcancel,mbusy,mdone,merror,dreq,dcancel,dbusy,ddone,derror;
wire signed[63:0]ma,mb,mresult,da,dresult;wire[31:0]db;
mtf_xyz_hold_control #(.CAL_MASK(8'hff),.VELOCITY_FRAC_BITS(16)) dut(
 .clk(clk),.rst_n(rst_n),.origin_reset(origin),.rc_valid(rc_valid),.channel_count(4'd8),
 .ch1(16'd1500),.ch2(16'd1500),.ch3(ch3),.ch4(16'd1500),.ch7(16'd2000),
 .xy_p_value(pval),.xy_i_value(ival),.parameter_boundary(),.enabled(enabled),.taking_off(taking_off),
 .position_valid(height_valid),.height_valid(height_valid),.position_update(position_update),.height_update(height_update),
 .sample_update(sample_update),.sample_dt_us(32'd11000),.position_age(32'd0),.position_dt_us(32'd22000),
 .x_q8(32'sd0),.y_q8(32'sd0),.vx(vx),.vy(vy),.height_mm(height_mm),.vz(vz),.yaw_cdeg(16'sd0),
 .acc_valid(height_valid),.ax_mmps2(32'sd0),.ay_mmps2(32'sd0),.az_mmps2(32'sd0),.collective_us(16'd1500),
 .requested(),.ready(),.active(),.height_requested(),.height_ready(),.height_active(hactive),.auto_takeoff(),
 .reason(),.height_reason(),.collective_target_us(collective),.roll_target(roll),.pitch_target(pitch),
 .throttle_delta(),.requested_climb_mmps(climb),.target_height_mm(target),
 .pilot_norm_x(),.pilot_norm_y(),.pilot_norm_update(),.pilot_norm_valid(),.pilot_norm_dt_us(),
 .math_mul_start(mreq),.math_mul_cancel(mcancel),.math_mul_a(ma),.math_mul_b(mb),
 .math_mul_busy(mbusy),.math_mul_done(mdone),.math_mul_result(mresult),
 .math_div_start(dreq),.math_div_cancel(dcancel),.math_div_numerator(da),.math_div_denominator(db),
 .math_div_busy(dbusy),.math_div_done(ddone),.math_div_error(derror),.math_div_result(dresult));
nav_math_service #(.CLIENTS(1),.DIVIDE(0)) mul(.clk(clk),.rst_n(rst_n),.request(mreq),.cancel(mcancel),
 .operand_a(ma),.operand_b(mb),.busy(mbusy),.done(mdone),.error(merror),.result(mresult),.grant());
nav_math_service #(.CLIENTS(1),.DIVIDE(1)) div(.clk(clk),.rst_n(rst_n),.request(dreq),.cancel(dcancel),
 .operand_a(da),.operand_b({32'd0,db}),.busy(dbusy),.done(ddone),.error(derror),.result(dresult),.grant());
endmodule
module base_side(input wire clk,rst_n,enabled,rc_valid,height_valid,origin,taking_off,
input wire sample_update,height_update,position_update,input wire[15:0]ch3,pval,ival,
input wire signed[31:0]height_mm,vz,vx,vy,output wire[15:0]collective,
output wire signed[31:0]target,climb,output wire signed[15:0]roll,pitch,output wire hactive);
wire mreq,mcancel,mbusy,mdone,merror,dreq,dcancel,dbusy,ddone,derror;
wire signed[63:0]ma,mb,mresult,da,dresult;wire[31:0]db;
mtf_xyz_hold_control_b3 #(.CAL_MASK(8'hff),.VELOCITY_FRAC_BITS(16)) dut(
 .clk(clk),.rst_n(rst_n),.origin_reset(origin),.rc_valid(rc_valid),.channel_count(4'd8),
 .ch1(16'd1500),.ch2(16'd1500),.ch3(ch3),.ch4(16'd1500),.ch7(16'd2000),
 .xy_p_value(pval),.xy_i_value(ival),.parameter_boundary(),.enabled(enabled),.taking_off(taking_off),
 .position_valid(height_valid),.height_valid(height_valid),.position_update(position_update),.height_update(height_update),
 .sample_update(sample_update),.sample_dt_us(32'd11000),.position_age(32'd0),.position_dt_us(32'd22000),
 .x_q8(32'sd0),.y_q8(32'sd0),.vx(vx),.vy(vy),.height_mm(height_mm),.vz(vz),.yaw_cdeg(16'sd0),
 .acc_valid(height_valid),.ax_mmps2(32'sd0),.ay_mmps2(32'sd0),.az_mmps2(32'sd0),.collective_us(16'd1500),
 .requested(),.ready(),.active(),.height_requested(),.height_ready(),.height_active(hactive),.auto_takeoff(),
 .reason(),.height_reason(),.collective_target_us(collective),.roll_target(roll),.pitch_target(pitch),
 .throttle_delta(),.requested_climb_mmps(climb),.target_height_mm(target),
 .pilot_norm_x(),.pilot_norm_y(),.pilot_norm_update(),.pilot_norm_valid(),.pilot_norm_dt_us(),
 .math_mul_start(mreq),.math_mul_cancel(mcancel),.math_mul_a(ma),.math_mul_b(mb),
 .math_mul_busy(mbusy),.math_mul_done(mdone),.math_mul_result(mresult),
 .math_div_start(dreq),.math_div_cancel(dcancel),.math_div_numerator(da),.math_div_denominator(db),
 .math_div_busy(dbusy),.math_div_done(ddone),.math_div_error(derror),.math_div_result(dresult));
nav_math_service #(.CLIENTS(1),.DIVIDE(0)) mul(.clk(clk),.rst_n(rst_n),.request(mreq),.cancel(mcancel),
 .operand_a(ma),.operand_b(mb),.busy(mbusy),.done(mdone),.error(merror),.result(mresult),.grant());
nav_math_service #(.CLIENTS(1),.DIVIDE(1)) div(.clk(clk),.rst_n(rst_n),.request(dreq),.cancel(dcancel),
 .operand_a(da),.operand_b({32'd0,db}),.busy(dbusy),.done(ddone),.error(derror),.result(dresult),.grant());
endmodule
