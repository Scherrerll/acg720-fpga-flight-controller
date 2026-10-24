"""Read already transmitted B0B0 targets; never reconstruct targets from RC."""
import math

FIELDS = {
    'roll_sp_deg': 'Roll target deg (reported)',
    'pitch_sp_deg': 'Pitch target deg (reported)',
    'yaw_rate_dps': 'Yaw measured body rate deg/s',
    'yaw_rate_sp_dps': 'Yaw target rate deg/s (reported)',
}


def numeric(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def tracking_fields(row, build=None):
    values = dict.fromkeys(FIELDS)
    if build != 0xb0b0 or row.get('_protocol') != 'a579':
        return values
    flags = row.get('flags')
    if type(flags) is not int:
        return values
    if flags & 12 == 12 and numeric(row.get('gz_corrected')):
        # B0B0 reports bias-corrected body counts, 16.4 counts/(deg/s).
        values['yaw_rate_dps'] = row['gz_corrected'] / 16.4
    if flags & 1:
        for target, source in [('roll_sp_deg', 'target_roll_cdeg'),
                               ('pitch_sp_deg', 'target_pitch_cdeg'),
                               ('yaw_rate_sp_dps', 'target_yaw_rate_cdeg_s')]:
            if numeric(row.get(source)):
                values[target] = row[source] / 100
    return values


def snapshot_tracking(snapshot, row):
    info = snapshot.get('flight_info') or {}
    seq, info_seq = snapshot.get('sequence'), info.get('sequence')
    coherent = (snapshot.get('fresh') is True and snapshot.get('flight_info_fresh') is True
                and type(seq) is int and type(info_seq) is int
                and (seq - info_seq) & 65535 in (0, 1)
                and row is not None and row.get('sequence') == seq)
    return tracking_fields(row, info.get('build_id')) if coherent else dict.fromkeys(FIELDS)
