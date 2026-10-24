"""Streaming log inspection. Observations and inference stay separate."""
import csv
import json
import math
from collections import deque
from mtf_protocol import display_values
from nav_protocol import display_values as nav_display_values,FIELDS as NAV_FIELDS,identity_matches,mtf_identity_matches,firmware_label

FIELDS={'roll_deg':'横滚 °','pitch_deg':'俯仰 °','yaw_deg':'相对航向 °',
        'throttle_us':'遥控油门 μs','m1_us':'M1调度PWM μs','m2_us':'M2调度PWM μs',
        'm3_us':'M3调度PWM μs','m4_us':'M4调度PWM μs','range_cm':'测距 cm',
        'selected_height_cm':'FPGA选通高度 cm','flow_x':'光流累计X 原始计数','flow_y':'光流累计Y 原始计数',
        'pose_age_ms':'姿态源年龄 ms','rc_valid':'遥控有效 0/1','sensor_ok':'传感器有效 0/1'}
MTF_FIELDS={'mtf_range_cm':'MTF 原始斜距 cm（临时状态筛选）',
    'mtf_vx_mm_s':'MTF 模块X速度 mm/s（水平假设）','mtf_vy_mm_s':'MTF 模块Y速度 mm/s（水平假设）',
    'mtf_x_mm':'MTF 模块X累计位移 mm（缺口不补积分）','mtf_y_mm':'MTF 模块Y累计位移 mm（缺口不补积分）',
    'mtf_quality':'MTF 光流质量（原码）','mtf_source_age_ms':'MTF 接收年龄 ms'}
MTF_RAW_FIELDS={'mtf_normalized_x':('normalized_flow_x','MTF 原始X速度 cm/s@1m'),
    'mtf_normalized_y':('normalized_flow_y','MTF 原始Y速度 cm/s@1m'),
    'mtf_tof_status':('tof_status','MTF 测距状态（原码）'),
    'mtf_flow_status':('flow_status','MTF 光流状态（原码）'),
    'mtf_strength':('strength','MTF 测距信号强度（原码）'),
    'mtf_precision':('precision','MTF 精度字段（原码）'),
    'mtf_samples':('sample_count','MTF FPGA收到的合法帧数'),
    'mtf_missing':('module_missing','MTF 模块序号缺样累计'),
    'mtf_restarts':('module_restarts','MTF 模块重启／时间倒序累计'),
    'mtf_checksum_errors':('checksum_errors','MTF 模块包校验错误累计'),
    'mtf_uart_errors':('uart_errors','MTF UART帧错累计'),
    'mtf_breaks':('integration_breaks','MTF 积分中断累计')}
MTF_FIELDS.update({key:description for key,(_,description) in MTF_RAW_FIELDS.items()})
FIELDS.update(MTF_FIELDS)
FIELDS.update(NAV_FIELDS)


def records(path,max_bytes=None):
    if not path.exists():return
    remaining=path.stat().st_size if max_bytes is None else max_bytes
    with path.open('rb') as stream:
        while remaining>0:
            line=stream.readline(remaining)
            if not line:break
            remaining-=len(line)
            try:yield json.loads(line)
            except ValueError:continue # Writer may be appending the final line.


