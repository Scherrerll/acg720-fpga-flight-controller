from test_tools import *
sources=[FIX/n for n in ['position/mtf_xyz_hold_control.v','position/ano_z_stick.v','position/ano_xy_stick.v','position/ano_xy_divide36.v','position/position_math.v','nav_math_service.v']]
bench=r'''
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
'''
(ROOT/'tests/bounded_divide.v').write_text(bench)
simulate('bounded_divide',sources,ROOT/'tests/bounded_divide.v')
header=(ROOT/'tests/height_reference.v').read_text().split('integer f,g,rv,')[0]
header=header.replace('always #5 clk=~clk;','always #10 clk=~clk;')
bench=header+r'''
integer phase=0,msidx=0;reg signed[26:0]saved_x,saved_y;reg signed[32:0]saved_ax,saved_ay;
always @(negedge clk)begin
 sample=0;hu=0;pu=0;
 if(rst_n)begin
  if(phase==1999)begin
   phase=0;msidx=msidx+1;sample=1;hu=(msidx%11==0);pu=(msidx%20==0);
  end else phase=phase+1;
 end
end
task ticks;input integer n;begin repeat(n)@(posedge clk);#1;end endtask
initial begin
 repeat(2)@(posedge clk);#1;rst_n=1;c3=2000;c1=1700;c2=1800;c7=2000;en=0;to=0;
 ticks(50000);if(active || za)$fatal(1,"selected mode cannot run while locked");
 en=1;to=1;wait(active && za);
 // A mode change is allowed while shared math is inside an uncommitted XY
 // callback. It must withdraw XY immediately, preserve Z, and roll back PI.
 wait(dut.work_xy && dut.state==7);#1;
 saved_x=dut.saved_ix;saved_y=dut.saved_iy;saved_ax=dut.saved_afx;saved_ay=dut.saved_afy;
 if(dut.ix_store==saved_x)$fatal(1,"race did not reach partial PI update");
 c7=1000;#1;if(active || !za)$fatal(1,"immediate XY revoke/Z continuity");
 ticks(20);
 if(dut.ix_store!=saved_x || dut.iy_store!=saved_y || dut.afx_store!=saved_ax || dut.afy_store!=saved_ay)$fatal(1,"partial callback not rolled back atomically");
 c7=2000;wait(active && za); // Full throttle, no center/reselect handshake.
 en=0;to=0;#1;if(active || za)$fatal(1,"lock revoke");
 ticks(20);en=1;to=1;wait(active && za);
 $display("CONTROL_RACE_PASS preselected/full-stick entry, immediate cancel, atomic PI rollback, vertical continuity, recovery");$finish;
end
initial begin #100000000;$fatal(1,"race timeout");end
endmodule
'''
(ROOT/'tests/control_races.v').write_text(bench)
simulate('control_races',sources,ROOT/'tests/control_races.v')
