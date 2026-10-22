"""One bounded ingest queue, raw-before-decode disk log, no serial writes."""
from pathlib import Path
import datetime
import hashlib
import json
import os
import queue
import threading
import time
import uuid

from protocol import receiver,gate_description

FILES=('meta.json','raw.bin','chunks.jsonl','telemetry.jsonl','events.jsonl','summary.json')


def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()


class Recorder:
    def __init__(self,root,config,dashboard):
        self.id=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ_')+uuid.uuid4().hex[:8]
        self.path=Path(root)/self.id;self.path.mkdir(parents=True)
        self.config=dict(config);self.dashboard=dashboard;self.receiver=receiver()
        self.queue=queue.Queue(maxsize=2048);self.error=None;self.closed=False
        self.started=time.monotonic();self.bytes=0;self.frames=0;self.primary=0
        self.dropped_chunks=0;self.dropped_bytes=0;self.missing=0;self.duplicates=0
        self.prev=None;self.prev_info=None;self.prev_mtf=None;self.epoch=0;self.events=0;self.last_flush=time.monotonic()
        self.prev_nav=None
        # A single writer orders events and decoded rows across their files.
        # Host timestamps can be equal; this ordinal preserves reconnect barriers.
        self.stream_order=0
        self.prev_connection=None
        self.last_epoch_evidence_ns=-10**20
        self.latencies=[];self._overflow_seen=0
        self.meta=dict(schema='acg720.ground-log.v1',session_id=self.id,started_utc=utc(),source=config,
                       started_monotonic_ns=int(self.started*1e9),
                       read_only=True,serial_writes=False,scope='Ground received telemetry, not an onboard black box',
                       protocol_units={'range':'cm','height':'mm selected fused-or-geometry bus',
                        'velocity':'mm/s','gyro_raw':'integer counts; internal PID gyro remainsQ12',
                        'PWM':'reported effective/command width us in staged frame snapshot; not live waveform measurement or RPM','position':'mm Q8'},
                       firmware_identity='unknown until A580 received',
                       clock_basis='UTC and monotonic host receive timestamps; uptime/event time only when reported by FPGA')
        self.meta['software_sha256']={p.name:hashlib.sha256(p.read_bytes()).hexdigest()
                                     for p in Path(__file__).parent.glob('*.py')}
        self._write_meta()
        self.thread=threading.Thread(target=self.run,name='flight-log-writer',daemon=True);self.thread.start()

    def _write_meta(self):
        p=self.path/'meta.json';temp=p.with_suffix('.tmp')
        temp.write_text(json.dumps(self.meta,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');os.replace(temp,p)

    def put(self,kind,value):
        if self.closed:return False
        item=(kind,value,utc(),time.monotonic_ns())
        try:self.queue.put_nowait(item)
        except queue.Full:
            self.dropped_chunks+=1
            if kind=='chunk':self.dropped_bytes+=len(value)
            self.error='采集队列溢出，存在未保存数据'
            return False
        return True

    def status(self):
        return dict(session_id=self.id,source=self.config,bytes=self.bytes,frames=self.frames,
                    primary_frames=self.primary,queue_depth=self.queue.qsize(),error=self.error,
                    dropped_chunks=self.dropped_chunks,dropped_bytes=self.dropped_bytes,
                    missing_primary_frames=self.missing,duplicates=self.duplicates,closed=self.closed,
                    receiver_checksum_errors=self.receiver.checksum_errors,
                    ingest_latency_p95_ms=sorted(self.latencies)[int(len(self.latencies)*.95)] if self.latencies else None)

    def event(self,kind,detail=None,stamp=None,ns=None):
        self.events+=1
        self.stream_order+=1
        stamp_ns=ns or time.monotonic_ns()
        row=dict(kind=kind,utc=stamp or utc(),host_ns=stamp_ns,elapsed_s=stamp_ns/1e9-self.started,epoch=self.epoch,detail=detail,record_order=self.stream_order)
        self._json(self.event_file,row)

    def _json(self,file,row):file.write(json.dumps(row,ensure_ascii=False,allow_nan=False)+'\n')

    def inspect(self,row,stamp,ns):
        protocol=row.get('_protocol')
        if protocol=='a582':
            if self.prev_nav is None or self.prev_nav['version']!=row['version']:
                self.meta['navigation']=dict(protocol=f"A582 v{row['version']}",height_unit='mm',velocity_unit='mm/s Q16',
                    position_unit='mm Q8',position_reference='provisional velocity integral',
                    height_fusion_enabled=row['height_fusion_enabled'],manual_throttle=row['manual_throttle'],
                    position_hold_includes_height=row['position_hold_includes_height'],
                    standalone_altitude_mode=row['standalone_altitude_mode'],joint_xyz=row['joint_xyz'],
                    module_axes_verified=False,rotation_verified=False,status_qualified=False,
                    physical_motor_stop_lock=row['physical_motor_stop_lock'],control_input=row['control_input'],
                    experimental_control=row['experimental_control'],installation_qualified=False,flight_ready=False)
                self._write_meta()
            if self.prev_nav:
                changed={key:dict(before=self.prev_nav[key],after=row[key]) for key in
                         ('flags','reason','nav_position_reason','axis_mapping','rotation_policy','mapping_verified','rotation_verified')
                         if self.prev_nav[key]!=row[key]}
                if changed:self.event('navigation_diagnostic_changes',changed,stamp,ns)
            self.prev_nav=dict(row)
        if protocol=='a581':
            if self.prev_mtf is None or self.prev_mtf['version']!=row['version']:
                self.meta['mtf_sensor']=dict(protocol=f"Micolink 0x51 / A581 v{row['version']}",distance_unit='mm',
                    normalized_flow_unit='cm/s at 1m',velocity_numerator_unit='0.01mm/s',
                    displacement_numerator_unit='0.00001mm',module_axes_verified=False,status_qualified=False,
                    geometry='level plane assumption',input_hz_nominal=100,telemetry_hz_nominal=5,
                    physical_motor_stop_lock=row['physical_motor_stop_lock'],control_input=row['control_input'],
                    experimental_control=row['experimental_control'],installation_qualified=False,flight_ready=False)
                self._write_meta()
            previous=self.prev_mtf
            if previous:
                counters=('checksum_errors','length_errors','uart_errors','packet_timeouts',
                          'module_missing','module_duplicates','module_restarts','integration_breaks')
                changed={key:dict(before=previous[key],after=row[key]) for key in counters if previous[key]!=row[key]}
                if changed:self.event('mtf_diagnostic_changes',changed,stamp,ns)
                if row['link_valid']!=previous['link_valid']:
                    self.event('mtf_link_validity',dict(valid=row['link_valid']),stamp,ns)
            self.prev_mtf=dict(row)
        if protocol=='a580':
            old=self.prev_info
            source_changed=bool(old and (row['build_id']!=old['build_id'] or row['uptime_ms']<old['uptime_ms']))
            if old and row['build_id']!=old['build_id']:
                # A distinct firmware identity is a distinct source epoch even
                # when uptime increases or restart evidence was just recorded.
                self.epoch+=1;self.last_epoch_evidence_ns=ns
                self.event('reported_build_changed',dict(before=old['build_id'],after=row['build_id']),stamp,ns)
            if old and row['uptime_ms']<old['uptime_ms']:
                self.bump_epoch(ns);self.event('reported_uptime_restart',dict(before=old['uptime_ms'],after=row['uptime_ms']),stamp,ns)
            # First observations from a new build/boot are retained state in
            # that source's epoch, even if they match the previous source.
            diagnostic_old=None if source_changed else old
            if row.get('throttle_takeover_active') != (diagnostic_old or {}).get('throttle_takeover_active') and (diagnostic_old or row.get('throttle_takeover_active')):
                self.event('throttle_takeover',dict(active=bool(row.get('throttle_takeover_active')),
                    explanation='定点退出后等待油门匹配；未保持高度。SWA仍立即停机。'),stamp,ns)
            if row.get('sticky_yaw_fault') and row.get('sticky_yaw_fault')!=(diagnostic_old or {}).get('sticky_yaw_fault'):
                self.event('sticky_yaw_controller_fault',dict(code=row['sticky_yaw_fault'],
                    retained=diagnostic_old is None,fpga_uptime_ms=row['uptime_ms']),stamp,ns)
            if row['event_sequence'] and (old is None or row['event_sequence']!=old['event_sequence']):
                self.event('retained_source_event' if old is None else 'source_event',dict(row,explanation=gate_description(row['event_code'])),stamp,ns)
            self.prev_info=dict(row)
            if self.meta.get('reported_build_id')!=row['build_id']:
                self.meta.update(reported_build_id=row['build_id'],firmware_identity='A580CRC source report, not JTAG')
                self._write_meta()
        if protocol!='a579':return
        self.primary+=1;old=self.prev
        if old:
            probable_restart=row['accepted_count']<old['accepted_count'] or row['command_count']<old['command_count']
            if probable_restart:
                self.bump_epoch(ns);self.event('counter_restart_evidence',dict(sequence=row['sequence']),stamp,ns)
            else:
                step=(row['sequence']-old['sequence'])&0xffff
                if not step:self.duplicates+=1;self.event('duplicate_primary',dict(sequence=row['sequence']),stamp,ns)
                elif step<0x8000 and step>1:
                    self.missing+=step-1;self.event('primary_gap',dict(missing=step-1,before=old['sequence'],after=row['sequence']),stamp,ns)
                elif step>=0x8000:self.event('out_of_order_or_restart_unknown',dict(before=old['sequence'],after=row['sequence']),stamp,ns)
            for counter,code in [('gate_revoke_count','gate_last_revoke_code'),('gate_interruption_count','gate_last_interruption_code')]:
                if row[counter]>old[counter]:self.event(counter,dict(code=row[code],explanation=gate_description(row[code]),row=row),stamp,ns)
            if row['controller_fault_count']>old['controller_fault_count']:
                self.event('controller_fault',dict(count=row['controller_fault_count'],code=row['last_controller_fault'],row=row),stamp,ns)
            if bool(row['flags']&16)!=bool(old['flags']&16):self.event('armed_change',dict(armed=bool(row['flags']&16)),stamp,ns)
        else:
            self.event('first_primary_retained_state',dict(sequence=row['sequence'],revoke_count=row['gate_revoke_count'],revoke_code=row['gate_last_revoke_code'],explanation=gate_description(row['gate_last_revoke_code'])),stamp,ns)
        self.prev=dict(row)

    def bump_epoch(self,ns):
        if ns-self.last_epoch_evidence_ns>1_000_000_000:self.epoch+=1
        self.last_epoch_evidence_ns=ns

    def flush(self):
        for stream in self.streams:stream.flush();os.fsync(stream.fileno())
        self.last_flush=time.monotonic()

    def snapshot_files(self):
        return dict(sizes={name:(self.path/name).stat().st_size for name in FILES if (self.path/name).exists()},
                    inline={name:(self.path/name).read_bytes() for name in ('meta.json','summary.json') if (self.path/name).exists()},
                    status=self.status(),utc=utc())

    def capture_snapshot(self):
        if self.closed:return self.snapshot_files()
        ready=threading.Event();box={}
        if not self.put('snapshot',(ready,box)):raise RuntimeError('记录器无法创建一致快照')
        if not ready.wait(5):raise OSError('日志快照超时；未导出不一致数据，请稍后重试')
        return box['snapshot']

    def run(self):
        self.streams=[]
        try:
            self.raw=(self.path/'raw.bin').open('wb')
            self.streams.append(self.raw)
            self.chunks=(self.path/'chunks.jsonl').open('w',encoding='utf-8',buffering=1)
            self.streams.append(self.chunks)
            self.decoded=(self.path/'telemetry.jsonl').open('w',encoding='utf-8',buffering=1)
            self.streams.append(self.decoded)
            self.event_file=(self.path/'events.jsonl').open('w',encoding='utf-8',buffering=1)
            self.streams.append(self.event_file)
            while True:
                try:item=self.queue.get(timeout=.25)
                except queue.Empty:
                    if time.monotonic()-self.last_flush>=1:self.flush()
                    continue
                if item is None:break
                kind,value,stamp,ns=item
                if self._overflow_seen!=self.dropped_chunks:
                    self.event('ingest_overflow',self.status(),stamp,ns);self.receiver.buffer.clear();self._overflow_seen=self.dropped_chunks
                if kind=='chunk':
                    offset=self.bytes
                    self.raw.write(value);self.bytes+=len(value)
                    self._json(self.chunks,dict(utc=stamp,host_ns=ns,offset=offset,length=len(value)))
                    for row in self.receiver.feed(value):
                        self.frames+=1
                        self.inspect(row,stamp,ns)
                        self.stream_order+=1
                        self._json(self.decoded,dict(utc=stamp,host_ns=ns,elapsed_s=ns/1e9-self.started,epoch=self.epoch,row=row,record_order=self.stream_order))
                        self.dashboard.ingest(row)
                    self.dashboard.update_receiver(self.receiver)
                    self.latencies.append((time.monotonic_ns()-ns)/1e6)
                    if len(self.latencies)>2000:del self.latencies[:1000]
                elif kind=='connection':
                    connected,error=value
                    if self.prev_connection==value:continue
                    self.prev_connection=value
                    self.receiver.buffer.clear()
                    self.dashboard.connection(connected,error)
                    self.event('connected' if connected else 'disconnected',dict(error=error),stamp,ns)
                elif kind=='mark':self.event('operator_mark',dict(text=value),stamp,ns)
                elif kind=='snapshot':
                    ready,box=value;self.flush();box['snapshot']=self.snapshot_files();ready.set()
                if time.monotonic()-self.last_flush>=1:self.flush()
            self.event('recording_closed',self.status());self.flush()
        except Exception as exc:
            self.error=f'日志写入已失败：{type(exc).__name__}: {exc}'
            self.dashboard.connection(False,self.error)
        finally:
            for stream in self.streams:
                try:stream.close()
                except OSError:pass
            self.closed=True
            try:
                self.meta.update(ended_utc=utc(),recording_error=self.error,status=self.status())
                self._write_meta()
                (self.path/'summary.json').write_text(json.dumps(self.status(),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
            except OSError:pass

    def close(self):
        if self.thread.is_alive():self.queue.put(None,timeout=3);self.thread.join(timeout=10)
        if self.thread.is_alive():raise RuntimeError('日志关闭未完成')
