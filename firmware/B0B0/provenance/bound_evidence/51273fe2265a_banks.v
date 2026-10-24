module reference(input clk,rst_n,diagnostic_hold,input [719:0] diagnostic_next,output [719:0] diagnostic_body);
 localparam [719:0] RESET_DIAGNOSTIC={8'd5,8'h80,8'd1,8'd0,64'd0,
  32'd0,32'hffffffff,32'd0,32'h001d0080,{11{32'd0}},
  16'sd0,16'sd0,16'sd0,16'h0040,8'd0,8'd0,16'd0,16'd1,32'sd0};
 reg [719:0] diagnostic_q=RESET_DIAGNOSTIC;
 always @(posedge clk)begin
  if(!rst_n)diagnostic_q<=RESET_DIAGNOSTIC;else if(!diagnostic_hold)diagnostic_q<=diagnostic_next;
 end
 // XY-active is shadow_flags[5], diagnostic_q[85]. Capture raw targets
 // and their flag together, then mask after the SAME snapshot register.
 // Every external diagnostic bit equals the old mask-before-register form.
 assign diagnostic_body={diagnostic_q[719:144],
  diagnostic_q[85] ?diagnostic_q[143:128]:16'd0,
  diagnostic_q[85] ?diagnostic_q[127:112]:16'd0,diagnostic_q[111:0]};
endmodule
module proposal#(parameter STARTUP_ONLY_DIAGNOSTIC_RESET=0)(input clk,rst_n,diagnostic_hold,input [719:0] diagnostic_next,output [719:0] diagnostic_body);
 localparam [719:0] RESET_DIAGNOSTIC={8'd5,8'h80,8'd1,8'd0,64'd0,
  32'd0,32'hffffffff,32'd0,32'h001d0080,{11{32'd0}},
  16'sd0,16'sd0,16'sd0,16'h0040,8'd0,8'd0,16'd0,16'd1,32'sd0};
 reg [719:0] diagnostic_q=RESET_DIAGNOSTIC;
 always @(posedge clk)begin
  if(STARTUP_ONLY_DIAGNOSTIC_RESET)begin
   // Caller must guarantee reset starts low and never reasserts.
   // Preserve initialized payload until reset releases; never delay captures.
   if(rst_n && !diagnostic_hold)diagnostic_q<=diagnostic_next;
  end else begin
   if(!rst_n)diagnostic_q<=RESET_DIAGNOSTIC;else if(!diagnostic_hold)diagnostic_q<=diagnostic_next;
  end
 end
 // XY-active is shadow_flags[5], diagnostic_q[85]. Capture raw targets
 // and their flag together, then mask after the SAME snapshot register.
 // Every external diagnostic bit equals the old mask-before-register form.
 assign diagnostic_body={diagnostic_q[719:144],
  diagnostic_q[85] ?diagnostic_q[143:128]:16'd0,
  diagnostic_q[85] ?diagnostic_q[127:112]:16'd0,diagnostic_q[111:0]};
endmodule
