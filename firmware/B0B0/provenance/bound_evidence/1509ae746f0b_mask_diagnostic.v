
`timescale 1ns/1ps
module tb;
reg clk=0;always #10 clk=~clk;
reg rst_n=0,hold=0;reg[719:0]raw_data=0,reference_q=0;
wire[719:0]actual;
mtf_xyz_navigation_control dut(.clk(clk),.rst_n(rst_n),.origin_reset(1'b0),.diagnostic_hold(hold),
 .sample_valid(1'b0),.range_valid(1'b0),.flow_valid(1'b0),.distance_mm(32'd100),.dt_ms(32'd20),.source_age_ms(32'd0),
 .vx_x100(32'sd0),.vy_x100(32'sd0),.pose_valid(1'b0),.pose_age_ticks(32'hffffffff),
 .roll_cdeg(16'sd0),.pitch_cdeg(16'sd0),.yaw_cdeg(16'sd0),.yaw_range_ok(1'b1),
 .acc_valid(1'b0),.acc_update(1'b0),.acc_dt_us(32'd1000),.ax_mmps2(32'sd0),.ay_mmps2(32'sd0),.az_up_mmps2(32'sd0),
 .rc_valid(1'b0),.enabled(1'b0),.taking_off(1'b0),.channel_count(4'd8),
 .ch1(16'd1500),.ch2(16'd1500),.ch3(16'd1000),.ch4(16'd1500),.ch7(16'd1000),.collective_us(16'd1000),.uptime_ms(64'd0),.diagnostic_body(actual));
function[719:0]mask_before;input[719:0]v;begin
 mask_before=v;mask_before[143:128]=v[85]?v[143:128]:16'd0;mask_before[127:112]=v[85]?v[127:112]:16'd0;
end endfunction
always @(posedge clk)if(!rst_n)reference_q<=dut.RESET_DIAGNOSTIC;else if(!hold)reference_q<=mask_before(raw_data);
integer i,j;
initial begin
 force dut.diagnostic_next=raw_data;
 repeat(2)@(negedge clk);rst_n=1;
 for(i=0;i<60000;i=i+1)begin
  for(j=0;j<22;j=j+1)raw_data[j*32+:32]=$random;raw_data[719:704]=$random;
  hold=(i%29>17);rst_n=i%7001>2;
  @(negedge clk);#1;if(actual!==reference_q)$fatal(1,"diagnostic720bit mismatch at%0d",i);
 end
 $display("DIAGNOSTIC_MASK_COMMUTATION_PASS60000cycles all720bits, resets and holds");$finish;
end
endmodule
