from pathlib import Path
import hashlib,json,os,subprocess,time
O=Path(__file__).resolve().parent;R=O.parents[2]
B3=R/'firmware/B0B3/source';B4=R/'out/z_aw_fix_20261026/compact_aw_v5/canonical/source'
B=Path(r'C:\Users\ScherrerL\Desktop\apple\.tools\iverilog\app\bin')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(B3/'position/mtf_xyz_hold_control.v')=='b7eef6d33789523cd1e8ff81b05e75db91ab3c67bf76e03483dec356055fa1a6'
assert sha(B4/'position/mtf_xyz_hold_control.v')=='04e75ada52551d5622af060efe38fda9aa66ff25199bfb67651f9ec5315ed873'
paths=[p.relative_to(B3) for p in sorted(B3.rglob('*')) if p.is_file()]
assert len(paths)==55
def sources(s):return {str(p).replace('\\','/'):sha(s/p) for p in paths}
before3=sources(B3);before4=sources(B4)
inputs={'B3_source55':before3,'B4_source55':before4,'source_roots':{'B3':str(B3),'B4':str(B4)},
 'scripts':{p.name:sha(p) for p in [O/'run_regression.py',O/'aw_tb.v',O/'b4_v1_reference.v']},'tools':{str(p):sha(p) for p in [B/'iverilog.exe',B/'vvp.exe']}}
(O/'inputs.json').write_text(json.dumps(inputs,indent=2)+'\n')
old=(B3/'position/mtf_xyz_hold_control.v').read_text().replace('module mtf_xyz_hold_control #(','module mtf_xyz_hold_control_b3 #(')
(O/'b3_controller_reference.v').write_text(old)
ports='''
 .clk(clk),.rst_n(rst_n),.origin_reset(origin),.rc_valid(rc_valid),.channel_count(4'd8),
 .ch1(16'd1500),.ch2(16'd1500),.ch3(ch3),.ch4(16'd1500),.ch7(16'd2000),
 .xy_p_value(pval),.xy_i_value(ival),.parameter_boundary(),.enabled(enabled),.taking_off(taking_off),
 .position_valid(height_valid),.height_valid(height_valid),.position_update(position_update),.height_update(height_update),
 .sample_update(sample_update),.sample_dt_us(32'd11000),.position_age(32'd0),.position_dt_us(32'd22000),
 .x_q8(32'sd0),.y_q8(32'sd0),.vx(vx),.vy(vy),.height_mm(height_mm),.vz(vz),.yaw_cdeg(16'sd0),
 .acc_valid(height_valid),.ax_mmps2(32'sd0),.ay_mmps2(32'sd0),.az_mmps2(32'sd0),.collective_us(16'd1500),
 .requested(),.ready(),.active(),.height_requested(),.height_ready(),.height_active(hactive),.auto_takeoff(),
 .reason(),.height_reason(),.collective_target_us(collective),.roll_target(roll),.pitch_target(pitch),
 .throttle_delta(),.requested_climb_mmps(climb),.target_height_mm(target),
 .pilot_norm_x(),.pilot_norm_y(),.pilot_norm_update(),.pilot_norm_valid(),.pilot_norm_dt_us(),
 .math_mul_start(mreq),.math_mul_cancel(mcancel),.math_mul_a(ma),.math_mul_b(mb),
 .math_mul_busy(mbusy),.math_mul_done(mdone),.math_mul_result(mresult),
 .math_div_start(dreq),.math_div_cancel(dcancel),.math_div_numerator(da),.math_div_denominator(db),
 .math_div_busy(dbusy),.math_div_done(ddone),.math_div_error(derror),.math_div_result(dresult)'''
