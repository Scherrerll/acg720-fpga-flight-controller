from pathlib import Path
import os,subprocess,json,hashlib
from xy_pi_cli import encode_request,decode_response,ResponseStream
R=Path(__file__).resolve().parent;O=R/'verification';O.mkdir(exist_ok=True);T=O/'tmp';T.mkdir(exist_ok=True)
env=dict(os.environ,TMP=str(T),TEMP=str(T),TMPDIR=str(T));B=R.parent/'.tools/iverilog/app/bin'
def run(name,tb,sources):
 p=O/(name+'.v');p.write_text(tb);v=O/(name+'.vvp')
 c=subprocess.run([str(B/'iverilog.exe'),'-g2012','-s','tb','-I',str(R/'source'),'-o',str(v),str(p),*map(str,sources)],env=env,capture_output=True,text=True)
 (O/(name+'.compile.log')).write_text(c.stdout+c.stderr);assert c.returncode==0,c.stdout+c.stderr
 c=subprocess.run([str(B/'vvp.exe'),str(v)],env=env,capture_output=True,text=True,timeout=180)
 (O/(name+'.log')).write_text(c.stdout+c.stderr);print(c.stdout[-5000:]);assert c.returncode==0,c.stdout+c.stderr
 return c.stdout
def frame(op,seq,p=0,i=0,change=None):
 f=bytearray(encode_request(op,seq,p,i))
 if change:
  for k,v in change.items():f[k]=v
  import binascii
  f[-2:]=binascii.crc_hqx(f[2:-2],0xffff).to_bytes(2,'big')
 return f"128'h{f.hex()}"
expected=[];lines=[]
def case(op,seq,p=0,i=0,status=0,ap=500,ai=0,g=0,change=None):
 lines.append(f'send_frame({frame(op,seq,p,i,change)});check({status},{ap},{ai},{g});')
 expected.append((status,ap,ai,g))
case(1,1)
case(2,10,1500,1000,ap=1500,ai=1000,g=1)
case(2,10,1500,1000,5,1500,1000,1)
case(2,10,999,0,5,1500,1000,1)
case(2,9,500,0,5,1500,1000,1)
lines.append('write_safe=0;');case(2,11,600,0,4,1500,1000,1)
lines.append('write_safe=1;');case(2,11,600,0,5,1500,1000,1)
case(2,12,10001,0,3,1500,1000,1)
lines.append(f'send_frame({frame(2,13,500,0)} ^ 128\'d1);check(2,1500,1000,1);');expected.append((2,1500,1000,1))
case(2,13,500,0,ap=500,ai=0,g=2)
case(2,14,700,800,1,500,0,2,{2:2})
case(8,14,700,800,6,500,0,2)
case(2,14,700,800,1,500,0,2,{5:1})
case(2,14,700,800,1,500,0,2,{4:17})
case(1,14,1,0,1,500,0,2)
lines.append(f'boundary=0;send_frame({frame(2,14,700,800)});wait(dut.state==2);@(negedge clk);write_safe=0;check(4,500,0,2);write_safe=1;boundary=1;');expected.append((4,500,0,2))
lines.append(f'boundary=0;send_frame({frame(2,15,700,800)});wait(dut.state==2);repeat(40)@(negedge clk);if(p!=500 || i!=0 || gen!=2)$fatal(1,"early commit");boundary=1;check(0,700,800,3);');expected.append((0,700,800,3))
lines.append('put(8\'h00);put(8\'ha5);put(8\'ha5);put(8\'h90);put(1);repeat(110)@(negedge clk);')
case(1,88,ap=700,ai=800,g=3)
lines.append('put(8\'ha5);put(8\'h90);put(1);rx_error=1;@(negedge clk);rx_error=0;')
case(1,89,ap=700,ai=800,g=3)
lines.append('rst_n=0;repeat(3)@(negedge clk);rst_n=1;')
case(1,90)
case(2,1,0,10000,ap=0,ai=10000,g=1)
case(2,2,10000,0,ap=10000,ai=0,g=2)
case(2,3,0,10001,status=3,ap=10000,ai=0,g=2)
# Every payload/header-body bit corruption is rejected by actual RTL CRC.
for bit in range(16,112):
 lines.append(f'send_frame({frame(2,4,1500,1000)} ^ (128\'d1<<{bit}));check(2,10000,0,2);')
 expected.append((2,10000,0,2))
