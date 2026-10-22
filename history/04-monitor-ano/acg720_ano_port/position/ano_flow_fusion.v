`timescale 1ns/1ps
// ANO Tech Ano_OF_DecoFusion.c OF_INS_Get + ANO_OF_Fusion numerical port.
// PMW3901 rotation/height/axis calibration is performed by relative_position;
// do not copy UP_OF's 160pixel/deg or .00012cm/pixel constants onto PMW3901.
// World X initial-forward, Y initial-right; mm/s and mm/s^2, internal Q16.
// Prediction: 5Hz source LPF(linear_acc) then v += a*dt.
// Correction: e=observed-v; i=clip(i+e*dt,+/-1000mm/s^2);
// v += (2*e+i)*dt. These retain source FUS_KP=2, FUS_KI=1 exactly.
// Source quality scores are not PMW3901 SQUAL scores; upstream hardware
// validity replaces source quality state machine and disallows stale bridging.
module ano_flow_fusion #(
 parameter integer CLK_HZ=50000000,AGE_LIMIT=5000000,
 parameter [7:0] CAL_MASK=0
)(
 input wire clk,rst_n,origin_reset,
 input wire acc_update,acc_valid,input wire [31:0] acc_dt_us,
 input wire signed [31:0] ax_mmps2,ay_mmps2,
 input wire flow_update,flow_valid,input wire [31:0] flow_dt_us,
 input wire signed [31:0] observed_vx,observed_vy,
 output wire valid,output reg qualified_valid=0,output reg update,flow_correction_update,
 output reg signed [31:0] fused_vx,fused_vy,
 output reg [15:0] reason);
 reg [31:0] age=32'hffffffff;
 reg seen=0,continuity=0,overrun=0,flow_pending=0,acc_pending=0;
 reg signed [30:0] vqx_store=0;
 wire signed [63:0] vqx={{33{vqx_store[30]}},vqx_store};
 reg signed [30:0] vqy_store=0;
 wire signed [63:0] vqy={{33{vqy_store[30]}},vqy_store};
 reg signed [26:0] iqx_store=0;
 wire signed [63:0] iqx={{37{iqx_store[26]}},iqx_store};
 reg signed [26:0] iqy_store=0;
 wire signed [63:0] iqy={{37{iqy_store[26]}},iqy_store};
 reg signed [31:0] aqx_store=0;
 wire signed [63:0] aqx={{32{aqx_store[31]}},aqx_store};
 reg signed [31:0] aqy_store=0;
 wire signed [63:0] aqy={{32{aqy_store[31]}},aqy_store};
 reg signed [31:0] pax=0,pay=0,pvx=0,pvy=0;
 reg [31:0] padt=0,pfdt=0,dt=0;
 reg correcting=0,transaction_epoch_ok=0,pending_acc_epoch_ok=0,pending_flow_epoch_ok=0;
 reg signed [31:0] hx_store=0;
 wire signed [63:0] hx={{32{hx_store[31]}},hx_store};
 reg signed [31:0] hy_store=0;
 wire signed [63:0] hy={{32{hy_store[31]}},hy_store};
 reg signed [31:0] errx_store=0;
 wire signed [63:0] errx={{32{errx_store[31]}},errx_store};
 reg signed [31:0] erry_store=0;
 wire signed [63:0] erry={{32{erry_store[31]}},erry_store};
 reg signed [17:0] alpha_store=0;
 wire signed [63:0] alpha={{46{alpha_store[17]}},alpha_store};
 reg [7:0] state=0,return_state=0;
 reg mul_start=0,div_start=0;
 reg signed [63:0] ma=0,mb=0,num=0,value=0;
 reg [31:0] den=1,pending_den=1;
 wire md,mbusy,dd,dbusy,derr;wire signed [63:0] product,quotient;
 wire good_sources=acc_valid && flow_valid && CAL_MASK[5:0]==6'h3f;
 wire cancel=origin_reset || !good_sources || overrun;
 // Live validity masks immediately; registered cleanup keeps the upstream
 // sensor-health cone off the 64-bit arithmetic enable/reset fanout.
 reg cleanup=1;
 always @(posedge clk) if(!rst_n) cleanup<=1;else cleanup<=cancel;
 assign valid=good_sources && !origin_reset && !cleanup && seen && continuity && age<AGE_LIMIT && !overrun;
 always @(posedge clk)if(!rst_n || origin_reset)qualified_valid<=0;else qualified_valid<=valid;
 wire bad_acc_callback=acc_update && (acc_pending || acc_dt_us==0 || acc_dt_us>100000 || ax_mmps2< -30000 || ax_mmps2>30000 || ay_mmps2< -30000 || ay_mmps2>30000);
 wire bad_flow_callback=flow_update && (flow_pending || flow_dt_us<1000 || flow_dt_us>100000 || observed_vx< -10000 || observed_vx>10000 || observed_vy< -10000 || observed_vy>10000);
 position_multiply m(.clk(clk),.rst_n(rst_n),.start(mul_start),.cancel(cleanup),.a(ma),.b(mb),.busy(mbusy),.done(md),.result(product));
 position_divide d(.clk(clk),.rst_n(rst_n),.start(div_start),.cancel(cleanup),.numerator(num),.denominator(den),.busy(dbusy),.done(dd),.error(derr),.quotient(quotient));
 function signed [63:0] keep64;
 input signed [63:0] a;begin keep64=a;end endfunction
 function signed [63:0] clip;
 input signed [63:0] a,lo,hi;begin clip=a<lo ? lo:a>hi ? hi:a;end endfunction
 task calc;
 input signed [63:0] a,b;input [31:0] denominator;input [7:0] dest;
 begin ma<=a;mb<=b;pending_den<=denominator;return_state<=dest;mul_start<=1;state<=100;end endtask
 initial begin update=0;flow_correction_update=0;fused_vx=0;fused_vy=0;reason=1;end
 always @(posedge clk) begin
  update<=0;flow_correction_update<=0;mul_start<=0;div_start<=0;
  if(!rst_n || cleanup || age>=AGE_LIMIT && seen) begin
   state<=0;seen<=0;continuity<=0;transaction_epoch_ok<=0;pending_acc_epoch_ok<=0;pending_flow_epoch_ok<=0;age<=32'hffffffff;flow_pending<=0;acc_pending<=0;
   vqx_store<=keep64(0);vqy_store<=keep64(0);iqx_store<=keep64(0);iqy_store<=keep64(0);aqx_store<=keep64(0);aqy_store<=keep64(0);fused_vx<=0;fused_vy<=0;
   reason<=!good_sources ? 1:origin_reset ? 2:overrun ? 4:8;
   if(!rst_n || origin_reset) overrun<=0;
   // A new good record permits recovery, but cannot integrate across the gap.
   if(rst_n && !origin_reset && good_sources && flow_update) begin overrun<=0;seen<=1;age<=0;continuity<=0;end
  end else begin
   if(age!=32'hffffffff) age<=age+1'b1;
   if(acc_update) begin
    if(bad_acc_callback) begin overrun<=1;reason<=4;end
    else begin acc_pending<=1;pax<=ax_mmps2;pay<=ay_mmps2;padt<=acc_dt_us;pending_acc_epoch_ok<=good_sources && !origin_reset && !overrun;end
   end
   if(flow_update) begin
    if(bad_flow_callback) begin overrun<=1;reason<=4;end
    else begin flow_pending<=1;pvx<=observed_vx;pvy<=observed_vy;pfdt<=flow_dt_us;pending_flow_epoch_ok<=good_sources && !origin_reset && !overrun;end
   end
   case(state)
    0:if(acc_pending) begin
     correcting<=0;acc_pending<=0;transaction_epoch_ok<=pending_acc_epoch_ok;hx_store<=keep64($signed(pax)*65536);hy_store<=keep64($signed(pay)*65536);dt<=padt;
     calc($signed({1'b0,padt})*314,65536,10000000+padt*314,1);
    end else if(flow_pending) begin
     correcting<=1;flow_pending<=0;transaction_epoch_ok<=pending_flow_epoch_ok;dt<=pfdt;errx_store<=keep64($signed(pvx)*65536-vqx);erry_store<=keep64($signed(pvy)*65536-vqy);
     if(!seen || !continuity) begin
      // Same source reset-to-zero state, no guessed initial velocity.
      seen<=1;continuity<=1;age<=0;reason<=0;state<=20;
      vqx_store<=keep64(0);vqy_store<=keep64(0);iqx_store<=keep64(0);iqy_store<=keep64(0);
     end else calc($signed(pvx)*65536-vqx,$signed({1'b0,pfdt}),1000000,10);
    end
    1:begin alpha_store<=keep64(value);calc(hx-aqx,value,65536,2);end
    2:begin aqx_store<=keep64(aqx+value);calc(hy-aqy,alpha,65536,3);end
    3:begin aqy_store<=keep64(aqy+value);calc(aqx,$signed({1'b0,dt}),1000000,4);end
    4:begin vqx_store<=keep64(clip(vqx+value,-655360000,655360000));calc(aqy,$signed({1'b0,dt}),1000000,5);end
    5:begin vqy_store<=keep64(clip(vqy+value,-655360000,655360000));state<=20;end
    10:begin iqx_store<=keep64(clip(iqx+value,-65536000,65536000));calc(erry,$signed({1'b0,dt}),1000000,11);end
    11:begin iqy_store<=keep64(clip(iqy+value,-65536000,65536000));calc(errx*2+iqx,$signed({1'b0,dt}),1000000,12);end
    12:begin vqx_store<=keep64(clip(vqx+value,-655360000,655360000));calc(erry*2+iqy,$signed({1'b0,dt}),1000000,13);end
    13:begin vqy_store<=keep64(clip(vqy+value,-655360000,655360000));age<=0;seen<=1;continuity<=1;reason<=0;state<=20;end
    20:begin
     transaction_epoch_ok<=0;state<=0;
     if(!good_sources || origin_reset || overrun || bad_acc_callback || bad_flow_callback || !transaction_epoch_ok || dt==0 || dt>100000 || correcting && dt<1000)begin overrun<=1;seen<=0;continuity<=0;reason<=4;end
     else begin fused_vx<=vqx/65536;fused_vy<=vqy/65536;update<=1;flow_correction_update<=correcting;end
    end
    100:if(md) begin num<=product;den<=pending_den;div_start<=1;state<=101;end
    101:if(dd) begin if(derr) begin overrun<=1;reason<=4;state<=0;end else begin value<=quotient;state<=return_state;end end
    default:state<=0;
   endcase
  end
 end
endmodule
