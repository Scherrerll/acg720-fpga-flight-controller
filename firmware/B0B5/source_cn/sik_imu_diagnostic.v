// 汇总 IMU 接收、姿态发布与保护事件，只生成 512 位诊断载荷，不参与电机控制。
// tick 为本地时钟计数，uptime_ms/event_time_ms 为毫秒；数据快照沿用对应有效事件的同拍字段。
`timescale 1ns/1ps
// SiK 只读摘要：hold 只冻结输出，源观测与诊断状态仍继续更新。
// 接口约定：raw_body/pose_body 在相邻有效事件之间保持各字段稳定。
module sik_imu_diagnostic #(parameter integer STARTUP_ONLY_SNAPSHOT_RESET=0)(
 input wire clk,rst_n,snapshot_hold,taking_off,
 input wire raw_valid,input wire [207:0] raw_body,
 input wire pose_valid,input wire [223:0] pose_body,input wire [31:0] pose_tick,
 input wire fault_valid,input wire [703:0] fault_body,input wire [31:0] fault_tick,
 input wire [31:0] clock_ticks,raw_count,pose_count,
 input wire [63:0] uptime_ms,input wire [31:0] build_id,
 input wire [15:0] event_sequence,input wire [63:0] event_time_ms,
 input wire [7:0] event_code,event_mask,event_imu,event_attitude,
 output reg [511:0] summary_body=0,output reg [31:0] summary_tick=0
);
 wire [31:0] accepted_count=raw_body[79:48],consumed_id=pose_body[223:192],held_dt=pose_body[191:160];
 reg [31:0] rejected_source_id=0;
 reg [7:0] rejected_reader=0,rejected_detail=0,rejected_flags=0;
 wire [7:0] pose_flags=pose_body[15:8],pose_fault=pose_body[7:0];
 reg pose_seen=0;reg [31:0] last_pose_tick=0,max_pose_gap=0;
 reg previous_taking_off=0,window_open=0,protection_seen=0;
 reg [15:0] previous_event_sequence=0;
 reg [31:0] protection_time=0;
 reg [7:0] protection_code=0,protection_mask=0,protection_imu=0,protection_attitude=0;
 wire new_window=taking_off && !previous_taking_off;
 wire new_protection=event_sequence!=previous_event_sequence &&
  event_code[5:4]==2'b11 && event_code[1:0]!=0 &&
  (window_open || new_window) && (!protection_seen || new_window);
 // 只记录已经完成的真实发布间隔；静默期间不推进姿态年龄诊断值。
 wire [31:0] pose_gap=pose_tick-last_pose_tick;
 wire [31:0] next_max_gap=pose_seen && pose_valid && pose_gap>max_pose_gap ?pose_gap:max_pose_gap;
 wire rejected_now=raw_valid && !raw_body[27];
 wire [31:0] next_accepted=raw_valid ?raw_body[79:48]:accepted_count;
 wire [31:0] next_rejected_id=rejected_now ?raw_body[207:176]:rejected_source_id;
 wire [7:0] next_reader=rejected_now ?raw_body[39:32]:rejected_reader;
 wire [7:0] next_detail=rejected_now ?raw_body[47:40]:rejected_detail;
 wire [7:0] next_raw_flags=rejected_now ?raw_body[31:24]:rejected_flags;
 wire [31:0] next_consumed=pose_valid ?pose_body[223:192]:consumed_id;
 wire [31:0] next_held_dt=pose_valid ?pose_body[191:160]:held_dt;
 wire [7:0] next_pose_flags=pose_valid ?pose_body[15:8]:pose_flags;
 wire [7:0] next_pose_fault=pose_valid ?pose_body[7:0]:pose_fault;
 // 诊断抽头在同一时钟沿清除冻结窗口，此处屏蔽非阻塞赋值更新前的旧元组。
 wire active_diagnostic_fault=fault_valid && !new_window;
 wire [31:0] first_tick=active_diagnostic_fault ?fault_tick:32'd0;
 wire [7:0] first_trigger=active_diagnostic_fault ?fault_body[703:696]:8'd0;
 wire [7:0] first_cause=active_diagnostic_fault ?fault_body[695:688]:8'd0;
 wire [7:0] first_attitude_fault=active_diagnostic_fault ?fault_body[687:680]:8'd0;
 wire [31:0] next_protection_time=new_protection ?event_time_ms[31:0]:new_window ?32'd0:protection_time;
 wire [7:0] next_protection_code=new_protection ?event_code:new_window ?8'd0:protection_code;
 wire [7:0] next_protection_mask=new_protection ?event_mask:new_window ?8'd0:protection_mask;
 wire [7:0] next_protection_imu=new_protection ?event_imu:new_window ?8'd0:protection_imu;
 wire [7:0] next_protection_attitude=new_protection ?event_attitude:new_window ?8'd0:protection_attitude;
 always @(posedge clk)begin
  if(!rst_n)begin
   rejected_source_id<=0;
   rejected_reader<=0;rejected_detail<=0;rejected_flags<=0;
   pose_seen<=0;last_pose_tick<=0;max_pose_gap<=0;
   previous_taking_off<=0;previous_event_sequence<=0;window_open<=0;protection_seen<=0;
   protection_time<=0;protection_code<=0;protection_mask<=0;protection_imu<=0;protection_attitude<=0;
  end else begin
   max_pose_gap<=next_max_gap;
   rejected_source_id<=next_rejected_id;
   rejected_reader<=next_reader;rejected_detail<=next_detail;rejected_flags<=next_raw_flags;
   
   if(pose_valid)begin pose_seen<=1;last_pose_tick<=pose_tick;end
   previous_taking_off<=taking_off;previous_event_sequence<=event_sequence;
   if(new_window)begin window_open<=1;protection_seen<=0;end
   if(new_protection)protection_seen<=1;
   protection_time<=next_protection_time;
   protection_code<=next_protection_code;protection_mask<=next_protection_mask;
   protection_imu<=next_protection_imu;protection_attitude<=next_protection_attitude;

  end
 end

 // 顶层已保证 boot 从零开始、饱和于 255 且不重新触发复位，
 // 因此可以选择仅启动时复位快照的模式。
 // 默认模式仍为其他调用方保留重复复位行为。
 always @(posedge clk)begin
  if(!STARTUP_ONLY_SNAPSHOT_RESET && !rst_n)begin
   summary_body<=0;summary_tick<=0;
  end else if(rst_n && !snapshot_hold)begin

    summary_tick<=clock_ticks;
    summary_body<={uptime_ms,build_id,raw_count,next_accepted,pose_count,next_rejected_id,
     next_max_gap,next_consumed,next_held_dt,first_tick,
     next_reader,next_detail,next_raw_flags,next_pose_flags,next_pose_fault,
     first_trigger,first_cause,first_attitude_fault,
     next_protection_time,next_protection_code,next_protection_mask,next_protection_imu,next_protection_attitude,32'd0};
  end
 end
endmodule
