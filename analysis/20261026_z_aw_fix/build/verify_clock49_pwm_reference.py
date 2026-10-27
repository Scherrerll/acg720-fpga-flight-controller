"""Measure actual RTL PWM wall-time at50/49MHz, including two stop/re-enable boundaries."""
from pathlib import Path
import datetime,hashlib,json,os,subprocess
R=Path(__file__).resolve().parents[3];O=Path(__file__).resolve().parent;M=O/'clock49_pwm';D=M/'proofs'
source=R/'out/z_aw_fix_20261026/compact_aw_v4/canonical/source/core/motor_pwm.v'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
utc=lambda:datetime.datetime.now(datetime.timezone.utc).isoformat()
assert not M.exists();D.mkdir(parents=True);T=D/'tmp';T.mkdir()
expected=json.loads((O/'v4_release_proofs/RESULT.json').read_text(encoding='utf8'))['source55']['core/motor_pwm.v'];assert sha(source)==expected
tb='''`timescale 1ns/1ps
module pulse_monitor #(parameter ID=0)(input pulse,rst_n,enabled,active,input [15:0] latched);
real start_ns,last_start,expected_ns,stop_elapsed,width_ns,expected_stop;
integer pulses=0,stops=0;reg seen=0,stopped=0;
always @(posedge pulse)begin
 start_ns=$realtime;
 if(seen && rst_n && (start_ns-last_start<2499940.0 || start_ns-last_start>2500060.0))
  $fatal(1,"PWM%0d restarted or wrong frame period=%0.6f",ID,start_ns-last_start);
 seen=1;last_start=start_ns;stopped=0;
 #0.001;expected_ns=active ? latched*1000.0:1000000.0;
end
always @(negedge enabled)if(pulse && seen)begin
 stopped=1;stop_elapsed=$realtime-start_ns;
 expected_stop=stop_elapsed<1000000.0 ? 1000000.0:stop_elapsed;
end
always @(negedge pulse)if(rst_n && seen)begin
 width_ns=$realtime-start_ns;
 if(stopped)begin
  if(width_ns<expected_stop-60.0 || width_ns>expected_stop+60.0)
   $fatal(1,"PWM%0d stop/re-enable failed width=%0.6f expected=%0.6f",ID,width_ns,expected_stop);
  stops=stops+1;
 end else if(width_ns<expected_ns-60.0 || width_ns>expected_ns+60.0)
  $fatal(1,"PWM%0d physical pulse width=%0.6f expected=%0.6f",ID,width_ns,expected_ns);
 pulses=pulses+1;
end
endmodule
module tb;
reg c50=0,c49=0;
always #10 c50=~c50;
always #10.204081632653 c49=~c49;
reg rst_n=0,en=0;
reg [15:0] m1=1000,m2=1200,m3=1500,m4=1850;
wire [3:0] p50,p49;wire a50,a49;
wire [15:0] l50a,l50b,l50c,l50d,l49a,l49b,l49c,l49d;
motor_pwm #(.TICKS_PER_US(50),.FRAME_US(2500),.MAX_US(2000),.EXTERNAL_TICKS(1)) old50(
 .clk(c50),.rst_n(rst_n),.enabled(en),.m1_us(m1),.m2_us(m2),.m3_us(m3),.m4_us(m4),
 .pre_ticks1(m1*32'd50),.pre_ticks2(m2*32'd50),.pre_ticks3(m3*32'd50),.pre_ticks4(m4*32'd50),
 .motor1_pwm(p50[0]),.motor2_pwm(p50[1]),.motor3_pwm(p50[2]),.motor4_pwm(p50[3]),.frame_active(a50),
 .frame_latched1_us(l50a),.frame_latched2_us(l50b),.frame_latched3_us(l50c),.frame_latched4_us(l50d));
motor_pwm #(.TICKS_PER_US(49),.FRAME_US(2500),.MAX_US(2000),.EXTERNAL_TICKS(1)) new49(
 .clk(c49),.rst_n(rst_n),.enabled(en),.m1_us(m1),.m2_us(m2),.m3_us(m3),.m4_us(m4),
 .pre_ticks1(m1*32'd49),.pre_ticks2(m2*32'd49),.pre_ticks3(m3*32'd49),.pre_ticks4(m4*32'd49),
 .motor1_pwm(p49[0]),.motor2_pwm(p49[1]),.motor3_pwm(p49[2]),.motor4_pwm(p49[3]),.frame_active(a49),
 .frame_latched1_us(l49a),.frame_latched2_us(l49b),.frame_latched3_us(l49c),.frame_latched4_us(l49d));
pulse_monitor #(0) a(p50[0],rst_n,en,a50,l50a);
pulse_monitor #(1) b(p50[1],rst_n,en,a50,l50b);
pulse_monitor #(2) c(p50[2],rst_n,en,a50,l50c);
pulse_monitor #(3) d(p50[3],rst_n,en,a50,l50d);
pulse_monitor #(4) e(p49[0],rst_n,en,a49,l49a);
pulse_monitor #(5) f(p49[1],rst_n,en,a49,l49b);
pulse_monitor #(6) g(p49[2],rst_n,en,a49,l49c);
pulse_monitor #(7) h(p49[3],rst_n,en,a49,l49d);
initial begin
 #200;rst_n=1;
 #1999800;en=1;
 #4000000;m1=2000;m2=1850;m3=1200;m4=1000;
 #8000000;m1=1850;m2=1850;m3=1850;m4=1850;
 #6400000;en=0;
 #50000;en=1;
 #5750000;en=0;
 #50000;en=1;
 #6000000;
 if(a.pulses<12 || b.pulses<12 || c.pulses<12 || d.pulses<12 || e.pulses<12 || f.pulses<12 || g.pulses<12 || h.pulses<12)
  $fatal(1,"Too few measured physical pulses");
 if(a.stops!=2 || b.stops!=2 || c.stops!=2 || d.stops!=2 || e.stops!=2 || f.stops!=2 || g.stops!=2 || h.stops!=2)
  $fatal(1,"Stop boundary was not exercised on every channel");
 $display("PASS actual motor_pwm RTL:50/49MHz physical1000/1200/1500/1850/2000us pulses,2500us frames, all8 monitors, two stop/re-enable boundaries each; width tolerance60ns");
 $finish;
end
initial begin #40000000;$fatal(1,"PWM timebase test timeout");end
endmodule
'''
(D/'tb.v').write_text(tb,encoding='utf8');B=R.parents[1]/'.tools/iverilog/app/bin'
inputs={str(p):sha(p) for p in [source,D/'tb.v',Path(__file__),B/'iverilog.exe',B/'vvp.exe']}
(D/'inputs.json').write_text(json.dumps({'scope':'Unmodified parameterized PWM RTL component, input clocks50/49MHz behavioral models. Separate vendor PLL model already checked49MHz clock generation. No DUT force/preload. Not integrated49MHz firmware or hardware qualification.',
    'input_sha256':inputs,'clock49_half_period_ns':10.204081632653,'wall_time_tolerance_ns':60},indent=2)+'\n',encoding='utf8')
