"""Read frozen B3/P2, derive force projection, and check the actual mixer only.

No plant/ESC identification, no aircraft simulation, no HTTP/serial/hardware.
The force table follows the Euler rotation derivation in TILT_FINDINGS.md;
it is not a claim that PWM is proportional to thrust.
"""
from pathlib import Path
import csv
import hashlib
import json
import math
import os
import subprocess

OUT=Path(__file__).resolve().parent
REPO=OUT.parents[2]
S=REPO/'firmware/B0B3/source'
P2=Path('C:/Users/ScherrerL/Desktop/apple/handoff_xy_pi_runtime_20261026/workspace_snapshot/reference_ano/quadrotor_tm_v1_20261012/Quadrotor_TM_V1')
BIN=Path('C:/Users/ScherrerL/Desktop/apple/.tools/iverilog/app/bin')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

CASES=[(1658,0,0,0),(1658,0,100,0),(1658,0,300,0),(1658,0,400,0),
       (1850,0,150,0),(1850,0,300,0),(1350,0,300,0),(1850,200,200,100)]

def mixer(t,r,p,y):
    raw=[t+r+p-y,t+p-r+y,t-r-p-y,t+r-p+y]
    bounded=[max(1200,min(2000,v))for v in raw]
    return dict(collective_us=t,roll_us=r,pitch_us=p,yaw_us=y,
       **{'raw_m'+str(k+1):v for k,v in enumerate(raw)},
       **{'m'+str(k+1):v for k,v in enumerate(bounded)},
       mean_pwm_us=sum(bounded)/4,mean_pwm_minus_collective_us=sum(bounded)/4-t,
       strict_clip_flag=any(v<1200 or v>2000 for v in raw),
       touches_limit=any(v<=1200 or v>=2000 for v in raw),
       min_upper_headroom_us=min(2000-v for v in raw),min_lower_headroom_us=min(v-1200 for v in raw))

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    files=[S/n for n in ('acg720_ano_port.v','mtf_xyz_navigation_control.v','core/flight_core.v',
        'core/rtl/quad_mixer_feedback.v','core/rtl/ano_rate_control.v','position/mtf_xyz_hold_control.v',
        'position/mtf_shared_height_fusion.v','position/ano_z_stick.v','sensor/mtf_shared_geometry.v','core/height_loss_fallback.v')]
    files+=[P2/n for n in ('SRC/fc_specific/Ano_AltCtrl.c','SRC/fc_specific/Ano_MotorCtrl.c',
        'SRC/fc_specific/Ano_FlightDataCal.c','SRC/fc_specific/config.h','Application/Ano_Scheduler.c')]
    before={str(p):dict(sha256=sha(p),bytes=p.stat().st_size)for p in files}
    projection=[]
    for roll,pitch in ((0,0),(0,5),(0,10),(0,15),(5,5),(10,10),(15,15)):
        factor=math.cos(math.radians(roll))*math.cos(math.radians(pitch))
        projection.append(dict(actual_roll_deg=roll,actual_pitch_deg=pitch,
            vertical_force_fraction_at_fixed_total_thrust=factor,
            force_deficit_percent=(1-factor)*100,required_total_thrust_ratio=1/factor,
            required_total_thrust_increase_percent=(1/factor-1)*100,
            fixed_slant_1000mm_vertical_height_mm=1000*factor,
            fixed_true_vertical_1000mm_required_slant_mm=1000/factor,
            ideal_uncompensated_initial_az_mps2=9.80665*(factor-1)))
    model=[mixer(*case)for case in CASES]
    for name,rows in (('force_geometry_reference.csv',projection),('mixer_reference.csv',model)):
        with(OUT/name).open('w',encoding='utf-8-sig',newline='')as f:
            w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    lines=['`timescale 1ns/1ps','module tb;',
        'reg enabled=1;reg[15:0]t=1000;reg signed[15:0]r=0,p=0,y=0;',
        'wire[15:0]a,b,c,d;wire sat;wire[2:0]pos,neg;',
        'quad_mixer_feedback #(.MIN_US(1200),.MAX_US(2000))dut(.enabled(enabled),.throttle_us(t),.roll_us(r),.pitch_us(p),.yaw_us(y),.m1_us(a),.m2_us(b),.m3_us(c),.m4_us(d),.saturated(sat),.saturation_positive(pos),.saturation_negative(neg));',
        'initial begin']
    for index,row in enumerate(model):
        lines.append(f't={row["collective_us"]};r={row["roll_us"]};p={row["pitch_us"]};y={row["yaw_us"]};#10;')
        lines.append(f'if(a!={row["m1"]} || b!={row["m2"]} || c!={row["m3"]} || d!={row["m4"]} || sat!={int(row["strict_clip_flag"])})$fatal(1,"mixer case{index} mismatch");')
        if index==4:lines.append('if(!pos[1] || sat)$fatal(1,"limit-touch must flag directional saturation before strict clip");')
        lines.append(f'$display("PASS mixer case{index}: t=%0d r=%0d p=%0d y=%0d motors=%0d,%0d,%0d,%0d sat=%0d pos=%0d neg=%0d",t,r,p,y,a,b,c,d,sat,pos,neg);')
    lines+=['enabled=0;#10;if({a,b,c,d}!={16\'d1000,16\'d1000,16\'d1000,16\'d1000} || sat || pos || neg)$fatal(1,"disabled outputs");',
            '$display("PASS disabled mixer outputs1000, feedback0");$finish;end','endmodule']
    tb=OUT/'mixer_tb.v';tb.write_text('\n'.join(lines)+'\n',encoding='utf8')
    tmp=OUT/'tmp';tmp.mkdir(exist_ok=True);vvp=tmp/'mixer.vvp'
    env=dict(os.environ,TMP=str(tmp),TEMP=str(tmp),TMPDIR=str(tmp))
    compile_args=[str(BIN/'iverilog.exe'),'-g2012','-s','tb','-o',str(vvp),str(tb),str(S/'core/rtl/quad_mixer_feedback.v')]
    compiled=subprocess.run(compile_args,cwd=OUT,env=env,capture_output=True,text=True)
    (OUT/'mixer_compile.log').write_text(compiled.stdout+compiled.stderr,encoding='utf8')
    assert compiled.returncode==0,compiled.stderr
    sim_args=[str(BIN/'vvp.exe'),str(vvp)]
    with(OUT/'mixer.log').open('w',encoding='utf8')as log:
        proc=subprocess.Popen(sim_args,cwd=OUT,env=env,stdout=log,stderr=subprocess.STDOUT,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        code=proc.wait(timeout=30)
    text=(OUT/'mixer.log').read_text(encoding='utf8');assert code==0,text
    assert before=={str(p):dict(sha256=sha(p),bytes=p.stat().st_size)for p in files}
    result=dict(passed=True,scope=__doc__,commands=[dict(command=compile_args,exit_code=compiled.returncode),
         dict(command=sim_args,pid=proc.pid,actual_wait_return=code)],
         source_inputs=before,source_inputs_unchanged=True,
         checks=[line for line in text.splitlines()if line.startswith('PASS')],
         generated={p.name:sha(p)for p in (tb,OUT/'force_geometry_reference.csv',OUT/'mixer_reference.csv',OUT/'mixer.log')})
    (OUT/'tilt_math_results.json').write_text(json.dumps(result,indent=2),encoding='utf8')
    print(json.dumps(dict(passed=True,compile_exit=compiled.returncode,actual_wait_return=code,checks=result['checks'],
         projection=projection,source_count=len(files)),indent=2))

if __name__=='__main__':main()
