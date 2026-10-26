`timescale 1ns/1ps
// Directed real-RTL witness, not a flight/plant replay. Every callback carries
// 11 ms of accepted IMU time. Callbacks are accelerated to 2500 FPGA clocks,
// retaining the source's eleven 1-ms stick steps and fixed 11-ms Z PID dt.
module tb;
 reg clk=0,rst_n=0,sample_update=0,height_update=0;
 reg [15:0] ch3=1684;
 wire mreq,mcancel,mbusy,mdone,merror,dreq,dcancel,dbusy,ddone,derror;
 wire signed[63:0] ma,mb,mresult,da,dresult; wire [31:0] db;
 wire [15:0] collective,reason; wire signed[31:0] target,climb;
 wire hactive,hready,auto_takeoff;
 mtf_xyz_hold_control #(.CAL_MASK(8'hff),.VELOCITY_FRAC_BITS(16)) dut(
  .clk(clk),.rst_n(rst_n),.origin_reset(1'b0),.rc_valid(1'b1),.channel_count(4'd8),
  .ch1(16'd1500),.ch2(16'd1500),.ch3(ch3),.ch4(16'd1500),.ch7(16'd2000),
  .xy_p_value(16'd1000),.xy_i_value(16'd350),.parameter_boundary(),
  .enabled(1'b1),.taking_off(1'b1),.position_valid(1'b1),.height_valid(1'b1),
  .position_update(1'b0),.height_update(height_update),.sample_update(sample_update),.sample_dt_us(32'd11000),
  .position_age(32'd0),.position_dt_us(32'd20000),.x_q8(32'sd0),.y_q8(32'sd0),
  .vx(32'sd0),.vy(32'sd0),.height_mm(32'sd300),.vz(32'sd0),.yaw_cdeg(16'sd0),
  .acc_valid(1'b1),.ax_mmps2(32'sd0),.ay_mmps2(32'sd0),.az_mmps2(32'sd0),.collective_us(16'd1500),
  .requested(),.ready(),.active(),.height_requested(),.height_ready(hready),.height_active(hactive),
  .auto_takeoff(auto_takeoff),.reason(),.height_reason(reason),.collective_target_us(collective),
  .roll_target(),.pitch_target(),.throttle_delta(),.requested_climb_mmps(climb),.target_height_mm(target),
  .pilot_norm_x(),.pilot_norm_y(),.pilot_norm_update(),.pilot_norm_valid(),.pilot_norm_dt_us(),
  .math_mul_start(mreq),.math_mul_cancel(mcancel),.math_mul_a(ma),.math_mul_b(mb),
  .math_mul_busy(mbusy),.math_mul_done(mdone),.math_mul_result(mresult),
  .math_div_start(dreq),.math_div_cancel(dcancel),.math_div_numerator(da),.math_div_denominator(db),
  .math_div_busy(dbusy),.math_div_done(ddone),.math_div_error(derror),.math_div_result(dresult));
 nav_math_service #(.CLIENTS(1),.DIVIDE(0)) mul(.clk(clk),.rst_n(rst_n),.request(mreq),.cancel(mcancel),
  .operand_a(ma),.operand_b(mb),.busy(mbusy),.done(mdone),.error(merror),.result(mresult),.grant());
 nav_math_service #(.CLIENTS(1),.DIVIDE(1)) div(.clk(clk),.rst_n(rst_n),.request(dreq),.cancel(dcancel),
  .operand_a(da),.operand_b({32'd0,db}),.busy(dbusy),.done(ddone),.error(derror),.result(dresult),.grant());
 always #10 clk=~clk;
 integer cycles=0,callbacks=0,pubs=0,low_start=-1,low_high=0,low_total=0;
 integer first_below_ceiling=-1,first_below_landing=-1,first_negative_target=-1,fd;
 integer elapsed;
 always @(negedge clk) begin
  sample_update=0;height_update=0;
  if(rst_n)begin
   cycles=cycles+1;
   if(cycles%2500==0)begin
    callbacks=callbacks+1;
    if(callbacks==1819)begin ch3=1002;low_start=callbacks*11;end
    sample_update=1;height_update=1;
   end
  end
 end
 always @(posedge clk)begin #1;
  if(rst_n)begin
   if(dut.blocked || dut.xy_blocked || dut.z_stick_fault || derror)$fatal(1,"unexpected controller/math fault");
   if(dut.height_command_seen && dut.height_command_age==0)begin
    pubs=pubs+1;
    $fdisplay(fd,"%0d,%0d,300,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d",callbacks*11,ch3,target,climb,collective,dut.iz,dut.bias,dut.exz,dut.vsz,auto_takeoff);
    if(low_start>=0)begin
     elapsed=callbacks*11-low_start;
     if(elapsed<=4600)begin
      low_total=low_total+1;
      if(collective==1850)low_high=low_high+1;
      if(collective!=1850)$fatal(1,"witness failed: low-stick high-clamp not sustained at %0dms: %0d",elapsed,collective);
     end
     if(target<0 && first_negative_target<0)first_negative_target=elapsed;
     if(collective<1850 && first_below_ceiling<0)first_below_ceiling=elapsed;
     if(collective<1250 && first_below_landing<0)first_below_landing=elapsed;
     if(elapsed>=15000)begin
      if(climb!=-2500 || target>=0 || first_below_ceiling<=4600 || first_below_landing<0 || low_total<400)
       $fatal(1,"witness coverage failed climb=%0d target=%0d ceil=%0d land=%0d n=%0d",climb,target,first_below_ceiling,first_below_landing,low_total);
      $display("PASS reachable real Z RTL: low-stick high-clamp callbacks=%0d/%0d over first 4600ms; negative_target_ms=%0d below1850_ms=%0d below1250_ms=%0d; no forced state or arithmetic fault",low_high,low_total,first_negative_target,first_below_ceiling,first_below_landing);
      $fclose(fd);$finish;
     end
    end
   end
  end
 end
 initial begin
  fd=$fopen("z_trace.csv","w");
  $fdisplay(fd,"logical_ms,ch3,height_mm,target_mm,requested_climb_mmps,collective_us,iz_q16,bias_q16,exz_q16,vsz_q16,auto_takeoff");
  repeat(8)@(negedge clk);rst_n=1;
 end
 initial begin #250000000;$fatal(1,"witness timeout");end
endmodule
