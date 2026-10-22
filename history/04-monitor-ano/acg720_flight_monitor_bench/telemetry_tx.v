// A578: 224 bytes, big endian, XOR over bytes2..222. Atomic snapshot.
module telemetry_tx #(parameter integer PERIOD=5000000)(
 input wire clk,input wire [863:0] core_body,input wire [887:0] extension,
 output wire tx
);
 reg [31:0] ticks=0;reg [15:0] sample_sequence=0;
 reg [1791:0] packet=0;reg [7:0] index=0,checksum=0,data=0;
 reg [1:0] state=0;reg start=0;wire busy;
 uart_tx_115200 uart(.clk(clk),.start(start),.data(data),.tx(tx),.busy(busy));
 always @(posedge clk) begin
  start<=0;
  if(ticks<PERIOD) ticks<=ticks+1'b1;
  case(state)
   0:if(ticks>=PERIOD) begin
    packet<={16'ha578,sample_sequence,core_body,extension,8'd0};
    sample_sequence<=sample_sequence+1'b1;index<=0;checksum<=0;ticks<=0;state<=1;
   end
   1:if(!busy) begin
    data<=index==223 ? checksum:packet[1791:1784];start<=1;state<=2;
    if(index>=2 && index<223) checksum<=checksum^packet[1791:1784];
   end
   2:if(busy) state<=3;
   3:if(!busy) begin
    if(index==223) state<=0;
    else begin index<=index+1'b1;packet<=packet<<8;state<=1;end
   end
  endcase
 end
endmodule
