`timescale 1ns/1ps
// XY 共用易失增益：公开参数值等于无符号线值除以 10000。
// 仅允许一个在途请求，主机须收到应答后再发下一条。
// XY 共用易失参数，复位默认 P=0.1000、I=0.0350；线值统一除以 10000。
// 默认接收超时为 1250000 个时钟周期，在 50 MHz 下等于 25 毫秒。
module xy_pi_parameters #(parameter integer TIMEOUT_TICKS=1250000)(
 input wire clk,rst_n,rx_valid,rx_error,input wire [7:0] rx_data,
 // 上层提供写入安全条件；实际成对更新还需等待控制周期边界。
 input wire write_safe,control_boundary,
 output reg [15:0] active_p,active_i,
 output reg [31:0] generation,
 output reg response_valid,output wire [191:0] response,
 input wire response_ready
);
 initial begin active_p=1000;active_i=350;generation=0;response_valid=0;end
 // CRC 按高位先行逐字节计算，初值 FFFF，多项式 1021，无末尾异或。
 function [15:0] crc_byte;
 input [15:0] previous;input [7:0] octet;
 reg [15:0] c;integer k;
 begin c=previous^{octet,8'd0};for(k=0;k<8;k=k+1)c=c[15]?(c<<1)^16'h1021:c<<1;crc_byte=c;end
 endfunction
 reg [4:0] count=0,crc_index=0;
 reg [31:0] age=0,highwater=0;
 reg seen_set=0;
 reg [127:0] frame=0;
 reg [15:0] crc=16'hffff,reply_crc=16'hffff;
 reg [2:0] state=0;
 reg [7:0] status=0;
 wire [7:0] opcode=frame[103:96];
 // SET 序号作为递增高水位比较，复位后清空；同序号或更小序号被拒绝。
 wire [31:0] sequence_id=frame[79:48];
 wire [15:0] proposed_p=frame[47:32],proposed_i=frame[31:16];
 // 从状态 3 到 valid/ready 交接完成，响应体字段始终冻结；
 // CRC 只扫描字节 2～21，不把正在生成的 CRC 尾部再次纳入计算。
 // 响应固定为 24 字节，带当前参数、代次及镜像标识 0000B0B5。
 assign response={16'ha591,8'd1,opcode,8'd24,status,sequence_id,
  active_p,active_i,generation,32'h0000b0b5,reply_crc};
 always @(posedge clk)begin
  if(!rst_n)begin
   active_p<=1000;active_i<=350;generation<=0;response_valid<=0;
   count<=0;age<=0;highwater<=0;seen_set<=0;frame<=0;crc<=16'hffff;
   reply_crc<=16'hffff;crc_index<=0;state<=0;status<=0;
  end else begin
   if(response_valid && response_ready)response_valid<=0;
   case(state)
    // 响应尚未被接收方取走时停止接收新请求，保证单个在途事务。
    0:if(!response_valid)begin
     if(count!=0)begin
      if(age>=TIMEOUT_TICKS-1)begin count<=0;crc<=16'hffff;end
      else age<=age+1'b1;
     end
     // UART 错误或字节等待超时清除半帧，随后重新寻找 A5 90 帧头。
     if(rx_error)begin count<=0;crc<=16'hffff;end
     else if(rx_valid)begin
      age<=0;
      if(count==0 || age>=TIMEOUT_TICKS-1)begin
       if(rx_data==8'ha5)begin frame<=8'ha5;count<=1;crc<=16'hffff;end
      end else if(count==1)begin
       if(rx_data==8'h90)begin frame<={frame[119:0],rx_data};count<=2;end
       else if(rx_data!=8'ha5)count<=0;
      end else begin
       frame<={frame[119:0],rx_data};
       // 请求 CRC 只覆盖字节 2 至 13，跳过两字节帧头与末尾 CRC。
       if(count<14)crc<=crc_byte(crc,rx_data);
       if(count==15)begin count<=0;state<=1;end else count<=count+1'b1;
      end
     end
    end
    1:begin
     // 格式错误或被拒绝的 SET 请求不修改增益寄存器。
     status<=0;
     if(frame[15:0]!=crc)begin status<=2;state<=3;end
     else if(frame[111:104]!=1 || frame[95:88]!=16 || frame[87:80]!=0)begin status<=1;state<=3;end
     else if(opcode!=1 && opcode!=2)begin status<=6;state<=3;end
     // 操作码 1 读取且要求参数字段为零；操作码 2 请求设置参数。
     else if(opcode==1)begin
      if(proposed_p!=0 || proposed_i!=0)status<=1;
      state<=3;
     end else if(seen_set && sequence_id<=highwater)begin status<=5;state<=3;end
     else begin
      // 每个格式正确且新鲜的 SET 序号都会被消耗，包括被拒绝的请求。
      // 避免迟到或重发的拒绝命令在稍后条件变化后变成有效写入。
      // 格式有效的新 SET 即使因范围或安全条件被拒绝，也消耗该序号。
      highwater<=sequence_id;seen_set<=1;
      // 两个增益的线值均只允许 0 至 10000，即公开值 0.0000 至 1.0000。
      if(proposed_p>10000 || proposed_i>10000)begin status<=3;state<=3;end
      else if(!write_safe)begin status<=4;state<=3;end
      else state<=2;
     end
    end
    2:begin
     // 在真正的原子提交沿再次检查安全条件，覆盖与解锁同拍竞争。
     // 等待边界期间逐拍复查安全条件，实际提交沿也必须保持安全。
     if(!write_safe)begin status<=4;state<=3;end
     else if(control_boundary)begin
      // P、I 与代次在同一时钟沿提交，避免控制周期看到新旧参数混用。
      active_p<=proposed_p;active_i<=proposed_i;generation<=generation+1'b1;
      state<=3;
     end
    end
    3:begin
     // 保留原提交后的 CRC/valid 调度，不再复制已经由银行状态
     // 冻结的响应字段。
     reply_crc<=16'hffff;crc_index<=2;state<=4;
    end
    4:begin
     // 响应 CRC 覆盖字节 2 至 21；计算完成后才拉高 response_valid。
     reply_crc<=crc_byte(reply_crc,response[191-crc_index*8 -:8]);
     if(crc_index==21)state<=5;else crc_index<=crc_index+1'b1;
    end
    5:begin response_valid<=1;state<=0;end
    default:state<=0;
   endcase
  end
 end
endmodule

// 两级同步后在位中心采样，50MHz 时钟下采用 115200、8N1 串口格式。
// 仅异步引脚到同步器第一级 D 端的路径设置为假路径。
// UART 接收按位中心采样，8 位数据低位先行，停止位错误只报告 error。
module xy_pi_uart_rx #(parameter integer BIT_TICKS=434)(
 input wire clk,rst_n,rx,output reg valid,error,output reg [7:0] data
);
 (* syn_preserve=1, async_reg="true" *) reg rx_meta=1,rx_sync=1;
 reg [15:0] ticks=0;reg [3:0] bit_index=0;reg [1:0] state=0;
 reg [7:0] shift=0;
 initial begin valid=0;error=0;data=0;end
 always @(posedge clk)begin rx_meta<=rx;rx_sync<=rx_meta;end
 always @(posedge clk)begin
  valid<=0;error<=0;
  if(!rst_n)begin ticks<=0;state<=0;bit_index<=0;shift<=0;data<=0;end
  else case(state)
   0:if(!rx_sync)begin ticks<=BIT_TICKS/2-1;state<=1;end
   1:if(ticks!=0)ticks<=ticks-1'b1;
     else if(rx_sync)state<=0;
     else begin ticks<=BIT_TICKS-1;bit_index<=0;state<=2;end
   2:if(ticks!=0)ticks<=ticks-1'b1;
     else begin
      shift[bit_index]<=rx_sync;ticks<=BIT_TICKS-1;
      if(bit_index==7)state<=3;else bit_index<=bit_index+1'b1;
     end
   3:if(ticks!=0)ticks<=ticks-1'b1;
     else begin
      if(rx_sync)begin data<=shift;valid<=1;state<=0;end
      else begin error<=1;state<=0;end
     end
  endcase
 end
endmodule
