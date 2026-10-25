`timescale 1ns/1ps
module tap_estimator_tb;
 reg clk=0;always #5 clk=~clk;
 reg rst_n=0,sample_valid=0,link_usable=1,reject_event=0;
 reg [95:0] raw={16'd0,16'd0,16'd2048,16'd1,16'd2,16'd3};
 reg [31:0] dt_ticks=10000,diag_accepted_id=0;
 integer publications=0;reg [31:0] expected_id=0,expected_dt=0;
 ano_attitude_estimator #(.CAL_SAMPLES(2)) dut(.clk(clk),.rst_n(rst_n),.sample_valid(sample_valid),
  .link_usable(link_usable),.reject_event(reject_event),.raw(raw),.dt_ticks(dt_ticks),.diag_accepted_id(diag_accepted_id));
 gold_ano_attitude_estimator #(.CAL_SAMPLES(2)) gold(.clk(clk),.rst_n(rst_n),.sample_valid(sample_valid),
  .link_usable(link_usable),.reject_event(reject_event),.raw(raw),.dt_ticks(dt_ticks));
 always @(negedge clk)if(rst_n)begin
  if({dut.calibrated,dut.attitude_valid,dut.update,dut.roll_cdeg,dut.pitch_cdeg,dut.yaw_cdeg,
      dut.yaw_range_ok,dut.tilt4500_ok,dut.bias_x,dut.bias_y,dut.bias_z,dut.cal_count,dut.fault,
      dut.accel_correction,dut.filtered_gx,dut.filtered_gy,dut.filtered_gz,
      dut.filtered_gx_q12,dut.filtered_gy_q12,dut.filtered_gz_q12,
      dut.world_ax_mmps2,dut.world_ay_mmps2,dut.world_az_mmps2,dut.linear_accel_valid}
    !=={gold.calibrated,gold.attitude_valid,gold.update,gold.roll_cdeg,gold.pitch_cdeg,gold.yaw_cdeg,
      gold.yaw_range_ok,gold.tilt4500_ok,gold.bias_x,gold.bias_y,gold.bias_z,gold.cal_count,gold.fault,
      gold.accel_correction,gold.filtered_gx,gold.filtered_gy,gold.filtered_gz,
      gold.filtered_gx_q12,gold.filtered_gy_q12,gold.filtered_gz_q12,
      gold.world_ax_mmps2,gold.world_ay_mmps2,gold.world_az_mmps2,gold.linear_accel_valid})
    $fatal(1,"original control outputs diverged");
  if(dut.update)begin
   publications=publications+1;
   if(dut.diag_consumed_accepted_id!==expected_id || dut.diag_held_dt!==expected_dt)
    $fatal(1,"consumed ID/held dt mismatch");
  end
 end
 task send;
  input [31:0] id;
  begin @(negedge clk);diag_accepted_id=id;dt_ticks=10000+id;expected_id=id;expected_dt=10000+id;
   sample_valid=1;@(negedge clk);sample_valid=0;end
 endtask
 task settle;begin repeat(10000)@(negedge clk);end endtask
 initial begin
  repeat(3)@(negedge clk);rst_n=1;
  send(1);settle();send(2);settle();send(3);settle();send(4);settle();send(5);settle();
  if(!dut.attitude_valid || publications!=1)$fatal(1,"initial pose did not publish");
  send(6);repeat(3)@(negedge clk);reject_event=1;@(negedge clk);reject_event=0;settle();
  if(!dut.attitude_valid || publications!=2 || dut.diag_first_cause!=0)$fatal(1,"stable rejection changed epoch");
  send(7);repeat(3)@(negedge clk);send(8);repeat(4)@(negedge clk);
  if(dut.fault!=8 || dut.diag_first_cause!=3 || dut.diag_consumed_accepted_id!=7)
   $fatal(1,"busy collision cause/consumption incorrect");
  raw={16'd0,16'd0,16'd3000,16'd1,16'd2,16'd3};send(9);settle();
  if(dut.fault!=4 || dut.diag_first_cause!=3)$fatal(1,"latest fault erased first cause");
  raw={16'd0,16'd0,16'd2048,16'd1,16'd2,16'd3};
  send(10);settle();send(11);settle();send(12);settle();
  if(!dut.attitude_valid || dut.diag_first_cause!=0 || publications!=3)$fatal(1,"recovery publication/cause clear");
  $display("PASS estimator: cycle-identical B0B0 outputs; exact consumed ID/dt; stable reject, collision, gravity recovery, first-cause lifetime");$finish;
 end
 initial begin #2000000;$fatal(1,"timeout");end
endmodule