env=dict(os.environ,TMP=str(T),TEMP=str(T),TMPDIR=str(T));exits=[]
for name,command in [('compile',[str(B/'iverilog.exe'),'-g2012','-s','tb','-o',str(D/'test.vvp'),str(D/'tb.v'),str(source)]),('vvp',[str(B/'vvp.exe'),str(D/'test.vvp')])]:
    record={'command':command,'started_utc':utc()}
    with (D/(name+'.log')).open('wb') as log:
        p=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL,env=env,creationflags=subprocess.CREATE_NO_WINDOW)
        record['pid']=p.pid;code=p.wait()
    record.update(actual_p_wait=code,normal_wait_return=True,ended_utc=utc(),log_sha256=sha(D/(name+'.log')))
    (D/(name+'_exit.json')).write_text(json.dumps(record,indent=2)+'\n',encoding='utf8');exits.append(code)
    if code!=0:print(json.dumps({'passed':False,'stage':name,'actual_wait':code,'log':str(D/(name+'.log'))}));raise SystemExit(code)
assert {str(p):sha(p) for p in map(Path,inputs)}==inputs
assert 'PASS actual motor_pwm RTL' in (D/'vvp.log').read_text(encoding='utf8')
(D/'RESULT.json').write_text(json.dumps({'passed':True,'scope':'PWM component proof only; whole49MHz firmware remains incomplete and unqualified.',
    'actual_waits':exits,'inputs_sha256':sha(D/'inputs.json'),'vvp_log_sha256':sha(D/'vvp.log'),
    'all_eight_channel_monitors_passed':True,'stop_boundaries_per_channel':2},indent=2)+'\n',encoding='utf8')
print(json.dumps({'PWM_component_passed':True,'actual_waits':exits,'all_eight_monitors':True,'whole_firmware_or_hardware_qualified':False}))
