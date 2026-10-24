"""Record exactly 60 s of existing B0B0 fused telemetry; HTTP/file reads only."""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import statistics
import struct
import time
import urllib.request

ROOT=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
utc=lambda:datetime.now(timezone.utc).isoformat()

def dump(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

def read_state():
    with urllib.request.urlopen("http://127.0.0.1:8767/api/state",timeout=3) as response:
        s=json.load(response)
    s.pop("history",None)
    return s

def stopped(s):
    d=s["data"]
    return (s["fresh"] and s["flight_info_fresh"] and s["navigation_fresh"] and not s.get("demo")
        and s["flight_info"]["build_id"]==0xb0b0 and not d["armed"]
        and not d["controller_enabled"] and not d["physical_output_active"]
        and d["command_us"]==[1000]*4 and d["pwm_us"]==[1000]*4)

def main():
    s=read_state()
    assert stopped(s) and not s["serial_writes"] and s["recording"]["error"] is None
    assert s["navigation"]["height_fusion_ready"] and s["navigation"]["velocity_fusion_ready"]
    sid=s["recording"]["session_id"];assert Path(sid).name==sid
    log=ROOT.parent/"flight_logs"/sid/"telemetry.jsonl"
    folder=ROOT/"dynamic_validation"/("minute_"+datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"))
    folder.mkdir(parents=True)
    start_ms=s["navigation"]["fpga_uptime_ms"];target=start_ms+60000
    offset=max(0,log.stat().st_size-65536)
    dump(folder/"start.json",dict(utc=utc(),state=s,source_session=sid,source_offset=offset,
        start_nav_uptime_ms=start_ms,target_nav_uptime_ms=target,
        protocol="User requested one minute stationary fused-data observation; retain printed-paper scene and remain disarmed. No extra operator confirmation requested.",
        capture_script_sha256=sha(__file__),manifest_sha256=sha(ROOT/"B0B0_51_608MHz_verified/manifest.json"),
        scope="HTTP and ground-log reads only; no serial writes, firmware changes, motor operations or flight acceptance."))
    dump(ROOT/"dynamic_validation/active_minute.json",dict(folder=str(folder),status="capturing",utc=utc()))
    print(json.dumps(dict(folder=str(folder),status="started",target_seconds=60,start_nav_uptime_ms=start_ms)),flush=True)
    began=time.monotonic();half=False;polls=[]
    while True:
        s=read_state();elapsed=s["navigation"]["fpga_uptime_ms"]-start_ms
        polls.append(dict(utc=utc(),nav_uptime_ms=s["navigation"]["fpga_uptime_ms"],fresh=s["fresh"],
            stopped=bool(stopped(s)),module_age_ms=s["mtf_sensor"]["source_age_ms"],
            recording_error=s["recording"]["error"],source_session=s["recording"]["session_id"]))
        if not stopped(s) or s["recording"]["session_id"]!=sid or s["recording"]["error"] is not None:
            dump(folder/"aborted.json",dict(utc=utc(),state=s,polls=polls,reason="Live state/session guard interrupted the observation; no commands sent."))
            raise RuntimeError("Observation guard interrupted; data preserved")
        if elapsed>=30000 and not half:
            print(json.dumps(dict(status="halfway",elapsed_seconds=elapsed/1000,stopped=True)),flush=True);half=True
        if elapsed>=60000:break
        if time.monotonic()-began>70:raise TimeoutError("Navigation uptime did not advance through60s")
        time.sleep(.25)
    # Recorder flushes independently once per second. Do not mutate that service.
    time.sleep(1.25)
    end_offset=log.stat().st_size
    with log.open("rb") as f:f.seek(offset);data=f.read(end_offset-offset)
    records=[];partial=0
    for line in data.splitlines():
        try:records.append(json.loads(line))
        except (ValueError,UnicodeDecodeError):partial+=1
    nav=[x for x in records if x.get("row",{}).get("_protocol")=="a582" and start_ms<=x["row"]["fpga_uptime_ms"]<=target]
    nav.sort(key=lambda x:x["row"]["fpga_uptime_ms"])
    assert nav and nav[0]["row"]["fpga_uptime_ms"]==start_ms and nav[-1]["row"]["fpga_uptime_ms"]==target
    assert len({x["row"]["fpga_uptime_ms"] for x in nav})==len(nav)
    seq={x["row"]["sequence"] for x in nav}
    selected=[x for x in records if x.get("row",{}).get("sequence") in seq]
    source=folder/"selected_telemetry.jsonl"
    source.write_text("".join(json.dumps(x,ensure_ascii=False)+"\n" for x in selected),encoding="utf-8")
    n=[x["row"] for x in nav]
    m=[x["row"] for x in selected if x["row"]["_protocol"]=="a581"]
    c=[x["row"] for x in selected if x["row"]["_protocol"]=="a579"]
    info=[x["row"] for x in selected if x["row"]["_protocol"]=="a580"]
    d=[(n[-1][k]-n[0][k])/256 for k in ["position_x_q8","position_y_q8"]]
    radius=[math.hypot((x["position_x_q8"]-n[0]["position_x_q8"])/256,(x["position_y_q8"]-n[0]["position_y_q8"])/256) for x in n]
    peak=max(range(len(radius)),key=radius.__getitem__)
    velocities={}
    for k in ["fused_vx_q16","fused_vy_q16"]:
        v=[x[k]/65536 for x in n];av=sorted(abs(x) for x in v)
        velocities[k]=dict(mean_mm_s=statistics.mean(v),median_mm_s=statistics.median(v),
            rms_mm_s=math.sqrt(statistics.mean(x*x for x in v)),p95_abs_mm_s=av[int(len(av)*.95)],max_abs_mm_s=av[-1])
    mismatch=[]
    for x in m:
        b=bytes.fromhex(x["module_raw_hex"]);t,dist=struct.unpack_from("<II",b,6);fx,fy=struct.unpack_from("<hh",b,18)
        valid=x["range_provisionally_valid"] and dist>=80 and b[23]==1 and b[22]!=0
        ok=(len(b)==27 and b[:4]==b"\xef\x0f\x00\x51" and b[5]==20 and sum(b[:-1])%256==b[-1]
            and t==x["module_time_ms"] and dist==x["distance_mm"] and fx==x["normalized_flow_x"] and fy==x["normalized_flow_y"]
            and x["vx_mmps_x100"]==(fx*dist if valid else 0) and x["vy_mmps_x100"]==(fy*dist if valid else 0))
        if not ok:mismatch.append(x["sequence"])
    checkpoints=[]
    for sec in range(0,61,10):
        row=min(n,key=lambda x:abs(x["fpga_uptime_ms"]-(start_ms+sec*1000)))
        dx=(row["position_x_q8"]-n[0]["position_x_q8"])/256;dy=(row["position_y_q8"]-n[0]["position_y_q8"])/256
        checkpoints.append(dict(seconds=(row["fpga_uptime_ms"]-start_ms)/1000,x_mm=dx,y_mm=dy,net_mm=math.hypot(dx,dy)))
    result=dict(utc=utc(),duration_s=(n[-1]["fpga_uptime_ms"]-n[0]["fpga_uptime_ms"])/1000,
        frames=len(n),protocol_counts=dict(Counter(x["row"]["_protocol"] for x in selected)),
        source_session=sid,source_offset=[offset,end_offset],source_sha256=sha(source),partial_boundary_lines_skipped=partial,
        fused_position_delta_xy_mm=d,fused_position_net_mm=math.hypot(*d),fused_position_net_cm=math.hypot(*d)/10,
        fused_position_max_excursion_mm=radius[peak],max_excursion_time_s=(n[peak]["fpga_uptime_ms"]-start_ms)/1000,
        fused_velocity=velocities,checkpoints=checkpoints,
        position_valid_all=all(x["position_accumulator_ready"] and x["nav_position_reason"]==0 for x in n),
        velocity_valid_all=all(x["velocity_fusion_ready"] for x in n),height_valid_all=all(x["height_fusion_ready"] for x in n),
        all_stopped=all(not(x["flags"]&(16|32)) and all(x[k]==1000 for k in ["m1_us","m2_us","m3_us","m4_us","physical_m1_us","physical_m2_us","physical_m3_us","physical_m4_us"]) for x in c),
        build_ids=sorted({x["build_id"] for x in info}),
        pose_ranges_deg={k:[min(x[k] for x in c)/100,max(x[k] for x in c)/100] for k in ["roll_cdeg","pitch_cdeg"]},
        module_age_max_ms=max(x["source_age_ms"] for x in m),module_packets=m[-1]["sample_count"]-m[0]["sample_count"],
        module_range_mm=[min(x["distance_mm"] for x in m),max(x["distance_mm"] for x in m)],
        module_quality=[min(x["flow_quality"] for x in m),max(x["flow_quality"] for x in m)],
        module_counter_deltas={k:m[-1][k]-m[0][k] for k in ["checksum_errors","length_errors","uart_errors","packet_timeouts","module_missing","module_duplicates","module_restarts","integration_breaks"]},
        core_counter_deltas={k:c[-1][k]-c[0][k] for k in ["rejected_count","controller_fault_count","gate_interruption_count","gate_revoke_count"]},
        raw_payloads_checked=len(m),raw_payload_mismatches=mismatch,
        http_guard_samples=len(polls),all_http_guards_stopped=all(x["stopped"] for x in polls),
        scope="One actual60s stationary unarmed observation; fused position is a velocity integral, not airborne position truth. No serial writes or sensor/firmware changes.",
        flight_ready=False,firmware_changed=False,factory_scale_changed=False)
    dump(folder/"guard_polls.json",polls);dump(folder/"end_state.json",s);dump(folder/"review.json",result)
    dump(ROOT/"dynamic_validation/active_minute.json",dict(folder=str(folder),status="complete",utc=utc(),review_sha256=sha(folder/"review.json")))
    print(json.dumps(result,ensure_ascii=False,indent=2),flush=True)
    assert result["duration_s"]==60 and result["all_stopped"] and result["position_valid_all"] and result["velocity_valid_all"] and not mismatch

if __name__=="__main__":main()
