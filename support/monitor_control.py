"""Receive no-prop motor telemetry; scheduled widths are not waveform measurements."""
import argparse
import csv
import json
import math
import struct
import time
from collections import Counter
from pathlib import Path

HEADER = b'\xa5\x79'
COORDINATE_FRAME = 'body_x_forward_y_right_z_down'
MAPPING_RECORD = 'airframe_mapping_20261011.json'
SIZE = 224
RUN_MIN_US = 1200 # Must match this derived bitstream configuration.
POSE_TIMEOUT_TICKS = 3000000 # Current 60 ms bench build; historical images differ.
FIELDS = ['elapsed_s', 'sequence', 'flags', 'inhibit_reason', 'imu_reason', 'last_controller_fault',
          'ch1', 'ch2', 'ch3', 'ch4', 'ch5', 'roll_cdeg', 'pitch_cdeg',
          'target_roll_cdeg', 'target_pitch_cdeg', 'target_yaw_rate_cdeg_s',
          'gx_corrected', 'gy_corrected', 'gz_corrected', 'roll_us', 'pitch_us', 'yaw_us',
          'm1_us', 'm2_us', 'm3_us', 'm4_us', 'accepted_count', 'rejected_count',
          'command_count', 'controller_fault_count', 'pose_age_ticks', 'latency_ticks', 'cal_count', 'who', 'pwr',
          'attitude_fault', 'gate_interruption_count', 'gate_revoke_count',
          'gate_last_interruption_code', 'gate_last_revoke_code',
          'gate_last_interruption_sensor_mask', 'gate_last_interruption_pose_age_ticks',
          'gate_last_interruption_imu_reason', 'gate_last_interruption_attitude_fault',
          'gate_last_revoke_sensor_mask', 'gate_last_revoke_pose_age_ticks',
          'gate_last_revoke_imu_reason', 'gate_last_revoke_attitude_fault', 'physical_m1_us','physical_m2_us','physical_m3_us','physical_m4_us','physical_flags']

# Gate diagnostics retain separate preparation interruptions (stages 1/2) and
# armed revocations (stage 3) until reset. Code bits 0..3 mean RC, sensor,
# switch, and preparation throttle departure; bits 5:4 identify stage 1 low
# confirmation, stage 2 high ready confirmation, or stage 3 armed. These bits
# describe the executed FSM branch priority, not every simultaneous departure.
# Sensor mask bits: 0 !attitude_valid, 1 !calibrated, 2 !pose_seen,
# 3 pose_age_ticks >= POSE_TIMEOUT_TICKS, 4 roll outside +/-45 degrees,
# 5 pitch outside +/-45 degrees, 6 controller_fault != 0, 7 controller_stale.


EXT_FIELDS = ['ch6','ch7','ch8','mode_requested','mode_active','mode_reason','system_flags','calibration_mask',
 'flow_dx','flow_dy','flow_squal','flow_motion','flow_id','flow_sequence','flow_age_ticks','flow_dt_ticks','flow_error','flow_sample_count',
 'flow_total_x','flow_total_y','distance_cm','range_strength','range_temp_raw','range_sequence','range_age_ticks','range_error','range_sample_count',
 'position_x_mm_q8','position_y_mm_q8','velocity_x_mm_s','velocity_y_mm_s','height_mm','vertical_velocity_mm_s',
 'yaw_relative_cdeg','observer_reason','hold_reason','position_sequence','position_age_ticks','run_min_us','run_max_us']
BASE_FMT = '>H4B5H4h4i3h4H5I2H3BHHBBBIBBBIBB4HB'
EXT_FMT = '>3H2BH2B2h3B5I2i3H4I6ih2H2I2H'
BASE_FIELDS = FIELDS[1:]
FIELDS += EXT_FIELDS
FIELDS += ['mode_requested_code','mode_active_code']
assert struct.calcsize(BASE_FMT)==110 and struct.calcsize(EXT_FMT)==111

ACCEL_FMT = '>H B I I 3i 3h'
ACCEL_FIELDS = ('sequence', 'accel_flags', 'pose_age_ticks', 'raw_age_ticks',
                'world_ax_mmps2', 'world_ay_mmps2', 'world_az_up_mmps2',
                'raw_ax', 'raw_ay', 'raw_az')


class _AccelerationDecoder:
    """Independent metadata; latest accepted raw and published pose may differ."""
    HEADER = b'\xa5\x7a'
    SIZE = 32

    @staticmethod
    def decode(packet):
        if len(packet) != 32 or packet[:2] != b'\xa5\x7a':
            raise ValueError('Invalid acceleration size/header')
        checksum = 0
        for byte in packet[2:-1]:
            checksum ^= byte
        if checksum != packet[-1]:
            raise ValueError('Acceleration checksum error')
        values = struct.unpack(ACCEL_FMT, packet[2:-1])
        return {'_kind': 'acceleration_metadata', '_protocol': 'a57a',
                **dict(zip(ACCEL_FIELDS, values, strict=True))}


ACCEL_DECODER = _AccelerationDecoder()
assert struct.calcsize(ACCEL_FMT) == 29


