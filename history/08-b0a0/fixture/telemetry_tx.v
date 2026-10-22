// Independent resource trial. Do not install without complete top-level PNR.
// A579224 bytes preserved; independent A57A32 follows the same snapshot/sequence.
// Each XOR excludes its two header bytes: A579[2:222], A57A[2:30].
module telemetry_tx #(parameter integer FLIGHT_INFO=0,parameter integer PERIOD=5000000,parameter integer RANGE_DIAGNOSTICS=0,parameter integer EXTERNAL_SNAPSHOT=0)(
 input wire clk,input wire [863:0] core_body,input wire [887:0] extension,
 input wire [215:0] acceleration_body,
 input wire [343:0] range_diagnostic_body,
 input wire [271:0] flight_info_body,
 output wire tx,output wire snapshot_hold
);
 reg [31:0] ticks=0;reg [15:0] sample_sequence=0;
 reg [2:0] state=0;reg start=0;wire busy;
 reg [63:0] byte_bank=0;
 reg [7:0] index=0,checksum=0,data=0;
 reg sending_range=0,sending_info=0;
 reg [15:0] crc=16'hffff;
 function [15:0] crc_byte;
 input [15:0] previous;input [7:0] octet;
 reg [15:0] c;integer k;
 begin c=previous ^ {octet,8'd0};for(k=0;k<8;k=k+1)c=c[15] ? (c<<1)^16'h1021:c<<1;crc_byte=c;end
 endfunction
 reg [271:0] info_storage=0;
 always @(posedge clk) if(snapshot_begin) info_storage<=flight_info_body;
 wire [319:0] info_packet={16'ha580,snapshot_sequence,info_storage,16'd0};
 wire snapshot_begin=state==0 && ticks>=PERIOD;
 wire frame_complete=state==4 && !busy && (sending_info ? index==39 : sending_range ? index==47 && !FLIGHT_INFO : index==255 && !RANGE_DIAGNOSTICS && !FLIGHT_INFO);
 // Release the upstream stage on the final completion edge. This guarantees
 // a fresh tuple even when PERIOD is shorter than the serial frame duration.
 assign snapshot_hold=EXTERNAL_SNAPSHOT && (state!=0 || ticks>=PERIOD) && !frame_complete;
 reg [15:0] snapshot_sequence=0;
 always @(posedge clk)if(snapshot_begin)snapshot_sequence<=sample_sequence;
 wire [2047:0] packet;wire [383:0] range_packet;
 generate if(EXTERNAL_SNAPSHOT)begin: caller_snapshot
  assign packet={16'ha579,snapshot_sequence,core_body,extension,8'd0,
                 16'ha57a,snapshot_sequence,acceleration_body,8'd0};
  assign range_packet={16'ha57b,snapshot_sequence,range_diagnostic_body,8'd0};
 end else begin: local_snapshot
  // Legacy callers need no hold contract; retain their own atomic snapshot.
  reg [2047:0] packet_storage=0;reg [383:0] range_storage=0;
  always @(posedge clk)if(snapshot_begin)begin
   packet_storage<={16'ha579,sample_sequence,core_body,extension,8'd0,
                    16'ha57a,sample_sequence,acceleration_body,8'd0};
   if(RANGE_DIAGNOSTICS)range_storage<={16'ha57b,sample_sequence,range_diagnostic_body,8'd0};
  end
  assign packet=packet_storage;assign range_packet=range_storage;
 end endgenerate




 wire [7:0] selected_byte=byte_bank[63-index[2:0]*8 -:8];
 uart_tx_115200 uart(.clk(clk),.start(start),.data(data),.tx(tx),.busy(busy));
 always @(posedge clk) begin
  start<=0;
  if(ticks<PERIOD) ticks<=ticks+1'b1;
  case(state)
   0:if(ticks>=PERIOD) begin


    sending_range<=0;sending_info<=0;
    sample_sequence<=sample_sequence+1'b1;
    index<=0;checksum<=0;ticks<=0;state<=5;
   end
   5:state<=1; // Preserve the previously qualified first-byte delay.
   // A registered eight-byte bank breaks the 256-to-1 byte mux into two
   // stages. The complete packet stays unchanged until the next snapshot.
   1:begin
    byte_bank<=sending_info ? info_packet[319-index[5:3]*64 -:64] : sending_range ? range_packet[383-index[5:3]*64 -:64] : packet[2047-index[7:3]*64 -:64];
    state<=2;
   end
   2:if(!busy) begin
    data<=sending_info ? (index==38 ? crc[15:8]:index==39 ? crc[7:0]:selected_byte) : (sending_range ? index==47 : (index==223 || index==255)) ? checksum:selected_byte;
    start<=1;state<=3;
    if(sending_info) begin
     if(index>=2 && index<38) crc<=crc_byte(crc,selected_byte);
    end else if(sending_range) begin
     if(index>=2 && index<47) checksum<=checksum^selected_byte;
    end else begin
     if(index==224) checksum<=0;
     else if((index>=2 && index<223) || (index>=226 && index<255)) checksum<=checksum^selected_byte;
    end
   end
   3:if(busy) state<=4;
   4:if(!busy) begin
    if(sending_info && index==39) state<=0;
    else if(sending_range && index==47) begin
     if(FLIGHT_INFO) begin sending_info<=1;index<=0;crc<=16'hffff;state<=1;end
     else state<=0;
    end
    else if(!sending_range && !sending_info && index==255) begin
     if(RANGE_DIAGNOSTICS) begin sending_range<=1;index<=0;checksum<=0;state<=1;end
     else if(FLIGHT_INFO) begin sending_info<=1;index<=0;crc<=16'hffff;state<=1;end
     else state<=0;
    end else begin index<=index+1'b1;state<=1;end
   end
  endcase
 end
endmodule
