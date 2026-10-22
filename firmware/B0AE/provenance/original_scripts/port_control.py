"""One-time, asserted migration from the frozen B0AD source. No hardware IO."""
from pathlib import Path
R=Path(__file__).resolve().parent/'fixture'

def replace(s,a,b):
    assert s.count(a)==1,(a[:100],s.count(a))
    return s.replace(a,b)

p=R/'position/mtf_xyz_hold_control.v';s=p.read_text()
s=s[s.index('module mtf_xyz_hold_control'):]
s='''`timescale 1ns/1ps
// ANO reference control migration: Z loop in both modes; OF XY velocity PI.
// All physical IO/FRD/unit adapters are documented in CONTROL_CONTRACT.txt.
// No centered-throttle entry, switch-reselection latch, position outer loop,
// captured entry thrust or manual pickup policy remains in this controller.
'''+s
s=replace(s,'input wire enabled,position_valid,','input wire enabled,taking_off,position_valid,')
s=replace(s,' assign height_requested=requested;',' assign height_requested=rc_valid;')
s=replace(s,' assign height_ready=ready;',' assign height_ready=z_numeric_ready && !origin_reset;')
a=s.index(' wire cancel_now=');b=s.index(' reg cancel=1',a)
s=s[:a]+''' wire cancel_now=!rc_valid || !enabled || !height_ready || blocked || command_stale;
 ano_z_stick z_stick(.clk(clk),.rst_n(rst_n),.enabled(rc_valid && !origin_reset),.taking_off(taking_off),
  .sample_update(sample_update),.sample_dt_us(sample_dt_us),.ch3(ch3),
  .norm_q16(z_norm_q16),.speed_q16(z_speed_q16),.busy(z_stick_busy),.update(),.fault(z_stick_fault));
 wire xy_stick_busy,xy_stick_fault;wire signed [17:0] stick_nx,stick_ny;
 ano_xy_stick xy_stick(.clk(clk),.rst_n(rst_n),.enabled(rc_valid && !origin_reset),
  .sample_update(sample_update),.sample_dt_us(sample_dt_us),.ch1(ch1),.ch2(ch2),
  .nx(stick_nx),.ny(stick_ny),.busy(xy_stick_busy),.fault(xy_stick_fault));
 wire xy_cancel_now=cancel_now || !requested || !ready || xy_stick_fault || !tracking;
 assign active=requested && enabled && ready && taking_off && tracking && xy_tracking && command_seen && !command_stale && !blocked && !xy_stick_fault;
 assign height_active=enabled && height_ready && taking_off && tracking && height_command_seen && !command_stale && !blocked;
''' +s[b:]
s=replace(s,' reg signed [31:0] target_x=0,target_y=0;', ''' reg signed [31:0] target_x=0,target_y=0;
 reg [1:0] auto_phase=0;reg [15:0] auto_ms=0;
 reg signed [31:0] auto_speed=0,alt_speed=0,next_auto_speed=0;
 reg signed [63:0] inner_alt_speed=0;''')
a=s.index('   // An observed origin');b=s.index('   if(cancel ||',a)
s=s[:a]+'''   // Faults stop the active calculation; normal mode/sensor recovery has
   // no switch-acknowledgement requirement. Arithmetic faults reset on lock.
   if(!enabled || origin_reset)begin blocked<=0;xy_blocked<=0;fault_reason<=0;end
''' +s[b:]
s=replace(s,'if(cancel || origin_reset || blocked || xy_blocked)begin','if(cancel || origin_reset || blocked)begin')
s=replace(s,'   end else if(!tracking)begin\n    if(!throttle_centered)begin prepare<=0;height_reason<=256;end\n    else if(prepare<ENTRY_TICKS)prepare<=prepare+1\'b1;\n    else if(position_update && position_dt_us>=1000 && position_dt_us<=100000)begin', '''   end else if(!tracking)begin
    if(height_update)begin''')