RANGE_FMT = '>H B 5I 3I B H H 5x'
RANGE_COUNTERS = ('framing', 'checksum', 'interbyte_timeout', 'distance', 'weak_signal')
RANGE_FIELDS = ('sequence', 'range_diag_flags', *RANGE_COUNTERS,
                'range_error_total', 'range_good_total', 'range_source_age_ticks',
                'range_last_reject_code', 'range_last_reject_distance_cm', 'range_last_reject_strength')
class _RangeDiagnosticDecoder:
    HEADER = b'\xa5\x7b'
    SIZE = 48
    @staticmethod
    def decode(packet):
        if len(packet)!=48 or packet[:2]!=b'\xa5\x7b':
            raise ValueError('Invalid range diagnostic size/header')
        check=0
        for byte in packet[2:-1]:check^=byte
        if check!=packet[-1]:raise ValueError('Range diagnostic checksum error')
        if any(packet[42:47]):raise ValueError('Nonzero reserved range diagnostic bytes')
        row=dict(zip(RANGE_FIELDS,struct.unpack(RANGE_FMT,packet[2:-1]),strict=True))
        if row['range_diag_flags'] & ~1 or row['range_last_reject_code']>5:
            raise ValueError('Unknown range diagnostic flags/reason')
        total=row['range_error_total']
        if total!=0xffffffff and sum(row[k] for k in RANGE_COUNTERS)!=total:
            raise ValueError('Range diagnostic exclusive counter sum mismatch')
        if total==0xffffffff and sum(row[k] for k in RANGE_COUNTERS)<total:
            raise ValueError('Range diagnostic saturated total inconsistent')
        return {'_kind':'range_diagnostics','_protocol':'a57b',**row}
RANGE_DECODER = _RangeDiagnosticDecoder()
assert struct.calcsize(RANGE_FMT)==45


def decode(packet):
    if len(packet)!=SIZE or packet[:2]!=HEADER: raise ValueError('Invalid size/header')
    check=0
    for byte in packet[2:-1]: check ^= byte
    if check!=packet[-1]: raise ValueError('Checksum error')
    row=dict(zip(BASE_FIELDS,struct.unpack(BASE_FMT,packet[2:112]),strict=True))
    row.update(zip(EXT_FIELDS,struct.unpack(EXT_FMT,packet[112:-1]),strict=True))
    f=row['system_flags']
    requested_code=row['mode_requested'];active_code=row['mode_active']
    mode_names={0:'自稳',1:'定高',2:'定点'}
    row.update(mode_requested_code=requested_code,mode_active_code=active_code,
      mode_requested=mode_names.get(requested_code,f'未知模式 ({requested_code})'),
      mode_active=mode_names.get(active_code,f'未知模式 ({active_code})'))
    row.update(range_valid=bool(f&4) and row['range_age_ticks']<5_000_000,
      flow_valid=bool(f&2) and row['flow_age_ticks']<5_000_000,
      flow_calibrated=bool(f&128),position_valid=bool(f&8) and row['position_age_ticks']<5_000_000,
      height_valid=bool(f&64),height_cm=row['height_mm']/10,
      # The diagnostic card is laser geometry, not the uncalibrated WCZ
      # inertial estimate in height_mm. Same-frame range/tilt are explicit;
      # an unpublished or stale source never creates a displayed estimate.
      height_estimate_cm=(row['distance_cm']*math.cos(math.radians(row['roll_cdeg']/100))*math.cos(math.radians(row['pitch_cdeg']/100))
          if row['observer_reason']&0x8000 and row['flags']&4 and f&4 and row['range_age_ticks']<5_000_000 and row['pose_age_ticks']<3_000_000 else None),
      position_x_m=row['position_x_mm_q8']/256000,position_y_m=row['position_y_mm_q8']/256000,
      velocity_x_m_s=row['velocity_x_mm_s']/1000,velocity_y_m_s=row['velocity_y_mm_s']/1000,
      mode_inhibit_reason={0:'自动模式计算有效',1:'自稳',2:'尚未启用控制',4:'所选模式的单位、安装或光流标定未完成',8:'定位或高度无效',16:'进入条件未满足，请检查油门中位或方向摇杆',32:'请将SWC拨低后重新选择',64:'等待首个自动模式输出',128:'自动控制计算超时或数据重叠',256:'进入定高前，请将油门保持中位'}.get(row['mode_reason'],f"原因代码 {row['mode_reason']}"),
      program_label='BMI088 适配诊断 · 加速度2048计数/g · WHO=加速度ID，PWR=陀螺仪ID · 四路1000 μs停机锁定 · 安装方向待验证')
    if not row['flags']&4: row.pop('yaw_relative_cdeg', None)
    return row


