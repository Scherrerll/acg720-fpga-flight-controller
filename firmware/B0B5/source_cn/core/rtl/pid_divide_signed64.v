`timescale 1ns/1ps
// 固定 66 拍延迟的有符号除法，采用最近舍入，恰好半单位时远离零。
// 所有算术限于有符号 64 位，调用方必须排除最小负数 INT64_MIN。
// start 在空闲时锁存有符号分子和非零无符号分母；busy 表示运算中，done 为结果提交单拍。
// 商的物理单位为分子单位/分母单位；本模块不额外引入定点缩放，也不检查除零或结果溢出。
// DIVISOR_BITS 默认 64，只保存分母低位；当前调用方按实际范围覆盖为 26、32 或 36 位。
module pid_divide_signed64 #(parameter integer DIVISOR_BITS=64)(
    input wire clk,rst_n,start,
    input wire signed [63:0] numerator,
    input wire [63:0] denominator,
    output reg busy,done,
    output reg signed [63:0] quotient
);
    initial begin busy=0;done=0;quotient=0;end
    reg [63:0] work=0,rounded_q=0;
    reg [DIVISOR_BITS-1:0] divisor=1,remainder=0;
    reg [1:0] finish=0;
    reg negative=0;
    reg [6:0] remaining=0;
    // 在原有舍入拍比较两倍余数与除数，决定是否将商的绝对值加一。
    // 无符号减法额外保留一位，以完整保存借位。
    wire [DIVISOR_BITS:0] trial={remainder,finish==1 ? 1'b0:work[63]};
    wire [DIVISOR_BITS+1:0] difference={1'b0,trial}-{2'b00,divisor};
    wire subtract=!difference[DIVISOR_BITS+1];
    wire [DIVISOR_BITS:0] reduced=subtract ? difference[DIVISOR_BITS:0] : trial;
    wire [63:0] shifted={work[62:0],subtract};
    wire round_up=subtract;
    wire [63:0] rounded=work+(round_up ? 64'd1 : 64'd0);
    always @(posedge clk) begin
        done<=0;
        if(!rst_n) begin busy<=0;finish<=0;remaining<=0;quotient<=0;remainder<=0;work<=0;end
        // 先记录分子符号并以绝对值执行 64 次恢复除法；调用方负责保证分母可由所选位宽精确表示。
        else if(start && !busy) begin
            work<=numerator<0 ? -numerator : numerator;
            negative<=numerator<0;divisor<=denominator[DIVISOR_BITS-1:0];finish<=0;
            remainder<=0;remaining<=64;busy<=1;
        // 最后两拍先对商的绝对值舍入，再恢复符号并发布，保证正负数规则一致。
        end else if(busy && finish==1) begin
           rounded_q<=rounded;finish<=2;
       end else if(busy && finish==2) begin
           quotient<=negative ? -$signed(rounded_q) : $signed(rounded_q);
           busy<=0;done<=1;finish<=0;
       end else if(busy) begin
            work<=shifted;remainder<=reduced[DIVISOR_BITS-1:0];remaining<=remaining-1'b1;
            if(remaining==1) begin
                finish<=1;
            end
        end
    end
endmodule
