"""Read immutable limited flight logs; write only this response investigation.

The old reader is imported for its exact epoch/sequence join only. Its run()
entry point, which would write the old archive, is never called.
"""
from pathlib import Path
import csv
import datetime
import hashlib
import importlib.util
import json
import math
import statistics
import sys

OUT=Path(__file__).resolve().parent
REPO=OUT.parents[2]
OLD=REPO/'firmware/B0B3/analysis'
sys.path.insert(0,str(OLD))
spec=importlib.util.spec_from_file_location('immutable_old_flight_reader',OLD/'analyze_evidence.py')
reader=importlib.util.module_from_spec(spec);spec.loader.exec_module(reader)
H=reader.ROOT

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def number(v):return isinstance(v,(int,float))and not isinstance(v,bool)and math.isfinite(v)
def centered(v):return number(v)and abs(v-1500)<=50
def seconds(utc):return datetime.datetime.fromisoformat(utc).timestamp()if utc else None
def span(values):
    values=[v for v in values if number(v)]
    return [min(values),max(values)]if values else None
def sign_reversals(values,threshold=.25):
    signs=[1 if v>0 else -1 for v in values if number(v)and abs(v)>=threshold]
    return sum(a!=b for a,b in zip(signs,signs[1:]))

def make_row(name,g):
    p=g['a579'];n=g.get('a582',{});f=g.get('a580',{});a=g.get('a57a',{})
    gain=.05 if name=='p005'else .15
    row=dict(dataset=name,epoch=g['epoch'],sequence=g['seq'],utc=g['utc'],
             paired_info=bool(f),paired_nav=bool(n),parameter_p=gain,parameter_i=0 if name=='p005'else .10)
    for field in ('ch1','ch2','ch3','ch4','ch5','ch7','flags','roll_cdeg','pitch_cdeg',
                  'target_roll_cdeg','target_pitch_cdeg','yaw_relative_cdeg','rejected_count',
                  'controller_fault_count','physical_flags','m1_us','m2_us','m3_us','m4_us'):
        row[field]=p.get(field)
    for field in ('taking_off','flying','auto_takeoff','motor_prepared','height_loss_fallback_active','build_id','uptime_ms'):
        row[field]=f.get(field)
    for field in ('xy_shadow_active','vertical_active','xyz_ready','xy_control_reason','z_reason',
                  'native_height_ready','height_fusion_ready','velocity_fusion_ready','dt_us',
                  'source_age_ms','fused_height_mm','target_height_mm','fused_vx_q16','fused_vy_q16',
                  'position_x_q8','position_y_q8','shadow_roll_cdeg','shadow_pitch_cdeg'):
        row[field]=n.get(field)
    for field in ('world_ax_mmps2','world_ay_mmps2','world_az_up_mmps2'):
        row[field]=a.get(field)
    row['xy_deadzone']=centered(p.get('ch1'))and centered(p.get('ch2'))
    row['xyz_yaw_deadzone']=row['xy_deadzone']and centered(p.get('ch3'))and centered(p.get('ch4'))
    row['armed']=bool(p.get('flags',0)&16)
    row['controller_enabled']=bool(p.get('flags',0)&32)
    row['qualified_visible_xy']=bool(f and n and row['armed']and row['controller_enabled']
        and f.get('taking_off')is True and f.get('height_loss_fallback_active')is False
        and n.get('xy_shadow_active')is True and n.get('vertical_active')is True
        and n.get('xy_control_reason')==0 and n.get('z_reason')==0)
    row['qualified_visible_hover']=bool(row['qualified_visible_xy']and row['xyz_yaw_deadzone']
        and f.get('auto_takeoff')is False and all(n.get(k)is True for k in
        ('native_height_ready','height_fusion_ready','velocity_fusion_ready')))
    for channel,axis in (('ch2','forward'),('ch1','right')):
        value=p.get(channel)
        offset=max(-500,min(500,value-1500))if number(value)else None
        dead=offset-50 if offset is not None and offset>50 else offset+50 if offset is not None and offset< -50 else 0 if offset is not None else None
        row[axis+'_raw_deadzone_norm']=dead*.0022 if dead is not None else None
        row[axis+'_filtered_stick_norm']=None
        row[axis+'_actual_P_cdeg']=None;row[axis+'_actual_I_cdeg']=None;row[axis+'_actual_FF_cdeg']=None
    yaw=p.get('yaw_relative_cdeg');vx=n.get('fused_vx_q16');vy=n.get('fused_vy_q16')
    if all(number(v)for v in (yaw,vx,vy)):
        c=math.cos(math.radians(yaw/100));s=math.sin(math.radians(yaw/100))
        row['heading_forward_velocity_est_mmps']=(vx*c+vy*s)/65536
        row['heading_right_velocity_est_mmps']=(-vx*s+vy*c)/65536
        # A counterfactual P-only reference, NOT an observed contribution.
        # Real callback feedback/LPF/I/command timing is not telemetered.
        row['zero_command_P_only_pitch_reference_deg']=gain*row['heading_forward_velocity_est_mmps']/10
        row['zero_command_P_only_roll_reference_deg']=-gain*row['heading_right_velocity_est_mmps']/10
    else:
        for k in ('heading_forward_velocity_est_mmps','heading_right_velocity_est_mmps',
                  'zero_command_P_only_pitch_reference_deg','zero_command_P_only_roll_reference_deg'):row[k]=None
    for axis in ('roll','pitch'):
        target=p.get('target_'+axis+'_cdeg');actual=p.get(axis+'_cdeg')
        row[axis+'_target_deg']=target/100 if number(target)else None
        row[axis+'_actual_deg']=actual/100 if number(actual)else None
        row[axis+'_target_minus_actual_deg']=(target-actual)/100 if number(target)and number(actual)else None
    row['actual_target_matches_nav']=bool(n and p.get('target_roll_cdeg')==n.get('shadow_roll_cdeg')and p.get('target_pitch_cdeg')==n.get('shadow_pitch_cdeg'))
    return row

