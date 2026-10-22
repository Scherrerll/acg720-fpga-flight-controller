`timescale 1ns/1ps
// Shared only by the added navigation domain. The original flight_core owns
// its independent arithmetic and is deliberately not a client of this service.
// Each client already holds its operands while awaiting its operation result.
// One pending BIT per client replaces duplicated helper engines, not a FIFO
// of wide requests. Requests while busy are ignored like the original helpers.
module nav_math_service #(
 parameter integer DIVIDE=0, CLIENTS=4
)(
 input wire clk,rst_n,
 input wire [CLIENTS-1:0] request,cancel,
 input wire [CLIENTS*64-1:0] operand_a,operand_b,
 output wire [CLIENTS-1:0] busy,done,error,
 output reg signed [63:0] result=0,
 output reg [CLIENTS-1:0] grant=0
);
 localparam OWNER_BITS=CLIENTS<=1 ? 1:$clog2(CLIENTS);
 localparam IDLE=0,START=1,WAIT=2;
 reg [1:0] state=IDLE;
 reg [OWNER_BITS-1:0] owner=0,round_robin=0,response_owner=0;
 reg [CLIENTS-1:0] pending=0,done_q=0,error_q=0;
 reg [CLIENTS-1:0] previous_cancel={CLIENTS{1'b1}};
 reg [7:0] generation[0:CLIENTS-1];
 reg [7:0] owner_epoch=0,response_epoch=0;
 reg signed [63:0] held_a=0,held_b=0;
 reg helper_start=0;
 wire helper_busy,helper_done,helper_error;
 wire signed [63:0] helper_result;
 wire owner_cancel=(state!=IDLE) && (cancel[owner] || owner_epoch!=generation[owner]);
 generate if(DIVIDE)begin: division_engine
  position_divide engine(.clk(clk),.rst_n(rst_n),.start(helper_start),.cancel(owner_cancel),
   .numerator(held_a),.denominator(held_b[31:0]),.busy(helper_busy),.done(helper_done),
   .error(helper_error),.quotient(helper_result));
 end else begin: multiplication_engine
  position_multiply engine(.clk(clk),.rst_n(rst_n),.start(helper_start),.cancel(owner_cancel),
   .a(held_a),.b(held_b),.busy(helper_busy),.done(helper_done),.result(helper_result));
  assign helper_error=1'b0;
 end endgenerate
 genvar c;
 generate for(c=0;c<CLIENTS;c=c+1)begin: client_status
  assign busy[c]=pending[c] || (state!=IDLE && owner==c);
  // Live cancel masks even the clock immediately before a client would
  // consume the response. Epoch tags also reject any response from old work.
  assign done[c]=done_q[c] && !cancel[c] && response_owner==c && response_epoch==generation[c];
  assign error[c]=done[c] && error_q[c];
 end endgenerate
 reg found;
 reg [OWNER_BITS-1:0] choice;
 integer offset,idx;
 always @*begin
  found=0;choice=0;
  for(offset=0;offset<CLIENTS;offset=offset+1)begin
   idx=round_robin+offset;
   if(idx>=CLIENTS)idx=idx-CLIENTS;
   if(!found && pending[idx] && !cancel[idx])begin found=1;choice=idx;end
  end
 end
 integer i;
 initial begin
  for(i=0;i<CLIENTS;i=i+1)generation[i]=0;
  if(CLIENTS<1 || CLIENTS>4 || DIVIDE<0 || DIVIDE>1)$error("Unsupported navigation service configuration");
 end
 always @(posedge clk)begin
  helper_start<=0;done_q<=0;error_q<=0;grant<=0;
  if(!rst_n)begin
   state<=IDLE;owner<=0;round_robin<=0;pending<=0;
   held_a<=0;held_b<=0;result<=0;owner_epoch<=0;response_epoch<=0;response_owner<=0;
   previous_cancel<={CLIENTS{1'b1}};
   for(i=0;i<CLIENTS;i=i+1)generation[i]<=0;
  end else begin
   previous_cancel<=cancel;
   for(i=0;i<CLIENTS;i=i+1)begin
    if(cancel[i])begin
     pending[i]<=0;
     if(!previous_cancel[i])generation[i]<=generation[i]+1'b1;
    end else if(request[i] && !busy[i])pending[i]<=1;
   end
   if(owner_cancel)begin
    // Only this owner drives helper cancellation. A canceled queued client
    // cannot abort another client's accepted multiplication or division.
    state<=IDLE;
   end else case(state)
    IDLE:if(found)begin
     owner<=choice;owner_epoch<=generation[choice];
     held_a<=$signed(operand_a[choice*64 +:64]);
     held_b<=$signed(operand_b[choice*64 +:64]);
     pending[choice]<=0;grant[choice]<=1;
     round_robin<=choice==CLIENTS-1 ? 0:choice+1'b1;
     state<=START;
    end
    START:begin helper_start<=1;state<=WAIT;end
    WAIT:if(helper_done)begin
     response_owner<=owner;response_epoch<=owner_epoch;
     result<=helper_result;done_q[owner]<=1;error_q[owner]<=helper_error;
     state<=IDLE;
    end
    default:state<=IDLE;
   endcase
  end
 end
endmodule
