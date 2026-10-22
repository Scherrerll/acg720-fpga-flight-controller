from test_tools import *
import sys
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
meta=json.loads((ROOT/'reference/mask_parent.json').read_text());cp=ROOT/'reference/mask_changes.json'
assert sha(cp)==meta['changes_sha256'];changes=json.loads(cp.read_text());paths=[cp,ROOT/'reference/mask_parent.json',ROOT/'test_mask_retiming.py']
for name,items in changes.items():
 old=ROOT/'reference/mask_parent'/name;new=FIX/name;assert sha(old)==meta['sources_sha256'][name]
 s=old.read_text()
 for a,b in items.items():assert s.count(a)==1;s=s.replace(a,b)
 assert s==new.read_text(),('Unexpected mask-retiming delta',name)
 paths +=[old,new]
old_pwm=ROOT/'reference/mask_parent/core/motor_pwm.v';s=old_pwm.read_text();assert s.count('module motor_pwm #(')==1
(ROOT/'tests/original_motor_pwm.v').write_text(s.replace('module motor_pwm #(','module original_motor_pwm #('))
bench=r'''
`timescale 1ns/1ps
module tb;
reg clk=0,run=0;always #10 if(run)clk=~clk;
reg rst_n=0,en=0,rf=0,ir=0;reg[3:0]mask=0;
reg[15:0]r1=1000,r2=1000,r3=1000,r4=1000;
flight_core core(.clk50(1'b0),.imu_miso(1'b0),.rc_ppm_in(1'b0),
 .hold_active(1'b0),.altitude_active(1'b0),.vertical_available(1'b0),.auto_takeoff(1'b0),
 .pilot_norm_x(18'sd0),.pilot_norm_y(18'sd0),.pilot_norm_update(1'b0),.pilot_norm_valid(1'b0),.pilot_norm_dt_us(16'd1000),
 .vertical_height_mm(32'sd100),.hold_roll_cdeg(16'sd0),.hold_pitch_cdeg(16'sd0),.hold_throttle_delta_us(16'sd0),.hold_collective_us(16'd1000));
wire[3:0]a,b;wire[63:0]ea,eb,la,lb;wire fa,fb,xa,xb;
original_motor_pwm #(.TICKS_PER_US(50),.FRAME_US(2500),.MAX_US(2000)) old_pwm(
 .clk(clk),.rst_n(rst_n),.enabled(en),
 .m1_us(core.published_m1),.m2_us(core.published_m2),.m3_us(core.published_m3),.m4_us(core.published_m4),
 .motor1_pwm(a[0]),.motor2_pwm(a[1]),.motor3_pwm(a[2]),.motor4_pwm(a[3]),
 .effective1_us(ea[63:48]),.effective2_us(ea[47:32]),.effective3_us(ea[31:16]),.effective4_us(ea[15:0]),
 .frame_latched1_us(la[63:48]),.frame_latched2_us(la[47:32]),.frame_latched3_us(la[31:16]),.frame_latched4_us(la[15:0]),
 .frame_active(fa),.limited(xa));
motor_pwm #(.TICKS_PER_US(50),.FRAME_US(2500),.MAX_US(2000),.EXTERNAL_TICKS(1)) new_pwm(
 .clk(clk),.rst_n(rst_n),.enabled(en),
 .m1_us(core.published_m1),.m2_us(core.published_m2),.m3_us(core.published_m3),.m4_us(core.published_m4),
 .pre_ticks1(core.outputs.pre_ticks1),.pre_ticks2(core.outputs.pre_ticks2),.pre_ticks3(core.outputs.pre_ticks3),.pre_ticks4(core.outputs.pre_ticks4),
 .motor1_pwm(b[0]),.motor2_pwm(b[1]),.motor3_pwm(b[2]),.motor4_pwm(b[3]),
 .effective1_us(eb[63:48]),.effective2_us(eb[47:32]),.effective3_us(eb[31:16]),.effective4_us(eb[15:0]),
 .frame_latched1_us(lb[63:48]),.frame_latched2_us(lb[47:32]),.frame_latched3_us(lb[31:16]),.frame_latched4_us(lb[15:0]),
 .frame_active(fb),.limited(xb));
task check_conversion;begin
 if({core.m1,core.m2,core.m3,core.m4,core.rate_fresh,core.idle_running,core.preparation_mask}!=={r1,r2,r3,r4,rf,ir,mask})$fatal(1,"test stimulus force did not propagate");
 if(core.outputs.EXTERNAL_TICKS!=1)$fatal(1,"core did not select conversion interface");
 if(core.outputs.pre_ticks1!==old_pwm.clamp(core.published_m1)*32'd50 ||
    core.outputs.pre_ticks2!==old_pwm.clamp(core.published_m2)*32'd50 ||
    core.outputs.pre_ticks3!==old_pwm.clamp(core.published_m3)*32'd50 ||
    core.outputs.pre_ticks4!==old_pwm.clamp(core.published_m4)*32'd50)$fatal(1,"preconversion mismatch%0d",r1);
 if({core.outputs.m1_us,core.outputs.m2_us,core.outputs.m3_us,core.outputs.m4_us}!==
    {core.published_m1,core.published_m2,core.published_m3,core.published_m4})$fatal(1,"frame data wiring changed");
end endtask
integer u,c,k,i,high_cycles=0;
initial begin
 force core.m1=r1;force core.m2=r2;force core.m3=r3;force core.m4=r4;
 force core.rate_fresh=rf;force core.idle_running=ir;force core.preparation_mask=mask;
 // Every uint16 command on every lane, all four validity selections, both
 // mask polarities plus mixed masks. Check actual core->PWM interface.
 for(u=0;u<65536;u=u+1)begin
  r1=u;r2=u^16'haaaa;r3=65535-u;r4=u*17;
  for(c=0;c<4;c=c+1)for(k=0;k<3;k=k+1)begin
   rf=c&1;ir=(c>>1)&1;mask=k==0 ?0:k==1 ?15:u&15;#1;check_conversion();
  end
 end
 run=1;repeat(2)@(negedge clk);rst_n=1;
 for(i=0;i<700000;i=i+1)begin
  en=(i%300000>=2000 && i%300000<260000);rf=(i/10000)%2;ir=!rf;mask=(i/5000)%16;
  if(i%5000==0)begin r1=$random;r2=$random;r3=$random;r4=$random;end
  @(negedge clk);#1;check_conversion();
  if({a,ea,la,fa,xa}!=={b,eb,lb,fb,xb})$fatal(1,"PWM/raw/effective waveform changed at%0d",i);
  if(fa && a!=0 && old_pwm.phase>50000)high_cycles=high_cycles+1;
 end
 if(high_cycles<1000)$fatal(1,"missing active pulse-extension observations");
 $display("PWM_PRECONVERSION_EXACT_PASS uint16x12selections x4lanes;700000actual50MHz clocks; all outputs equal");$finish;
end
endmodule
'''
(ROOT/'tests/mask_pwm.v').write_text(bench)
model=Path(json.loads((ROOT/'baseline.json').read_text())['parent']).parent/'b0ac_algorithm_review_20261020T090039Z/external_producer_models.v'
names=['core/flight_core.v','core/ano_flight_state.v','core/control_gate.v','core/motor_pwm.v',
 'core/rtl/quad_mixer_feedback.v','core/rtl/ano_rate_control.v','core/rtl/ano_yaw_control.v',
 'core/rtl/pid_divide_signed64.v','core/rtl/ano_rc_angle_targets.v','core/rtl/ano_manual_angles.v','position/ano_xy_divide36.v']
