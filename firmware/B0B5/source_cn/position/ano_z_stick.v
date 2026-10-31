`timescale 1ns/1ps
// Flight_State_Task 的 Z 摇杆链按 1 ms 运行；消耗已接受 IMU 记录的
// 实际累计时间，保留不足 1 ms 的余量，每满 1 ms 重放一次源算法的
// 0.5 低通和 0.8 cm/s 变化率步骤；仅仅经过 FPGA 时钟不会
// 把保持不变的样本反复积分。高度 PID 的周期仍为 11 ms。
// 归一化摇杆与 mm/s 速度均采用 Q16，所有限幅保留源算法值。
module ano_z_stick(
 input wire clk,rst_n,enabled,taking_off,sample_update,
 // ch3 为油门脉宽 us，1500 居中；sample_update 携带实际样本时长，taking_off 控制速度输出资格。
 // enabled 撤销后清空滤波、累计时间和故障；busy 时新回调会锁存 fault。
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
   // 0..5：锁存油门并去死区，固定分母串行除法得到 Q16 归一化值。
   0:if(sample_update)begin
    elapsed_us<=elapsed_sum[15:0];held_ch3<=ch3;state<=1;
   end
   1:begin
    deviation<=held_ch3>2000 ?11'sd500:held_ch3<1000 ?-11'sd500:$signed({1'b0,held_ch3})-17'sd1500;
    state<=2;
   end
   2:begin dead<=deviation>50 ?deviation-50:deviation< -50 ?deviation+50:0;state<=3;end
   3:begin
    // 先算 abs(dead)×(0.0023×65536)，随后用小型固定分母除法器完成缩放。
    dividend<={21'd0,dead_magnitude}*31'd1507328;
    quotient<=0;remainder<=0;index<=0;state<=4;
   end
   4:begin
    dividend<=dividend<<1;quotient<=quotient_next;remainder<=reduced[13:0];
    if(index==30)state<=5;else index<=index+1'b1;
   end
   5:begin normalized<=dead<0 ?-$signed(rounded[17:0]):$signed(rounded[17:0]);state<=6;end
   // 每次消耗 1000 us，执行一轮低通与速度变化率限制；不足 1 ms 留给下次有效样本。
   6:if(elapsed_us>=1000)begin
    elapsed_us<=elapsed_us-16'd1000;norm_sum<=$signed(norm_q16)+$signed(normalized);state<=7;
   end else begin update<=1;state<=0;end
   7:begin
    // 有符号除以 2 按向零截断处理，负奇数和也遵守同一规则。
    norm_q16<=norm_sum>=0 ?norm_sum>>>1:-((-norm_sum)>>>1);state<=8;
   end
   // 正向目标上限 3500 mm/s，负向 2500 mm/s；每毫秒速度最多改变 8 mm/s。
   8:begin desired_product<=$signed(norm_q16)*(dead>0 ?31'sd3500:31'sd2500);state<=9;end
   9:begin
    desired<=desired_product< -31'sd163840000 ?-29'sd163840000:
             desired_product>31'sd229376000 ?29'sd229376000:desired_product[28:0];state<=10;
   end
   10:begin difference<=$signed(desired)-$signed(speed_q16);state<=11;end
   11:begin
    speed_q16<=!taking_off ? 29'sd0 : $signed(speed_q16)+(difference< -30'sd524288 ?-30'sd524288:
                 difference>30'sd524288 ?30'sd524288:difference);state<=6;
   end
   default:state<=0;
  endcase
 end
endmodule
