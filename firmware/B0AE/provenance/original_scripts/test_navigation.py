from test_tools import *
bench=r'''
`timescale 1ns/1ps
module tb;
reg clk=0;always #10 clk=~clk;
reg rst_n=0,sample=0,acc=0;
reg signed[15:0]roll=0;
wire xr,xready,xa,za,pr,hr;wire[15:0]xc,zc,coll;wire[719:0]diag;
mtf_xyz_navigation_control #(.PROOF_CONTROLLER(1),.PRECHECKED_YAW_RANGE(1)) dut(
 .clk(clk),.rst_n(rst_n),.origin_reset(1'b0),.diagnostic_hold(1'b0),
 .sample_valid(sample),.range_valid(1'b1),.flow_valid(1'b1),.distance_mm(32'd1000),.dt_ms(32'd10),.source_age_ms(32'd0),
 .vx_x100(32'sd0),.vy_x100(32'sd0),.pose_valid(1'b1),.pose_age_ticks(32'd0),
 .roll_cdeg(roll),.pitch_cdeg(16'sd0),.yaw_cdeg(16'sd0),.yaw_range_ok(1'b1),
 .acc_valid(1'b1),.acc_update(acc),.acc_dt_us(32'd2000),.ax_mmps2(32'sd0),.ay_mmps2(32'sd0),.az_up_mmps2(32'sd0),
 .rc_valid(1'b1),.enabled(1'b1),.taking_off(1'b1),.channel_count(4'd8),
 .ch1(16'd1500),.ch2(16'd1500),.ch3(16'd1500),.ch4(16'd1500),.ch7(16'd2000),.collective_us(16'd1000),
 .uptime_ms(64'd0),.diagnostic_body(diag),.position_ready(pr),.height_ready(hr),
 .xy_requested(xr),.xy_ready(xready),.xy_active(xa),.xy_reason(xc),.z_active(za),.z_collective(coll),.z_reason(zc));
integer ticks=0;
always @(negedge clk)begin
 sample=0;acc=0;
 if(rst_n)begin
  ticks=ticks+1;
  if(ticks%100000==0)acc=1;
  if(ticks%500000==0)sample=1;
 end
end
initial begin
 repeat(4)@(negedge clk);rst_n=1;
 wait(xa && za);@(negedge clk);
 force dut.integral_valid=0;
 force dut.position_age=32'hffffffff;
 repeat(1500000)@(negedge clk);
 if(pr || !xr || !xready || !xa || !za || !hr)$fatal(1,"telemetry accumulator must not control OF authority");
 // A tilt outside the current OF qualification withdraws XY immediately,
 // while the cosine-corrected vertical laser reference remains available.
 roll=3000;#1;if(xa || !za || !hr)$fatal(1,"XY tilt bound must not drop Z");
 repeat(1000000)@(negedge clk);
 if(xa || !za || !hr)$fatal(1,"Z continuity through tilt/flow withdrawal");
 roll=0;wait(xa && za);
 $display("NAVIGATION_PASS real50MHz services: velocity authority independent of position display; 30deg withdraws XY but preserves Z; recovery");$finish;
end
initial begin #300000000;$fatal(1,"navigation timeout xr=%d ready=%d xy=%d z=%d height=%d reasons=%d/%d",xr,xready,xa,za,hr,xc,zc);end
endmodule
'''
(ROOT/'tests/navigation_control.v').write_text(bench)
names=['mtf_xyz_navigation_control.v','sensor/mtf_shared_geometry.v','sensor/mtf_native_geometry.v',
 'position/mtf_shared_flow_fusion.v','position/mtf_shared_height_fusion.v','position/mtf_position_integrator.v',
 'position/mtf_xyz_hold_control.v','position/ano_z_stick.v','position/ano_xy_stick.v','position/ano_xy_divide36.v','position/position_math.v','nav_math_service.v']
simulate('navigation_control',[FIX/n for n in names],ROOT/'tests/navigation_control.v')
