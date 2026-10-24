`timescale 1ns/1ps
module tb;
reg clk=0;always #10 clk=~clk;
wire tx,hold;integer file_id,count=0;
wire[271:0]info={8'd2,8'd1,32'h0000b0ad,64'd123400,16'd3,64'd123000,
 8'h32,8'h40,8'd0,8'd0,32'd42,8'd0,8'h04};
// Includes negative full Q12 gyro, exact 1deg/s, source age and pickup value.
wire[335:0]pair={8'd1,8'h0f,16'd321,32'd123399,32'd223,16'd10,32'd50000,
 -32'sd22300,32'sd4460,32'sd67174,-32'sd134349,32'sd0,16'd0,16'd1850};
telemetry_tx #(.PERIOD(64),.ROTATION_INFO(1),.FLIGHT_INFO(1),.MTF_INFO(1),
 .NAV_INFO(1),.EXTERNAL_SNAPSHOT(1),.MTF_CALLER_SNAPSHOT(1),.NAV_CALLER_SNAPSHOT(1)) dut(
 .clk(clk),.core_body(864'd0),.extension(888'd0),.acceleration_body(216'd0),
 .range_diagnostic_body(344'd0),.flight_info_body(info),.rotation_body(pair),
 .mtf_body(976'd0),.nav_body(720'd0),.tx(tx),.snapshot_hold(hold));
initial file_id=$fopen("telemetry_wire.hex","w");
// Sample the byte on exactly the same clock the REAL UART accepts it.
always @(posedge clk)if(dut.start && !dut.busy)begin
 $fwrite(file_id,"%02x\n",dut.data);count=count+1;
 if(count==1136)begin $fclose(file_id);
  $display("TELEMETRY_WIRE_PASS two complete 568 byte frames");$finish;end
end
initial begin #200000000;$fatal(1,"wire timeout count=%0d",count);end
endmodule
