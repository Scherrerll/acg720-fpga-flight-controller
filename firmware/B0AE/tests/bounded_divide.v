
module tb;
mtf_xyz_hold_control dut();
integer h,whole,j,frac;reg signed[28:0]raw;reg signed[63:0]wide,expected;
initial begin
 for(h=0;h<=5000;h=h+1)begin
  if(dut.feedback_height_q16(h)!=(h/10)*655360)$fatal(1,"height cm narrowing");
  expected=h>=600 ?0:((600-h)*2/10)*10;if(expected>800)expected=800;
  if(dut.auto_takeoff_mmps(h)!=expected)$fatal(1,"auto speed narrowing");
 end
 for(whole=-2500;whole<=3500;whole=whole+1)for(j=0;j<4;j=j+1)begin
  case(j)0:frac=0;1:frac=1;2:frac=32768;3:frac=65535;endcase
  raw=whole*65536+frac;wide=raw;expected=dut.integer_q16(wide)/10*64'sd655360;
  if(dut.quantized_climb_q16(raw)!=expected)$fatal(1,"signed climb cm narrowing %d",raw);
 end
 $display("BOUNDED_DIVIDE_PASS all5001heights,24004signed/fraction-boundary speeds");$finish;
end
endmodule