# Too-short frames time out; extra trailing bytes cannot become a SET.
lines.append('put(8\'ha5);put(8\'h90);put(1);put(2);put(16);repeat(110)@(negedge clk);')
case(1,200,ap=10000,ai=0,g=2)
lines.append('put(8\'h11);put(8\'h22);put(8\'h33);')
case(1,201,ap=10000,ai=0,g=2)
tb='''`timescale 1ns/1ps
module tb;
reg clk=0,rst_n=0,rx_valid=0,rx_error=0,write_safe=1,boundary=1,ready=0;reg[7:0]data=0;
wire[15:0]p,i;wire[31:0]gen;wire valid;wire[191:0]resp;
always #10 clk=~clk;
xy_pi_parameters #(.TIMEOUT_TICKS(100))dut(clk,rst_n,rx_valid,rx_error,data,write_safe,boundary,p,i,gen,valid,resp,ready);
task put;input[7:0]b;begin @(negedge clk);data=b;rx_valid=1;@(negedge clk);rx_valid=0;repeat(2)@(negedge clk);end endtask
task send_frame;input[127:0]f;integer k;begin for(k=15;k>=0;k=k-1)put(f[k*8+:8]);end endtask
task check;input integer status,ep,ei,eg;begin
 wait(valid);#1;
 if(resp[151:144]!=status || p!=ep || i!=ei || gen!=eg)$fatal(1,"response status=%0d expected=%0d p=%0d i=%0d gen=%0d",resp[151:144],status,p,i,gen);
 $display("RESPONSE %048h",resp);
 repeat(4)@(negedge clk);if(!valid)$fatal(1,"response not held under backpressure");
 ready=1;@(negedge clk);ready=0;repeat(3)@(negedge clk);
end endtask
initial begin repeat(5)@(negedge clk);rst_n=1;
'''+ '\n'.join(lines)+'''\n$display("PASS protocol registers replay CRC range reset timeout lock race atomic-boundary backpressure");$finish;end
initial begin #10000000;$fatal(1,"timeout");end
endmodule
'''
log=run('protocol_tb',tb,[R/'source/xy_pi_parameters.v'])
rows=[decode_response(bytes.fromhex(s.split()[1])) for s in log.splitlines() if s.startswith('RESPONSE ')]
assert len(rows)==len(expected)
for row,e in zip(rows,expected):assert (row['status'],row['p_wire'],row['i_wire'],row['generation'])==e
# Real stream decoder: fragmentation, coalescing, telemetry/noise and CRC failure.
all_packets=[bytes.fromhex(s.split()[1]) for s in log.splitlines() if s.startswith('RESPONSE ')]
bad=bytearray(all_packets[0]);bad[-1]^=1
wire=b'noise\xa5'+bytes(bad)+b'\xa5\x86'+bytes(222)+b''.join(all_packets)
for step in (1,2,7,23,4096):
 stream=ResponseStream();actual=[]
 for at in range(0,len(wire),step):actual+=stream.feed(wire[at:at+step])
 assert actual==rows
uart='''`timescale 1ns/1ps
module tb;
reg clk=0,rst_n=0,rx=1;wire valid,error;wire[7:0]data;
integer received=0,errors=0;
always #10 clk=~clk;
xy_pi_uart_rx dut(clk,rst_n,rx,valid,error,data);
always @(posedge clk)if(valid)begin
 if(data!==(received==0?8'ha5:8'h90))$fatal(1,"UART byte mismatch %h",data);
 received=received+1;
end else if(error)errors=errors+1;
task octet;input[7:0]b;input stop;integer k;begin
 @(negedge clk);rx=0;repeat(434)@(negedge clk);
 for(k=0;k<8;k=k+1)begin rx=b[k];repeat(434)@(negedge clk);end
 rx=stop;repeat(434)@(negedge clk);rx=1;repeat(20)@(negedge clk);
end endtask
initial begin repeat(5)@(negedge clk);rst_n=1;
 rx=0;repeat(30)@(negedge clk);rx=1;repeat(500)@(negedge clk);
 octet(8'ha5,1);octet(8'h90,1);octet(8'hff,0);repeat(500)@(negedge clk);
 if(received!=2 || errors!=1)$fatal(1,"UART count valid=%0d errors=%0d",received,errors);
 $display("PASS UART physical 434 clocks/bit 115200 false-start bad-stop");$finish;end
initial begin #1000000;$fatal(1,"UART timeout");end
endmodule
'''
run('uart_tb',uart,[R/'source/xy_pi_parameters.v'])
(O/'protocol_results.json').write_text(json.dumps({'passed':True,'register_cases':len(rows),'stream_fragment_sizes':[1,2,7,23,4096],'physical_uart_passed':True,'scope':'actual RTL and shipping host parser; no hardware'},indent=2))
