`timescale 1ns/1ps
// Cascaded position P -> velocity PI -> limited tilt; height P -> limited
// collective offset. Structure follows PX4, constants are bench candidates.
// No position command through sticks yet: any direction stick departure
// exits hold. Re-enter by cycling SWC low, to avoid unexpected target capture.
module hold_control #(
 parameter integer ENTRY_TICKS=10000000,
 parameter [7:0] CAL_MASK=0,
 parameter integer MAX_ANGLE=500,MAX_DELTA_US=15
)(
 input wire clk,rst_n,rc_valid,input wire [3:0] channel_count,
 input wire [15:0] ch1,ch2,ch4,ch7,
 input wire enabled,position_valid,height_valid,position_update,
 input wire [31:0] position_age,
 input wire signed [31:0] x_q8,y_q8,vx,vy,height_mm,vz,
 input wire signed [15:0] yaw_cdeg,
 output wire requested,ready,active,
 output reg [15:0] reason,
 output reg signed [15:0] roll_target,pitch_target,throttle_delta);

 function signed [63:0] trunc_shift;
 input signed [63:0] value;input integer bits;
 begin trunc_shift=value<0 ? -((-value)>>>bits):(value>>>bits);end
 endfunction
 initial begin reason=0;roll_target=0;pitch_target=0;throttle_delta=0; end

 assign requested=rc_valid && channel_count>=7 && ch7>=1800 && ch7<=2200;
 wire centered=ch1>=1450 && ch1<=1550 && ch2>=1450 && ch2<=1550 && ch4>=1450 && ch4<=1550;
 assign ready=CAL_MASK==8'hff && position_valid && height_valid && position_age<5000000;
 reg [31:0] prepare=0,command_age=32'hffffffff;
 reg tracking=0,command_seen=0,blocked=0;
 assign active=requested && enabled && ready && centered && tracking && command_seen && command_age<5000000 && !blocked;
 reg signed [31:0] tx=0,ty=0,tz=0,ix=0,iy=0;
 reg signed [63:0] ex=0,ey=0,ax=0,ay=0;
 // Rotation of two bounded +/-850 components cannot exceed +/-1700.
 reg signed [12:0] abx=0,aby=0;
 reg signed [33:0] roll_product=0,pitch_product=0;
 reg signed [63:0] height_product=0,vertical_product=0;
 reg signed [31:0] roll_raw=0,pitch_raw=0,throttle_raw=0;
 reg [3:0] state=0;
 reg trig_start=0;wire trig_done,trig_busy;wire signed [17:0] sn,cs;
 reg signed [31:0] angle=0;
 wire cancel_now=!requested || !enabled || !ready || !centered || blocked;
 // Keep the public active mask combinational. Only internal arithmetic
 // cleanup is registered to avoid a long high-fanout clock-enable path.
 reg cancel=1;
 always @(posedge clk) if(!rst_n) cancel<=1;else cancel<=cancel_now;
 reg mul_start=0;reg signed [63:0] ma=0,mb=0,mt=0;
 wire md,m_busy;wire signed [63:0] mr;
 position_multiply math(.clk(clk),.rst_n(rst_n),.start(mul_start),.cancel(cancel),.a(ma),.b(mb),.busy(m_busy),.done(md),.result(mr));
 reg freeze_x=0,freeze_y=0;
 position_sincos trig(.clk(clk),.rst_n(rst_n),.start(trig_start),.cancel(cancel),.angle_q20(angle),.busy(trig_busy),.done(trig_done),.sin_q16(sn),.cos_q16(cs));
 function signed [31:0] limit;
 input signed [63:0] value;input signed [31:0] bound;
 begin limit=value>bound ? bound : value< -bound ? -bound : value;end
 endfunction
 reg [31:0] sample_age=0,dt=0;
 always @(posedge clk) begin
  trig_start<=0;mul_start<=0;
  if(!rst_n) begin
   prepare<=0;command_age<=32'hffffffff;tracking<=0;command_seen<=0;blocked<=0;
   roll_target<=0;pitch_target<=0;throttle_delta<=0;state<=0;ix<=0;iy<=0;reason<=1;sample_age<=0;
  end else begin
   if(command_age!=32'hffffffff) command_age<=command_age+1'b1;
   if(sample_age<5000000) sample_age<=sample_age+1'b1;
   // Lost/invalid CH7 is not evidence of an intentional low-switch action.
   if(rc_valid && channel_count>=7 && ch7>=900 && ch7<=1700) blocked<=0;
   else if(tracking && (!requested || !enabled || !ready || !centered || command_age>=5000000 && command_seen)) blocked<=1;
   if(cancel) begin
    tracking<=0;command_seen<=0;prepare<=0;state<=0;ix<=0;iy<=0;roll_target<=0;pitch_target<=0;throttle_delta<=0;
    reason<=!requested ? 1 : !enabled ? 2 : CAL_MASK!=8'hff ? 4 : !ready ? 8 : !centered ? 16 : 32;
   end else if(!tracking) begin
    if(prepare<ENTRY_TICKS) prepare<=prepare+1'b1;
    else if(position_update) begin tx<=x_q8;ty<=y_q8;tz<=height_mm;tracking<=1;sample_age<=0;reason<=64;end
   end else case(state)
    0:if(position_update) begin
     // P=1/s position loop, max requested horizontal speed 0.5 m/s.
     ex<=limit(($signed(tx)-x_q8)/256,500)-$signed(vx);
     ey<=limit(($signed(ty)-y_q8)/256,500)-$signed(vy);
     dt<=sample_age;sample_age<=0;angle<=trunc_shift($signed(yaw_cdeg)*64'sd11993813,16);
     state<=1;
    end
    1:begin
     // Velocity P=1/s, I=0.25/s^2, bounded integral acceleration.
     // Freeze integration when the preliminary acceleration saturates outward.
     freeze_x<=((ex+ix>850 && ex>0)||(ex+ix< -850 && ex<0));
     freeze_y<=((ey+iy>850 && ey>0)||(ey+iy< -850 && ey<0));
     ax<=limit(ex+ix,850);ay<=limit(ey+iy,850);
     ma<=ex;mb<=$signed({1'b0,dt});mul_start<=1;state<=4;
    end
    4:if(md) begin
     ma<=mr;mb<=5498;mul_start<=1;state<=12;
    end
    12:if(md) begin
     if(!freeze_x) ix<=limit(ix+trunc_shift(mr,40),200);
     ma<=ey;mb<=$signed({1'b0,dt});mul_start<=1;state<=5;
    end
    5:if(md) begin
     ma<=mr;mb<=5498;mul_start<=1;state<=13;
    end
    13:if(md) begin
     if(!freeze_y) iy<=limit(iy+trunc_shift(mr,40),200);
     trig_start<=1;state<=2;
    end
    2:if(trig_done) begin ma<=ax;mb<=cs;mul_start<=1;state<=6;end
    6:if(md) begin mt<=mr;ma<=ay;mb<=sn;mul_start<=1;state<=7;end
    7:if(md) begin abx<=(mt+mr)>>>16;ma<=ax;mb<=sn;mul_start<=1;state<=8;end
    8:if(md) begin mt<=mr;ma<=ay;mb<=cs;mul_start<=1;state<=9;end
    9:if(md) begin aby<=(-mt+mr)>>>16;state<=3;end
    3:begin
     // a/g in radians -> centidegrees: 18000/(pi*9807) ~= 0.584.
     roll_product<=aby*34'sd612368;
     pitch_product<=-abx*34'sd612368;
     // Bench-only collective slope, gated by calibration bit7. Not a thrust model.
     ma<=$signed(tz)-$signed(height_mm);mb<=335544;mul_start<=1;state<=10;
    end
    10:if(md) begin height_product<=mr;ma<=vz;mb<=167772;mul_start<=1;state<=14;end
    14:if(md) begin vertical_product<=mr;state<=15;end
    15:begin
     roll_raw<=trunc_shift($signed(roll_product),20);pitch_raw<=trunc_shift($signed(pitch_product),20);
     throttle_raw<=trunc_shift(height_product,24)-trunc_shift(vertical_product,24);state<=11;
    end
    11:begin
     roll_target<=limit(roll_raw,MAX_ANGLE);pitch_target<=limit(pitch_raw,MAX_ANGLE);
     throttle_delta<=limit(throttle_raw,MAX_DELTA_US);
     command_age<=0;command_seen<=1;reason<=0;state<=0;
    end
    default:state<=0;
   endcase
  end
 end
endmodule
