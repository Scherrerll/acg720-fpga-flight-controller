`timescale 1ns/1ps
module top13_root;
 GSR GSR(.GSRI(1'b1));
 tb original();
 initial begin
  #1;
`ifdef GW5_USE_VENDOR_BRAM
  if(original.dut.staged_telemetry.extension_storage.SIMULATION_BYPASS!==0)$fatal(1,"Vendor top13 FF bypass");
`else
  if(original.dut.staged_telemetry.extension_storage.SIMULATION_BYPASS!==1)$fatal(1,"Default top13 branch differs");
`endif
 end
endmodule
