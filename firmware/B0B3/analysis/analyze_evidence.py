"""Read frozen evidence only; exact epoch/sequence pairing, no interpolation."""
from pathlib import Path
import json, hashlib, csv, math, statistics, collections
from read_numbered import ROOT, P2, RTL, BASE
OUT=Path(__file__).resolve().parent
HW=BASE/'hardware'
CAND=ROOT/'timing_closure_20261025/v15_xy_p005_i0_review_20261025/hardware'
DATA={
 'latest':CAND/'response_20261025T160009_877779Z/telemetry_clip.jsonl',
 'dynamic':HW/'v15_stick_oscillation_20261025/recent_telemetry.jsonl',
 'rotation':HW/'v15_unarmed_rotation_20261025T141628_867271Z/samples.jsonl',
 'flow_motion':HW/'v15_flow_motion_20261025T125704_865917Z/samples.jsonl',
 'surface_plain':CAND/'static_20261025T153755_949338Z/samples.jsonl',
 'surface_texture':CAND/'static_20261025T154302_137183Z/samples.jsonl',
 'early1':ROOT/'flight_review_20261025_two_trials/timeline_agent/trial_1.jsonl',
 'early2':ROOT/'flight_review_20261025_two_trials/timeline_agent/trial_2.jsonl',
}
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def read_join(path):
    groups={}; protocols=collections.Counter(); duplicates=0; raw_errors=collections.Counter(); decode_n=0
    local_epoch=0;last_wrapper_seq=None
    def records():
        nonlocal local_epoch,last_wrapper_seq
        for line in path.open(encoding='utf-8-sig'):
            xx=json.loads(line)
            if 'data' not in xx:yield xx;continue
            seq=xx.get('sequence',xx.get('flight_info',{}).get('sequence'))
            if seq is None:continue
            if last_wrapper_seq is not None and seq<last_wrapper_seq:local_epoch+=1
            last_wrapper_seq=seq
            dat=xx['data'];diag=xx.get('diagnostics',{});tr=xx.get('tracking',{})
            p={**diag,'sequence':seq,'_protocol':'a579'}
            for axis in ['roll','pitch']:
                p[axis+'_cdeg']=round(dat[axis+'_deg']*100) if dat.get(axis+'_deg')is not None else None
                p['target_'+axis+'_cdeg']=round(tr[axis+'_sp_deg']*100)if tr.get(axis+'_sp_deg')is not None else None
            for i,v in enumerate(dat.get('rc_us',[]),1):p['ch'+str(i)]=v
            for i,v in enumerate(dat.get('command_us',[]),1):p['m'+str(i)+'_us']=v
            p['flags']=(0x10 if dat.get('armed')else 0)|(0x20 if dat.get('controller_enabled')else 0)
            yield {'epoch':xx.get('epoch',local_epoch),'utc':xx.get('utc'),'elapsed_s':xx.get('elapsed_seconds'),'row':p}
            for key in ['flight_info','mtf_sensor','navigation','rotation_pair','imu_diagnostic']:
                rr=xx.get(key)
                # Snapshot polling is not an atomic multi-packet acquisition.
                if rr and rr.get('sequence')==seq:yield {'epoch':xx.get('epoch',local_epoch),'utc':xx.get('utc'),'elapsed_s':xx.get('elapsed_seconds'),'row':rr}
    for x in records():
        r=x.get('row',x); pr=r.get('_protocol')
        if pr is None:
            if 'roll_cdeg' in r:pr='a579'
            elif 'shadow_roll_cdeg' in r:pr='a582'
            else:pr='unknown'
        seq=r.get('sequence'); epoch=x.get('epoch',0)
        if seq is None:continue
        protocols[pr]+=1; k=(epoch,seq)
        g=groups.setdefault(k,{'epoch':epoch,'seq':seq,'utc':x.get('utc'),'elapsed_s':x.get('elapsed_s')})
        if pr in g:
            duplicates+=1
            # Polling duplicates do not add samples or replace paired data.
            continue
        g[pr]=r
        if pr=='a581' and r.get('module_raw_hex'):
            b=bytes.fromhex(r['module_raw_hex']);decode_n+=1
            if len(b)!=27:raw_errors['length']+=1;continue
            if sum(b[:-1])%256!=b[-1]:raw_errors['checksum']+=1
            raw={
             'distance_mm':int.from_bytes(b[10:14],'little'),
             'module_time_ms':int.from_bytes(b[6:10],'little'),
             'normalized_flow_x':int.from_bytes(b[18:20],'little',signed=True),
             'normalized_flow_y':int.from_bytes(b[20:22],'little',signed=True),
             'flow_quality':b[22], 'flow_status':b[23], 'tof_status':b[16],
            }
            for f,v in raw.items():
                if f in r and r[f]!=v:raw_errors[f]+=1
            for axis in ('x','y'):
                if r.get('flow_provisionally_valid'):
                    v=raw['normalized_flow_'+axis]*raw['distance_mm']
                    if r.get('v'+axis+'_mmps_x100')!=v:raw_errors['metric_'+axis]+=1
    return sorted(groups.values(),key=lambda x:(x['epoch'],x['seq'])),dict(protocols),duplicates,decode_n,dict(raw_errors)
