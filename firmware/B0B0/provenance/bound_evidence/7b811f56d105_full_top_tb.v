module tb;
reg clk=0;always #10 clk=~clk;
wire txa,txb;
acg720_ano_port a(.clk50(clk),.imu_miso(1'b0),.rc_ppm_in(1'b0),.range_rx(1'b1),.uart_tx(txa));
top_proposed b(.clk50(clk),.imu_miso(1'b0),.rc_ppm_in(1'b0),.range_rx(1'b1),.uart_tx(txb));
// Only the frame PERIOD is accelerated. Actual UART RTL/433-clock baud is unchanged.
defparam a.telemetry.PERIOD=512;
defparam b.telemetry.PERIOD=512;
reg [719:0] live_payload=0;
reg origin_event=0;
reg [31:0] rng=32'h86c95afe;
integer cycle=0,bytes=0,j,held_changes=0,origin_events=0,frames=0,trace;
reg previous_hold=0;
initial begin
 trace=$fopen("full_top_acceptance.log","w");
 force a.native_navigation.diagnostic_next=live_payload;
 force b.native_navigation.diagnostic_next=live_payload;
 force a.observer_reset=origin_event;
 force b.observer_reset=origin_event;
end
always @(negedge clk)begin
 if(cycle%997==0)begin
  for(j=0;j<23;j=j+1)begin
   rng=rng^(rng<<13);rng=rng^(rng>>17);rng=rng^(rng<<5);
   live_payload={live_payload[687:0],rng};
  end
  if(a.telemetry_snapshot_hold)held_changes=held_changes+1;
 end
 origin_event=(cycle%12347<7);
 if(cycle%12347==0)origin_events=origin_events+1;
end
always @(posedge clk)begin
 cycle=cycle+1;
 if(a.telemetry.start!==b.telemetry.start || a.telemetry.busy!==b.telemetry.busy)
  $fatal(1,"UART acceptance control mismatch at %0d",cycle);
 if(a.telemetry.start && !a.telemetry.busy)begin
  if(a.telemetry.data!==b.telemetry.data)$fatal(1,"byte mismatch");
  $fwrite(trace,"%0d %0d %02x\n",cycle,bytes,a.telemetry.data);
  bytes=bytes+1;
 end
 #1;
 if(txa!==txb || a.radio_tx!==b.radio_tx)$fatal(1,"wire mismatch");
 if(a.rst_n!==b.rst_n || a.telemetry_snapshot_hold!==b.telemetry_snapshot_hold)$fatal(1,"hold/reset mismatch");
 if(a.navigation_body!==b.navigation_body || a.native_navigation.diagnostic_q!==b.native_navigation.diagnostic_q)
  $fatal(1,"diagnostic snapshot mismatch at %0d",cycle);
 if(a.telemetry.snapshot_sequence!==b.telemetry.snapshot_sequence || a.telemetry.snapshot_begin!==b.telemetry.snapshot_begin)
  $fatal(1,"sequence/start mismatch");
 if(previous_hold && !a.telemetry_snapshot_hold)frames=frames+1;
 previous_hold=a.telemetry_snapshot_hold;
 if(frames==2)begin
  if(bytes!=1136 || held_changes<2 || origin_events<2)$fatal(1,"insufficient coverage");
  $display("PASS actual dual top: cycles=%0d bytes=%0d frames=%0d held_changes=%0d origin_events=%0d",cycle,bytes,frames,held_changes,origin_events);
  $fclose(trace);$finish;
 end
 if(cycle>6000000)$fatal(1,"full top timeout");
end
endmodule
