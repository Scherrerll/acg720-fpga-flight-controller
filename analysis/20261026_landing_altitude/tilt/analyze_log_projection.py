"""Derived pose projections from a frozen, same-key telemetry table; no plant proof."""
from pathlib import Path
import csv
import hashlib
import json
import math

OUT = Path(__file__).resolve().parent
REPO = OUT.parents[2]
TABLE = OUT.parent / 'logs/joined_rows.csv'
RAW = REPO / 'out/landing_altitude_20261026/snapshot_0253Z/recent_telemetry.jsonl'
EXPECTED = 'c46a8f81344b5af33060c216fd0446383a6b65c477680b73e0668d7df18b469c'
P2 = Path('C:/Users/ScherrerL/Desktop/apple/handoff_xy_pi_runtime_20261026/workspace_snapshot/reference_ano/quadrotor_tm_v1_20261012/Quadrotor_TM_V1')
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    original = json.loads((OUT / 'tilt_math_results.json').read_text())['source_inputs']
    paths = [Path(p) for p in original]
    paths += [P2 / p for p in ('SRC/fc_general/Ano_Pid.c', 'SRC/fc_specific/Ano_AttCtrl.c',
         'Driver/Drv_PwmOut.c', 'Application/Ano_Parameter.c', 'SRC/fc_specific/Ano_FlightCtrl.c')]
    paths += [TABLE, RAW]
    before = {str(p): {'sha256': sha(p), 'bytes': p.stat().st_size} for p in paths}
    assert before[str(RAW)]['sha256'] == EXPECTED
    assert all(before[p] == item for p, item in original.items())
    with TABLE.open(encoding='utf-8-sig', newline='') as f:
        rows = [r for r in csv.DictReader(f) if r['epoch'] == '8']
    report = []
    samples = []
    for first, last in ((3579, 3595), (3602, 3610), (4041, 4282), (4259, 4282)):
        selected = [r for r in rows if first <= int(r['sequence']) <= last]
        paired = [r for r in selected if all(r[k] == 'True' for k in
            ('paired_primary', 'paired_info', 'paired_nav', 'paired_mtf', 'paired_accel', 'paired_imu'))]
        projection = []
        pulse_delta = []
        for r in paired:
            roll, pitch = (float(r[k]) / 100 for k in ('roll_cdeg', 'pitch_cdeg'))
            fraction = math.cos(math.radians(roll)) * math.cos(math.radians(pitch))
            avg = sum(float(r[f'physical_m{n}_us']) for n in range(1,5)) / 4
            delta = avg - float(r['z_collective_us'])
            projection.append(100 * (1-fraction)); pulse_delta.append(delta)
            samples.append(dict(window=f'{first}-{last}', epoch=8, sequence=int(r['sequence']),
                utc=r['utc'], actual_roll_deg=roll, actual_pitch_deg=pitch,
                ideal_vertical_force_deficit_percent=100*(1-fraction),
                z_collective_us=int(r['z_collective_us']), physical_pwm_mean_us=avg,
                pwm_mean_minus_z_collective_us=delta))
        ranges = {k: [min(float(r[k]) for r in paired), max(float(r[k]) for r in paired)]
            for k in ('roll_cdeg','pitch_cdeg','fused_vz_mmps','world_az_up_mmps2',
                      'target_height_mm','fused_height_mm','raw_distance_mm','ch3')}
        report.append(dict(first=first,last=last,all_groups=len(selected),all_six_packet_groups=len(paired),
            nav_groups=sum(r['paired_nav']=='True' for r in selected),
            nav_at1850=sum(r['paired_nav']=='True' and r['z_collective_us']=='1850' for r in selected),
            first_utc=selected[0]['utc'],last_utc=selected[-1]['utc'],ranges=ranges,
            force_deficit_percent_range=[min(projection),max(projection)],
            physical_pwm_mean_minus_z_collective_us_range=[min(pulse_delta),max(pulse_delta)],
            groups_with_motor_touching_2000=sum(r['motor_at_run_max']=='True' for r in paired),
            fallback_true=sum(r['fallback']=='True' for r in paired)))
    assert report[0]['all_six_packet_groups'] == 17
    assert report[2]['nav_groups'] == report[2]['nav_at1850'] == 242
    assert report[3]['all_six_packet_groups'] == 24
    after = {str(p): {'sha256': sha(p), 'bytes': p.stat().st_size} for p in paths}
    assert before == after
    with (OUT / 'log_projection_samples.csv').open('w', encoding='utf-8-sig', newline='') as f:
        writer=csv.DictWriter(f, fieldnames=list(samples[0])); writer.writeheader(); writer.writerows(samples)
    result = dict(passed=True,scope=__doc__,source_inputs=before,source_inputs_unchanged=True,windows=report)
    (OUT / 'log_projection_results.json').write_text(json.dumps(result,indent=2),encoding='utf8')
    print(json.dumps(dict(passed=True,windows=report),indent=2))

if __name__ == '__main__':
    main()
