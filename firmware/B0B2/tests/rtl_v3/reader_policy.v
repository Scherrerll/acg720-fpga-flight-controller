`timescale 1ns/1ps
module reader_policy;
 reg clk=0;always #10 clk=~clk;reg rst_n=0;
 wire nready,bready;wire [7:0] nfault,bfault;
 bmi088_reader actual(.clk(clk),.rst_n(rst_n),.miso(1'b0),.record_ready(nready),.record_fault(nfault));
 bmi088_reader_baseline original(.clk(clk),.rst_n(rst_n),.miso(1'b0),.record_ready(bready),.record_fault(bfault));
 task tick;begin @(posedge clk);#1;end endtask
 initial begin
  repeat(3)tick();rst_n=1;
  @(negedge clk);
  // Hold the real reader in the gyro-status transaction, with no completion.
  actual.state=16;original.state=16;
  actual.config_ok=1;original.config_ok=1;
  original.monitor_active=1;original.valid_age=2999998;
  force actual.busy=0;force original.busy=0;
  force actual.done=0;force original.done=0;
  repeat(5)tick();
  if(original.state!=0 || bfault!=8'h10 || original.config_ok)$fatal(1,"baseline timeout witness absent");
  if(actual.state!=16 || nfault!=0 || !actual.config_ok || nready)$fatal(1,"silence reset or fabricated record");
  @(negedge clk);actual.state=14;
  tick();
  if(!nready || nfault==0 || actual.config_ok)$fatal(1,"ID/config check removed");
  $display("PASS reader_policy: baseline resets at silence threshold; candidate waits without inventing samples; actual ID/config rejection retained");
  $finish;
 end
 initial begin #10000;$fatal(1,"reader test timeout");end
endmodule
