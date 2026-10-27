`timescale 1ns/1ps
module tb;
reg clk=0;always #10 clk=~clk;
acg720_ano_port dut(.clk50(clk),.imu_miso(1'b0),.rc_ppm_in(1'b0),.range_rx(1'b1),.radio_rx(1'b1));
task safe;input expected;begin #1;if(dut.parameter_write_safe!==expected)$fatal(1,"actual core safety cone expected%0d got%0d",expected,dut.parameter_write_safe);end endtask
task put;input[7:0]b;begin
 @(negedge clk);force dut.parameter_rx_valid=1;force dut.parameter_rx_data=b;
 @(negedge clk);force dut.parameter_rx_valid=0;
 repeat(3)@(negedge clk);
end endtask
task request;input[127:0]f;integer k;begin for(k=15;k>=0;k=k-1)put(f[k*8+:8]);end endtask
initial begin
 wait(dut.rst_n);repeat(10)@(negedge clk);if(dut.xy_p_value!=1000 || dut.xy_i_value!=350 || dut.xy_generation!=0)$fatal(1,"B4 top reset defaults");
 force dut.core.rc_valid=0;force dut.core.ch5=1000;
 force dut.core.armed_raw=0;force dut.core.control_enabled=0;force dut.core.taking_off=0;force dut.core.command_fresh=0;
 force dut.core.pwm_ticks1=50000;force dut.core.pwm_ticks2=50000;force dut.core.pwm_ticks3=50000;force dut.core.pwm_ticks4=50000;
 safe(1);
 force dut.core.rc_valid=1;force dut.core.ch5=2000;safe(0);
 force dut.core.ch5=1500;safe(1);force dut.core.rc_valid=0;
 force dut.core.armed_raw=1;safe(0);force dut.core.armed_raw=0;
 force dut.core.control_enabled=1;safe(0);force dut.core.control_enabled=0;
 force dut.core.taking_off=1;safe(0);force dut.core.taking_off=0;
 force dut.core.command_fresh=1;safe(0);force dut.core.command_fresh=0;
 force dut.core.pwm_ticks1=60000;safe(0);force dut.core.pwm_ticks1=50000;
 force dut.core.pwm_ticks2=60000;safe(0);force dut.core.pwm_ticks2=50000;
 force dut.core.pwm_ticks3=60000;safe(0);force dut.core.pwm_ticks3=50000;
 force dut.core.pwm_ticks4=60000;safe(0);force dut.core.pwm_ticks4=50000;safe(1);
 force dut.parameter_rx_error=0;
request(128'ha590010210000000000104b00384a9a9);

 wait(dut.parameters.response_valid);#1;
 if(dut.xy_p_value!=1200 || dut.xy_i_value!=900 || dut.xy_generation!=1)$fatal(1,"top pair not committed");
 if(dut.native_navigation.controller_proof.xy_p_value!=1200 || dut.native_navigation.controller_proof.xy_i_value!=900)$fatal(1,"gain not wired into real controller");
 wait(!dut.parameters.response_valid);repeat(5)@(negedge clk);
 force dut.core.armed_raw=1;
request(128'ha5900102100000000002032002bcea05);

 wait(dut.parameters.response_valid);#1;
 if(dut.parameters.response[151:144]!=4 || dut.xy_p_value!=1200 || dut.xy_i_value!=900 || dut.xy_generation!=1)$fatal(1,"armed top write not rejected");
 wait(!dut.parameters.response_valid);repeat(5)@(negedge clk);
 force dut.core.armed_raw=0;force dut.core.rc_valid=1;force dut.core.ch5=1000;
 force dut.parameter_boundary=0;
request(128'ha5900102100000000003032002bc4054);

 wait(dut.parameters.state==2);@(negedge clk);
 // Actual gate arm FF rises on the same edge at which the bank could commit.
 // Pre-arm switch intent must reject before the old armed Q is sampled.
 force dut.core.ch5=2000;release dut.core.armed_raw;
 force dut.core.gate.sensor_ok=1;force dut.core.gate.channel_count=8;
 force dut.core.gate.ch3=1000;force dut.core.gate.low_ready=1;
 force dut.core.gate.high_hold_count=24999999;force dut.parameter_boundary=1;
 @(posedge clk);#2;if(!dut.core.armed_raw)$fatal(1,"arm-edge test did not arm actual gate");
 wait(dut.parameters.response_valid);#1;
 if(dut.parameters.response[151:144]!=4 || dut.xy_generation!=1 || dut.xy_p_value!=1200 || dut.xy_i_value!=900)$fatal(1,"simultaneous arm/commit escaped guard");
 release dut.parameter_boundary;
 // Controller only advertises a bank boundary after stopped cancellation.
 force dut.native_navigation.controller_proof.state=0;
 force dut.native_navigation.controller_proof.cancel=0;#1;
 if(dut.parameter_boundary)$fatal(1,"live idle could commit");
 force dut.native_navigation.controller_proof.cancel=1;#1;
 if(!dut.parameter_boundary)$fatal(1,"stopped idle cannot commit");
 $display("PASS actual top/core stopped-width arm/controller/fresh/takeoff gates; actual simultaneous arm-FF/commit rejected; bank through real controller ports; cancelled-idle boundary");$finish;
end
initial begin #10000000;$fatal(1,"top test timeout bank_state=%0d response_valid=%0d safe=%0d boundary=%0d",dut.parameters.state,dut.parameters.response_valid,dut.parameter_write_safe,dut.parameter_boundary);end
endmodule
