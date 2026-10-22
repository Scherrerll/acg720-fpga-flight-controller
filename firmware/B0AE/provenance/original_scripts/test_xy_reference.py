from test_tools import *
rows=[]
def span(ms,arm=1,thr=1500,c1=1500,c2=1500,flow=1,vx=0,vy=0):
 rows.extend([(arm,c1,c2,thr,flow,23.4,vx,vy,350)]*ms)
span(100,0,1000);span(1400,thr=1000);span(200,thr=1555)
span(300,c1=2000,c2=2000,vx=3.5,vy=-2.2)
span(304,c1=1000,c2=1800,vx=-30,vy=15)
span(200,flow=0,c1=1700,c2=1300,vx=-15,vy=10)
span(300,vx=30,vy=-25);span(300);span(100,0,1000)
trace=ROOT/'tests/xy_inputs.txt';trace.write_text('\n'.join(' '.join(map(str,r))for r in rows)+'\n')
p=subprocess.run([str(ROOT/'tests/reference_oracle.exe'),'xy'],input=trace.read_text(),capture_output=True,text=True,check=True)
ref=[l.split()for l in p.stdout.splitlines()];(ROOT/'tests/xy_reference.txt').write_text(p.stdout)
(ROOT/'tests/xy_rtl_inputs.txt').write_text('\n'.join(f'{r[0]} {r[1]} {r[2]} {r[3]} {c[2]} {2000 if r[4] else 1000} {round(r[6]*10)} {round(r[7]*10)}'for r,c in zip(rows,ref))+'\n')
s=(ROOT/'tests/height_reference.v').read_text()
s=s.replace('reg[15:0]c1=', 'reg signed[31:0] env_vx=0,env_vy=0,fake_x=0;\nreg[15:0]c1=')
s=s.replace(".x_q8(32'sd0),.y_q8(32'sd0),.vx(32'sd0),.vy(32'sd0)",".x_q8(fake_x),.y_q8(-fake_x),.vx(env_vx),.vy(env_vy)")
s=s.replace('integer f,g,rv,a,b,c,d,t,msidx=0,last_height_ms=0;', 'integer f,g,rv,a,b,c,d,t,mode,vx,vy,msidx=0,last_height_ms=0,last_position_ms=0;')
s=s.replace('dut.height_command_age==0 && dut.height_command_seen','dut.command_age==0 && dut.command_seen')
s=s.replace('$fwrite(g,"%d %d %d %d %d %d %d %d\\n",last_height_ms,coll,target,climb,dut.auto_phase,dut.bias_store,active,za);','$fwrite(g,"%d %d %d %d %d\\n",last_position_ms,rt,pt,active,za);')
s=s.replace('height_rtl_inputs.txt','xy_rtl_inputs.txt').replace('height_rtl.txt','xy_rtl.txt')
s=s.replace('"%d %d %d %d %d\\n",a,b,c,d,t','"%d %d %d %d %d %d %d %d\\n",a,b,c,d,t,mode,vx,vy').replace('if(rv==5)','if(rv==8)')
s=s.replace('c7=(msidx>=2100 && msidx<2700)?1000:2000;', 'c7=mode;env_vx=vx*65536;env_vy=vy*65536;fake_x=msidx*2560;')
s=s.replace('if(hu)last_height_ms=msidx;', 'if(hu)last_height_ms=msidx;if(pu)last_position_ms=msidx;')
# The C scheduler cannot switch modes in the middle of Loc_1level_Ctrl.
# The compressed simulator uses2000clocks/ms instead of50000, so put this
# cache-parity switch after the2300 callback completes. A separate race bench
# verifies immediate revocation/rollback when mode changes during FPGA math.
s=s.replace('c7=mode;env_vx=', 'if(msidx==2305 && dut.work_xy)$fatal(1,"cache parity switch must follow complete callback");c7=mode;env_vx=')
(ROOT/'tests/xy_reference.v').write_text(s)
sources=[FIX/n for n in ['position/mtf_xyz_hold_control.v','position/ano_z_stick.v','position/ano_xy_stick.v','position/ano_xy_divide36.v','position/position_math.v','nav_math_service.v']]
simulate('xy_reference',sources,ROOT/'tests/xy_reference.v')
obs=[list(map(int,l.split()))for l in (ROOT/'tests/xy_rtl.txt').read_text().splitlines()]
assert len(obs)>80,'missing XY callbacks'
bad=[];err=[0.,0.];compared=0
for ms,roll,pitch,active,z in obs:
 c=ref[ms-1]
 if ms<1501 or ms>3000:continue
 expected=[max(-2500,min(2500,-float(c[15])*100)),max(-2500,min(2500,-float(c[14])*100))]
 e=[abs(roll-expected[0]),abs(pitch-expected[1])];err=[max(a,b)for a,b in zip(err,e)];compared+=1
 if any(x>3 for x in e) or not active or not z:bad.append([ms,e,roll,pitch,expected,active,z])
report=dict(publications=len(obs),compared=compared,max_abs_error_cdeg=err,allowed_cdeg=3,passed=not bad,differences=bad[:10],reference='unchanged original OF branch, original PID_calculate and Flight_State_Task',mode_switch_cache=True,position_outer_loop_absent=True)
(ROOT/'tests/xy_reference.json').write_text(json.dumps(report,indent=2));assert report['passed'],report
print('Original C OF velocity controller passed',err)
