// Independent resource trial. Do not install without complete top-level PNR.
// A579224 bytes preserved; independent A57A32 follows the same snapshot/sequence.
// Each XOR excludes its two header bytes: A579[2:222], A57A[2:30].
module telemetry_tx #(parameter integer ROTATION_INFO=0,parameter integer NAV_CALLER_SNAPSHOT=0,parameter integer MTF_CALLER_SNAPSHOT=0,parameter integer NAV_INFO=0,parameter integer MTF_INFO=0,parameter integer FLIGHT_INFO=0,parameter integer PERIOD=5000000,parameter integer RANGE_DIAGNOSTICS=0,parameter integer EXTERNAL_SNAPSHOT=0)(
 input wire clk,input wire [863:0] core_body,input wire [887:0] extension,
 input wire [215:0] acceleration_body,
 input wire [343:0] range_diagnostic_body,
 input wire [335:0] rotation_body,
 input wire [271:0] flight_info_body,input wire [975:0] mtf_body,input wire [719:0] nav_body,
 output wire tx,output wire snapshot_hold
);
 reg [31:0] ticks=0;reg [15:0] sample_sequence=0;
 reg [2:0] state=0;reg start=0;wire busy;
 reg [63:0] byte_bank=0;
 reg [7:0] index=0,checksum=0,data=0;
 reg sending_rotation=0;
 reg sending_range=0,sending_info=0,sending_mtf=0,sending_nav=0;
 reg [15:0] crc=16'hffff;
 function [15:0] crc_byte;
 input [15:0] previous;input [7:0] octet;
 reg [15:0] c;integer k;
 begin c=previous ^ {octet,8'd0};for(k=0;k<8;k=k+1)c=c[15] ? (c<<1)^16'h1021:c<<1;crc_byte=c;end
 endfunction
 wire [975:0] mtf_snapshot;
 generate if(MTF_CALLER_SNAPSHOT)begin: held_mtf_input
  assign mtf_snapshot=mtf_body;
 end else begin: local_mtf_snapshot
  reg [975:0] mtf_storage=0;
  always @(posedge clk)if(snapshot_begin)mtf_storage<=mtf_body;
  assign mtf_snapshot=mtf_storage;
 end endgenerate
 initial if(MTF_CALLER_SNAPSHOT && !EXTERNAL_SNAPSHOT)$error("Caller-held MTF requires snapshot_hold contract");
 wire [719:0] nav_snapshot;
 generate if(NAV_CALLER_SNAPSHOT)begin: held_nav_input
  assign nav_snapshot=nav_body;
 end else begin: local_nav_snapshot
  reg [719:0] nav_storage=0;
  always @(posedge clk)if(snapshot_begin)nav_storage<=nav_body;
  assign nav_snapshot=nav_storage;
 end endgenerate
 initial if(NAV_CALLER_SNAPSHOT && !EXTERNAL_SNAPSHOT)$error("Caller-held navigation requires snapshot_hold contract");
 wire [383:0] rotation_packet={16'ha583,snapshot_sequence,rotation_body,16'd0};
 wire [767:0] nav_packet={16'ha582,snapshot_sequence,nav_snapshot,16'd0};
 reg [271:0] info_storage=0;
 wire [1023:0] mtf_packet={16'ha581,snapshot_sequence,mtf_snapshot,16'd0};
 always @(posedge clk) if(snapshot_begin) info_storage<=flight_info_body;
 wire [319:0] info_packet={16'ha580,snapshot_sequence,info_storage,16'd0};
 wire snapshot_begin=state==0 && ticks>=PERIOD;
 wire frame_complete=state==4 && !busy && (sending_rotation ? index==47 : sending_nav ? index==95 && !ROTATION_INFO : sending_mtf ? index==127 && !NAV_INFO && !ROTATION_INFO : sending_info ? index==39 && !MTF_INFO && !NAV_INFO && !ROTATION_INFO : sending_range ? index==47 && !FLIGHT_INFO && !MTF_INFO && !NAV_INFO && !ROTATION_INFO : index==255 && !RANGE_DIAGNOSTICS && !FLIGHT_INFO && !MTF_INFO && !NAV_INFO && !ROTATION_INFO);
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




 // Shared one-hot bank decode; preserve packet data and registered latency.
 reg [31:0] bank_select;reg [63:0] decoded_bank;
 always @* begin
  bank_select=32'd1 << index[7:3];decoded_bank=64'd0;
  if(sending_rotation)begin
   decoded_bank=decoded_bank | (rotation_packet[383-:64] & {64{bank_select[0]}});
   decoded_bank=decoded_bank | (rotation_packet[319-:64] & {64{bank_select[1]}});
   decoded_bank=decoded_bank | (rotation_packet[255-:64] & {64{bank_select[2]}});
   decoded_bank=decoded_bank | (rotation_packet[191-:64] & {64{bank_select[3]}});
   decoded_bank=decoded_bank | (rotation_packet[127-:64] & {64{bank_select[4]}});
   decoded_bank=decoded_bank | (rotation_packet[63-:64] & {64{bank_select[5]}});
  end else begin
  decoded_bank=decoded_bank | (nav_packet[767-:64] & {64{bank_select[0] && (sending_nav)}});
  decoded_bank=decoded_bank | (nav_packet[703-:64] & {64{bank_select[1] && (sending_nav)}});
  decoded_bank=decoded_bank | (nav_packet[639-:64] & {64{bank_select[2] && (sending_nav)}});
  decoded_bank=decoded_bank | (nav_packet[575-:64] & {64{bank_select[3] && (sending_nav)}});
  decoded_bank=decoded_bank | (nav_packet[511-:64] & {64{bank_select[4] && (sending_nav)}});
  decoded_bank=decoded_bank | (nav_packet[447-:64] & {64{bank_select[5] && (sending_nav)}});
  decoded_bank=decoded_bank | (nav_packet[383-:64] & {64{bank_select[6] && (sending_nav)}});
  decoded_bank=decoded_bank | (nav_packet[319-:64] & {64{bank_select[7] && (sending_nav)}});
  decoded_bank=decoded_bank | (nav_packet[255-:64] & {64{bank_select[8] && (sending_nav)}});
  decoded_bank=decoded_bank | (nav_packet[191-:64] & {64{bank_select[9] && (sending_nav)}});
  decoded_bank=decoded_bank | (nav_packet[127-:64] & {64{bank_select[10] && (sending_nav)}});
  decoded_bank=decoded_bank | (nav_packet[63-:64] & {64{bank_select[11] && (sending_nav)}});
  decoded_bank=decoded_bank | (mtf_packet[1023-:64] & {64{bank_select[0] && (!sending_nav && sending_mtf)}});
  decoded_bank=decoded_bank | (mtf_packet[959-:64] & {64{bank_select[1] && (!sending_nav && sending_mtf)}});
  decoded_bank=decoded_bank | (mtf_packet[895-:64] & {64{bank_select[2] && (!sending_nav && sending_mtf)}});
  decoded_bank=decoded_bank | (mtf_packet[831-:64] & {64{bank_select[3] && (!sending_nav && sending_mtf)}});
  decoded_bank=decoded_bank | (mtf_packet[767-:64] & {64{bank_select[4] && (!sending_nav && sending_mtf)}});
  decoded_bank=decoded_bank | (mtf_packet[703-:64] & {64{bank_select[5] && (!sending_nav && sending_mtf)}});
  decoded_bank=decoded_bank | (mtf_packet[639-:64] & {64{bank_select[6] && (!sending_nav && sending_mtf)}});
  decoded_bank=decoded_bank | (mtf_packet[575-:64] & {64{bank_select[7] && (!sending_nav && sending_mtf)}});
  decoded_bank=decoded_bank | (mtf_packet[511-:64] & {64{bank_select[8] && (!sending_nav && sending_mtf)}});
  decoded_bank=decoded_bank | (mtf_packet[447-:64] & {64{bank_select[9] && (!sending_nav && sending_mtf)}});
  decoded_bank=decoded_bank | (mtf_packet[383-:64] & {64{bank_select[10] && (!sending_nav && sending_mtf)}});
  decoded_bank=decoded_bank | (mtf_packet[319-:64] & {64{bank_select[11] && (!sending_nav && sending_mtf)}});
  decoded_bank=decoded_bank | (mtf_packet[255-:64] & {64{bank_select[12] && (!sending_nav && sending_mtf)}});
  decoded_bank=decoded_bank | (mtf_packet[191-:64] & {64{bank_select[13] && (!sending_nav && sending_mtf)}});
  decoded_bank=decoded_bank | (mtf_packet[127-:64] & {64{bank_select[14] && (!sending_nav && sending_mtf)}});
  decoded_bank=decoded_bank | (mtf_packet[63-:64] & {64{bank_select[15] && (!sending_nav && sending_mtf)}});
  decoded_bank=decoded_bank | (info_packet[319-:64] & {64{bank_select[0] && (!sending_nav && !sending_mtf && sending_info)}});
  decoded_bank=decoded_bank | (info_packet[255-:64] & {64{bank_select[1] && (!sending_nav && !sending_mtf && sending_info)}});
  decoded_bank=decoded_bank | (info_packet[191-:64] & {64{bank_select[2] && (!sending_nav && !sending_mtf && sending_info)}});
  decoded_bank=decoded_bank | (info_packet[127-:64] & {64{bank_select[3] && (!sending_nav && !sending_mtf && sending_info)}});
  decoded_bank=decoded_bank | (info_packet[63-:64] & {64{bank_select[4] && (!sending_nav && !sending_mtf && sending_info)}});
  decoded_bank=decoded_bank | (range_packet[383-:64] & {64{bank_select[0] && (!sending_nav && !sending_mtf && !sending_info && sending_range)}});
  decoded_bank=decoded_bank | (range_packet[319-:64] & {64{bank_select[1] && (!sending_nav && !sending_mtf && !sending_info && sending_range)}});
  decoded_bank=decoded_bank | (range_packet[255-:64] & {64{bank_select[2] && (!sending_nav && !sending_mtf && !sending_info && sending_range)}});
  decoded_bank=decoded_bank | (range_packet[191-:64] & {64{bank_select[3] && (!sending_nav && !sending_mtf && !sending_info && sending_range)}});
  decoded_bank=decoded_bank | (range_packet[127-:64] & {64{bank_select[4] && (!sending_nav && !sending_mtf && !sending_info && sending_range)}});
  decoded_bank=decoded_bank | (range_packet[63-:64] & {64{bank_select[5] && (!sending_nav && !sending_mtf && !sending_info && sending_range)}});
  decoded_bank=decoded_bank | (packet[2047-:64] & {64{bank_select[0] && (!sending_nav && !sending_mtf && !sending_info && !sending_range)}});
  decoded_bank=decoded_bank | (packet[1983-:64] & {64{bank_select[1] && (!sending_nav && !sending_mtf && !sending_info && !sending_range)}});
  decoded_bank=decoded_bank | (packet[1919-:64] & {64{bank_select[2] && (!sending_nav && !sending_mtf && !sending_info && !sending_range)}});
  decoded_bank=decoded_bank | (packet[1855-:64] & {64{bank_select[3] && (!sending_nav && !sending_mtf && !sending_info && !sending_range)}});
  decoded_bank=decoded_bank | (packet[1791-:64] & {64{bank_select[4] && (!sending_nav && !sending_mtf && !sending_info && !sending_range)}});
  decoded_bank=decoded_bank | (packet[1727-:64] & {64{bank_select[5] && (!sending_nav && !sending_mtf && !sending_info && !sending_range)}});
  decoded_bank=decoded_bank | (packet[1663-:64] & {64{bank_select[6] && (!sending_nav && !sending_mtf && !sending_info && !sending_range)}});
  decoded_bank=decoded_bank | (packet[1599-:64] & {64{bank_select[7] && (!sending_nav && !sending_mtf && !sending_info && !sending_range)}});
  decoded_bank=decoded_bank | (packet[1535-:64] & {64{bank_select[8] && (!sending_nav && !sending_mtf && !sending_info && !sending_range)}});
  decoded_bank=decoded_bank | (packet[1471-:64] & {64{bank_select[9] && (!sending_nav && !sending_mtf && !sending_info && !sending_range)}});
  decoded_bank=decoded_bank | (packet[1407-:64] & {64{bank_select[10] && (!sending_nav && !sending_mtf && !sending_info && !sending_range)}});
  decoded_bank=decoded_bank | (packet[1343-:64] & {64{bank_select[11] && (!sending_nav && !sending_mtf && !sending_info && !sending_range)}});
  decoded_bank=decoded_bank | (packet[1279-:64] & {64{bank_select[12] && (!sending_nav && !sending_mtf && !sending_info && !sending_range)}});
  decoded_bank=decoded_bank | (packet[1215-:64] & {64{bank_select[13] && (!sending_nav && !sending_mtf && !sending_info && !sending_range)}});
  decoded_bank=decoded_bank | (packet[1151-:64] & {64{bank_select[14] && (!sending_nav && !sending_mtf && !sending_info && !sending_range)}});
  decoded_bank=decoded_bank | (packet[1087-:64] & {64{bank_select[15] && (!sending_nav && !sending_mtf && !sending_info && !sending_range)}});
  decoded_bank=decoded_bank | (packet[1023-:64] & {64{bank_select[16] && (!sending_nav && !sending_mtf && !sending_info && !sending_range)}});
  decoded_bank=decoded_bank | (packet[959-:64] & {64{bank_select[17] && (!sending_nav && !sending_mtf && !sending_info && !sending_range)}});
  decoded_bank=decoded_bank | (packet[895-:64] & {64{bank_select[18] && (!sending_nav && !sending_mtf && !sending_info && !sending_range)}});
  decoded_bank=decoded_bank | (packet[831-:64] & {64{bank_select[19] && (!sending_nav && !sending_mtf && !sending_info && !sending_range)}});
  decoded_bank=decoded_bank | (packet[767-:64] & {64{bank_select[20] && (!sending_nav && !sending_mtf && !sending_info && !sending_range)}});
  decoded_bank=decoded_bank | (packet[703-:64] & {64{bank_select[21] && (!sending_nav && !sending_mtf && !sending_info && !sending_range)}});
  decoded_bank=decoded_bank | (packet[639-:64] & {64{bank_select[22] && (!sending_nav && !sending_mtf && !sending_info && !sending_range)}});
  decoded_bank=decoded_bank | (packet[575-:64] & {64{bank_select[23] && (!sending_nav && !sending_mtf && !sending_info && !sending_range)}});
  decoded_bank=decoded_bank | (packet[511-:64] & {64{bank_select[24] && (!sending_nav && !sending_mtf && !sending_info && !sending_range)}});
  decoded_bank=decoded_bank | (packet[447-:64] & {64{bank_select[25] && (!sending_nav && !sending_mtf && !sending_info && !sending_range)}});
  decoded_bank=decoded_bank | (packet[383-:64] & {64{bank_select[26] && (!sending_nav && !sending_mtf && !sending_info && !sending_range)}});
  decoded_bank=decoded_bank | (packet[319-:64] & {64{bank_select[27] && (!sending_nav && !sending_mtf && !sending_info && !sending_range)}});
  decoded_bank=decoded_bank | (packet[255-:64] & {64{bank_select[28] && (!sending_nav && !sending_mtf && !sending_info && !sending_range)}});
  decoded_bank=decoded_bank | (packet[191-:64] & {64{bank_select[29] && (!sending_nav && !sending_mtf && !sending_info && !sending_range)}});
  decoded_bank=decoded_bank | (packet[127-:64] & {64{bank_select[30] && (!sending_nav && !sending_mtf && !sending_info && !sending_range)}});
  decoded_bank=decoded_bank | (packet[63-:64] & {64{bank_select[31] && (!sending_nav && !sending_mtf && !sending_info && !sending_range)}});
  end
 end
 wire [7:0] selected_byte=byte_bank[63-index[2:0]*8 -:8];
 uart_tx_115200 uart(.clk(clk),.start(start),.data(data),.tx(tx),.busy(busy));
 always @(posedge clk) begin
  start<=0;
  if(ticks<PERIOD) ticks<=ticks+1'b1;
  case(state)
   0:if(ticks>=PERIOD) begin


    sending_rotation<=0;sending_range<=0;sending_info<=0;sending_mtf<=0;sending_nav<=0;
    sample_sequence<=sample_sequence+1'b1;
    index<=0;checksum<=0;ticks<=0;state<=5;
   end
   5:state<=1; // Preserve the previously qualified first-byte delay.
   // A registered eight-byte bank breaks the 256-to-1 byte mux into two
   // stages. The complete packet stays unchanged until the next snapshot.
   1:begin
    byte_bank<=decoded_bank;
    state<=2;
   end
   2:if(!busy) begin
    data<=sending_rotation ? (index==46 ? crc[15:8]:index==47 ? crc[7:0]:selected_byte) : sending_nav ? (index==94 ? crc[15:8]:index==95 ? crc[7:0]:selected_byte) : sending_mtf ? (index==126 ? crc[15:8]:index==127 ? crc[7:0]:selected_byte) : sending_info ? (index==38 ? crc[15:8]:index==39 ? crc[7:0]:selected_byte) : (sending_range ? index==47 : (index==223 || index==255)) ? checksum:selected_byte;
    start<=1;state<=3;
    if(sending_rotation) begin
     if(index>=2 && index<46)crc<=crc_byte(crc,selected_byte);
    end else if(sending_nav) begin
     if(index>=2 && index<94)crc<=crc_byte(crc,selected_byte);
    end else if(sending_mtf) begin
     if(index>=2 && index<126)crc<=crc_byte(crc,selected_byte);
    end else if(sending_info) begin
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
    if(sending_rotation && index==47)begin sending_rotation<=0;state<=0;end
    else if(sending_nav && index==95)begin
     if(ROTATION_INFO)begin sending_nav<=0;sending_rotation<=1;index<=0;crc<=16'hffff;state<=1;end
     else state<=0;
    end
    else if(sending_mtf && index==127)begin
     if(NAV_INFO)begin sending_mtf<=0;sending_nav<=1;index<=0;crc<=16'hffff;state<=1;end
     else state<=0;
    end
    else if(sending_info && index==39)begin
     if(MTF_INFO)begin sending_info<=0;sending_mtf<=1;index<=0;crc<=16'hffff;state<=1;end
     else if(NAV_INFO)begin sending_info<=0;sending_nav<=1;index<=0;crc<=16'hffff;state<=1;end
     else state<=0;
    end
    else if(sending_range && index==47) begin
     if(FLIGHT_INFO) begin sending_info<=1;index<=0;crc<=16'hffff;state<=1;end
     else if(MTF_INFO)begin sending_range<=0;sending_mtf<=1;index<=0;crc<=16'hffff;state<=1;end
     else if(NAV_INFO)begin sending_range<=0;sending_nav<=1;index<=0;crc<=16'hffff;state<=1;end
     else state<=0;
    end
    else if(!sending_range && !sending_info && !sending_mtf && index==255) begin
     if(RANGE_DIAGNOSTICS) begin sending_range<=1;index<=0;checksum<=0;state<=1;end
     else if(FLIGHT_INFO) begin sending_info<=1;index<=0;crc<=16'hffff;state<=1;end
     else if(MTF_INFO)begin sending_mtf<=1;index<=0;crc<=16'hffff;state<=1;end
     else if(NAV_INFO)begin sending_nav<=1;index<=0;crc<=16'hffff;state<=1;end
     else state<=0;
    end else begin index<=index+1'b1;state<=1;end
   end
  endcase
 end
endmodule
