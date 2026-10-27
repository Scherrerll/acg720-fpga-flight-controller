`timescale 1ns/1ps
// Flight_State_Task / land_discriminat / Motor_Ctrl_Task state port.
// Source: reference/Ano_FlightCtrl.c and Ano_MotorCtrl.c, hash-pinned in baseline.
// SWA unlock/stop and sensor-health gates are the existing hardware adapter.
// Module never drives PWM directly. Source motor numbering is remapped to the
// already verified project order: source m1,m2,m3,m4 = project M2,M1,M4,M3.
module legacy_ano_flight_state #(parameter integer TICKS_PER_MS=50000)(
 input wire clk,rst_n,armed,
 input wire [15:0] ch3,collective_us,
 output reg motor_prepared=0,output reg taking_off=0,output reg flying=0,output reg land_lock=0,
 output reg [3:0] preparation_mask=0
);
 reg [15:0] phase=0;
 reg half=0;
 reg [10:0] preparation_ms=0,flying_ms=0,landing_ms=0;
 reg [7:0] landing_delay=0;
 reg normal_unlock=0; // source unlock_sta2 until throttle passes1200
 wire start_takeoff=motor_prepared && ch3>=1555;
 wire positive_stick=ch3>=1594;
 always @(posedge clk)begin
  if(!rst_n)begin
   phase<=0;half<=0;motor_prepared<=0;taking_off<=0;flying<=0;
   land_lock<=0;preparation_mask<=0;preparation_ms<=0;flying_ms<=0;
   landing_ms<=0;landing_delay<=0;normal_unlock<=0;
  end else begin
   if(phase==TICKS_PER_MS-1)begin
    phase<=0;half<=~half;
    // Flight_State_Task is1ms; source updates the LPF/stick separately.
    if(armed)begin
     if(ch3>1200)normal_unlock<=1;
     if(start_takeoff)taking_off<=1;
     if(taking_off || start_takeoff)begin
      if(flying_ms<1000)flying_ms<=flying_ms+1'b1;else flying<=1;
     end
     if(positive_stick)landing_delay<=200;
     else if(landing_delay!=0)landing_delay<=landing_delay-1'b1;
     if(normal_unlock && !positive_stick && landing_delay<=1 && ch3<=1150 && collective_us<1250)begin
      if(landing_ms<1500)landing_ms<=landing_ms+1'b1;
      else begin
       land_lock<=1;taking_off<=0;flying<=0;flying_ms<=0;landing_ms<=0;
      end
     end else landing_ms<=0;
    end else begin taking_off<=0;flying<=0;flying_ms<=0;landing_ms<=0;land_lock<=0;end
    // Motor_Ctrl_Task is2ms. As in the source, its partial preparation
    // counter survives a lock; the motor array itself is cleared on lock.
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
   // Public gating in the core is immediate; state clear does not wait1ms.
   if(!armed)begin taking_off<=0;flying<=0;motor_prepared<=0;preparation_mask<=0;land_lock<=0;normal_unlock<=0;end
  end
 end
endmodule
