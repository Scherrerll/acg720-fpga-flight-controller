`timescale 1ns/1ps
// Passive A584 diagnostic link. No ready/backpressure is exposed to producers.
// Per-type two-entry queues retain capture ticks while an unrelated long frame
// is transmitted. Payload storage is split into 64-bit banks; the shared path
// selects only bytes, never multiplexes/copies an entire maximum-size frame.
module diagnostic_uart #(
 parameter integer BIT_TICKS=54,
 parameter integer STATUS_PERIOD_TICKS=50000000
)(
 input wire clk,rst_n,
 input wire raw_valid,input wire [207:0] raw_body,input wire [31:0] raw_tick,
 input wire pose_valid,input wire [223:0] pose_body,input wire [31:0] pose_tick,
 input wire fault_valid,input wire [703:0] fault_body,input wire [31:0] fault_tick,
 input wire [31:0] clock_ticks,max_accept_gap,raw_count,pose_count,
 input wire [63:0] uptime_ms,input wire [31:0] build_id,
 output wire tx
);
 localparam IDLE=0,SEND=1,WAIT_BYTE=2;
 localparam STATUS_BITS=STATUS_PERIOD_TICKS<=1 ? 1:$clog2(STATUS_PERIOD_TICKS);
 reg [STATUS_BITS-1:0] status_timer=0;
 wire status_due=status_timer==STATUS_PERIOD_TICKS-1;
 reg [31:0] dropped_raw=0,dropped_pose=0,dropped_fault=0,dropped_status=0;
 // A frozen fault retries without counting each retry as a loss. If its
 // producer starts a new window before enqueue, count that canceled event.
 reg fault_enqueued=0,fault_waiting_seen=0;
 wire [319:0] status_body={uptime_ms,build_id,dropped_raw,dropped_pose,
  dropped_fault,dropped_status,max_accept_gap,raw_count,pose_count};
 reg [1:0] state=IDLE,round_robin=0;
 reg [2:0] frame_type=0;
 reg [7:0] byte_index=0,payload_length=0;
 reg [15:0] transmit_sequence=0,crc=16'hffff;
 reg [31:0] capture_tick=0;
 reg byte_start=0;reg [7:0] byte_data=0;
 wire byte_busy,byte_done;
 wire frame_done=state==WAIT_BYTE && byte_done && byte_index==payload_length+11;
 wire [3:0] pop={frame_done && frame_type==4,frame_done && frame_type==3,
  frame_done && frame_type==2,frame_done && frame_type==1};
 wire [3:0] available,ready;
 wire [7:0] raw_byte,pose_byte,fault_byte,status_byte;
 wire [31:0] raw_head_tick,pose_head_tick,fault_head_tick,status_head_tick;
 wire [6:0] payload_index=byte_index-8'd10;
 wire enqueue_fault=fault_valid && !fault_enqueued && ready[2];
 diagnostic_packet_queue #(.PAYLOAD_BYTES(26)) raw_queue(
  .clk(clk),.rst_n(rst_n),.push(raw_valid),.body(raw_body),.tick(raw_tick),
  .pop(pop[0]),.ready(ready[0]),.available(available[0]),
  .read_index(payload_index),.read_byte(raw_byte),.head_tick(raw_head_tick));
 diagnostic_packet_queue #(.PAYLOAD_BYTES(28)) pose_queue(
  .clk(clk),.rst_n(rst_n),.push(pose_valid),.body(pose_body),.tick(pose_tick),
  .pop(pop[1]),.ready(ready[1]),.available(available[1]),
  .read_index(payload_index),.read_byte(pose_byte),.head_tick(pose_head_tick));
 diagnostic_packet_queue #(.PAYLOAD_BYTES(88)) fault_queue(
  .clk(clk),.rst_n(rst_n),.push(enqueue_fault),.body(fault_body),.tick(fault_tick),
  .pop(pop[2]),.ready(ready[2]),.available(available[2]),
  .read_index(payload_index),.read_byte(fault_byte),.head_tick(fault_head_tick));
 diagnostic_packet_queue #(.PAYLOAD_BYTES(40)) status_queue(
  .clk(clk),.rst_n(rst_n),.push(status_due),.body(status_body),.tick(clock_ticks),
  .pop(pop[3]),.ready(ready[3]),.available(available[3]),
  .read_index(payload_index),.read_byte(status_byte),.head_tick(status_head_tick));
 diagnostic_uart_byte_tx #(.BIT_TICKS(BIT_TICKS)) transmitter(
  .clk(clk),.rst_n(rst_n),.start(byte_start),.data(byte_data),
  .tx(tx),.busy(byte_busy),.done(byte_done));
 function [15:0] crc_byte;
 input [15:0] old;input [7:0] value;
 integer bit_number;reg [15:0] c;
 begin
  c=old^{value,8'd0};
  for(bit_number=0;bit_number<8;bit_number=bit_number+1)
   c=c[15] ? (c<<1)^16'h1021:c<<1;
  crc_byte=c;
 end endfunction
 reg found;reg [1:0] choice;integer offset,queue_index;
 always @*begin
  found=0;choice=0;
  for(offset=0;offset<4;offset=offset+1)begin
   queue_index=round_robin+offset;
   if(queue_index>=4)queue_index=queue_index-4;
   if(!found && available[queue_index])begin found=1;choice=queue_index[1:0];end
  end
 end
 reg [7:0] next_byte;
 always @*begin
  next_byte=0;
  case(byte_index)
   0:next_byte=8'ha5;1:next_byte=8'h84;2:next_byte=8'd1;
   3:next_byte={5'd0,frame_type};4:next_byte=transmit_sequence[15:8];5:next_byte=transmit_sequence[7:0];
   6:next_byte=capture_tick[31:24];7:next_byte=capture_tick[23:16];
   8:next_byte=capture_tick[15:8];9:next_byte=capture_tick[7:0];
   default:begin
    if(byte_index==payload_length+10)next_byte=crc[15:8];
    else if(byte_index==payload_length+11)next_byte=crc[7:0];
    else case(frame_type)
     1:next_byte=raw_byte;2:next_byte=pose_byte;
     3:next_byte=fault_byte;4:next_byte=status_byte;
     default:next_byte=0;
    endcase
   end
  endcase
 end
 initial begin
  if(BIT_TICKS<2 || STATUS_PERIOD_TICKS<1)$error("Unsupported diagnostic UART timing");
 end
 always @(posedge clk)begin
  byte_start<=0;
  if(!rst_n)begin
   status_timer<=0;dropped_raw<=0;dropped_pose<=0;dropped_fault<=0;dropped_status<=0;
   fault_enqueued<=0;fault_waiting_seen<=0;state<=IDLE;round_robin<=0;frame_type<=0;
   byte_index<=0;payload_length<=0;transmit_sequence<=0;crc<=16'hffff;capture_tick<=0;
   byte_start<=0;byte_data<=0;
  end else begin
   if(status_due)status_timer<=0;else status_timer<=status_timer+1'b1;
   if(raw_valid && !ready[0] && dropped_raw!=32'hffffffff)dropped_raw<=dropped_raw+1'b1;
   if(pose_valid && !ready[1] && dropped_pose!=32'hffffffff)dropped_pose<=dropped_pose+1'b1;
   if(status_due && !ready[3] && dropped_status!=32'hffffffff)dropped_status<=dropped_status+1'b1;
   if(!fault_valid)begin
    if(fault_waiting_seen && !fault_enqueued && dropped_fault!=32'hffffffff)
     dropped_fault<=dropped_fault+1'b1;
    fault_enqueued<=0;fault_waiting_seen<=0;
   end else if(enqueue_fault)begin fault_enqueued<=1;fault_waiting_seen<=0;end
   else if(!fault_enqueued)fault_waiting_seen<=1;
   case(state)
    IDLE:if(found)begin
     frame_type<={1'b0,choice}+3'd1;byte_index<=0;crc<=16'hffff;
     case(choice)
      0:begin payload_length<=26;capture_tick<=raw_head_tick;end
      1:begin payload_length<=28;capture_tick<=pose_head_tick;end
      2:begin payload_length<=88;capture_tick<=fault_head_tick;end
      3:begin payload_length<=40;capture_tick<=status_head_tick;end
     endcase
     round_robin<=choice+1'b1;state<=SEND;
    end
    SEND:if(!byte_busy)begin
     byte_data<=next_byte;byte_start<=1;
     if(byte_index>=2 && byte_index<payload_length+10)crc<=crc_byte(crc,next_byte);
     state<=WAIT_BYTE;
    end
    WAIT_BYTE:if(byte_done)begin
     if(frame_done)begin transmit_sequence<=transmit_sequence+1'b1;state<=IDLE;end
     else begin byte_index<=byte_index+1'b1;state<=SEND;end
    end
    default:state<=IDLE;
   endcase
  end
 end
endmodule

// Two packet slots, independent of UART service. Each 64-bit bank has only
// two entries and an 8:1 byte selector; arbitration above sees four byte buses.
module diagnostic_packet_queue #(parameter integer PAYLOAD_BYTES=26)(
 input wire clk,rst_n,push,input wire [PAYLOAD_BYTES*8-1:0] body,input wire [31:0] tick,
 input wire pop,output wire ready,available,
 input wire [6:0] read_index,output reg [7:0] read_byte,
 output wire [31:0] head_tick
);
 localparam BANKS=(PAYLOAD_BYTES+7)/8,PAD_BITS=BANKS*64;
 reg write_pointer=0,read_pointer=0;reg [1:0] count=0;
 reg [31:0] tick_memory[0:1];
 wire write_item=push && ready,read_item=pop && available;
 assign available=count!=0;assign ready=count<2 || read_item;
 assign head_tick=tick_memory[read_pointer];
 wire [PAD_BITS-1:0] padded_body={body,{(PAD_BITS-PAYLOAD_BYTES*8){1'b0}}};
 wire [BANKS*8-1:0] bank_byte;
 genvar bank;
 generate for(bank=0;bank<BANKS;bank=bank+1)begin:payload_bank
  reg [63:0] memory[0:1];
  wire [63:0] head_word=memory[read_pointer];
  wire [7:0] selected_byte=head_word[63-read_index[2:0]*8 -:8];
  assign bank_byte[bank*8+:8]=read_index[6:3]==bank ?selected_byte:8'd0;
  always @(posedge clk)if(write_item)memory[write_pointer]<=padded_body[PAD_BITS-1-bank*64 -:64];
 end endgenerate
 integer b;
 always @*begin
  read_byte=0;
  for(b=0;b<BANKS;b=b+1)read_byte=read_byte|bank_byte[b*8+:8];
  if(read_index>=PAYLOAD_BYTES)read_byte=0;
 end
 always @(posedge clk)begin
  if(!rst_n)begin write_pointer<=0;read_pointer<=0;count<=0;end
  else begin
   if(write_item)begin tick_memory[write_pointer]<=tick;write_pointer<=!write_pointer;end
   if(read_item)read_pointer<=!read_pointer;
   case({write_item,read_item})
    2'b10:count<=count+1'b1;2'b01:count<=count-1'b1;default:count<=count;
   endcase
  end
 end
endmodule

// Independent 8N1 transmitter: 50MHz/54 = 925925.93 baud (+0.47% nominal).
module diagnostic_uart_byte_tx #(parameter integer BIT_TICKS=54)(
 input wire clk,rst_n,start,input wire [7:0] data,
 output reg tx=1,output reg busy=0,output reg done=0
);
 localparam TIMER_BITS=BIT_TICKS<=2 ?1:$clog2(BIT_TICKS);
 reg [TIMER_BITS-1:0] timer=0;reg [3:0] bit_number=0;reg [9:0] shift=10'h3ff;
 always @(posedge clk)begin
  done<=0;
  if(!rst_n)begin tx<=1;busy<=0;done<=0;timer<=0;bit_number<=0;shift<=10'h3ff;end
  else if(!busy)begin
   if(start)begin tx<=0;busy<=1;timer<=BIT_TICKS-1;bit_number<=0;shift<={1'b1,data,1'b0};end
  end else if(timer!=0)timer<=timer-1'b1;
  else if(bit_number==9)begin tx<=1;busy<=0;done<=1;end
  else begin tx<=shift[1];shift<={1'b1,shift[9:1]};bit_number<=bit_number+1'b1;timer<=BIT_TICKS-1;end
 end
endmodule
