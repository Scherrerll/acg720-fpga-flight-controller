`timescale 1ns/1ps
// 移植自 ANO Tech 的 Ano_OF_DecoFusion.c：OF_INS_Get 与 ANO_OF_Fusion 数值算法。
// PMW3901 的旋转补偿、高度及轴向标定由 relative_position 完成；
// 不能直接套用 UP_OF 的 160 像素/度或 0.00012 cm/像素常量。
// 世界坐标 X 指初始前方、Y 指初始右方；速度为 mm/s，加速度为 mm/s²，内部采用 Q16。
// 预测：先按源算法做 5 Hz 线加速度低通，再计算 v += a*dt。
// 校正：e=观测速度-v；i=clip(i+e*dt,±1000 mm/s²)；
// 再计算 v += (2*e+i)*dt，严格保留源算法 FUS_KP=2、FUS_KI=1。
// 源算法质量分数与 PMW3901 的 SQUAL 含义不同；本模块使用上游硬件
// 有效性替代源质量状态机，并禁止跨越失效或过期区间续算。
module ano_flow_fusion #(
 parameter integer CLK_HZ=50000000,AGE_LIMIT=5000000,
 parameter integer VELOCITY_FRAC_BITS=0,
 parameter [7:0] CAL_MASK=0
)(
 input wire clk,rst_n,origin_reset,
 // acc/flow_update 各表示一条新样本；对应 dt_us 均为该样本区间的微秒数。
 input wire acc_update,acc_valid,input wire [31:0] acc_dt_us,
 input wire signed [31:0] ax_mmps2,ay_mmps2,
 input wire flow_update,flow_valid,input wire [31:0] flow_dt_us,
 input wire signed [31:0] observed_vx,observed_vy,
 // 输入观测速度可按 VELOCITY_FRAC_BITS 选择整数或 Q16；公开 fused_vx/vy 为整数 mm/s。
 // fused_vx/vy_q16 保留 Q16 精度；update 为提交脉冲，flow_correction_update 标识光流校正。
 output wire valid,output reg qualified_valid=0,output reg update,flow_correction_update,
 output reg signed [31:0] fused_vx,fused_vy,
 output reg signed [30:0] fused_vx_q16,fused_vy_q16,
 output reg [15:0] reason);
 localparam signed [31:0] INPUT_V_LIMIT=32'sd10000<<<VELOCITY_FRAC_BITS;
 initial if(VELOCITY_FRAC_BITS!=0 && VELOCITY_FRAC_BITS!=16)$error("Unsupported velocity fraction bits");
 reg [31:0] age=32'hffffffff;
 // 两种输入各保留一个待办样本；时段资格随样本锁存，禁止故障前后的区间混用。
 // age 按 clk 拍计数，只由已完成的光流校正刷新；超时会清除融合连续性。
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
 // 实时有效性直接屏蔽输出；内部使用寄存后的 cleanup 清理，避免上游
 // 传感器健康判断路径直接扇出到 64 位算术寄存器的使能和复位端。
 reg cleanup=1;
 always @(posedge clk) if(!rst_n) cleanup<=1;else cleanup<=cancel;
 assign valid=good_sources && !origin_reset && !cleanup && seen && continuity && age<AGE_LIMIT && !overrun;
 always @(posedge clk)if(!rst_n || origin_reset)qualified_valid<=0;else qualified_valid<=valid;
 wire bad_acc_callback=acc_update && (acc_pending || acc_dt_us==0 || acc_dt_us>100000 || ax_mmps2< -30000 || ax_mmps2>30000 || ay_mmps2< -30000 || ay_mmps2>30000);
 wire bad_flow_callback=flow_update && (flow_pending || flow_dt_us<1000 || flow_dt_us>100000 || observed_vx< -INPUT_V_LIMIT || observed_vx>INPUT_V_LIMIT || observed_vy< -INPUT_V_LIMIT || observed_vy>INPUT_V_LIMIT);
 position_multiply m(.clk(clk),.rst_n(rst_n),.start(mul_start),.cancel(cleanup),.a(ma),.b(mb),.busy(mbusy),.done(md),.result(product));
 position_divide d(.clk(clk),.rst_n(rst_n),.start(div_start),.cancel(cleanup),.numerator(num),.denominator(den),.busy(dbusy),.done(dd),.error(derr),.quotient(quotient));
 function signed [63:0] keep64;
 input signed [63:0] a;begin keep64=a;end endfunction
 function signed [63:0] clip;
 input signed [63:0] a,lo,hi;begin clip=a<lo ? lo:a>hi ? hi:a;end endfunction
 // 每次 calc 串行执行 a*b/denominator，100/101 等待乘除完成后跳回 dest。
 task calc;
 input signed [63:0] a,b;input [31:0] denominator;input [7:0] dest;
 begin ma<=a;mb<=b;pending_den<=denominator;return_state<=dest;mul_start<=1;state<=100;end endtask
 initial begin fused_vx_q16=0;fused_vy_q16=0;update=0;flow_correction_update=0;fused_vx=0;fused_vy=0;reason=1;end
 always @(posedge clk) begin
  update<=0;flow_correction_update<=0;mul_start<=0;div_start<=0;
  if(!rst_n || cleanup || age>=AGE_LIMIT && seen) begin
   state<=0;seen<=0;continuity<=0;transaction_epoch_ok<=0;pending_acc_epoch_ok<=0;pending_flow_epoch_ok<=0;age<=32'hffffffff;flow_pending<=0;acc_pending<=0;
   vqx_store<=keep64(0);vqy_store<=keep64(0);iqx_store<=keep64(0);iqy_store<=keep64(0);aqx_store<=keep64(0);aqy_store<=keep64(0);fused_vx<=0;fused_vy<=0;fused_vx_q16<=0;fused_vy_q16<=0;
   reason<=!good_sources ? 1:origin_reset ? 2:overrun ? 4:8;
   if(!rst_n || origin_reset) overrun<=0;
   // 新的有效记录允许恢复，但不能对中断缺口补做积分。
   if(rst_n && !origin_reset && good_sources && flow_update) begin overrun<=0;seen<=1;age<=0;continuity<=0;end
  end else begin
   if(age!=32'hffffffff) age<=age+1'b1;
   // 回调过密、时长非法或数值越界即锁存溢出，后续提交阶段还会再复核。
   if(acc_update) begin
    if(bad_acc_callback) begin overrun<=1;reason<=4;end
    else begin acc_pending<=1;pax<=ax_mmps2;pay<=ay_mmps2;padt<=acc_dt_us;pending_acc_epoch_ok<=good_sources && !origin_reset && !overrun;end
   end
   if(flow_update) begin
    if(bad_flow_callback) begin overrun<=1;reason<=4;end
    else begin flow_pending<=1;pvx<=observed_vx;pvy<=observed_vy;pfdt<=flow_dt_us;pending_flow_epoch_ok<=good_sources && !origin_reset && !overrun;end
   end
   case(state)
    // 空闲优先处理加速度预测，其次处理光流校正；均完整消费锁存的数据组。
    0:if(acc_pending) begin
     correcting<=0;acc_pending<=0;transaction_epoch_ok<=pending_acc_epoch_ok;hx_store<=keep64($signed(pax)*65536);hy_store<=keep64($signed(pay)*65536);dt<=padt;
     calc($signed({1'b0,padt})*314,65536,10000000+padt*314,1);
    end else if(flow_pending) begin
     correcting<=1;flow_pending<=0;transaction_epoch_ok<=pending_flow_epoch_ok;dt<=pfdt;errx_store<=keep64(($signed({{32{pvx[31]}},pvx})<<<(16-VELOCITY_FRAC_BITS))-vqx);erry_store<=keep64(($signed({{32{pvy[31]}},pvy})<<<(16-VELOCITY_FRAC_BITS))-vqy);
     if(!seen || !continuity) begin
      // 沿用源算法从零恢复的状态，不猜测初始速度。
      seen<=1;continuity<=1;age<=0;reason<=0;state<=20;
      vqx_store<=keep64(0);vqy_store<=keep64(0);iqx_store<=keep64(0);iqy_store<=keep64(0);
     end else calc(($signed({{32{pvx[31]}},pvx})<<<(16-VELOCITY_FRAC_BITS))-vqx,$signed({1'b0,pfdt}),1000000,10);
    end
    // 状态 1..5：按实际 dt 求 5 Hz 低通系数，更新两轴加速度后对速度积分。
    1:begin alpha_store<=keep64(value);calc(hx-aqx,value,65536,2);end
    2:begin aqx_store<=keep64(aqx+value);calc(hy-aqy,alpha,65536,3);end
    3:begin aqy_store<=keep64(aqy+value);calc(aqx,$signed({1'b0,dt}),1000000,4);end
    4:begin vqx_store<=keep64(clip(vqx+value,-655360000,655360000));calc(aqy,$signed({1'b0,dt}),1000000,5);end
    5:begin vqy_store<=keep64(clip(vqy+value,-655360000,655360000));state<=20;end
    // 状态 10..13：对两轴速度误差积分限幅，再用比例加积分项校正融合速度。
    10:begin iqx_store<=keep64(clip(iqx+value,-65536000,65536000));calc(erry,$signed({1'b0,dt}),1000000,11);end
    11:begin iqy_store<=keep64(clip(iqy+value,-65536000,65536000));calc(errx*2+iqx,$signed({1'b0,dt}),1000000,12);end
    12:begin vqx_store<=keep64(clip(vqx+value,-655360000,655360000));calc(erry*2+iqy,$signed({1'b0,dt}),1000000,13);end
    13:begin vqy_store<=keep64(clip(vqy+value,-655360000,655360000));age<=0;seen<=1;continuity<=1;reason<=0;state<=20;end
    // 事务仅在来源、时段和当前回调仍合法时统一提交；避免发布已被取消的旧结果。
    20:begin
     transaction_epoch_ok<=0;state<=0;
     if(!good_sources || origin_reset || overrun || bad_acc_callback || bad_flow_callback || !transaction_epoch_ok || dt==0 || dt>100000 || correcting && dt<1000)begin overrun<=1;seen<=0;continuity<=0;reason<=4;end
     else begin fused_vx<=vqx/65536;fused_vy<=vqy/65536;fused_vx_q16<=vqx_store;fused_vy_q16<=vqy_store;update<=1;flow_correction_update<=correcting;end
    end
    100:if(md) begin num<=product;den<=pending_den;div_start<=1;state<=101;end
    101:if(dd) begin if(derr) begin overrun<=1;reason<=4;state<=0;end else begin value<=quotient;state<=return_state;end end
    default:state<=0;
   endcase
  end
 end
endmodule