def point(record):
    r=record['row']
    empty={key:None for key in FIELDS}
    if r.get('_protocol')=='a582':
        return dict(empty,t=record['elapsed_s'],sequence=r['sequence'],epoch=record.get('epoch',0),
                    navigation_sequence=r['navigation_sequence'],source_ready=r['module_link_fresh'],
                    navigation_version=r['version'],navigation_build_id=record.get('_navigation_build_id'),
                    program_label=firmware_label(record.get('_navigation_build_id')),
                    navigation_reason=r['reason'],mapping_verified=bool(r['mapping_verified']),
                    rotation_verified=bool(r['rotation_verified']),
                    control_input=bool(r.get('control_input')) and record.get('_navigation_build_fresh',False),
                    experimental_control=bool(r.get('experimental_control')) and record.get('_navigation_build_fresh',False),
                    installation_qualified=False,flight_ready=False,armed=False,
                    **nav_display_values(r,record.get('_navigation_build_fresh',False)))
    if r.get('_protocol')=='a581':
        fresh=record.get('_mtf_build_fresh',False)
        return dict(empty,t=record['elapsed_s'],sequence=r['sequence'],epoch=record.get('epoch',0),
                    module_epoch=r['module_restarts'],module_breaks=r['integration_breaks'],armed=False,
                    mtf_version=r['version'],mtf_build_id=record.get('_mtf_build_id'),
                    program_label=firmware_label(record.get('_mtf_build_id')),
                    source_ready=fresh and r['link_valid'],
                    control_input=bool(r.get('control_input')) and fresh,
                    experimental_control=bool(r.get('experimental_control')) and fresh,
                    installation_qualified=False,flight_ready=False,
                    **display_values(r,fresh),**{key:r.get(source) if fresh else None for key,(source,_) in MTF_RAW_FIELDS.items()})
    flags=r['flags']
    def angle(key):
        value=r.get(key)
        return value/100 if flags&4 and value is not None else None
    return dict(empty,t=record['elapsed_s'],sequence=r['sequence'],epoch=record.get('epoch',0),
                firmware_build_id=record.get('_firmware_build_id'),
                program_label=firmware_label(record.get('_firmware_build_id')),
                control_input=record.get('_firmware_build_id') in (0xb0ab,0xb0ac,0xb0ad,0xb0ae,0xb0af,0xb0b0),
                experimental_control=record.get('_firmware_build_id') in (0xb0ab,0xb0ac,0xb0ad,0xb0ae,0xb0af,0xb0b0),
                installation_qualified=False,flight_ready=False,
                roll_deg=angle('roll_cdeg'),pitch_deg=angle('pitch_cdeg'),
                yaw_deg=angle('yaw_relative_cdeg'),throttle_us=r['ch3'] if flags&1 else None,
                **{f'm{i}_us':r[f'physical_m{i}_us'] for i in range(1,5)},
                range_cm=r['distance_cm'] if r.get('range_valid') else None,
                selected_height_cm=r['height_mm']/10 if r.get('observer_reason',0)&0x8000 else None,
                flow_x=r['flow_total_x'],flow_y=r['flow_total_y'],pose_age_ms=r['pose_age_ticks']/50000,
                armed=bool(flags&16),rc_valid=int(bool(flags&1)),sensor_ok=int(bool(flags&8)))


def annotated_records(path,max_bytes=None):
    """Bind MTF/navigation to a prior fresh identity in the same source epoch.

    Both input files are size-bounded streams. New recorder logs supply one
    writer's record_order across both files, including equal host timestamps.
    Legacy logs use host_ns (then elapsed_s); equal timestamps consume barriers
    before telemetry rows. Their original cross-file order is not recoverable.
    """
    event_path=path.with_name('events.jsonl')
    event_size=event_path.stat().st_size if event_path.exists() else 0
    barriers=(event for event in records(event_path,event_size)
              if event.get('kind') in ('connected','disconnected'))
    pending=next(barriers,None)
    info=None;info_t=None;info_epoch=None

    def precedes(event,record):
        order=event.get('record_order');record_order=record.get('record_order')
        if isinstance(order,int) and isinstance(record_order,int):
            return order<=record_order
        stamp=event.get('host_ns');record_stamp=record.get('host_ns')
        if isinstance(stamp,int) and isinstance(record_stamp,int):
            return stamp<=record_stamp
        # Very old logs may have elapsed receive time only. A barrier without
        # any usable time conservatively invalidates identity before this row.
        return event.get('elapsed_s',float('-inf'))<=record.get('elapsed_s',0)

    for rec in records(path,max_bytes):
        while pending is not None and precedes(pending,rec):
            info=None;info_t=None;info_epoch=None
            pending=next(barriers,None)
        row=rec.get('row',{});stamp=rec.get('elapsed_s',0)
        epoch=rec.get('epoch',0)
        if info is not None and info_epoch!=epoch:
            info=None;info_t=None;info_epoch=None
        if row.get('_protocol')=='a580':
            info=row;info_t=stamp;info_epoch=epoch
        elif row.get('_protocol')=='a579':
            build_fresh=bool(info and info_epoch==epoch and 0<=stamp-info_t<1)
            rec=dict(rec,_firmware_build_id=info['build_id'] if build_fresh else None)
        elif row.get('_protocol')=='a582':
            build_fresh=bool(identity_matches(info,row) and info_epoch==epoch and
                0<=stamp-info_t<1 and abs(row['fpga_uptime_ms']-info['uptime_ms'])<1000)
            rec=dict(rec,_navigation_build_fresh=build_fresh,
                     _navigation_build_id=info['build_id'] if build_fresh else None)
        elif row.get('_protocol')=='a581':
            build_fresh=bool(mtf_identity_matches(info,row) and info_epoch==epoch and
                0<=stamp-info_t<1 and abs(row['fpga_uptime_ms']-info['uptime_ms'])<1000)
            rec=dict(rec,_mtf_build_fresh=build_fresh,
                     _mtf_build_id=info['build_id'] if build_fresh else None)
        yield rec