def harness(name,module):return f'''module {name}(input wire clk,rst_n,enabled,rc_valid,height_valid,origin,taking_off,
input wire sample_update,height_update,position_update,input wire[15:0]ch3,pval,ival,
input wire signed[31:0]height_mm,vz,vx,vy,output wire[15:0]collective,
output wire signed[31:0]target,climb,output wire signed[15:0]roll,pitch,output wire hactive);
wire mreq,mcancel,mbusy,mdone,merror,dreq,dcancel,dbusy,ddone,derror;
wire signed[63:0]ma,mb,mresult,da,dresult;wire[31:0]db;
{module} #(.CAL_MASK(8'hff),.VELOCITY_FRAC_BITS(16)) dut({ports});
nav_math_service #(.CLIENTS(1),.DIVIDE(0)) mul(.clk(clk),.rst_n(rst_n),.request(mreq),.cancel(mcancel),
 .operand_a(ma),.operand_b(mb),.busy(mbusy),.done(mdone),.error(merror),.result(mresult),.grant());
nav_math_service #(.CLIENTS(1),.DIVIDE(1)) div(.clk(clk),.rst_n(rst_n),.request(dreq),.cancel(dcancel),
 .operand_a(da),.operand_b({{32'd0,db}}),.busy(dbusy),.done(ddone),.error(derror),.result(dresult),.grant());
endmodule\n'''
(O/'pair_harness.v').write_text(harness('candidate_side','mtf_xyz_hold_control')+harness('base_side','mtf_xyz_hold_control_b3')+harness('v1_side','mtf_xyz_hold_control_v1'))
T=O/'tmp';T.mkdir(exist_ok=True)
env=dict(os.environ,TMP=str(T),TEMP=str(T),TMPDIR=str(T))
helper=['nav_math_service.v','position/position_math.v','position/ano_xy_stick.v','position/ano_xy_divide36.v','position/ano_z_stick.v']
assert all(sha(B3/p)==sha(B4/p) for p in helper)
cmd=[str(B/'iverilog.exe'),'-g2012','-s','tb','-o',str(O/'regression.vvp'),str(O/'aw_tb.v'),str(O/'pair_harness.v'),str(O/'b3_controller_reference.v'),str(O/'b4_v1_reference.v'),str(B4/'position/mtf_xyz_hold_control.v'),*[str(B4/p) for p in helper]]
c=subprocess.run(cmd,env=env,capture_output=True,text=True)
(O/'compile.log').write_text(c.stdout+c.stderr)
assert c.returncode==0,c.stdout+c.stderr
results=[]
for n,name in [(1,'natural_upper_and_low_stick'),(2,'unsaturated_equivalence'),(3,'natural_lower_and_positive_recovery'),(4,'cancel_and_takingoff'),(5,'xy_i0_independence')]:
    d=O/name;d.mkdir(exist_ok=True);start=time.time()
    with (d/'simulation.log').open('w') as f:
        p=subprocess.run([str(B/'vvp.exe'),str(O/'regression.vvp'),f'+CASE={n}'],cwd=d,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=600)
    output=(d/'simulation.log').read_text()
    row={'case':n,'name':name,'exit_code':p.returncode,'seconds':time.time()-start,'checks':[x for x in output.splitlines() if x.startswith('PASS')],
         'log_sha256':sha(d/'simulation.log'),'trace_sha256':sha(d/'trace.csv')}
    results.append(row)
    (O/'results.json').write_text(json.dumps({'scope':'Actual B3/B4 controller/shared-math RTL; legal fixed sensor boundary stimuli, no plant or flight replay. Callback cadence2500clocks forZ-only and20000 forXY/I0, original11ms/1ms dt. Compact vsB4-v1 module outputs/integrals are checked everycycle. No private force/preload. Publication comparison allows exactly2newclocks.','completed':len(results),'passed':all(r['exit_code']==0 and len(r['checks'])>=2 for r in results),'results':results},indent=2)+'\n')
    print(output,flush=True)
    assert p.returncode==0 and len(row['checks'])>=2,output
assert sources(B3)==before3 and sources(B4)==before4,'Input source changed during regressions'
(O/'source_stability.json').write_text(json.dumps({'B3_source55_unchanged':True,'B4_source55_unchanged':True,'inputs_sha256':sha(O/'inputs.json'),'local_compiled_omitted_sha256':sha(O/'regression.vvp')},indent=2)+'\n')
