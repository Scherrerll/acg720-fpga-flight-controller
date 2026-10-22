`timescale 1ns/1ps
// Flight_State_Task's Z stick chain is a 1 ms source task. Consume elapsed
// time from accepted IMU records, retain a sub-ms remainder, and replay one
// original .5 LPF / .8 cm/s slew step for each elapsed millisecond. No held
// sample is integrated merely because FPGA clocks pass. Height PID stays11ms.
// Q16 normalized stick; Q16 mm/s speed. All limits are original source values.
module ano_z_stick(
 input wire clk,rst_n,enabled,sample_update,
 input wire [31:0] sample_dt_us,
 input wire [15:0] ch3,
 output reg signed [17:0] norm_q16=0,
 output reg signed [28:0] speed_q16=0,
 output wire busy,
 output reg update=0,
 output reg fault=0
);
 reg [3:0] state=0;
 reg [15:0] elapsed_us=0,held_ch3=1500;
 reg signed [10:0] deviation=0;
 reg signed [9:0] dead=0;
 reg [30:0] dividend=0,quotient=0;
 reg [13:0] remainder=0;
 reg [5:0] index=0;
 reg signed [17:0] normalized=0;
 reg signed [18:0] norm_sum=0;
 reg signed [30:0] desired_product=0;
 reg signed [28:0] desired=0;
 reg signed [29:0] difference=0;
 wire [16:0] elapsed_sum={1'b0,elapsed_us}+{1'b0,sample_dt_us[15:0]};
 wire [14:0] trial={remainder,dividend[30]};
 wire take_bit=trial>=15'd10000;
 wire [14:0] reduced=take_bit ? trial-15'd10000:trial;
 wire [30:0] quotient_next={quotient[29:0],take_bit};
 wire [30:0] rounded=quotient+({remainder,1'b0}>=15'd10000 ?31'd1:31'd0);
 wire [9:0] dead_magnitude=dead[9] ?~dead+10'd1:dead;
 assign busy=state!=0;
 always @(posedge clk)begin
  update<=0;
  if(!rst_n || !enabled)begin
   state<=0;elapsed_us<=0;norm_q16<=0;speed_q16<=0;fault<=0;
   deviation<=0;dead<=0;dividend<=0;quotient<=0;remainder<=0;index<=0;
   normalized<=0;norm_sum<=0;desired_product<=0;desired<=0;difference<=0;
  end else if(fault)begin state<=0;norm_q16<=0;speed_q16<=0;end
  else if(sample_update && (busy || sample_dt_us==0 || sample_dt_us>60000 || ch3<900 || ch3>2200))begin
   fault<=1;state<=0;norm_q16<=0;speed_q16<=0;
  end else case(state)
   0:if(sample_update)begin
    elapsed_us<=elapsed_sum[15:0];held_ch3<=ch3;state<=1;
   end
   1:begin
    deviation<=held_ch3>2000 ?11'sd500:held_ch3<1000 ?-11'sd500:$signed({1'b0,held_ch3})-17'sd1500;
    state<=2;
   end
   2:begin dead<=deviation>50 ?deviation-50:deviation< -50 ?deviation+50:0;state<=3;end
   3:begin
    // abs(dead)*(.0023*65536), followed by a small fixed-divisor divider.
    dividend<={21'd0,dead_magnitude}*31'd1507328;
    quotient<=0;remainder<=0;index<=0;state<=4;
   end
   4:begin
    dividend<=dividend<<1;quotient<=quotient_next;remainder<=reduced[13:0];
    if(index==30)state<=5;else index<=index+1'b1;
   end
   5:begin normalized<=dead<0 ?-$signed(rounded[17:0]):$signed(rounded[17:0]);state<=6;end
   6:if(elapsed_us>=1000)begin
    elapsed_us<=elapsed_us-16'd1000;norm_sum<=$signed(norm_q16)+$signed(normalized);state<=7;
   end else begin update<=1;state<=0;end
   7:begin
    // Signed division by2 truncates toward zero, including negative odd sums.
    norm_q16<=norm_sum>=0 ?norm_sum>>>1:-((-norm_sum)>>>1);state<=8;
   end
   8:begin desired_product<=$signed(norm_q16)*(dead>0 ?31'sd3500:31'sd2500);state<=9;end
   9:begin
    desired<=desired_product< -31'sd163840000 ?-29'sd163840000:
             desired_product>31'sd229376000 ?29'sd229376000:desired_product[28:0];state<=10;
   end
   10:begin difference<=$signed(desired)-$signed(speed_q16);state<=11;end
   11:begin
    speed_q16<=$signed(speed_q16)+(difference< -30'sd524288 ?-30'sd524288:
                 difference>30'sd524288 ?30'sd524288:difference);state<=6;
   end
   default:state<=0;
  endcase
 end
endmodule
