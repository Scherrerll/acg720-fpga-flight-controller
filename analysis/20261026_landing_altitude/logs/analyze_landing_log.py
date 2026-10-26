"""Analyze an explicitly frozen finite decoded telemetry window; never live I/O.

--input and its producer's --sha256 are mandatory. Output is confined beside
this script. A591 transaction sequences are never telemetry group keys.
"""
from pathlib import Path
import argparse, collections, csv, datetime, hashlib, json, math, statistics

OUT=Path(__file__).resolve().parent
REPO=OUT.parents[2]
PROTOCOLS={'a579','a57a','a580','a581','a582','a585'}

def stats(values):
    v=[x for x in values if isinstance(x,(int,float))and not isinstance(x,bool)and math.isfinite(x)]
    return dict(n=len(v),min=min(v),max=max(v),first=v[0],last=v[-1],mean=statistics.mean(v))if v else None

def segments(rows,predicate):
    result=[];current=[]
    for r in rows:
        match=predicate(r)
        contiguous=current and r['epoch']==current[-1]['epoch'] and r['sequence']==current[-1]['sequence']+1
        if current and(not match or not contiguous):result.append(summarize(current));current=[]
        if match:current.append(r)
    if current:result.append(summarize(current))
    return result

def summarize(rows):
    a,b=rows[0],rows[-1]
    result=dict(epoch=a['epoch'],start_sequence=a['sequence'],end_sequence=b['sequence'],samples=len(rows),
                start_utc=a['utc'],end_utc=b['utc'],start_uptime_ms=a['uptime_ms'],end_uptime_ms=b['uptime_ms'],
                sampled_span_ms=b['uptime_ms']-a['uptime_ms']if isinstance(a['uptime_ms'],int)and isinstance(b['uptime_ms'],int)else None)
    names=['ch1','ch2','ch3','ch4','ch5','ch7','roll_cdeg','pitch_cdeg','target_roll_cdeg','target_pitch_cdeg',
           'target_height_mm','fused_height_mm','raw_distance_mm','fused_vz_mmps','z_collective_us',
           'min_motor_us','max_motor_us','world_az_up_mmps2','flow_quality']
    result['ranges']={key:stats([r[key]for r in rows])for key in names}
    result['visible_states']={key:dict(collections.Counter(str(r[key])for r in rows))for key in
        ['armed','controller_enabled','command_fresh','taking_off','flying','motor_prepared','auto_takeoff',
         'fallback','xy_active','vertical_active','z_reason','native_height_ready','height_fusion_ready']}
    result['parameter_readbacks']=sorted(set((str(r['p_text']),str(r['i_text']),str(r['generation']))for r in rows))
    result['motor_floor_samples']=sum(r['motor_at_run_min']is True for r in rows)
    result['motor_ceiling_samples']=sum(r['motor_at_run_max']is True for r in rows)
    result['first_row']=a;result['last_row']=b
    return result

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',type=Path,required=True)
    parser.add_argument('--sha256',required=True)
    args=parser.parse_args();source=args.input.resolve()
    if source.is_relative_to((REPO/'ground/runtime').resolve()):raise ValueError('Refuse an active runtime log; provide the frozen out/ window')
    data=source.read_bytes();digest=hashlib.sha256(data).hexdigest()
    if digest!=args.sha256.lower():raise ValueError('Frozen input SHA256 mismatch')
    groups={};parameter_events=[];counts=collections.Counter();dups=collections.Counter();last_order=None;order_errors=0
    for line_number,line in enumerate(data.decode('utf-8-sig').splitlines(),1):
        record=json.loads(line);r=record.get('row',{});pr=r.get('_canonical_protocol',r.get('_protocol'));ep=record.get('epoch')
        counts[pr]+=1
        order=record.get('record_order',line_number)
        if last_order is not None and order<=last_order:order_errors+=1
        last_order=order
        if pr=='a591':
            parameter_events.append(dict(line=line_number,record_order=order,epoch=ep,utc=record.get('utc'),
                                         **{k:r.get(k)for k in ['opcode','status','status_name','sequence','p_text','i_text','p_wire','i_wire','generation','build']}))
            continue
        if pr not in PROTOCOLS:continue
        seq=r.get('sequence')
        if type(seq)is not int or ep is None:continue
        group=groups.setdefault((ep,seq),dict(epoch=ep,sequence=seq,utc=record.get('utc'),first_line=line_number,first_order=order))
        if pr in group:dups[pr]+=1;continue
        group[pr]=r
    rows=[];latest_parameter={};event_index=0
    for g in sorted(groups.values(),key=lambda v:v['first_line']):
        while event_index<len(parameter_events)and parameter_events[event_index]['line']<g['first_line']:
            e=parameter_events[event_index];event_index+=1
            if e['status']==0 and e['build']=='0000B0B3':latest_parameter[e['epoch']]=e
        p=g.get('a579',{});f=g.get('a580',{});n=g.get('a582',{});m=g.get('a581',{});acc=g.get('a57a',{});diag=g.get('a585',{})
        gain=latest_parameter.get(g['epoch'],{})
        flags=p.get('flags');motors=[p.get('physical_m'+str(i)+'_us')for i in range(1,5)]
        motor_valid=all(type(v)is int for v in motors)
        r={k:g[k]for k in ['epoch','sequence','utc','first_line','first_order']}
        r.update(paired_primary=bool(p),paired_info=bool(f),paired_nav=bool(n),paired_mtf=bool(m),paired_accel=bool(acc),paired_imu=bool(diag),
                 uptime_ms=f.get('uptime_ms',n.get('fpga_uptime_ms')),
                 armed=bool(flags&16)if flags is not None else None,
                 controller_enabled=bool(flags&32)if flags is not None else None,
                 command_fresh=bool(flags&64)if flags is not None else None,
                 rc_valid=bool(flags&1)if flags is not None else None,
                 p_text=gain.get('p_text')or(f"{gain['p_wire']/10000:.4f}"if type(gain.get('p_wire'))is int else None),
                 i_text=gain.get('i_text')or(f"{gain['i_wire']/10000:.4f}"if type(gain.get('i_wire'))is int else None),
                 generation=gain.get('generation'),parameter_observed_utc=gain.get('utc'),parameter_transaction_sequence=gain.get('sequence'),
                 min_motor_us=min(motors)if motor_valid else None,max_motor_us=max(motors)if motor_valid else None,
                 motor_at_run_min=(min(motors)==p.get('run_min_us'))if motor_valid else None,
                 motor_at_run_max=(max(motors)==p.get('run_max_us'))if motor_valid else None,
                 raw_distance_mm=m.get('distance_mm'),module_time_ms=m.get('module_time_ms'),native_dt_ms=m.get('dt_ms'),flow_quality=m.get('flow_quality'),
                 fused_vz_mmps=n['fused_vz_q16']/65536 if isinstance(n.get('fused_vz_q16'),int)else None,
                 fused_vx_mmps=n['fused_vx_q16']/65536 if isinstance(n.get('fused_vx_q16'),int)else None,
                 fused_vy_mmps=n['fused_vy_q16']/65536 if isinstance(n.get('fused_vy_q16'),int)else None,
                 fallback=f.get('height_loss_fallback_active'),xy_active=n.get('xy_shadow_active',n.get('xyz_active')),
                 world_az_up_mmps2=acc.get('world_az_up_mmps2'))
        for key in ['ch1','ch2','ch3','ch4','ch5','ch7','roll_cdeg','pitch_cdeg','target_roll_cdeg','target_pitch_cdeg',
                    'mode_active_code','mode_reason','run_min_us','run_max_us','controller_fault_count','rejected_count',
                    'gate_revoke_count','gate_interruption_count','physical_flags']:
            r[key]=p.get(key)
        for i in range(1,5):
            r['command_m'+str(i)+'_us']=p.get('m'+str(i)+'_us')
            r['physical_m'+str(i)+'_us']=p.get('physical_m'+str(i)+'_us')
        for key in ['taking_off','flying','motor_prepared','auto_takeoff','event_code','event_uptime_ms']:
            r[key]=f.get(key)
        for key in ['target_height_mm','fused_height_mm','z_collective_us','z_reason','source_age_ms','vertical_active',
                    'native_height_ready','height_fusion_ready','velocity_fusion_ready','xy_control_reason','xyz_ready',
                    'shadow_roll_cdeg','shadow_pitch_cdeg']:
            r[key]=n.get(key)
        rows.append(r)
    flight=lambda r:r['taking_off']is True and r['armed']is True
    selected=dict(xy_flight=segments(rows,lambda r:flight(r)and r['xy_active']is True),
                  low_throttle=segments(rows,lambda r:flight(r)and type(r['ch3'])is int and r['ch3']<=1100),
                  forward_positive=segments(rows,lambda r:flight(r)and type(r['ch2'])is int and r['ch2']>1550),
                  forward_negative=segments(rows,lambda r:flight(r)and type(r['ch2'])is int and r['ch2']<1450))
    envelopes=[];current=[]
    for r in rows:
        if r['taking_off']is True:current.append(r)
        elif r['taking_off']is None:
            if current:current.append(r)
        elif current:
            e=summarize(current);e['first_observed_not_taking_off']=r
            e['taking_off_unobserved_groups']=sum(v['taking_off']is None for v in current)
            e['taking_off_true_groups']=sum(v['taking_off']is True for v in current)
            envelopes.append(e);current=[]
    if current:
        e=summarize(current);e['first_observed_not_taking_off']=None;e['open_at_window_end']=True;envelopes.append(e)
    group_gaps=[]
    for a,b in zip(rows,rows[1:]):
        if a['epoch']==b['epoch']and b['sequence']>a['sequence']+1:
            group_gaps.append(dict(epoch=a['epoch'],after_sequence=a['sequence'],before_sequence=b['sequence']))
    matched_targets=[r for r in rows if r['xy_active']is True and r['paired_primary']and r['paired_nav']]
    mismatch_targets=[dict(epoch=r['epoch'],sequence=r['sequence'])for r in matched_targets if
                      (r['target_roll_cdeg'],r['target_pitch_cdeg'])!=(r['shadow_roll_cdeg'],r['shadow_pitch_cdeg'])]
    state_keys=['armed','controller_enabled','taking_off','flying','motor_prepared','auto_takeoff','fallback','xy_active','vertical_active','z_reason']
    events=[];previous=None
    for r in rows:
        changes={k:[previous[k],r[k]]for k in state_keys if previous and previous['epoch']==r['epoch']and previous[k]!=r[k]}
        if not previous or previous['epoch']!=r['epoch']or changes:
            events.append(dict(epoch=r['epoch'],sequence=r['sequence'],utc=r['utc'],changes=changes,row=r))
        previous=r
    summary=dict(scope='Frozen finite ground-received observations only; no interpolation, land_lock timer or external height truth',
                 source=str(source),sha256=digest,bytes=len(data),protocol_counts=dict(counts),duplicate_group_protocol_keys=dict(dups),
                 record_order_nonmonotonic=order_errors,groups=len(rows),epochs=sorted(set(r['epoch']for r in rows)),
                 parameters=parameter_events,segments=selected,state_events=events,flight_envelopes=envelopes,
                 entirely_missing_group_brackets=group_gaps,
                 packet_coverage={key:sum(r[key]for r in rows)for key in ['paired_primary','paired_info','paired_nav','paired_mtf','paired_accel','paired_imu']},
                 active_target_comparison=dict(same_key_compared=len(matched_targets),mismatches=mismatch_targets),
                 unknown_fields=['land_lock','landing_ms','landing_delay','per-callback target/P/I/FF','external position/height truth'])
    OUT.mkdir(parents=True,exist_ok=True)
    with (OUT/'joined_rows.csv').open('w',encoding='utf-8-sig',newline='')as out:
        writer=csv.DictWriter(out,fieldnames=list(rows[0])if rows else []);writer.writeheader();writer.writerows(rows)
    (OUT/'log_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    (OUT/'parameter_events.json').write_text(json.dumps(parameter_events,ensure_ascii=False,indent=2),encoding='utf-8')
    assert hashlib.sha256(source.read_bytes()).hexdigest()==digest
    print(json.dumps({k:summary[k]for k in ['source','sha256','bytes','protocol_counts','groups','epochs']},ensure_ascii=False))
    print('segments',json.dumps({k:[{f:s[f]for f in ['epoch','start_sequence','end_sequence','samples','sampled_span_ms']}for s in v]for k,v in selected.items()}))

if __name__=='__main__':main()
