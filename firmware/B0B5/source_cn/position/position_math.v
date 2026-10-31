`timescale 1ns/1ps
// 共享有符号乘法器：复用 32×32 DSP 数据通路，精确返回乘积低 64 位。
// 调用方须约束操作数，保证数学乘积可放入 64 位有符号数。
// 通用握手约定：rst_n 低有效；start 仅在空闲时接受，done 为单拍，cancel 清除未完成事务。
module position_multiply(input wire clk,rst_n,start,cancel,
 input wire signed [63:0] a,b,output reg busy,done,
 output reg signed [63:0] result);
 initial begin busy=0;done=0;result=0;end
 reg [31:0] op_a=0,op_b=0,a_high=0,b_high=0,b_low=0;
 reg [31:0] result_low=0,upper_acc=0;
 reg [6:0] remaining=0;
 // 保留无符号部分乘积的全部 64 位；交叉乘积仅需取低 32 位，
 // 即可按恒等式重构完整乘积的精确低 64 位。
 wire [63:0] partial_product=$unsigned(op_a)*$unsigned(op_b);
 wire [63:0] exact_low64={upper_acc,result_low};
 always @(posedge clk) begin
  done<=0;
  if(!rst_n || cancel)begin busy<=0;remaining<=0;result<=0;end
  else if(start && !busy)begin
   op_a<=a[31:0];op_b<=b[31:0];
   a_high<=a[63:32];b_high<=b[63:32];b_low<=b[31:0];
   remaining<=64;busy<=1;
  end else if(busy)begin
   remaining<=remaining-1'b1;
   // 依次算低×低、低×高、高×低三项；等待计数保持既定的串行服务完成时序。
   case(remaining)
    64:begin result_low<=partial_product[31:0];upper_acc<=partial_product[63:32];op_b<=b_high;end
    63:begin upper_acc<=upper_acc+partial_product[31:0];op_a<=a_high;op_b<=b_low;end
    62:upper_acc<=upper_acc+partial_product[31:0];
   endcase
   if(remaining==1)begin result<=exact_low64;busy<=0;done<=1;end
  end
 end
endmodule

// 供光流支路使用的旧精度陀螺积分：输入为整数归一化计数，输出为 Q20 弧度。
// dt 为 50 MHz 时钟拍数；三轴顺序复用乘法器，任一忙时重入都会撤销整组增量并置 overrun。
module position_gyro_increment(input wire clk,rst_n,start,cancel,
 input wire signed [16:0] gx,gy,gz,input wire [31:0] dt,
 output wire busy,output reg done,overrun,
 output reg signed [63:0] ix,iy,iz);
 initial begin done=0;overrun=0;ix=0;iy=0;iz=0;end
 reg [3:0] state=0;reg signed [16:0] hy=0,hz=0;reg [31:0] ht=0;
 reg launch=0;reg signed [63:0] a=0,b=0;wire md,mb;wire signed [63:0] product;
 assign busy=state!=0;
 position_multiply m(.clk(clk),.rst_n(rst_n),.start(launch),.cancel(cancel || (start && busy)),.a(a),.b(b),.busy(mb),.done(md),.result(product));
 wire signed [63:0] scaled=product<0 ? -((-product)>>>40):(product>>>40);
 always @(posedge clk) begin
  done<=0;launch<=0;
  if(!rst_n || cancel) begin state<=0;overrun<=0;ix<=0;iy<=0;iz<=0;end
  else if(start && busy) begin state<=0;overrun<=1;ix<=0;iy<=0;iz<=0;end
  else case(state)
   // 每轴先计算原始计数×dt，再乘固定换算系数并向零截断；三轴全部完成后才给出 done。
   0:if(start) begin hy<=gy;hz<=gz;ht<=dt;a<=gx;b<=$signed({1'b0,dt});launch<=1;state<=1;overrun<=0;end
   1:if(md) begin a<=product;b<=24539222;launch<=1;state<=2;end
   2:if(md) begin ix<=scaled;a<=hy;b<=$signed({1'b0,ht});launch<=1;state<=3;end
   3:if(md) begin a<=product;b<=24539222;launch<=1;state<=4;end
   4:if(md) begin iy<=scaled;a<=hz;b<=$signed({1'b0,ht});launch<=1;state<=5;end
   5:if(md) begin a<=product;b<=24539222;launch<=1;state<=6;end
   6:if(md) begin iz<=scaled;done<=1;state<=0;end
   default:state<=0;
  endcase
 end
endmodule
// 有界逐位恢复除法器：64 位有符号分子除以 32 位无符号分母，
// 四舍五入，半值远离零；分母为零或分子为 INT64_MIN 时报告错误。
// 每个商位占 2 拍，进位链最长为 18 位。
// 求绝对值、舍入加一和符号恢复各按四个 16 位块执行。
// 合法事务在接受输入边沿之后第 143 拍完成。
module position_divide (
    input wire clk,rst_n,start,cancel,
    input wire signed [63:0] numerator,input wire [31:0] denominator,
    output reg busy,done,error,
    output reg signed [63:0] quotient);
 initial begin busy=0;done=0;error=0;quotient=0; end

    // 先分块求绝对值，再以低/高半步生成 64 个商位，最后分块舍入、恢复符号并发布。
    localparam IDLE=0,ABS0=1,ABS1=2,ABS2=3,ABS3=4,
               BIT_LOW=5,BIT_HIGH=6,ROUND_TEST=7,
               INC0=8,INC1=9,INC2=10,INC3=11,SIGN_PREP=12,
               NEG0=13,NEG1=14,NEG2=15,NEG3=16,PUBLISH=17;
    reg [4:0] state=IDLE;
    reg [63:0] work=0;
    reg [31:0] divisor=1,remainder=0;
    reg negative=0,carry=0,borrow=0;
    reg [6:0] left=0;
    reg [16:0] low_difference=0,high_difference=0;
    wire [32:0] trial={remainder,work[63]};
    wire [17:0] low_subtract={1'b0,trial[16:0]}-{1'b0,divisor[16:0]};
    wire [16:0] high_subtract={1'b0,trial[32:17]}-{2'b0,divisor[31:17]};
    wire [16:0] high_reduced=high_difference-(borrow ? 17'd1:17'd0);
    // 直接以减法最终借位决定商位，避免先比较再相减的串联路径。
    wire take_bit=!high_reduced[16];
    wire [16:0] chunk0={1'b0,work[15:0]}+(carry ? 17'd1:17'd0);
    wire [16:0] chunk1={1'b0,work[31:16]}+(carry ? 17'd1:17'd0);
    wire [16:0] chunk2={1'b0,work[47:32]}+(carry ? 17'd1:17'd0);
    wire [16:0] chunk3={1'b0,work[63:48]}+(carry ? 17'd1:17'd0);
    always @(posedge clk) begin
        done<=0;
        if(!rst_n || cancel) begin
            busy<=0;error<=0;quotient<=0;state<=IDLE;left<=0;
            work<=0;remainder<=0;carry<=0;borrow<=0;
            low_difference<=0;high_difference<=0;negative<=0;
        end
        else if(start && !busy) begin
            if(denominator==0 || numerator==64'sh8000000000000000) begin
                done<=1;error<=1;quotient<=0;
            end else begin
                work<=numerator[63] ? ~numerator:numerator;
                negative<=numerator[63];carry<=numerator[63];
                divisor<=denominator;remainder<=0;left<=64;
                busy<=1;error<=0;state<=ABS0;
            end
        end else if(busy) begin
            case(state)
                ABS0,INC0,NEG0:begin
                    work[15:0]<=chunk0[15:0];carry<=chunk0[16];state<=state+1'b1;
                end
                ABS1,INC1,NEG1:begin
                    work[31:16]<=chunk1[15:0];carry<=chunk1[16];state<=state+1'b1;
                end
                ABS2,INC2,NEG2:begin
                    work[47:32]<=chunk2[15:0];carry<=chunk2[16];state<=state+1'b1;
                end
                ABS3:begin work[63:48]<=chunk3[15:0];state<=BIT_LOW;end
                BIT_LOW:begin
                    low_difference<=low_subtract[16:0];borrow<=low_subtract[17];
                    high_difference<=high_subtract;state<=BIT_HIGH;
                end
                BIT_HIGH:begin
                    work<={work[62:0],take_bit};
                    remainder<=take_bit ? {high_reduced[14:0],low_difference} : trial[31:0];
                    left<=left-1'b1;
                    state<=left==1 ? ROUND_TEST:BIT_LOW;
                end
                // 双倍余数不小于分母时，绝对值商加一；之后才恢复符号，实现半值远离零。
                ROUND_TEST:begin
                    carry<={remainder,1'b0}>={1'b0,divisor};state<=INC0;
                end
                INC3:begin work[63:48]<=chunk3[15:0];state<=SIGN_PREP;end
                SIGN_PREP:begin work<=negative ? ~work:work;carry<=negative;state<=NEG0;end
                NEG3:begin work[63:48]<=chunk3[15:0];state<=PUBLISH;end
                PUBLISH:begin quotient<=$signed(work);busy<=0;done<=1;state<=IDLE;end
                default:begin busy<=0;state<=IDLE;end
            endcase
        end
    end
endmodule

// 16 次迭代 CORDIC：角度为 Q20 弧度，正弦/余弦为有符号 Q16。
// 调用方须提供 [-π,π] 范围的角度；从 start 到 done 最多 18 拍。
module position_sincos (
    input wire clk,rst_n,start,cancel,
    input wire signed [31:0] angle_q20,
    output reg busy,done,
    output reg signed [17:0] sin_q16,cos_q16
);
    initial begin busy=0;done=0;sin_q16=0;cos_q16=65536;end
    reg signed [19:0] x=0,y=0;
    reg signed [31:0] z=0;
    reg negate=0;
    reg [4:0] step=0;
    function signed [31:0] atan_step;
        input [4:0] idx;
        begin case(idx)
            0:atan_step=823550;1:atan_step=486170;2:atan_step=256879;
            3:atan_step=130396;4:atan_step=65451;5:atan_step=32757;
            6:atan_step=16383;7:atan_step=8192;8:atan_step=4096;
            9:atan_step=2048;10:atan_step=1024;11:atan_step=512;
            12:atan_step=256;13:atan_step=128;14:atan_step=64;15:atan_step=32;
            default:atan_step=0;
        endcase end
    endfunction
    always @(posedge clk) begin
        done<=0;
        if(!rst_n || cancel) begin busy<=0;x<=0;y<=0;z<=0;step<=0;sin_q16<=0;cos_q16<=65536;end
        else if(start && !busy) begin
        // CORDIC 先把角度折叠到 ±π/2；记录象限符号，迭代后同时修正正弦与余弦。
            x<=39797;y<=0;step<=0;busy<=1;
            if(angle_q20>1647099) begin z<=angle_q20-3294199;negate<=1;end
            else if(angle_q20< -1647099) begin z<=angle_q20+3294199;negate<=1;end
            else begin z<=angle_q20;negate<=0;end
        end else if(busy) begin
            // 每拍按当前残差角方向旋转，移位代替乘法；16 次后一次提交两路三角函数。
            if(step<16) begin
                if(z>=0) begin x<=x-(y>>>step);y<=y+(x>>>step);z<=z-atan_step(step);end
                else begin x<=x+(y>>>step);y<=y-(x>>>step);z<=z+atan_step(step);end
                step<=step+1'b1;
            end else begin
                sin_q16<=negate ? -y:y;cos_q16<=negate ? -x:x;
                busy<=0;done<=1;
            end
        end
    end
endmodule
