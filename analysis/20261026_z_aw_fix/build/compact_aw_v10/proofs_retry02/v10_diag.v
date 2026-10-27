`default_nettype none
module diag_v10 #(parameter STARTUP_ONLY_DIAGNOSTIC_RESET=0)(input clk,rst_n,diagnostic_hold,
input [671:0] payload,input [15:0] shadow_flags,input [7:0] live,
output wire [719:0] diagnostic_body);
wire [63:0] uptime_ms=payload[63:0];
wire [31:0] navigation_sequence=payload[95:64],source_age_ms=payload[127:96],geometry_dt_us=payload[159:128],reasons=payload[191:160];
wire [31:0] height_mm=payload[223:192],bvx=payload[255:224],bvy=payload[287:256],wvx=payload[319:288],wvy=payload[351:320];
wire [30:0] fused_vx_q16=payload[382:352],fused_vy_q16=payload[413:383];
wire [31:0] fused_height=payload[445:414],fused_vz_q16=payload[477:446],position_x_q8=payload[509:478],position_y_q8=payload[541:510];
wire [15:0] controller_roll=payload[557:542],controller_pitch=payload[573:558],controller_delta=payload[589:574],controller_collective=payload[605:590];
wire [31:0] controller_target_height=payload[637:606];
wire [15:0] z_reason=payload[655:640];
wire signed [15:0] z_throttle_delta;wire [15:0] z_collective;
wire position_ready=live[0],live_velocity=live[1],height_ready=live[2],geometry_flow_ready=live[3],geometry_height_ready=live[4],module_fresh=live[5],mapping_verified=live[6],rotation_compensated=live[7];
wire z_active=shadow_flags[4];
 assign z_throttle_delta=z_active ?controller_delta:16'sd0;
 assign z_collective=z_active ?controller_collective:16'd0;
 wire signed [31:0] z_target_height=z_active ?controller_target_height:32'sd0;
 wire [719:0] diagnostic_next={8'd5,{1'b1,1'b0,position_ready,live_velocity,height_ready,
  geometry_flow_ready,geometry_height_ready,module_fresh},8'd1,8'd0,uptime_ms,
  navigation_sequence,source_age_ms,geometry_dt_us,reasons,height_mm,bvx,bvy,wvx,wvy,
  {fused_vx_q16[30],fused_vx_q16},{fused_vy_q16[30],fused_vy_q16},fused_height,fused_vz_q16,
  position_x_q8,position_y_q8,controller_roll,controller_pitch,controller_delta,shadow_flags,
  {7'd0,mapping_verified},{7'd0,rotation_compensated},controller_collective,z_reason,controller_target_height};
 // One complete90-byte caller-held snapshot. Hold affects telemetry only;
 // sources, math, raw masks and controller outputs continue independently.
 // Physical public masks above remain combinational; only telemetry adds1tick.
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
 // Z-active is shadow_flags[4], diagnostic_q[84]. The same snapshot flag
 // masks raw Z delta/collective/target after capture, exactly as XY below.
 // XY-active is shadow_flags[5], diagnostic_q[85]. Capture raw targets
 // and their flag together, then mask after the SAME snapshot register.
 // Every external diagnostic bit equals the old mask-before-register form.
 assign diagnostic_body={diagnostic_q[719:144],
  diagnostic_q[85] ?diagnostic_q[143:128]:16'd0,
  diagnostic_q[85] ?diagnostic_q[127:112]:16'd0,
  diagnostic_q[84] ?diagnostic_q[111:96]:16'd0,diagnostic_q[95:64],
  diagnostic_q[84] ?diagnostic_q[63:48]:16'd0,diagnostic_q[47:32],
  diagnostic_q[84] ?diagnostic_q[31:0]:32'd0};
endmodule
