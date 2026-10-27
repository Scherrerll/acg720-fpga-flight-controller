`timescale 1ns/1ps
// MicoAir Micolink 0x51 reader. Diagnostic parameters declare the caller's control contract.
// Frame layout/units: https://micoair.cn/zh/docs/sensors/micolink
module old_mtf_uart_rx #(parameter integer CLOCK_HZ=50000000, BAUD=115200)(
 input wire clk,rst_n,rx, output reg valid=0,output reg frame_error=0,output reg [7:0] data=0
);
 localparam integer BIT_TICKS=(CLOCK_HZ+BAUD/2)/BAUD;
 reg sync1=1,sync2=1;reg [1:0] state=0;reg [15:0] timer=0;
 reg [2:0] bit_index=0;reg [7:0] shift=0;
 always @(posedge clk) begin
  sync1<=rx;sync2<=sync1;valid<=0;frame_error<=0;
  if(!rst_n) begin state<=0;timer<=0;sync1<=1;sync2<=1;end
  else case(state)
   0:if(!sync2) begin timer<=BIT_TICKS/2-1;state<=1;end
   1:if(timer!=0)timer<=timer-1'b1;
     else if(sync2)state<=0;
     else begin timer<=BIT_TICKS-1;bit_index<=0;state<=2;end
   2:if(timer!=0)timer<=timer-1'b1;
     else begin shift[bit_index]<=sync2;timer<=BIT_TICKS-1;
      if(bit_index==7)state<=3;else bit_index<=bit_index+1'b1;end
   3:if(timer!=0)timer<=timer-1'b1;
     else begin state<=0;if(sync2)begin data<=shift;valid<=1;end else frame_error<=1;end
  endcase
 end
endmodule

module old_micolink_parser(
 input wire clk,rst_n,tick_ms,byte_valid,byte_error,input wire [7:0] byte_data,
 output reg sample_valid=0,output reg [215:0] raw_frame=0,
 output wire [31:0] time_ms,output wire [31:0] distance_mm,
 output wire [7:0] module_seq,output wire [7:0] strength,output wire [7:0] precision,
 output wire [7:0] tof_status,output wire [7:0] quality,output wire [7:0] flow_status,
 output wire signed [15:0] flow_x,output wire signed [15:0] flow_y,
 output reg [31:0] samples=0,output reg [31:0] checksum_errors=0,output reg [31:0] length_errors=0,
 output reg [31:0] uart_errors=0,output reg [31:0] timeouts=0
);
 reg [2:0] state=0;reg [3:0] gap_ms=0;
 reg [7:0] sum=0,message_id=0,payload_length=0,payload_index=0;
 reg [215:0] shift=0;
 // Published fields share the committed frame and its reset/hold behavior.
 assign time_ms={raw_frame[143:136],raw_frame[151:144],raw_frame[159:152],raw_frame[167:160]};
 assign distance_mm={raw_frame[111:104],raw_frame[119:112],raw_frame[127:120],raw_frame[135:128]};
 assign strength=raw_frame[103:96];
 assign precision=raw_frame[95:88];
 assign tof_status=raw_frame[87:80];
 assign flow_x={raw_frame[63:56],raw_frame[71:64]};
 assign flow_y={raw_frame[47:40],raw_frame[55:48]};
 assign quality=raw_frame[39:32];
 assign flow_status=raw_frame[31:24];
 assign module_seq=raw_frame[183:176];
 always @(posedge clk) begin
  sample_valid<=0;
  if(!rst_n) begin
   state<=0;gap_ms<=0;sum<=0;payload_index<=0;shift<=0;
   samples<=0;checksum_errors<=0;length_errors<=0;uart_errors<=0;timeouts<=0;
   raw_frame<=0;
  end else if(byte_error) begin uart_errors<=uart_errors+1'b1;state<=0;gap_ms<=0;end
  else if(byte_valid) begin
   gap_ms<=0;
   if(state==0) begin
    if(byte_data==8'hef)begin state<=1;sum<=8'hef;shift<=byte_data;payload_index<=0;end
   end else begin
    shift<={shift[207:0],byte_data};sum<=sum+byte_data;
    case(state)
     1:state<=2;
     2:state<=3;
     3:begin message_id<=byte_data;state<=4;end
     4:state<=5;
     5:begin
      payload_length<=byte_data;payload_index<=0;
      if(byte_data>64 || (message_id==8'h51 && byte_data!=20)) begin
       length_errors<=length_errors+1'b1;state<=0;
      end else state<=byte_data==0 ? 7:6;
     end
     6:begin
      payload_index<=payload_index+1'b1;
      if(payload_index+1==payload_length)state<=7;
     end
     7:begin
      state<=0;
      if(byte_data==sum)begin
       if(message_id==8'h51 && payload_length==20)begin
        samples<=samples+1'b1;sample_valid<=1;raw_frame<={shift[207:0],byte_data};
       end
      end else begin
       checksum_errors<=checksum_errors+1'b1;
       // A checksum byte can also be the next start delimiter after a lost byte.
       if(byte_data==8'hef)begin state<=1;sum<=8'hef;shift<=byte_data;end
      end
     end
    endcase
   end
  end else if(tick_ms && state!=0) begin
   if(gap_ms==4)begin state<=0;gap_ms<=0;timeouts<=timeouts+1'b1;end
   else gap_ms<=gap_ms+1'b1;
  end
 end
endmodule

module old_mtf_metric_observer(
 input wire clk,rst_n,sample_valid,link_fresh,
 input wire [31:0] time_ms,distance_mm,input wire [7:0] module_seq,tof_status,flow_status,quality,
 input wire signed [15:0] flow_x,flow_y,
 output wire range_numeric_ok,flow_numeric_ok,
 output reg [31:0] dt_ms=0,output reg [31:0] missing=0,output reg [31:0] duplicates=0,
 output reg [31:0] restarts=0,output reg [31:0] integration_breaks=0,
 output reg signed [31:0] vx_x100=0,output reg signed [31:0] vy_x100=0,
 output reg signed [63:0] x_x100000=0,output reg signed [63:0] y_x100000=0,
 output reg integrated=0,output reg saturated=0
);
 // Status=1 is a STRICT PROVISIONAL bench policy, not a certified enum.
 // Public manufacturer example does not define these status values.
 assign range_numeric_ok=link_fresh && tof_status==1 && distance_mm>=10 && distance_mm<=12000;
 assign flow_numeric_ok=range_numeric_ok && distance_mm>=80 && flow_status==1 && quality!=0;
 reg have_previous=0,previous_ok=0;reg [31:0] previous_time=0;reg [7:0] previous_seq=0;
 wire [31:0] delta_ms=time_ms-previous_time;
 wire [7:0] delta_seq=module_seq-previous_seq;
 wire time_forward=delta_ms!=0 && !delta_ms[31];
 // Both operands are explicitly signed; 15 bits covers the permitted 12000mm.
 wire signed [30:0] product_x=$signed(flow_x)*$signed({1'b0,distance_mm[13:0]});
 wire signed [30:0] product_y=$signed(flow_y)*$signed({1'b0,distance_mm[13:0]});
 wire signed [38:0] dx=$signed({product_x[30],product_x})*$signed({1'b0,delta_ms[5:0]});
 wire signed [38:0] dy=$signed({product_y[30],product_y})*$signed({1'b0,delta_ms[5:0]});
 wire signed [64:0] sum_x=$signed({x_x100000[63],x_x100000})+$signed({{26{dx[38]}},dx});
 wire signed [64:0] sum_y=$signed({y_x100000[63],y_x100000})+$signed({{26{dy[38]}},dy});
 function [63:0] saturate64;
  input signed [64:0] value;
  begin saturate64=value>65'sd9223372036854775807 ? 64'h7fffffffffffffff :
    value< -65'sd9223372036854775808 ? 64'h8000000000000000:value[63:0];end
 endfunction
 always @(posedge clk) begin
  if(!rst_n)begin
   have_previous<=0;previous_ok<=0;previous_time<=0;previous_seq<=0;
   dt_ms<=0;missing<=0;duplicates<=0;restarts<=0;integration_breaks<=0;
   vx_x100<=0;vy_x100<=0;x_x100000<=0;y_x100000<=0;saturated<=0;integrated<=0;
  end else begin
   if(!link_fresh)begin previous_ok<=0;integrated<=0;end
   if(sample_valid)begin
    integrated<=0;
    vx_x100<=flow_numeric_ok ? {{1{product_x[30]}},product_x}:32'sd0;
    vy_x100<=flow_numeric_ok ? {{1{product_y[30]}},product_y}:32'sd0;
    dt_ms<=have_previous && time_forward ? delta_ms:0;
    if(have_previous && delta_ms==0)duplicates<=duplicates+1'b1;
    else begin
     if(have_previous && !time_forward)begin
      restarts<=restarts+1'b1;
      // Separate module epochs: no stale displacement across reset/out-of-order time.
      x_x100000<=0;y_x100000<=0;saturated<=0;
     end else if(have_previous && delta_seq>1 && delta_seq<128)missing<=missing+delta_seq-1'b1;
     if(have_previous && previous_ok && flow_numeric_ok && delta_seq==1 && delta_ms>=1 && delta_ms<=50)begin
      x_x100000<=saturate64(sum_x);y_x100000<=saturate64(sum_y);integrated<=1;
      if(sum_x[64]!=sum_x[63] || sum_y[64]!=sum_y[63])saturated<=1;
     end else integration_breaks<=integration_breaks+1'b1;
     have_previous<=1;previous_time<=time_ms;previous_seq<=module_seq;previous_ok<=flow_numeric_ok;
    end
   end
  end
 end
endmodule

module old_mtf01p_reader #(parameter integer CLOCK_HZ=50000000,EXTERNAL_DIAGNOSTIC_HOLD=0,
 DIAGNOSTIC_VERSION=1,PHYSICAL_STOP_LOCK=1,CONTROL_PATH=0,STARTUP_ONLY_DIAGNOSTIC_RESET=0)(
 input wire clk,rst_n,rx,input wire [63:0] uptime_ms,
 input wire diagnostic_hold,
 output reg [975:0] diagnostic_body=0,
 output wire metric_sample_valid,metric_range_valid,metric_flow_valid,metric_interval_integrated,
 output wire [31:0] metric_distance_mm,metric_dt_ms,module_age_ms,
 output wire signed [31:0] metric_vx_x100,metric_vy_x100
);
 localparam integer MS_TICKS=CLOCK_HZ/1000;
 reg [31:0] phase=0;wire tick_ms=phase==MS_TICKS-1;
 always @(posedge clk)if(!rst_n || tick_ms)phase<=0;else phase<=phase+1'b1;
 wire byte_valid,byte_error;wire [7:0] byte_data;
 old_mtf_uart_rx #(.CLOCK_HZ(CLOCK_HZ)) uart(.clk(clk),.rst_n(rst_n),.rx(rx),.valid(byte_valid),.frame_error(byte_error),.data(byte_data));
 wire sample_valid;wire [215:0] raw_frame;
 wire [31:0] time_ms,distance_mm,samples,checksum_errors,length_errors,uart_errors,timeouts;
 wire [7:0] module_seq,strength,precision,tof_status,quality,flow_status;
 wire signed [15:0] flow_x,flow_y;
 old_micolink_parser parser(.clk(clk),.rst_n(rst_n),.tick_ms(tick_ms),.byte_valid(byte_valid),.byte_error(byte_error),.byte_data(byte_data),
  .sample_valid(sample_valid),.raw_frame(raw_frame),.time_ms(time_ms),.distance_mm(distance_mm),.module_seq(module_seq),
  .strength(strength),.precision(precision),.tof_status(tof_status),.quality(quality),.flow_status(flow_status),
  .flow_x(flow_x),.flow_y(flow_y),.samples(samples),.checksum_errors(checksum_errors),.length_errors(length_errors),.uart_errors(uart_errors),.timeouts(timeouts));
 reg [31:0] age_ms=32'hffffffff,age_previous_time=0;reg age_seen=0;
 always @(posedge clk)begin
  if(!rst_n)begin age_ms<=32'hffffffff;age_previous_time<=0;age_seen<=0;end
  else if(sample_valid && (!age_seen || time_ms!=age_previous_time))begin
   age_ms<=0;age_previous_time<=time_ms;age_seen<=1;
  end else if(tick_ms && age_ms!=32'hffffffff)age_ms<=age_ms+1'b1;
 end
 // P2 module offline indication is separate from metric/control freshness.
 wire module_online=samples!=0 && age_ms<1000;
 wire link_fresh=samples!=0 && age_ms<200;
 wire range_ok,flow_ok,integrated,saturated;
 wire [31:0] dt_ms,missing,duplicates,restarts,integration_breaks;
 wire signed [31:0] vx_x100,vy_x100;wire signed [63:0] x_x100000,y_x100000;
 // A new validated frame is usable on its commit edge even when the old source
 // age expired. previous_ok still prevents integration across the stale gap.
 old_mtf_metric_observer metric(.clk(clk),.rst_n(rst_n),.sample_valid(sample_valid),.link_fresh(link_fresh || sample_valid),
  .time_ms(time_ms),.distance_mm(distance_mm),.module_seq(module_seq),.tof_status(tof_status),.flow_status(flow_status),.quality(quality),
  .flow_x(flow_x),.flow_y(flow_y),.range_numeric_ok(range_ok),.flow_numeric_ok(flow_ok),.dt_ms(dt_ms),
  .missing(missing),.duplicates(duplicates),.restarts(restarts),.integration_breaks(integration_breaks),
  .vx_x100(vx_x100),.vy_x100(vy_x100),.x_x100000(x_x100000),.y_x100000(y_x100000),.integrated(integrated),.saturated(saturated));
 // Publish only after metric commit, preserving one coherent native tuple.
 // Parser and integer metric arithmetic are unchanged; only diagnostic ABI is configurable.
 reg metric_commit=0;
 always @(posedge clk) if(!rst_n)metric_commit<=0;else metric_commit<=sample_valid;
 assign metric_sample_valid=metric_commit;
 assign metric_range_valid=range_ok;
 assign metric_flow_valid=flow_ok && !saturated;
 assign metric_interval_integrated=integrated;
 assign metric_distance_mm=distance_mm;
 assign metric_dt_ms=dt_ms;
 assign module_age_ms=age_ms;
 assign metric_vx_x100=vx_x100;
 assign metric_vy_x100=vy_x100;
 // 122-byte body; A581 adds its 2B header, 2B telemetry module_seq and CRC16.
 // Flags: saturation, reserved(dt), status-certified=0, motor-lock=1,
 // last integration update, provisional metric usable, provisional range, link.
 // Do not publish the one-clock interval between parser commit and metric commit.
 // Only the display snapshot freezes; parser, freshness and metric outputs
 // continue at module rate. This replaces a duplicate 976-bit telemetry bank.
 always @(posedge clk)begin
  if(STARTUP_ONLY_DIAGNOSTIC_RESET)begin
   // Opt-in caller must guarantee reset starts low and never reasserts.
   // Preserve the initialized snapshot until reset releases.
   if(rst_n && !sample_valid && !(EXTERNAL_DIAGNOSTIC_HOLD && diagnostic_hold))
    diagnostic_body<={DIAGNOSTIC_VERSION[7:0],{saturated,1'b0,CONTROL_PATH[0],PHYSICAL_STOP_LOCK[0],integrated,flow_ok,range_ok,module_online},uptime_ms,
   samples,age_ms,checksum_errors,length_errors,uart_errors,timeouts,missing,duplicates,restarts,
   raw_frame,dt_ms,vx_x100,vy_x100,x_x100000,y_x100000,integration_breaks,136'd0};
  end else begin
  if(!rst_n)diagnostic_body<=0;else if(!sample_valid && !(EXTERNAL_DIAGNOSTIC_HOLD && diagnostic_hold))
  diagnostic_body<={DIAGNOSTIC_VERSION[7:0],{saturated,1'b0,CONTROL_PATH[0],PHYSICAL_STOP_LOCK[0],integrated,flow_ok,range_ok,module_online},uptime_ms,
   samples,age_ms,checksum_errors,length_errors,uart_errors,timeouts,missing,duplicates,restarts,
   raw_frame,dt_ms,vx_x100,vy_x100,x_x100000,y_x100000,integration_breaks,136'd0};
  end
 end
endmodule
