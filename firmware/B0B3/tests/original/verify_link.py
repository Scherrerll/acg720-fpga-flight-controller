from pathlib import Path
import os,subprocess,json,hashlib
from xy_pi_cli import encode_request,ResponseStream
R=Path(__file__).resolve().parent;O=R/'verification';T=O/'tmp';B=R.parent/'.tools/iverilog/app/bin'
P=R/'test_baseline/source/telemetry_tx.v'
assert hashlib.sha256(P.read_bytes()).hexdigest()=='feaae7a1f14e7e420554f58b0d106ab2a4ef2da7e1bbd9cd0fd5c81379db5582'
(O/'telemetry_before.v').write_text(P.read_text().replace('module telemetry_tx #(','module telemetry_before #('))
ports='''.clk(clk),.core_body(864'h123456789abcdef),.extension(888'hffffeeee),.acceleration_body(216'h123456),.range_diagnostic_body(344'd0),.flight_info_body(272'h345678),.mtf_body(976'h6789abcd),.nav_body(720'h3245678),.rotation_body(336'h1234),.diagnostic_body(512'habcdef),.diagnostic_tick(32'h998877),.snapshot_hold()'''
tb='''`timescale 1ns/1ps
module tb;
reg clk=0,rst_n=0,rx=1;wire tx,btx,rv,re;wire[7:0]rd;
wire valid,ready;wire[191:0]packet;wire[15:0]p,i;wire[31:0]gen;
always #10 clk=~clk;
xy_pi_uart_rx rx_uart(clk,rst_n,rx,rv,re,rd);
xy_pi_parameters bank(clk,rst_n,rv,re,rd,1'b1,1'b1,p,i,gen,valid,packet,ready);
'''+f'''telemetry_tx #(.PERIOD(10000000),.DIAGNOSTIC_INFO(1),.ROTATION_INFO(1),.FLIGHT_INFO(1),.MTF_INFO(1),.NAV_INFO(1),.EXTERNAL_SNAPSHOT(1))dut({ports},.parameter_valid(valid),.parameter_packet(packet),.parameter_ready(ready),.tx(tx));
telemetry_before #(.PERIOD(10000000),.DIAGNOSTIC_INFO(1),.ROTATION_INFO(1),.FLIGHT_INFO(1),.MTF_INFO(1),.NAV_INFO(1),.EXTERNAL_SNAPSHOT(1))before_tx({ports},.tx(btx));
'''+'''
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
'''+f'''request(128'h{encode_request(1,100).hex()});
wait(n==668);repeat(500)@(negedge clk);request(128'h{encode_request(2,101,1500,1000).hex()});
'''+'''
 wait(n==692);repeat(1000)@(negedge clk);
 if(bn!=644 || p!=1500 || i!=1000 || gen!=1)$fatal(1,"link count/commit");
 $display("PASS complete telemetry packet group preserved; UART GET and SET responses interleaved at boundaries");$finish;
end
initial begin #100000000;$fatal(1,"link timeout n=%0d bn=%0d state=%0d",n,bn,dut.state);end
endmodule
'''
(O/'link_tb.v').write_text(tb)
env=dict(os.environ,TMP=str(T),TEMP=str(T),TMPDIR=str(T))
sources=[O/'link_tb.v',O/'telemetry_before.v',R/'source/telemetry_tx.v',R/'source/xy_pi_parameters.v',R/'source/core/spi_uart_modules.v']
c=subprocess.run([str(B/'iverilog.exe'),'-g2012','-s','tb','-o',str(O/'link.vvp'),*map(str,sources)],env=env,capture_output=True,text=True)
(O/'link.compile.log').write_text(c.stdout+c.stderr);assert c.returncode==0,c.stdout+c.stderr
with (O/'link.log').open('w') as log:c=subprocess.run([str(B/'vvp.exe'),str(O/'link.vvp')],env=env,stdout=log,stderr=subprocess.STDOUT,timeout=300)
s=(O/'link.log').read_text();assert c.returncode==0,s[-2000:]
actual=bytes(int(l.split()[1],16) for l in s.splitlines() if l.startswith('WIRE '));base=bytes(int(l.split()[1],16) for l in s.splitlines() if l.startswith('BASE '))
assert actual[:644]==base and len(base)==644
stream=ResponseStream();rows=stream.feed(actual[644:]);assert len(rows)==2
assert rows[0]['sequence']==100 and rows[0]['p_wire']==500 and rows[0]['i_wire']==0
assert rows[1]['sequence']==101 and rows[1]['p_wire']==1500 and rows[1]['i_wire']==1000 and rows[1]['generation']==1
(O/'link_results.json').write_text(json.dumps({'passed':True,'baseline_telemetry_bytes_equal':len(base),'response_rows':rows,'actual_serial_bit_sampling':True,'scope':'real UART RX, bank, TX arbiter and serial output; no hardware'},indent=2))
print('PASS',len(base),'baseline bytes match exactly; complete GET/SET serial responses decoded by shipping host tool')
