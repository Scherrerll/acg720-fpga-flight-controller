`timescale 1ns/1ps
module tb;
reg clk=0;always #10 clk=~clk;
reg vertical_ok=1,xy=0;
wire taking_off,enabled,fresh,armed,fallback;
flight_core #(.ARM_LOW_TICKS(8),.ARM_HIGH_TICKS(8),.FLIGHT_STATE_TICKS_PER_MS(100)) dut(
 .clk50(clk),.imu_miso(1'b0),.rc_ppm_in(1'b0),.hold_active(xy && vertical_ok),
 .altitude_active(taking_off && vertical_ok),.vertical_available(vertical_ok),
 .vertical_height_mm(32'sd200),.auto_takeoff(1'b0),
 .pilot_norm_x(18'sd0),.pilot_norm_y(18'sd0),.pilot_norm_valid(vertical_ok),
 .pilot_norm_update(dut.pose_update && vertical_ok),.pilot_norm_dt_us(16'd2000),
 .taking_off_out(taking_off),.height_fallback_active(fallback),
 .hold_roll_cdeg(16'sd0),.hold_pitch_cdeg(16'sd0),.hold_throttle_delta_us(16'sd0),
 .hold_collective_us(vertical_ok ?16'd1400:16'd0),.control_enabled(enabled),
 .command_fresh(fresh),.armed_usable(armed));
task ticks;input integer n;begin repeat(n)@(negedge clk);end endtask
task launch;begin
 vertical_ok=1;xy=0;dut.receiver.env_ch1=1500;dut.receiver.env_ch3=1000;dut.receiver.env_ch5=1000;
 ticks(30);dut.receiver.env_ch5=2000;ticks(30);
 wait(dut.motor_prepared);dut.receiver.env_ch3=1600;
 wait(fresh && dut.pending_throttle==1400 && dut.effective1_us==1400 && dut.effective4_us==1400);ticks(10000);dut.receiver.env_ch3=1500;ticks(10000);
 if(!armed || !enabled || !dut.fallback_control.seen)$fatal(1,"Launch/valid automatic collective missing");
end endtask
integer i;
initial begin
 wait(dut.rst_n);wait(dut.fallback_norm_valid);launch();
 vertical_ok=0;#1;
 if(!fallback || !enabled || !armed || !fresh || dut.selected_throttle!=1400)
  $fatal(1,"Height loss must preserve live attitude/collective");
 for(i=0;i<200000;i=i+1)begin ticks(1);
  if(!fallback || !enabled || !fresh || dut.effective1_us==1000 || dut.effective4_us==1000)
   begin $display("DIAG fallback=%b enabled=%b fresh=%b armed=%b raw=%b sensor=%b manualfault=%h ctrl_fault=%h gate=%h seen=%b latch=%b normvalid=%b selected=%d pending=%d takingoff=%b land=%b ratefresh=%b commandseen=%b m1=%d eff1=%d",fallback,enabled,fresh,armed,dut.armed,dut.sensor_ok,dut.manual_angle_fault,dut.controller_fault,dut.gate_last_revoke_code,dut.fallback_control.seen,dut.fallback_control.latched,dut.fallback_norm_valid,dut.selected_throttle,dut.pending_throttle,taking_off,dut.land_lock,dut.rate_fresh,dut.command_seen,dut.m1,dut.effective1_us); $fatal(1,"Gap/reset in actual core PWM path after height loss"); end
 end
 if(dut.manual_angle_fault || dut.controller_fault)$fatal(1,"Manual path faulted on lost native normalizer");
 dut.receiver.env_ch1=1900;ticks(1500000);
 if(!fallback || !enabled || dut.outer_target_roll<=0 || dut.mix1==dut.mix3)
  $fatal(1,"Independent pilot input did not reach actual attitude/mixer");
 vertical_ok=1;ticks(10000);if(!fallback)$fatal(1,"Automatic reentry after range recovery");
 dut.receiver.env_ch5=1000;#1;
 if(fallback || fresh || enabled || dut.effective1_us!=1000 || dut.effective4_us!=1000)
  $fatal(1,"SWA did not immediately override fallback");
 ticks(2);vertical_ok=0;dut.receiver.env_ch3=1000;ticks(30);dut.receiver.env_ch5=2000;ticks(30);
 if(armed || fallback)$fatal(1,"Missing height allowed preflight arming");
 launch();vertical_ok=0;ticks(100);force dut.attitude_valid=0;#1;
 if(fallback || fresh || enabled || dut.effective1_us!=1000)$fatal(1,"IMU stop lost priority");
 ticks(2);release dut.attitude_valid;ticks(30);if(armed || fallback)$fatal(1,"IMU recovery rearmed automatically");
 launch();vertical_ok=0;ticks(100);force dut.rc_valid=0;#1;
 if(fallback || fresh || enabled || dut.effective1_us!=1000)$fatal(1,"RC stop lost priority");
 ticks(2);release dut.rc_valid;ticks(30);if(armed || fallback)$fatal(1,"RC recovery rearmed automatically");
 $display("PASS actual core: no PWM gap, independent pilot, latched fallback, preflight block, SWA/IMU/RC immediate stops");$finish;
end
initial begin #300000000;$fatal(1,"Core fallback timeout");end
endmodule