s=replace(s,"bias_store<=keep64(($signed({1'b0,collective_us})-1000)*65536);reason<=64;height_reason<=64;",'bias_store<=keep64(0);reason<=64;height_reason<=64;')
s=replace(s,'    if(position_update)begin','    if(xy_cancel)begin position_due<=0;command_seen<=0;ix_store<=0;iy_store<=0;afx_store<=0;afy_store<=0;end\n    else if(position_update && !xy_stick_busy)begin')
s=replace(s,'      calc($signed(pending_az)*65536-afz,1,5,20);','      inner_alt_speed<=alt_speed;calc($signed(pending_az)*65536-afz,1,5,20);')
a=s.index('     43:begin');b=s.index('     1:begin',a)
s=s[:a]+'''     43:calc($signed(stick_nx),horizontal_speed_limit_q16,65536,44);
     44:begin sx_store<=keep64(value);calc($signed(stick_ny),horizontal_speed_limit_q16,65536,45);end
     45:begin sy_store<=keep64(value);world_sx_store<=0;world_sy_store<=0;calc($signed({1'b0,dt})*314,65536,10000000+dt*314,1);end
''' +s[b:]
# Desired velocity already lives in H/body coordinates, unlike world feedback.
s=replace(s,'30:if(trig_done) calc(world_sx,cs,65536,31);','30:if(trig_done) calc(-sample_vx,cs,65536,35);')
s=replace(s,'fixx_store<=keep64(rot_tmp+value);','fixx_store<=keep64(rot_tmp+value+sx);')
s=replace(s,'fixy_store<=keep64(-rot_tmp+value);','fixy_store<=keep64(-rot_tmp+value+sy);')
s=replace(s,'clip(ix+value,-65536000,65536000)','taking_off ?clip(ix+value,-65536000,65536000):0')
s=replace(s,'clip(iy+value,-65536000,65536000)','taking_off ?clip(iy+value,-65536000,65536000):0')
s=replace(s,'calc(speed_z_tick,3,5,53);','calc(inner_alt_speed,3,5,53);')
s=replace(s,'iz_store<=keep64(clip(iz+value,-(131072000-bias),131072000-bias));','iz_store<=keep64(taking_off ?clip(iz+value,-(131072000-bias),131072000-bias):0);')
a=s.index('     // B0AC:');b=s.index('     54:begin',a)
s=s[:a]+'''     // Source1Hz THR_START35 bias relaxation, never captured stick PWM.
     23:begin bias_store<=keep64(taking_off ?bias+value:0);calc(exz,1,5,24);end
     24:begin collective_q16_store<=keep64(taking_off ?clip(value+iz+bias,0,55705600):0);state<=60;end
     // Auto_Take_Off_Land_Task executes after Alt1, before Alt2 (11ms).
     60:begin
      if(!taking_off)begin auto_phase<=0;auto_ms<=0;next_auto_speed<=0;end
      else if(auto_phase==0 || auto_phase==1)begin
       auto_ms<=auto_ms+16'd11;auto_phase<=1;
       next_auto_speed<=held_h>=600 ?0:(600-held_h)*2>800 ?800:((600-held_h)*2/10)*10;
       if(auto_ms+11>=5000 || 64'sd39321600-target_z_q16<64'sd1310720 ||
          (auto_ms+11>2000 && (ch3<=1406 || ch3>=1594)))auto_phase<=2;
      end else begin auto_ms<=0;next_auto_speed<=0;end
      state<=61;
     end
     61:begin
      // _flight_state_st.alt_ctrl_speed_set is s16 cm/s in the C source.
      auto_speed<=next_auto_speed;
      alt_speed<=taking_off ?integer_q16(speed_z_tick)/10*655360+next_auto_speed*65536:0;
      state<=62;
     end
     62:calc(alt_speed,11,1000,54);
''' +s[b:]
s=replace(s,'vsz_store<=keep64(clip(target_z_q16-$signed(held_h)*65536,-98304000,98304000));','vsz_store<=keep64(taking_off ?clip(target_z_q16-($signed(held_h)/10)*655360,-98304000,98304000):0);\n      if(!taking_off)target_z_q16_store<=keep64(($signed(held_h)/10)*655360);')
# C resets Alt2 target to integer-cm feedback while not taking off.
s=replace(s,'publish_speed<=integer_q16(speed_z_tick);','publish_speed<=integer_q16(alt_speed);')
s=replace(s,'   end else if(!tracking)begin','    auto_phase<=0;auto_ms<=0;auto_speed<=0;alt_speed<=0;next_auto_speed<=0;\n   end else if(!tracking)begin')
p.write_text(s)

