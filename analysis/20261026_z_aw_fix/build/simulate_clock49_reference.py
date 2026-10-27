"""Simulate unmodified generated PLLA/init RTL with the installed manufacturer primitive model."""
from pathlib import Path
import datetime,hashlib,json,os,subprocess
R=Path(__file__).resolve().parents[3];M=Path(__file__).resolve().parent/'clock49_generate';S=M/'vendor_generated_reference';D=M/'simulation'
B=R.parents[1]/'.tools/iverilog/app/bin';PRIM=Path('C:/Gowin/Gowin_V1.9.12.04_x64/IDE/simlib/gw5a/prim_sim.v')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
utc=lambda:datetime.datetime.now(datetime.timezone.utc).isoformat()
assert not D.exists();D.mkdir();T=D/'tmp';T.mkdir()
manifest=json.loads((M/'REFERENCE_IP_MANIFEST.json').read_text(encoding='utf8'))
assert all(sha(S/name)==item['sha256'] for name,item in manifest['files'].items())
tb='''`timescale 1ns/1ps
module tb;
reg input50=0;
always #10 input50=~input50;
wire output49,locked;
clock49 dut(.clkin(input50),.mdclk(input50),.clkout0(output49),.lock(locked));
real start_ns,previous_ns,period_ns,elapsed_ns;
integer n;
initial begin
 wait(locked===1'b1);
 repeat(100) @(posedge output49);
 @(posedge output49);start_ns=$realtime;previous_ns=$realtime;
 for(n=0;n<49000;n=n+1)begin
  @(posedge output49);
  if(locked!==1'b1)$fatal(1,"generated PLL lost lock during measurement");
  period_ns=$realtime-previous_ns;previous_ns=$realtime;
  if(period_ns<20.390 || period_ns>20.430)$fatal(1,"unexpected49MHz model period=%0.6f",period_ns);
 end
 elapsed_ns=$realtime-start_ns;
 if(elapsed_ns<999980.0 || elapsed_ns>1000020.0)$fatal(1,"49000 periods must span1ms; elapsed=%0.6f",elapsed_ns);
 $display("PASS unmodified vendor PLLA+PLL_INIT model, natural50MHz input, lock held,49000 output periods elapsed_ns=%0.6f",elapsed_ns);
 $finish;
end
initial begin #10000000;$fatal(1,"PLL model did not lock/complete within10ms");end
endmodule
'''
(D/'tb.v').write_text(tb,encoding='utf8')
inputs={str(p):sha(p) for p in [S/'clock49.v',S/'clock49_mod.v',S/'pll_init.v',PRIM,D/'tb.v',B/'iverilog.exe',B/'vvp.exe',Path(__file__)]}
(D/'inputs.json').write_text(json.dumps({'scope':'Isolated generated IP/model simulation only; not a flight-controller or physical/hardware qualification. No DUT force/preload, no SIM define, unmodified vendor sources.',
    'input_sha256':inputs,'manufacturer_reference_manifest_sha256':sha(M/'REFERENCE_IP_MANIFEST.json')},indent=2)+'\n',encoding='utf8')
env=dict(os.environ,TMP=str(T),TEMP=str(T),TMPDIR=str(T))
commands=[('compile',[str(B/'iverilog.exe'),'-g2012','-s','tb','-o',str(D/'clock49.vvp'),str(D/'tb.v'),str(S/'clock49.v'),str(S/'clock49_mod.v'),str(S/'pll_init.v'),str(PRIM)]),
          ('vvp',[str(B/'vvp.exe'),str(D/'clock49.vvp')])]
exits=[]
for name,command in commands:
    record={'command':command,'started_utc':utc()}
    with (D/(name+'.log')).open('wb') as log:
        p=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL,env=env,creationflags=subprocess.CREATE_NO_WINDOW)
        record['pid']=p.pid;code=p.wait()
    record.update(ended_utc=utc(),actual_p_wait=code,normal_wait_return=True,log_sha256=sha(D/(name+'.log')))
    (D/(name+'_exit.json')).write_text(json.dumps(record,indent=2)+'\n',encoding='utf8');exits.append(code)
    if code!=0:
        print(json.dumps({'isolated_clock_model_passed':False,'failed_stage':name,'actual_wait':code,'log':str(D/(name+'.log'))}));raise SystemExit(code)
assert {str(p):sha(p) for p in map(Path,inputs)}==inputs
assert 'PASS unmodified vendor PLLA+PLL_INIT model' in (D/'vvp.log').read_text(encoding='utf8',errors='replace')
(D/'RESULT.json').write_text(json.dumps({'passed':True,'scope':'Isolated unmodified vendor49MHz PLLA model only. No FPGA synthesis/route, flight-controller tests or hardware action.',
    'actual_waits':exits,'inputs_sha256':sha(D/'inputs.json'),'compile_exit_sha256':sha(D/'compile_exit.json'),'vvp_exit_sha256':sha(D/'vvp_exit.json'),
    'vvp_log_sha256':sha(D/'vvp.log')},indent=2)+'\n',encoding='utf8')
print(json.dumps({'isolated_clock_model_passed':True,'actual_waits':exits,'source_or_hardware_changed':False}))
