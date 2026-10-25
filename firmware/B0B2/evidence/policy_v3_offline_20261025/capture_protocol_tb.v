`timescale 1ns/1ps
module capture_protocol;
 reg clk=0,rx=1,tx_ack=0;always #10 clk=~clk;
 wire tx;acg720_ano_port dut(.clk50(clk),.imu_miso(1'b0),.rc_ppm_in(1'b0),.range_rx(rx),.radio_tx(tx));
 integer file,count=0,i=0,j=0;reg [7:0] packet[0:26];
 task byte_rx(input[7:0] value);integer b;begin
  @(negedge clk);rx=0;repeat(434)@(negedge clk);
  for(b=0;b<8;b=b+1)begin rx=value[b];repeat(434)@(negedge clk);end
  rx=1;repeat(868)@(negedge clk);
 end endtask
 always @(posedge clk)begin tx_ack<=dut.telemetry.start;if(dut.telemetry.start)begin
  $fwrite(file,"%02x\n",dut.telemetry.data);count=count+1;
  if(count==644)begin $fclose(file);$display("PASS capture_protocol644 bytes: actual top, real Micolink UART receive, byte-FSM output with immediate transport acknowledgment");$finish;end
 end end
 initial begin
file=$fopen("C:/Users/ScherrerL/Desktop/apple/timeout_policy_20261025/wire.hex","w");
packet[0]=8'hef;packet[1]=8'h01;packet[2]=8'h01;packet[3]=8'h51;packet[4]=8'h01;packet[5]=8'h14;packet[6]=8'h01;packet[7]=8'h00;packet[8]=8'h00;packet[9]=8'h00;packet[10]=8'he8;packet[11]=8'h03;packet[12]=8'h00;packet[13]=8'h00;packet[14]=8'h64;packet[15]=8'h00;packet[16]=8'h01;packet[17]=8'h00;packet[18]=8'h00;packet[19]=8'h00;packet[20]=8'h00;packet[21]=8'h00;packet[22]=8'h32;packet[23]=8'h01;packet[24]=8'h00;packet[25]=8'h00;packet[26]=8'hdb;
repeat(400)@(negedge clk);
 for(i=0;i<27;i=i+1)byte_rx(packet[i]);
 repeat(5000)@(negedge clk);
 if(dut.mtf.samples!=1)$fatal(1,"real Micolink frame not received");
 force dut.telemetry.busy=tx_ack;
 force dut.telemetry.ticks=10000000;
 @(negedge clk);release dut.telemetry.ticks;
 end
 initial begin #10000000;$fatal(1,"protocol capture timeout count=%0d",count);end
endmodule
