"""B0B2 passive SiK A585 v1/v2/v3 decoder. No serial operations."""
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
VERSIONS=(1,2,3)
UNAVAILABLE_V2=('latest_rejected_source_id','first_protection_time_ms_low32')
UNAVAILABLE_V3=('first_protection_pose_age_ticks',)

def decode(packet):
    if len(packet)!=SIZE or packet[:2]!=HEADER:raise ValueError('A585 size/header')
    if binascii.crc_hqx(packet[2:-2],0xffff)!=int.from_bytes(packet[-2:],'big'):raise ValueError('A585 CRC')
    version,kind,sequence,tick=struct.unpack('>BBHI',packet[2:10])
    if version not in VERSIONS or kind!=1:raise ValueError('A585 version/profile')
    row=dict(zip(KEYS,struct.unpack(FORMAT,packet[10:-2])))
    if row['build_id']!=BUILD_ID:raise ValueError('A585 build identity')
    if row['latest_pose_flags'] & 0xc0:raise ValueError('A585 reserved pose flags')
    if row['first_diagnostic_trigger'] & ~(6 if version==3 else 7):raise ValueError('A585 diagnostic trigger')
    if row['first_diagnostic_cause']>9:raise ValueError('A585 diagnostic cause')
    code=row['first_protection_code']
    if code and ((code>>4)&3!=3 or not code&3):raise ValueError('A585 protection event')
    unavailable=UNAVAILABLE_V2 if version==2 else UNAVAILABLE_V3 if version==3 else ()
    if any(row[name]!=0 for name in unavailable):raise ValueError(f'A585 v{version} unavailable slots must be zero')
    if version==3 and row['first_protection_sensor_mask']&8:raise ValueError('A585 removed age fault bit')
    for name in unavailable:row[name]=None
    row.update(version=version,type=kind,sequence=sequence,capture_tick=tick,
               capabilities={name:name not in unavailable for name in KEYS},
               unavailable_fields=list(unavailable),
               usb_profile='sik_115200_mirror',max_pose_gap_ms=row['max_pose_gap_ticks']/50000,
               held_dt_ms=row['held_dt_ticks']/50000,
               first_protection_pose_age_ms=None if row['first_protection_pose_age_ticks'] is None else row['first_protection_pose_age_ticks']/50000,
               max_pose_gap_scope='completed_publication_intervals' if version==3 else 'includes_open_gap',
               pose_age_qualification_enabled=version!=3,
               diagnostic_scope='First diagnostic anomaly and first recorded armed health protection are separate; neither proves physical root cause')
    if version==3:row['_age_policy']='no_pose_age_v3'
    return row
