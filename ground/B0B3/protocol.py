"""Reuse the actual BMI088 decoder and read-only website model."""
from pathlib import Path
import binascii
import struct
import sys
import time
from mtf_protocol import decode_mtf,display_values
from rotation_protocol import decode_rotation
from xy_pi_control import decode_parameter_response
from sik_diagnostic_protocol import decode as decode_imu_diagnostic
from policy_protocol import install_aliases,decode_mtf_v3
from nav_protocol import (decode_nav,display_values as nav_display_values,identity_matches,
                          mtf_identity_matches,OBSERVER_BUILDS)

ROOT=next(p for p in Path(__file__).resolve().parents if (p/'support/bmi_dashboard.py').is_file())
sys.path.insert(0,str(ROOT/'support'))
import bmi_dashboard as base


def gate_description(code):
    stage={0:'无阶段',1:'低档确认阶段',2:'等待高档/高档确认阶段',3:'已解锁阶段'}[(code>>4)&3]
    causes=[label for bit,label in [(1,'遥控无效/通道数或行程越界'),(2,'传感器健康条件不满足'),
                                   (4,'开关离开要求档位'),(8,'准备阶段油门未保持低位')] if code&bit]
    return f"0x{code:02X} · {stage} · "+('；'.join(causes) if causes else '无触发原因位')


def decode_info(packet):
    if len(packet)!=40 or packet[:2]!=b'\xa5\x80':raise ValueError('A580 size/header')
    if binascii.crc_hqx(packet[2:-2],0xffff)!=int.from_bytes(packet[-2:],'big'):raise ValueError('A580 CRC')
    keys=('sequence','version','info_flags','build_id','uptime_ms','event_sequence','event_uptime_ms',
          'event_code','event_sensor_mask','event_imu_reason','event_attitude_fault','event_pose_age_ticks','controller_fault','reserved')
    row=dict(zip(keys,struct.unpack('>HBBIQHQBBBBIBB',packet[2:-2])))
    if row['version']==1:
        if row['reserved'] or row['info_flags']:raise ValueError('A580 v1 reserved')
        row.update(throttle_takeover_active=False,sticky_yaw_fault=None)
    elif row['version']==2 and row['build_id']==0xb0ad:
        if row['info_flags'] & ~1:raise ValueError('A580 v2 flags')
        row.update(throttle_takeover_active=bool(row['info_flags']&1),
                   sticky_yaw_fault=row.pop('reserved'))
    elif row['version']==3 and row['build_id']==0xb0ae:
        if row['info_flags'] & ~15:raise ValueError('A580 ANO state flags')
        row.update(throttle_takeover_active=False,sticky_yaw_fault=row.pop('reserved'),taking_off=bool(row['info_flags']&1),motor_prepared=bool(row['info_flags']&2),flying=bool(row['info_flags']&4),auto_takeoff=bool(row['info_flags']&8))
    elif row['version']==4 and row['build_id'] in (0xb0af,0xb0b0,0xb0b2):
        if row['info_flags'] & ~31:raise ValueError('A580 fallback state flags')
        row.update(throttle_takeover_active=False,sticky_yaw_fault=row.pop('reserved'),
                   taking_off=bool(row['info_flags']&1),motor_prepared=bool(row['info_flags']&2),
                   flying=bool(row['info_flags']&4),auto_takeoff=bool(row['info_flags']&8),
                   height_loss_fallback_active=bool(row['info_flags']&16))
    else:raise ValueError('A580 version/build')
    return row


def receiver():
    result=base.make_receiver()
    result.protocols[b'\xa5\x91']=(24,decode_parameter_response)
    size,primary_decoder=result.protocols[b'\xa5\x79']
    def primary_packet(packet):
        row=primary_decoder(packet)
        # Preserve the legacy decoder's static description as raw annotation,
        # never as a current firmware identity or a physical stop claim.
        if 'program_label' in row:row['legacy_raw_label']=row.pop('program_label')
        return row
    result.protocols[b'\xa5\x79']=(size,primary_packet)
    result.protocols[b'\xa5\x80']=(40,decode_info)
    result.protocols[b'\xa5\x81']=(128,lambda packet:decode_mtf_v3(packet,decode_mtf))
    result.protocols[b'\xa5\x82']=(96,decode_nav)
    result.protocols[b'\xa5\x83']=(48,decode_rotation)
    result.protocols[b'\xa5\x85']=(76,decode_imu_diagnostic)
    install_aliases(result,decode_info,decode_rotation)
    return result


