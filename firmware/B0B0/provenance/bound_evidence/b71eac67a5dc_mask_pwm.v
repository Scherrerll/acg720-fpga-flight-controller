
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
