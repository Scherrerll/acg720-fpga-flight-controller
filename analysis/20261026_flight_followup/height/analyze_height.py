"""Read frozen flight packets; write derived evidence only beside this script.

No interpolation and no requirement for a main packet before examining A580/
A582. This preserves seq375, whose main packet is absent from the window.
"""
from pathlib import Path
import collections
import csv
import difflib
import hashlib
import json

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
H = Path('C:/Users/ScherrerL/Desktop/apple/handoff_xy_pi_runtime_20261026')
OLD = H / 'workspace_snapshot/timing_closure_20261025/v15_xy_p005_i0_review_20261025/source'
NEW = REPO / 'firmware/B0B3/source'
CLIP = OLD.parent / 'hardware/response_20261025T160009_877779Z/telemetry_clip.jsonl'
EXPECTED_CLIP = '73df2c5c9b36e3e6d8f8afee94b6c3e508ab8d4112982055e7ac9fb8d96a0649'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(name, obj):
    (HERE / name).write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n', encoding='utf8')


def main():
    assert sha(CLIP) == EXPECTED_CLIP
    groups = {}
    protocols = collections.Counter()
    duplicates = []
    for line_number, line in enumerate(CLIP.open(encoding='utf8'), 1):
        item = json.loads(line)
        row = item['row']
        key = item.get('epoch'), row.get('sequence')
        protocol = row.get('_protocol')
        protocols[protocol] += 1
        group = groups.setdefault(key, {})
        if protocol in group:
            duplicates.append([key, protocol, line_number])
            continue
        group[protocol] = dict(row=row, line=line_number, utc=item['utc'])

    columns = [('a579', n) for n in (
        'ch1', 'ch2', 'ch3', 'ch4', 'ch5', 'ch7', 'flags', 'roll_cdeg', 'pitch_cdeg',
        'target_roll_cdeg', 'target_pitch_cdeg', 'rejected_count', 'controller_fault_count',
        'gate_revoke_count', 'gate_last_revoke_code', 'm1_us', 'm2_us', 'm3_us', 'm4_us')]
    columns += [('a580', n) for n in (
        'uptime_ms', 'taking_off', 'flying', 'motor_prepared', 'height_loss_fallback_active',
        'event_sequence', 'event_uptime_ms', 'event_code', 'event_sensor_mask')]
    columns += [('a57a', n) for n in (
        'accel_flags', 'raw_age_ticks', 'world_ax_mmps2', 'world_ay_mmps2', 'world_az_up_mmps2')]
    columns += [('a581', n) for n in (
        'sample_count', 'source_age_ms', 'distance_mm', 'tof_status', 'flow_status', 'flow_quality',
        'module_time_ms', 'module_sequence', 'dt_ms', 'module_missing', 'module_duplicates',
        'module_restarts', 'integration_breaks', 'checksum_errors', 'uart_errors', 'length_errors', 'packet_timeouts')]
    columns += [('a582', n) for n in (
        'fpga_uptime_ms', 'navigation_sequence', 'height_mm', 'fused_height_mm', 'fused_vz_q16',
        'native_height_ready', 'native_range_fresh', 'height_fusion_ready', 'velocity_fusion_ready',
        'xy_shadow_active', 'vertical_active', 'xy_control_reason', 'z_reason', 'z_collective_us',
        'target_height_mm', 'reason')]
    columns += [('a585', n) for n in (
        'raw_count', 'accepted_count', 'pose_count', 'latest_reader_fault', 'latest_pose_flags',
        'latest_pose_attitude_fault', 'first_diagnostic_trigger', 'first_protection_code', 'max_pose_gap_ticks')]
    fields = ['epoch', 'sequence', 'protocols', 'primary_missing', 'mtf_minus_geometry_publications']
    for protocol in ('a579', 'a580', 'a57a', 'a581', 'a582', 'a585'):
        fields += [protocol + '.utc', protocol + '.line']
    fields += [protocol + '.' + field for protocol, field in columns]
    selected = []
    for (epoch, seq), group in sorted(groups.items()):
        if epoch != 22 or not (195 <= seq <= 250 or 335 <= seq <= 392):
            continue
        value = dict(epoch=epoch, sequence=seq, protocols=','.join(sorted(group)), primary_missing='a579' not in group)
        for protocol, item in group.items():
            value[protocol + '.utc'] = item['utc']
            value[protocol + '.line'] = item['line']
        for protocol, field in columns:
            if protocol in group:
                value[protocol + '.' + field] = group[protocol]['row'].get(field)
        if 'a581' in group and 'a582' in group:
            value['mtf_minus_geometry_publications'] = group['a581']['row']['sample_count'] - group['a582']['row']['navigation_sequence']
        selected.append(value)
    with (HERE / 'boundary_packets.csv').open('w', encoding='utf8', newline='') as stream:
        writer = csv.DictWriter(stream, fields, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(selected)

    transitions = []
    last = None
    for (epoch, seq), group in sorted(groups.items()):
        if epoch != 22 or 'a580' not in group:
            continue
        item = group['a580']
        active = item['row']['height_loss_fallback_active']
        if active and last and not last['active']:
            before = groups[(epoch, last['seq'])]
            mt0 = before.get('a581', {}).get('row', {})
            mt1 = group.get('a581', {}).get('row', {})
            counters = {n: dict(before=mt0.get(n), after=mt1.get(n), delta=mt1[n] - mt0[n])
                        for n in ('sample_count', 'module_time_ms', 'module_missing', 'module_duplicates',
                                  'module_restarts', 'integration_breaks', 'checksum_errors', 'length_errors',
                                  'uart_errors', 'packet_timeouts') if n in mt0 and n in mt1}
            transitions.append(dict(epoch=epoch, last_false_sequence=last['seq'], first_true_sequence=seq,
                                    last_false_uptime_ms=last['uptime'], first_true_uptime_ms=item['row']['uptime_ms'],
                                    false_info_line=last['line'], true_info_line=item['line'],
                                    first_true_primary_missing='a579' not in group, counters=counters))
        last = dict(seq=seq, active=active, uptime=item['row']['uptime_ms'], line=item['line'])

    names = ['acg720_ano_port.v', 'core/flight_core.v', 'core/height_loss_fallback.v',
             'core/ano_flight_state.v', 'core/ano_attitude_estimator.v', 'core/imu_pipeline_pipelined.v',
             'sensor/mtf01p_reader.v', 'sensor/mtf_shared_geometry.v', 'position/pose_time_adapter.v',
             'position/mtf_shared_height_fusion.v', 'mtf_xyz_navigation_control.v']
    sources = {}
    diffs = []
    for name in names:
        a, b = OLD / name, NEW / name
        sources[name] = dict(p005_sha256=sha(a), b3_sha256=sha(b), byte_identical=a.read_bytes() == b.read_bytes())
        if not sources[name]['byte_identical']:
            diffs += list(difflib.unified_diff(a.read_text(encoding='utf8').splitlines(True),
                                             b.read_text(encoding='utf8').splitlines(True),
                                             fromfile='P005/' + name, tofile='B3/' + name))
    (HERE / 'height_chain_source_changes.diff').write_text(''.join(diffs), encoding='utf8')
    anchors = []
    for seq in (227, 230, 231, 232, 374, 375):
        group = groups[(22, seq)]
        mt, nav = group['a581']['row'], group['a582']['row']
        anchors.append(dict(sequence=seq, mtf_line=group['a581']['line'], nav_line=group['a582']['line'],
                            source_age_ms=mt['source_age_ms'], mtf_samples=mt['sample_count'],
                            geometry_publications=nav['navigation_sequence'],
                            counter_difference=mt['sample_count'] - nav['navigation_sequence'],
                            geometry_height_ready=nav['native_height_ready']))
    write('packet_evidence.json', dict(scope='Exact-key frozen packet analysis; no invented high-rate samples',
          input=dict(path=str(CLIP), sha256=sha(CLIP)), protocol_counts=dict(protocols), duplicate_protocol_keys=duplicates,
          transition_brackets=transitions, geometry_counter_anchors=anchors, source_comparison=sources))
    print(json.dumps(dict(derived_rows=len(selected), transition_brackets=transitions,
                         height_chain_byte_identical=[n for n, v in sources.items() if v['byte_identical']]), indent=2))


if __name__ == '__main__':
    main()
