from pathlib import Path
import hashlib,json,os,struct,subprocess
ROOT=Path(__file__).resolve().parent;SOURCE=ROOT/'candidate'
IV=ROOT.parent/'.tools/iverilog/app/bin/iverilog.exe'
payload=struct.pack('<IIBBBBhhBBH',1,1000,100,0,1,0,0,0,50,1,0)
frame=bytes([0xef,1,1,0x51,1,20])+payload;frame+=bytes([sum(frame)&255]);assert len(frame)==27
path=(ROOT/'wire.hex').as_posix()
tb='''`timescale 1ns/1ps
module capture_protocol;
 reg clk=0,rx=1,tx_ack=0;always #10 clk=~clk;
 wire tx;acg720_ano_port dut(.clk50(clk),.imu_miso(1'b0),.rc_ppm_in(1'b0),.range_rx(rx),.radio_tx(tx));
 integer file,count=0,i=0,j=0;reg [7:0] packet[0:26];
 task byte_rx(input[7:0] value);integer b;begin
  @(negedge clk);rx=0;repeat(434)@(negedge clk);
  for(b=0;b<8;b=b+1)begin rx=value[b];repeat(434)@(negedge clk);end
  rx=1;repeat(868)@(negedge clk);
 end endtask
 always @(posedge clk)begin tx_ack<=dut.telemetry.start;if(dut.telemetry.start)begin
  $fwrite(file,"%02x\\n",dut.telemetry.data);count=count+1;
  if(count==644)begin $fclose(file);$display("PASS capture_protocol644 bytes: actual top, real Micolink UART receive, byte-FSM output with immediate transport acknowledgment");$finish;end
 end end
 initial begin
'''
tb+=f'file=$fopen("{path}","w");\n'+''.join(f'packet[{i}]=8\'h{x:02x};'for i,x in enumerate(frame))+'\n'
tb+='''repeat(400)@(negedge clk);
 for(i=0;i<27;i=i+1)byte_rx(packet[i]);
 repeat(5000)@(negedge clk);
 if(dut.mtf.samples!=1)$fatal(1,"real Micolink frame not received");
 force dut.telemetry.busy=tx_ack;
 force dut.telemetry.ticks=10000000;
 @(negedge clk);release dut.telemetry.ticks;
 end
 initial begin #10000000;$fatal(1,"protocol capture timeout count=%0d",count);end
endmodule
'''
(ROOT/'capture_protocol_tb.v').write_text(tb)
env=dict(os.environ,TMP=str(ROOT/'tmp'),TEMP=str(ROOT/'tmp'),TMPDIR=str(ROOT/'tmp'))
commands=[]
for argv in ([IV,'-g2012','-I',SOURCE,'-s','capture_protocol','-o',ROOT/'tmp/capture_protocol.vvp',ROOT/'capture_protocol_tb.v',*sorted(SOURCE.rglob('*.v'))],[IV.with_name('vvp.exe'),'-n',ROOT/'tmp/capture_protocol.vvp']):
    r=subprocess.run(list(map(str,argv)),capture_output=True,text=True,env=env,timeout=180)
    commands.append(dict(argv=list(map(str,argv)),returncode=r.returncode,stdout=r.stdout,stderr=r.stderr));(ROOT/'protocol_capture_commands.json').write_text(json.dumps(commands,indent=2)+'\n')
    print(r.stdout,r.stderr,flush=True);r.check_returncode()
assert 'PASS capture_protocol644'in commands[-1]['stdout']
print('PASS captured current RTL protocol bytes; no physical UART transmission claimed',flush=True)