def span(v):return [min(v),max(v)] if v else None
def corr(x,y):
    if len(x)<3:return None
    mx=statistics.mean(x);my=statistics.mean(y); a=sum((v-mx)*(w-my) for v,w in zip(x,y)); b=sum((v-mx)**2 for v in x)*sum((w-my)**2 for w in y)
    return a/math.sqrt(b) if b else None
def run(name,path):
    groups,protocols,dup,raw_n,raw_err=read_join(path)
    primary=[g for g in groups if 'a579'in g]
    paired=[g for g in primary if 'a582'in g]
    enabled=[g for g in paired if g['a579'].get('flags',0)&0x20]
    active=[g for g in paired if g['a582'].get('xy_shadow_active',g['a582'].get('xyz_active',False))]
    # Preserve raw flags; bit4 is armed and bit5 is controller enabled.
    s={'source':str(path),'sha256':sha(path),'protocol_counts':protocols,'duplicate_protocol_keys':dup,
       'groups':len(groups),'primary':len(primary),'primary_nav_pairs':len(paired),'missing_nav_for_primary':len(primary)-len(paired),
       'epochs':sorted({g['epoch'] for g in groups}),'raw_packets_checked':raw_n,'raw_decode_errors':raw_err,
       'active_count':len(active),'raw_primary_flag_counts':dict(collections.Counter(str(g['a579'].get('flags')) for g in primary))}
    export=[]
    for g in paired:
        p=g['a579'];n=g['a582'];a=g.get('a57a',{});f=g.get('a580',{});m=g.get('a581',{});rot=g.get('a583',{});d=g.get('a585',{})
        z={'epoch':g['epoch'],'seq':g['seq'],'utc':g['utc'],'elapsed_s':g['elapsed_s']}
        for src,fields in [(p,['flags','ch1','ch2','ch3','ch5','ch7','roll_cdeg','pitch_cdeg','target_roll_cdeg','target_pitch_cdeg','rejected_count','controller_fault_count','pose_age_ticks','imu_reason','inhibit_reason','m1_us','m2_us','m3_us','m4_us','physical_flags']),
          (n,['xyz_requested','xyz_ready','xyz_active','xy_shadow_active','vertical_active','xy_control_reason','z_reason','source_age_ms','dt_us','body_vx_q16','body_vy_q16','world_vx_q16','world_vy_q16','fused_vx_q16','fused_vy_q16','fused_height_mm','fused_vz_q16','shadow_roll_cdeg','shadow_pitch_cdeg','z_collective_us','target_height_mm','native_height_ready','height_fusion_ready','velocity_fusion_ready','rotation_compensated']),
          (a,['world_ax_mmps2','world_ay_mmps2','world_az_up_mmps2']),
          (f,['build_id','taking_off','height_loss_fallback_active','event_code','event_uptime_ms']),
          (m,['distance_mm','dt_ms','normalized_flow_x','normalized_flow_y','flow_quality','flow_status','tof_status','checksum_errors','uart_errors','module_restarts','module_missing']),
          (rot,['gx_deg_s','gy_deg_s','gz_deg_s','exposure_time_aligned']),
          (d,['max_pose_gap_ms','raw_count','accepted_count','pose_count','held_dt_ms'])]:
            z.update({k:src.get(k) for k in fields})
        export.append(z)
    if export:
        with (OUT/(name+'_paired.csv')).open('w',encoding='utf-8-sig',newline='')as f:
            w=csv.DictWriter(f,fieldnames=list(export[0]));w.writeheader();w.writerows(export)
    active_exp=[z for z in export if z.get('xy_shadow_active') or z.get('xyz_active')]
    s['active_ranges']={k:span([z[k] for z in active_exp if isinstance(z.get(k),(float,int))]) for k in ['seq','roll_cdeg','pitch_cdeg','target_roll_cdeg','target_pitch_cdeg','distance_mm','fused_height_mm','fused_vx_q16','fused_vy_q16','body_vx_q16','body_vy_q16','flow_quality']}
    s['target_mismatches_active']=[{'epoch':z['epoch'],'seq':z['seq'],'nav':[z['shadow_roll_cdeg'],z['shadow_pitch_cdeg']],'actual':[z['target_roll_cdeg'],z['target_pitch_cdeg']]} for z in active_exp if [z['shadow_roll_cdeg'],z['shadow_pitch_cdeg']]!=[z['target_roll_cdeg'],z['target_pitch_cdeg']]]
    s['active_runs']=[]
    last=None
    for z in export:
        act=bool(z.get('xy_shadow_active') or z.get('xyz_active'))
        if act and (last is None or not last['active'] or z['epoch']!=last['epoch']):s['active_runs'].append({'epoch':z['epoch'],'start_seq':z['seq'],'start_utc':z['utc'],'count':0})
        if act:
            rr=s['active_runs'][-1];rr.update(end_seq=z['seq'],end_utc=z['utc']);rr['count']+=1
        last={'active':act,'epoch':z['epoch']}
    ev=[];last=None
    for z in export:
        state=tuple(z.get(k)for k in ['ch7','xy_shadow_active','vertical_active','taking_off','height_loss_fallback_active','xy_control_reason','z_reason'])
        relevant=(z.get('ch5',0)>1700 or z.get('taking_off') or z.get('height_loss_fallback_active'))
        if relevant and state!=last:ev.append(z)
        last=state
    s['events']=ev
    rotpairs=[z for z in export if z['gy_deg_s'] is not None and z['body_vx_q16'] is not None]
    s['receipt_corr']={'n':len(rotpairs),'body_forward_vs_pitchrate':corr([z['body_vx_q16']/65536 for z in rotpairs],[z['gy_deg_s'] for z in rotpairs]),'body_right_vs_rollrate':corr([z['body_vy_q16']/65536 for z in rotpairs],[z['gx_deg_s'] for z in rotpairs])}
    s['all_ranges']={k:span([z[k]for z in export if isinstance(z.get(k),(int,float))])for k in ['distance_mm','body_vx_q16','body_vy_q16','flow_quality','rejected_count','controller_fault_count','max_pose_gap_ms','source_age_ms','dt_ms','module_missing','module_restarts','checksum_errors','uart_errors']}
    if name=='dynamic':
        s['dynamic_height_rate_correlation']={}
        for lo,hi,axis,rate in [(223,308,'body_vx_q16','gy_deg_s'),(409,505,'body_vy_q16','gx_deg_s')]:
            v=[z for z in export if z['epoch']==12 and lo<=z['seq']<=hi and z.get('xy_shadow_active') and isinstance(z.get('distance_mm'),(int,float)) and z['distance_mm']>600 and isinstance(z.get(rate),(int,float))]
            s['dynamic_height_rate_correlation'][str(lo)]={'n':len(v),'r':corr([z[axis]/65536 for z in v],[z['distance_mm']*math.radians(z[rate])for z in v]),'sequences':[z['seq']for z in v],'formula':axis+'/65536 versus distance_mm * radians('+rate+')','exposure_time_aligned':False,'interpretation':'Association only. Translation, receipt-time pairing and 5Hz sampling remain confounded.'}
    if name.startswith('surface'):
        s['surface_distinct_nav_n']=len(export)
        s['surface_peak_body_mmps']={k:max(abs(z[k])/65536 for z in export if isinstance(z.get(k),(float,int)))for k in ['body_vx_q16','body_vy_q16']}
        s['surface_attitude_std_deg']={k:statistics.pstdev(z[k]/100 for z in export if isinstance(z.get(k),(float,int)))for k in ['roll_cdeg','pitch_cdeg']}
        s['surface_max_abs_gyro_dps']={k:max(abs(z[k]) for z in export if isinstance(z.get(k),(float,int)))for k in ['gx_deg_s','gy_deg_s']}
    return s
if __name__=='__main__':
    all_s={k:run(k,p)for k,p in DATA.items()}
    (OUT/'evidence_summary.json').write_text(json.dumps(all_s,ensure_ascii=False,indent=2),encoding='utf8')
    for k,s in all_s.items(): print(k,json.dumps({x:y for x,y in s.items()if x not in ['events','target_mismatches_active','source']},ensure_ascii=False))
