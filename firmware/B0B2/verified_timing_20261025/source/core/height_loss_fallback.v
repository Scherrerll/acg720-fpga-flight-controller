`timescale 1ns/1ps
// Development component. Normal ANO control does not consume this output.
// Manual takeover has no stick-matching gate. The entry collective/stick are
// a continuous curve anchor; explicit stop conditions bypass all slew state.
module height_loss_fallback #(
 parameter integer SLEW_TICKS=50000,
 parameter integer MIN_US=1200,MAX_US=1850
)(
 input wire clk,rst_n,healthy,armed,taking_off,height_available,
 input wire automatic_valid,
 input wire [15:0] automatic_collective_us,ch3,
 output wire active,prior_collective_valid,
 // Height-independent facts for callers to avoid availability -> active ->
 // availability reconvergence. Both retain the immediate live-stop mask.
 output wire latched_active,takeover_ready,
 output wire [15:0] collective_us,
 // Unmasked numeric branch for speculative pure arithmetic only. Public
 // collective_us and active retain the same immediate stop qualification.
 output wire [15:0] unmasked_collective_us
);
 reg seen=0,latched=0;
 reg [15:0] last_good=MIN_US,manual_us=MIN_US,anchor_us=MIN_US;
 reg [15:0] anchor_stick=1500;
 wire enter=armed && taking_off && seen && !height_available;
 assign active=rst_n && healthy && armed && (latched || enter);
 assign latched_active=rst_n && healthy && armed && latched;
 assign takeover_ready=rst_n && healthy && armed && (latched || taking_off && seen);
 assign prior_collective_valid=seen;
 assign unmasked_collective_us=latched ?manual_us:last_good;
 assign collective_us=active ?unmasked_collective_us:16'd1000;
 wire [15:0] stick=ch3<1000 ?16'd1000:ch3>2000 ?16'd2000:ch3;
 wire [15:0] entry_stick=stick<=1000 ?16'd1001:stick>=2000 ?16'd1999:stick;
 // Two entry-only unsigned restoring divisions. No combinational divider.
 reg [23:0] numerator=0,quotient=0;
 reg [10:0] remainder=0;
 reg [9:0] denominator=1;
 reg [4:0] bits_left=0;
 reg [1:0] divide_state=0;
 reg [23:0] lower_slope=0,upper_slope=0;
 reg curve_ready=0;
 wire [11:0] trial={remainder,numerator[23]};
 wire subtract=trial>={2'b00,denominator};
 wire [11:0] reduced=subtract ? trial-{2'b00,denominator}:trial;
 wire [23:0] next_quotient={quotient[22:0],subtract};
 reg [31:0] slew_phase=0;
 reg [9:0] distance_q=0;
 reg [23:0] slope_q=0;
 reg up_q=0,product_up_q=0,low_q=0,high_q=0,product_low_q=0,product_high_q=0;
 reg [33:0] product_q=0;
 reg [15:0] target_q=MIN_US;
 reg [2:0] valid_q=0;
 reg signed [35:0] target_work;
 always @* begin
  target_work=product_up_q ? $signed({1'b0,anchor_us})+$signed({1'b0,product_q>>12}):
                                            $signed({1'b0,anchor_us})-$signed({1'b0,product_q>>12});
 end
 always @(posedge clk)begin
  if(!rst_n || !healthy || !armed)begin
   seen<=0;latched<=0;last_good<=MIN_US;manual_us<=MIN_US;
   anchor_us<=MIN_US;anchor_stick<=1500;curve_ready<=0;
   divide_state<=0;numerator<=0;quotient<=0;remainder<=0;
   denominator<=1;bits_left<=0;lower_slope<=0;upper_slope<=0;
   slew_phase<=0;distance_q<=0;slope_q<=0;up_q<=0;
   product_up_q<=0;product_q<=0;target_q<=MIN_US;valid_q<=0;
   low_q<=0;high_q<=0;product_low_q<=0;product_high_q<=0;
  end else begin
   if(!latched && height_available && automatic_valid && taking_off &&
      automatic_collective_us>=1000 && automatic_collective_us<=MAX_US)begin
    seen<=1;last_good<=automatic_collective_us;
   end
   if(!latched && enter)begin
    latched<=1;manual_us<=last_good;anchor_us<=last_good;
    anchor_stick<=entry_stick;target_q<=last_good;
    numerator<=last_good<MIN_US ?24'd0:({8'd0,last_good}-MIN_US)<<12;
    denominator<=entry_stick-1000;quotient<=0;remainder<=0;
    bits_left<=24;divide_state<=1;curve_ready<=0;slew_phase<=0;valid_q<=0;
   end else if(latched)begin
    if(divide_state!=0)begin
     numerator<={numerator[22:0],1'b0};quotient<=next_quotient;
     remainder<=reduced[10:0];bits_left<=bits_left-1'b1;
     if(bits_left==1)begin
      if(divide_state==1)begin
       lower_slope<=next_quotient;numerator<=(MAX_US-{8'd0,anchor_us})<<12;
       denominator<=2000-anchor_stick;quotient<=0;remainder<=0;
       bits_left<=24;divide_state<=2;
      end else begin upper_slope<=next_quotient;divide_state<=0;curve_ready<=1;end
     end
    end
    // Coherent multiply pipeline, separate from the physical live-stop mask.
    valid_q<={valid_q[1:0],curve_ready};
    distance_q<=stick>=anchor_stick ?stick-anchor_stick:anchor_stick-stick;
    slope_q<=stick>=anchor_stick ?upper_slope:lower_slope;
    up_q<=stick>=anchor_stick;
    low_q<=stick<=1000;high_q<=stick>=2000;
    product_q<=distance_q*slope_q;product_up_q<=up_q;
    product_low_q<=low_q;product_high_q<=high_q;
    if(valid_q[1])begin
     if(product_low_q)target_q<=MIN_US;
     else if(product_high_q)target_q<=MAX_US;
     else if(target_work<MIN_US)target_q<=MIN_US;
     else if(target_work>MAX_US)target_q<=MAX_US;
     else target_q<=target_work[15:0];
    end
    // 1us/ms at 50MHz. Explicit SWA/RC/IMU stop never waits for this ramp.
    if(slew_phase>=SLEW_TICKS-1)begin
     slew_phase<=0;
     if(valid_q[2])begin
      if(manual_us<target_q)manual_us<=manual_us+1'b1;
      else if(manual_us>target_q)manual_us<=manual_us-1'b1;
     end
    end else slew_phase<=slew_phase+1'b1;
   end
  end
 end
 initial begin
  if(SLEW_TICKS<1 || MIN_US<1000 || MAX_US>2000 || MIN_US>=MAX_US)
   $error("Invalid fallback throttle bounds");
 end
endmodule