def analyze(path,field='throttle_us',start=0,end=float('inf'),limit=2000):
    if field not in FIELDS:raise ValueError('Unknown plot field')
    protocol='a582' if field in NAV_FIELDS else 'a581' if field in MTF_FIELDS else 'a579'
    if not math.isfinite(start) or math.isnan(end) or start<0 or end<start:raise ValueError('Invalid time range')
    limit=max(20,min(4000,int(limit)))//2*2;count=0;first=last=None;prev=None;gaps=0;duplicates=0;restarts=0
    ranges={};faults=0;armed=0;control_candidate_seen=False
    source=path/'telemetry.jsonl';source_size=source.stat().st_size if source.exists() else 0
    for rec in annotated_records(source,source_size):
        r=rec.get('row',{})
        if r.get('_protocol')!=protocol or not start<=rec['elapsed_s']<=end:continue
        p=point(rec);count+=1;armed+=p['armed'];faults=max(faults,r.get('controller_fault_count',0))
        control_candidate_seen=control_candidate_seen or p.get('experimental_control',False)
        if first is None:first=p['t']
        last=p['t']
        if prev and p['epoch']==prev['epoch']:
            delta=(p['sequence']-prev['sequence'])&0xffff
            if delta==0:duplicates+=1
            elif 1<delta<0x8000:gaps+=delta-1
        elif prev:restarts+=1
        prev=p
        for k in FIELDS:
            v=p[k]
            if v is None:continue
            bounds=ranges.setdefault(k,[v,v]);bounds[0]=min(bounds[0],v);bounds[1]=max(bounds[1],v)
    stride=max(1,math.ceil(count/(limit/2)));points=[];bucket=[];prev=None;carry_gap=False
    def emit():
        nonlocal carry_gap
        if bucket:
            valid=[i for i in range(len(bucket)) if bucket[i][field] is not None]
            selected={min(valid,key=lambda i:bucket[i][field]),max(valid,key=lambda i:bucket[i][field])} if valid else {0}
            shown=[bucket[i] for i in sorted(selected)]
            # A gap anywhere in a compressed bucket breaks its incoming line.
            # Never collect one point per gap: corrupt/slow links can be huge.
            broken=any(p['gap'] or p[field] is None for p in bucket)
            if broken:
                for p in shown:p['gap']=True
            elif carry_gap:shown[0]['gap']=True
            carry_gap=broken
            points.extend(shown)
            bucket.clear()
    for rec in annotated_records(source,source_size):
        if rec.get('row',{}).get('_protocol')!=protocol or not start<=rec['elapsed_s']<=end:continue
        p=point(rec)
        p['gap']=bool((protocol=='a581' and not rec['row']['last_interval_integrated']) or (prev and (p['t']-prev['t']>.5 or (p['sequence']-prev['sequence'])&0xffff!=1 or p['epoch']!=prev['epoch'] or p.get('module_epoch')!=prev.get('module_epoch') or p.get('module_breaks')!=prev.get('module_breaks'))))
        if protocol=='a579' and prev:
            p['gap']=p['gap'] or p['firmware_build_id']!=prev.get('firmware_build_id')
        if protocol=='a581':
            p['gap']=p['gap'] or p[field] is None or not p['source_ready'] or bool(prev and
                (p['mtf_version']!=prev.get('mtf_version') or p['mtf_build_id']!=prev.get('mtf_build_id')))
        if protocol=='a582':
            p['gap']=p['gap'] or p[field] is None or not p['source_ready'] or rec['row']['dt_us']==0 or bool(prev and
                (p['navigation_version']!=prev.get('navigation_version') or p['navigation_build_id']!=prev.get('navigation_build_id'))) or bool(prev and
                ((p['navigation_sequence']-prev['navigation_sequence'])&0xffffffff)==0) or bool(prev and
                ((p['navigation_sequence']-prev['navigation_sequence'])&0xffffffff)>=0x80000000)
        bucket.append(p);prev=p
        if len(bucket)>=stride:emit()
    emit()
    events=deque(maxlen=500);event_count=0
    for r in records(path/'events.jsonl'):
        if start<=r.get('elapsed_s',0)<=end:events.append(r);event_count+=1
    return dict(field=field,field_label=FIELDS[field],primary_samples=count,sample_protocol=protocol,time_range=[first,last],
                missing_sequence_estimate=gaps,duplicates=duplicates,epoch_changes=restarts,armed_samples=armed,
                max_controller_fault_count=faults,ranges=ranges,points=points,
                events=list(events),event_count=event_count,
                experimental_control=control_candidate_seen,installation_qualified=False,flight_ready=False,
                interpretation=('本段包含B0AB/B0AC XYZ控制候选数据：控制路径已连接，实物资格未完成；不能将指令解释为停机影子。位置仍由速度积分，无绝对参照。' if control_candidate_seen else 'MTF临时机体／局部坐标估计，方向和转动补偿未实物验收；位置由速度积分得到，无绝对参照。影子指令不驱动电机。' if protocol=='a582' else 'MTF模块坐标、水平面假设；状态码及轴向尚未实物验收。累计位移不补积分缺口；原始斜距与垂直高度分开。' if protocol=='a581' else '地面接收记录；缺口不等于飞机断电。PWM为指令/调度值，非转速。高度为融合/几何选通总线。'),
                verdict=('实验控制候选，DO_NOT_PROGRAM，实物安装／纠偏／飞行资格均未完成；数据仅支持离线分析。' if control_candidate_seen else '仅用于传感器／导航台架分析；不能据此确认定高/定点可飞。' if protocol in ('a581','a582') else '可根据已收到的有效性和事件定位；记录缺失时，停机原因仍可能无法判断。'))


