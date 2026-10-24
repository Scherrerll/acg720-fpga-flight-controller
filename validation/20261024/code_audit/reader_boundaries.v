`timescale 1ns/1ps
// Offline UART-to-metric boundary checks against the frozen reader source.
// CLOCK_HZ is scaled to 1 MHz; each UART bit uses the receiver's rounded 9 ticks.
module reader_boundaries;
 reg clk=0,rst_n=0,rx=1;
 always #5 clk=~clk;
 wire sample,range_ok,flow_ok,integrated;
 wire [31:0] distance,dt,age;
 wire signed [31:0] vx,vy;
 mtf01p_reader #(.CLOCK_HZ(1000000)) dut(
  .clk(clk),.rst_n(rst_n),.rx(rx),.uptime_ms(64'd0),.diagnostic_hold(1'b0),
  .diagnostic_body(),.metric_sample_valid(sample),.metric_range_valid(range_ok),
  .metric_flow_valid(flow_ok),.metric_interval_integrated(integrated),
  .metric_distance_mm(distance),.metric_dt_ms(dt),.module_age_ms(age),
  .metric_vx_x100(vx),.metric_vy_x100(vy));
 integer checks=0,k;
 reg [7:0] bytes[0:25];
 reg [7:0] checksum;
 reg [31:0] saved_samples,saved_time;
 task clocks; input integer n; begin repeat(n) @(negedge clk); end endtask
 task check; input ok; input [767:0] msg;
  begin if(ok!==1'b1)begin $display("FAIL: %0s",msg);$fatal(1);end checks=checks+1;end
 endtask
 task reset;
  begin rx=1;rst_n=0;clocks(5);rst_n=1;clocks(5);end
 endtask
 task uart_byte;input [7:0] b;integer j;
  begin rx=0;clocks(9);for(j=0;j<8;j=j+1)begin rx=b[j];clocks(9);end rx=1;clocks(9);end
 endtask
 task frame;
  input [31:0] t,mm;
  input [7:0] seq,tof,quality,flow;
  input signed [15:0] fx,fy;
  input corrupt;
  integer i;
  begin
   bytes[0]=8'hef;bytes[1]=15;bytes[2]=0;bytes[3]=8'h51;bytes[4]=seq;bytes[5]=20;
   bytes[6]=t[7:0];bytes[7]=t[15:8];bytes[8]=t[23:16];bytes[9]=t[31:24];
   bytes[10]=mm[7:0];bytes[11]=mm[15:8];bytes[12]=mm[23:16];bytes[13]=mm[31:24];
   bytes[14]=255;bytes[15]=0;bytes[16]=tof;bytes[17]=255;
   bytes[18]=fx[7:0];bytes[19]=fx[15:8];bytes[20]=fy[7:0];bytes[21]=fy[15:8];
   bytes[22]=quality;bytes[23]=flow;bytes[24]=255;bytes[25]=255;
   checksum=0;
   for(i=0;i<26;i=i+1)begin checksum=checksum+bytes[i];uart_byte(bytes[i]);end
   uart_byte(checksum ^ (corrupt ? 8'h01:8'h00));clocks(30);
  end
 endtask
 initial begin
  reset();
  frame(100,12000,1,1,85,1,-32768,32767,0);
  check(range_ok && flow_ok && distance==12000,"valid signed extremes/range upper boundary accepted");
  check(vx== -32'sd393216000 && vy==32'sd393204000,"signed product preserves both extremes");
  frame(110,12001,2,1,85,1,10,-10,0);
  check(!range_ok && !flow_ok && vx==0 && vy==0,"distance above 12000 cannot wrap into eligibility");
  frame(120,222,3,0,85,1,10,-10,0);
  check(!range_ok && !flow_ok,"bad TOF status withdraws both domains");
  frame(130,222,4,1,0,1,10,-10,0);
  check(range_ok && !flow_ok,"zero flow quality withdraws only flow");
  frame(140,222,5,1,85,0,10,-10,0);
  check(range_ok && !flow_ok,"bad flow status preserves range availability");
  saved_samples=dut.samples;saved_time=dut.time_ms;
  frame(150,222,6,1,85,1,10,-10,1);
  check(dut.samples==saved_samples && dut.time_ms==saved_time && dut.checksum_errors==1,"bad checksum cannot commit data");
  frame(150,222,7,1,85,1,10,-10,0);
  check(dut.samples==saved_samples+1 && dut.time_ms==150,"parser recovers on next valid packet");
  // Every duplicate is a valid UART packet, but cannot renew the source timestamp.
  for(k=0;k<84;k=k+1)frame(150,222,8+k,1,85,1,10,-10,0);
  check(age>=200 && !range_ok && !flow_ok,"repeated source timestamp expires despite continuous valid packets");
  check(dut.duplicates==84,"duplicate counter matches repeated packets");
  frame(160,222,100,1,85,1,10,-10,0);
  check(age<5 && range_ok && flow_ok && !integrated,"fresh timestamp restores data without bridging stale integration gap");
  reset();
  frame(32'hfffffff0,222,254,1,85,1,10,-10,0);
  frame(32'hfffffffa,222,255,1,85,1,10,-10,0);
  frame(32'h00000004,222,0,1,85,1,10,-10,0);
  check(dt==10 && dut.restarts==0 && dut.missing==0 && integrated,"timestamp and sequence rollover remain continuous");
  frame(0,222,1,1,85,1,10,-10,0);
  check(dut.restarts==1 && !integrated && dut.x_x100000==0 && dut.y_x100000==0,"backward source time creates a clean integration epoch");
  $display("PASS: %0d UART/parser/metric boundary checks",checks);$finish;
 end
 initial begin #50000000;$fatal(1,"timeout");end
endmodule
