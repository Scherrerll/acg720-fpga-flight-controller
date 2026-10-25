`timescale 1ns/1ps
// Native MTF observer geometry only. No empirical optical/range coefficients.
// Body X forward/Y right, relative-world X initial-forward/Y initial-right.
// The factory velocity observation is NOT assumed to be gyro-compensated.
module mtf_native_geometry #(
 parameter integer CLK_HZ=50000000,AGE_LIMIT=5000000,
 parameter integer MAX_COMPUTE_TICKS=10000,
 parameter integer SWAP_AXES=0,NEGATE_X=0,NEGATE_Y=0,MAPPING_VERIFIED=0
)(
 input wire clk,rst_n,origin_reset,sample_valid,range_valid,flow_valid,
 input wire [31:0] distance_mm,dt_ms,
 input wire signed [31:0] vx_x100,vy_x100,
 input wire pose_valid,
 input wire signed [15:0] roll_cdeg,pitch_cdeg,body_yaw_cdeg,
 output reg update=0,
 output wire height_ready,flow_ready,
 output wire [15:0] reason,
 output reg signed [31:0] height_mm=0,
 output reg signed [31:0] body_vx_q16=0,
 output reg signed [31:0] body_vy_q16=0,
 output reg signed [31:0] world_vx_q16=0,
 output reg signed [31:0] world_vy_q16=0,
 output reg [31:0] dt_us=0,
 output wire busy,mapping_verified,rotation_compensated,control_verified
);
 localparam signed [63:0] V_LIMIT_Q16=64'sd655360000;
 localparam integer AGE_BITS=$clog2(AGE_LIMIT+1),COMPUTE_BITS=$clog2(MAX_COMPUTE_TICKS+1);
 localparam [AGE_BITS-1:0] AGE_SAT=AGE_LIMIT;
 wire pose_ok=pose_valid &&
  roll_cdeg>=-1500 && roll_cdeg<=1500 && pitch_cdeg>=-1500 && pitch_cdeg<=1500 &&
  body_yaw_cdeg>=-18000 && body_yaw_cdeg<=18000;
 wire range_ok=range_valid && distance_mm>=10 && distance_mm<=5000;
 wire dt_ok=dt_ms>=1 && dt_ms<=50;
 wire input_velocity_ok=vx_x100>=-1000000 && vx_x100<=1000000 &&
  vy_x100>=-1000000 && vy_x100<=1000000;
 wire sources_ok=pose_ok && range_ok;
 wire live_flow_ok=flow_valid && range_ok && dt_ok && input_velocity_ok;
 reg seen=0,flow_seen=0,transaction_epoch_ok=0,flow_epoch_ok=0,output_velocity_fault=0,pending_velocity_fault=0;
 reg [AGE_BITS-1:0] publication_age=AGE_SAT;
 reg [COMPUTE_BITS-1:0] compute_age=0;
 reg [15:0] fault=0;
 reg [6:0] state=0;reg [4:0] return_state=0;
 assign busy=state!=0;
 wire overlap=sample_valid && busy;
 wire cancel=origin_reset || !sources_ok || fault!=0 || overlap;
 assign mapping_verified=MAPPING_VERIFIED!=0;
 assign rotation_compensated=1'b0;
 // A verified axis map alone never grants control permission.
 assign control_verified=1'b0;
 assign height_ready=rst_n && sources_ok && !origin_reset && fault==0 && !overlap && seen && publication_age<AGE_LIMIT;
 assign flow_ready=height_ready && flow_seen && live_flow_ok;
 assign reason=(!pose_ok ? 16'h0001:16'h0000) |
  (!range_ok ? 16'h0002:16'h0000) | (!dt_ok ? 16'h0004:16'h0000) |
  (!input_velocity_ok || output_velocity_fault ? 16'h0008:16'h0000) | (!flow_valid ? 16'h0010:16'h0000) |
  (overlap ? 16'h0020:16'h0000) | fault |
  (!seen ? 16'h0080:16'h0000) | (!MAPPING_VERIFIED ? 16'h0100:16'h0000) |
  16'h0200 | (origin_reset ? 16'h0400:16'h0000) |
  (seen && publication_age>=AGE_LIMIT ? 16'h0800:16'h0000);
 reg signed [15:0] held_pitch=0,held_yaw=0;
 reg [12:0] held_distance=0;reg [5:0] held_dt=0;
 reg signed [20:0] held_vx100_store=0,held_vy100_store=0;
 wire signed [63:0] held_vx100={{43{held_vx100_store[20]}},held_vx100_store};
 wire signed [63:0] held_vy100={{43{held_vy100_store[20]}},held_vy100_store};
 reg signed [17:0] cr=65536,cp=65536,cy=65536,sy=0;
 reg signed [13:0] pending_height_store=0;
 reg signed [30:0] pending_bx_store=0,pending_by_store=0,pending_wx_store=0,pending_wy_store=0;
 reg signed [47:0] rot_tmp_store=0;
 wire signed [63:0] pending_height={{50{pending_height_store[13]}},pending_height_store};
 wire signed [63:0] pending_bx={{33{pending_bx_store[30]}},pending_bx_store};
 wire signed [63:0] pending_by={{33{pending_by_store[30]}},pending_by_store};
 wire signed [63:0] pending_wx={{33{pending_wx_store[30]}},pending_wx_store};
 wire signed [63:0] pending_wy={{33{pending_wy_store[30]}},pending_wy_store};
 wire signed [63:0] rot_tmp={{16{rot_tmp_store[47]}},rot_tmp_store};
 wire pending_velocity_ok=pending_bx>=-V_LIMIT_Q16 && pending_bx<=V_LIMIT_Q16 && pending_by>=-V_LIMIT_Q16 && pending_by<=V_LIMIT_Q16 &&
  pending_wx>=-V_LIMIT_Q16 && pending_wx<=V_LIMIT_Q16 && pending_wy>=-V_LIMIT_Q16 && pending_wy<=V_LIMIT_Q16;
 reg mul_start=0,div_start=0,trig_start=0;
 reg signed [47:0] ma_store=0,value_store=0;
 reg signed [24:0] mb_store=0;
 reg signed [36:0] num_store=0;
 wire signed [63:0] ma={{16{ma_store[47]}},ma_store};
 wire signed [63:0] mb={{39{mb_store[24]}},mb_store};
 wire signed [63:0] value={{16{value_store[47]}},value_store};
 reg [1:0] scale_mode=0;
 reg signed [31:0] angle_q20=0;
 wire md,mbusy,dd,dbusy,derr,td,tbusy;
 wire signed [63:0] product,quotient;
 wire signed [17:0] sn,cs;
 position_multiply m(.clk(clk),.rst_n(rst_n),.start(mul_start),.cancel(cancel),.a(ma),.b(mb),.busy(mbusy),.done(md),.result(product));
 mtf_divide100 d(.clk(clk),.rst_n(rst_n),.start(div_start),.cancel(cancel),.numerator(num_store),.busy(dbusy),.done(dd),.error(derr),.quotient(quotient));
 position_sincos t(.clk(clk),.rst_n(rst_n),.start(trig_start),.cancel(cancel),.angle_q20(angle_q20),.busy(tbusy),.done(td),.sin_q16(sn),.cos_q16(cs));
 // Nearest/ties-away on proven signed48 intermediates. Arithmetic-floor high
 // bits plus a fractional carry avoid wide abs/add/negate chains entirely.
 function signed [63:0] round_shift32;
 input signed [47:0] a;
 reg signed [16:0] q;
 begin
  q=$signed({a[47],a[47:32]})+
   (a[47] ? (a[31:0]>32'h80000000 ? 17'sd1:17'sd0):(a[31:0]>=32'h80000000 ? 17'sd1:17'sd0));
  round_shift32={{47{q[16]}},q};
 end
 endfunction
 function signed [63:0] round_shift16;
 input signed [47:0] a;
 reg signed [32:0] q;
 begin
  q=$signed({a[47],a[47:16]})+
   (a[47] ? (a[15:0]>16'h8000 ? 33'sd1:33'sd0):(a[15:0]>=16'h8000 ? 33'sd1:33'sd0));
  round_shift16={{31{q[32]}},q};
 end
 endfunction
 function signed [47:0] keep48;
 input signed [63:0] a;begin keep48=a[47:0];end
 endfunction
 function signed [24:0] keep25;
 input signed [63:0] a;begin keep25=a[24:0];end
 endfunction
 function signed [13:0] keep14;
 input signed [63:0] a;begin keep14=a[13:0];end
 endfunction
 task calc;
 input signed [63:0] a,b;input [31:0] denominator;input [7:0] dest;
 begin ma_store<=keep48(a);mb_store<=keep25(b);
  scale_mode<=denominator==1 ? 0:denominator==65536 ? 1:2;
  return_state<=dest[4:0];mul_start<=1;state<=100;end
 endtask
 task clear_outputs;
 begin
  seen<=0;flow_seen<=0;transaction_epoch_ok<=0;flow_epoch_ok<=0;output_velocity_fault<=0;pending_velocity_fault<=0;
  publication_age<=AGE_SAT;compute_age<=0;state<=0;
  height_mm<=0;body_vx_q16<=0;body_vy_q16<=0;world_vx_q16<=0;world_vy_q16<=0;dt_us<=0;
 end
 endtask
 initial begin
  if(CLK_HZ!=50000000 || AGE_LIMIT<1 || MAX_COMPUTE_TICKS<4000 ||
   SWAP_AXES<0 || SWAP_AXES>1 || NEGATE_X<0 || NEGATE_X>1 || NEGATE_Y<0 || NEGATE_Y>1 || MAPPING_VERIFIED<0 || MAPPING_VERIFIED>1)
   $error("Unsupported native MTF geometry configuration");
 end
 always @(posedge clk)begin
  update<=0;mul_start<=0;div_start<=0;trig_start<=0;
  if(!rst_n || origin_reset || !sources_ok)begin clear_outputs();fault<=0;end
  else if(overlap)begin clear_outputs();fault<=16'h0020;end
  else if(fault!=0)clear_outputs();
  else if(busy && compute_age>=MAX_COMPUTE_TICKS)begin clear_outputs();fault<=16'h0040;end
  else begin
   if(publication_age<AGE_LIMIT)publication_age<=publication_age+1'b1;
   if(busy)compute_age<=compute_age+1'b1;
   // A brief flow invalidation cannot be bridged by a still-running transaction.
   if(!live_flow_ok)begin
    flow_epoch_ok<=0;flow_seen<=0;body_vx_q16<=0;body_vy_q16<=0;world_vx_q16<=0;world_vy_q16<=0;dt_us<=0;
   end
   case(state)
    0:if(sample_valid)begin
     held_pitch<=pitch_cdeg;held_yaw<=body_yaw_cdeg;held_distance<=distance_mm[12:0];held_dt<=dt_ok ? dt_ms[5:0]:6'd0;
     // Widen before negation, including raw signed32 MIN (rejected by bounds).
     // Bound BEFORE narrowing: rejected INT32_MIN must never wrap into eligibility.
     held_vx100_store<=!input_velocity_ok ? 21'sd0:NEGATE_X ? -(SWAP_AXES ? $signed(vy_x100):$signed(vx_x100)):
      (SWAP_AXES ? $signed(vy_x100):$signed(vx_x100));
     held_vy100_store<=!input_velocity_ok ? 21'sd0:NEGATE_Y ? -(SWAP_AXES ? $signed(vx_x100):$signed(vy_x100)):
      (SWAP_AXES ? $signed(vx_x100):$signed(vy_x100));
     transaction_epoch_ok<=1;flow_epoch_ok<=live_flow_ok;pending_velocity_fault<=0;compute_age<=0;
     calc($signed(roll_cdeg),64'sd11993813,32'd65536,1);
    end
    1:begin angle_q20<=value[31:0];trig_start<=1;state<=2;end
    2:if(td)begin cr<=cs;calc($signed(held_pitch),64'sd11993813,32'd65536,3);end
    3:begin angle_q20<=value[31:0];trig_start<=1;state<=4;end
    4:if(td)begin cp<=cs;calc($signed(held_yaw),64'sd11993813,32'd65536,5);end
    5:begin angle_q20<=value[31:0];trig_start<=1;state<=6;end
    6:if(td)begin cy<=cs;sy<=sn;calc($signed({1'b0,held_distance}),$signed(cr),32'd1,7);end
    7:calc(value,$signed(cp),32'd1,8);
    8:begin pending_height_store<=keep14(round_shift32(value));calc(held_vx100,64'sd65536,32'd100,9);end
    9:begin
     pending_bx_store<=value>=-V_LIMIT_Q16 && value<=V_LIMIT_Q16 ? value[30:0]:31'sd0;
     if(value< -V_LIMIT_Q16 || value>V_LIMIT_Q16)pending_velocity_fault<=1;
     calc(held_vy100,64'sd65536,32'd100,10);
    end
    10:begin
     pending_by_store<=value>=-V_LIMIT_Q16 && value<=V_LIMIT_Q16 ? value[30:0]:31'sd0;
     if(value< -V_LIMIT_Q16 || value>V_LIMIT_Q16)pending_velocity_fault<=1;
     calc(pending_bx,$signed(cy),32'd1,11);
    end
    11:begin rot_tmp_store<=keep48(value);calc(pending_by,$signed(sy),32'd1,12);end
    12:calc(rot_tmp-value,64'sd1,32'd65536,13);
    13:begin
     pending_wx_store<=value>=-V_LIMIT_Q16 && value<=V_LIMIT_Q16 ? value[30:0]:31'sd0;
     if(value< -V_LIMIT_Q16 || value>V_LIMIT_Q16)pending_velocity_fault<=1;
     calc(pending_bx,$signed(sy),32'd1,14);
    end
    14:begin rot_tmp_store<=keep48(value);calc(pending_by,$signed(cy),32'd1,15);end
    15:calc(rot_tmp+value,64'sd1,32'd65536,16);
    16:begin
     pending_wy_store<=value>=-V_LIMIT_Q16 && value<=V_LIMIT_Q16 ? value[30:0]:31'sd0;
     if(value< -V_LIMIT_Q16 || value>V_LIMIT_Q16)pending_velocity_fault<=1;
     state<=17;
    end
    17:begin
     state<=0;transaction_epoch_ok<=0;
     if(!sources_ok || origin_reset || !transaction_epoch_ok || pending_height<0 || pending_height>5000)begin clear_outputs();fault<=16'h0040;end
     else begin
      height_mm<=pending_height[31:0];publication_age<=0;seen<=1;update<=1;
      output_velocity_fault<=flow_epoch_ok && live_flow_ok && (pending_velocity_fault || !pending_velocity_ok);
      if(flow_epoch_ok && live_flow_ok && !pending_velocity_fault && pending_velocity_ok)begin
       body_vx_q16<=pending_bx[31:0];body_vy_q16<=pending_by[31:0];world_vx_q16<=pending_wx[31:0];world_vy_q16<=pending_wy[31:0];dt_us<=held_dt*32'd1000;flow_seen<=1;
      end else begin
       body_vx_q16<=0;body_vy_q16<=0;world_vx_q16<=0;world_vy_q16<=0;dt_us<=0;flow_seen<=0;
      end
     end
    end
    100:if(md)begin
     if(scale_mode==0)begin value_store<=keep48(product);state<=return_state;end
     else if(scale_mode==1)begin value_store<=keep48(round_shift16(product));state<=return_state;end
     else if(product[63:37]!={27{product[36]}} || $signed(product[36:0])< -37'sd65536000000 || $signed(product[36:0])>37'sd65536000000)begin clear_outputs();fault<=16'h0040;end
     else begin num_store<=product[36:0];div_start<=1;state<=101;end
    end
    101:if(dd)begin
     if(derr)begin clear_outputs();fault<=16'h0040;end
     else begin value_store<=keep48(quotient);state<=return_state;end
    end
    default:begin clear_outputs();fault<=16'h0040;end
   endcase
  end
 end
endmodule

// Dedicated native-velocity conversion: signed37 / 100 -> signed31 Q16.
// Numerator magnitude is <=65,536,000,000, so36 unsigned quotient-work bits
// and7 remainder bits are sufficient. Rounded output magnitude <=655,360,000.
// Nearest rounding, ties away from zero; invalid input errors without narrowing.
module mtf_divide100(
 input wire clk,rst_n,start,cancel,
 input wire signed [36:0] numerator,
 output reg busy=0,output reg done=0,output reg error=0,
 output wire signed [63:0] quotient
);
 localparam IDLE=0,DIVIDE=1,ROUND=2,PUBLISH=3;
 reg [1:0] state=IDLE;
 reg [35:0] work=0;
 reg [6:0] remainder=0;
 reg [5:0] remaining=0;
 reg negative=0;
 reg [30:0] rounded_magnitude=0;
 reg signed [30:0] result=0;
 wire [36:0] magnitude=numerator[36] ? (~numerator+37'd1):numerator;
 wire [7:0] trial={remainder,work[35]};
 wire take_bit=trial>=8'd100;
 wire [7:0] reduced=take_bit ? trial-8'd100:trial;
 wire [30:0] rounded_work=work[30:0]+(remainder>=7'd50 ? 31'd1:31'd0);
 assign quotient={{33{result[30]}},result};
 always @(posedge clk)begin
  done<=0;
  if(!rst_n || cancel)begin
   state<=IDLE;busy<=0;error<=0;work<=0;remainder<=0;remaining<=0;
   negative<=0;rounded_magnitude<=0;result<=0;
  end else if(start && !busy)begin
   if(numerator< -37'sd65536000000 || numerator>37'sd65536000000)begin
    state<=IDLE;busy<=0;error<=1;done<=1;result<=0;
   end else begin
    work<=magnitude[35:0];remainder<=0;remaining<=36;
    negative<=numerator[36];busy<=1;error<=0;state<=DIVIDE;
   end
  end else if(busy)begin
   case(state)
    DIVIDE:begin
     work<={work[34:0],take_bit};remainder<=reduced[6:0];remaining<=remaining-1'b1;
     if(remaining==1)state<=ROUND;
    end
    ROUND:begin
     if(work>36'd655360000 || rounded_work>31'd655360000)begin
      state<=IDLE;busy<=0;done<=1;error<=1;result<=0;
     end else begin rounded_magnitude<=rounded_work;state<=PUBLISH;end
    end
    PUBLISH:begin
     result<=negative ? -$signed(rounded_magnitude):$signed(rounded_magnitude);
     state<=IDLE;busy<=0;done<=1;error<=0;
    end
    default:begin state<=IDLE;busy<=0;done<=1;error<=1;result<=0;end
   endcase
  end
 end
endmodule
