"""Read-only rotation follow-up. Writes derived files beside this script only.

python -X utf8 -B analysis/20261026_flight_followup/rotation/analyze_rotation.py
Uses the standard library. No importing product/old analysis code or live I/O.
Fits below are descriptive falsification probes, never deployable calibration.
"""
from pathlib import Path
import collections, csv, datetime, hashlib, json, math, statistics

OUT = Path(__file__).resolve().parent
REPO = OUT.parents[2]
H = REPO.parents[1] / 'handoff_xy_pi_runtime_20261026'
W = H / 'workspace_snapshot'
HW = W / 'github_publish/acg720-fpga-flight-controller/firmware/B0B2/hardware'
P005 = W / 'timing_closure_20261025/v15_xy_p005_i0_review_20261025/hardware'
INPUTS = {
    'dynamic': HW/'v15_stick_oscillation_20261025/recent_telemetry.jsonl',
    'rotation': HW/'v15_unarmed_rotation_20261025T141628_867271Z/samples.jsonl',
    'flow_motion': HW/'v15_flow_motion_20261025T125704_865917Z/samples.jsonl',
    'latest': P005/'response_20261025T160009_877779Z/telemetry_clip.jsonl',
    'surface_plain': P005/'static_20261025T153755_949338Z/samples.jsonl',
    'surface_texture': P005/'static_20261025T154302_137183Z/samples.jsonl',
    'p005_actions': P005/'unarmed_actions_20261025T154419_128573Z/samples.jsonl',
}
PROTOCOLS = {'mtf_sensor':'a581','navigation':'a582','rotation_pair':'a583','flight_info':'a580'}

def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def numbers(values): return [x for x in values if isinstance(x,(int,float)) and not isinstance(x,bool) and math.isfinite(x)]
def describe(values):
    v=sorted(numbers(values))
    if not v:return {'n':0}
    return dict(n=len(v),min=v[0],median=statistics.median(v),max=v[-1],mean=statistics.mean(v),
                p90=v[min(len(v)-1,math.floor(.9*(len(v)-1)))])
def corr(a,b):
    if len(a)<3:return None
    ma=statistics.mean(a);mb=statistics.mean(b)
    aa=[x-ma for x in a];bb=[x-mb for x in b]
    den=math.sqrt(sum(x*x for x in aa)*sum(x*x for x in bb))
    return sum(x*y for x,y in zip(aa,bb))/den if den else None
def rms(values): return math.sqrt(statistics.mean(x*x for x in values)) if values else None

def read_groups(path):
    groups={}; epoch=0; previous_seq=None; duplicates=0
    for line in path.open(encoding='utf-8-sig'):
        record=json.loads(line)
        if 'row' in record:
            rows=[record['row']]; ep=record.get('epoch',0)
        else:
            seq=record.get('sequence',(record.get('flight_info')or{}).get('sequence'))
            if seq is None:continue
            if previous_seq is not None and seq<previous_seq:epoch+=1
            previous_seq=seq;ep=record.get('epoch',epoch)
            data=record.get('data')or{}
            primary={'sequence':seq,'_protocol':'a579'}
            for key in ['roll','pitch','yaw_relative']:
                primary[key+'_cdeg']=data.get(key+'_deg')*100 if isinstance(data.get(key+'_deg'),(int,float))else None
            rows=[primary]
            for key,protocol in PROTOCOLS.items():
                row=record.get(key)
                if row and row.get('sequence')==seq:rows.append(dict(row,_protocol=protocol))
        for row in rows:
            seq=row.get('sequence');pr=row.get('_protocol')
            if seq is None or pr not in ['a579','a57a','a580','a581','a582','a583']:continue
            group=groups.setdefault((ep,seq),dict(epoch=ep,seq=seq,utc=record.get('utc')))
            if pr in group:duplicates+=1;continue
            group[pr]=row
    return sorted(groups.values(),key=lambda g:(g['epoch'],g['seq'])),duplicates

