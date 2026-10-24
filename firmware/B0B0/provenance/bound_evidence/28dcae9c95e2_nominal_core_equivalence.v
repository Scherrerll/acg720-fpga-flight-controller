`timescale 1ns/1ps
module tb;
reg clk=0;always #10 clk=~clk;
reg xy=0;reg signed[17:0]nx=0,ny=0;
wire ta,tb,ea,eb,fa,fb,aa,ab;
wire[863:0]da,db;
flight_core #(.ARM_LOW_TICKS(8),.ARM_HIGH_TICKS(8),.FLIGHT_STATE_TICKS_PER_MS(100)) a(
 .clk50(clk),.imu_miso(1'b0),.rc_ppm_in(1'b0),.hold_active(xy),.altitude_active(ta),
 .vertical_available(1'b1),.vertical_height_mm(32'sd234),.auto_takeoff(1'b0),
 .pilot_norm_x(nx),.pilot_norm_y(ny),.pilot_norm_valid(1'b1),.pilot_norm_update(a.pose_update),.pilot_norm_dt_us(16'd2000),
 .taking_off_out(ta),.hold_roll_cdeg(16'sd100),.hold_pitch_cdeg(-16'sd80),
 .hold_throttle_delta_us(16'sd0),.hold_collective_us(16'd1400),
 .control_enabled(ea),.command_fresh(fa),.armed_usable(aa),.telemetry_body(da));
flight_core_b0ae #(.ARM_LOW_TICKS(8),.ARM_HIGH_TICKS(8),.FLIGHT_STATE_TICKS_PER_MS(100)) b(
 .clk50(clk),.imu_miso(1'b0),.rc_ppm_in(1'b0),.hold_active(xy),.altitude_active(tb),
 .vertical_available(1'b1),.vertical_height_mm(32'sd234),.auto_takeoff(1'b0),
 .pilot_norm_x(nx),.pilot_norm_y(ny),.pilot_norm_valid(1'b1),.pilot_norm_update(b.pose_update),.pilot_norm_dt_us(16'd2000),
 .taking_off_out(tb),.hold_roll_cdeg(16'sd100),.hold_pitch_cdeg(-16'sd80),
 .hold_throttle_delta_us(16'sd0),.hold_collective_us(16'd1400),
 .control_enabled(eb),.command_fresh(fb),.armed_usable(ab),.telemetry_body(db));
integer checks=0;
always @(negedge clk)if(a.rst_n && b.rst_n)begin
 checks=checks+1;
 if({ta,ea,fa,aa,da}!=={tb,eb,fb,ab,db})$fatal(1,"Nominal core observable difference at clock %0d",checks);
 if(a.height_fallback_active)$fatal(1,"Fallback entered with valid height");
 if({a.motor1_pwm,a.motor2_pwm,a.motor3_pwm,a.motor4_pwm}!=={b.motor1_pwm,b.motor2_pwm,b.motor3_pwm,b.motor4_pwm})$fatal(1,"Physical PWM difference");
end
task ticks;input integer n;begin repeat(n)@(posedge clk);#1;end endtask
task channels;input integer throttle,switch;begin
 a.receiver.env_ch3=throttle;b.receiver.env_ch3=throttle;
 a.receiver.env_ch5=switch;b.receiver.env_ch5=switch;
end endtask
initial begin
 wait(a.rst_n && b.rst_n);ticks(30);channels(1000,2000);ticks(30);
 wait(a.motor_prepared);channels(1600,2000);wait(fa && fb);ticks(150000);
 channels(1500,2000);nx=18000;ny=-12000;ticks(1100000);
 xy=1;ticks(500000);xy=0;nx=-16000;ny=9000;ticks(1100000);
 channels(1000,2000);ticks(200000);channels(1000,1000);ticks(200);
 channels(1000,2000);ticks(100);channels(1000,1000);ticks(30);
 $display("PASS nominal core equivalence: %0d clocks, core telemetry and four actual PWM signals",checks);$finish;
end
initial begin #200000000;$fatal(1,"Nominal comparison timeout");end
endmodule