# Navigation: Z validity/epoch must not depend on XY quality or mode selection.
p=R/'mtf_xyz_navigation_control.v';s=p.read_text()
s=replace(s,'input wire rc_valid,enabled,','input wire rc_valid,enabled,taking_off,')
s=replace(s,' output wire z_active,',' output wire signed [31:0] z_feedback_height,z_target_height_out,\n output wire z_active,')
s=replace(s,' wire observation_bad=!live_velocity;',' wire observation_bad=!height_ready || !fused_vz_q16_valid;')
a=s.index(' wire control_bad=');b=s.index(' reg observation_bad_d=',a)
s=s[:a]+''' wire control_bad=observation_bad || !rc_valid || !enabled;
''' +s[b:]
s=replace(s,' || (raw_manual && !manual_d)','')
s=replace(s,'.ch7(c_ch7),.enabled(c_enabled && controller_control_epoch_ok),','.ch7(c_ch7),.enabled(c_enabled && controller_control_epoch_ok),.taking_off(taking_off),')
a=s.index(' assign xy_ready=');b=s.index(' // Source-epoch',a)
s=s[:a]+''' assign xy_ready=controller_ready && position_ready && raw_numeric_ok && controller_observation_epoch_ok && !origin_reset;
 assign xy_active=controller_active && xy_ready && controller_control_epoch_ok && raw_requested && rc_valid && enabled;
''' +s[b:]
s=replace(s,' assign z_active=xy_active;', ' assign z_active=controller_z_active && controller_z_ready && height_ready && fused_vz_q16_valid && controller_observation_epoch_ok && controller_control_epoch_ok && rc_valid && enabled && !origin_reset;')
s=replace(s,'assign z_throttle_delta=xy_active ?','assign z_throttle_delta=z_active ?')
s=replace(s,'assign z_collective=xy_active ?','assign z_collective=z_active ?')
s=replace(s,'wire signed [31:0] z_target_height=xy_active ?','wire signed [31:0] z_target_height=z_active ?')
s=replace(s,' assign control_permission=xy_active;',' assign z_feedback_height=fused_height;assign z_target_height_out=z_target_height;\n assign control_permission=xy_active;')
p.write_text(s)

