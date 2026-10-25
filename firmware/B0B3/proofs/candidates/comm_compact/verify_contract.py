"""Additional actual-UART bank/zero-copy TX ownership/backpressure check."""
from pathlib import Path
import hashlib,json,os,re,subprocess
C=Path(__file__).resolve().parent;R=C.parents[1];O=C/'verification';B=R.parent/'.tools/iverilog/app/bin';T=O/'tmp'
base=(O/'link_tb.v').read_text()
monitor='''
reg holding=0;reg[191:0]held_packet=0;
integer ack_count=0,frame_starts=0,hold_clocks=0,max_hold_clocks=0;
always @(posedge clk)begin
 if(rst_n)begin
  if(valid)begin
   if(!holding)begin holding=1;held_packet=packet;hold_clocks=0;end
   else if(packet!==held_packet)$fatal(1,"bank changed packet before final completion ACK");
   hold_clocks=hold_clocks+1;
   if(bank.count!=0 || bank.state!=0)$fatal(1,"bank accepted another frame while response held");
  end else if(holding)$fatal(1,"response_valid dropped before UART ownership completed");
  if(ready)begin
   if(!valid || dut.state!=8 || dut.busy || dut.parameter_index!=23)$fatal(1,"ready was not last-byte physical UART completion");
   if(!holding)$fatal(1,"ACK without a held packet");
   if(hold_clocks>max_hold_clocks)max_hold_clocks=hold_clocks;
   ack_count=ack_count+1;holding=0;
  end
  if(rv && rd==8'ha5 && bank.count==0 && !valid)begin
   frame_starts=frame_starts+1;
   if(frame_starts>ack_count+1)$fatal(1,"next request began before preceding last-byte ACK");
  end
 end
end
'''
assert base.count('task octet;')==1
tb=base.replace('task octet;',monitor+'\ntask octet;')
needle=' $display("PASS complete telemetry packet group preserved; UART GET and SET responses interleaved at boundaries");$finish;'
assert tb.count(needle)==1
tb=tb.replace(needle,''' if(ack_count!=2 || frame_starts!=2 || holding || valid || max_hold_clocks<1000000)$fatal(1,"ownership/backpressure coverage incomplete ack=%0d frames=%0d held=%0d",ack_count,frame_starts,holding);
 $display("CONTRACT ACKs=%0d request_starts=%0d max_held_packet_clocks=%0d",ack_count,frame_starts,max_hold_clocks);
 $display("PASS stable bank packet held through full telemetry backpressure; ready only after final UART busy completion; subsequent request then accepted");$finish;''')
(O/'contract_tb.v').write_text(tb)
sources=[O/'contract_tb.v',O/'telemetry_before.v',C/'source/telemetry_tx.v',C/'source/xy_pi_parameters.v',C/'source/core/spi_uart_modules.v']
env=dict(os.environ,TMP=str(T),TEMP=str(T),TMPDIR=str(T))
c=subprocess.run([str(B/'iverilog.exe'),'-g2012','-s','tb','-o',str(O/'contract.vvp'),*map(str,sources)],env=env,capture_output=True,text=True)
(O/'contract.compile.log').write_text(c.stdout+c.stderr);assert c.returncode==0,c.stdout+c.stderr
with (O/'contract.log').open('w')as log:c=subprocess.run([str(B/'vvp.exe'),str(O/'contract.vvp')],env=env,stdout=log,stderr=subprocess.STDOUT,timeout=300)
s=(O/'contract.log').read_text();assert c.returncode==0,s[-2500:]
wire=lambda text:bytes(int(l.split()[1],16)for l in text.splitlines()if l.startswith('WIRE '))
actual=wire(s);canonical=wire((R/'verification/link.log').read_text())
assert len(actual)==692 and actual==canonical,'candidate differs from canonical 644-byte telemetry + GET/SET response stream'
match=re.search(r'CONTRACT ACKs=(\d+) request_starts=(\d+) max_held_packet_clocks=(\d+)',s);assert match
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
result=dict(passed=True,last_byte_ack_count=int(match[1]),request_starts=int(match[2]),max_held_packet_clocks=int(match[3]),canonical_wire_bytes_identical=len(actual),scope='real UART, unchanged parameter bank, candidate TX; stable-bank ownership and final-byte ready contract',evidence_sha256={str(p.relative_to(C)):sha(p)for p in [Path(__file__),O/'contract_tb.v',O/'contract.log',O/'contract.compile.log',C/'source/telemetry_tx.v',C/'source/xy_pi_parameters.v']},canonical_link_log_sha256=sha(R/'verification/link.log'))
(O/'contract_results.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
