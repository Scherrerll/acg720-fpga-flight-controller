`timescale 1ns/1ps
module tap_temporal_tb;
 reg clk=0;always #5 clk=~clk;
 reg rst_n=0,record_ready=0,base_ok=1,calibrated=1;
 reg [95:0] raw={16'd0,16'd0,16'd2048,16'd1,16'd2,16'd3};
 reg signed [15:0] bias_x=1,bias_y=2,bias_z=3;
 reg [31:0] diag_source_id_in=0,diag_tick_in=0;
 reg [9:0] diag_reader_meta_in=10'h003;
 wire checked_ready,checked_base_ok,candidate_pending;
 wire [95:0] checked_raw,diag_trusted_out,diag_candidate_out;
 wire [7:0] reject_detail,quiet_count;wire [31:0] diag_source_id_out,diag_tick_out;
 wire [9:0] diag_reader_meta_out;
 imu_temporal_check #(.TIMEOUT_TICKS(10000),.QUIET_SAMPLES(1)) dut(.*);
 task send;
  input [31:0] id;input [95:0] value;
  begin
   @(negedge clk);record_ready=1;raw=value;diag_source_id_in=id;diag_tick_in=100+id;
   diag_reader_meta_in={id[7:0],2'b11};
   @(negedge clk);record_ready=0;raw=96'hffffffffffffffffffffffff;
   diag_source_id_in=99;diag_tick_in=999;diag_reader_meta_in=0;
   wait(checked_ready);#1;
   if(checked_raw!==value || diag_source_id_out!==id || diag_tick_out!==100+id ||
      diag_reader_meta_out!=={id[7:0],2'b11})$fatal(1,"temporal input metadata incoherent");
   @(negedge clk);
  end
 endtask
 initial begin
  repeat(3)@(negedge clk);rst_n=1;
  send(1,{16'd0,16'd0,16'd2048,16'd1,16'd2,16'd3});
  send(2,{16'd0,16'd0,16'd2048,16'd1,16'd2,16'd3});
  send(3,{16'd600,16'd0,16'd2048,16'd1,16'd2,16'd3});
  if(reject_detail!=2 || diag_trusted_out!=={16'd0,16'd0,16'd2048,16'd1,16'd2,16'd3} || diag_candidate_out!==0)
   $fatal(1,"first rejection tuple incorrect");
  send(4,{-16'sd600,16'd0,16'd2048,16'd1,16'd2,16'd3});
  if(reject_detail!=2 || diag_candidate_out!=={16'd600,16'd0,16'd2048,16'd1,16'd2,16'd3})
   $fatal(1,"second rejection did not retain prior candidate");
  $display("PASS temporal: source/tick/reader metadata and predecision trusted/candidate belong to exact input");$finish;
 end
 initial begin #100000;$fatal(1,"timeout");end
endmodule
