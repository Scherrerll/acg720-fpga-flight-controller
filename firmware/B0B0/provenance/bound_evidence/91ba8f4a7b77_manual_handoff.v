`timescale 1ns/1ps
module tb;
reg clk=0;always #10 clk=~clk;
reg rst_n=0,en=1,stab=0,override_on=0,sample=0,outer=0;
wire signed[15:0]r,p;wire update,busy;wire[7:0]fault;
ano_manual_angles dut(.clk(clk),.rst_n(rst_n),.sample_update(sample),.norm_valid(1'b1),.outer_update(outer),.enabled(en),.att_stab(stab),
 .norm_roll_q16(18'sd0),.norm_pitch_q16(18'sd0),.norm_dt_us(16'd20000),.outer_dt_ticks(32'd300000),.roll_cdeg(16'sd0),.pitch_cdeg(16'sd0),
 .loc_override(override_on),.loc_roll_cdeg(16'sd315),.loc_pitch_cdeg(-16'sd190),
 .manual_roll_cdeg(r),.manual_pitch_cdeg(p),.update(update),.busy(busy),.fault(fault));
task ticks;input integer n;begin repeat(n)@(negedge clk);end endtask
task outer_call;begin wait(!busy);@(negedge clk);outer=1;ticks(1);outer=0;wait(update);ticks(1);end endtask
initial begin
 ticks(3);rst_n=1;ticks(3);override_on=1;ticks(3);outer_call();
 if(r!=315 || p!=190 || fault)$fatal(1,"shared Loc OF cache");
 override_on=0;stab=1;outer_call();
 if(r<315 || r>316 || p<190 || p>191 || dut.tr<=0 || dut.tp<=0)$fatal(1,"Att2 must retain previous Loc result until next manual Loc task");
 sample=1;ticks(1);sample=0;wait(!busy);outer_call();
 if(r!=0 || p!=0 || dut.loc_r!=0 || dut.loc_p!=0 || fault)$fatal(1,"next20ms Loc callback must adopt manual command");
 en=0;#1;if(r!=0 || p!=0)$fatal(1,"disabled output");
 $display("MANUAL_HANDOFF_PASS one Loc cache, OF-to-manual task ordering, original trim, immediate disabled output");$finish;
end
initial begin #1000000;$fatal(1,"manual handoff timeout");end
endmodule
