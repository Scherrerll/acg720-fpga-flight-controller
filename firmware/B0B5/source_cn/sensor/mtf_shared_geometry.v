// 算术资源试验副本：将乘法器接口外置，由调用方共享乘法资源；保留原几何算法次序。
`timescale 1ns/1ps
// MTF 原生观测几何换算层，不引入经验光流或测距系数。
// 机体系 X 向前、Y 向右；相对世界系 X/Y 为初始前向/右向，以输入机体偏航角旋转。
// distance_mm/height_mm 单位为 mm，dt_ms 为 ms，dt_us 为 us；
// vx_x100/vy_x100 为 mm/s×100，body_*_q16/world_*_q16 为 mm/s 的有符号 Q16 值。
// roll_cdeg/pitch_cdeg/body_yaw_cdeg 单位为 0.01 度；clk 仅支持 50 MHz，rst_n 低有效同步复位。
// sample_valid 启动一组完整观测计算；update 在一致输出提交时脉冲一拍，busy 期间不得重入。
// AGE_LIMIT/MAX_COMPUTE_TICKS 按时钟拍计数；origin_reset 清除观测历元和输出。
// 不假定出厂速度已经陀螺补偿，rotation_compensated 与 control_verified 固定为零。
module mtf_shared_geometry #(
 parameter integer CLK_HZ=50000000,AGE_LIMIT=5000000,
 parameter integer MAX_COMPUTE_TICKS=10000,
 parameter integer HEIGHT_TILT_LIMIT_CDEG=1500,FLOW_TILT_LIMIT_CDEG=1500,
 parameter integer SWAP_AXES=0,NEGATE_X=0,NEGATE_Y=0,MAPPING_VERIFIED=0,PRECHECKED_YAW_RANGE=0,PRECHECKED_HEIGHT_TILT4500=0,PRECHECKED_FLOW_TILT1500=0,PRECHECKED_INPUT_VELOCITY=0
)(
 input wire clk,rst_n,origin_reset,sample_valid,range_valid,flow_valid,
 input wire [31:0] distance_mm,dt_ms,
 input wire signed [31:0] vx_x100,vy_x100,
 input wire velocity_range_ok,
 input wire pose_valid,
 input wire signed [15:0] roll_cdeg,pitch_cdeg,body_yaw_cdeg,
 input wire body_yaw_range_ok,
 output reg update=0,
 output wire height_ready,flow_ready,
 output wire [15:0] reason,
 output reg signed [31:0] height_mm=0,
 output reg signed [31:0] body_vx_q16=0,
 output reg signed [31:0] body_vy_q16=0,
 output reg signed [31:0] world_vx_q16=0,
 output reg signed [31:0] world_vy_q16=0,
 output reg [31:0] dt_us=0,
 output wire busy,mapping_verified,rotation_compensated,control_verified,
 output wire math_mul_start,math_mul_cancel,
 output wire signed [63:0] math_mul_a,math_mul_b,
 input wire math_mul_busy,math_mul_done,
 input wire signed [63:0] math_mul_result,
 input wire body_tilt4500_ok,body_tilt1500_ok,
 output wire height_ready_state_numeric_tail,
 output wire height_ready_state_numeric_tail_without_live_flags
);
 // 输出各轴速度限制为 ±10000 mm/s；中间寄存器只在边界检查后缩窄，运算口仍做符号扩展。
 localparam signed [63:0] V_LIMIT_Q16=64'sd655360000;
 localparam integer AGE_BITS=$clog2(AGE_LIMIT+1),COMPUTE_BITS=$clog2(MAX_COMPUTE_TICKS+1);
 localparam [AGE_BITS-1:0] AGE_SAT=AGE_LIMIT;
 // PRECHECKED_* 启用时复用调用方的同源比较结果，否则按输入角度实时比较。
 // 高度和光流可采用不同倾角上限；预检查倾角入口分别仅用于 4500/1500 百分之一度配置。
 wire live_yaw_range_ok=PRECHECKED_YAW_RANGE ?body_yaw_range_ok:(body_yaw_cdeg>=-18000 && body_yaw_cdeg<=18000);
 wire live_height_tilt_ok=(PRECHECKED_HEIGHT_TILT4500 && HEIGHT_TILT_LIMIT_CDEG==4500) ?body_tilt4500_ok:(roll_cdeg>=-HEIGHT_TILT_LIMIT_CDEG && roll_cdeg<=HEIGHT_TILT_LIMIT_CDEG && pitch_cdeg>=-HEIGHT_TILT_LIMIT_CDEG && pitch_cdeg<=HEIGHT_TILT_LIMIT_CDEG);
 // 姿态由 pose_valid 显式判定，本层不另设姿态龄资格门限。
 wire pose_ok=pose_valid &&
  live_height_tilt_ok &&
  live_yaw_range_ok;
 wire flow_pose_ok=(PRECHECKED_FLOW_TILT1500 && FLOW_TILT_LIMIT_CDEG==1500) ?body_tilt1500_ok:(roll_cdeg>=-FLOW_TILT_LIMIT_CDEG && roll_cdeg<=FLOW_TILT_LIMIT_CDEG &&
  pitch_cdeg>=-FLOW_TILT_LIMIT_CDEG && pitch_cdeg<=FLOW_TILT_LIMIT_CDEG);
 // 测距有效区间 10..5000 mm，样本间隔有效区间 1..50 ms；速度输入限制为 ±1000000。
 wire range_ok=range_valid && distance_mm>=10 && distance_mm<=5000;
 wire dt_ok=dt_ms>=1 && dt_ms<=50;
 // 默认由本层比较原始有符号 32 位速度；启用 PRECHECKED_INPUT_VELOCITY 后，
 // 调用方必须提供与当前速度字在同一提交边沿生成的 velocity_range_ok。
 wire input_velocity_ok=PRECHECKED_INPUT_VELOCITY ?velocity_range_ok:
  (vx_x100>=-1000000 && vx_x100<=1000000 &&
   vy_x100>=-1000000 && vy_x100<=1000000);
 wire sources_ok=pose_ok && range_ok;
 wire live_flow_ok=flow_valid && flow_pose_ok && range_ok && dt_ok && input_velocity_ok;
 reg seen=0,flow_seen=0,transaction_epoch_ok=0,flow_epoch_ok=0,output_velocity_fault=0,pending_velocity_fault=0;
 reg [AGE_BITS-1:0] publication_age=AGE_SAT;
 reg [COMPUTE_BITS-1:0] compute_age=0;
 reg [15:0] fault=0;
 reg [6:0] state=0;reg [4:0] return_state=0;
 assign busy=state!=0;
 wire overlap=sample_valid && busy;
 wire cancel=origin_reset || !sources_ok || fault!=0 || overlap;
 // 私有除法/三角辅助单元使用寄存一拍的取消信号来限制实时资格信号的扇出。
// 主状态机、外部乘法取消以及公开资格门控仍直接响应实时 cancel。
 reg private_cancel=1;
 always @(posedge clk)if(!rst_n)private_cancel<=1;else private_cancel<=cancel;
 assign mapping_verified=MAPPING_VERIFIED!=0;
 assign rotation_compensated=1'b0;
 // 即使轴向映射已确认，也不能单独据此授予控制资格。
 assign control_verified=1'b0;
 assign height_ready=rst_n && sources_ok && !origin_reset && fault==0 && !overlap && seen && publication_age<AGE_LIMIT;
 // 此尾项供调用方组合；调用方须另加 rst_n、非 origin_reset、range_valid、pose_valid 及姿态龄门控。
 (* syn_keep = 1 *) wire height_ready_state_numeric_tail_kept=
  live_height_tilt_ok && live_yaw_range_ok && distance_mm>=10 && distance_mm<=5000 &&
  fault==0 && !overlap && seen && publication_age<AGE_LIMIT;
 assign height_ready_state_numeric_tail=height_ready_state_numeric_tail_kept;
 // 不含实时标志的状态/数值尾项，供调用方最终组合实时门控。
// 原 height_ready、原尾项以及状态机/取消条件仍保持实时判定。
 (* syn_keep = 1 *) wire height_ready_state_numeric_tail_without_live_flags_kept=
  distance_mm>=10 && distance_mm<=5000 &&
  fault==0 && !overlap && seen && publication_age<AGE_LIMIT;
 assign height_ready_state_numeric_tail_without_live_flags=height_ready_state_numeric_tail_without_live_flags_kept;
 assign flow_ready=height_ready && flow_seen && live_flow_ok;
 // reason 按位合并：0 姿态、1 测距、2 间隔、3 速度、4 光流、5 重入、6 运算故障，
 // 7 未发布、8 映射未确认、9 未做旋转补偿、10 原点复位、11 发布结果过期。
 assign reason=(!pose_ok ? 16'h0001:16'h0000) |
  (!range_ok ? 16'h0002:16'h0000) | (!dt_ok ? 16'h0004:16'h0000) |
  (!input_velocity_ok || output_velocity_fault ? 16'h0008:16'h0000) | (!flow_valid ? 16'h0010:16'h0000) |
  (overlap ? 16'h0020:16'h0000) | fault |
  (!seen ? 16'h0080:16'h0000) | (!MAPPING_VERIFIED ? 16'h0100:16'h0000) |
  16'h0200 | (origin_reset ? 16'h0400:16'h0000) |
  (seen && publication_age>=AGE_LIMIT ? 16'h0800:16'h0000);
 // 锁存一次计算的距离、角度、速度和间隔，避免多周期运算中混入后续输入。
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
 // 外部乘法握手：启动/取消与有符号 64 位操作数送出，完成时取 math_mul_result。
 // 调用方应将 done/result 对应到本次事务；本层在等待状态保持待返回目标。
 assign math_mul_start=mul_start;assign math_mul_cancel=cancel;
 assign math_mul_a=ma;assign math_mul_b=mb;
 assign mbusy=math_mul_busy;assign md=math_mul_done;assign product=math_mul_result;
 mtf_divide100 d(.clk(clk),.rst_n(rst_n),.start(div_start),.cancel(private_cancel),.numerator(num_store),.busy(dbusy),.done(dd),.error(derr),.quotient(quotient));
 position_sincos t(.clk(clk),.rst_n(rst_n),.start(trig_start),.cancel(private_cancel),.angle_q20(angle_q20),.busy(tbusy),.done(td),.sin_q16(sn),.cos_q16(cs));
 // 对已证明范围的有符号 48 位中间值作最近舍入，恰好半单位时远离零。
// 用算术右移后的高位加小数进位实现，避免宽位绝对值、加法、取负级联。
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
 // keep48/keep25/keep14 仅截取已由调用路径范围约束的低位，用于收紧存储位宽。
 function signed [47:0] keep48;
 input signed [63:0] a;begin keep48=a[47:0];end
 endfunction
 function signed [24:0] keep25;
 input signed [63:0] a;begin keep25=a[24:0];end
 endfunction
 function signed [13:0] keep14;
 input signed [63:0] a;begin keep14=a[13:0];end
 endfunction
 // 统一乘法调度：denominator=1 保持乘积，65536 作 Q16 舍入右移，100 交给专用除法器。
 // return_state 保存结果返回点，100/101 状态分别等候乘法和除以 100 完成。
 task calc;
 input signed [63:0] a,b;input [31:0] denominator;input [7:0] dest;
 begin ma_store<=keep48(a);mb_store<=keep25(b);
  scale_mode<=denominator==1 ? 0:denominator==65536 ? 1:2;
  return_state<=dest[4:0];mul_start<=1;state<=100;end
 endtask
 // 无效源、原点复位、重入或运算故障均撤销已发布资格并清空输出，防止跨历元沿用数据。
 task clear_outputs;
 begin
  seen<=0;flow_seen<=0;transaction_epoch_ok<=0;flow_epoch_ok<=0;output_velocity_fault<=0;pending_velocity_fault<=0;
  publication_age<=AGE_SAT;compute_age<=0;state<=0;
  height_mm<=0;body_vx_q16<=0;body_vy_q16<=0;world_vx_q16<=0;world_vy_q16<=0;dt_us<=0;
 end
 endtask
 initial begin
  if(CLK_HZ!=50000000 || AGE_LIMIT<1 || MAX_COMPUTE_TICKS<4000 ||
   HEIGHT_TILT_LIMIT_CDEG<1 || HEIGHT_TILT_LIMIT_CDEG>4500 || FLOW_TILT_LIMIT_CDEG<1 || FLOW_TILT_LIMIT_CDEG>HEIGHT_TILT_LIMIT_CDEG ||
   SWAP_AXES<0 || SWAP_AXES>1 || NEGATE_X<0 || NEGATE_X>1 || NEGATE_Y<0 || NEGATE_Y>1 || MAPPING_VERIFIED<0 || MAPPING_VERIFIED>1)
   $error("Unsupported native MTF geometry configuration");
 end
 // 主状态机优先处理复位/源失效、重入、已锁存故障和计算超时，再推进运算。
 always @(posedge clk)begin
  update<=0;mul_start<=0;div_start<=0;trig_start<=0;
  if(!rst_n || origin_reset || !sources_ok)begin clear_outputs();fault<=0;end
  else if(overlap)begin clear_outputs();fault<=16'h0020;end
  else if(fault!=0)clear_outputs();
  else if(busy && compute_age>=MAX_COMPUTE_TICKS)begin clear_outputs();fault<=16'h0040;end
  else begin
   if(publication_age<AGE_LIMIT)publication_age<=publication_age+1'b1;
   if(busy)compute_age<=compute_age+1'b1;
   // 光流即使短暂失效也撤销当前计算的光流历元资格，未结束的事务不能跨过这段失效。
   if(!live_flow_ok)begin
    flow_epoch_ok<=0;flow_seen<=0;body_vx_q16<=0;body_vy_q16<=0;world_vx_q16<=0;world_vy_q16<=0;dt_us<=0;
   end
   case(state)
    0:if(sample_valid)begin
     held_pitch<=pitch_cdeg;held_yaw<=body_yaw_cdeg;held_distance<=distance_mm[12:0];held_dt<=dt_ok ? dt_ms[5:0]:6'd0;
     // 先在原输入位宽检查范围，再做轴交换/符号翻转并缩窄存储。
     // 原始 32 位最小负数必须先被拒绝，不能因截断回绕而成为合格值。
     held_vx100_store<=!input_velocity_ok ? 21'sd0:NEGATE_X ? -(SWAP_AXES ? $signed(vy_x100):$signed(vx_x100)):
      (SWAP_AXES ? $signed(vy_x100):$signed(vx_x100));
     held_vy100_store<=!input_velocity_ok ? 21'sd0:NEGATE_Y ? -(SWAP_AXES ? $signed(vx_x100):$signed(vy_x100)):
      (SWAP_AXES ? $signed(vx_x100):$signed(vy_x100));
     transaction_epoch_ok<=1;flow_epoch_ok<=live_flow_ok;pending_velocity_fault<=0;compute_age<=0;
     calc($signed(roll_cdeg),64'sd11993813,32'd65536,1);
    end
    // 1..6：百分之一度换算为弧度 Q20，依次求横滚/俯仰余弦及偏航正余弦。
    1:begin angle_q20<=value[31:0];trig_start<=1;state<=2;end
    2:if(td)begin cr<=cs;calc($signed(held_pitch),64'sd11993813,32'd65536,3);end
    3:begin angle_q20<=value[31:0];trig_start<=1;state<=4;end
    4:if(td)begin cp<=cs;calc($signed(held_yaw),64'sd11993813,32'd65536,5);end
    5:begin angle_q20<=value[31:0];trig_start<=1;state<=6;end
    6:if(td)begin cy<=cs;sy<=sn;calc($signed({1'b0,held_distance}),$signed(cr),32'd1,7);end
    // 6..8：高度=距离×cos(横滚)×cos(俯仰)，去掉两次 Q16 小数位后舍入至 mm。
    7:calc(value,$signed(cp),32'd1,8);
    8:begin pending_height_store<=keep14(round_shift32(value));calc(held_vx100,64'sd65536,32'd100,9);end
    // 8..10：原生速度×65536/100 转为机体系 Q16；11..16 依偏航角旋转至世界系。
    // 世界速度为 wx=bx*cos(yaw)-by*sin(yaw)，wy=bx*sin(yaw)+by*cos(yaw)。
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
    // 17：再次检查源、历元及数值范围；一次性提交高度，光流另受全程有效及速度边界约束。
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
    // 等待算术单元结束后按缩放方式取值；超界或除法错误锁存为 0x0040 运算故障。
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