def invariants(row, run_min_us=RUN_MIN_US):
    errors = []
    flags = row['flags']
    rc_valid, calibrated, attitude_valid, sensor_ok, armed, enabled, fresh = [
        bool(flags & (1 << bit)) for bit in range(7)]
    motors = [row[f'm{i}_us'] for i in range(1, 5)]
    if row.get('mode_requested_code',0) not in (0,1,2) or row.get('mode_active_code',0) not in (0,1,2):
        errors.append('unknown_mode')
    if any(not 1000 <= value <= 2000 for value in motors):
        errors.append('motor_range')
    if fresh and any(value < run_min_us for value in motors):
        errors.append('active_motor_below_run_min')
    if not fresh and motors != [1000] * 4:
        errors.append('inactive_command_not_idle')
    if enabled and not (rc_valid and calibrated and attitude_valid and sensor_ok and armed and (row['ch3'] > 1100 or row.get('mode_active_code',0) in (1,2))):
        errors.append('enabled_without_requirements')
    if fresh and not enabled:
        errors.append('fresh_without_enabled')
    if armed and not (rc_valid and sensor_ok and 1800 <= row['ch5'] <= 2200):
        errors.append('armed_without_requirements')
    if fresh and row['latency_ticks'] > 4096:
        errors.append('control_latency_over_budget')
    if sensor_ok and ((row.get('_age_policy')!='no_pose_age_v3' and row['pose_age_ticks'] >= POSE_TIMEOUT_TICKS) or abs(row['roll_cdeg']) > 4500 or abs(row['pitch_cdeg']) > 4500):
        errors.append('sensor_freshness_or_tilt')
    # last_controller_fault and gate diagnostics are retained history; they do
    # not mean a live fault and must not participate in these live invariants.
    physical=[row[f'physical_m{i}_us'] for i in range(1,5)]
    if any(not 1000<=v<=2000 for v in physical): errors.append('physical_range')
    if not (row['physical_flags'] & 2) and physical != [1000]*4: errors.append('physical_inactive_not_idle')
    if row['physical_flags'] & 2 and any(value < run_min_us for value in physical):
        errors.append('physical_active_below_run_min')
    if row['physical_flags'] & 2 and not fresh: errors.append('physical_active_without_fresh_command')
    if row.get('mode_active_code',0)==2 and (row['calibration_mask']!=255 or not row['position_valid'] or not row['height_valid'] or not enabled):
        errors.append('hold_without_requirements')
    if row.get('mode_active_code',0)==1 and (row['calibration_mask']&0x98!=0x98 or not row['height_valid'] or not enabled):
        errors.append('altitude_without_requirements')
    if row['run_min_us']!=1200 or row['run_max_us']!=2000:
        errors.append('unexpected_pwm_profile')
    return errors


def idle_departures(row):
    """Capture policy for stationary disarmed tests, not an FPGA failsafe."""
    reasons = []
    if row['flags'] & 1 and not (800 <= row['ch3'] <= 1100 and 800 <= row['ch5'] <= 1200):
        reasons.append('idle_throttle_or_switch_changed')
    if row['flags'] & 0x70:
        reasons.append('idle_control_activated')
    if row['physical_flags'] & 2 or any(row[f'physical_m{i}_us'] != 1000 for i in range(1,5)):
        reasons.append('idle_pwm_not_idle')
    return reasons


class Receiver:
    """Return/count primary A579 only; track A57A metadata independently."""
    def __init__(self):
        self.buffer = bytearray()
        self.checksum_errors = 0
        self.discarded_bytes = 0
        self.acceleration_metadata_frames = 0
        self.acceleration_checksum_errors = 0
        self.latest_acceleration_metadata = None
        self.range_diagnostic_frames=0
        self.range_diagnostic_checksum_errors=0
        self.latest_range_diagnostic=None

    def feed(self, data):
        self.buffer.extend(data)
        rows = []
        while True:
            positions = [(self.buffer.find(header), header, size)
                         for header, size in ((HEADER, SIZE), (ACCEL_DECODER.HEADER, ACCEL_DECODER.SIZE), (RANGE_DECODER.HEADER,RANGE_DECODER.SIZE))]
            candidates = [item for item in positions if item[0] >= 0]
            if not candidates:
                keep = 1 if self.buffer.endswith(HEADER[:1]) else 0
                self.discarded_bytes += len(self.buffer) - keep
                self.buffer[:] = self.buffer[-keep:] if keep else b''
                break
            index, header, size = min(candidates, key=lambda item: item[0])
            if index:
                self.discarded_bytes += index
                del self.buffer[:index]
            if len(self.buffer) < size:
                break
            packet = bytes(self.buffer[:size])
            try:
                row = decode(packet) if header == HEADER else (ACCEL_DECODER.decode(packet) if header==ACCEL_DECODER.HEADER else RANGE_DECODER.decode(packet))
            except ValueError:
                if header == HEADER:
                    self.checksum_errors += 1
                elif header==ACCEL_DECODER.HEADER:
                    self.acceleration_checksum_errors += 1
                else:
                    self.range_diagnostic_checksum_errors += 1
                del self.buffer[0]
                continue
            if header == HEADER:
                rows.append(row)
            elif header==RANGE_DECODER.HEADER:
                self.range_diagnostic_frames+=1;self.latest_range_diagnostic=row
            else:
                self.acceleration_metadata_frames += 1
                self.latest_acceleration_metadata = row
            del self.buffer[:size]
        return rows

