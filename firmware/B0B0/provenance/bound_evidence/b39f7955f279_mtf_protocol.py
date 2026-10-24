"""Versioned MTF diagnostic packet; units never overlap legacy PMW counts."""
import binascii
import struct

FORMAT='>BBQ9I27sIiiqqI17s'
assert struct.calcsize(FORMAT)==122
KEYS=('version','mtf_flags','fpga_uptime_ms','sample_count','source_age_ms',
      'checksum_errors','length_errors','uart_errors','packet_timeouts','module_missing',
      'module_duplicates','module_restarts','module_raw','dt_ms','vx_mmps_x100',
      'vy_mmps_x100','x_mm_x100000','y_mm_x100000','integration_breaks','reserved')

def decode_micolink(packet):
    if len(packet)!=27 or packet[0]!=0xef or packet[3]!=0x51 or packet[5]!=20:
        raise ValueError('Micolink 0x51 exact length/header')
    if sum(packet[:-1])&255!=packet[-1]:raise ValueError('Micolink checksum')
    values=struct.unpack('<IIBBBBhhBBH',packet[6:-1])
    keys=('module_time_ms','distance_mm','strength','precision','tof_status',
          'reserved1','normalized_flow_x','normalized_flow_y','flow_quality','flow_status','reserved2')
    return dict(zip(keys,values),module_sequence=packet[4],device_id=packet[1],system_id=packet[2])

def decode_mtf(packet):
    if len(packet)!=128 or packet[:2]!=b'\xa5\x81':raise ValueError('A581 size/header')
    if binascii.crc_hqx(packet[2:-2],0xffff)!=int.from_bytes(packet[-2:],'big'):raise ValueError('A581 CRC')
    row=dict(zip(KEYS,struct.unpack(FORMAT,packet[4:-2])))
    if row['version'] not in (1,2) or any(row.pop('reserved')):raise ValueError('A581 version/reserved')
    flags=row['mtf_flags']
    control=row['version']==2
    if flags&0x70 != (0x20 if control else 0x10):raise ValueError('A581 versioned control/stop-lock contract')
    raw=row.pop('module_raw');row['module_raw_hex']=raw.hex()
    row.update(sequence=int.from_bytes(packet[2:4],'big'),status_qualified=False,
               coordinate_frame='module_axes_unverified',geometry='level_plane_assumption',
               control_input=control,physical_motor_stop_lock=not control,
               experimental_control=control,installation_qualified=False,flight_ready=False)
    if row['sample_count']:
        row.update(decode_micolink(raw))
    elif any(raw):raise ValueError('A581 no-sample raw bytes')
    row.update(link_valid=bool(flags&1) and row['source_age_ms']<200,
               range_provisionally_valid=bool(flags&2),flow_provisionally_valid=bool(flags&4),
               last_interval_integrated=bool(flags&8),saturated=bool(flags&128))
    expected_range=bool(row['sample_count'] and row['link_valid'] and row.get('tof_status')==1 and 10<=row['distance_mm']<=12000)
    expected_flow=bool(expected_range and row['distance_mm']>=80 and row.get('flow_status')==1 and row.get('flow_quality',0)!=0)
    if row['range_provisionally_valid']!=expected_range or row['flow_provisionally_valid']!=expected_flow:
        raise ValueError('A581 provisional validity contradicts raw sample')
    return row

def display_values(row,fresh=True):
    range_ok=fresh and row['link_valid'] and row['range_provisionally_valid']
    flow_ok=range_ok and row['flow_provisionally_valid'] and not row['saturated']
    return dict(mtf_range_cm=row.get('distance_mm',0)/10 if range_ok else None,
        mtf_vx_mm_s=row['vx_mmps_x100']/100 if flow_ok else None,
        mtf_vy_mm_s=row['vy_mmps_x100']/100 if flow_ok else None,
        mtf_x_mm=row['x_mm_x100000']/100000 if flow_ok else None,
        mtf_y_mm=row['y_mm_x100000']/100000 if flow_ok else None,
        mtf_quality=row.get('flow_quality') if fresh and row['link_valid'] else None,
        mtf_source_age_ms=row['source_age_ms'] if fresh else None)
