// B0AA single position mode: shared XYZ arithmetic retained; joint epoch/entry.
`timescale 1ns/1ps
// ANO Tech Quadrotor_TM_V1 numerical port:Loc/AltCtrl, Flight_State_Task.
// World X initial-forward,Y initial-right,Z up. mm Q8 position,mm/s velocity,
// mm/s^2 linear acceleration; XY PI/filter in heading-aligned body frame.
// Source unchanged defaults:Pxy=.15,Ixy=.10,Dxy=0,FFxy=.02;Pz=2,Iz=1,
// z acceleration lead=.05s,heightP=1,captured motorunit bias,850 max,FINAL_P=.35.
// One source motorunit=one us above1000us. HighCH7=one joint XYZ position mode;
// low/mid=manual self-level. New relative-positionP1/s outer loop is an explicit
// project adaptation (the original OF branch only controls velocity).
// Source OF speed bound=clip(1.5*height_cm,50,150)cm/s.
// Source throttle deadzone50us,.0023 normalization,.5 LPF at1ms,
// +350/-250cm/s speeds,.8cm/s per1ms slew,.6 vertical speed feedforward.
// No source one-key takeoff or implicit low-throttle disarm is invoked;
// SWA remains the project's manual arm/stop. Height entry requires centered
// throttle and seeds measured height/current collective for bumpless switching.
module mtf_xyz_hold_control #(
 parameter integer ENTRY_TICKS=10000000,CLK_HZ=50000000,
 parameter [7:0] CAL_MASK=0,
 parameter integer VELOCITY_FRAC_BITS=0,
 parameter integer MAX_ANGLE=1200,MAX_DELTA_US=1000,
 parameter integer POSITION_KP_Q16=65536
)(
 input wire clk,rst_n,origin_reset,rc_valid,input wire [3:0] channel_count,
 input wire [15:0] ch1,ch2,ch3,ch4,ch7,
 input wire enabled,position_valid,height_valid,position_update,height_update,
 input wire sample_update,input wire [31:0] sample_dt_us,
 input wire [31:0] position_age,position_dt_us,
 input wire signed [31:0] x_q8,y_q8,vx,vy,height_mm,vz,
 input wire signed [15:0] yaw_cdeg,
 input wire acc_valid,input wire signed [31:0] ax_mmps2,ay_mmps2,az_mmps2,
 input wire [15:0] collective_us,
 output wire requested,ready,active,height_requested,height_ready,height_active,
 output reg [15:0] reason,height_reason,
 output reg [15:0] collective_target_us,
 output reg signed [15:0] roll_target,pitch_target,throttle_delta,
 output reg signed [31:0] requested_climb_mmps,target_height_mm,
 output wire math_mul_start,math_mul_cancel,
 output wire signed [63:0] math_mul_a,math_mul_b,
 input wire math_mul_busy,math_mul_done,
 input wire signed [63:0] math_mul_result,
 output wire math_div_start,math_div_cancel,
 output wire signed [63:0] math_div_numerator,
 output wire [31:0] math_div_denominator,
 input wire math_div_busy,math_div_done,math_div_error,
 input wire signed [63:0] math_div_result
);
 // Width trial: only stored representations change. Original names remain
 // signed64 aliases so every operation retains the original sizing/sign.
 function signed [63:0] keep64;
 input signed [63:0] a;begin keep64=a;end endfunction
 localparam AGE_LIMIT=CLK_HZ/10;
 localparam signed [31:0] INPUT_V_LIMIT=32'sd10000<<<VELOCITY_FRAC_BITS;
 initial if(VELOCITY_FRAC_BITS!=0 && VELOCITY_FRAC_BITS!=16)$error("Unsupported velocity fraction bits");
 reg tracking=0,xy_tracking=0,command_seen=0,height_command_seen=0,blocked=0,xy_blocked=0;
 reg [15:0] fault_reason=0;
 reg [31:0] prepare=0,xy_prepare=0,command_age=32'hffffffff,height_command_age=32'hffffffff;
 reg height_due=0,position_due=0,work_xy=0;
 assign requested=rc_valid && channel_count>=7 && ch7>=1800 && ch7<=2200;
 assign height_requested=requested;
 wire manual_selection=rc_valid && channel_count>=7 && ch7>=900 && ch7<=1700;
 wire centered=ch1>=1450 && ch1<=1550 && ch2>=1450 && ch2<=1550 && ch4>=1450 && ch4<=1550;
 wire throttle_centered=ch3>=1450 && ch3<=1550;
 // Numeric eligibility only: capture, then compare in a separate clock.
 // In particular upstream signed world-Y negation cannot share one path
 // with32-bit bounds, mode logic and the motor/telemetry consumers.
 // Numeric out-of-range revocation is at most2clocks (40ns at50MHz).
 // Live transport/sensor valid, RC/SWA/arm, pilot intent and age checks
 // remain combinational below; none of those emergency masks are delayed.
 reg [15:0] check_collective=0,check_ch3=0;
 reg signed [31:0] check_height=0,check_vz=0,check_az=0;
 reg signed [31:0] check_vx=0,check_vy=0,check_ax=0,check_ay=0;
 reg signed [15:0] check_yaw=0;
 reg hbounds_q=0,xybounds_q=0;
 always @(posedge clk)begin
  if(!rst_n)begin
   check_collective<=0;check_ch3<=0;check_height<=0;check_vz<=0;check_az<=0;
   check_vx<=0;check_vy<=0;check_ax<=0;check_ay<=0;check_yaw<=0;
   hbounds_q<=0;xybounds_q<=0;
  end else begin
   check_collective<=collective_us;check_ch3<=ch3;check_height<=height_mm;check_vz<=vz;check_az<=az_mmps2;
   check_vx<=vx;check_vy<=vy;check_ax<=ax_mmps2;check_ay<=ay_mmps2;check_yaw<=yaw_cdeg;
   hbounds_q<=check_collective>=1000 && check_collective<=2000 && check_ch3>=900 && check_ch3<=2200 && check_height>=0 && check_height<=5000 && check_vz>=-INPUT_V_LIMIT && check_vz<=INPUT_V_LIMIT && check_az>=-30000 && check_az<=30000;
   xybounds_q<=check_vx>=-INPUT_V_LIMIT && check_vx<=INPUT_V_LIMIT && check_vy>=-INPUT_V_LIMIT && check_vy<=INPUT_V_LIMIT && check_ax>=-30000 && check_ax<=30000 && check_ay>=-30000 && check_ay<=30000 && check_yaw>=-18000 && check_yaw<=18000;
  end
 end
 wire z_stick_busy,z_stick_fault;
 wire signed [17:0] z_norm_q16;
 wire signed [28:0] z_speed_q16;
 // Public readiness is joint numeric/age qualification only, not RC/arming.
 // Keep the Z numeric term independent to avoid ready<->height_ready feedback.
 wire z_numeric_ready=(CAL_MASK &8'h98)==8'h98 && height_valid && acc_valid && hbounds_q && !z_stick_fault;
 assign ready=CAL_MASK==8'hff && position_valid && z_numeric_ready && xybounds_q && position_age<AGE_LIMIT && !origin_reset;
 assign height_ready=ready;
 wire command_stale=(command_seen && command_age>=AGE_LIMIT) || (height_command_seen && height_command_age>=AGE_LIMIT);
 wire cancel_now=!requested || !enabled || !ready || !centered || blocked || xy_blocked || command_stale;
 ano_z_stick z_stick(.clk(clk),.rst_n(rst_n),.enabled(tracking && !cancel_now),
  .sample_update(sample_update),.sample_dt_us(sample_dt_us),.ch3(ch3),
  .norm_q16(z_norm_q16),.speed_q16(z_speed_q16),.busy(z_stick_busy),.update(),.fault(z_stick_fault));
 wire xy_cancel_now=cancel_now || !tracking;
 assign active=requested && enabled && ready && centered && tracking && xy_tracking && command_seen && height_command_seen && !command_stale && !blocked && !xy_blocked;
 assign height_active=active;
 reg cancel=1,xy_cancel=1;
 always @(posedge clk) if(!rst_n)begin cancel<=1;xy_cancel<=1;end else begin cancel<=cancel_now;xy_cancel<=xy_cancel_now;end
 wire math_cancel=cancel || origin_reset || work_xy && xy_cancel;
 reg signed [31:0] target_x=0,target_y=0;
 reg signed [49-1:0] target_z_q16_store=0;
 reg signed [48-1:0] height_feedback_old_store=0;
 reg signed [27-1:0] ix_store=0;
 reg signed [27-1:0] iy_store=0;
 reg signed [33-1:0] iz_store=0;
 reg signed [33-1:0] bias_store=0;
 reg signed [33-1:0] afx_store=0;
 reg signed [33-1:0] afy_store=0;
 reg signed [32-1:0] afz_store=0;
 reg signed [29-1:0] sx_store=0;
 reg signed [29-1:0] sy_store=0;
 reg signed [28-1:0] world_sx_store=0;
 reg signed [28-1:0] world_sy_store=0;
 reg signed [32-1:0] world_ax_store=0;
 reg signed [32-1:0] world_ay_store=0;
 reg signed [32-1:0] ex_store=0;
 reg signed [32-1:0] ey_store=0;
 reg signed [32-1:0] fixx_store=0;
 reg signed [32-1:0] fixy_store=0;
 reg signed [32-1:0] ux_store=0;
 reg signed [32-1:0] uy_store=0;
 reg signed [33-1:0] hx_store=0;
 reg signed [33-1:0] hy_store=0;
 reg signed [31-1:0] sample_vx_store=0;
 reg signed [31-1:0] sample_vy_store=0;
 reg signed [17-1:0] alpha_store=0;
 reg signed [31-1:0] exz_store=0;
 reg signed [28-1:0] vsz_store=0;
 reg signed [29-1:0] speed_z_tick_store=0;
 reg signed [27-1:0] collective_q16_store=0;
 reg signed [31:0] pending_h=0,pending_vz=0,pending_az=0;
 reg signed [31:0] held_h=0,held_az=0;
 reg signed [31:0] px=0,py=0,pvx=0,pvy=0,pax=0,pay=0,ph=0;
 reg signed [15:0] pyaw=0;reg [31:0] pdt=20000;
 reg signed [24-1:0] angle_store=0;
 reg signed [33-1:0] rot_tmp_store=0;
 reg signed [33-1:0] position_ex_store=0;
 reg signed [33-1:0] position_ey_store=0;
 reg signed [((POSITION_KP_Q16==65536)?49:64)-1:0] position_px_store=0;
 reg signed [((POSITION_KP_Q16==65536)?49:64)-1:0] position_py_store=0;
 reg signed [((POSITION_KP_Q16==65536)?41:64)-1:0] position_qx_store=0;
 reg signed [((POSITION_KP_Q16==65536)?41:64)-1:0] position_qy_store=0;
 reg signed [31:0] publish_roll=0,publish_pitch=0,publish_height=0,publish_speed=0,publish_collective=0,publish_delta=0;
 reg [31:0] dt=20000,base=1000;
 wire signed [63:0] target_z_q16={{15{target_z_q16_store[48]}},target_z_q16_store};
 wire signed [63:0] height_feedback_old={{16{height_feedback_old_store[47]}},height_feedback_old_store};
 wire signed [63:0] ix={{37{ix_store[26]}},ix_store};
 wire signed [63:0] iy={{37{iy_store[26]}},iy_store};
 wire signed [63:0] iz={{31{iz_store[32]}},iz_store};
 wire signed [63:0] bias={{31{bias_store[32]}},bias_store};
 wire signed [63:0] afx={{31{afx_store[32]}},afx_store};
 wire signed [63:0] afy={{31{afy_store[32]}},afy_store};
 wire signed [63:0] afz={{32{afz_store[31]}},afz_store};
 wire signed [63:0] sx={{35{sx_store[28]}},sx_store};
 wire signed [63:0] sy={{35{sy_store[28]}},sy_store};
 wire signed [63:0] world_sx={{36{world_sx_store[27]}},world_sx_store};
 wire signed [63:0] world_sy={{36{world_sy_store[27]}},world_sy_store};
 wire signed [63:0] world_ax={{32{world_ax_store[31]}},world_ax_store};
 wire signed [63:0] world_ay={{32{world_ay_store[31]}},world_ay_store};
 wire signed [63:0] ex={{32{ex_store[31]}},ex_store};
 wire signed [63:0] ey={{32{ey_store[31]}},ey_store};
 wire signed [63:0] fixx={{32{fixx_store[31]}},fixx_store};
 wire signed [63:0] fixy={{32{fixy_store[31]}},fixy_store};
 wire signed [63:0] ux={{32{ux_store[31]}},ux_store};
 wire signed [63:0] uy={{32{uy_store[31]}},uy_store};
 wire signed [63:0] hx={{31{hx_store[32]}},hx_store};
 wire signed [63:0] hy={{31{hy_store[32]}},hy_store};
 wire signed [63:0] sample_vx={{33{sample_vx_store[30]}},sample_vx_store};
 wire signed [63:0] sample_vy={{33{sample_vy_store[30]}},sample_vy_store};
 wire signed [63:0] alpha={{47{alpha_store[16]}},alpha_store};
 wire signed [63:0] exz={{33{exz_store[30]}},exz_store};
 wire signed [63:0] vsz={{36{vsz_store[27]}},vsz_store};
 wire signed [63:0] norm_lpf={{46{z_norm_q16[17]}},z_norm_q16};
 wire signed [63:0] speed_z={{35{z_speed_q16[28]}},z_speed_q16};
 wire signed [63:0] speed_z_tick={{35{speed_z_tick_store[28]}},speed_z_tick_store};
 wire signed [63:0] collective_q16={{37{collective_q16_store[26]}},collective_q16_store};
 wire signed [63:0] angle={{40{angle_store[23]}},angle_store};
 wire signed [63:0] rot_tmp={{31{rot_tmp_store[32]}},rot_tmp_store};
 wire signed [63:0] position_ex={{31{position_ex_store[32]}},position_ex_store};
 wire signed [63:0] position_ey={{31{position_ey_store[32]}},position_ey_store};
 wire signed [63:0] position_px=$signed(position_px_store);
 wire signed [63:0] position_py=$signed(position_py_store);
 wire signed [63:0] position_qx=$signed(position_qx_store);
 wire signed [63:0] position_qy=$signed(position_qy_store);
 wire signed [63:0] horizontal_speed_limit_q16=clip($signed(ph)*64'sd98304,64'sd32768000,64'sd98304000);
 reg [7:0] state=0,return_state=0;
 reg mul_start=0,div_start=0,trig_start=0;
 reg signed [63:0] ma=0;
 reg signed [63:0] mb=0;
 reg signed [63:0] num=0;
 reg signed [63:0] value=0;
 // Split the original signed64 add-and-clip path without narrowing its
 // arithmetic. Four16-bit comparisons preserve signed lexicographic order;
 // this adds only2clocks to each11ms height calculation, not to safety gates.
 reg signed [63:0] target_sum_q=0,target_lo_q=0,target_hi_q=0;
 reg [3:0] target_lt_lo_q=0,target_eq_lo_q=0,target_gt_hi_q=0,target_eq_hi_q=0;
 wire target_below_lo=target_lt_lo_q[3] || (target_eq_lo_q[3] &&
  (target_lt_lo_q[2] || (target_eq_lo_q[2] &&
  (target_lt_lo_q[1] || (target_eq_lo_q[1] && target_lt_lo_q[0])))));
 wire target_above_hi=target_gt_hi_q[3] || (target_eq_hi_q[3] &&
  (target_gt_hi_q[2] || (target_eq_hi_q[2] &&
  (target_gt_hi_q[1] || (target_eq_hi_q[1] && target_gt_hi_q[0])))));
 reg [31:0] den=1,pending_den=1;
 wire md,mbusy,dd,dbusy,derr,trig_done,trig_busy;wire signed [63:0] product,quotient;wire signed [17:0] sn,cs;
 assign math_mul_start=mul_start;assign math_mul_cancel=math_cancel;
 assign math_mul_a=ma;assign math_mul_b=mb;
 assign mbusy=math_mul_busy;assign md=math_mul_done;assign product=math_mul_result;
 assign math_div_start=div_start;assign math_div_cancel=math_cancel;
 assign math_div_numerator=num;assign math_div_denominator=den;
 assign dbusy=math_div_busy;assign dd=math_div_done;assign derr=math_div_error;assign quotient=math_div_result;
 position_sincos t(.clk(clk),.rst_n(rst_n),.start(trig_start),.cancel(math_cancel),.angle_q20(angle[31:0]),.busy(trig_busy),.done(trig_done),.sin_q16(sn),.cos_q16(cs));
 function signed [63:0] clip;
 input signed [63:0] a,lo,hi;begin clip=a<lo ? lo:a>hi ? hi:a;end endfunction
 function signed [63:0] integer_q16;
 input signed [63:0] a;begin integer_q16=(a>>>16)+(a[63] && |a[15:0] ?64'sd1:64'sd0);end endfunction
 function signed [63:0] integer_q8;
 input signed [63:0] a;begin integer_q8=(a>>>8)+(a[63] && |a[7:0] ?64'sd1:64'sd0);end endfunction
 task calc;
 input signed [63:0] a,b;input [31:0] denominator;input [7:0] dest;
 begin ma<=a;mb<=b;pending_den<=denominator;return_state<=dest;mul_start<=1;state<=100;end endtask
 initial begin reason=1;height_reason=1;roll_target=0;pitch_target=0;throttle_delta=0;collective_target_us=1000;requested_climb_mmps=0;target_height_mm=0;end
 always @(posedge clk) begin
  mul_start<=0;div_start<=0;trig_start<=0;
  if(!rst_n)begin
   state<=0;tracking<=0;xy_tracking<=0;command_seen<=0;height_command_seen<=0;blocked<=0;xy_blocked<=0;
   prepare<=0;xy_prepare<=0;height_due<=0;position_due<=0;work_xy<=0;command_age<=32'hffffffff;height_command_age<=32'hffffffff;fault_reason<=0;
   target_x<=0;target_y<=0;height_feedback_old_store<=keep64(0);
   ix_store<=keep64(0);iy_store<=keep64(0);iz_store<=keep64(0);bias_store<=keep64(0);afx_store<=keep64(0);afy_store<=keep64(0);afz_store<=keep64(0);vsz_store<=keep64(0);target_z_q16_store<=keep64(0);
   roll_target<=0;pitch_target<=0;throttle_delta<=0;collective_target_us<=1000;reason<=1;height_reason<=1;requested_climb_mmps<=0;target_height_mm<=0;
  end else begin
   if(command_age!=32'hffffffff)command_age<=command_age+1'b1;
   if(height_command_age!=32'hffffffff)height_command_age<=height_command_age+1'b1;
   // An observed origin/source/RC/arm/pilot revoke invalidates ALL targets.
   // Staying high cannot resurrect an old point; valid low/mid acknowledges it.
   if(origin_reset)begin blocked<=1;xy_blocked<=1;fault_reason<=1024;end
   else if(manual_selection)begin blocked<=0;xy_blocked<=0;fault_reason<=0;end
   else if((requested && (!enabled || !ready || !centered || command_stale)) ||
           ((tracking || prepare!=0) && !requested))begin
    blocked<=1;xy_blocked<=1;
    fault_reason<=!requested ?1:!enabled ?2:!ready ?4:!centered ?16:32;
   end
   if(cancel || origin_reset || blocked || xy_blocked)begin
    state<=0;tracking<=0;xy_tracking<=0;command_seen<=0;height_command_seen<=0;prepare<=0;xy_prepare<=0;height_due<=0;position_due<=0;work_xy<=0;
    ix_store<=keep64(0);iy_store<=keep64(0);iz_store<=keep64(0);bias_store<=keep64(0);afx_store<=keep64(0);afy_store<=keep64(0);afz_store<=keep64(0);vsz_store<=keep64(0);target_z_q16_store<=keep64(0);
    target_x<=0;target_y<=0;height_feedback_old_store<=keep64(0);
    roll_target<=0;pitch_target<=0;throttle_delta<=0;collective_target_us<=1000;requested_climb_mmps<=0;target_height_mm<=0;
    reason<=origin_reset ?1024:!requested ?1:!enabled ?2:!ready ?4:!centered ?16:(blocked || xy_blocked) ?(fault_reason|16'd32):64;
    height_reason<=origin_reset ?1024:!requested ?1:!enabled ?2:!ready ?8:!centered ?16:(blocked || xy_blocked) ?(fault_reason|16'd32):64;
   end else if(!tracking)begin
    if(!throttle_centered)begin prepare<=0;height_reason<=256;end
    else if(prepare<ENTRY_TICKS)prepare<=prepare+1'b1;
    else if(position_update && position_dt_us>=1000 && position_dt_us<=100000)begin
     target_z_q16_store<=keep64($signed(height_mm)*65536);height_feedback_old_store<=keep64($signed(height_mm)*65536);target_height_mm<=height_mm;
     target_x<=x_q8;target_y<=y_q8;tracking<=1;xy_tracking<=1;
     command_seen<=0;height_command_seen<=0;command_age<=32'hffffffff;height_command_age<=32'hffffffff;
     bias_store<=keep64(($signed({1'b0,collective_us})-1000)*65536);reason<=64;height_reason<=64;
    end
   end else begin
    if(height_update)begin
     if(height_due)begin blocked<=1;xy_blocked<=1;fault_reason<=128;height_reason<=128;end
     else begin height_due<=1;pending_h<=height_mm;pending_vz<=vz;pending_az<=az_mmps2;end
    end
    // Joint entry above already captured X/Y/Z. There is no second XY dwell
    // or independently active Z-only mode behind high CH7.
    if(position_update)begin
      if(position_due || position_dt_us<1000 || position_dt_us>100000)begin blocked<=1;xy_blocked<=1;fault_reason<=128;reason<=128;end
     else begin position_due<=1;px<=x_q8;py<=y_q8;pvx<=vx;pvy<=vy;pax<=ax_mmps2;pay<=ay_mmps2;ph<=height_mm;pyaw<=yaw_cdeg;pdt<=position_dt_us;end
    end
    if(work_xy && xy_cancel)begin state<=0;work_xy<=0;end
    else case(state)
     0:if(height_due && !z_stick_busy && !sample_update)begin
      height_due<=0;work_xy<=0;base<=collective_us;sample_vx_store<=keep64(($signed({{32{pending_vz[31]}},pending_vz})<<<(16-VELOCITY_FRAC_BITS)));
      held_h<=pending_h;held_az<=pending_az;speed_z_tick_store<=keep64(speed_z);
      calc($signed(pending_az)*65536-afz,1,5,20);
     end else if(position_due && !xy_cancel)begin
      position_due<=0;work_xy<=1;
      position_ex_store<=keep64($signed(target_x)-$signed(px));position_ey_store<=keep64($signed(target_y)-$signed(py));
      sample_vx_store<=keep64(($signed({{32{pvx[31]}},pvx})<<<(16-VELOCITY_FRAC_BITS)));sample_vy_store<=keep64(($signed({{32{pvy[31]}},pvy})<<<(16-VELOCITY_FRAC_BITS)));
      world_ax_store<=keep64($signed(pax)*65536);world_ay_store<=keep64($signed(pay)*65536);dt<=pdt;angle_store<=keep64($signed(pyaw)*64'sd183);
      state<=43;
     end
     43:begin position_px_store<=keep64(position_ex*POSITION_KP_Q16);position_py_store<=keep64(position_ey*POSITION_KP_Q16);state<=44;end
     44:begin position_qx_store<=keep64(integer_q8(position_px));position_qy_store<=keep64(integer_q8(position_py));state<=45;end
     45:begin world_sx_store<=keep64(clip(position_qx,-horizontal_speed_limit_q16,horizontal_speed_limit_q16));world_sy_store<=keep64(clip(position_qy,-horizontal_speed_limit_q16,horizontal_speed_limit_q16));calc($signed({1'b0,dt})*314,65536,10000000+dt*314,1);end
     1:begin alpha_store<=keep64(value);trig_start<=1;state<=30;end
     2:begin afx_store<=keep64(afx+value);calc(hy-afy,alpha,65536,3);end
     3:begin afy_store<=keep64(afy+value);calc(afx,3,100,4);end
     4:begin ex_store<=keep64(fixx-value);calc(afy,3,100,5);end
     5:begin ey_store<=keep64(fixy-value);calc(clip(fixx,-32768000,32768000),$signed({1'b0,dt}),1000000,6);end
     6:begin ix_store<=keep64(clip(ix+value,-65536000,65536000));calc(clip(fixy,-32768000,32768000),$signed({1'b0,dt}),1000000,7);end
     7:begin iy_store<=keep64(clip(iy+value,-65536000,65536000));calc(ex,15,10,8);end
     8:begin ux_store<=keep64(value+ix);calc(ey,15,10,9);end
     9:begin uy_store<=keep64(value+iy);calc(sx,1,5,10);end
     10:begin ux_store<=keep64(ux+value);calc(sy,1,5,11);end
     11:begin uy_store<=keep64(uy+value);state<=17;end
     17:begin
      // Original Y-left roll=-Y; adapting Y-right makes project roll=+Y.
      publish_roll<=integer_q16(uy);publish_pitch<=integer_q16(-ux);state<=46;
     end
     46:begin
      roll_target<=clip(publish_roll,-MAX_ANGLE,MAX_ANGLE);
      pitch_target<=clip(publish_pitch,-MAX_ANGLE,MAX_ANGLE);
      command_age<=0;command_seen<=1;reason<=0;state<=0;work_xy<=0;
     end
     // Source OF PI and5Hz acceleration LPF operate in heading-aligned body
     // HXYZ, not inertial-world axes. Rotate before filtering/integrating so
     // yaw changes cannot rotate old integral/filter state into new axes.
     30:if(trig_done) calc(world_sx,cs,65536,31);
     31:begin rot_tmp_store<=keep64(value);calc(world_sy,sn,65536,32);end
     32:begin sx_store<=keep64(rot_tmp+value);calc(world_sx,sn,65536,33);end
     33:begin rot_tmp_store<=keep64(value);calc(world_sy,cs,65536,34);end
     34:begin sy_store<=keep64(-rot_tmp+value);calc(world_sx-sample_vx,cs,65536,35);end
     35:begin rot_tmp_store<=keep64(value);calc(world_sy-sample_vy,sn,65536,36);end
     36:begin fixx_store<=keep64(rot_tmp+value);calc(world_sx-sample_vx,sn,65536,37);end
     37:begin rot_tmp_store<=keep64(value);calc(world_sy-sample_vy,cs,65536,38);end
     38:begin fixy_store<=keep64(-rot_tmp+value);calc(world_ax,cs,65536,39);end
     39:begin rot_tmp_store<=keep64(value);calc(world_ay,sn,65536,40);end
     40:begin hx_store<=keep64(rot_tmp+value);calc(world_ax,sn,65536,41);end
     41:begin rot_tmp_store<=keep64(value);calc(world_ay,cs,65536,42);end
     42:begin hy_store<=keep64(-rot_tmp+value);calc(hx-afx,alpha,65536,2);end
     // Alt1 then Alt2 remain11ms; speed_z_tick is the completed1ms stick state.
     20:begin afz_store<=keep64(afz+value);calc(afz+value,1,20,21);end
     21:begin exz_store<=keep64(vsz-sample_vx-value);calc(speed_z_tick,3,5,53);end
     53:begin exz_store<=keep64(exz+value);calc(clip(exz+value,-65536000,65536000),11,10000,22);end
     22:begin
      iz_store<=keep64(clip(iz+value,-(131072000-bias),131072000-bias));
      calc(22937600-bias,6908,106908,23);
     end
     // B0AC: keep the original shared calculation/FSM schedule.
     // Its default350 relaxation result is intentionally discarded;
     // the integer collective captured at entry remains this epoch bias.
     23:begin calc(exz,1,5,24);end
     24:begin collective_q16_store<=keep64(clip(value+iz+bias,0,55705600));calc(speed_z_tick,11,1000,54);end
     54:begin
      target_sum_q<=target_z_q16+value;
      target_lo_q<=height_feedback_old-64'sd131072000;
      target_hi_q<=height_feedback_old+64'sd131072000;
      state<=58;
     end
     58:begin
      target_lt_lo_q<={$signed(target_sum_q[63:48])<$signed(target_lo_q[63:48]),
       target_sum_q[47:32]<target_lo_q[47:32],target_sum_q[31:16]<target_lo_q[31:16],target_sum_q[15:0]<target_lo_q[15:0]};
      target_eq_lo_q<={target_sum_q[63:48]==target_lo_q[63:48],target_sum_q[47:32]==target_lo_q[47:32],
       target_sum_q[31:16]==target_lo_q[31:16],target_sum_q[15:0]==target_lo_q[15:0]};
      target_gt_hi_q<={$signed(target_sum_q[63:48])>$signed(target_hi_q[63:48]),
       target_sum_q[47:32]>target_hi_q[47:32],target_sum_q[31:16]>target_hi_q[31:16],target_sum_q[15:0]>target_hi_q[15:0]};
      target_eq_hi_q<={target_sum_q[63:48]==target_hi_q[63:48],target_sum_q[47:32]==target_hi_q[47:32],
       target_sum_q[31:16]==target_hi_q[31:16],target_sum_q[15:0]==target_hi_q[15:0]};
      state<=59;
     end
     59:begin
      target_z_q16_store<=keep64(target_below_lo ? target_lo_q:target_above_hi ? target_hi_q:target_sum_q);
      state<=55;
     end
     55:begin
      vsz_store<=keep64(clip(target_z_q16-$signed(held_h)*65536,-98304000,98304000));
      height_feedback_old_store<=keep64($signed(held_h)*65536);publish_height<=integer_q16(target_z_q16);publish_speed<=integer_q16(speed_z_tick);publish_collective<=integer_q16(collective_q16);state<=57;
     end
     57:begin publish_delta<=1000+publish_collective-$signed({1'b0,base});state<=25;end
     25:begin
      collective_target_us<=1000+publish_collective;
      throttle_delta<=clip(publish_delta,-MAX_DELTA_US,MAX_DELTA_US);
      height_command_seen<=1;height_command_age<=0;height_reason<=0;requested_climb_mmps<=publish_speed;target_height_mm<=publish_height;state<=0;
     end
     100:if(md)begin num<=product;den<=pending_den;div_start<=1;state<=101;end
     101:if(dd)begin
      if(derr)begin blocked<=1;xy_blocked<=1;fault_reason<=512;reason<=512;height_reason<=512;state<=0;end
      else begin value<=quotient;state<=return_state;end
     end
     default:state<=0;
    endcase
   end
  end
 end
endmodule
