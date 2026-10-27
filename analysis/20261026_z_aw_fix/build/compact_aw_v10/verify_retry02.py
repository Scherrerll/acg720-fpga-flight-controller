"""Execute exact extracted diagnostic RTL under its producer contract, then top13."""
from pathlib import Path
import datetime,hashlib,json,os,re,subprocess,sys
sys.dont_write_bytecode=True
O=Path(__file__).resolve().parent;R=O.parents[3];D=O/'proofs_retry02';assert D.is_dir() and not (D/'inputs.json').exists()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text())
OLD=R/'out/z_aw_fix_20261026/compact_aw_v9/canonical/source';NEW=R/'out/z_aw_fix_20261026/compact_aw_v10/canonical/source'
before={'v9':read(O.parent/'compact_aw_v9/source_freeze.json')['source55'],'v10':read(O/'source_freeze.json')['source55']}
for tag,s in [('v9',OLD),('v10',NEW)]:assert {p:sha(s/p) for p in before[tag]}==before[tag]
IV=R.parents[1]/'.tools/iverilog/app/bin/iverilog.exe';VVP=IV.with_name('vvp.exe');(D/'tmp').mkdir()
env=dict(os.environ,TMP=str(D/'tmp'),TEMP=str(D/'tmp'),TMPDIR=str(D/'tmp'))
stages=[]
def run(name,command):
    record={'command':command,'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()};log=D/(name+'.log')
    with log.open('wb') as output:
        p=subprocess.Popen(command,cwd=D,env=env,stdin=subprocess.DEVNULL,stdout=output,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
        record['pid']=p.pid;(D/(name+'_process.json')).write_text(json.dumps(record,indent=2)+'\n');code=p.wait()
    record.update(actual_p_wait=code,normal_wait_return=True,ended_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),log_sha256=sha(log))
    (D/(name+'_exit.json')).write_text(json.dumps(record,indent=2)+'\n');stages.append(record)
    print(name,'actual_wait',code,flush=True);assert code==0,log.read_text(errors='replace')
    return log.read_text(errors='replace')
decl='''`default_nettype none
module diag_@TAG@ #(parameter STARTUP_ONLY_DIAGNOSTIC_RESET=0)(input clk,rst_n,diagnostic_hold,
input [671:0] payload,input [15:0] shadow_flags,input [7:0] live,
output wire [719:0] diagnostic_body);
wire [63:0] uptime_ms=payload[63:0];
wire [31:0] navigation_sequence=payload[95:64],source_age_ms=payload[127:96],geometry_dt_us=payload[159:128],reasons=payload[191:160];
wire [31:0] height_mm=payload[223:192],bvx=payload[255:224],bvy=payload[287:256],wvx=payload[319:288],wvy=payload[351:320];
wire [30:0] fused_vx_q16=payload[382:352],fused_vy_q16=payload[413:383];
wire [31:0] fused_height=payload[445:414],fused_vz_q16=payload[477:446],position_x_q8=payload[509:478],position_y_q8=payload[541:510];
wire [15:0] controller_roll=payload[557:542],controller_pitch=payload[573:558],controller_delta=payload[589:574],controller_collective=payload[605:590];
wire [31:0] controller_target_height=payload[637:606];
wire [15:0] z_reason=payload[655:640];
wire signed [15:0] z_throttle_delta;wire [15:0] z_collective;
wire position_ready=live[0],live_velocity=live[1],height_ready=live[2],geometry_flow_ready=live[3],geometry_height_ready=live[4],module_fresh=live[5],mapping_verified=live[6],rotation_compensated=live[7];
wire z_active=shadow_flags[4];
'''
for tag,s in [('v9',OLD),('v10',NEW)]:
    text=(s/'mtf_xyz_navigation_control.v').read_text()
    assert "wire [15:0] shadow_flags={position_reason[9:0],xy_active,z_active,xy_requested," in text
    boundary=' wire [719:0] diagnostic_next='
    assert text.count(boundary)==1
    block=text[text.index(boundary):text.rindex('endmodule')]
    expressions=[]
    for pattern in [r' assign z_throttle_delta=.*?;',r' assign z_collective=.*?;',r' wire signed \[31:0\] z_target_height=.*?;']:
        matches=re.findall(pattern,text);assert len(matches)==1;expressions+=matches
    fixture=decl.replace('@TAG@',tag)+'\n'.join(expressions)+'\n'+block+'endmodule\n'
    (D/(tag+'_diag.v')).write_text(fixture)
tb=r'''`timescale 1ns/1ps
module tb;
reg clk=0;always #10 clk=~clk;
reg rst_n=0,hold=0;reg [671:0] data=0;reg [15:0] flags=0;reg [7:0] live=0;
wire [719:0] a0,b0,a1,b1;
diag_v9 #(.STARTUP_ONLY_DIAGNOSTIC_RESET(0)) a(.clk(clk),.rst_n(rst_n),.diagnostic_hold(hold),.payload(data),.shadow_flags(flags),.live(live),.diagnostic_body(a0));
diag_v10 #(.STARTUP_ONLY_DIAGNOSTIC_RESET(0)) b(.clk(clk),.rst_n(rst_n),.diagnostic_hold(hold),.payload(data),.shadow_flags(flags),.live(live),.diagnostic_body(b0));
diag_v9 #(.STARTUP_ONLY_DIAGNOSTIC_RESET(1)) c(.clk(clk),.rst_n(rst_n),.diagnostic_hold(hold),.payload(data),.shadow_flags(flags),.live(live),.diagnostic_body(a1));
diag_v10 #(.STARTUP_ONLY_DIAGNOSTIC_RESET(1)) d(.clk(clk),.rst_n(rst_n),.diagnostic_hold(hold),.payload(data),.shadow_flags(flags),.live(live),.diagnostic_body(b1));
integer cycles=0,active=0,inactive=0,unknown=0,held=0,resets=0,n,j;
reg [719:0] previous0,previous1;
task compare;begin
 if(a0!==b0 || a1!==b1)$fatal(1,"diagnostic mismatch cycle%0d flag=%h hold=%b rst=%b",cycles,flags,hold,rst_n);
end endtask
always @(posedge clk)begin
 cycles=cycles+1;
 if(rst_n===1 && hold===0)begin
  if(flags[4]===1)active=active+1;else if(flags[4]===0)inactive=inactive+1;else unknown=unknown+1;
 end
 if(hold===1)held=held+1;if(rst_n===0)resets=resets+1;
 #1;compare;
end
initial begin
 #1;compare;
 for(n=0;n<160000;n=n+1)begin
  @(negedge clk);previous0=a0;previous1=a1;
  for(j=0;j<21;j=j+1)data[j*32+:32]=$random;
  live=$random;flags=$random;
  case(n%4)0:flags[4]=0;1:flags[4]=1;2:flags[4]=1'bx;3:flags[4]=1'bz;endcase
  case(n%13)0:flags[5]=1'bx;1:flags[5]=1'bz;endcase
  if(n%17==0)data[589:574]=16'hxxxx;
  if(n%23==0)data[605:590]=16'hzzzz;
  if(n%19==0)data[637:606]=32'hzzzzzzzz;
  rst_n=n%211<3 ?1'b0:1'b1;hold=n%7==0;
  if(n%97==0)hold=1'bx;
  if(n%101==0)rst_n=1'bx;
  #1;compare;
  if(a0!==previous0 || a1!==previous1)$fatal(1,"current input leaked through held snapshot");
 end
 @(negedge clk);
 if(active<10000 || inactive<10000 || unknown<20000 || held<10000 || resets<1000)$fatal(1,"coverage insufficient");
 $display("PASS diagnostic cycles=%0d public_bits_per_mode=720 modes=2 active=%0d inactive=%0d unknown=%0d held=%0d reset=%0d",cycles,active,inactive,unknown,held,resets);$finish;
end
endmodule
'''
(D/'tb.v').write_text(tb)
(D/'inputs.json').write_text(json.dumps({'source55':before,'driver_sha256':sha(Path(__file__)),
    'extracted_sources':{p.name:sha(p) for p in [D/'v9_diag.v',D/'v10_diag.v']},'tb_sha256':sha(D/'tb.v'),
    'contract':'shadow_flags[4] is same-cycle z_active in actual source. Exact whole diagnostic_next/reg/body blocks are executed; no private force.'},indent=2)+'\n')
run('diagnostic_compile',[str(IV),'-g2012','-Wall','-s','tb','-o',str(D/'diagnostic.vvp'),str(D/'tb.v'),str(D/'v9_diag.v'),str(D/'v10_diag.v')])
log=run('diagnostic_simulation',[str(VVP),str(D/'diagnostic.vvp')]);assert 'PASS diagnostic ' in log
fixture=R/'analysis/20261026_z_aw_fix/aw_storage_integration/verify_top_safety.py'
text=fixture.read_text().replace('compact_aw_v7/canonical','compact_aw_v10/canonical')
text=text.replace('REPO=Path(__file__).resolve().parents[3]',f'REPO=Path({str(R)!r})')
text=text.replace('O=Path(__file__).resolve().parent;O.mkdir(exist_ok=True);',"O=Path(__file__).resolve().parent/'top';O.mkdir(exist_ok=False);")
(D/'verify_top.py').write_text(text);run('top13',[sys.executable,'-B',str(D/'verify_top.py')])
for tag,s in [('v9',OLD),('v10',NEW)]:assert {p:sha(s/p) for p in before[tag]}==before[tag]
v9proof=O.parent/'compact_aw_v9/proofs_retry02/results.json';v9exit=O.parent/'compact_aw_v9/proofs_retry02/runner_exit.json'
assert read(v9proof)['passed'] and read(v9exit)['actual_p_wait']==0
unchanged=[p for p in before['v9'] if before['v9'][p]==before['v10'][p]];assert len(unchanged)==54
(D/'results.json').write_text(json.dumps({'passed':True,'source55':before['v10'],'source55_unchanged':True,'diagnostic':log,
    'top13':read(D/'top/top_safety_results.json'),'stages':stages,'unchanged_files':unchanged,
    'reused_v9_control_and_v8_guard_proofs':{'v9_results_sha256':sha(v9proof),'v9_exit_sha256':sha(v9exit),
        'reason':'Controller six dependencies, producer, height fusion and arithmetic services unchanged; only diagnostic packing changed.'},
    'scope_limit':'Extracted actual diagnostic block under exact source contract plus full top safety. No new plant/flight or physical qualification.'},indent=2)+'\n')
print('PASS v10 diagnostic equivalence and actual top13',flush=True)