def run_metrics(rows,prior,category):
    first,last=rows[0],rows[-1]
    result=dict(category=category,dataset=first['dataset'],epoch=first['epoch'],
        first_sequence=first['sequence'],last_sequence=last['sequence'],samples=len(rows),
        utc_start=first['utc'],utc_end=last['utc'],duration_s=round(seconds(last['utc'])-seconds(first['utc']),6),
        prior_primary_sequence=prior['sequence']if prior else None,
        prior_active_outside_deadzone=bool(prior and prior['qualified_visible_xy']and not prior['xy_deadzone']),
        visible_target_matches_nav=sum(r['actual_target_matches_nav']for r in rows),
        all_xyz_yaw_center=all(r['xyz_yaw_deadzone']for r in rows),
        all_hover_qualified=all(r['qualified_visible_hover']for r in rows))
    result['ranges']={k:span([r.get(k)for r in rows])for k in ('ch1','ch2','ch3','ch4','roll_actual_deg','pitch_actual_deg',
        'roll_target_deg','pitch_target_deg','fused_height_mm','target_height_mm','heading_forward_velocity_est_mmps','heading_right_velocity_est_mmps')}
    result['target_sign_reversals_over_0p25deg']={a:sign_reversals([r[a+'_target_deg']for r in rows])for a in ('roll','pitch')}
    result['tracking_rms_deg']={a:math.sqrt(statistics.mean(r[a+'_target_minus_actual_deg']**2 for r in rows))for a in ('roll','pitch')}
    result['visible_displacement_from_velocity_integrator_mm']={a:(last['position_'+a+'_q8']-first['position_'+a+'_q8'])/256
        if number(last.get('position_'+a+'_q8'))and number(first.get('position_'+a+'_q8'))else None for a in ('x','y')}
    return result

