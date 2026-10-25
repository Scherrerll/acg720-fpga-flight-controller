`timescale 1ns/1ps
module tb;
reg clk=0,rst_n=0,rx=1;wire tx,btx,rv,re;wire[7:0]rd;
wire valid,ready;wire[191:0]packet;wire[15:0]p,i;wire[31:0]gen;
always #10 clk=~clk;
xy_pi_uart_rx rx_uart(clk,rst_n,rx,rv,re,rd);
xy_pi_parameters bank(clk,rst_n,rv,re,rd,1'b1,1'b1,p,i,gen,valid,packet,ready);
telemetry_tx #(.PERIOD(10000000),.DIAGNOSTIC_INFO(1),.ROTATION_INFO(1),.FLIGHT_INFO(1),.MTF_INFO(1),.NAV_INFO(1),.EXTERNAL_SNAPSHOT(1))dut(.clk(clk),.core_body(864'h123456789abcdef),.extension(888'hffffeeee),.acceleration_body(216'h123456),.range_diagnostic_body(344'd0),.flight_info_body(272'h345678),.mtf_body(976'h6789abcd),.nav_body(720'h3245678),.rotation_body(336'h1234),.diagnostic_body(512'habcdef),.diagnostic_tick(32'h998877),.snapshot_hold(),.parameter_valid(valid),.parameter_packet(packet),.parameter_ready(ready),.tx(tx));
telemetry_before #(.PERIOD(10000000),.DIAGNOSTIC_INFO(1),.ROTATION_INFO(1),.FLIGHT_INFO(1),.MTF_INFO(1),.NAV_INFO(1),.EXTERNAL_SNAPSHOT(1))before_tx(.clk(clk),.core_body(864'h123456789abcdef),.extension(888'hffffeeee),.acceleration_body(216'h123456),.range_diagnostic_body(344'd0),.flight_info_body(272'h345678),.mtf_body(976'h6789abcd),.nav_body(720'h3245678),.rotation_body(336'h1234),.diagnostic_body(512'habcdef),.diagnostic_tick(32'h998877),.snapshot_hold(),.tx(btx));

wire tv,te;wire[7:0]td;integer n=0,bn=0;
xy_pi_uart_rx wire_monitor(clk,rst_n,tx,tv,te,td);
always @(posedge clk)begin
 if(tv)begin $display("WIRE %02h",td);n=n+1;end
 if(te)$fatal(1,"TX framing error");
 if(before_tx.start)begin $display("BASE %02h",before_tx.data);bn=bn+1;end
end
task octet;input[7:0]b;integer k;begin
 @(negedge clk);rx=0;repeat(434)@(negedge clk);
 for(k=0;k<8;k=k+1)begin rx=b[k];repeat(434)@(negedge clk);end
 rx=1;repeat(434)@(negedge clk);
end endtask
task request;input[127:0]f;integer k;begin for(k=15;k>=0;k=k-1)octet(f[k*8+:8]);end endtask
initial begin
 repeat(10)@(negedge clk);rst_n=1;dut.ticks=10000000;before_tx.ticks=10000000;
 repeat(500)@(negedge clk);
request(128'ha5900101100000000064000000005b89);
wait(n==668);repeat(500)@(negedge clk);request(128'ha590010210000000006505dc03e80ce7);

 wait(n==692);repeat(1000)@(negedge clk);
 if(bn!=644 || p!=1500 || i!=1000 || gen!=1)$fatal(1,"link count/commit");
 $display("PASS complete telemetry packet group preserved; UART GET and SET responses interleaved at boundaries");$finish;
end
initial begin #100000000;$fatal(1,"link timeout n=%0d bn=%0d state=%0d",n,bn,dut.state);end
endmodule