def flatten(name,groups):
    rows=[];errors=collections.Counter();examples=[]
    for group in groups:
        m=group.get('a581',{});p=group.get('a579',{});rot=group.get('a583',{});n=group.get('a582',{});f=group.get('a580',{})
        raw=m.get('module_raw_hex')
        if not raw:continue
        b=bytes.fromhex(raw)
        if len(b)!=27:errors['raw_length']+=1;continue
        if sum(b[:-1])%256!=b[-1]:errors['raw_checksum']+=1
        if b[0]!=0xef or b[3]!=0x51 or b[5]!=20:errors['raw_header']+=1
        native=dict(module_ms=int.from_bytes(b[6:10],'little'),distance_mm=int.from_bytes(b[10:14],'little'),
                    flow_x=int.from_bytes(b[18:20],'little',signed=True),flow_y=int.from_bytes(b[20:22],'little',signed=True),
                    native_seq=b[4],quality=b[22],flow_status=b[23],tof_status=b[16],device_id=b[1],system_id=b[2],reserved1=b[17],reserved2=int.from_bytes(b[24:26],'little'))
        r=dict(dataset=name,epoch=group['epoch'],seq=group['seq'],utc=group['utc'],**native)
        r.update(sample_count=m.get('sample_count'),fpga_snapshot_ms=m.get('fpga_uptime_ms'),source_age_ms=m.get('source_age_ms'),
                 dt_ms=m.get('dt_ms'),module_missing=m.get('module_missing'),module_restarts=m.get('module_restarts'),
                 module_duplicates=m.get('module_duplicates'),uart_errors=m.get('uart_errors'),checksum_errors=m.get('checksum_errors'),
                 pair_sequence=rot.get('pair_sequence'),received_ms=rot.get('received_uptime_ms'),
                 gx=rot.get('gx_deg_s'),gy=rot.get('gy_deg_s'),gz=rot.get('gz_deg_s'),
                 receipt_pair_valid=rot.get('receipt_pair_valid'),exposure_time_aligned=rot.get('exposure_time_aligned'),
                 roll_cdeg=p.get('roll_cdeg'),pitch_cdeg=p.get('pitch_cdeg'),yaw_cdeg=p.get('yaw_relative_cdeg'),
                 xy_active=n.get('xy_shadow_active',n.get('xyz_active')),nav_ready=n.get('xyz_ready'),
                 native_height_ready=n.get('native_height_ready'),velocity_fusion_ready=n.get('velocity_fusion_ready'),
                 xy_reason=n.get('xy_control_reason'),taking_off=f.get('taking_off'),
                 target_roll=p.get('target_roll_cdeg'),target_pitch=p.get('target_pitch_cdeg'),
                 nav_body_x=n.get('body_vx_q16'),nav_body_y=n.get('body_vy_q16'),
                 fused_x=n.get('fused_vx_q16'),fused_y=n.get('fused_vy_q16'))
        r['raw_forward_mmps']=native['flow_y']*native['distance_mm']/100
        r['raw_right_mmps']=-native['flow_x']*native['distance_mm']/100
        r['forward_normalized_radps']=native['flow_y']/100
        r['right_normalized_radps']=-native['flow_x']/100
        for key,expected in [('module_time_ms',native['module_ms']),('distance_mm',native['distance_mm']),('normalized_flow_x',native['flow_x']),('normalized_flow_y',native['flow_y'])]:
            if key in m and m[key]!=expected:errors['decoded_'+key]+=1
        if m.get('flow_provisionally_valid'):
            for axis in ['x','y']:
                if m.get('v'+axis+'_mmps_x100')!=native['flow_'+axis]*native['distance_mm']:errors['metric_product_'+axis]+=1
        if rot:
            for key,expected in [('distance_mm',native['distance_mm']),('vx_x100',m.get('vx_mmps_x100')),('vy_x100',m.get('vy_mmps_x100'))]:
                if rot.get(key)!=expected:
                    errors['pair_'+key]+=1
                    if len(examples)<12:examples.append(dict(epoch=r['epoch'],seq=r['seq'],key=key,mtf=expected,pair=rot.get(key)))
            if r['pair_sequence']!=r['sample_count']%65536:errors['pair_sequence_samplecount']+=1
        if r['received_ms']is not None:
            r['module_minus_fpga_clock_ms']=r['module_ms']-r['received_ms']
            r['snapshot_minus_pair_ms']=r['fpga_snapshot_ms']-r['received_ms']
            r['age_pair_residual_ms']=r['snapshot_minus_pair_ms']-r['source_age_ms']
        rows.append(r)
    return rows,dict(errors),examples

