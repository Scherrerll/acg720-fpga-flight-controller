"""Read-only USB/SiK observation of a human-operated battery-only cold boot.

This records an observed telemetry gap and new FPGA uptime. Actual removal of
all board power is a physical operator assertion, attached separately afterward.
No programmer, serial write, receiver restart, or motor operation is performed.
"""
import datetime as dt
import json
from pathlib import Path
import time
import urllib.request

ROOT=Path(__file__).resolve().parent
URLS={'usb':'http://127.0.0.1:8767/api/state','sik':'http://127.0.0.1:8765/api/state'}


def fetch(url):
    try:
        with urllib.request.urlopen(url,timeout=2) as response:return json.load(response)
    except (OSError,ValueError) as error:return dict(status='unavailable',fresh=False,error=repr(error))


def fresh(s):
    return bool(s.get('fresh') and s.get('flight_info_fresh') and (s.get('flight_info')or{}).get('build_id')==0xb0b0)


def stopped(s):
    d=s.get('data')or{};rc=d.get('rc_us')or[]
    return (fresh(s) and not any(d.get(k,True) for k in ['armed','controller_enabled','physical_output_active'])
            and d.get('pwm_us')==d.get('command_us')==[1000]*4 and len(rc)==8
            and 800<=rc[2]<=1100 and rc[4]<=1200 and rc[6]<=1200)


def healthy(s):
    d=s.get('data')or{};m=s.get('mtf_sensor')or{};n=s.get('navigation')or{};f=s.get('flight_info')or{}
    return (stopped(s) and all(d.get(k) for k in ['rc_valid','calibrated','attitude_valid','sensor_ok'])
            and m.get('link_valid') and m.get('source_age_ms',9999)<100 and s.get('navigation_fresh')
            and n.get('height_fusion_ready') and n.get('velocity_fusion_ready')
            and f.get('controller_fault')==0 and not f.get('height_loss_fallback_active'))


def summary(s):
    return {k:s.get(k) for k in ['status','fresh','flight_info_fresh','frame_age_ms','source','recording','flight_info',
                                'data','last_valid_diagnostics','mtf_sensor','navigation']}


def main():
    initial={name:fetch(url) for name,url in URLS.items()}
    assert all(healthy(s) for s in initial.values()), 'Both fresh B0B0 links with stopped healthy telemetry required before cold-boot marker'
    base_ms=initial['sik']['flight_info']['uptime_ms']
    assert base_ms>=20000, 'Wait for stable pre-test uptime >=20s'
    p=ROOT/'bench/hardware'/dt.datetime.now(dt.timezone.utc).strftime('cold_boot_%Y%m%dT%H%M%S_%fZ')
    p.mkdir(parents=True,exist_ok=False)
    start=dict(utc=dt.datetime.now(dt.timezone.utc).isoformat(),initial={k:summary(s) for k,s in initial.items()},
               source='HTTP read-only USB and SiK receivers',serial_writes=False,programmer_operations=False,
               criteria='Observed SiK telemetry absent >=3s, B0B0 new lower uptime, then >=30 unique healthy stopped snapshots spanning >=10s after uptime10s; USB stays offline during new healthy window; physical battery-only power cycle separately confirmed by operator')
    (p/'start.json').write_text(json.dumps(start,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (ROOT/'bench/hardware/active_cold_boot.json').write_text(json.dumps(dict(folder=str(p),status='recording'),indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(recording=True,folder=str(p),baseline_uptime_ms=base_ms)),flush=True)
    began=time.monotonic();gap_start=None;gap_duration=0;restart=None;good=[];unsafe=[];last_print=began
    result=dict(observed_restart=False,physical_power_cycle_human_confirmed=False,passed=False,flight_ready=False)
    try:
        with (p/'observations.jsonl').open('w',encoding='utf-8') as log:
            while time.monotonic()-began<600:
                now=time.monotonic();states={name:fetch(url) for name,url in URLS.items()};s=states['sik']
                entry=dict(utc=dt.datetime.now(dt.timezone.utc).isoformat(),elapsed_s=now-began,states={k:summary(v) for k,v in states.items()})
                log.write(json.dumps(entry,ensure_ascii=False)+'\n');log.flush()
                if not fresh(s):
                    if gap_start is None:gap_start=now
                    good=[]
                else:
                    if gap_start is not None:
                        gap_duration=max(gap_duration,now-gap_start);gap_start=None
                    uptime=s['flight_info']['uptime_ms']
                    if restart is None and gap_duration>=3 and uptime<base_ms-2000:
                        restart=dict(elapsed_s=now-began,uptime_ms=uptime,utc=entry['utc'])
                        print(json.dumps(dict(new_b0b0_restart=restart,prior_gap_s=gap_duration)),flush=True)
                    if restart is not None:
                        d=s.get('data')or{}
                        if any(d.get(k,False) for k in ['armed','controller_enabled','physical_output_active']) or d.get('pwm_us')!=[1000]*4:
                            unsafe.append(entry['utc'])
                            raise RuntimeError('Active motor state observed; operator must stop with SWA low')
                        if uptime>=10000 and healthy(s) and not states['usb'].get('fresh'):
                            if not good or uptime!=good[-1]['states']['sik']['flight_info']['uptime_ms']:good.append(entry)
                            if len(good)>=30 and good[-1]['elapsed_s']-good[0]['elapsed_s']>=10:
                                first=good[0]['states']['sik'];last=good[-1]['states']['sik']
                                errors={k:last['mtf_sensor'][k]-first['mtf_sensor'][k] for k in ['checksum_errors','length_errors','uart_errors','packet_timeouts','module_missing','module_duplicates','module_restarts','integration_breaks']}
                                diag_changes={k:last['last_valid_diagnostics'][k]-first['last_valid_diagnostics'][k] for k in ['controller_fault_count','gate_interruption_count','gate_revoke_count']}
                                assert not any(errors.values()) and not any(diag_changes.values()), 'Stable-window error counters changed'
                                result.update(observed_restart=True,restart=restart,gap_s=gap_duration,
                                              stable_unique_samples=len(good),stable_span_s=good[-1]['elapsed_s']-good[0]['elapsed_s'],
                                              stable_first_uptime_ms=first['flight_info']['uptime_ms'],stable_last_uptime_ms=last['flight_info']['uptime_ms'],
                                              module_error_increments=errors,core_fault_gate_increments=diag_changes,
                                              stable_new_module_packets=last['mtf_sensor']['sample_count']-first['mtf_sensor']['sample_count'],
                                              usb_offline_during_new_stable_window=True,
                                              after=last,software_observation_passed=True)
                                break
                        else:good=[]
                if now-last_print>=20:
                    print(json.dumps(dict(elapsed_s=round(now-began,1),sik_fresh=fresh(s),gap_s=round(gap_duration,1),restart_seen=restart is not None,healthy_unique_samples=len(good))),flush=True);last_print=now
                time.sleep(.25)
            else:raise TimeoutError('No complete cold-boot observation within ten minutes')
    except Exception as error:
        result['error']=repr(error)
        raise
    finally:
        result.update(utc=dt.datetime.now(dt.timezone.utc).isoformat(),folder=str(p),unsafe_observations=unsafe,
                      serial_writes=False,programmer_operations=False,physical_power_cycle_human_confirmed=False,flight_ready=False)
        (p/'capture_result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        (ROOT/'bench/hardware/active_cold_boot.json').write_text(json.dumps(dict(folder=str(p),status='software_observation_complete' if result.get('software_observation_passed') else 'incomplete'),indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k!='after'},ensure_ascii=False,indent=2),flush=True)


if __name__=='__main__':main()
