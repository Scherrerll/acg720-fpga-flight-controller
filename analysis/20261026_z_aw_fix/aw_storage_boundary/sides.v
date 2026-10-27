module old_side #(parameter F=0)(input clk,rst_n,su,hu,pu,
input [15:0] ch1,ch2,ch3,pval,ival,input signed[31:0] h,vx,vy,vz,ax,ay,az,input signed[15:0] yaw,
output wire[221:0] observed);
wire req,ready,active,hr,hready,ha,auto_to,nu,nv,pb;
wire[15:0] reason,hreason,collective,ndt;wire signed[15:0] roll,pitch,delta;
wire signed[31:0] climb,target;wire signed[17:0]nx,ny;
wire mreq,mc,mbusy,mdone,me,dreq,dc,dbusy,ddone,derror;
wire signed[63:0]ma,mb,mresult,da,dresult;wire[31:0]db;wire mg;
assign observed={pb,req,ready,active,hr,hready,ha,auto_to,reason,hreason,collective,roll,pitch,delta,climb,target,nx,ny,nu,nv,ndt};
mtf_xyz_hold_control_v5 #(.CAL_MASK(8'hff),.VELOCITY_FRAC_BITS(F),.POSITION_KP_Q16(98304)) dut(.clk(clk),.rst_n(rst_n),.origin_reset(1'b0),.rc_valid(1'b1),.channel_count(4'd8),
 .ch1(ch1),.ch2(ch2),.ch3(ch3),.ch4(16'd1500),.ch7(16'd2000),.xy_p_value(pval),.xy_i_value(ival),
 .parameter_boundary(pb),.enabled(1'b1),.taking_off(1'b1),.position_valid(1'b1),.height_valid(1'b1),
 .position_update(pu),.height_update(hu),.sample_update(su),.sample_dt_us(32'd11000),
 .position_age(32'd0),.position_dt_us(32'd100000),.x_q8(32'sd0),.y_q8(32'sd0),
 .vx(vx),.vy(vy),.height_mm(h),.vz(vz),.yaw_cdeg(yaw),.acc_valid(1'b1),
 .ax_mmps2(ax),.ay_mmps2(ay),.az_mmps2(az),.collective_us(16'd1500),
 .requested(req),.ready(ready),.active(active),.height_requested(hr),.height_ready(hready),
 .height_active(ha),.auto_takeoff(auto_to),.reason(reason),.height_reason(hreason),
 .collective_target_us(collective),.roll_target(roll),.pitch_target(pitch),.throttle_delta(delta),
 .requested_climb_mmps(climb),.target_height_mm(target),.pilot_norm_x(nx),.pilot_norm_y(ny),
 .pilot_norm_update(nu),.pilot_norm_valid(nv),.pilot_norm_dt_us(ndt),
 .math_mul_start(mreq),.math_mul_cancel(mc),.math_mul_a(ma),.math_mul_b(mb),
 .math_mul_busy(mbusy),.math_mul_done(mdone),.math_mul_result(mresult),
 .math_div_start(dreq),.math_div_cancel(dc),.math_div_numerator(da),.math_div_denominator(db),
 .math_div_busy(dbusy),.math_div_done(ddone),.math_div_error(derror),.math_div_result(dresult));
nav_math_service #(.CLIENTS(1),.DIVIDE(0)) mul(.clk(clk),.rst_n(rst_n),.request(mreq),.cancel(mc),
 .operand_a(ma),.operand_b(mb),.busy(mbusy),.done(mdone),.error(me),.result(mresult),.grant(mg));
nav_math_service #(.CLIENTS(1),.DIVIDE(1)) div(.clk(clk),.rst_n(rst_n),.request(dreq),.cancel(dc),
 .operand_a(da),.operand_b({32'd0,db}),.busy(dbusy),.done(ddone),.error(derror),.result(dresult),.grant());
endmodule
module new_side #(parameter F=0)(input clk,rst_n,su,hu,pu,
input [15:0] ch1,ch2,ch3,pval,ival,input signed[31:0] h,vx,vy,vz,ax,ay,az,input signed[15:0] yaw,
output wire[221:0] observed);
wire req,ready,active,hr,hready,ha,auto_to,nu,nv,pb;
wire[15:0] reason,hreason,collective,ndt;wire signed[15:0] roll,pitch,delta;
wire signed[31:0] climb,target;wire signed[17:0]nx,ny;
wire mreq,mc,mbusy,mdone,me,dreq,dc,dbusy,ddone,derror;
wire signed[63:0]ma,mb,mresult,da,dresult;wire[31:0]db;wire mg;
assign observed={pb,req,ready,active,hr,hready,ha,auto_to,reason,hreason,collective,roll,pitch,delta,climb,target,nx,ny,nu,nv,ndt};
mtf_xyz_hold_control #(.CAL_MASK(8'hff),.VELOCITY_FRAC_BITS(F),.POSITION_KP_Q16(98304)) dut(.clk(clk),.rst_n(rst_n),.origin_reset(1'b0),.rc_valid(1'b1),.channel_count(4'd8),
 .ch1(ch1),.ch2(ch2),.ch3(ch3),.ch4(16'd1500),.ch7(16'd2000),.xy_p_value(pval),.xy_i_value(ival),
 .parameter_boundary(pb),.enabled(1'b1),.taking_off(1'b1),.position_valid(1'b1),.height_valid(1'b1),
 .position_update(pu),.height_update(hu),.sample_update(su),.sample_dt_us(32'd11000),
 .position_age(32'd0),.position_dt_us(32'd100000),.x_q8(32'sd0),.y_q8(32'sd0),
 .vx(vx),.vy(vy),.height_mm(h),.vz(vz),.yaw_cdeg(yaw),.acc_valid(1'b1),
 .ax_mmps2(ax),.ay_mmps2(ay),.az_mmps2(az),.collective_us(16'd1500),
 .requested(req),.ready(ready),.active(active),.height_requested(hr),.height_ready(hready),
 .height_active(ha),.auto_takeoff(auto_to),.reason(reason),.height_reason(hreason),
 .collective_target_us(collective),.roll_target(roll),.pitch_target(pitch),.throttle_delta(delta),
 .requested_climb_mmps(climb),.target_height_mm(target),.pilot_norm_x(nx),.pilot_norm_y(ny),
 .pilot_norm_update(nu),.pilot_norm_valid(nv),.pilot_norm_dt_us(ndt),
 .math_mul_start(mreq),.math_mul_cancel(mc),.math_mul_a(ma),.math_mul_b(mb),
 .math_mul_busy(mbusy),.math_mul_done(mdone),.math_mul_result(mresult),
 .math_div_start(dreq),.math_div_cancel(dc),.math_div_numerator(da),.math_div_denominator(db),
 .math_div_busy(dbusy),.math_div_done(ddone),.math_div_error(derror),.math_div_result(dresult));
nav_math_service #(.CLIENTS(1),.DIVIDE(0)) mul(.clk(clk),.rst_n(rst_n),.request(mreq),.cancel(mc),
 .operand_a(ma),.operand_b(mb),.busy(mbusy),.done(mdone),.error(me),.result(mresult),.grant(mg));
nav_math_service #(.CLIENTS(1),.DIVIDE(1)) div(.clk(clk),.rst_n(rst_n),.request(dreq),.cancel(dc),
 .operand_a(da),.operand_b({32'd0,db}),.busy(dbusy),.done(ddone),.error(derror),.result(dresult),.grant());
endmodule
