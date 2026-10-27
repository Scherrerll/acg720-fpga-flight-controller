`timescale 1ns/1ps
`default_nettype none
module age_old(input wire clk,rst_n,sample_valid,tick_ms,seed,
 input wire[31:0]time_ms,seed_age,seed_previous,input wire seed_seen,
 output wire[31:0]age,previous,output wire seen,f1000,f200);
 reg [31:0] age_ms=32'hffffffff,age_previous_time=0;reg age_seen=0;
 always @(posedge clk)begin
  if(seed)begin age_ms<=seed_age;age_previous_time<=seed_previous;age_seen<=seed_seen;end else begin
  if(!rst_n)begin age_ms<=32'hffffffff;age_previous_time<=0;age_seen<=0;end
  else if(sample_valid && (!age_seen || time_ms!=age_previous_time))begin
   age_ms<=0;age_previous_time<=time_ms;age_seen<=1;
  end else if(tick_ms && age_ms!=32'hffffffff)age_ms<=age_ms+1'b1;
 end

 end
 assign age=age_ms;assign previous=age_previous_time;assign seen=age_seen;
 assign f1000=(age_ms<1000);
 assign f200=(age_ms<200);
endmodule
module age_new(input wire clk,rst_n,sample_valid,tick_ms,seed,
 input wire[31:0]time_ms,seed_age,seed_previous,input wire seed_seen,
 output wire[31:0]age,previous,output wire seen,f1000,f200);
 reg [31:0] age_ms=32'hffffffff,age_previous_time=0;reg age_seen=0;
 // Exact predicates of this same 32-bit age, including expiry and publication clocks.
 reg age_below_1000=0,age_below_200=0;
 always @(posedge clk)begin
  if(seed)begin age_ms<=seed_age;age_previous_time<=seed_previous;age_seen<=seed_seen;age_below_1000<=seed_age<1000;age_below_200<=seed_age<200;end else begin
  if(!rst_n)begin
   age_ms<=32'hffffffff;age_previous_time<=0;age_seen<=0;
   age_below_1000<=0;age_below_200<=0;
  end else if(sample_valid && (!age_seen || time_ms!=age_previous_time))begin
   age_ms<=0;age_previous_time<=time_ms;age_seen<=1;
   age_below_1000<=1;age_below_200<=1;
  end else if(tick_ms && age_ms!=32'hffffffff)begin
   age_ms<=age_ms+1'b1;
   age_below_1000<=age_ms<32'd999;age_below_200<=age_ms<32'd199;
  end
 end

 end
 assign age=age_ms;assign previous=age_previous_time;assign seen=age_seen;
 assign f1000=age_below_1000;
 assign f200=age_below_200;
endmodule
`default_nettype wire
