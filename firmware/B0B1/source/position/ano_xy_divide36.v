`timescale 1ns/1ps
// Private XY stick arithmetic only. All legal numerators fit signed36 and
// denominators fit unsigned17; unlike the shared navigation divider this
// helper does not need64/32 operands. Nearest rounding, ties away from zero.
module ano_xy_divide36(
 input wire clk,rst_n,start,cancel,
 input wire signed [35:0] numerator,input wire [16:0] denominator,
 output reg busy=0,output reg done=0,output reg error=0,
 output reg signed [35:0] quotient=0,output reg signed [17:0] residue=0
);
 reg [2:0] state=0;
 reg negative=0;
 reg [35:0] work=0,rounded=0;
 reg [16:0] divisor=1,remainder=0;
 reg signed [17:0] rounded_residue=0;
 reg [5:0] bits_left=0;
 wire [17:0] trial={remainder,work[35]};
 wire take_bit=trial>={1'b0,divisor};
 wire [17:0] reduced=take_bit ?trial-{1'b0,divisor}:trial;
 always @(posedge clk)begin
  done<=0;
  if(!rst_n || cancel)begin state<=0;busy<=0;done<=0;error<=0;quotient<=0;residue<=0;work<=0;remainder<=0;end
  else case(state)
   0:if(start)begin
    error<=0;
    if(denominator==0)begin quotient<=0;residue<=0;error<=1;done<=1;end
    else begin
     negative<=numerator[35];work<=numerator[35] ?-$signed(numerator):numerator;
     divisor<=denominator;remainder<=0;bits_left<=36;busy<=1;state<=1;
    end
   end
   1:begin
    work<={work[34:0],take_bit};remainder<=reduced[16:0];bits_left<=bits_left-1'b1;
    if(bits_left==1)state<=2;
   end
   2:begin
    rounded<=work+({remainder,1'b0}>={1'b0,divisor} ?36'd1:36'd0);
    rounded_residue<=$signed({1'b0,remainder})-({remainder,1'b0}>={1'b0,divisor} ?$signed({1'b0,divisor}):18'sd0);state<=3;
   end
   3:begin quotient<=negative ?-$signed(rounded):$signed(rounded);residue<=negative ?-rounded_residue:rounded_residue;busy<=0;done<=1;state<=0;end
   default:begin state<=0;busy<=0;error<=1;end
  endcase
 end
endmodule