def timing(rows):
    intervals=[];per_epoch=[]
    for ep in sorted(set(r['epoch']for r in rows)):
        rr=[r for r in rows if r['epoch']==ep]
        native_unique=len(set((r['module_ms'],r['native_seq'])for r in rr))
        span=rr[-1]['module_ms']-rr[0]['module_ms']
        clock_rows=[r for r in rr if r.get('received_ms')is not None]
        clock_fit=fit([[r['received_ms']]for r in clock_rows],[r['module_ms']for r in clock_rows],['fpga_received_ms'])
        per_epoch.append(dict(epoch=ep,snapshots=len(rr),unique_native=native_unique,module_span_ms=span,
                              nominal_100hz_coverage=native_unique/(span/10+1)if span>0 else None,
                              affine_clock_fit=clock_fit))
        for a,b in zip(rr,rr[1:]):
            dt=b['module_ms']-a['module_ms']
            if 0<dt<5000:
                intervals.append(dict(epoch=ep,first=a['seq'],second=b['seq'],native_ms=dt,native_seq_delta=(b['native_seq']-a['native_seq'])%256,
                                      sample_count_delta=b['sample_count']-a['sample_count'],telemetry_seq_delta=b['seq']-a['seq']))
    return dict(snapshots=len(rows),per_epoch=per_epoch,
                native_snapshot_spacing_ms=describe([v['native_ms']for v in intervals]),
                sample_count_steps=describe([v['sample_count_delta']for v in intervals]),
                module_seq_matches_10ms_lattice=sum(v['native_ms']%10==0 and v['native_seq_delta']==(v['native_ms']//10)%256 for v in intervals),
                forward_intervals=len(intervals),
                interval_integrated_dt_ms=describe([r['dt_ms']for r in rows]),
                source_age_ms=describe([r['source_age_ms']for r in rows]),
                age_pair_residual_ms=describe([r.get('age_pair_residual_ms')for r in rows]),
                module_minus_fpga_clock_ms=describe([r.get('module_minus_fpga_clock_ms')for r in rows]),
                exposure_time_aligned_counts=dict(collections.Counter(str(r['exposure_time_aligned'])for r in rows)),
                last_error_counters={k:describe([r[k]for r in rows])for k in ['module_missing','module_restarts','uart_errors','checksum_errors']},
                headers_and_reserved={k:sorted(set(r[k]for r in rows))for k in ['device_id','system_id','reserved1','reserved2']})

def quantization(rows):
    result={}
    for axis in ['flow_x','flow_y']:
        values=[r[axis]for r in rows];unique=sorted(set(values));gcd=math.gcd(*[abs(v)for v in values])if values else 0
        result[axis]=dict(n=len(values),nonzero=sum(v!=0 for v in values),zero=sum(v==0 for v in values),
                          unique_values=unique,observed_gcd=gcd,
                          minimum_observed_nonzero_gap=min((b-a for a,b in zip(unique,unique[1:])),default=None))
    return result

def fit(features,target,names):
    if len(target)<max(8,len(names)+3):return None
    means=[statistics.mean(c)for c in zip(*features)];scales=[statistics.pstdev(c)for c in zip(*features)]
    if min(scales)<=1e-12:return None
    x=[[1]+[(v-m)/s for v,m,s in zip(row,means,scales)]for row in features];d=len(x[0])
    matrix=[[sum(row[i]*row[j]for row in x)for j in range(d)]+[sum(row[i]*y for row,y in zip(x,target))]for i in range(d)]
    for i in range(d):
        pivot=max(range(i,d),key=lambda j:abs(matrix[j][i]));matrix[i],matrix[pivot]=matrix[pivot],matrix[i]
        if abs(matrix[i][i])<1e-8:return None
        v=matrix[i][i];matrix[i]=[a/v for a in matrix[i]]
        for j in range(d):
            if j!=i:
                v=matrix[j][i];matrix[j]=[a-v*b for a,b in zip(matrix[j],matrix[i])]
    beta=[matrix[i][-1]for i in range(d)];coef=[v/s for v,s in zip(beta[1:],scales)];intercept=beta[0]-sum(v*m for v,m in zip(coef,means))
    predicted=[intercept+sum(v*b for v,b in zip(row,coef))for row in features]
    mean_target=statistics.mean(target)
    sse=sum((a-b)**2 for a,b in zip(target,predicted));sst=sum((a-mean_target)**2 for a in target)
    return dict(n=len(target),intercept=intercept,coefficients=dict(zip(names,coef)),rmse=math.sqrt(sse/len(target)),r_squared=1-sse/sst if sst else None)

def subset_metrics(rows):
    rr=[r for r in rows if r['receipt_pair_valid'] and all(r[x]is not None for x in ['gx','gy','gz'])and r['flow_status']==1 and r['tof_status']==1 and r['distance_mm']>=80]
    result=dict(n=len(rr),height_mm=describe([r['distance_mm']for r in rr]),gyro_peak_degps={k:max((abs(r[k])for r in rr),default=None)for k in ['gx','gy','gz']})
    for axis,key,sign in [('forward','gy',1),('right','gx',-1)]:
        if not rr:continue
        y=[r['raw_'+axis+'_mmps']for r in rr];q=[math.radians(r[key])*sign for r in rr];h=[r['distance_mm']for r in rr];hq=[a*b for a,b in zip(h,q)]
        strong=[abs(a/b)for a,b in zip(y,q)if abs(b)>=math.radians(5)]
        z=dict(r_raw_gyro=corr(y,q),r_raw_height_gyro=corr(y,hq),r_angular_gyro=corr([r[axis+'_normalized_radps']for r in rr],q),
               raw_rms_mmps=rms(y),apparent_radius_mm_if_all_motion_were_rotation=describe(strong),
               raw_zero_count=sum(v==0 for v in y),
               feature_collinearity_r=corr(q,hq),
               fits=dict(lever_only=fit([[v]for v in q],y,['omega_radps']),
                         height_only=fit([[v]for v in hq],y,['height_mm_times_omega_radps']),
                         both=fit([[a,b]for a,b in zip(q,hq)],y,['omega_radps','height_mm_times_omega_radps']),
                         all_axes_height=fit([[r['distance_mm']*math.radians(r[k])for k in ['gx','gy','gz']]for r in rr],y,['h_gx','h_gy','h_gz'])))
        rho=z['feature_collinearity_r']
        z['standardized_two_feature_gram_condition_number']=(1+abs(rho))/(1-abs(rho))if rho is not None and abs(rho)<1 else None
        bykey={(r['epoch'],r['seq']):r for r in rr};lags={}
        for lag in range(-3,4):
            pairs=[(r,bykey[(r['epoch'],r['seq']+lag)])for r in rr if (r['epoch'],r['seq']+lag)in bykey]
            lags[str(lag)]=dict(n=len(pairs),r=corr([a['raw_'+axis+'_mmps']for a,b in pairs],[a['distance_mm']*math.radians(b[key])*sign for a,b in pairs]),
                               measured_shift_ms=describe([b['received_ms']-a['received_ms']for a,b in pairs]))
        z['lags_telemetry_steps']=lags
        result[axis]=z
    return result

def main():
    allrows={};out=dict(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        scope='Sparse module-payload/receipt-gyro observations only; descriptive fits are not compensation coefficients.',datasets={})
    manifest=[]
    index=json.loads((H/'flight_dataset_index.json').read_text(encoding='utf-8-sig'))
    indexed_hashes={str((W/d['relative_path']/rel).resolve()):entry['sha256']for d in index['datasets']for rel,entry in d['files'].items()}
    for name,path in INPUTS.items():
        groups,dups=read_groups(path);rows,errors,examples=flatten(name,groups);allrows[name]=rows
        entry=dict(handoff_relative=path.relative_to(H).as_posix(),sha256=digest(path),bytes=path.stat().st_size)
        assert indexed_hashes[str(path.resolve())]==entry['sha256'], 'frozen input hash mismatch: '+str(path)
        manifest.append(entry)
        out['datasets'][name]=dict(input=entry,duplicate_protocol_keys=dups,arithmetic_and_pair_errors=errors,
                                    mismatch_examples=examples,timing=timing(rows),observed_raw_quantization=quantization(rows),all_valid=subset_metrics(rows))
    windows={
        'dynamic_pitch_223_308':[r for r in allrows['dynamic']if r['epoch']==12 and 223<=r['seq']<=308 and r['xy_active']and r['distance_mm']>600],
        'dynamic_roll_409_505':[r for r in allrows['dynamic']if r['epoch']==12 and 409<=r['seq']<=505 and r['xy_active']and r['distance_mm']>600],
        'rotation_motion_gt5':[r for r in allrows['rotation']if max(abs(r[k]or 0)for k in ['gx','gy','gz'])>5],
        'rotation_pitch_dominant':[r for r in allrows['rotation']if abs(r['gy']or 0)>5 and abs(r['gy']or 0)>2*max(abs(r['gx']or 0),abs(r['gz']or 0))],
        'rotation_roll_dominant':[r for r in allrows['rotation']if abs(r['gx']or 0)>5 and abs(r['gx']or 0)>2*max(abs(r['gy']or 0),abs(r['gz']or 0))],
        'p005_actions_motion_gt5':[r for r in allrows['p005_actions']if max(abs(r[k]or 0)for k in ['gx','gy','gz'])>5],
    }
    out['windows']={key:subset_metrics(rows)for key,rows in windows.items()}
    out['windows_timing']={key:timing(rows)for key,rows in windows.items()}
    out['recovery_rows']=[r for r in allrows['dynamic']if r['epoch']==12 and r['seq']in [291,292,293,294,295,498,499,500,501,502]]
    out['max_tilt_distance_projection_factor_at_15deg_both_axes']=math.cos(math.radians(15))**2
    out['visible_20_count_velocity_steps_mmps']={str(height):20*height/100 for height in [250,500,1000]}
    out['nominal_native_packet_uart_duration_ms']=27*10/115200*1000
    out['source_bindings']=[]
    for rel in ['sensor/mtf01p_reader.v','sensor/mtf_shared_geometry.v','position/mtf_shared_flow_fusion.v','acg720_ano_port.v']:
        p=REPO/'firmware/B0B3/source'/rel;old=W/'timing_closure_20261025/v15_xy_p005_i0_review_20261025/source'/rel
        out['source_bindings'].append(dict(current_repo_relative=p.relative_to(REPO).as_posix(),sha256=digest(p),frozen_p005_sha256=digest(old),byte_identical=digest(p)==digest(old)))
    (OUT/'rotation_summary.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
    rows=[r for rr in allrows.values()for r in rr]
    with (OUT/'paired_native_rotation.csv').open('w',encoding='utf-8-sig',newline='')as f:
        writer=csv.DictWriter(f,fieldnames=list(dict.fromkeys(k for r in rows for k in r)));writer.writeheader();writer.writerows(rows)
    context_paths=[HW/'v15_unarmed_rotation_20261025T141628_867271Z/operator_context_followup.json',
                   HW/'v15_unarmed_rotation_20261025T141628_867271Z/operator_complete.json',
                   W/'reference_ano/quadrotor_tm_v1_20261012/Quadrotor_TM_V1/Application/Ano_OF_DecoFusion.c']
    contexts=[dict(handoff_relative=p.relative_to(H).as_posix(),sha256=digest(p))for p in context_paths]
    (OUT/'input_manifest.json').write_text(json.dumps(dict(inputs=manifest,all_raw_inputs_match_handoff_index=True,context_sources=contexts,script_sha256=digest(Path(__file__)),writes_scope=str(OUT),hardware_accessed=False),indent=2),encoding='utf-8')
    for name,value in out['datasets'].items():
        t=value['timing'];print(name,'snapshots',t['snapshots'],'spacing',t['native_snapshot_spacing_ms'],'pair/errors',value['arithmetic_and_pair_errors'])
    for key,value in out['windows'].items():
        print(key,json.dumps({axis:{k:v for k,v in value.get(axis,{}).items()if k not in ['fits','lags_telemetry_steps']}for axis in ['forward','right']}))

if __name__=='__main__':main()