def consecutive_runs(rows,predicate):
    runs=[];current=[]
    for row in rows:
        if predicate(row)and(not current or row['epoch']==current[-1]['epoch']and row['sequence']==current[-1]['sequence']+1):current.append(row)
        else:
            if current:runs.append(current)
            current=[row]if predicate(row)else[]
    if current:runs.append(current)
    return runs

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    summary=dict(scope='Exact epoch/sequence visible-state evidence; no interpolation, no external position truth, no new flight samples.',datasets={},windows=[])
    rows_all=[];events=[];inputs={}
    for name,oldname in (('p005','latest'),('v15','dynamic')):
        path=reader.DATA[oldname];inputs[str(path)]=dict(sha256=sha(path),bytes=path.stat().st_size)
        groups,protocol_counts,duplicates,_,_=reader.read_join(path)
        rows=[make_row(name,g)for g in groups if 'a579'in g];rows_all+=rows
        lookup={(r['epoch'],r['sequence']):r for r in rows}
        dataset=dict(primary_frames=len(rows),protocol_counts=protocol_counts,duplicate_protocol_keys=duplicates,
            visible_qualified_xy=sum(r['qualified_visible_xy']for r in rows),
            visible_xy_with_target_mismatch=sum(r['qualified_visible_xy']and not r['actual_target_matches_nav']for r in rows),
            same_key_missing_info=sum(not r['paired_info']for r in rows),same_key_missing_nav=sum(not r['paired_nav']for r in rows))
        for category,predicate in (
            ('xy_center',lambda r:r['qualified_visible_xy']and r['xy_deadzone']),
            ('all_sticks_center_hover_context',lambda r:r['qualified_visible_hover'])):
            for run in consecutive_runs(rows,predicate):
                if len(run)<2:continue
                prior=lookup.get((run[0]['epoch'],run[0]['sequence']-1))
                summary['windows'].append(run_metrics(run,prior,category))
        dataset['release_windows']=[w for w in summary['windows']if w['dataset']==name and w['category']=='xy_center'and w['prior_active_outside_deadzone']]
        previous=None
        for row in rows:
            if previous and previous['epoch']==row['epoch']and previous['sequence']+1==row['sequence']:
                changed=[k for k in ('xy_deadzone','qualified_visible_xy','height_loss_fallback_active','taking_off','xy_control_reason','z_reason')if row.get(k)!=previous.get(k)]
                if changed:events.append(dict(dataset=name,epoch=row['epoch'],sequence=row['sequence'],utc=row['utc'],changed=';'.join(changed),
                    before=json.dumps({k:previous.get(k)for k in changed}),after=json.dumps({k:row.get(k)for k in changed})))
            previous=row
        summary['datasets'][name]=dataset
    for name,data in (('response_rows.csv',rows_all),('state_events.csv',events)):
        with (OUT/name).open('w',encoding='utf-8-sig',newline='')as f:
            writer=csv.DictWriter(f,fieldnames=list(data[0]));writer.writeheader();writer.writerows(data)
    sources=[OLD/'analyze_evidence.py',OLD/'read_numbered.py',
       REPO/'firmware/B0B3/source/position/mtf_xyz_hold_control.v',REPO/'firmware/B0B3/source/position/ano_xy_stick.v',
       REPO/'firmware/B0B3/source/mtf_xyz_navigation_control.v',REPO/'firmware/B0B3/source/core/flight_core.v',
       reader.RTL/'position/mtf_xyz_hold_control.v',reader.BASE/'source/position/mtf_xyz_hold_control.v',
       reader.P2/'SRC/fc_specific/Ano_LocCtrl.c',reader.P2/'SRC/fc_specific/Ano_FlightCtrl.c',
       reader.P2/'SRC/fc_general/Ano_Pid.c',reader.P2/'Application/Ano_Scheduler.c']
    for path in sources:inputs[str(path)]=dict(sha256=sha(path),bytes=path.stat().st_size)
    summary['unobserved_internal_fields']=['completed 1ms filtered pilot target','20ms callback captured target/feedback/yaw','5Hz LPF internal acceleration','individual P/I/FF contributions','saved/live I and cancellation transactions']
    (OUT/'response_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf8')
    (OUT/'input_manifest.json').write_text(json.dumps(inputs,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps(dict(datasets=summary['datasets'],long_hover_windows=[w for w in summary['windows']if w['category']=='all_sticks_center_hover_context'and w['duration_s']>=5]),indent=2,ensure_ascii=False))

if __name__=='__main__':main()
