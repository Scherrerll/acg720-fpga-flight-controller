from pathlib import Path
import re,os,subprocess,hashlib,json,time
D=Path(__file__).resolve().parent; R=D.parent.parent; F=R/'fixture'
sources=[F/n for n in re.findall(r'<File path="([^"]+\.v)"',(F/'acg720_ano_port.gprj').read_text())]
hashes={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}
nav=(D/'mtf_xyz_navigation_control.proposed.v').read_text().replace('module mtf_xyz_navigation_control #','module navigation_proposed #')
top=(D/'acg720_ano_port.proposed.v').read_text().split('endmodule',1)[0]+'endmodule\n'
top=top.replace('module acg720_ano_port(','module top_proposed(').replace('mtf_xyz_navigation_control #','navigation_proposed #')
(D/'full_proposed.v').write_text(top+'\n'+nav)
bench='''module tb;
reg clk=0;always #10 clk=~clk;
wire txa,txb;
acg720_ano_port a(.clk50(clk),.imu_miso(1'b0),.rc_ppm_in(1'b0),.range_rx(1'b1),.uart_tx(txa));
top_proposed b(.clk50(clk),.imu_miso(1'b0),.rc_ppm_in(1'b0),.range_rx(1'b1),.uart_tx(txb));
// Only the frame PERIOD is accelerated. Actual UART RTL/433-clock baud is unchanged.
defparam a.telemetry.PERIOD=512;
defparam b.telemetry.PERIOD=512;
reg [719:0] live_payload=0;
reg origin_event=0;
reg [31:0] rng=32'h86c95afe;
integer cycle=0,bytes=0,j,held_changes=0,origin_events=0,frames=0,trace;
reg previous_hold=0;
initial begin
 trace=$fopen("full_top_acceptance.log","w");
 force a.native_navigation.diagnostic_next=live_payload;
 force b.native_navigation.diagnostic_next=live_payload;
 force a.observer_reset=origin_event;
 force b.observer_reset=origin_event;
end
always @(negedge clk)begin
 if(cycle%997==0)begin
  for(j=0;j<23;j=j+1)begin
   rng=rng^(rng<<13);rng=rng^(rng>>17);rng=rng^(rng<<5);
   live_payload={live_payload[687:0],rng};
  end
  if(a.telemetry_snapshot_hold)held_changes=held_changes+1;
 end
 origin_event=(cycle%12347<7);
 if(cycle%12347==0)origin_events=origin_events+1;
end
always @(posedge clk)begin
 cycle=cycle+1;
 if(a.telemetry.start!==b.telemetry.start || a.telemetry.busy!==b.telemetry.busy)
  $fatal(1,"UART acceptance control mismatch at %0d",cycle);
 if(a.telemetry.start && !a.telemetry.busy)begin
  if(a.telemetry.data!==b.telemetry.data)$fatal(1,"byte mismatch");
  $fwrite(trace,"%0d %0d %02x\\n",cycle,bytes,a.telemetry.data);
  bytes=bytes+1;
 end
 #1;
 if(txa!==txb || a.radio_tx!==b.radio_tx)$fatal(1,"wire mismatch");
 if(a.rst_n!==b.rst_n || a.telemetry_snapshot_hold!==b.telemetry_snapshot_hold)$fatal(1,"hold/reset mismatch");
 if(a.navigation_body!==b.navigation_body || a.native_navigation.diagnostic_q!==b.native_navigation.diagnostic_q)
  $fatal(1,"diagnostic snapshot mismatch at %0d",cycle);
 if(a.telemetry.snapshot_sequence!==b.telemetry.snapshot_sequence || a.telemetry.snapshot_begin!==b.telemetry.snapshot_begin)
  $fatal(1,"sequence/start mismatch");
 if(previous_hold && !a.telemetry_snapshot_hold)frames=frames+1;
 previous_hold=a.telemetry_snapshot_hold;
 if(frames==2)begin
  if(bytes!=1136 || held_changes<2 || origin_events<2)$fatal(1,"insufficient coverage");
  $display("PASS actual dual top: cycles=%0d bytes=%0d frames=%0d held_changes=%0d origin_events=%0d",cycle,bytes,frames,held_changes,origin_events);
  $fclose(trace);$finish;
 end
 if(cycle>6000000)$fatal(1,"full top timeout");
end
endmodule
'''
(D/'full_top_tb.v').write_text(bench)
ws=next(p for p in R.parents if (p/'.tools/iverilog/app/bin/iverilog.exe').is_file())
iv=ws/'.tools/iverilog/app/bin/iverilog.exe'
env=dict(os.environ,PATH=str(iv.parent)+os.pathsep+os.environ['PATH'],TMP=str(D),TEMP=str(D),TMPDIR=str(D))
commands=[[str(iv),'-g2012','-I',str(F),'-s','tb','-o',str(D/'full_top.vvp'),*map(str,sources),str(D/'full_proposed.v'),str(D/'full_top_tb.v')],[str(iv.with_name('vvp.exe')),str(D/'full_top.vvp')]]
logs=[]; start=time.time()
for i,cmd in enumerate(commands):
 p=subprocess.run(cmd,capture_output=True,text=True,cwd=D,env=env,timeout=1200)
 logs.append(p.stdout+p.stderr);(D/f'full_top_{i}.log').write_text(logs[-1])
 if p.returncode:raise RuntimeError(logs[-1])
assert hashes=={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}
report={'passed':True,'seconds':time.time()-start,'result':logs[-1],'source_sha256':hashes,'commands':commands,'scope':'Actual dual full top and all actual RTL dependencies. Frame PERIOD512 override on both sides; unchanged actual UART433 baud. Input pins constant. diagnostic_next forced identically to changing720bit payload; observer_reset forced identically to periodic origin events. Snapshot bank/output/UART/hold unforced. Physical INIT and default production PERIOD not verified by this simulation.'}
(D/'full_top.proof.json').write_text(json.dumps(report,indent=2));print(logs[-1],flush=True)
