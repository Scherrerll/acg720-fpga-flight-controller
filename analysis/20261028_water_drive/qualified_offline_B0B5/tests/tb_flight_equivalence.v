`timescale 1ns/1ps
// Same input stream into the frozen B0B4 core and candidate. Sensor/committed
// control fixtures isolate the adapter, gate, state, publication and physical PWM.
module tb_flight_equivalence;
reg clk=0;always #10 clk=~clk;
reg [15:0] c1=1500,c2=1500,c3=1000,c4=1500,c5=1000,c6=1000,c7=1000;
reg valid=1,health=1,rate_test=0;reg update=0;integer beat=0,checks=0;
always @(negedge clk) begin beat=beat+1;update=beat%5==0;end
flight_core #(.ARM_LOW_TICKS(20),.ARM_HIGH_TICKS(20),.FLIGHT_STATE_TICKS_PER_MS(5),.CAL_SAMPLES(4)) dut(.clk50(clk),.imu_miso(1'b0),.rc_ppm_in(1'b0),
.hold_active(1'b0),.altitude_active(1'b1),.vertical_available(1'b1),.auto_takeoff(1'b0),
.pilot_norm_x(18'sd0),.pilot_norm_y(18'sd0),.pilot_norm_update(1'b0),.pilot_norm_valid(1'b1),.pilot_norm_dt_us(16'd10000),
.vertical_height_mm(32'sd1000),.hold_roll_cdeg(16'sd0),.hold_pitch_cdeg(16'sd0),.hold_throttle_delta_us(16'sd0),.hold_collective_us(16'd1300));
flight_core_reference #(.ARM_LOW_TICKS(20),.ARM_HIGH_TICKS(20),.FLIGHT_STATE_TICKS_PER_MS(5),.CAL_SAMPLES(4)) refcore(.clk50(clk),.imu_miso(1'b0),.rc_ppm_in(1'b0),
.hold_active(1'b0),.altitude_active(1'b1),.vertical_available(1'b1),.auto_takeoff(1'b0),
.pilot_norm_x(18'sd0),.pilot_norm_y(18'sd0),.pilot_norm_update(1'b0),.pilot_norm_valid(1'b1),.pilot_norm_dt_us(16'd10000),
.vertical_height_mm(32'sd1000),.hold_roll_cdeg(16'sd0),.hold_pitch_cdeg(16'sd0),.hold_throttle_delta_us(16'sd0),.hold_collective_us(16'd1300));
defparam dut.water_control.TIMER_DIVISOR=1;
defparam dut.water_control.FRESH_TICKS=100;
defparam dut.water_control.MODE_HOLD_TICKS=8;
defparam dut.water_control.LOW_HOLD_TICKS=20;
defparam dut.water_control.HIGH_HOLD_TICKS=20;
task cycles;input integer n;integer i;begin for(i=0;i<n;i=i+1)begin @(posedge clk);#3;end @(negedge clk);end endtask
reg compare=1;
always @(posedge clk) begin #2;
 if(dut.rst_n && refcore.rst_n && compare) begin
  checks=checks+1;
  if({dut.armed_raw,dut.armed_usable,dut.control_enabled,dut.command_fresh,dut.navigation_enabled,dut.flight_state_flags,dut.motor1_pwm,dut.motor2_pwm,dut.motor3_pwm,dut.motor4_pwm} !==
     {refcore.armed_raw,refcore.armed_usable,refcore.control_enabled,refcore.command_fresh,refcore.navigation_enabled,refcore.flight_state_flags,refcore.motor1_pwm,refcore.motor2_pwm,refcore.motor3_pwm,refcore.motor4_pwm})
      $fatal(1,"B0B4 flight adapter/PWM mismatch at check %0d",checks);
 end
 if(dut.rst_n && !dut.flight_permitted && dut.armed_raw)$fatal(1,"inhibited actual core armed");
 if(dut.water_enabled && (dut.armed_raw || dut.command_fresh || dut.flight_permitted))$fatal(1,"actual core mutual exclusion");
end
initial begin
 force dut.rc_valid=valid;
 force dut.channel_count=4'd8;
 force dut.rc_update=update;
 force dut.sensor_ok=health;
 force dut.yaw_fault=8'd0;
 force dut.controller_fault=8'd0;
 force dut.rate_fresh=rate_test;
 force dut.m1=16'd1300;
 force dut.m2=16'd1400;
 force dut.m3=16'd1500;
 force dut.m4=16'd1600;
 force dut.ch1=c1;
 force dut.ch2=c2;
 force dut.ch3=c3;
 force dut.ch4=c4;
 force dut.ch5=c5;
 force dut.ch6=c6;
 force dut.ch7=c7;
 force dut.ch8=16'd1500;
 force refcore.rc_valid=valid;
 force refcore.channel_count=4'd8;
 force refcore.rc_update=update;
 force refcore.sensor_ok=health;
 force refcore.yaw_fault=8'd0;
 force refcore.controller_fault=8'd0;
 force refcore.rate_fresh=rate_test;
 force refcore.m1=16'd1300;
 force refcore.m2=16'd1400;
 force refcore.m3=16'd1500;
 force refcore.m4=16'd1600;
 force refcore.ch1=c1;
 force refcore.ch2=c2;
 force refcore.ch3=c3;
 force refcore.ch4=c4;
 force refcore.ch5=c5;
 force refcore.ch6=c6;
 force refcore.ch7=c7;
 force refcore.ch8=16'd1500;
 cycles(270);
 cycles(30);c5=2000;cycles(100);if(!dut.armed_raw)$fatal(1,"fixture did not arm actual flight gate");
 cycles(125000); // one full real 400Hz frame including preparation
 c3=1600;rate_test=1;cycles(250000); // two complete PWM frames, four distinct widths
 rate_test=0;valid=0;cycles(15);if(dut.armed_raw)$fatal(1,"flight RC loss did not disarm");
 valid=1;cycles(35);if(dut.armed_raw)$fatal(1,"flight fault recovered with switch high");
 c3=1000;c5=1000;cycles(30);c5=2000;cycles(50);health=0;cycles(5);health=1;cycles(30);
 if(dut.armed_raw)$fatal(1,"flight health recovery rearmed");
 c5=1000;cycles(30);c5=2000;cycles(30);
 // In-air CH6 toggle is ignored by candidate, with actual flight gate armed.
 c6=2000;cycles(30);if(!dut.armed_raw || !dut.flight_permitted)$fatal(1,"in-air CH6 interrupted flight");
 c6=1000;cycles(5);c5=1000;cycles(20);
 compare=0;c6=2000;cycles(30);if(!dut.water_mode || dut.flight_permitted)$fatal(1,"water not integrated into core");
 cycles(30);c5=2000;cycles(30);if(!dut.water_enabled || dut.armed_raw)$fatal(1,"water failed or flight armed in water mode");
 c2=1800;cycles(250000);if(dut.command_fresh)$fatal(1,"flight command active in water mode");
 c6=1000;cycles(5);if(dut.water_enabled)$fatal(1,"mode request did not revoke water");
 c5=1000;c2=1500;cycles(30);if(dut.water_mode || !dut.flight_permitted)$fatal(1,"flight return failed");
 if(checks<375000)$fatal(1,"insufficient waveform comparisons");
 $display("PASS frozen B0B4 flight adapter equivalence: %0d clock comparisons, real 400Hz PWM, arming/preparation/health/RC recovery; actual core water exclusion",checks);$finish;
end
initial begin #30000000;$fatal(1,"miter timeout");end
endmodule
