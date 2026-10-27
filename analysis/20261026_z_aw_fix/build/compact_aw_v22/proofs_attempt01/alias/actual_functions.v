module old_actual(input signed [28:0] speed_z_tick_store,input signed [31:0] next_auto_speed,input taking_off,output signed [31:0] q,alt);
 function signed [31:0] quantized_climb_q16;
 input signed [28:0] v;
 reg signed [13:0] whole_mm;
 reg signed [9:0] cm;
 begin
  whole_mm=$signed(v[28:16])+(v[28] && |v[15:0] ?14'sd1:14'sd0);
  cm=whole_mm/14'sd10;quantized_climb_q16=cm*32'sd655360;
 end endfunction

assign q=quantized_climb_q16(speed_z_tick_store);
assign alt=taking_off ?quantized_climb_q16(speed_z_tick_store)+next_auto_speed*32'sd65536:0;
endmodule
module new_actual(input signed [28:0] speed_z_tick_store,input signed [31:0] next_auto_speed,input taking_off,output signed [31:0] q,alt);
 function signed [31:0] quantized_climb_q16;
 input signed [28:0] v;
 reg signed [13:0] whole_mm;
 reg signed [9:0] cm;
 begin
  whole_mm=$signed(v[28:16])+(v[28] && |v[15:0] ?14'sd1:14'sd0);
  cm=whole_mm/14'sd10;quantized_climb_q16=cm*32'sd655360;
 end endfunction
 wire signed [31:0] quantized_climb_logic_q16 /* synthesis syn_dspstyle="logic" */;
 assign quantized_climb_logic_q16=quantized_climb_q16(speed_z_tick_store);
assign q=quantized_climb_q16(speed_z_tick_store);
assign alt=taking_off ?quantized_climb_logic_q16+next_auto_speed*32'sd65536:0;
endmodule