simulate('mask_pwm',[FIX/n for n in names]+[model,ROOT/'tests/original_motor_pwm.v'],ROOT/'tests/mask_pwm.v')
bench=r'''
`timescale 1ns/1ps
module tb;
reg clk=0;always #10 clk=~clk;
reg rst_n=0,a=0;reg[15:0]r=0,p=0,d=0,c=0;
wire[64:0]old_out,raw_out;wire[64:0]new_out={raw_out[64],raw_out[64]?raw_out[63:48]:16'd0,raw_out[64]?raw_out[47:32]:16'd0,raw_out[31:0]};
nav_control_handoff old_h(.clk(clk),.rst_n(rst_n),.command_in({a,a?r:16'd0,a?p:16'd0,d,c}),.command_out(old_out));
nav_control_handoff new_h(.clk(clk),.rst_n(rst_n),.command_in({a,r,p,d,c}),.command_out(raw_out));
integer i;
initial begin
 repeat(2)@(negedge clk);rst_n=1;
 for(i=0;i<50000;i=i+1)begin
  a=$random;r=$random;p=$random;d=$random;c=$random;rst_n=i%7001>2;
  @(negedge clk);#1;if(old_out!==new_out)$fatal(1,"handoff bit mismatch");
 end
 $display("HANDOFF_MASK_COMMUTATION_PASS50000cycles no latency or value change");$finish;
end
endmodule
'''
(ROOT/'tests/mask_handoff.v').write_text(bench)
simulate('mask_handoff',[FIX/'acg720_ano_port.v'],ROOT/'tests/mask_handoff.v')
bench=r'''
`timescale 1ns/1ps
module tb;
reg clk=0;always #10 clk=~clk;
reg rst_n=0,hold=0;reg[719:0]raw_data=0,reference_q=0;
wire[719:0]actual;
mtf_xyz_navigation_control dut(.clk(clk),.rst_n(rst_n),.origin_reset(1'b0),.diagnostic_hold(hold),
 .sample_valid(1'b0),.range_valid(1'b0),.flow_valid(1'b0),.distance_mm(32'd100),.dt_ms(32'd20),.source_age_ms(32'd0),
 .vx_x100(32'sd0),.vy_x100(32'sd0),.pose_valid(1'b0),.pose_age_ticks(32'hffffffff),
 .roll_cdeg(16'sd0),.pitch_cdeg(16'sd0),.yaw_cdeg(16'sd0),.yaw_range_ok(1'b1),
 .acc_valid(1'b0),.acc_update(1'b0),.acc_dt_us(32'd1000),.ax_mmps2(32'sd0),.ay_mmps2(32'sd0),.az_up_mmps2(32'sd0),
 .rc_valid(1'b0),.enabled(1'b0),.taking_off(1'b0),.channel_count(4'd8),
 .ch1(16'd1500),.ch2(16'd1500),.ch3(16'd1000),.ch4(16'd1500),.ch7(16'd1000),.collective_us(16'd1000),.uptime_ms(64'd0),.diagnostic_body(actual));
function[719:0]mask_before;input[719:0]v;begin
 mask_before=v;mask_before[143:128]=v[85]?v[143:128]:16'd0;mask_before[127:112]=v[85]?v[127:112]:16'd0;
end endfunction
always @(posedge clk)if(!rst_n)reference_q<=dut.RESET_DIAGNOSTIC;else if(!hold)reference_q<=mask_before(raw_data);
integer i,j;
initial begin
 force dut.diagnostic_next=raw_data;
 repeat(2)@(negedge clk);rst_n=1;
 for(i=0;i<60000;i=i+1)begin
  for(j=0;j<22;j=j+1)raw_data[j*32+:32]=$random;raw_data[719:704]=$random;
  hold=(i%29>17);rst_n=i%7001>2;
  @(negedge clk);#1;if(actual!==reference_q)$fatal(1,"diagnostic720bit mismatch at%0d",i);
 end
 $display("DIAGNOSTIC_MASK_COMMUTATION_PASS60000cycles all720bits, resets and holds");$finish;
end
endmodule
'''
(ROOT/'tests/mask_diagnostic.v').write_text(bench)
sources=[FIX/n for n in re.findall(r'<File path="([^"]+\.v)"',(FIX/'acg720_ano_port.gprj').read_text())]
simulate('mask_diagnostic',sources,ROOT/'tests/mask_diagnostic.v')
report=dict(passed=True,pwm_uint16_selections=65536*12*4,pwm_actual50mhz_cycles=700000,
 handoff_cycles=50000,diagnostic_cycles=60000,diagnostic_bits_compared=720,
 extra_control_latency_clocks=0,physical_raw_and_effective_outputs_bit_equal=True,
 payload_and_control_values_bit_equal=True,fractional_precision_changed=False)
(ROOT/'tests/mask_retiming.json').write_text(json.dumps(report,indent=2))
paths +=[ROOT/'tests/original_motor_pwm.v']
(ROOT/'tests/mask_retiming.proof.json').write_text(json.dumps(dict(passed=True,
 source_sha256={str(p.relative_to(ROOT)).replace('\\','/'):sha(p)for p in paths},
 method='Exact listed transforms; function/selector distribution; mask/register commutation; actual-interface and whole-waveform comparisons'),indent=2))
print('MASK_RETIMING_EQUIVALENCE_PASS all external values/latency preserved')
