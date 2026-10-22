`timescale 1ns/1ps
// 66-cycle fixed-latency signed division, rounded nearest (half away from zero).
// Every arithmetic operation is bounded to signed64 excluding INT64_MIN.
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
    wire [DIVISOR_BITS:0] trial={remainder,work[63]};
    wire subtract=trial>={1'b0,divisor};
    wire [DIVISOR_BITS:0] reduced=subtract ? trial-{1'b0,divisor} : trial;
    wire [63:0] shifted={work[62:0],subtract};
    wire round_up={remainder,1'b0}>={1'b0,divisor};
    wire [63:0] rounded=work+(round_up ? 64'd1 : 64'd0);
    always @(posedge clk) begin
        done<=0;
        if(!rst_n) begin busy<=0;finish<=0;remaining<=0;quotient<=0;remainder<=0;work<=0;end
        else if(start && !busy) begin
            work<=numerator<0 ? -numerator : numerator;
            negative<=numerator<0;divisor<=denominator[DIVISOR_BITS-1:0];finish<=0;
            remainder<=0;remaining<=64;busy<=1;
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