class Dashboard(base.BmiDashboard):
    def __init__(self,port):
        super().__init__(port=port)
        self.info=None;self.info_time=None;self.mtf=None;self.mtf_time=None
        self.nav=None;self.nav_time=None
        self.nav_identity=None
        self.mtf_identity=None
        self.rotation=None;self.rotation_time=None

    def _current_level_application(self):return None

    def ingest(self,row):
        if row.get('_protocol')=='a583':
            with self.lock:
                self.rotation=dict(row);self.rotation_time=self.clock()
            return
        if row.get('_protocol')=='a582':
            with self.lock:
                self.nav=dict(row);self.nav_time=self.clock()
                self.nav_identity=(self.info['build_id'] if self.connected and self.info_time is not None and
                    0<=self.clock()-self.info_time<1 and identity_matches(self.info,row) and
                    abs(row['fpga_uptime_ms']-self.info['uptime_ms'])<1000 else None)
            return
        if row.get('_protocol')=='a581':
            with self.lock:
                self.mtf=dict(row);self.mtf_time=self.clock()
                self.mtf_identity=(self.info['build_id'] if self.connected and self.info_time is not None and
                    0<=self.clock()-self.info_time<1 and mtf_identity_matches(self.info,row) and
                    abs(row['fpga_uptime_ms']-self.info['uptime_ms'])<1000 else None)
            return
        if row.get('_protocol')=='a580':
            with self.lock:
                if self.info and (row['build_id']!=self.info['build_id'] or row['uptime_ms']<self.info['uptime_ms']):
                    self.mtf_time=None;self.nav_time=None;self.nav_identity=None;self.mtf_identity=None
                    self.rotation_time=None
                self.info=dict(row);self.info_time=self.clock()
            return
        super().ingest(row)

    def connection(self,connected,error=None):
        super().connection(connected,error)
        if not connected:
            with self.lock:self.info_time=None;self.mtf_time=None;self.nav_time=None;self.nav_identity=None;self.mtf_identity=None;self.rotation_time=None

    def clear_source(self,port):
        self.connection(False,'切换数据源')
        with self.lock:
            self.port=port;self.latest=None;self.latest_primary_row=None;self.latest_time=None
            self.info=None;self.info_time=None;self.mtf=None;self.mtf_time=None;self.previous_sequence=None
            self.nav=None;self.nav_time=None;self.nav_identity=None
            self.mtf_identity=None
            self.history.clear();self.raw_history.clear();self.last_history_time=-1
            self.frames=0;self.sequence_gap_events=0;self.missing_frames=0;self.sequence_resets=0

    def snapshot(self):
        result=super().snapshot()
        with self.lock:
            info=dict(self.info) if self.info else None
            info_fresh=bool(self.connected and self.info_time is not None and self.clock()-self.info_time<1)
            mtf=dict(self.mtf) if self.mtf else None
            mtf_fresh=bool(self.connected and self.mtf_time is not None and self.clock()-self.mtf_time<.5)
            nav=dict(self.nav) if self.nav else None
            nav_fresh=bool(self.connected and self.nav_time is not None and self.clock()-self.nav_time<.5)
            nav_identity=self.nav_identity
            mtf_identity=self.mtf_identity
        observed=info['build_id'] if info and info_fresh else None
        label=f'BMI088 · {observed:04X} · 数传遥测' if observed is not None else 'BMI088 遥测 · 固件版本待设备上报'
        experimental=observed in (0xb0ab,0xb0ac,0xb0ad,0xb0ae,0xb0af,0xb0b0,0xb0b2)
        with self.lock:
            pair=dict(self.rotation) if self.rotation else None
            pair_fresh=bool(info_fresh and observed in (0xb0ad,0xb0ae,0xb0af,0xb0b0,0xb0b2) and pair and
                            self.rotation_time is not None and self.clock()-self.rotation_time<.5 and
                            pair['sequence']==info['sequence'])
        result.update(throttle_takeover_active=bool(info_fresh and info.get('throttle_takeover_active')),
                      throttle_pickup_us=pair['pickup_us'] if pair_fresh else None,
                      sticky_yaw_fault=info.get('sticky_yaw_fault') if info_fresh else None,
                      rotation_pair=pair if pair_fresh else None)
        result.update(program_label=label,motor_stop_lock_expected=False,flight_ready=False,control_input=experimental,
                      experimental_control=experimental,installation_qualified=False,
                      telemetry_snapshot_scope='已接收的FPGA分帧快照；有效PWM是上报状态，不是当前波形或转速实测',
                      physical_pwm_is_live_measurement=False,
                      flight_info=info if info_fresh else None,flight_info_fresh=info_fresh,
                      firmware_identity_source='设备A580/CRC上报，非JTAG验证' if observed is not None else 'unknown')
        if result.get('data') is not None:result['data']['program_label']=label
        if observed in OBSERVER_BUILDS:
            result.update(program_label=f'{observed:04X} · '+('XYZ定点观察 · 定点含定高 · 四路停机' if observed==0xb0aa else 'MTF-01P 台架观察 · 四路停机'),motor_stop_lock_expected=True)
            if result.get('data') is not None:result['data']['program_label']=result['program_label']
        elif experimental:
            result.update(program_label=f'{observed:04X} · XYZ控制候选 · 实物资格未完成 · DO_NOT_PROGRAM',
                          motor_stop_lock_expected=False,motor_stop_lock_observed=False)
            if result.get('data') is not None:result['data']['program_label']=result['program_label']
        if mtf is not None:
            mtf_fresh=mtf_fresh and info_fresh and mtf_identity_matches(info,mtf) and mtf_identity==observed and abs(mtf['fpga_uptime_ms']-info['uptime_ms'])<1000
            result.update(mtf_sensor=mtf,mtf_fresh=mtf_fresh,
                          mtf_values=display_values(mtf,mtf_fresh))
        if nav is not None:
            nav_fresh=nav_fresh and info_fresh and identity_matches(info,nav) and nav_identity==observed and abs(nav['fpga_uptime_ms']-info['uptime_ms'])<1000
            result.update(navigation=nav,navigation_fresh=nav_fresh,
                          navigation_values=nav_display_values(nav,nav_fresh))
        if observed in (0xb0ae,0xb0af,0xb0b0,0xb0b2) and result.get('data') is not None:
            d=result['data'];rc=d.get('rc_us') or []
            selected=len(rc)>=7 and rc[6]>=1800
            d['mode_active']='光流速度控制 + 高度' if result.get('fresh') and result.get('navigation_fresh') and nav and nav.get('xyz_active') else '自稳 + 高度控制' if result.get('fresh') and d.get('controller_enabled') else '待机'
            d['mode_requested']='光流速度控制 + 高度' if selected else '自稳 + 高度控制'
        fallback=bool(observed in (0xb0af,0xb0b0,0xb0b2) and info_fresh and result.get('fresh') and info.get('height_loss_fallback_active') and (result.get('data') or {}).get('armed') and (result.get('data') or {}).get('controller_enabled'))
        result.update(height_loss_fallback_active=fallback,manual_throttle_active=fallback)
        if fallback and result.get('data') is not None:
            result['data']['mode_active']='自稳 · 测高失效，手动油门接管'
            result['data']['inhibit_text']='测高失效降级已锁存；测距恢复不会在解锁期间自动接管油门，SWA低档停机。'
        return result



