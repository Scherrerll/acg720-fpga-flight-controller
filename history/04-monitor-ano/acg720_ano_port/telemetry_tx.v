// Independent resource trial. Do not install without complete top-level PNR.
// A579224 bytes preserved; independent A57A32 follows the same snapshot/sequence.
// Each XOR excludes its two header bytes: A579[2:222], A57A[2:30].
module telemetry_tx #(parameter integer PERIOD=5000000,parameter integer RANGE_DIAGNOSTICS=0)(
 input wire clk,input wire [863:0] core_body,input wire [887:0] extension,
 input wire [215:0] acceleration_body,
 input wire [343:0] range_diagnostic_body,
 output wire tx
);
 reg [31:0] ticks=0;reg [15:0] sample_sequence=0;
 reg [2047:0] packet=0;
 reg [383:0] range_packet=0;reg sending_range=0;
 reg [63:0] byte_bank=0;
 reg [7:0] index=0,checksum=0,data=0;
 reg [2:0] state=0;reg start=0;wire busy;
 wire [7:0] selected_byte=byte_bank[63-index[2:0]*8 -:8];
 uart_tx_115200 uart(.clk(clk),.start(start),.data(data),.tx(tx),.busy(busy));
 always @(posedge clk) begin
  start<=0;
  if(ticks<PERIOD) ticks<=ticks+1'b1;
  case(state)
   0:if(ticks>=PERIOD) begin
    packet<={16'ha579,sample_sequence,core_body,extension,8'd0,
             16'ha57a,sample_sequence,acceleration_body,8'd0};
    if(RANGE_DIAGNOSTICS) range_packet<={16'ha57b,sample_sequence,range_diagnostic_body,8'd0};
    sending_range<=0;
    sample_sequence<=sample_sequence+1'b1;
    index<=0;checksum<=0;ticks<=0;state<=1;
   end
   // A registered eight-byte bank breaks the 256-to-1 byte mux into two
   // stages. The complete packet stays unchanged until the next snapshot.
   1:begin
    byte_bank<=sending_range ? range_packet[383-index[5:3]*64 -:64] : packet[2047-index[7:3]*64 -:64];
    state<=2;
   end
   2:if(!busy) begin
    data<=(sending_range ? index==47 : (index==223 || index==255)) ? checksum:selected_byte;
    start<=1;state<=3;
    if(sending_range) begin
     if(index>=2 && index<47) checksum<=checksum^selected_byte;
    end else begin
     if(index==224) checksum<=0;
     else if((index>=2 && index<223) || (index>=226 && index<255)) checksum<=checksum^selected_byte;
    end
   end
   3:if(busy) state<=4;
   4:if(!busy) begin
    if(sending_range && index==47) state<=0;
    else if(!sending_range && index==255) begin
     if(RANGE_DIAGNOSTICS) begin sending_range<=1;index<=0;checksum<=0;state<=1;end
     else state<=0;
    end else begin index<=index+1'b1;state<=1;end
   end
  endcase
 end
endmodule
