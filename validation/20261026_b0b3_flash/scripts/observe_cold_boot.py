"""Read-only HTTP observer; never opens serial or runs the programmer."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import json
import time
from flash_b0b3 import get, stopped, sha

HERE=Path(__file__).resolve().parent

def brief(value):
    data=value.get('data')or{};info=value.get('flight_info')or{};imu=value.get('imu_diagnostic')or{}
    return dict(sequence=value.get('sequence'),fresh=value.get('fresh'),uptime_ms=info.get('uptime_ms'),
                armed=data.get('armed'),controller_enabled=data.get('controller_enabled'),
                pwm_us=data.get('pwm_us'),rc_us=data.get('rc_us'),taking_off=info.get('taking_off'),
                raw_count=imu.get('raw_count'),pose_count=imu.get('pose_count'))

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--observe',action='store_true')
    args=parser.parse_args()
    if not args.observe:print('Use --observe only when ready for the operator power cycle.');return
    folder=HERE/'cold_boot';folder.mkdir(exist_ok=False)
    before=stopped(get('/api/state'));last_uptime=before['flight_info']['uptime_ms']
    report=dict(passed=False,physical_cold_boot_verified=False,operator_confirmation_required=True,
                observed_stale_or_offline=False,observed_uptime_reset=False,script_sha256=sha(Path(__file__)),
                started_utc=datetime.now(timezone.utc).isoformat(),before=brief(before),hardware_writes=False)
    (folder/'before.json').write_text(json.dumps(before,ensure_ascii=False,indent=2),encoding='utf-8')
    good=[];deadline=time.monotonic()+300;reset_seen=False
    try:
        with (folder/'samples.jsonl').open('w',encoding='utf-8')as stream:
            while time.monotonic()<deadline:
                try:
                    value=get('/api/state');entry=brief(value)
                    entry['utc']=datetime.now(timezone.utc).isoformat()
                    stream.write(json.dumps(entry,ensure_ascii=False)+'\n');stream.flush()
                    if value.get('fresh')is not True:
                        report['observed_stale_or_offline']=True;good=[]
                    else:
                        uptime=(value.get('flight_info')or{}).get('uptime_ms')
                        if type(uptime)is int:
                            if uptime<last_uptime:
                                reset_seen=True;report.update(observed_uptime_reset=True,first_new_boot=entry);good=[]
                            last_uptime=uptime
                        if reset_seen:
                            stopped(value)
                            data=value['data']
                            if all(data.get(k)is True for k in ('calibrated','attitude_valid','sensor_ok'))and value.get('imu_diagnostic_fresh'):
                                if not good or entry['sequence']!=good[-1]['sequence']:good.append(entry)
                                if len(good)>=10 and good[-1]['uptime_ms']>good[0]['uptime_ms']:
                                    for key in ('raw_count','pose_count'):
                                        assert type(good[-1][key])is int and good[-1][key]>good[0][key]
                                    report.update(passed=True,healthy_new_boot_samples=good,after=entry)
                                    break
                except (OSError,ValueError,KeyError)as exc:
                    report['last_wait_reason']=str(exc);good=[]
                time.sleep(.2)
            else:raise TimeoutError('No stable new boot observed within five minutes')
    except Exception as exc:
        report['error']=type(exc).__name__+': '+str(exc);raise
    finally:
        report['finished_utc']=datetime.now(timezone.utc).isoformat()
        (folder/'summary.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        print(json.dumps(report,ensure_ascii=False,indent=2),flush=True)

if __name__=='__main__':main()
