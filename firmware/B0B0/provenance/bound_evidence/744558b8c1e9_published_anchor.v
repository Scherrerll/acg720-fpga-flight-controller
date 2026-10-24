`timescale 1ns/1ps
module tb;
reg clk=0;always #10 clk=~clk;
reg vertical_ok=1,altitude=1;
wire fallback;
flight_core dut(.clk50(clk),.imu_miso(1'b0),.rc_ppm_in(1'b0),.hold_active(1'b0),.altitude_active(altitude),.vertical_available(vertical_ok),.vertical_height_mm(32'sd200),.auto_takeoff(1'b0),.pilot_norm_x(18'sd0),.pilot_norm_y(18'sd0),.pilot_norm_valid(1'b1),.pilot_norm_update(1'b0),.pilot_norm_dt_us(16'd2000),.hold_roll_cdeg(16'sd0),.hold_pitch_cdeg(16'sd0),.hold_throttle_delta_us(16'sd0),.hold_collective_us(16'd1400),.height_fallback_active(fallback));
integer errors=0,checks=0,k,prior_value;
reg[15:0] pre1,pre2,pre3,pre4;
task tick;input integer n;begin repeat(n)@(negedge clk);end endtask
task check;input condition;input [511:0]message;begin checks=checks+1;if(condition !== 1'b1)begin errors=errors+1;$display("FAIL %0s",message);end end endtask
task clear;begin
 vertical_ok=1;altitude=1;force dut.controller_update=0;
 force dut.fallback_control.rst_n=0;tick(2);release dut.fallback_control.rst_n;tick(1);
end endtask
task publish;input[15:0]value;begin
 force dut.pending_throttle=value;force dut.controller_update=1;tick(1);force dut.controller_update=0;tick(1);
end endtask
initial begin
 wait(dut.rst_n);tick(2);
 // Isolate the actual publication/selection boundary; separate full-core test exercises all health gates.
 force dut.sensor_ok=1;force dut.rc_valid=1;force dut.armed=1;force dut.taking_off=1;
 force dut.ch3=1500;force dut.ch5=2000;force dut.fallback_norm_valid=1;force dut.land_lock=0;
 force dut.controller_enabled=1;force dut.controller_run=1;force dut.rate_fresh=1;
 force dut.rate_sample_update=0;force dut.correction_roll=75;force dut.correction_pitch=-25;force dut.correction_yaw=10;
 clear();publish(1400);publish(1100);pre1=dut.m1;pre2=dut.m2;pre3=dut.m3;pre4=dut.m4;vertical_ok=0;#1;
 check(fallback && dut.fallback_collective==1100,"fresh published1100 replaces older1400");
 check(dut.mixed_collective==1100,"loss selects exact published anchor prior_value mixer");
 tick(1);check(dut.fallback_control.manual_us==1100,"entry edge preserves below-idle anchor");
 force dut.controller_update=1;tick(1);force dut.controller_update=0;
 check(dut.m1==pre1 && dut.m2==pre2 && dut.m3==pre3 && dut.m4==pre4,"first fallback publication preserves four nonzero-correction motor commands");
 tick(60);prior_value=dut.fallback_collective;tick(10000);check(dut.fallback_collective==prior_value,"sub-idle anchor cannot jump prior_value1ms slew interval");
 clear();publish(1400);force dut.pending_throttle=1500;tick(4);vertical_ok=0;#1;
 check(dut.fallback_collective==1400,"unpublished pending1500 cannot replace published1400");
 check(dut.mixed_collective==1400,"queued automatic1500 excluded immediately on loss");
 force dut.controller_update=1;tick(1);force dut.controller_update=0;#1;
 check(dut.m1==1440 && dut.m2==1310 && dut.m3==1340 && dut.m4==1510,"queued completion uses fallback anchor with nonzero attitude corrections");
 clear();force dut.pending_throttle=1100;tick(3);vertical_ok=0;#1;
 check(!fallback,"no fallback prior_value first actual publication");
 force dut.controller_update=1;tick(1);force dut.controller_update=0;check(!fallback,"first completion after height loss cannot establish prior valid anchor");
 clear();publish(1100);vertical_ok=0;#1;check(fallback && dut.fallback_collective==1100,"first legal sub-idle publication permits fallback");
 clear();publish(1000);vertical_ok=0;#1;check(fallback && dut.fallback_collective==1000,"legal1000 publication is exact first anchor");
 tick(60);prior_value=dut.fallback_collective;tick(50000);check(dut.fallback_collective==prior_value+1 && dut.fallback_control.target_q==1200,"below-idle recovery retains1us per millisecond slew");
 if(errors)$fatal(1,"Published anchor regression: %0d of %0d checks failed",errors,checks);
 $display("PASS published anchor: %0d checks, publication boundary,1000/1100 anchors, queued result, nonzero corrections, slew",checks);$finish;
end
initial begin #10000000;$fatal(1,"Published anchor timeout");end
endmodule