LegacyDashboard=Dashboard
class Dashboard(LegacyDashboard):
    def __init__(self,port):
        super().__init__(port)
        self.imu_diagnostic=None;self.imu_diagnostic_time=None

    def ingest(self,row):
        if row.get('_protocol')=='a585':
            with self.lock:
                self.imu_diagnostic=dict(row);self.imu_diagnostic_time=self.clock()
            return
        if row.get('_protocol')=='a580':
            with self.lock:
                if self.info and (self.info['build_id']!=row['build_id'] or row['uptime_ms']<self.info['uptime_ms']):
                    self.imu_diagnostic_time=None
        super().ingest(row)

    def connection(self,connected,error=None):
        super().connection(connected,error)
        if not connected:
            with self.lock:self.imu_diagnostic_time=None

    def clear_source(self,port):
        super().clear_source(port)
        with self.lock:self.imu_diagnostic=None;self.imu_diagnostic_time=None

    def snapshot(self):
        result=super().snapshot()
        info=result.get('flight_info')
        with self.lock:
            row=dict(self.imu_diagnostic) if self.imu_diagnostic else None
            fresh=bool(row and self.connected and self.imu_diagnostic_time is not None and
                0<=self.clock()-self.imu_diagnostic_time<.5 and result.get('flight_info_fresh') and
                isinstance(info,dict) and info.get('build_id')==row['build_id'] and
                isinstance(info.get('uptime_ms'),int) and abs(info['uptime_ms']-row['uptime_ms'])<1000)
        result.update(imu_diagnostic=row,imu_diagnostic_fresh=fresh)
        return result
