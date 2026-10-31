`timescale 1ns/1ps
// 原程序手动 Loc_1level_Ctrl（20 毫秒）到 Att_2level_Ctrl 微调（6 毫秒）的实现。
// Flight_State_Task 共用的一组低通、长度限制后摇杆值由
// ano_xy_stick 输入；此处不重复设置滤波器、开方器或 64 位算术引擎。
// 俯仰输出保持翻转前符号，与 flight_core 既有接口相符。
// norm_roll/pitch 为范围 ±1 的 Q16 摇杆；norm_dt_us 为微秒，outer_dt_ticks 为 50 MHz 时钟拍。
// 输入反馈、定位覆盖和输出目标均为百分之一度；snapshot 与本次输出保留同一外环时刻的反馈。
// 20 毫秒累计周期、±25 度角度上限、±1 度微调上限为本模块固定值；busy/故障均由事务状态产生。
module ano_manual_angles(
 input wire clk,rst_n,sample_update,norm_valid,outer_update,enabled,att_stab,
 input wire signed [17:0] norm_roll_q16,norm_pitch_q16,
 input wire [15:0] norm_dt_us,
 input wire [31:0] outer_dt_ticks,
 input wire signed [15:0] roll_cdeg,pitch_cdeg,
 input wire loc_override,input wire signed [15:0] loc_roll_cdeg,loc_pitch_cdeg,
 output wire signed [15:0] manual_roll_cdeg,manual_pitch_cdeg,
 output reg signed [15:0] snapshot_roll_cdeg=0,
 output reg signed [15:0] snapshot_pitch_cdeg=0,
 output reg update=0,output wire busy,output reg [7:0] fault=0
) /* synthesis syn_dspstyle="logic" */;
 // WINDOW、TRIM_LIMIT、ANGLE_LIMIT 依次为 Q16 百分之一度的 ±5 度窗口、±1 度微调和 ±25 度目标。
 localparam signed [31:0] WINDOW=32768000,TRIM_LIMIT=6553600,ANGLE_LIMIT=163840000;
 reg [3:0] state=0;
 reg norm_pending=0,outer_pending=0,pending_stab=0,pending_enabled=0,publish_allowed=0;
 reg signed [17:0] pending_nr=0,pending_np=0,held_nr=0,held_np=0;
 reg [15:0] pending_dt=0;
 reg [16:0] elapsed=0,time_sum=0;reg loc_due=0;
 reg signed [31:0] loc_r=0,loc_p=0,held_r=0,held_p=0;
 reg signed [23:0] tr=0,tp=0,next_tr=0,next_tp=0;
 reg signed [15:0] published_r=0,published_p=0,pending_roll_fb=0,pending_pitch_fb=0;
 reg [8:0] compute_age=0;
 reg div_start=0;reg signed [35:0] numerator=0;
 wire div_done,div_error;wire signed [35:0] quotient;
 // 共享 36 位除法器把固定系数 3/2500 分拍执行，fault 非零即取消该算术事务。
 ano_xy_divide36 divider(.clk(clk),.rst_n(rst_n),.start(div_start),.cancel(fault!=0),
  .numerator(numerator),.denominator(17'd2500),.busy(),.done(div_done),.error(div_error),.quotient(quotient));
 assign busy=state!=0 || norm_pending || outer_pending;
 assign manual_roll_cdeg=enabled && fault==0 ?published_r:16'sd0;
 assign manual_pitch_cdeg=enabled && fault==0 ?published_p:16'sd0;
 wire signed [31:0] roll_sum=held_r+$signed(tr),pitch_sum=held_p+$signed(tp);
 function signed [23:0] trim_clip;
 input signed [35:0] x;
 begin trim_clip=x>TRIM_LIMIT ?TRIM_LIMIT:x< -TRIM_LIMIT ?-TRIM_LIMIT:x[23:0];end endfunction
 function signed [15:0] angle_integer;
 input signed [31:0] x;
 reg signed [31:0] a;
 begin
  a=x>ANGLE_LIMIT ?ANGLE_LIMIT:x< -ANGLE_LIMIT ?-ANGLE_LIMIT:x;
  angle_integer=(a>>>16)+(a[31] && |a[15:0] ?32'sd1:32'sd0);
 end endfunction
 always @(posedge clk)begin
  update<=0;div_start<=0;
  if(!rst_n)begin
   state<=0;norm_pending<=0;outer_pending<=0;elapsed<=0;time_sum<=0;
   loc_r<=0;loc_p<=0;tr<=0;tp<=0;next_tr<=0;next_tp<=0;
   published_r<=0;published_p<=0;fault<=0;compute_age<=0;publish_allowed<=0;
  end else if(!enabled && fault!=0)begin state<=0;norm_pending<=0;outer_pending<=0;fault<=0;published_r<=0;published_p<=0;end
  else if(fault!=0)begin state<=0;published_r<=0;published_p<=0;end
  else if(enabled && !norm_valid)begin fault<=8'h01;state<=0;published_r<=0;published_p<=0;end
  else begin
   // 忙时计时和输入待处理位检测重入、非法 dt 或摇杆范围；故障后公开角度置零，停用后才清故障。
   if(state==0)compute_age<=0;else if(compute_age==511)begin fault<=8'h04;state<=0;end else compute_age<=compute_age+1'b1;
   if(!enabled)publish_allowed<=0;
   if(sample_update)begin
    if(norm_pending || norm_dt_us==0 || norm_dt_us>60000 || !norm_valid ||
       norm_roll_q16< -65536 || norm_roll_q16>65536 || norm_pitch_q16< -65536 || norm_pitch_q16>65536)fault<=8'h02;
    else begin norm_pending<=1;pending_nr<=norm_roll_q16;pending_np<=norm_pitch_q16;pending_dt<=norm_dt_us;end
   end
   if(outer_update)begin
    if(outer_pending || outer_dt_ticks==0 || outer_dt_ticks>3000000)fault<=8'h08;
    else begin outer_pending<=1;pending_stab<=att_stab;pending_enabled<=enabled;pending_roll_fb<=roll_cdeg;pending_pitch_fb<=pitch_cdeg;end
   end
   case(state)
    // 外环回调优先处理已缓存的位置角及微调；摇杆样本则按累计微秒数触发 20 毫秒位置更新。
    0:if(outer_pending)begin
     outer_pending<=0;held_r<=loc_r;held_p<=loc_p;publish_allowed<=pending_enabled && enabled;
     next_tr<=tr;next_tp<=tp;state<=1;
    end else if(norm_pending)begin
     norm_pending<=0;held_nr<=pending_nr;held_np<=pending_np;
     time_sum<=elapsed+{1'b0,pending_dt};loc_due<=0;state<=8;
    end
    // 原调度器以固定 6 毫秒调用 Att_2level_Ctrl，因此微调积分系数
    // 为 0.2×0.006=3/2500；偏航和角速度控制仍使用各自的真实 dt 通路。
    1:if(!pending_stab)begin next_tr<=0;next_tp<=0;state<=5;end
      else if(roll_sum> -WINDOW && roll_sum<WINDOW)begin numerator<=$signed(held_r)*36'sd3;div_start<=1;state<=2;end
      else state<=3;
    2:if(div_done)begin if(div_error)fault<=8'h10;else next_tr<=trim_clip($signed(tr)+quotient);state<=3;end
    3:if(pitch_sum> -WINDOW && pitch_sum<WINDOW)begin numerator<=$signed(held_p)*36'sd3;div_start<=1;state<=4;end else state<=5;
    4:if(div_done)begin if(div_error)fault<=8'h10;else next_tp<=trim_clip($signed(tp)+quotient);state<=5;end
    // 完成两轴微调后统一限幅和发布；publish_allowed 防止停用前的旧事务在重新使能后暴露。
    5:begin
     tr<=next_tr;tp<=next_tp;
     published_r<=publish_allowed && enabled ?angle_integer(held_r+$signed(next_tr)):16'sd0;
     published_p<=publish_allowed && enabled ?angle_integer(held_p+$signed(next_tp)):16'sd0;
     snapshot_roll_cdeg<=pending_roll_fb;snapshot_pitch_cdeg<=pending_pitch_fb;update<=1;state<=0;
    end
    8:if(time_sum>=20000)begin time_sum<=time_sum-17'd20000;loc_due<=1;end
      else begin
       elapsed<=time_sum;
       if(loc_due)begin loc_r<=$signed(held_nr)*32'sd2500;loc_p<=$signed(held_np)*32'sd2500;end
       state<=0;
      end
    default:begin fault<=8'h20;state<=0;end
   endcase
   // loc_ctrl_1.out 是光流与手动分支共用的同一个原程序缓存。
   // 光流工作时保存其已完成角度；离开光流后，该缓存继续供二级姿态环使用，
   // 直到下一次 20 毫秒手动位置回调更新为止。
   if(loc_override)begin loc_r<=$signed(loc_roll_cdeg)*32'sd65536;loc_p<=-$signed(loc_pitch_cdeg)*32'sd65536;end
  end
 end
endmodule
