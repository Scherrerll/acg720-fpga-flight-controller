`timescale 1ns/1ps
module tb;
reg clk=0;always #10 clk=~clk;
reg xy=0,vertical_ok=1;
wire taking_off,enabled,fresh,armed,pickup;wire[3:0]state;
flight_core #(.ARM_LOW_TICKS(8),.ARM_HIGH_TICKS(8),.FLIGHT_STATE_TICKS_PER_MS(100)) dut(
 .clk50(clk),.imu_miso(1'b0),.rc_ppm_in(1'b0),.hold_active(xy),.altitude_active(taking_off),
 .vertical_available(vertical_ok),.vertical_height_mm(32'sd234),.auto_takeoff(1'b0),
 .pilot_norm_x(18'sd0),.pilot_norm_y(18'sd0),.pilot_norm_valid(1'b1),.pilot_norm_update(dut.pose_update),.pilot_norm_dt_us(16'd2000),
 .taking_off_out(taking_off),.flight_state_flags(state),.hold_roll_cdeg(16'sd0),.hold_pitch_cdeg(16'sd0),
 .hold_throttle_delta_us(16'sd0),.hold_collective_us(16'd1400),.control_enabled(enabled),.command_fresh(fresh),
 .armed_usable(armed),.throttle_takeover_active(pickup));
task ticks;input integer n;begin repeat(n)@(negedge clk);end endtask
task settle;begin wait(fresh && dut.published_m1==1400 && dut.published_m4==1400);ticks(100);end endtask
initial begin
 wait(dut.rst_n);ticks(30);dut.receiver.env_ch5=2000;ticks(30);
 if(!armed)$fatal(1,"arm adapter");
 wait(dut.preparation_mask==2);ticks(1);
 if(dut.published_m2!=1200 || dut.published_m1!=1000 || enabled)$fatal(1,"source preparation order/idle telemetry");
 wait(state[1]);ticks(100);
 if(taking_off || enabled || dut.published_m1!=1200 || dut.published_m4!=1200)$fatal(1,"source prepared idle");
 dut.receiver.env_ch3=2000; // No centered-throttle entry and no manual-PWM map.
 settle();if(!taking_off || !enabled || pickup)$fatal(1,"full-stick takeoff state");
 xy=1;ticks(200000);settle();xy=0;ticks(200000);settle();
 if(pickup || !enabled)$fatal(1,"mode changes must retain vertical controller without pickup");
 dut.receiver.env_ch3=1000;ticks(200000);settle();
 if(!enabled || !taking_off)$fatal(1,"low stick is descent in both modes");
 dut.receiver.env_ch5=1000;#1;
 if(enabled || fresh || dut.effective1_us!=1000 || dut.effective4_us!=1000)$fatal(1,"SWA immediate stop");
 ticks(2);dut.receiver.env_ch5=2000;ticks(200);
 if(armed)$fatal(1,"unexpected rearm after lock with no new low confirmation");
 dut.receiver.env_ch5=1000;ticks(20);dut.receiver.env_ch3=1000;ticks(20);dut.receiver.env_ch5=2000;ticks(30);
 if(!armed)$fatal(1,"new low/high arm confirmation");
 vertical_ok=0;#1;
 if(armed || enabled || fresh || dut.effective1_us!=1000)$fatal(1,"vertical reference failure stop");
 $display("CORE_ANO_PASS preparation/idle/full-stick takeoff/vertical continuity/no pickup/descent/SWA/fault stop");$finish;
end
initial begin #100000000;$fatal(1,"core timeout");end
endmodule
