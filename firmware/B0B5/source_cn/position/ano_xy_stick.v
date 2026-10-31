`timescale 1ns/1ps
// 按 Flight_State_Task 处理：死区 50，归一化系数 0.0022，3 Hz 低通，向量模长限为 1。
// 本项目 Y 向右（源坐标 Y 向左）；CH2 前向、CH1 右向均保留
// 实测遥控极性；按已接受的 IMU 样本累计时间重放源算法 1 ms 任务。
module ano_xy_stick(
 input wire clk,rst_n,enabled,sample_update,
 // ch1/ch2 为遥控脉宽 us，1500 居中；输出 nx/ny 为 Q16 无量纲向量，模长不超过 1。
 // output_dt_us 跟随本次完成样本；busy 时重入或非法输入锁存 fault，禁用后清除。
 input wire [31:0] sample_dt_us,input wire [15:0] ch1,ch2,
 output reg signed [17:0] nx=0,output reg signed [17:0] ny=0,output wire busy,output reg fault=0,
 output reg update=0,output wire valid,output reg [15:0] output_dt_us=0
);
 reg [7:0] state=0,resume=0;
 reg [15:0] elapsed=0;
 reg seen=0;reg [15:0] held_dt_us=0;reg signed [17:0] publish_nx=0;
 reg signed [17:0] target_x=0,target_y=0,fx=0,fy=0;
 reg signed [16:0] filter_residue_x=0,filter_residue_y=0;
 reg signed [10:0] cx=0,cy=0,dx=0,dy=0;
 reg start=0;reg signed [63:0] numerator=0,value=0;
 reg [31:0] denominator=1;
 wire done,dbusy,error;wire signed [63:0] quotient;
 reg [35:0] squared=0,square_shift=0;
 reg signed [17:0] square_operand=0;
 wire [35:0] square_product=$signed(square_operand)*$signed(square_operand);
 reg [35:0] saved_square=0;
 reg [19:0] sqrt_remainder=0;
 reg [17:0] root=0;reg [4:0] bit_index=0;
 wire [19:0] shifted_remainder={sqrt_remainder[17:0],square_shift[35:34]};
 wire [19:0] sqrt_trial={root,2'b01};
 wire sqrt_take=shifted_remainder>=sqrt_trial;
 reg [17:0] length=1;
 wire [16:0] elapsed_sum={1'b0,elapsed}+{1'b0,sample_dt_us[15:0]};
 assign busy=state!=0;
 assign valid=enabled && seen && !fault;
 wire signed [35:0] quotient36;
 wire signed [17:0] divide_residue;
 assign quotient={{28{quotient36[35]}},quotient36};
 ano_xy_divide36 div(.clk(clk),.rst_n(rst_n),.start(start),.cancel(!enabled),
  .numerator(numerator[35:0]),.denominator(denominator[16:0]),.busy(dbusy),.done(done),.error(error),.quotient(quotient36),.residue(divide_residue));
 task divide;
 input signed [63:0] n;input [31:0] d;input [7:0] dest;
 begin
  if(n[63:36]!={28{n[35]}} || d==0 || d>131071)begin fault<=1;nx<=0;ny<=0;state<=0;end
  else begin numerator<=n;denominator<=d;resume<=dest;start<=1;state<=100;end
 end endtask
 always @(posedge clk)begin
  start<=0;update<=0;
  if(!rst_n || !enabled)begin
   state<=0;elapsed<=0;target_x<=0;target_y<=0;fx<=0;fy<=0;nx<=0;ny<=0;fault<=0;seen<=0;output_dt_us<=0;filter_residue_x<=0;filter_residue_y<=0;
  end else if(sample_update && (busy || sample_dt_us==0 || sample_dt_us>60000 || ch1<900 || ch1>2200 || ch2<900 || ch2>2200))begin
   fault<=1;state<=0;nx<=0;ny<=0;
  end else if(!fault)case(state)
   // 0..4：锁存遥控、限制脉宽、去死区并归一化；5..7 按累计整毫秒重放 3 Hz 低通。
   0:if(sample_update)begin
    elapsed<=elapsed_sum[15:0];held_dt_us<=sample_dt_us[15:0];
    cx<=ch2<1000 ?-11'sd500:ch2>2000 ?11'sd500:$signed({1'b0,ch2})-17'sd1500;
    cy<=ch1<1000 ?-11'sd500:ch1>2000 ?11'sd500:$signed({1'b0,ch1})-17'sd1500;
    state<=1;
   end
   1:begin dx<=cx>50 ?cx-50:cx< -50 ?cx+50:0;dy<=cy>50 ?cy-50:cy< -50 ?cy+50:0;state<=2;end
   2:divide($signed(dx)*64'sd1441792,10000,3);
   3:begin target_x<=value;divide($signed(dy)*64'sd1441792,10000,4);end
   4:begin target_y<=value;state<=5;end
   // 保存四舍五入除法的余量，避免小幅摇杆输入在 Q16 低通中
   // 形成量化死区；不扩大滤波状态位宽即可更贴近 C 源算法。
   5:if(elapsed>=1000)begin elapsed<=elapsed-1000;divide(($signed(target_x)-$signed(fx))*64'sd1884+$signed(filter_residue_x),101884,6);end else state<=8;
   6:begin fx<=$signed(fx)+value;filter_residue_x<=divide_residue;divide(($signed(target_y)-$signed(fy))*64'sd1884+$signed(filter_residue_y),101884,7);end
   7:begin fy<=$signed(fy)+value;filter_residue_y<=divide_residue;state<=5;end
   // 复用一个 18 位平方运算，再以 20 位减法执行逐位恢复开平方。
   // 避免三个并行平方器，也避免每步开平方都经过 36 位比较器。
   8:begin square_operand<=fx;state<=14;end
   14:begin saved_square<=square_product;square_operand<=fy;state<=15;end
   15:begin squared<=saved_square+square_product;state<=16;end
   16:begin square_shift<=squared;root<=0;sqrt_remainder<=0;bit_index<=17;state<=9;end
   9:begin
    root<={root[16:0],sqrt_take};square_shift<=square_shift<<2;
    sqrt_remainder<=sqrt_take ?shifted_remainder-sqrt_trial:shifted_remainder;
    if(bit_index==0)state<=10;else bit_index<=bit_index-1'b1;
   end
   // 模长不超过 Q16 的 1 时直接发布；否则以向上取整的模长归一化，保证不超过单位圆。
   10:if(root<=65536)begin nx<=fx;ny<=fy;seen<=1;update<=1;output_dt_us<=held_dt_us;state<=0;end
      else begin length<=root+1'b1;state<=11;end
   11:divide($signed(fx)*64'sd65536,{14'd0,length},12);
   12:begin publish_nx<=value;divide($signed(fy)*64'sd65536,{14'd0,length},13);end
   13:begin nx<=publish_nx;ny<=value;seen<=1;update<=1;output_dt_us<=held_dt_us;state<=0;end
   100:if(done)begin if(error)begin fault<=1;nx<=0;ny<=0;state<=0;end else begin value<=quotient;state<=resume;end end
   default:state<=0;
  endcase
 end
endmodule
