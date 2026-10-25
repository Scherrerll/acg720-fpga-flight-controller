"""B0B2 passive SiK A585 v1 decoder. No serial operations."""
import binascii
import struct

HEADER=b'\xa5\x85'
SIZE=76
BUILD_ID=0xb0b2
FORMAT='>Q9I8BI4BI'
KEYS=('uptime_ms','build_id','raw_count','accepted_count','pose_count',
      'latest_rejected_source_id','max_pose_gap_ticks','consumed_accepted_id',
      'held_dt_ticks','first_diagnostic_tick','latest_reader_fault',
      'latest_temporal_detail','latest_rejected_raw_flags','latest_pose_flags',
      'latest_pose_attitude_fault','first_diagnostic_trigger','first_diagnostic_cause',
      'first_diagnostic_attitude_fault','first_protection_time_ms_low32',
      'first_protection_code','first_protection_sensor_mask','first_protection_imu_reason',
      'first_protection_attitude_fault','first_protection_pose_age_ticks')
assert struct.calcsize(FORMAT)==64

def decode(packet):
    if len(packet)!=SIZE or packet[:2]!=HEADER:raise ValueError('A585 size/header')
    if binascii.crc_hqx(packet[2:-2],0xffff)!=int.from_bytes(packet[-2:],'big'):raise ValueError('A585 CRC')
    version,kind,sequence,tick=struct.unpack('>BBHI',packet[2:10])
    if version!=1 or kind!=1:raise ValueError('A585 version/profile')
    row=dict(zip(KEYS,struct.unpack(FORMAT,packet[10:-2])))
    if row['build_id']!=BUILD_ID:raise ValueError('A585 build identity')
    if row['latest_pose_flags'] & 0xc0:raise ValueError('A585 reserved pose flags')
    if row['first_diagnostic_trigger'] & ~7:raise ValueError('A585 diagnostic trigger')
    if row['first_diagnostic_cause']>9:raise ValueError('A585 diagnostic cause')
    code=row['first_protection_code']
    if code and ((code>>4)&3!=3 or not code&3):raise ValueError('A585 protection event')
    row.update(version=version,type=kind,sequence=sequence,capture_tick=tick,
               usb_profile='sik_115200_mirror',max_pose_gap_ms=row['max_pose_gap_ticks']/50000,
               held_dt_ms=row['held_dt_ticks']/50000,
               first_protection_pose_age_ms=row['first_protection_pose_age_ticks']/50000,
               diagnostic_scope='First diagnostic anomaly and first recorded armed health protection are separate; neither proves physical root cause')
    return row
