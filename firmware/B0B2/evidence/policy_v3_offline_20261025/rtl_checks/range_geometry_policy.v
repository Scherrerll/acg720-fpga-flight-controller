`timescale 1ns/1ps
module range_geometry_policy;
 reg clk=0,rst_n=0,pose_valid=1;always #10 clk=~clk;
 reg[31:0] range_age=0;wire current_ready,old_ready,current_update;
 range_height_estimate #(.CAL_MASK(8'h18)) actual(.clk(clk),.rst_n(rst_n),.pose_update(1'b0),.pose_valid(pose_valid),
  .roll(16'sd0),.pitch(16'sd0),.range_link(1'b1),.distance_cm(16'd100),.range_age(range_age),.estimate_ready(current_ready),.update(current_update));
 range_height_estimate_before #(.CAL_MASK(8'h18)) original(.clk(clk),.rst_n(rst_n),.pose_update(1'b0),.pose_valid(pose_valid),
  .roll(16'sd0),.pitch(16'sd0),.range_link(1'b1),.distance_cm(16'd100),.range_age(range_age),.estimate_ready(old_ready));
 task tick;begin @(posedge clk);#2;end endtask
 initial begin
  repeat(3)tick();@(negedge clk);rst_n=1;
  force actual.seen=1;force original.seen=1;original.publication_age=2999998;
  if(!current_ready || !old_ready)begin #1;if(!current_ready || !old_ready)$fatal(1,"initial valid projection absent");end
  repeat(4)tick();
  if(!current_ready || old_ready || current_update)$fatal(1,"pose publication expiry retained or fake update emitted");
  @(negedge clk);range_age=4999999;tick();if(!current_ready)$fatal(1,"range freshness early");
  @(negedge clk);range_age=5000000;tick();if(current_ready)$fatal(1,"100ms range freshness removed");
  @(negedge clk);range_age=0;pose_valid=0;tick();if(current_ready)$fatal(1,"explicit pose invalidity removed");
  $display("PASS range_geometry_policy: removed derived pose-publication60ms watchdog; no fake update; source range4999999/5000000 ticks and explicit validity preserved");$finish;
 end
 initial begin #100000;$fatal(1,"range geometry policy timeout");end
endmodule
