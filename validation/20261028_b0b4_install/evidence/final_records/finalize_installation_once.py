"""Combine immutable cold observations with the human power-cycle assertion, offline."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[1]
TARGET=REPO/'validation/20261028_b0b4_install/completion.json'
paths={
 'operator':HERE/'human_cold_boot_confirmation.json',
 'operator_current_power':HERE/'current_power_clarification.json',
 'cold':HERE/'cold_20261027T230359_351896Z/summary.json',
 'cold_samples':HERE/'cold_20261027T230359_351896Z/samples.jsonl',
 'cold_root':HERE/'root_cold_20261027T230359_148141Z/exit.json',
 'flash':HERE/'flash_20261027T225901_092572Z/stage_report.json',
 'flash_root':HERE/'root_flash_20261027T225900_901379Z/exit.json',
 'initial_post_cold_stale':HERE/'post_cold_current_state.json',
 'recovered':HERE/'post_cold_recovered_state.json',
 'live_window':HERE/'post_cold_live_window.json',
}
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def require(ok,why):
 if not ok:raise ValueError(why)
def load(path):return json.loads(path.read_text(encoding='utf-8-sig'))
values={key:load(path) for key,path in paths.items() if key!='cold_samples'}
cold=values['cold'];root=values['cold_root'];human=values['operator'];flash=values['flash']
for key in ('cold_root','flash_root'):
 value=values[key]
 require(value.get('normal_wait_return')is True and type(value.get('actual_p_wait'))is int and value['actual_p_wait']==0,'Actual root wait required: '+key)
 for stream in ('stdout','stderr'):
  path=paths[key].parent/(stream+'.log')
  require(sha(path)==value[stream+'_sha256'],'Root log changed')
require(root['script_sha256']=='c9b146a914a0f279a1319002f1812d458f40f81caea28ada3e3c200b1ff64225','Wrong observer')
require(all(cold.get(k)is True for k in ('passed','observed_stale_or_offline','uptime_reset','healthy_new_boot','default_GET')),'Cold observation incomplete')
require(cold.get('physical_cold_boot_verified')is False and cold.get('flight_ready')is False,'Original cold observation must remain unchanged')
require(all(flash.get(k)is True for k in ('passed','flash_written','flash_contents_certified','independent_flash_verify_passed')),'Flash certification incomplete')
require(values['flash_root']['stage_report_sha256']==sha(paths['flash']),'Flash root binding changed')
human_keys=('battery_disconnected','board_usb_disconnected','programmer_disconnected_from_board','all_board_leds_off_at_least_5_seconds',
            'battery_only_power_afterwards','board_stationary_after_power_on','computer_radio_kept_connected','ch3_ch5_ch7_kept_low')
require(human.get('source')=='Direct human reply to request_user_input_async' and human.get('answer')=='已按上述步骤完成' and all(human.get(k)is True for k in human_keys),'Human physical power-cycle facts missing')
samples=cold['healthy_new_boot_samples'];require(len(samples)==10,'Ten new boot samples required')
for row in samples:
 require(row['sequence']==row['info_sequence'] and row['fresh']is True and row['flight_info_fresh']is True,'Strict main/flight-info group required')
 require(all(row.get(k)is False for k in ('armed','controller_enabled','command_fresh','physical_output_active','taking_off')),'Stopped state required')
 require(row['pwm_us']==[1000]*4 and row['command_us']==[1000]*4,'Stopped outputs required')
 require(all(row.get(k)is True for k in ('calibrated','attitude_valid','sensor_ok','imu_diagnostic_fresh','rc_valid')),'Healthy sensor/RC required')
 require(all(type(row['rc_us'][k])is int and 800<=row['rc_us'][k]<=1100 for k in (2,4,6)),'Low switches required')
for first,last in zip(samples,samples[1:]):
 require(all(type(last[k])is int and last[k]>first[k] for k in ('uptime_ms','raw_count','accepted_count','pose_count')),'Healthy counters must progress')
query=cold['default_GET_result'];active=query['active']
require(query['epoch']!=cold['baseline_status']['epoch'] and query['operation_id']!=cold['baseline_status']['operation_id'] and query['result']['code']=='queried','New cold GET required')
require(active==dict(build='0000B0B4',p_wire=1000,i_wire=350,generation=0),'Cold defaults mismatch')
require(cold['baseline']['uptime_ms']>cold['first_new_boot']['uptime_ms'],'Uptime reset missing')
for original,digest in cold['prior_flash']['bound_inputs'].items():require(sha(Path(original))==digest,'Original Flash evidence changed')
window=values['live_window']
require(window['live_samples']==40 and window['nonfresh_samples']==0 and window['observed_uptime_regressions']==0 and window['observed_activity']is False,'Latest live window incomplete')
image=REPO/'firmware/B0B4/release/acg720_ano_port.fs';manifest=REPO/'firmware/B0B4/release_manifest.json'
require(sha(image)=='199bc466f8a8fe18e891600d18161babcea9c2495eee8d307dac62ac8646c610','Qualified image changed')
require(sha(manifest)=='c8e03412ff44cbe929f5d8ce6fed6eb3c61078a2028df466a340a61894893a2d','Frozen manifest changed')
result=dict(schema='b0b4.hardware-installation-completion.v1',recorded_utc=datetime.now(timezone.utc).isoformat(),
 scope='Props-off SRAM/Flash identity, independent Flash verify, human-confirmed complete power cycle and cold defaults/IMU only.',
 installation_passed=True,installed=True,sram_verified=True,flash_written=True,independent_flash_verified=True,
 physical_cold_boot_verified=True,physical_fact_basis='Direct operator assertion combined with immutable observed gap/new boot/default GET evidence',
 flight_ready=False,flight_qualified=False,radio_link_stability_qualified=False,
 image=dict(path=image.relative_to(REPO).as_posix(),sha256=sha(image)),release_manifest_sha256=sha(manifest),
 original_observation_unchanged=True,original_cold_observation_physical_flag=False,
 cold_proof=dict(baseline_uptime_ms=cold['baseline']['uptime_ms'],first_new_boot_uptime_ms=cold['first_new_boot']['uptime_ms'],
                 healthy_samples=10,healthy_uptime_start_ms=samples[0]['uptime_ms'],healthy_uptime_end_ms=samples[-1]['uptime_ms'],
                 query=query),
 latest_live_window=dict(total=40,live=40,uptime_regressions=0,activity=False),
 open_findings=['Range and flow remain invalid, also observed before programming B0B3.',
                'A post-cold telemetry receive gap occurred while the operator reports power/connection remained on; source still under read-only investigation.'],
 no_motor_unlock_or_flight_commands=True,no_parameter_SET=True,automatic_recovery_performed=False,
 evidence_inputs={key:dict(original_path=str(path),sha256=sha(path),bytes=path.stat().st_size) for key,path in paths.items()},
 archive_index='evidence/ARCHIVE_INDEX.json')
require(not TARGET.exists(),'Never overwrite a completion seal')
TARGET.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(installation_passed=True,physical_cold_boot_verified=True,flight_ready=False,path=str(TARGET),sha256=sha(TARGET))))
