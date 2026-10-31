`timescale 1ns/1ps
// MicoAir Micolink 消息 0x51 读取器；诊断参数声明调用方的控制与停机契约。
// 帧布局与单位参考：https://micoair.cn/zh/docs/sensors/micolink
// 串口层把异步 RX 同步后按 8 位数据、1 位停止位接收，默认 50 MHz/115200 波特。
// clk 由 CLOCK_HZ 声明，rst_n 低有效同步复位；data 在 valid 单拍脉冲时有效，frame_error 表示坏停止位。
// 波特率分频四舍五入到整数时钟拍，起始位半位复核后按最低有效位优先采样。
module mtf_uart_rx #(parameter integer CLOCK_HZ=50000000, BAUD=115200)(
 input wire clk,rst_n,rx, output reg valid=0,output reg frame_error=0,output reg [7:0] data=0
);
 localparam integer BIT_TICKS=(CLOCK_HZ+BAUD/2)/BAUD;
 // 起始位在半位处复核，随后逐位采样；停止位为低时只报告帧错误。
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

// 协议层从 0xEF 起始字节查找帧；仅提交消息 0x51、20 字节载荷且累加校验正确的帧。
// clk/rst_n 为同步接口，tick_ms 每毫秒一拍，byte_valid/byte_error 为 UART 结果脉冲。
// raw_frame 为 27 字节完整帧；sample_valid 在原始帧及资格位同时提交时脉冲一拍。
// time_ms/distance_mm 分别为毫秒/毫米；flow_x/flow_y 保留协议有符号原始量，状态与质量保留原始字节。
module micolink_parser(
 input wire clk,rst_n,tick_ms,byte_valid,byte_error,input wire [7:0] byte_data,
 output reg sample_valid=0,output reg [215:0] raw_frame=0,
 output wire payload_range_ok,payload_flow_ok,
 output wire [31:0] time_ms,output wire [31:0] distance_mm,
 output wire [7:0] module_seq,output wire [7:0] strength,output wire [7:0] precision,
 output wire [7:0] tof_status,output wire [7:0] quality,output wire [7:0] flow_status,
 output wire signed [15:0] flow_x,output wire signed [15:0] flow_y,
 output reg [31:0] samples=0,output reg [31:0] checksum_errors=0,output reg [31:0] length_errors=0,
 output reg [31:0] uart_errors=0,output reg [31:0] timeouts=0
);
 // 6 字节头部中，状态 1/2 消费其余固定头字段，3 取消息号，4 消费序号，5 取长度，6 收载荷，7 校验。
 // 校验为此前所有字节的 8 位累加和；过长载荷或 0x51 长度非 20 时立即退回帧头搜索。
 reg [2:0] state=0;reg [3:0] gap_ms=0;
 reg [7:0] sum=0,message_id=0,payload_length=0,payload_index=0;
 reg [215:0] shift=0;
 (* syn_preserve=1 *) reg payload_range_ok_q=0;
 assign payload_range_ok=payload_range_ok_q;
 (* syn_preserve=1 *) reg payload_flow_ok_q=0;
 assign payload_flow_ok=payload_flow_ok_q;
 // 在接受帧的同一边沿缓存该帧的测距/光流资格，避免下游重复组合比较。
 // 数据及资格位的提交、复位和保持均由本解析器负责。
 // 测距资格要求状态为 1 且距离在 10..12000 mm；光流另要求距离至少 80 mm、状态及质量有效。
 wire [215:0] next_raw_frame={shift[207:0],byte_data};
 wire [31:0] next_distance_mm={next_raw_frame[111:104],next_raw_frame[119:112],next_raw_frame[127:120],next_raw_frame[135:128]};
 wire next_payload_range_ok=next_raw_frame[87:80]==8'd1 && next_distance_mm>=32'd10 && next_distance_mm<=32'd12000;
 wire next_payload_flow_ok=next_payload_range_ok && next_distance_mm>=32'd80 && next_raw_frame[31:24]==8'd1 && next_raw_frame[39:32]!=8'd0;
 // 所有公开字段均取自同一已提交帧，共享其复位和保持行为。
 // 多字节时间、距离和有符号光流按载荷的小端顺序重组，字段都取自同一已提交帧。
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
   raw_frame<=0;payload_range_ok_q<=0;payload_flow_ok_q<=0;
 // 串口错误立即丢弃当前半帧并计数；已发布的上一完整帧继续保留。
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
        samples<=samples+1'b1;sample_valid<=1;raw_frame<=next_raw_frame;payload_range_ok_q<=next_payload_range_ok;payload_flow_ok_q<=next_payload_flow_ok;
       end
      end else begin
       checksum_errors<=checksum_errors+1'b1;
       // 校验失败且当前字节为 0xEF 时，把它复用为下一帧起点，以从丢字节中恢复。
       if(byte_data==8'hef)begin state<=1;sum<=8'hef;shift<=byte_data;end
      end
     end
    endcase
   end
 // 半帧持续五个毫秒节拍没有新字节即超时，回到帧头搜索。
  end else if(tick_ms && state!=0) begin
   if(gap_ms==4)begin state<=0;gap_ms<=0;timeouts<=timeouts+1'b1;end
   else gap_ms<=gap_ms+1'b1;
  end
 end
endmodule

// 度量层只在新完整帧脉冲上推进；速度尺度为 mm/s×100，累计位移尺度为 mm×100000。
// sample_valid 表示提交新帧，link_fresh 直接门控资格；PRECHECKED_* 启用时复用同帧缓存资格。
// dt_ms 为相邻模块时间戳差；missing/duplicates/restarts/integration_breaks 记录缺帧、重复、历元重启和断积分次数。
// integrated 表示最近一次处理完成了积分；saturated 在本历元内锁存累计位移饱和，rst_n 低有效同步复位。
module mtf_metric_observer #(parameter integer PRECHECKED_RANGE=0,PRECHECKED_FLOW=0)(
 input wire clk,rst_n,sample_valid,link_fresh,
 input wire payload_range_ok,payload_flow_ok,
 input wire [31:0] time_ms,distance_mm,input wire [7:0] module_seq,tof_status,flow_status,quality,
 input wire signed [15:0] flow_x,flow_y,
 output wire range_numeric_ok,flow_numeric_ok,
 output reg [31:0] dt_ms=0,output reg [31:0] missing=0,output reg [31:0] duplicates=0,
 output reg [31:0] restarts=0,output reg [31:0] integration_breaks=0,
 output reg signed [31:0] vx_x100=0,output reg signed [31:0] vy_x100=0,
 output reg velocity_range_ok=1,
 output reg signed [63:0] x_x100000=0,output reg signed [63:0] y_x100000=0,
 output reg integrated=0,output reg saturated=0
);
 // 状态值等于 1 只是严格的临时台架资格策略，尚未作为厂商认证的枚举含义。
 // 厂商公开示例没有定义这些状态值，因而本层仅据此提供临时数值资格。
 assign range_numeric_ok=link_fresh && (PRECHECKED_RANGE ? payload_range_ok :
  (tof_status==1 && distance_mm>=10 && distance_mm<=12000));
 assign flow_numeric_ok=PRECHECKED_FLOW ? (link_fresh && payload_flow_ok) :
  (range_numeric_ok && distance_mm>=80 && flow_status==1 && quality!=0);
 reg have_previous=0,previous_ok=0;reg [31:0] previous_time=0;reg [7:0] previous_seq=0;
 // 时间差和序号差使用无符号回绕减法；时间差最高位用于拒绝倒退或过大的跳变。
 wire [31:0] delta_ms=time_ms-previous_time;
 wire [7:0] delta_seq=module_seq-previous_seq;
 wire time_forward=delta_ms!=0 && !delta_ms[31];
 // 两操作数均显式为有符号数；距离前补零形成 15 位正数，可覆盖允许的 12000 mm。
 // 原生光流乘当前距离得到整数速度；本层保留原始轴向，坐标交换由后级几何模块处理。
 wire signed [30:0] product_x=$signed(flow_x)*$signed({1'b0,distance_mm[13:0]});
 wire signed [30:0] product_y=$signed(flow_y)*$signed({1'b0,distance_mm[13:0]});
 // 与本拍发布的有符号速度字同时缓存范围资格；无效观测发布零速度。
 // velocity_range_ok 与速度字共享复位和保持行为，供下游预检查入口复用。
 wire signed [31:0] next_vx_x100=flow_numeric_ok ? {product_x[30],product_x}:32'sd0;
 wire signed [31:0] next_vy_x100=flow_numeric_ok ? {product_y[30],product_y}:32'sd0;
 wire next_velocity_range_ok=next_vx_x100>=-32'sd1000000 && next_vx_x100<=32'sd1000000 &&
  next_vy_x100>=-32'sd1000000 && next_vy_x100<=32'sd1000000;
 // 位移使用当前速度乘毫秒间隔；65 位求和后饱和到有符号 64 位并记录饱和。
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
   vx_x100<=0;vy_x100<=0;velocity_range_ok<=1;x_x100000<=0;y_x100000<=0;saturated<=0;integrated<=0;
  end else begin
   if(!link_fresh)begin previous_ok<=0;integrated<=0;end
   if(sample_valid)begin
    integrated<=0;
    vx_x100<=next_vx_x100;vy_x100<=next_vy_x100;
    velocity_range_ok<=next_velocity_range_ok;
    dt_ms<=have_previous && time_forward ? delta_ms:0;
    // 重复时间戳只计数；时间倒退清位移，缺帧计数不允许跨间隙补积分。
    if(have_previous && delta_ms==0)duplicates<=duplicates+1'b1;
    else begin
     if(have_previous && !time_forward)begin
      restarts<=restarts+1'b1;
      // 模块复位或乱序时间形成新历元，清除旧位移，避免跨历元保留累计结果。
      x_x100000<=0;y_x100000<=0;saturated<=0;
     end else if(have_previous && delta_seq>1 && delta_seq<128)missing<=missing+delta_seq-1'b1;
     // 仅前后帧均有效、序号连续且间隔 1..50 ms 时积分，断链后须重新建立连续样本。
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

// 读数顶层组合 UART、解析与度量，并向导航输出同一度量样本及独立遥测快照。
// clk 按 CLOCK_HZ 产生毫秒节拍，rst_n 为低有效同步复位；uptime_ms 为外部 64 位运行毫秒数。
// metric_distance_mm/dt_ms/vx_x100/vy_x100 单位分别为 mm、ms、mm/s×100；module_age_ms 为源龄。
// metric_sample_valid 每个度量提交脉冲一拍；range/flow_valid 与 interval_integrated 分别描述资格和积分连续性。
// diagnostic_hold 仅在 EXTERNAL_DIAGNOSTIC_HOLD 启用时冻结 976 位诊断显示快照。
module mtf01p_reader #(parameter integer CLOCK_HZ=50000000,EXTERNAL_DIAGNOSTIC_HOLD=0,
 DIAGNOSTIC_VERSION=1,PHYSICAL_STOP_LOCK=1,CONTROL_PATH=0,STARTUP_ONLY_DIAGNOSTIC_RESET=0)(
 input wire clk,rst_n,rx,input wire [63:0] uptime_ms,
 input wire diagnostic_hold,
 output reg [975:0] diagnostic_body=0,
 output wire metric_sample_valid,metric_range_valid,metric_flow_valid,metric_interval_integrated,
 output wire [31:0] metric_distance_mm,metric_dt_ms,module_age_ms,
 output wire signed [31:0] metric_vx_x100,metric_vy_x100,
 output wire metric_velocity_range_ok
);
 localparam integer MS_TICKS=CLOCK_HZ/1000;
 reg [31:0] phase=0;wire tick_ms=phase==MS_TICKS-1;
 always @(posedge clk)if(!rst_n || tick_ms)phase<=0;else phase<=phase+1'b1;
 wire byte_valid,byte_error;wire [7:0] byte_data;
 mtf_uart_rx #(.CLOCK_HZ(CLOCK_HZ)) uart(.clk(clk),.rst_n(rst_n),.rx(rx),.valid(byte_valid),.frame_error(byte_error),.data(byte_data));
 wire sample_valid,payload_range_ok,payload_flow_ok;wire [215:0] raw_frame;
 wire [31:0] time_ms,distance_mm,samples,checksum_errors,length_errors,uart_errors,timeouts;
 wire [7:0] module_seq,strength,precision,tof_status,quality,flow_status;
 wire signed [15:0] flow_x,flow_y;
 micolink_parser parser(.clk(clk),.rst_n(rst_n),.tick_ms(tick_ms),.byte_valid(byte_valid),.byte_error(byte_error),.byte_data(byte_data),
  .sample_valid(sample_valid),.raw_frame(raw_frame),.payload_range_ok(payload_range_ok),.payload_flow_ok(payload_flow_ok),.time_ms(time_ms),.distance_mm(distance_mm),.module_seq(module_seq),
  .strength(strength),.precision(precision),.tof_status(tof_status),.quality(quality),.flow_status(flow_status),
  .flow_x(flow_x),.flow_y(flow_y),.samples(samples),.checksum_errors(checksum_errors),.length_errors(length_errors),.uart_errors(uart_errors),.timeouts(timeouts));
 // 模块龄只在接受到不同时间戳时归零，重复帧无法持续刷新新鲜度。
 reg [31:0] age_ms=32'hffffffff,age_previous_time=0;reg age_seen=0;
 always @(posedge clk)begin
  if(!rst_n)begin age_ms<=32'hffffffff;age_previous_time<=0;age_seen<=0;end
  else if(sample_valid && (!age_seen || time_ms!=age_previous_time))begin
   age_ms<=0;age_previous_time<=time_ms;age_seen<=1;
  end else if(tick_ms && age_ms!=32'hffffffff)age_ms<=age_ms+1'b1;
 end
 // P2 页面模块离线显示与度量/控制新鲜度分别判定。
 // 在线显示阈值为 1000 ms，度量新鲜度阈值为 200 ms；导航层另有更严格的控制门限。
 wire module_online=samples!=0 && age_ms<1000;
 wire link_fresh=samples!=0 && age_ms<200;
 wire range_ok,flow_ok,integrated,saturated;
 wire [31:0] dt_ms,missing,duplicates,restarts,integration_breaks;
 wire signed [31:0] vx_x100,vy_x100;wire signed [63:0] x_x100000,y_x100000;
 // 即使旧源龄已经过期，新校验帧在提交边沿仍可形成度量。
 // previous_ok 会阻止跨越旧数据失效区间的积分。
 mtf_metric_observer #(.PRECHECKED_RANGE(1),.PRECHECKED_FLOW(1)) metric(.clk(clk),.rst_n(rst_n),.sample_valid(sample_valid),.link_fresh(link_fresh || sample_valid),
  .payload_range_ok(payload_range_ok),.payload_flow_ok(payload_flow_ok),
  .time_ms(time_ms),.distance_mm(distance_mm),.module_seq(module_seq),.tof_status(tof_status),.flow_status(flow_status),.quality(quality),
  .flow_x(flow_x),.flow_y(flow_y),.range_numeric_ok(range_ok),.flow_numeric_ok(flow_ok),.dt_ms(dt_ms),
  .missing(missing),.duplicates(duplicates),.restarts(restarts),.integration_breaks(integration_breaks),
  .vx_x100(vx_x100),.vy_x100(vy_x100),.velocity_range_ok(metric_velocity_range_ok),.x_x100000(x_x100000),.y_x100000(y_x100000),.integrated(integrated),.saturated(saturated));
 // 只在度量提交后公开原生观测元组，保持距离、速度、间隔及资格的一致性。
 // 解析与整数度量算法固定，诊断版本及控制契约字段由参数配置。
 // 延迟一拍发布 metric_sample_valid，使速度、间隔及其范围标志在度量提交后保持一致。
 reg metric_commit=0;
 always @(posedge clk) if(!rst_n)metric_commit<=0;else metric_commit<=sample_valid;
 assign metric_sample_valid=metric_commit;
 assign metric_range_valid=range_ok;
 // 累计位移一旦饱和会撤销公开光流资格，避免把异常累计状态继续用于控制。
 assign metric_flow_valid=flow_ok && !saturated;
 assign metric_interval_integrated=integrated;
 assign metric_distance_mm=distance_mm;
 assign metric_dt_ms=dt_ms;
 assign module_age_ms=age_ms;
 assign metric_vx_x100=vx_x100;
 assign metric_vy_x100=vy_x100;
 // 122 字节诊断只冻结显示快照；外部 hold 不阻止解析、源龄与度量状态继续更新。
 // 诊断体为 122 字节，A581 封装另加 2 字节头、2 字节遥测模块序号和 CRC16。
 // 标志由高至低为：饱和、间隔保留位、CONTROL_PATH、PHYSICAL_STOP_LOCK、
 // 最近积分更新、临时光流可用、临时测距可用、模块在线；契约位默认分别为 0/1。
 // 解析提交与度量提交之间的一拍禁止刷新快照，以免混合新帧与旧度量。
 // 快照冻结期间，解析、新鲜度和度量仍按模块频率推进；复用该快照避免重复的 976 位遥测寄存器组。
 always @(posedge clk)begin
  if(STARTUP_ONLY_DIAGNOSTIC_RESET)begin
   // 只有调用方保证复位上电为低且释放后不再拉低，才能启用仅启动复位模式。
   // 复位释放前保持声明时初始化的快照，释放后按正常条件刷新。
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
