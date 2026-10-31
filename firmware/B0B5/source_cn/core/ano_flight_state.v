`timescale 1ns/1ps
// 移植 Flight_State_Task、land_discriminat 与 Motor_Ctrl_Task 的状态处理。
// 来源为 reference/Ano_FlightCtrl.c 与 Ano_MotorCtrl.c，基线已固定源文件哈希。
// SWA 解锁/停机及传感器健康条件由现有硬件适配层提供。
// 本模块仅输出准备、起飞、飞行与着陆锁状态，不直接驱动 PWM；
// 沿用已验证的项目电机顺序：原程序 m1、m2、m3、m4 对应项目 M2、M1、M4、M3。
// 接口中 ch3、collective_us 单位为微秒；状态输出为持续电平，preparation_mask 对应项目四电机。
// 默认 TICKS_PER_MS=50000 对应 50 MHz；PRECHECKED_COLLECTIVE 默认 0，自行比较总油门 <1250 微秒。
// flight_core 将 PRECHECKED_COLLECTIVE 覆盖为 1，改用同一时刻预计算的 collective_below_landing。
module ano_flight_state #(parameter integer TICKS_PER_MS=50000,
 parameter integer PRECHECKED_COLLECTIVE=0)(
 input wire clk,rst_n,armed,
 input wire [15:0] ch3,collective_us,
 input wire collective_below_landing,
 output reg motor_prepared=0,output reg taking_off=0,output reg flying=0,output reg land_lock=0,
 output reg [3:0] preparation_mask=0
);
 reg [15:0] phase=0;
 reg half=0;
 reg [10:0] preparation_ms=0,flying_ms=0,landing_ms=0;
 reg [7:0] landing_delay=0;
 reg normal_unlock=0; // 对应原程序 unlock_sta2：油门超过 1200 微秒后置位。
 wire start_takeoff=motor_prepared && ch3>=1555;
 wire positive_stick=ch3>=1594;
 wire landing_collective_low=PRECHECKED_COLLECTIVE ?collective_below_landing:(collective_us<1250);
 always @(posedge clk)begin
  if(!rst_n)begin
   phase<=0;half<=0;motor_prepared<=0;taking_off<=0;flying<=0;
   land_lock<=0;preparation_mask<=0;preparation_ms<=0;flying_ms<=0;
   landing_ms<=0;landing_delay<=0;normal_unlock<=0;
  end else begin
   // 1 毫秒计时域处理起飞和着陆确认；正向摇杆离开后还须等待 200 毫秒才允许判定着陆。
   if(phase==TICKS_PER_MS-1)begin
    phase<=0;half<=~half;
    // 飞行状态每 1 毫秒更新；原程序的低通和摇杆处理由其他模块独立完成。
    if(armed)begin
     if(ch3>1200)normal_unlock<=1;
     if(start_takeoff)taking_off<=1;
     if(taking_off || start_takeoff)begin
      if(flying_ms<1000)flying_ms<=flying_ms+1'b1;else flying<=1;
     end
     if(positive_stick)landing_delay<=200;
     else if(landing_delay!=0)landing_delay<=landing_delay-1'b1;
     if(normal_unlock && !positive_stick && landing_delay<=1 && ch3<=1150 && landing_collective_low)begin
      if(landing_ms<1500)landing_ms<=landing_ms+1'b1;
      else begin
       land_lock<=1;taking_off<=0;flying<=0;flying_ms<=0;landing_ms<=0;
      end
     end else landing_ms<=0;
    end else begin taking_off<=0;flying<=0;flying_ms<=0;landing_ms<=0;land_lock<=0;end
    // 电机准备任务每 2 毫秒更新；与原程序一致，未完成的准备计时
    // 在锁定后保留，但准备掩码和电机准备完成状态在锁定时清零。
    if(half)begin
     if(!armed)begin motor_prepared<=0;preparation_mask<=0;end
     else if(!motor_prepared)begin
      if(preparation_ms+2<300)begin preparation_ms<=preparation_ms+2;preparation_mask[1]<=1;end
      else if(preparation_ms+2<600)begin preparation_ms<=preparation_ms+2;preparation_mask[0]<=1;end
      else if(preparation_ms+2<900)begin preparation_ms<=preparation_ms+2;preparation_mask[3]<=1;end
      else if(preparation_ms+2<1200)begin preparation_ms<=preparation_ms+2;preparation_mask[2]<=1;end
      else begin motor_prepared<=1;preparation_ms<=0;end
     end
    end
   end else phase<=phase+1'b1;
   // 核心的公开输出立即受门控；撤销解锁时状态清零无需等待下一次 1 毫秒节拍。
   if(!armed)begin taking_off<=0;flying<=0;motor_prepared<=0;preparation_mask<=0;land_lock<=0;normal_unlock<=0;end
  end
 end
endmodule