# Core: all-flight vertical closed loop. No manual PWM/pickup policy.
p=R/'core/flight_core.v';s=p.read_text()
s=replace(s,'input wire hold_active,altitude_active,','input wire hold_active,altitude_active,vertical_available,\n    output wire taking_off_out,\n    input wire signed [31:0] vertical_height_mm,')
s=replace(s,'sensor_ok && installation_verified)', 'sensor_ok && installation_verified && vertical_available && !land_lock)')
s=replace(s,'sensor_ok && channel_count>=5', 'sensor_ok && vertical_available && !land_lock && channel_count>=5')
s=replace(s,'assign controller_enabled=RUN_RANGE_OK && armed_usable && (ch3>1100 || altitude_active || takeover_retain);', 'assign controller_enabled=RUN_RANGE_OK && armed_usable && taking_off && altitude_active;')
s=replace(s,'throttle_active_q<=ch3>1100 || altitude_active || takeover_retain;', 'throttle_active_q<=taking_off && altitude_active;')
s=replace(s,'.att_stab(!altitude_active)', '.att_stab(!hold_active)')
a=s.index('    wire takeover_retain;');b=s.index('    // Latch the exact yaw code',a)
s=s[:a]+'''    wire motor_prepared,taking_off,flying,land_lock;wire [3:0] preparation_mask;
    ano_flight_state flight_state(.clk(clk50),.rst_n(rst_n),.armed(armed_usable),
     .ch3(ch3),.collective_us(hold_collective_us),.motor_prepared(motor_prepared),
     .taking_off(taking_off),.flying(flying),.land_lock(land_lock),.preparation_mask(preparation_mask));
    assign taking_off_out=taking_off;
    assign throttle_takeover_active=1'b0;assign throttle_pickup_us=16'd0;
    wire [15:0] selected_throttle=hold_collective_us;
    wire [15:0] mixed_collective=pending_throttle;
''' +s[b:]
s=replace(s,'captured_active<=RUN_RANGE_OK && (ch3>1100 || altitude_active || takeover_retain);','captured_active<=RUN_RANGE_OK && taking_off && altitude_active;')
# Source motor preparation/idle bypasses taking_off controller, still behind
# immediate SWA/RC/IMU/vertical health gates. No stale rate command is published.
a=s.index('    assign command_fresh=');b=s.index('    wire [15:0] effective1_us',a)
s=s[:a]+'''    wire rate_fresh=controller_enabled && controller_run && command_seen && command_age<POSE_TIMEOUT_TICKS;
    wire idle_running=armed_usable && (!taking_off || !motor_prepared);
    assign command_fresh=rate_fresh || idle_running;
    wire [15:0] published_m1=rate_fresh ?m1:idle_running && preparation_mask[0] ?RUN_MIN_US:16'd1000;
    wire [15:0] published_m2=rate_fresh ?m2:idle_running && preparation_mask[1] ?RUN_MIN_US:16'd1000;
    wire [15:0] published_m3=rate_fresh ?m3:idle_running && preparation_mask[2] ?RUN_MIN_US:16'd1000;
    wire [15:0] published_m4=rate_fresh ?m4:idle_running && preparation_mask[3] ?RUN_MIN_US:16'd1000;
''' +s[b:]
s=replace(s,'.m1_us(m1),.m2_us(m2),.m3_us(m3),.m4_us(m4),', '.m1_us(published_m1),.m2_us(published_m2),.m3_us(published_m3),.m4_us(published_m4),')
s=replace(s,'assign base_throttle_us=mapped_throttle;', 'assign base_throttle_us=altitude_active ?hold_collective_us:16\'d1000;')
p.write_text(s)

# Separate XY and Z handoff records. A switch change never switches the
# vertical stick meaning from climb-rate back to raw ESC PWM.
p=R/'acg720_ano_port.v';s=p.read_text()
s=replace(s,' wire raw_xyz_joint_active=nav_xy_active && nav_z_active;', ''' wire raw_xyz_joint_active=nav_xy_active;
 wire taking_off,nav_vertical_ready;wire signed [31:0] nav_feedback_height,nav_target_height;
 reg z_handoff_active=0;
 always @(posedge clk50)if(!rst_n)z_handoff_active<=0;else z_handoff_active<=nav_z_active;''')
s=replace(s,'.hold_active(xyz_joint_active),.altitude_active(xyz_joint_active),', '.hold_active(xyz_joint_active),.altitude_active(z_handoff_active),.vertical_available(nav_vertical_ready),.taking_off_out(taking_off),.vertical_height_mm(nav_feedback_height),')
s=replace(s,'.enabled(armed && !throttle_takeover_active)', '.enabled(armed),.taking_off(taking_off)')
s=replace(s,'.position_ready(),.height_ready(),', '.position_ready(),.height_ready(nav_vertical_ready),.z_feedback_height(nav_feedback_height),.z_target_height_out(nav_target_height),')
# Handoff bus must carry Z collective even when XY inactive; its valid bit is
# solely XY validity, with the separately registered Z-valid bit above.
p.write_text(s)
p=R/'acg720_ano_port.gprj';s=p.read_text().replace('<File path="core/throttle_takeover.v" type="file.verilog" enable="1"/>','<File path="core/ano_flight_state.v" type="file.verilog" enable="1"/>\n<File path="position/ano_xy_stick.v" type="file.verilog" enable="1"/>');p.write_text(s)
print('Migrated isolated B0AE source; offline only, not programmed')
