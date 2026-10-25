`timescale 1ns/1ps
// Volatile shared XY gains. Public value = unsigned wire value / 10000.
// Single outstanding request; host must await the response before another.
module xy_pi_parameters #(parameter integer TIMEOUT_TICKS=1250000)(
 input wire clk,rst_n,rx_valid,rx_error,input wire [7:0] rx_data,
 input wire write_safe,control_boundary,
 output reg [15:0] active_p,active_i,
 output reg [31:0] generation,
 output reg response_valid,output wire [191:0] response,
 input wire response_ready
);
 initial begin active_p=500;active_i=0;generation=0;response_valid=0;end
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
 wire [31:0] sequence_id=frame[79:48];
 wire [15:0] proposed_p=frame[47:32],proposed_i=frame[31:16];
 // Body fields are frozen from state3 through valid/ready ownership. The
 // CRC scans bytes2..21 only; its own changing tail is never consumed.
 assign response={16'ha591,8'd1,opcode,8'd24,status,sequence_id,
  active_p,active_i,generation,32'h0000b0b3,reply_crc};
 always @(posedge clk)begin
  if(!rst_n)begin
   active_p<=500;active_i<=0;generation<=0;response_valid<=0;
   count<=0;age<=0;highwater<=0;seen_set<=0;frame<=0;crc<=16'hffff;
   reply_crc<=16'hffff;crc_index<=0;state<=0;status<=0;
  end else begin
   if(response_valid && response_ready)response_valid<=0;
   case(state)
    0:if(!response_valid)begin
     if(count!=0)begin
      if(age>=TIMEOUT_TICKS-1)begin count<=0;crc<=16'hffff;end
      else age<=age+1'b1;
     end
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
       if(count<14)crc<=crc_byte(crc,rx_data);
       if(count==15)begin count<=0;state<=1;end else count<=count+1'b1;
      end
     end
    end
    1:begin
     // Malformed and rejected SETs never touch the gain registers.
     status<=0;
     if(frame[15:0]!=crc)begin status<=2;state<=3;end
     else if(frame[111:104]!=1 || frame[95:88]!=16 || frame[87:80]!=0)begin status<=1;state<=3;end
     else if(opcode!=1 && opcode!=2)begin status<=6;state<=3;end
     else if(opcode==1)begin
      if(proposed_p!=0 || proposed_i!=0)status<=1;
      state<=3;
     end else if(seen_set && sequence_id<=highwater)begin status<=5;state<=3;end
     else begin
      // Consume every well-formed fresh SET sequence, including rejections.
      // A delayed/repeated rejected command must never become a later write.
      highwater<=sequence_id;seen_set<=1;
      if(proposed_p>10000 || proposed_i>10000)begin status<=3;state<=3;end
      else if(!write_safe)begin status<=4;state<=3;end
      else state<=2;
     end
    end
    2:begin
     // Recheck on the actual atomic commit edge (including arm races).
     if(!write_safe)begin status<=4;state<=3;end
     else if(control_boundary)begin
      active_p<=proposed_p;active_i<=proposed_i;generation<=generation+1'b1;
      state<=3;
     end
    end
    3:begin
     // Preserve the original post-commit CRC/valid schedule; no second
     // copy of fields already frozen by the bank state is needed.
     reply_crc<=16'hffff;crc_index<=2;state<=4;
    end
    4:begin
     reply_crc<=crc_byte(reply_crc,response[191-crc_index*8 -:8]);
     if(crc_index==21)state<=5;else crc_index<=crc_index+1'b1;
    end
    5:begin response_valid<=1;state<=0;end
    default:state<=0;
   endcase
  end
 end
endmodule

// Two-flop synchronizer and center sampling, 115200 8N1 at 50MHz.
// Only the asynchronous pad -> first synchronizer D is a false path.
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
