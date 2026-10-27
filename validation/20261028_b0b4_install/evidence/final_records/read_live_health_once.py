"""Ten-second read-only HTTP observation; never opens serial or sends a query."""
from pathlib import Path
from datetime import datetime, timezone
import json, time, urllib.request

HERE=Path(__file__).resolve().parent
samples=[]
for _ in range(40):
    row={'utc':datetime.now(timezone.utc).isoformat()}
    try:
        with urllib.request.urlopen('http://127.0.0.1:8765/api/state',timeout=4) as response: value=json.load(response)
        data=value.get('data') or {}; info=value.get('flight_info') or {}; imu=value.get('imu_diagnostic') or {}
        row.update(status=value.get('status'),fresh=value.get('fresh'),sequence=value.get('sequence'),
                   info_sequence=info.get('sequence'),uptime_ms=info.get('uptime_ms'),
                   raw_count=imu.get('raw_count'),accepted_count=imu.get('accepted_count'),pose_count=imu.get('pose_count'),
                   imu_fresh=value.get('imu_diagnostic_fresh'),armed=data.get('armed'),controller_enabled=data.get('controller_enabled'),
                   physical_output_active=data.get('physical_output_active'),pwm_us=data.get('pwm_us'),
                   range_valid=data.get('range_valid'),flow_valid=data.get('flow_valid'))
    except (OSError, ValueError) as exc: row['error_type']=type(exc).__name__
    samples.append(row);time.sleep(.25)
fresh=[row for row in samples if row.get('fresh') is True and type(row.get('uptime_ms')) is int]
report=dict(schema='b0b4.readonly-live-window.v1',hardware_writes=False,http_query_or_set=False,samples=samples,
            total_samples=len(samples),live_samples=len(fresh),nonfresh_samples=len(samples)-len(fresh),
            observed_uptime_regressions=sum(last['uptime_ms']<first['uptime_ms'] for first,last in zip(fresh,fresh[1:])),
            observed_activity=any(any(row.get(k) is True for k in ('armed','controller_enabled','physical_output_active')) for row in samples),
            first=fresh[0] if fresh else None,last=fresh[-1] if fresh else None,flight_ready=False)
(HERE/'post_cold_live_window.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps({key:value for key,value in report.items() if key!='samples'},indent=2))
