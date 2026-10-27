"""Actual UART default50 equivalence,49MHz loopback, independent host frames and TX bit widths."""
from pathlib import Path
import datetime,hashlib,json,os,subprocess
R=Path(__file__).resolve().parents[3];O=Path(__file__).resolve().parent;M=O/'clock49_uart';D=M/'proofs'
W=R/'out/z_aw_fix_20261026/clock49_working/source';B=R/'out/z_aw_fix_20261026/compact_aw_v4/canonical/source'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
utc=lambda:datetime.datetime.now(datetime.timezone.utc).isoformat()
binding=json.loads((M/'SOURCE_BINDING.json').read_text(encoding='utf8'))
assert all(sha(W/n)==x['new_sha256'] and sha(B/n)==x['old_sha256'] for n,x in binding['changes'].items())
assert not D.exists();D.mkdir();T=D/'tmp';T.mkdir()
original=(B/'core/spi_uart_modules.v').read_text(encoding='utf8');assert original.count('module uart_tx_115200 (')==1
(D/'old_tx.v').write_text('module old_uart_tx_115200 ('+original.split('module uart_tx_115200 (',1)[1],encoding='utf8')
tb='''`timescale 1ns/1ps
module tb;
reg c50=0,c49=0;always #10 c50=~c50;always #10.204081632653 c49=~c49;
reg rst_n=0,s50=0,s49=0,host=1;
reg [7:0] d50=0,d49=0,host_expected=0;
reg host_good=0;
wire txold,txnew,tx49,bo,bn,b49,lv,le,hv,he;
wire [7:0] ld,hd;
old_uart_tx_115200 old50(.clk(c50),.start(s50),.data(d50),.tx(txold),.busy(bo));
uart_tx_115200 new50(.clk(c50),.start(s50),.data(d50),.tx(txnew),.busy(bn));
uart_tx_115200 #(.BIT_TICKS(425)) new49(.clk(c49),.start(s49),.data(d49),.tx(tx49),.busy(b49));
xy_pi_uart_rx #(.BIT_TICKS(425)) loop_rx(.clk(c49),.rst_n(rst_n),.rx(tx49),.valid(lv),.error(le),.data(ld));
xy_pi_uart_rx #(.BIT_TICKS(425)) host_rx(.clk(c49),.rst_n(rst_n),.rx(host),.valid(hv),.error(he),.data(hd));
integer loop_count=0,host_count=0,host_errors=0,tx50_count=0,tx49_count=0,bit_widths=0;
reg edge_seen=0;real last_edge,delta;
always @(negedge c50)begin
 #0.001;
 if({old50.tx,old50.busy,old50.baud,old50.bit_index,old50.shift}!=={new50.tx,new50.busy,new50.baud,new50.bit_index,new50.shift})
  $fatal(1,"default50 actual UART TX cycle/state mismatch");
end
always @(posedge c49)begin
 #0.001;
 if(rst_n && lv)begin if(ld!==d49)$fatal(1,"49MHz loopback byte mismatch");loop_count=loop_count+1;end
 if(rst_n && le)$fatal(1,"49MHz loopback error");
 if(rst_n && hv)begin
  if(!host_good || hd!==host_expected)$fatal(1,"49MHz nominal-host RX accepted wrong/bad-stop byte");
  host_count=host_count+1;
 end
 if(rst_n && he)begin if(host_good)$fatal(1,"nominal-host good frame rejected");host_errors=host_errors+1;end
end
always @(tx49)begin
 #0.001;
 if(d49==8'h55 && b49)begin
  if(edge_seen)begin
   delta=$realtime-last_edge;
   if(delta<8650.0 || delta>8700.0)$fatal(1,"49MHz TX wrong physical bit width=%0.6f",delta);
   bit_widths=bit_widths+1;
  end
  last_edge=$realtime;edge_seen=1;
 end else edge_seen=0;
end
task nominal_host_frame;
 input [7:0] b;input good;integer k;
 begin
  host_expected=b;host_good=good;
  host=0;#8680.555555556;
  for(k=0;k<8;k=k+1)begin host=b[k];#8680.555555556;end
  host=good;#8680.555555556;
  host=1;#26041.666666667;
 end
endtask
integer a,b,c;
initial begin
 #200;rst_n=1;
 fork
  begin
   for(a=0;a<256;a=a+1)begin
    @(negedge c50);d50=a;s50=1;
    @(negedge c50);s50=0;
    wait(bo);wait(!bo);repeat(3)@(negedge c50);tx50_count=tx50_count+1;
   end
  end
  begin
   for(b=0;b<256;b=b+1)begin
    @(negedge c49);d49=b;s49=1;
    @(negedge c49);s49=0;
    wait(b49);wait(!b49);repeat(5)@(negedge c49);tx49_count=tx49_count+1;
   end
  end
  begin
   // A quarter-bit false start must disappear before center qualification.
   #500;host=0;#2000;host=1;#26000;
   for(c=0;c<256;c=c+1)begin
    if(c%16==0)nominal_host_frame(c^8'h5a,0);
    nominal_host_frame(c,1);
   end
  end
 join
 #100000;
 if(tx50_count!=256 || tx49_count!=256 || loop_count!=256 || host_count!=256 || host_errors!=16 || bit_widths<9)
  $fatal(1,"UART coverage incomplete tx50=%0d tx49=%0d loop=%0d host=%0d errors=%0d bitWidths=%0d",tx50_count,tx49_count,loop_count,host_count,host_errors,bit_widths);
 $display("PASS actual UART sources: default50 cycle/state equivalence256 bytes;49MHz Tx/Rx256 loopback bytes; nominal115200 external host256 good/16 bad-stop frames plus false start; physical TX bit widths checked=%0d",bit_widths);
 $finish;
end
initial begin #80000000;$fatal(1,"UART unit timeout");end
endmodule
'''
(D/'tb.v').write_text(tb,encoding='utf8');tools=R.parents[1]/'.tools/iverilog/app/bin'
paths=[W/'core/spi_uart_modules.v',W/'telemetry_tx.v',B/'xy_pi_parameters.v',D/'old_tx.v',D/'tb.v',M/'SOURCE_BINDING.json',Path(__file__),tools/'iverilog.exe',tools/'vvp.exe']
inputs={str(p):sha(p) for p in paths}
(D/'inputs.json').write_text(json.dumps({'scope':'Actual UART TX/RX components and ideal49/50MHz clock models only. No full aircraft clock integration or hardware. Nominal-host bit periods are independently8680.555556ns; TX425 bit width must be8650..8700ns, so retaining434 at49MHz fails that check.',
    'input_sha256':inputs,'no_DUT_force_or_preload':True,'default50_TX_bytes':256,'clock49_loopback_bytes':256,'external_host_good_frames':256,'external_host_bad_stop_frames':16},indent=2)+'\n',encoding='utf8')
