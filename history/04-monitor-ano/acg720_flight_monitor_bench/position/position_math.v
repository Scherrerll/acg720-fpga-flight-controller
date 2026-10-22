`timescale 1ns/1ps
// Shared signed multiply: exact low64 result, one add per clock, no DSPs.
// Callers bound operands so the mathematical product fits signed64.
module position_multiply(input wire clk,rst_n,start,cancel,
 input wire signed [63:0] a,b,output reg busy,done,
 output reg signed [63:0] result);
 initial begin busy=0;done=0;result=0;end
 reg [63:0] lhs=0,rhs=0,acc=0;reg [6:0] remaining=0;
 wire [63:0] sum=acc+(rhs[0] ? lhs:64'd0);
 always @(posedge clk) begin
  done<=0;
  if(!rst_n || cancel) begin busy<=0;remaining<=0;acc<=0;result<=0;end
  else if(start && !busy) begin lhs<=a;rhs<=b;acc<=0;remaining<=64;busy<=1;end
  else if(busy) begin
   acc<=sum;lhs<=lhs<<1;rhs<=rhs>>1;remaining<=remaining-1'b1;
   if(remaining==1) begin result<=sum;busy<=0;done<=1;end
  end
 end
endmodule

// Integrate three angular rates without three parallel wide multipliers.
module position_gyro_increment(input wire clk,rst_n,start,cancel,
 input wire signed [16:0] gx,gy,gz,input wire [31:0] dt,
 output wire busy,output reg done,overrun,
 output reg signed [63:0] ix,iy,iz);
 initial begin done=0;overrun=0;ix=0;iy=0;iz=0;end
 reg [3:0] state=0;reg signed [16:0] hy=0,hz=0;reg [31:0] ht=0;
 reg launch=0;reg signed [63:0] a=0,b=0;wire md,mb;wire signed [63:0] product;
 assign busy=state!=0;
 position_multiply m(.clk(clk),.rst_n(rst_n),.start(launch),.cancel(cancel),.a(a),.b(b),.busy(mb),.done(md),.result(product));
 wire signed [63:0] scaled=product<0 ? -((-product)>>>40):(product>>>40);
 always @(posedge clk) begin
  done<=0;launch<=0;
  if(!rst_n || cancel) begin state<=0;overrun<=0;ix<=0;iy<=0;iz<=0;end
  else if(start && busy) begin overrun<=1;end
  else case(state)
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
// Bounded restoring divider: signed64 numerator / unsigned32 denominator,
// nearest rounding, ties away from zero. Used operands exclude INT64_MIN.
module position_divide (
    input wire clk,rst_n,start,cancel,
    input wire signed [63:0] numerator,input wire [31:0] denominator,
    output reg busy,done,error,
    output reg signed [63:0] quotient);
 initial begin busy=0;done=0;error=0;quotient=0; end

    reg [63:0] work=0;
    reg [31:0] divisor=1,remainder=0;
    reg negative=0;
    reg [6:0] left=0;
    wire [32:0] trial={remainder,work[63]};
    wire subtract=trial>={1'b0,divisor};
    wire [32:0] reduced=subtract ? trial-{1'b0,divisor}:trial;
    wire [63:0] shifted={work[62:0],subtract};
    wire round_up={reduced[31:0],1'b0}>={1'b0,divisor};
    wire [63:0] rounded=shifted+(round_up ? 64'd1:64'd0);
    always @(posedge clk) begin
        done<=0;
        if(!rst_n || cancel) begin busy<=0;error<=0;quotient<=0;left<=0;work<=0;remainder<=0;end
        else if(start && !busy) begin
            if(denominator==0 || numerator==64'sh8000000000000000) begin
                done<=1;error<=1;quotient<=0;
            end else begin
                work<=numerator<0 ? -numerator:numerator;
                negative<=numerator<0;divisor<=denominator;
                remainder<=0;left<=64;busy<=1;error<=0;
            end
        end else if(busy) begin
            if(left==0) begin
                work<=work+({remainder,1'b0}>={1'b0,divisor} ? 64'd1:64'd0);
                left<=65;
            end else if(left==65) begin
                quotient<=negative ? -$signed(work):$signed(work);busy<=0;done<=1;
            end else begin
                work<=shifted;remainder<=reduced[31:0];left<=left-1'b1;
            end
        end
    end
endmodule

// Sixteen-iteration CORDIC. Angle radians Q20, sine/cosine signed Q16.
// Caller provides angle in [-pi,pi]. At most18 clocks from start to done.
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
            x<=39797;y<=0;step<=0;busy<=1;
            if(angle_q20>1647099) begin z<=angle_q20-3294199;negate<=1;end
            else if(angle_q20< -1647099) begin z<=angle_q20+3294199;negate<=1;end
            else begin z<=angle_q20;negate<=0;end
        end else if(busy) begin
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
