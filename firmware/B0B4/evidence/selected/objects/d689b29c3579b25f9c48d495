`timescale 1ns/1ps
// Convert ticks/50, carrying sub-microsecond ticks through valid tuples.
// Fixed7bit remainder replaces a long32bit combinational constant division.
module pose_time_adapter_v7(
 input wire clk,rst_n,cancel,start,acc_valid,
 input wire [31:0] ticks,
 input wire signed [31:0] ax,ay,az,
 output reg update=0,
 output reg [31:0] dt_us=0,
 output reg signed [31:0] output_ax=0,
 output reg signed [31:0] output_ay=0,
 output reg signed [31:0] output_az=0,
 output reg output_acc_valid=0,
 output reg busy=0,
 output reg [7:0] fault=0
);
 reg [31:0] dividend=0,quotient=0;
 reg [5:0] remainder=0,index=0;
 reg [5:0] tick_fraction=0;
 reg signed [31:0] held_ax=0,held_ay=0,held_az=0;
 reg held_valid=0;
 wire [6:0] shifted={remainder,dividend[31]};
 wire quotient_bit=shifted>=7'd50;
 wire [6:0] reduced=quotient_bit ? shifted-7'd50:shifted;
 wire [31:0] next_quotient={quotient[30:0],quotient_bit};
 wire [6:0] carried_ticks=reduced+(held_valid ? {1'b0,tick_fraction}:7'd0);
 wire carry_microsecond=carried_ticks>=7'd50;
 always @(posedge clk) begin
  update<=0;
  if(!rst_n || cancel) begin
   busy<=0;fault<=0;dt_us<=0;output_acc_valid<=0;index<=0;remainder<=0;tick_fraction<=0;
   output_ax<=0;output_ay<=0;output_az<=0;
  end else if(fault!=0) begin busy<=0;output_acc_valid<=0;tick_fraction<=0;end
  else if(start && busy) begin busy<=0;output_acc_valid<=0;fault<=1;tick_fraction<=0;end
  else if(start) begin
   dividend<=ticks;quotient<=0;remainder<=0;index<=0;busy<=1;
   held_ax<=ax;held_ay<=ay;held_az<=az;held_valid<=acc_valid;
   if(!acc_valid) tick_fraction<=0;
  end else if(busy) begin
   dividend<=dividend<<1;quotient<=next_quotient;remainder<=reduced[5:0];
   if(index==31) begin
    busy<=0;update<=1;dt_us<=next_quotient+(carry_microsecond ? 32'd1:32'd0);
    tick_fraction<=held_valid ? (carry_microsecond ? carried_ticks-7'd50:carried_ticks):0;
    output_ax<=held_ax;output_ay<=held_ay;output_az<=held_az;output_acc_valid<=held_valid;
   end else index<=index+1'b1;
  end
 end
endmodule