def export_csv(path,output):
    diagnostic_fields=['height_loss_fallback_active','taking_off','motor_prepared','flying','auto_takeoff','build_id','info_flags','event_sequence','event_code','event_sensor_mask','event_imu_reason','event_attitude_fault','event_pose_age_ticks','controller_fault','throttle_takeover_active','sticky_yaw_fault','pickup_us','pair_sequence',
        'received_uptime_ms','distance_mm','dt_ms','pose_age_ticks','vx_x100','vy_x100',
        'gx_counts_q12','gy_counts_q12','gz_counts_q12','receipt_pair_valid','exposure_time_aligned']
    names=['utc','elapsed_s','epoch','protocol','sequence',*FIELDS,'program_label','firmware_build_id','navigation_version','navigation_build_id',
           'mtf_version','mtf_build_id','control_input','experimental_control','installation_qualified','flight_ready','armed',*diagnostic_fields]
    writer=csv.DictWriter(output,fieldnames=names,extrasaction='ignore');writer.writeheader()
    for r in annotated_records(path/'telemetry.jsonl'):
        if r.get('row',{}).get('_protocol') in ('a579','a581','a582'):
            writer.writerow(dict(utc=r['utc'],elapsed_s=r['elapsed_s'],protocol=r['row']['_protocol'],**point(r)))
        elif r.get('row',{}).get('_protocol') in ('a580','a583'):
            row=r['row']
            writer.writerow(dict(utc=r['utc'],elapsed_s=r['elapsed_s'],epoch=r.get('epoch'),
                protocol=row['_protocol'],sequence=row['sequence'],
                **{k:row.get(k) for k in diagnostic_fields}))
