`timescale 1ns/1ps
// Complete navigation wrappers, actual shared math services, every public output.
// No force on data, validity, published heights, numerical/FSM state or flags.
module tb_navigation_equivalence;
reg clk=0;always #10 clk=~clk;
reg rst=0,pose=1,origin_ok=1,diag_hold=0,range_ok=1,flow_ok=1,acc_ok=1,enabled=0,taking_off=0,burst=0,accelerated=0;
reg sample=0,acc_update=0;reg[31:0] distance=1000,dt=10,source_age=0;reg signed[31:0] vx=0,vy=0,az=0;
reg signed[15:0] roll=0,pitch=0,yaw=0;reg[15:0] ch1=1500,ch2=1500,ch3=1000,ch4=1500,ch7=1000;
wire origin_reset=!pose || !origin_ok;
wire yaw_ok=yaw>=-18000 && yaw<=18000;
wire tilt45=roll>=-4500 && roll<=4500 && pitch>=-4500 && pitch<=4500;
wire tilt15=roll>=-1500 && roll<=1500 && pitch>=-1500 && pitch<=1500;
wire az_ok=az>=-30000 && az<=30000;
wire velocity_ok=vx>=-1000000 && vx<=1000000 && vy>=-1000000 && vy<=1000000;
integer clocks=0,comparisons=0,publications=0,height_publications=0,ready_cycles=0,overlaps=0,i;
reg[63:0] uptime=0;
always @(posedge clk)clocks=clocks+1;
always @(negedge clk)begin
 sample=rst && (burst ? clocks%10==0:accelerated ? clocks%2500==0:clocks%50000==0);
 acc_update=rst && clocks%50000==100;
 uptime=clocks/50000;
end
wire[1041:0] a,b;
mtf_xyz_navigation_control #(.PROOF_CONTROLLER(1),.PRECHECKED_YAW_RANGE(1),.STARTUP_ONLY_DIAGNOSTIC_RESET(1),.PRECHECKED_HEIGHT_TILT4500(1),.PRECHECKED_FLOW_TILT1500(1),.PRECHECKED_HEIGHT_ORIGIN(1),.PRECHECKED_AZ_RANGE(1),.PRECHECKED_INPUT_VELOCITY(1)) dut(
.clk(clk),.rst_n(rst),.origin_reset(origin_reset),.diagnostic_hold(diag_hold),.xy_p_value(16'd1000),.xy_i_value(16'd350),
.height_origin_ok(origin_ok),.sample_valid(sample),.range_valid(range_ok),.flow_valid(flow_ok),.distance_mm(distance),.dt_ms(dt),.source_age_ms(source_age),
.vx_x100(vx),.vy_x100(vy),.velocity_range_ok(velocity_ok),.pose_valid(pose),.roll_cdeg(roll),.pitch_cdeg(pitch),.yaw_cdeg(yaw),.yaw_range_ok(yaw_ok),
.acc_valid(acc_ok && pose),.acc_update(acc_update),.acc_dt_us(32'd1000),.az_range_ok(az_ok),.ax_mmps2(32'sd0),.ay_mmps2(32'sd0),.az_up_mmps2(az),
.rc_valid(1'b1),.enabled(enabled),.taking_off(taking_off),.channel_count(4'd8),.ch1(ch1),.ch2(ch2),.ch3(ch3),.ch4(ch4),.ch7(ch7),.collective_us(16'd1300),.uptime_ms(uptime),
.height_tilt4500_ok(tilt45),.flow_tilt1500_ok(tilt15),
.parameter_boundary(a[0:0]),
.diagnostic_body(a[720:1]),
.control_permission(a[721:721]),
.position_ready(a[722:722]),
.height_ready(a[723:723]),
.core_height_tail(a[724:724]),
.core_height_tail_without_acc(a[725:725]),
.core_height_state_tail(a[726:726]),
.position_x_q8(a[758:727]),
.position_y_q8(a[790:759]),
.xy_requested(a[791:791]),
.xy_ready(a[792:792]),
.xy_active(a[793:793]),
.xy_roll_target(a[809:794]),
.xy_pitch_target(a[825:810]),
.xy_payload_roll(a[841:826]),
.xy_payload_pitch(a[857:842]),
.xy_reason(a[873:858]),
.z_feedback_height(a[905:874]),
.z_target_height_out(a[937:906]),
.pilot_norm_x(a[955:938]),
.pilot_norm_y(a[973:956]),
.pilot_norm_update(a[974:974]),
.pilot_norm_valid(a[975:975]),
.pilot_norm_dt_us(a[991:976]),
.auto_takeoff(a[992:992]),
.z_active(a[993:993]),
.z_throttle_delta(a[1009:994]),
.z_collective(a[1025:1010]),
.z_reason(a[1041:1026]));
mtf_xyz_navigation_control_reference #(.PROOF_CONTROLLER(1),.PRECHECKED_YAW_RANGE(1),.STARTUP_ONLY_DIAGNOSTIC_RESET(1),.PRECHECKED_HEIGHT_TILT4500(1),.PRECHECKED_FLOW_TILT1500(1),.PRECHECKED_HEIGHT_ORIGIN(1),.PRECHECKED_AZ_RANGE(1),.PRECHECKED_INPUT_VELOCITY(1)) refnav(
.clk(clk),.rst_n(rst),.origin_reset(origin_reset),.diagnostic_hold(diag_hold),.xy_p_value(16'd1000),.xy_i_value(16'd350),
.height_origin_ok(origin_ok),.sample_valid(sample),.range_valid(range_ok),.flow_valid(flow_ok),.distance_mm(distance),.dt_ms(dt),.source_age_ms(source_age),
.vx_x100(vx),.vy_x100(vy),.velocity_range_ok(velocity_ok),.pose_valid(pose),.roll_cdeg(roll),.pitch_cdeg(pitch),.yaw_cdeg(yaw),.yaw_range_ok(yaw_ok),
.acc_valid(acc_ok && pose),.acc_update(acc_update),.acc_dt_us(32'd1000),.az_range_ok(az_ok),.ax_mmps2(32'sd0),.ay_mmps2(32'sd0),.az_up_mmps2(az),
.rc_valid(1'b1),.enabled(enabled),.taking_off(taking_off),.channel_count(4'd8),.ch1(ch1),.ch2(ch2),.ch3(ch3),.ch4(ch4),.ch7(ch7),.collective_us(16'd1300),.uptime_ms(uptime),
.height_tilt4500_ok(tilt45),.flow_tilt1500_ok(tilt15),
.parameter_boundary(b[0:0]),
.diagnostic_body(b[720:1]),
.control_permission(b[721:721]),
.position_ready(b[722:722]),
.height_ready(b[723:723]),
.core_height_tail(b[724:724]),
.core_height_tail_without_acc(b[725:725]),
.core_height_state_tail(b[726:726]),
.position_x_q8(b[758:727]),
.position_y_q8(b[790:759]),
.xy_requested(b[791:791]),
.xy_ready(b[792:792]),
.xy_active(b[793:793]),
.xy_roll_target(b[809:794]),
.xy_pitch_target(b[825:810]),
.xy_payload_roll(b[841:826]),
.xy_payload_pitch(b[857:842]),
.xy_reason(b[873:858]),
.z_feedback_height(b[905:874]),
.z_target_height_out(b[937:906]),
.pilot_norm_x(b[955:938]),
.pilot_norm_y(b[973:956]),
.pilot_norm_update(b[974:974]),
.pilot_norm_valid(b[975:975]),
.pilot_norm_dt_us(b[991:976]),
.auto_takeoff(b[992:992]),
.z_active(b[993:993]),
.z_throttle_delta(b[1009:994]),
.z_collective(b[1025:1010]),
.z_reason(b[1041:1026]));

always @(posedge clk)begin #2;
 comparisons=comparisons+1;
 if(a!==b)$fatal(1,"navigation public cycle mismatch at %0d h=%0d/%0d XOR=%h",comparisons,dut.height_mm,refnav.height_mm,a^b);
 if((^dut.height_mm)===1'bx || dut.height_mm<0 || dut.height_mm>5000)$fatal(1,"geometry producer violated bounded-height contract");
 if(dut.geometry_update)publications=publications+1;
 if(dut.height_fusion_update)height_publications=height_publications+1;
 if(dut.height_ready)ready_cycles=ready_cycles+1;
 if(dut.geometry.overlap)overlaps=overlaps+1;
end
task cycles;input integer n;integer j;begin for(j=0;j<n;j=j+1)@(negedge clk);end endtask
initial begin
 cycles(5);rst=1;cycles(1200000);
 burst=1;cycles(100);burst=0;accelerated=1;enabled=1;
 for(i=0;i<128;i=i+1)begin
  case(i%12)0:distance=0;1:distance=9;2:distance=10;3:distance=80;4:distance=4999;5:distance=5000;6:distance=5001;7:distance=32'hffffffff;8:distance=32'h80000000;default:distance=1000+i*7;endcase
  range_ok=i%13!=0;flow_ok=i%5!=0;pose=i%17!=0;origin_ok=i%19!=0;diag_hold=i%7==0;source_age=i%11==0?100:0;
  roll=i%9==0?4501:i%3==0?-1499:500;pitch=i%8==0?-4501:i%4==0?1501:0;yaw=i%23==0?18001:i*13-500;
  vx=i%7==0?1000001:i*91-5000;vy=i%9==0?-1000001:5000-i*57;az=i%29==0?30001:i%3==0?-500:250;
  acc_ok=i%31!=0;dt=i%21==0?0:i%27==0?51:10;ch1=1500+i%3*20;ch2=1500-i%3*20;ch7=i%2==0?2000:1000;taking_off=i%3==0;
  cycles(2500);
 end
 accelerated=0;range_ok=1;flow_ok=1;pose=1;origin_ok=1;source_age=0;roll=0;pitch=0;yaw=0;vx=0;vy=0;az=0;acc_ok=1;dt=10;distance=1200;diag_hold=0;enabled=0;taking_off=0;ch1=1500;ch2=1500;ch7=1000;
 cycles(1200000);
 if(comparisons<2700000 || publications<20 || height_publications<2 || ready_cycles<10000 || overlaps==0)$fatal(1,"navigation coverage: compare%0d geometry%0d height%0d ready%0d overlap%0d",comparisons,publications,height_publications,ready_cycles,overlaps);
 $display("PASS navigation public cycle equivalence: %0d comparisons %0d geometry publications %0d height publications %0d ready cycles %0d overlaps; geometry height always0..5000",comparisons,publications,height_publications,ready_cycles,overlaps);$finish;
end
initial begin #80000000;$fatal(1,"navigation equivalence timeout");end
endmodule
