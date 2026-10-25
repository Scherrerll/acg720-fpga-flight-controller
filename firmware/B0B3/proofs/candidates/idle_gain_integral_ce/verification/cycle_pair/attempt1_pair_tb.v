`timescale 1ns/1ps
module tb;
reg clk=0,rst_n=0,enabled=1,rc_valid=1,taking_off=1,origin=0,sensor_valid=1;
reg[15:0]ch1=1500,ch2=1500,ch3=1500,ch7=2000,pval=500,ival=0;
reg sample_update=0,position_update=0,height_update=0,inject_error=0;
reg[31:0]position_dt=20000,position_age=0;
reg signed[31:0]vx=0,vy=0,height=1000,vz=0,ax=0,ay=0,az=0;reg signed[15:0]yaw=0;
wire[449:0]old_public,new_public,idle_public;
old_wrapper a(clk,rst_n,enabled,rc_valid,taking_off,origin,sensor_valid,ch1,ch2,ch3,ch7,pval,ival,sample_update,position_update,height_update,inject_error,position_dt,position_age,vx,vy,height,vz,ax,ay,az,yaw,old_public);new_wrapper b(clk,rst_n,enabled,rc_valid,taking_off,origin,sensor_valid,ch1,ch2,ch3,ch7,pval,ival,sample_update,position_update,height_update,inject_error,position_dt,position_age,vx,vy,height,vz,ax,ay,az,yaw,new_public);idle_base_wrapper c(clk,rst_n,enabled,rc_valid,taking_off,origin,sensor_valid,ch1,ch2,ch3,ch7,pval,ival,sample_update,position_update,height_update,inject_error,position_dt,position_age,vx,vy,height,vz,ax,ay,az,yaw,idle_public);
always #10 clk=~clk;
integer saved_freeze=0,saved_captures=0,saved_rollbacks=0,partial_I_rollbacks=0,saved_idle_differences=0;
reg[26:0]pre_sx,pre_sy,pre_ix,pre_iy;reg restore_edge,partial_I;
integer cycles=0,xy_pubs=0,z_pubs=0,xy_starts=0,z_starts=0,idle_differences=0,freeze_checks=0,start_checks=0;
integer cancel_mbusy=0,cancel_dbusy=0,error_hits=0,rollback_hits=0,priority_checks=0,reset_busy=0;
reg[255:0]states=0;reg[31:0]rng=32'h49a173ed;reg random_gains=0,pause_samples=0;integer sample_clock=0;
reg[15:0]prev_bp,prev_bi,admit_p,admit_i;reg[7:0]prestate;reg pre_work,pre_both,pre_cancel,pre_rst;integer phase=0;
reg[65535:0]p_seen=0,i_seen=0;
always @(negedge clk)begin
 sample_update=0;
 if(rst_n)begin
  sample_clock=sample_clock+1;
  if(sample_clock%1000==0 && !pause_samples)sample_update=1;
 end
 if(random_gains)begin
  rng={rng[30:0],rng[31]^rng[21]^rng[1]^rng[0]};pval=rng[15:0];
  rng={rng[30:0],rng[31]^rng[21]^rng[1]^rng[0]};ival=rng[31:16];
 end
end
always @(posedge clk)begin
 prestate=b.dut.state;pre_work=b.dut.work_xy;pre_cancel=b.dut.xy_cancel;pre_rst=rst_n;
 prev_bp=b.dut.work_p;prev_bi=b.dut.work_i;admit_p=pval;admit_i=ival;
 pre_sx=b.dut.saved_ix;pre_sy=b.dut.saved_iy;pre_ix=b.dut.ix_store;pre_iy=b.dut.iy_store;
 restore_edge=rst_n && !b.dut.cancel && !origin && !b.dut.blocked && b.dut.tracking && pre_work && pre_cancel;
 partial_I=({pre_ix,pre_iy}!={pre_sx,pre_sy}) && ({pre_ix,pre_iy}!=0);
 pre_both=b.dut.state==0 && b.dut.tracking && !b.dut.cancel && !origin && !b.dut.blocked && b.dut.height_due && b.dut.height_stick_captured && b.dut.position_due && b.dut.position_stick_captured && !b.dut.xy_cancel;
 if(!rst_n && b.dut.state!=0)reset_busy=reset_busy+1;
 if(b.math_mul_cancel && b.mbusy)cancel_mbusy=cancel_mbusy+1;
 if(b.math_div_cancel && b.dbusy)cancel_dbusy=cancel_dbusy+1;
 if(rst_n && b.dut.state==101 && b.ddone && inject_error)error_hits=error_hits+1;
 if(rst_n && pre_work && pre_cancel)rollback_hits=rollback_hits+1;
 #2;cycles=cycles+1;
 if(idle_public!==new_public)$fatal(1,"immediate frozen idle baseline public mismatch cycle=%0d",cycles);
 if(old_public!==new_public)$fatal(1,"public cycle mismatch cycle=%0d phase=%0d states=%0d/%0d",cycles,phase,a.dut.state,b.dut.state);
 if(a.dut.state!==b.dut.state || a.dut.work_xy!==b.dut.work_xy)$fatal(1,"FSM mismatch");
 if(c.dut.state!==b.dut.state || c.dut.work_xy!==b.dut.work_xy)$fatal(1,"immediate baseline FSM mismatch");
 if(prestate!=0)begin if(b.dut.saved_ix!==pre_sx || b.dut.saved_iy!==pre_sy)$fatal(1,"saved I changed during nonidle work");saved_freeze=saved_freeze+1;end
 if(b.dut.work_xy && b.dut.state!=0 && ({b.dut.saved_ix,b.dut.saved_iy}!=={c.dut.saved_ix,c.dut.saved_iy} || {b.dut.saved_ix,b.dut.saved_iy}!=={a.dut.saved_ix,a.dut.saved_iy}))$fatal(1,"active saved I pair differs from actual baselines");
 if(prestate==0 && b.dut.state==43 && b.dut.work_xy)begin if(b.dut.saved_ix!==pre_ix || b.dut.saved_iy!==pre_iy)$fatal(1,"saved I admission edge changed");saved_captures=saved_captures+1;end
 if(restore_edge)begin if(b.dut.ix_store!==pre_sx || b.dut.iy_store!==pre_sy)$fatal(1,"saved I rollback value/edge changed");saved_rollbacks=saved_rollbacks+1;if(partial_I)partial_I_rollbacks=partial_I_rollbacks+1;end
 if(b.dut.state==0 && {b.dut.saved_ix,b.dut.saved_iy}!=={c.dut.saved_ix,c.dut.saved_iy})saved_idle_differences=saved_idle_differences+1;
 states[b.dut.state]=1;
 if(prestate!=0)begin
  if(b.dut.work_p!==prev_bp || b.dut.work_i!==prev_bi)$fatal(1,"candidate gain changed while pre-edge state!=0");
  freeze_checks=freeze_checks+1;
 end
 if(b.dut.work_xy && b.dut.state!=0)begin
  if(a.dut.work_p!==b.dut.work_p || a.dut.work_i!==b.dut.work_i)$fatal(1,"active XY snapshot mismatch");
 end
 if(prestate==0 && b.dut.state==43 && b.dut.work_xy)begin
  if(b.dut.work_p!==admit_p || b.dut.work_i!==admit_i)$fatal(1,"same-edge pair capture failed");
  p_seen[admit_p]=1;i_seen[admit_i]=1;start_checks=start_checks+1;xy_starts=xy_starts+1;
 end
 if(prestate==0 && b.dut.state==100 && !b.dut.work_xy)z_starts=z_starts+1;
 if(pre_both)begin
  if(b.dut.work_xy || b.dut.state!=100 || b.dut.return_state!=20)$fatal(1,"Z priority changed");
  priority_checks=priority_checks+1;
 end
 if(b.dut.command_seen && b.dut.command_age==0)xy_pubs=xy_pubs+1;
 if(b.dut.height_command_seen && b.dut.height_command_age==0)z_pubs=z_pubs+1;
 if(b.dut.state==0 && {a.dut.work_p,a.dut.work_i}!=={b.dut.work_p,b.dut.work_i})idle_differences=idle_differences+1;
end
task tick;input integer n;begin repeat(n)@(negedge clk);#1;end endtask
task pulse;input integer xy,z;begin @(negedge clk);#1;position_update=xy;height_update=z;@(negedge clk);#1;position_update=0;height_update=0;end endtask
task boot;begin
 @(negedge clk);#1;rst_n=0;enabled=0;position_update=0;height_update=0;inject_error=0;origin=0;rc_valid=1;sensor_valid=1;ch7=2000;taking_off=1;position_age=0;
 tick(5);rst_n=1;enabled=1;tick(10);pulse(0,1);tick(10);
 if(!b.dut.tracking)$fatal(1,"entry failed");
end endtask
task complete_pair;begin
 pause_samples=1;tick(1);while(b.dut.xy_stick_busy || b.dut.z_stick_busy)tick(1);
 pulse(1,1);tick(5);pause_samples=0;tick(11995);
 if(b.dut.state!=0 || b.dut.position_due || b.dut.height_due || b.dut.blocked)$fatal(1,"callback failed to finish phase=%0d",phase);
end endtask
function[15:0]corner;input integer i;begin case(i)
 0:corner=0;1:corner=1;2:corner=500;3:corner=10000;4:corner=16383;5:corner=16384;6:corner=32767;7:corner=32768;8:corner=65534;default:corner=65535;endcase end endfunction
integer i;integer seen_p_count=0,seen_i_count=0;
initial begin
 boot();tick(3);pval=123;ival=456;tick(4);
 if(b.dut.work_p!=123 || b.dut.work_i!=456 || a.dut.work_p==123)$fatal(1,"idle waveform distinction was not exercised");
 phase=1;
 for(i=0;i<20;i=i+1)begin
  pval=corner(i%10);ival=corner((i*3+1)%10);vx=((i%3)-1)*1000*65536;vy=(((i+1)%3)-1)*701*65536;
  yaw=(i%5-2)*8000;ax=(i%3-1)*21000;ay=((i+1)%3-1)*12000;position_dt=(i%2)?1000:100000;
  complete_pair();
 end
 $display("PASS all16-bit gain corner values, high bits, XY/Z priority, real math and exact public cycles");
 phase=2;random_gains=1;
 for(i=0;i<48;i=i+1)begin
  vx=(i%7-3)*317*65536;vy=((i+3)%7-3)*419*65536;yaw=(i%9-4)*4100;
  height=200+(i*89)%4400;vz=(i%5-2)*111*65536;az=(i%5-2)*12000;position_dt=1000+(i*7171)%99001;
  ch1=1150+(i*131)%701;ch2=1150+(i*197)%701;ch3=1400+(i*31)%201;complete_pair();
 end
 $display("PASS deterministic arbitrary16-bit gain changes each work/idle clock; active snapshots remain frozen");
 phase=3;ch1=1500;ch2=1500;ch3=1500;yaw=0;vx=500*65536;vy=-800*65536;height=1000;vz=0;az=0;position_dt=20000;
 pulse(1,0);wait(b.dut.work_xy && b.dut.state==64);@(negedge clk);#1;ch7=1500;tick(500);ch7=2000;complete_pair();
 pulse(1,0);wait(b.dut.work_xy && b.dut.state==100);@(negedge clk);#1;enabled=0;tick(500);boot();complete_pair();
 pulse(1,0);wait(b.dut.work_xy && b.dut.state==101);@(negedge clk);#1;origin=1;tick(500);origin=0;boot();complete_pair();
 pulse(1,0);wait(b.dut.work_xy && b.dut.state==101);@(negedge clk);#1;rc_valid=0;tick(500);boot();complete_pair();
 pulse(1,0);wait(b.dut.work_xy && b.dut.state==100);@(negedge clk);#1;sensor_valid=0;tick(500);boot();complete_pair();
 pulse(1,0);wait(b.dut.work_xy && b.dut.state==101);boot();complete_pair();
 pulse(0,1);wait(!b.dut.work_xy && b.dut.state==101);boot();complete_pair();
 $display("PASS XY rollback, busy multiply/divide cancel and drain, RC/sensor/origin/stop, XY and Z busy resets");
 phase=4;
 pulse(1,0);wait(b.dut.work_xy && b.dut.state==101);@(negedge clk);#1;inject_error=1;tick(500);
 if(!b.dut.blocked || b.reason!=512)$fatal(1,"public arithmetic error input did not block");
 inject_error=0;boot();complete_pair();
 taking_off=0;complete_pair();taking_off=1;complete_pair();
 pulse(1,0);wait(b.dut.work_xy && b.dut.state==101);@(negedge clk);#1;position_age=5000000;tick(500);position_age=0;complete_pair();
 $display("PASS real service done with injected public divider error, blocked recovery, taking-off changes, age cancellation");
 random_gains=0;
 for(i=0;i<65536;i=i+1)begin if(p_seen[i])seen_p_count=seen_p_count+1;if(i_seen[i])seen_i_count=seen_i_count+1;end
 if(xy_pubs<70 || z_pubs<70 || priority_checks<60 || freeze_checks<100000 || idle_differences<100 || cancel_mbusy==0 || cancel_dbusy==0 || rollback_hits==0 || error_hits==0 || reset_busy<2)$fatal(1,"coverage incomplete xy=%0d z=%0d priority=%0d freeze=%0d idle=%0d cm=%0d cd=%0d rb=%0d err=%0d resets=%0d",xy_pubs,z_pubs,priority_checks,freeze_checks,idle_differences,cancel_mbusy,cancel_dbusy,rollback_hits,error_hits,reset_busy);
 if(!p_seen[65535] || !p_seen[32768] || !p_seen[16384] || !i_seen[65535] || !i_seen[32768] || !i_seen[16384])$fatal(1,"full-width high-bit corners missing");
 $display("PASS COVERAGE cycles=%0d xy_pubs=%0d z_pubs=%0d xy_starts=%0d z_starts=%0d start_checks=%0d freeze_checks=%0d idle_differences=%0d priority=%0d cancel_mbusy=%0d cancel_dbusy=%0d rollback=%0d fault=%0d reset_busy=%0d distinct_p=%0d distinct_i=%0d states=%h",cycles,xy_pubs,z_pubs,xy_starts,z_starts,start_checks,freeze_checks,idle_differences,priority_checks,cancel_mbusy,cancel_dbusy,rollback_hits,error_hits,reset_busy,seen_p_count,seen_i_count,states);
 if(saved_freeze<100000 || saved_captures!=xy_starts || saved_rollbacks<1 || partial_I_rollbacks<1 || saved_idle_differences<100)$fatal(1,"saved I coverage incomplete freeze=%0d captures=%0d rollback=%0d partial=%0d idle=%0d",saved_freeze,saved_captures,saved_rollbacks,partial_I_rollbacks,saved_idle_differences);
 $display("PASS SAVED_I freeze=%0d captures=%0d rollbacks=%0d nonzero_partial_I_rollbacks=%0d private_idle_differences=%0d; both actual response and immediate idle baselines public450bits cycle equal",saved_freeze,saved_captures,saved_rollbacks,partial_I_rollbacks,saved_idle_differences);
 $finish;
end
initial begin #100000000;$fatal(1,"pair timeout phase=%0d state=%0d",phase,b.dut.state);end
endmodule
module old_wrapper(input wire clk,rst_n,enabled,rc_valid,taking_off,origin,sensor_valid,
 input wire[15:0]ch1,ch2,ch3,ch7,pval,ival,input wire sample_update,position_update,height_update,inject_error,
 input wire[31:0]position_dt,position_age,
 input wire signed[31:0]vx,vy,height,vz,ax,ay,az,input wire signed[15:0]yaw,output wire[449:0]public_out);
 wire parameter_boundary,mbusy,mdone,merror,dbusy,ddone,derror;wire signed[63:0]mresult,dresult;
  wire [0:0] requested;
 wire [0:0] ready;
 wire [0:0] active;
 wire [0:0] height_requested;
 wire [0:0] height_ready;
 wire [0:0] height_active;
 wire [0:0] auto_takeoff;
 wire [15:0] reason;
 wire [15:0] height_reason;
 wire [15:0] collective_target_us;
 wire [15:0] roll_target;
 wire [15:0] pitch_target;
 wire [15:0] throttle_delta;
 wire [31:0] requested_climb_mmps;
 wire [31:0] target_height_mm;
 wire [17:0] pilot_norm_x;
 wire [17:0] pilot_norm_y;
 wire [0:0] pilot_norm_update;
 wire [0:0] pilot_norm_valid;
 wire [15:0] pilot_norm_dt_us;
 wire [0:0] math_mul_start;
 wire [0:0] math_mul_cancel;
 wire [63:0] math_mul_a;
 wire [63:0] math_mul_b;
 wire [0:0] math_div_start;
 wire [0:0] math_div_cancel;
 wire [63:0] math_div_numerator;
 wire [31:0] math_div_denominator;
 mtf_xyz_hold_control_old #(.CAL_MASK(8'hff),.VELOCITY_FRAC_BITS(16))dut(
  .clk(clk),.rst_n(rst_n),.origin_reset(origin),.rc_valid(rc_valid),.channel_count(4'd8),
 .ch1(ch1),.ch2(ch2),.ch3(ch3),.ch4(16'd1500),.ch7(ch7),.xy_p_value(pval),.xy_i_value(ival),.parameter_boundary(parameter_boundary),
 .enabled(enabled),.taking_off(taking_off),.position_valid(sensor_valid),.height_valid(sensor_valid),
 .position_update(position_update),.height_update(height_update),.sample_update(sample_update),.sample_dt_us(32'd1000),
 .position_age(position_age),.position_dt_us(position_dt),.x_q8(32'sd0),.y_q8(32'sd0),.vx(vx),.vy(vy),.height_mm(height),.vz(vz),.yaw_cdeg(yaw),
 .acc_valid(sensor_valid),.ax_mmps2(ax),.ay_mmps2(ay),.az_mmps2(az),.collective_us(16'd1500),
 .math_mul_busy(mbusy),.math_mul_done(mdone),.math_mul_result(mresult),
 .math_div_busy(dbusy),.math_div_done(ddone),.math_div_error(derror||inject_error),.math_div_result(dresult),
 .requested(requested),.ready(ready),.active(active),.height_requested(height_requested),.height_ready(height_ready),.height_active(height_active),.auto_takeoff(auto_takeoff),.reason(reason),.height_reason(height_reason),.collective_target_us(collective_target_us),.roll_target(roll_target),.pitch_target(pitch_target),.throttle_delta(throttle_delta),.requested_climb_mmps(requested_climb_mmps),.target_height_mm(target_height_mm),.pilot_norm_x(pilot_norm_x),.pilot_norm_y(pilot_norm_y),.pilot_norm_update(pilot_norm_update),.pilot_norm_valid(pilot_norm_valid),.pilot_norm_dt_us(pilot_norm_dt_us),.math_mul_start(math_mul_start),.math_mul_cancel(math_mul_cancel),.math_mul_a(math_mul_a),.math_mul_b(math_mul_b),.math_div_start(math_div_start),.math_div_cancel(math_div_cancel),.math_div_numerator(math_div_numerator),.math_div_denominator(math_div_denominator));
 assign public_out={requested,ready,active,height_requested,height_ready,height_active,auto_takeoff,reason,height_reason,collective_target_us,roll_target,pitch_target,throttle_delta,requested_climb_mmps,target_height_mm,pilot_norm_x,pilot_norm_y,pilot_norm_update,pilot_norm_valid,pilot_norm_dt_us,math_mul_start,math_mul_cancel,math_mul_a,math_mul_b,math_div_start,math_div_cancel,math_div_numerator,math_div_denominator,parameter_boundary};
 nav_math_service #(.CLIENTS(1),.DIVIDE(0))mservice(.clk(clk),.rst_n(rst_n),.request(math_mul_start),.cancel(math_mul_cancel),
 .operand_a(math_mul_a),.operand_b(math_mul_b),.busy(mbusy),.done(mdone),.error(merror),.result(mresult),.grant());
 nav_math_service #(.CLIENTS(1),.DIVIDE(1))dservice(.clk(clk),.rst_n(rst_n),.request(math_div_start),.cancel(math_div_cancel),
 .operand_a(math_div_numerator),.operand_b({32'd0,math_div_denominator}),.busy(dbusy),.done(ddone),.error(derror),.result(dresult),.grant());
 endmodule
module new_wrapper(input wire clk,rst_n,enabled,rc_valid,taking_off,origin,sensor_valid,
 input wire[15:0]ch1,ch2,ch3,ch7,pval,ival,input wire sample_update,position_update,height_update,inject_error,
 input wire[31:0]position_dt,position_age,
 input wire signed[31:0]vx,vy,height,vz,ax,ay,az,input wire signed[15:0]yaw,output wire[449:0]public_out);
 wire parameter_boundary,mbusy,mdone,merror,dbusy,ddone,derror;wire signed[63:0]mresult,dresult;
  wire [0:0] requested;
 wire [0:0] ready;
 wire [0:0] active;
 wire [0:0] height_requested;
 wire [0:0] height_ready;
 wire [0:0] height_active;
 wire [0:0] auto_takeoff;
 wire [15:0] reason;
 wire [15:0] height_reason;
 wire [15:0] collective_target_us;
 wire [15:0] roll_target;
 wire [15:0] pitch_target;
 wire [15:0] throttle_delta;
 wire [31:0] requested_climb_mmps;
 wire [31:0] target_height_mm;
 wire [17:0] pilot_norm_x;
 wire [17:0] pilot_norm_y;
 wire [0:0] pilot_norm_update;
 wire [0:0] pilot_norm_valid;
 wire [15:0] pilot_norm_dt_us;
 wire [0:0] math_mul_start;
 wire [0:0] math_mul_cancel;
 wire [63:0] math_mul_a;
 wire [63:0] math_mul_b;
 wire [0:0] math_div_start;
 wire [0:0] math_div_cancel;
 wire [63:0] math_div_numerator;
 wire [31:0] math_div_denominator;
 mtf_xyz_hold_control #(.CAL_MASK(8'hff),.VELOCITY_FRAC_BITS(16))dut(
  .clk(clk),.rst_n(rst_n),.origin_reset(origin),.rc_valid(rc_valid),.channel_count(4'd8),
 .ch1(ch1),.ch2(ch2),.ch3(ch3),.ch4(16'd1500),.ch7(ch7),.xy_p_value(pval),.xy_i_value(ival),.parameter_boundary(parameter_boundary),
 .enabled(enabled),.taking_off(taking_off),.position_valid(sensor_valid),.height_valid(sensor_valid),
 .position_update(position_update),.height_update(height_update),.sample_update(sample_update),.sample_dt_us(32'd1000),
 .position_age(position_age),.position_dt_us(position_dt),.x_q8(32'sd0),.y_q8(32'sd0),.vx(vx),.vy(vy),.height_mm(height),.vz(vz),.yaw_cdeg(yaw),
 .acc_valid(sensor_valid),.ax_mmps2(ax),.ay_mmps2(ay),.az_mmps2(az),.collective_us(16'd1500),
 .math_mul_busy(mbusy),.math_mul_done(mdone),.math_mul_result(mresult),
 .math_div_busy(dbusy),.math_div_done(ddone),.math_div_error(derror||inject_error),.math_div_result(dresult),
 .requested(requested),.ready(ready),.active(active),.height_requested(height_requested),.height_ready(height_ready),.height_active(height_active),.auto_takeoff(auto_takeoff),.reason(reason),.height_reason(height_reason),.collective_target_us(collective_target_us),.roll_target(roll_target),.pitch_target(pitch_target),.throttle_delta(throttle_delta),.requested_climb_mmps(requested_climb_mmps),.target_height_mm(target_height_mm),.pilot_norm_x(pilot_norm_x),.pilot_norm_y(pilot_norm_y),.pilot_norm_update(pilot_norm_update),.pilot_norm_valid(pilot_norm_valid),.pilot_norm_dt_us(pilot_norm_dt_us),.math_mul_start(math_mul_start),.math_mul_cancel(math_mul_cancel),.math_mul_a(math_mul_a),.math_mul_b(math_mul_b),.math_div_start(math_div_start),.math_div_cancel(math_div_cancel),.math_div_numerator(math_div_numerator),.math_div_denominator(math_div_denominator));
 assign public_out={requested,ready,active,height_requested,height_ready,height_active,auto_takeoff,reason,height_reason,collective_target_us,roll_target,pitch_target,throttle_delta,requested_climb_mmps,target_height_mm,pilot_norm_x,pilot_norm_y,pilot_norm_update,pilot_norm_valid,pilot_norm_dt_us,math_mul_start,math_mul_cancel,math_mul_a,math_mul_b,math_div_start,math_div_cancel,math_div_numerator,math_div_denominator,parameter_boundary};
 nav_math_service #(.CLIENTS(1),.DIVIDE(0))mservice(.clk(clk),.rst_n(rst_n),.request(math_mul_start),.cancel(math_mul_cancel),
 .operand_a(math_mul_a),.operand_b(math_mul_b),.busy(mbusy),.done(mdone),.error(merror),.result(mresult),.grant());
 nav_math_service #(.CLIENTS(1),.DIVIDE(1))dservice(.clk(clk),.rst_n(rst_n),.request(math_div_start),.cancel(math_div_cancel),
 .operand_a(math_div_numerator),.operand_b({32'd0,math_div_denominator}),.busy(dbusy),.done(ddone),.error(derror),.result(dresult),.grant());
 endmodule
module idle_base_wrapper(input wire clk,rst_n,enabled,rc_valid,taking_off,origin,sensor_valid,
 input wire[15:0]ch1,ch2,ch3,ch7,pval,ival,input wire sample_update,position_update,height_update,inject_error,
 input wire[31:0]position_dt,position_age,
 input wire signed[31:0]vx,vy,height,vz,ax,ay,az,input wire signed[15:0]yaw,output wire[449:0]public_out);
 wire parameter_boundary,mbusy,mdone,merror,dbusy,ddone,derror;wire signed[63:0]mresult,dresult;
  wire [0:0] requested;
 wire [0:0] ready;
 wire [0:0] active;
 wire [0:0] height_requested;
 wire [0:0] height_ready;
 wire [0:0] height_active;
 wire [0:0] auto_takeoff;
 wire [15:0] reason;
 wire [15:0] height_reason;
 wire [15:0] collective_target_us;
 wire [15:0] roll_target;
 wire [15:0] pitch_target;
 wire [15:0] throttle_delta;
 wire [31:0] requested_climb_mmps;
 wire [31:0] target_height_mm;
 wire [17:0] pilot_norm_x;
 wire [17:0] pilot_norm_y;
 wire [0:0] pilot_norm_update;
 wire [0:0] pilot_norm_valid;
 wire [15:0] pilot_norm_dt_us;
 wire [0:0] math_mul_start;
 wire [0:0] math_mul_cancel;
 wire [63:0] math_mul_a;
 wire [63:0] math_mul_b;
 wire [0:0] math_div_start;
 wire [0:0] math_div_cancel;
 wire [63:0] math_div_numerator;
 wire [31:0] math_div_denominator;
 mtf_xyz_hold_control_idle_base #(.CAL_MASK(8'hff),.VELOCITY_FRAC_BITS(16))dut(
  .clk(clk),.rst_n(rst_n),.origin_reset(origin),.rc_valid(rc_valid),.channel_count(4'd8),
 .ch1(ch1),.ch2(ch2),.ch3(ch3),.ch4(16'd1500),.ch7(ch7),.xy_p_value(pval),.xy_i_value(ival),.parameter_boundary(parameter_boundary),
 .enabled(enabled),.taking_off(taking_off),.position_valid(sensor_valid),.height_valid(sensor_valid),
 .position_update(position_update),.height_update(height_update),.sample_update(sample_update),.sample_dt_us(32'd1000),
 .position_age(position_age),.position_dt_us(position_dt),.x_q8(32'sd0),.y_q8(32'sd0),.vx(vx),.vy(vy),.height_mm(height),.vz(vz),.yaw_cdeg(yaw),
 .acc_valid(sensor_valid),.ax_mmps2(ax),.ay_mmps2(ay),.az_mmps2(az),.collective_us(16'd1500),
 .math_mul_busy(mbusy),.math_mul_done(mdone),.math_mul_result(mresult),
 .math_div_busy(dbusy),.math_div_done(ddone),.math_div_error(derror||inject_error),.math_div_result(dresult),
 .requested(requested),.ready(ready),.active(active),.height_requested(height_requested),.height_ready(height_ready),.height_active(height_active),.auto_takeoff(auto_takeoff),.reason(reason),.height_reason(height_reason),.collective_target_us(collective_target_us),.roll_target(roll_target),.pitch_target(pitch_target),.throttle_delta(throttle_delta),.requested_climb_mmps(requested_climb_mmps),.target_height_mm(target_height_mm),.pilot_norm_x(pilot_norm_x),.pilot_norm_y(pilot_norm_y),.pilot_norm_update(pilot_norm_update),.pilot_norm_valid(pilot_norm_valid),.pilot_norm_dt_us(pilot_norm_dt_us),.math_mul_start(math_mul_start),.math_mul_cancel(math_mul_cancel),.math_mul_a(math_mul_a),.math_mul_b(math_mul_b),.math_div_start(math_div_start),.math_div_cancel(math_div_cancel),.math_div_numerator(math_div_numerator),.math_div_denominator(math_div_denominator));
 assign public_out={requested,ready,active,height_requested,height_ready,height_active,auto_takeoff,reason,height_reason,collective_target_us,roll_target,pitch_target,throttle_delta,requested_climb_mmps,target_height_mm,pilot_norm_x,pilot_norm_y,pilot_norm_update,pilot_norm_valid,pilot_norm_dt_us,math_mul_start,math_mul_cancel,math_mul_a,math_mul_b,math_div_start,math_div_cancel,math_div_numerator,math_div_denominator,parameter_boundary};
 nav_math_service #(.CLIENTS(1),.DIVIDE(0))mservice(.clk(clk),.rst_n(rst_n),.request(math_mul_start),.cancel(math_mul_cancel),
 .operand_a(math_mul_a),.operand_b(math_mul_b),.busy(mbusy),.done(mdone),.error(merror),.result(mresult),.grant());
 nav_math_service #(.CLIENTS(1),.DIVIDE(1))dservice(.clk(clk),.rst_n(rst_n),.request(math_div_start),.cancel(math_div_cancel),
 .operand_a(math_div_numerator),.operand_b({32'd0,math_div_denominator}),.busy(dbusy),.done(ddone),.error(derror),.result(dresult),.grant());
 endmodule
