`timescale 1ns/1ps
// Native MTF velocity integration. Internal units are (mm/s Q16)*microsecond;
// retain the interval remainder in signed64 rather than rounding each delta.
// Public position is mm Q8: accumulated / (1000000*256), nearest/ties away.
// Every invalidity starts a new epoch; the next accepted callback seeds zero.
// This numerical observer does not qualify a sensor or authorize hold control.
module mtf_position_integrator #(
 parameter integer AGE_LIMIT=5000000
)(
 input wire clk,rst_n,cancel,update_in,sources_valid,
 input wire [31:0] dt_us,
 input wire signed [31:0] vx_q16,vy_q16,
 output reg update=0,
 output wire busy,valid,
 output reg signed [31:0] x_q8=0,
 output reg signed [31:0] y_q8=0,
 output reg [31:0] age_ticks=32'hffffffff,
 output reg [15:0] reason=16'd1
);
 localparam signed [31:0] VELOCITY_LIMIT=32'sd655360000;
 // +/- 1 km in internal units. This also proves every ordinary sum fits64.
 localparam signed [63:0] POSITION_LIMIT_ACC=64'sd65536000000000000;
 localparam signed [63:0] POSITION_LIMIT_Q8=64'sd256000000;
 reg have_epoch=0;
 reg [3:0] state=0;
 // +/-1km is +/-65536000000000000 internal units, strictly within
 // signed57. Storage is narrowed only after the full signed65 guards.
 reg signed [56:0] accumulated_x_store=0,accumulated_y_store=0;
 wire signed [63:0] accumulated_x={{7{accumulated_x_store[56]}},accumulated_x_store};
 wire signed [63:0] accumulated_y={{7{accumulated_y_store[56]}},accumulated_y_store};
 reg signed [30:0] held_vy=0;
 reg [15:0] held_dt=0;
 reg signed [28:0] publish_x=0;
 reg mul_start=0,div_start=0;
 reg signed [30:0] ma_store=0;
 reg [15:0] mb_store=0;
 reg signed [56:0] numerator_store=0;
 wire signed [63:0] ma={{33{ma_store[30]}},ma_store};
 wire signed [63:0] mb={48'd0,mb_store};
 wire signed [63:0] numerator={{7{numerator_store[56]}},numerator_store};
 reg mul_done=0;
 reg signed [47:0] product_store=0;
 wire div_done,div_busy,div_error;
 wire signed [63:0] product={{16{product_store[47]}},product_store};
 wire signed [63:0] quotient;
 assign busy=state!=0;
 wire bad_dt=dt_us<1000 || dt_us>50000;
 wire bad_velocity=vx_q16< -VELOCITY_LIMIT || vx_q16>VELOCITY_LIMIT ||
                   vy_q16< -VELOCITY_LIMIT || vy_q16>VELOCITY_LIMIT;
 wire bad_callback=update_in && (busy || bad_dt || bad_velocity);
 wire expired=have_epoch && age_ticks>=AGE_LIMIT;
 wire math_cancel=cancel || !sources_valid || expired || bad_callback;
 assign valid=have_epoch && sources_valid && !cancel && !expired && !bad_callback;
 // A shared16-bit add/subtract serves both sums and bound comparisons.
 // Full64-bit product faults are still checked before narrowing to57 bits.
 reg working_y=0,carry=0;reg [1:0] word_index=0;
 reg [63:0] sum_store=0;
 wire signed [63:0] selected_accumulated=working_y ? accumulated_y:accumulated_x;
 wire signed [64:0] sum={selected_accumulated[63]^product[63]^carry,sum_store};
 wire overflow=sum[64]!=sum[63];
 wire [63:0] bound=sum_store[63] ? -POSITION_LIMIT_ACC:POSITION_LIMIT_ACC;
 wire [15:0] sign_mask=word_index==3 ?16'h8000:16'd0;
 wire [15:0] operand_a=state==7 ? (sum_store[word_index*16 +:16]^sign_mask):selected_accumulated[word_index*16 +:16];
 wire [15:0] operand_b=state==7 ? ~(bound[word_index*16 +:16]^sign_mask):product[word_index*16 +:16];
 wire [16:0] arithmetic={1'b0,operand_a}+{1'b0,operand_b}+(state==7 ?17'd1:{16'd0,carry});
 wire word_equal=arithmetic[15:0]==0;
 wire word_less=!arithmetic[16];
 wire out_of_position_bounds=!word_equal && (sum_store[63] ? word_less:!word_less);
 // Legal speed and dt exactly fit signed31 x positive signed17 = signed48.
 // The native-width multiply avoids general64-bit cross-product machinery.
 always @(posedge clk)begin
  mul_done<=0;
  if(!rst_n || math_cancel)product_store<=0;
  else if(mul_start)begin product_store<=$signed(ma_store)*$signed({1'b0,mb_store});mul_done<=1;end
 end
 mtf_position_divide_constant divide(.clk(clk),.rst_n(rst_n),.start(div_start),.cancel(math_cancel),
  .numerator(numerator_store),.busy(div_busy),.done(div_done),
  .error(div_error),.quotient(quotient));
 task clear_epoch;
 input [15:0] why;
 begin
  have_epoch<=0;state<=0;x_q8<=0;y_q8<=0;
  age_ticks<=32'hffffffff;reason<=why;
 end endtask
 always @(posedge clk)begin
  update<=0;mul_start<=0;div_start<=0;
  if(!rst_n)clear_epoch(16'd1);
  else if(cancel)clear_epoch(16'd2);
  else if(!sources_valid)clear_epoch(16'd4);
  else if(bad_callback)clear_epoch(busy ?16'd64:bad_dt ?16'd16:16'd32);
  else if(expired)clear_epoch(16'd8);
  else begin
   if(age_ticks!=32'hffffffff)age_ticks<=age_ticks+1'b1;
   case(state)
    0:if(update_in)begin
     age_ticks<=0;
     if(!have_epoch)begin
      have_epoch<=1;accumulated_x_store<=0;accumulated_y_store<=0;
      x_q8<=0;y_q8<=0;reason<=0;update<=1;
     end else begin
      held_vy<=vy_q16[30:0];held_dt<=dt_us[15:0];
      ma_store<=vx_q16[30:0];mb_store<=dt_us[15:0];
      working_y<=0;mul_start<=1;state<=1;
     end
    end
    1,2:if(mul_done)begin carry<=0;word_index<=0;state<=5;end
    5:begin
     sum_store[word_index*16 +:16]<=arithmetic[15:0];carry<=arithmetic[16];
     if(word_index==3)state<=6;else word_index<=word_index+1'b1;
    end
    6:if(overflow)clear_epoch(16'd128);else begin word_index<=3;state<=7;end
    7:if(out_of_position_bounds)clear_epoch(16'd256);
     else if(word_equal && word_index!=0)word_index<=word_index-1'b1;
     else state<=8;
    8:if(!working_y)begin
     accumulated_x_store<=sum_store[56:0];working_y<=1;
     ma_store<=held_vy;mb_store<=held_dt;mul_start<=1;state<=2;
    end else begin
     accumulated_y_store<=sum_store[56:0];numerator_store<=accumulated_x_store;div_start<=1;state<=3;
    end
    3:if(div_done)begin
     if(div_error)clear_epoch(16'd512);
     else if(quotient>POSITION_LIMIT_Q8 || quotient< -POSITION_LIMIT_Q8)clear_epoch(16'd256);
     else begin publish_x<=quotient[28:0];numerator_store<=accumulated_y_store;div_start<=1;state<=4;end
    end
    4:if(div_done)begin
     if(div_error)clear_epoch(16'd512);
     else if(quotient>POSITION_LIMIT_Q8 || quotient< -POSITION_LIMIT_Q8)clear_epoch(16'd256);
     else begin
      // Commit public coordinates together. Private residuals are protected
      // by epoch invalidation and are both zeroed before a new epoch begins.
      x_q8<={{3{publish_x[28]}},publish_x};y_q8<=quotient[31:0];reason<=0;update<=1;state<=0;
     end
    end
    default:clear_epoch(16'd512);
   endcase
  end
 end
endmodule

// Exact nearest/ties-away division by256000000. For magnitude N:
// round(N/D)=floor((N+128000000)/D), D=15625*16384. Therefore discard
// the14 low bits ONLY AFTER adding the exact rounding offset, then divide
// the resulting43-bit integer by15625 with a shared16-bit subtractor.
module mtf_position_divide_constant(
 input wire clk,rst_n,start,cancel,
 input wire signed [56:0] numerator,
 output reg busy=0,
 output reg done=0,
 output reg error=0,
 output wire signed [63:0] quotient
);
 reg [3:0] state=0;
 reg [56:0] work=0;
 reg [13:0] remainder=0;
 reg [5:0] left=0;
 reg negative=0,carry=0;
 reg signed [29:0] result_store=0;
 assign quotient={{34{result_store[29]}},result_store};
 wire [16:0] chunk0={1'b0,work[15:0]}+(carry ?17'd1:17'd0);
 wire [16:0] chunk1={1'b0,work[31:16]}+(carry ?17'd1:17'd0);
 wire [16:0] chunk2={1'b0,work[47:32]}+(carry ?17'd1:17'd0);
 wire [9:0] chunk3={1'b0,work[56:48]}+(carry ?10'd1:10'd0);
 // 128000000 = 0x07a12000. Constant addition is split into16-bit chunks.
 wire [16:0] round0={1'b0,work[15:0]}+17'h02000;
 wire [16:0] round1={1'b0,work[31:16]}+17'h007a1+(carry ?17'd1:17'd0);
 wire [14:0] trial={remainder,work[42]};
 wire [15:0] difference={1'b0,trial}-16'd15625;
 wire take_bit=!difference[15];
 always @(posedge clk)begin
  done<=0;
  if(!rst_n || cancel)begin state<=0;busy<=0;error<=0;work<=0;remainder<=0;left<=0;negative<=0;carry<=0;result_store<=0;end
  else if(start && !busy)begin
   work<=numerator[56] ? ~numerator:numerator;negative<=numerator[56];carry<=numerator[56];
   busy<=1;error<=0;state<=1;
  end else if(busy)case(state)
   1:begin work[15:0]<=chunk0[15:0];carry<=chunk0[16];state<=2;end
   2:begin work[31:16]<=chunk1[15:0];carry<=chunk1[16];state<=3;end
   3:begin work[47:32]<=chunk2[15:0];carry<=chunk2[16];state<=4;end
   4:begin work[56:48]<=chunk3[8:0];state<=5;end
   5:begin work[15:0]<=round0[15:0];carry<=round0[16];state<=6;end
   6:begin work[31:16]<=round1[15:0];carry<=round1[16];state<=7;end
   7:begin work[47:32]<=chunk2[15:0];carry<=chunk2[16];state<=8;end
   8:begin work[56:48]<=chunk3[8:0];state<=9;end
   9:begin work<=work>>14;left<=43;remainder<=0;state<=10;end
   10:begin
    work<={14'd0,work[41:0],take_bit};
    remainder<=take_bit ? difference[13:0]:trial[13:0];
    left<=left-1'b1;if(left==1)state<=11;
   end
   11:begin work[29:0]<=negative ? ~work[29:0]:work[29:0];carry<=negative;state<=12;end
   12:begin work[15:0]<=chunk0[15:0];carry<=chunk0[16];state<=13;end
   13:begin work[29:16]<=chunk1[13:0];state<=14;end
   14:begin result_store<=$signed(work[29:0]);busy<=0;done<=1;state<=0;end
   default:begin busy<=0;done<=1;error<=1;state<=0;result_store<=0;end
  endcase
 end
endmodule
