"""Read-only replay of the predeclared B0B0 props-off correction criteria."""
import datetime as dt
import hashlib
import json
from pathlib import Path
import statistics as st
import struct

ROOT = Path(__file__).resolve().parent
SESSION = ROOT / 'bench/hardware/powered_direction_20261024T041227Z'
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
sgn = lambda x: (x > 0) - (x < 0)


def main():
    start = json.loads((SESSION/'start.json').read_text(encoding='utf-8-sig'))
    end = json.loads((SESSION/'end.json').read_text(encoding='utf-8-sig'))
    criteria = start['criteria']
    records = [json.loads(line) for line in (SESSION/'selected_telemetry.jsonl').read_text(encoding='utf-8-sig').splitlines()]
    protocols = {}
    bundles = {}
    for item in records:
        row = item['row']
        protocols.setdefault(row['_protocol'], []).append(row)
        bundles.setdefault(row['sequence'], {})[row['_protocol']] = item
    core = protocols['a579']
    active = [r for r in core if r['flags'] & 32]
    selected = {}
    selected_rows = []
    for axis, gyro in [('roll', 'gx_corrected'), ('pitch', 'gy_corrected')]:
        for sign in [-1, 1]:
            rows = [r for r in active
                    if all(criteria['select_centered_sticks_us'][0] <= r[k] <= criteria['select_centered_sticks_us'][1] for k in ['ch1','ch2','ch4'])
                    and r['ch7'] <= 1200
                    and sign*(r['target_'+axis+'_cdeg']-r[axis+'_cdeg']) >= criteria['minimum_steady_angle_error_cdeg']
                    and abs(r[gyro]) <= criteria['maximum_selected_axis_gyro_abs_counts']]
            def differential(r, prefix):
                m = [r[f'{prefix}m{i}_us'] for i in range(1,5)]
                return m[1]+m[2]-m[0]-m[3] if axis == 'roll' else m[0]+m[1]-m[2]-m[3]
            expect_diff_sign = -sign if axis == 'roll' else sign
            good_correction = sum(sgn(r[axis+'_us']) == sign for r in rows)
            good_cmd = sum(sgn(differential(r,'')) == expect_diff_sign for r in rows)
            good_pwm = sum(sgn(differential(r,'physical_')) == expect_diff_sign for r in rows)
            unsat = [r for r in rows if not r['flags'] & 128]
            selected[f'{axis}_error_{sign:+d}'] = dict(
                samples=len(rows), correction_sign_correct=good_correction,
                command_differential_sign_correct=good_cmd, reported_pwm_differential_sign_correct=good_pwm,
                unsaturated_samples=len(unsat),
                unsaturated_command_sign_correct=sum(sgn(differential(r,'')) == expect_diff_sign for r in unsat),
                unsaturated_reported_pwm_sign_correct=sum(sgn(differential(r,'physical_')) == expect_diff_sign for r in unsat),
                pose_range_deg=[min(r[axis+'_cdeg'] for r in rows)/100,max(r[axis+'_cdeg'] for r in rows)/100],
                correction_range_us=[min(r[axis+'_us'] for r in rows),max(r[axis+'_us'] for r in rows)],
                correction_median_us=st.median(r[axis+'_us'] for r in rows),
                command_differential_median_us=st.median(differential(r,'') for r in rows),
                reported_pwm_differential_median_us=st.median(differential(r,'physical_') for r in rows),
                sequences=[r['sequence'] for r in rows])
            selected_rows.extend(dict(axis=axis,error_sign=sign,sequence=r['sequence']) for r in rows)
    info = protocols['a580']; module = protocols['a581']; nav = protocols['a582']
    active_sequences = {r['sequence'] for r in active}
    active_info = [r for r in info if r['sequence'] in active_sequences]
    active_nav = [r for r in nav if r['sequence'] in active_sequences]
    payload_errors = []
    for r in module:
        p = bytes.fromhex(r['module_raw_hex'])
        ts, distance = struct.unpack_from('<II', p, 6)
        fx, fy = struct.unpack_from('<hh', p, 18)
        valid = r['range_provisionally_valid'] and distance>=80 and p[23]==1 and p[22]!=0
        checks = [len(p)==27, p[:4]==b'\xef\x0f\x00\x51', p[5]==20,
                  sum(p[:-1])%256==p[-1], ts==r['module_time_ms'], distance==r['distance_mm'],
                  fx==r['normalized_flow_x'], fy==r['normalized_flow_y'],p[22]==r['flow_quality'],
                  p[16]==r['tof_status'],p[23]==r['flow_status'],p[4]==r['module_sequence'],
                  r['vx_mmps_x100']==(fx*distance if valid else 0),
                  r['vy_mmps_x100']==(fy*distance if valid else 0)]
        if not all(checks): payload_errors.append(r['sequence'])
    changes = {k:core[-1][k]-core[0][k] for k in ['rejected_count','controller_fault_count','gate_interruption_count','gate_revoke_count']}
    module_changes = {k:module[-1][k]-module[0][k] for k in ['sample_count','checksum_errors','length_errors','uart_errors','packet_timeouts','module_missing','module_duplicates','module_restarts','integration_breaks']}
    active_times = [bundles[r['sequence']]['a579']['elapsed_s'] for r in active]
    pretilt = [bundles[r['sequence']] for r in active
               if 5 <= bundles[r['sequence']]['a579']['elapsed_s']-active_times[0] <= 25
               and 'a581' in bundles[r['sequence']] and 'a582' in bundles[r['sequence']]]
    pretilt_velocity = {}
    for protocol, keys, scale in [('a582',['fused_vx_q16','fused_vy_q16'],65536),
                                   ('a581',['vx_mmps_x100','vy_mmps_x100'],100)]:
        pretilt_velocity[protocol] = {k:dict(
            rms_mm_s=(sum((b[protocol]['row'][k]/scale)**2 for b in pretilt)/len(pretilt))**.5,
            max_abs_mm_s=max(abs(b[protocol]['row'][k]/scale) for b in pretilt)) for k in keys}
    stopped = end['state']['data']
    final_stopped = (not any(stopped[k] for k in ['armed','controller_enabled','physical_output_active'])
                     and stopped['command_us']==stopped['pwm_us']==[1000]*4
                     and stopped['rc_us'][2]<=1100 and stopped['rc_us'][4]<=1200)
    checks = dict(
        all_four_groups_sufficient=all(g['samples']>=criteria['minimum_stable_samples_each_error_sign'] for g in selected.values()),
        selected_correction_signs=all(g['correction_sign_correct']==g['samples'] for g in selected.values()),
        selected_command_differential_signs=all(g['command_differential_sign_correct']==g['samples'] for g in selected.values()),
        selected_reported_pwm_differential_signs=all(g['reported_pwm_differential_sign_correct']==g['samples'] for g in selected.values()),
        commands_and_reported_pwm_in_bounds=all(1000<=r[f'{p}m{i}_us']<=2000 for r in core for p in ['', 'physical_'] for i in range(1,5)),
        active_commands_and_reported_pwm_at_least_run_min=all(r[f'{p}m{i}_us']>=r['run_min_us'] for r in active for p in ['', 'physical_'] for i in range(1,5)),
        all_rc_calibrated_attitude_sensor_healthy=all(r['flags']&15==15 and r['imu_reason']==0 and r['attitude_fault']==0 for r in core),
        all_build_b0b0=all(r['build_id']==0xb0b0 for r in info),
        no_fpga_reset=all(b['uptime_ms']-a['uptime_ms']==200 for a,b in zip(info,info[1:])),
        no_controller_fault=changes['controller_fault_count']==0 and all(r['controller_fault']==0 for r in info),
        only_intended_swa_revoke=changes['gate_interruption_count']==0 and changes['gate_revoke_count']==1
                                and info[-1]['event_code']==52 and info[-1]['event_sensor_mask']==0
                                and info[-1]['event_imu_reason']==info[-1]['event_attitude_fault']==0,
        no_fallback=all(not r['height_loss_fallback_active'] for r in info),
        no_module_error_increments=all(v==0 for k,v in module_changes.items() if k!='sample_count'),
        all_module_fresh=all(r['link_valid'] and r['source_age_ms']<100 for r in module),
        all_height_velocity_ready=all(r['height_fusion_ready'] and r['velocity_fusion_ready'] for r in nav),
        swc_low_xy_inactive=all(r['ch7']<=1200 for r in active) and all(not r['xyz_active'] for r in active_nav),
        module_payloads_independently_match=not payload_errors,
        final_stopped=final_stopped)
    result = dict(utc=dt.datetime.now(dt.timezone.utc).isoformat(),
        passed=all(checks.values()), checks=checks,
        source_sha256={n:sha(SESSION/n) for n in ['start.json','end.json','selected_telemetry.jsonl']},
        script_sha256=sha(__file__), frame_counts={k:len(v) for k,v in protocols.items()},
        first_utc=records[0]['utc'],last_utc=records[-1]['utc'],active_samples=len(active),
        active_sample_span_s=active_times[-1]-active_times[0],sampling_period_ms=200,
        criteria=criteria,selected_groups=selected,
        selected_sample_sets_overlap_between_axes=True,
        mixer_saturated_active_samples=sum(bool(r['flags']&128) for r in active),
        command_reported_pwm_exact_match_active_samples=sum(all(r[f'm{i}_us']==r[f'physical_m{i}_us'] for i in range(1,5)) for r in active),
        telemetry_pwm_scope='FPGA-reported effective PWM; not external waveform, RPM or thrust measurement',
        core_counter_increments=changes,module_counter_increments=module_changes,
        module_payload_checks=len(module),payload_error_sequences=payload_errors,
        pretilt_observation=dict(selection='5..25 seconds after first enabled snapshot; observational, no acceptance threshold or independently confirmed fixed-camera constraint',
                                samples=len(pretilt),velocity=pretilt_velocity),
        active_info_samples=len(active_info),active_nav_samples=len(active_nav),
        active_height_control_samples=sum(r['vertical_active'] for r in active_nav),
        operator_confirmation=end['human'], firmware_changed=False,flash_changed=False,
        rotation_compensation_qualified=False,loaded_flight_accepted=False,flight_ready=False,
        limitations=['Actual powered duration exceeded requested short protocol; open-loop props-off holding and mixer saturation cannot qualify flight gains.',
                    'Pitch negative-error selection includes baseline pitch around +2deg as predeclared; all four deliberate poses are additionally visible in attitude trace.',
                    'SWC low: this verifies attitude correction and motor allocation, not active optical-flow XY behavior or exposure-aligned rotation compensation.'])
    (SESSION/'review.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:result[k] for k in ['passed','checks','frame_counts','active_samples','active_sample_span_s','mixer_saturated_active_samples','command_reported_pwm_exact_match_active_samples','core_counter_increments','module_counter_increments','active_height_control_samples']},ensure_ascii=False,indent=2))
    for k,g in selected.items():print(k,{a:b for a,b in g.items() if a!='sequences'})
    assert result['passed'], 'Review failed; preserve records and investigate before acceptance'


if __name__=='__main__':main()
