`timescale 1ns/1ps
// Adapted from the historical actual-top SP miter. Only extension source payload
// and the byte-level transport-busy acknowledgment are forced. No hold/state,
// boot/reset/ticks/index/cache/storage register is forced or preloaded.
module extension_top_miter;
 parameter integer TEST_PERIOD=8;
 reg clk=0,ackbusy=0,capture_armed=0,capturing=0;
 reg[887:0]extension_input=0,expected_extension=0,last_extension=0;
 reg sampled_hold=0,previous_hold=0;
 reg[255:0]index_seen=0;reg[31:0]rng=32'h32c619a7;
 integer i,j,cycles=0,bytes=0,total_starts=0,busy_count=0,held_checks=0,updates=0,releases=0,captured_releases=0,fd;
 integer x_captures=0,z_captures=0,partial_bank_vectors=0;
 GSR GSR(.GSRI(1'b1));
 acg720_ano_port_before old(.clk50(clk),.imu_miso(1'b0),.rc_ppm_in(1'b0),.range_rx(1'b1),.radio_rx(1'b1));
 acg720_ano_port revised(.clk50(clk),.imu_miso(1'b0),.rc_ppm_in(1'b0),.range_rx(1'b1),.radio_rx(1'b1));
 defparam old.telemetry.PERIOD=TEST_PERIOD;
 defparam revised.telemetry.PERIOD=TEST_PERIOD;
 always @(posedge clk)begin
  sampled_hold<=old.telemetry_snapshot_hold;
  if(!old.telemetry_snapshot_hold)begin
   expected_extension<=extension_input;updates=updates+1;
   if(extension_input==={888{1'bx}})x_captures=x_captures+1;
   if(extension_input==={888{1'bz}})z_captures=z_captures+1;
  end
  index_seen[revised.telemetry.index]<=1;
  if(previous_hold && !old.telemetry_snapshot_hold)begin
   releases=releases+1;
   if(capturing)captured_releases=captured_releases+1;
   if(capture_armed)capturing<=1;
  end
  previous_hold<=old.telemetry_snapshot_hold;
  if(old.telemetry.start)begin
   total_starts=total_starts+1;
   if(capturing)begin $fwrite(fd,"%02x\n",old.telemetry.data);bytes=bytes+1;end
   busy_count<=3+(total_starts%5)+(total_starts%31==0 ?17:0);ackbusy<=1;
  end else if(busy_count>0)begin busy_count<=busy_count-1;ackbusy<=1;end else ackbusy<=0;
 end
 task random_inputs;begin
  for(j=0;j<888;j=j+8)begin rng=rng*32'd1664525+32'd1013904223;extension_input[j+:8]=rng[31:24];end
  if(i%7==0)begin extension_input=0;extension_input[i%888]=1'b1;end
  if(i%11==0)begin extension_input={888{1'b1}};extension_input[i%888]=1'b0;end
  if(i%13==0)begin extension_input[887:864]=24'hf05aa5;partial_bank_vectors=partial_bank_vectors+1;end
 end endtask
 task compare;begin
  if(revised.staged_telemetry.extension_storage.SIMULATION_BYPASS!==0)$fatal(1,"SP branch not selected");
  if(old.staged_telemetry.extension_q!==expected_extension || revised.staged_telemetry.extension_q!==expected_extension)
   $fatal(1,"888-bit enabled same-edge expected tuple mismatch cycle=%0d hold=%b",cycles,sampled_hold);
  if(revised.staged_telemetry.extension_storage.hardware_bram.padded_q[895:888]!==8'd0)$fatal(1,"Final SP padding corrupted");
  if(revised.telemetry.bank_select !== (32'd1 << revised.telemetry.index[7:3]))$fatal(1,"Natural cached selector invariant failed");
  if({old.imu_sck,old.imu_mosi,old.imu_cs_n,old.imu_gyro_cs_n,old.range_tx,old.uart_tx,old.radio_tx,old.led2,old.led3,old.motor1_pwm,old.motor2_pwm,old.motor3_pwm,old.motor4_pwm} !==
     {revised.imu_sck,revised.imu_mosi,revised.imu_cs_n,revised.imu_gyro_cs_n,revised.range_tx,revised.uart_tx,revised.radio_tx,revised.led2,revised.led3,revised.motor1_pwm,revised.motor2_pwm,revised.motor3_pwm,revised.motor4_pwm})
   $fatal(1,"Actual top public output mismatch cycle=%0d",cycles);
  if({old.core_snapshot,old.extension_snapshot,old.acceleration_snapshot,old.range_diagnostic_snapshot,old.flight_info_q,old.rotation_pair_q,old.mtf_body,old.navigation_body,old.telemetry.start,old.telemetry.data,old.telemetry_snapshot_hold,old.core.telemetry_body} !==
     {revised.core_snapshot,revised.extension_snapshot,revised.acceleration_snapshot,revised.range_diagnostic_snapshot,revised.flight_info_q,revised.rotation_pair_q,revised.mtf_body,revised.navigation_body,revised.telemetry.start,revised.telemetry.data,revised.telemetry_snapshot_hold,revised.core.telemetry_body})
   $fatal(1,"Actual snapshot/serializer/core telemetry mismatch cycle=%0d bytes=%0d",cycles,bytes);
  if(sampled_hold)begin
   if(revised.staged_telemetry.extension_q!==last_extension)$fatal(1,"Extension changed during natural hold");held_checks=held_checks+1;
  end
  last_extension=revised.staged_telemetry.extension_q;
 end endtask
 task tick;begin #10;clk=1;#2;cycles=cycles+1;compare();#8;clk=0;end endtask
 initial begin
  force old.extension=extension_input;force revised.extension=extension_input;
  force old.telemetry.busy=ackbusy;force revised.telemetry.busy=ackbusy;
  fd=$fopen("wire.hex","w");if(!fd)$fatal(1,"Cannot open owned capture file");
  #1;compare();
  for(i=0;i<4096;i=i+1)begin
   random_inputs();
   if(i==1)extension_input={888{1'bx}};
   if(i==2)extension_input={888{1'bz}};
   if(i==3)for(j=0;j<888;j=j+1)case(j%4)0:extension_input[j]=0;1:extension_input[j]=1;2:extension_input[j]=1'bx;3:extension_input[j]=1'bz;endcase
   tick();
  end
  // Keep the real serializer running. Begin byte capture only at its next
  // natural inter-group hold release, after all source payloads are known.
  random_inputs();capture_armed=1;
  while(bytes<1932 && cycles<4096+5*(TEST_PERIOD+20000))begin i=i+1;random_inputs();tick();end
  $fclose(fd);
  if(bytes!=1932 || captured_releases<2 || held_checks<1000 || updates<3 || x_captures<1 || z_captures<1 || partial_bank_vectors<100)
   $fatal(1,"Natural integration coverage incomplete bytes=%0d releases=%0d holds=%0d updates=%0d X/Z=%0d/%0d",bytes,captured_releases,held_checks,updates,x_captures,z_captures);
  if(index_seen[223:0]!=={224{1'b1}})$fatal(1,"Natural primary-frame byte-index coverage incomplete");
  $display("PASS actual_v18_FF_vs_v21_vendor_SP extension888=1 SP=28 all_public_outputs=13 no_internal_state_force_or_preload=1 forced_boundaries=extension_payload_and_transport_busy period=%0d CLK_HZ=50000000 bytes=%0d captured_releases=%0d holds=%0d updates=%0d X_captures=%0d Z_captures=%0d cycles=%0d",TEST_PERIOD,bytes,captured_releases,held_checks,updates,x_captures,z_captures,cycles);$finish;
 end
 initial begin #10000000;$fatal(1,"Bounded natural integration timeout");end
endmodule