env=dict(os.environ,TMP=str(T),TEMP=str(T),TMPDIR=str(T));exits=[]
commands=[('compile',[str(tools/'iverilog.exe'),'-g2012','-s','tb','-o',str(D/'test.vvp'),str(D/'tb.v'),str(D/'old_tx.v'),str(W/'core/spi_uart_modules.v'),str(B/'xy_pi_parameters.v')]),('vvp',[str(tools/'vvp.exe'),str(D/'test.vvp')])]
for name,command in commands:
    record={'command':command,'started_utc':utc()}
    with (D/(name+'.log')).open('wb') as log:
        p=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL,env=env,creationflags=subprocess.CREATE_NO_WINDOW)
        record['pid']=p.pid;code=p.wait()
    record.update(actual_p_wait=code,normal_wait_return=True,ended_utc=utc(),log_sha256=sha(D/(name+'.log')))
    (D/(name+'_exit.json')).write_text(json.dumps(record,indent=2)+'\n',encoding='utf8');exits.append(code)
    if code!=0:print(json.dumps({'passed':False,'stage':name,'actual_wait':code,'log':str(D/(name+'.log'))}));raise SystemExit(code)
assert {str(p):sha(p) for p in map(Path,inputs)}==inputs
assert 'PASS actual UART sources' in (D/'vvp.log').read_text(encoding='utf8')
(D/'RESULT.json').write_text(json.dumps({'passed':True,'scope':'UART component proof only. The complete49MHz flight controller is not integrated or qualified.',
    'actual_waits':exits,'inputs_sha256':sha(D/'inputs.json'),'vvp_log_sha256':sha(D/'vvp.log')},indent=2)+'\n',encoding='utf8')
print(json.dumps({'UART_components_passed':True,'actual_waits':exits,'default50_and_actual49_divisors_verified':True,'whole_firmware_or_hardware_qualified':False}))
