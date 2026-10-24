"""Mark and extract existing read-only ground logs around an operator motion.

Never opens a serial port, sends commands, modifies firmware, or fits sensor gains.
The continuous ground logger records A583 receipt pairs at 5 Hz; they are not
exposure-aligned gyro integrals. This tool reports observation, not qualification.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import statistics
import urllib.request

ROOT = Path(__file__).resolve().parent
LOGS = ROOT.parent / "flight_logs"
OUT = ROOT / "dynamic_validation"
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
utc = lambda: datetime.now(timezone.utc).isoformat()

def dump(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

def state():
    with urllib.request.urlopen("http://127.0.0.1:8767/api/state", timeout=3) as response:
        s = json.load(response)
    s.pop("history", None)
    return s

def stopped(s):
    d = s["data"]
    return (s["fresh"] and s["flight_info_fresh"] and not s.get("demo")
        and s["flight_info"]["build_id"] == 0xB0B0
        and not d["armed"] and not d["controller_enabled"] and not d["physical_output_active"]
        and d["command_us"] == [1000]*4 and d["pwm_us"] == [1000]*4
        and d["rc_us"][2] <= 1100 and d["rc_us"][4] <= 1200 and d["rc_us"][6] <= 1200)

def start(axis):
    s = state()
    assert stopped(s), "Current telemetry does not confirm B0B0 and stopped low-switch state"
    assert not s["serial_writes"] and s["recording"]["error"] is None
    assert s["mtf_sensor"]["source_age_ms"] < 100 and s["mtf_fresh"] and s["navigation_fresh"]
    sid = s["recording"]["session_id"]
    assert Path(sid).name == sid
    log = LOGS / sid
    folder = OUT / (axis + "_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"))
    folder.mkdir(parents=True)
    marker = dict(utc=utc(), axis=axis, source_session=sid, telemetry_offset=(log/"telemetry.jsonl").stat().st_size,
        event_offset=(log/"events.jsonl").stat().st_size, raw_offset=(log/"raw.bin").stat().st_size,
        source_meta_sha256=sha(log/"meta.json"), state=s,
        manifest_sha256=sha(ROOT/"B0B0_51_608MHz_verified/manifest.json"),
        protocol=("Unarmed props-off fixed aircraft and textured floor, hands outside sensor field, static observation; no gain/offset fit." if axis=="static" else "Unarmed props-off small roll both ways; approximately fixed camera position, textured floor; no gain, offset, lever-arm or gyro compensation fit."),
        exposure_time_aligned=False, lever_arm="unknown; no remeasurement requested", flight_ready=False)
    dump(folder/"start.json", marker)
    dump(OUT/"active_motion.json", dict(folder=str(folder), axis=axis, status="awaiting_operator", utc=utc()))
    print(json.dumps(dict(folder=str(folder), source_session=sid, build="B0B0", stopped=True), ensure_ascii=False))

def span(values):
    return dict(min=min(values), median=statistics.median(values), max=max(values)) if values else None

def analyze(rows):
    groups = {}
    for record in rows:
        row = record.get("row", {})
        groups.setdefault(row.get("_protocol"), []).append(record)
    core = [r["row"] for r in groups.get("a579", [])]
    mtf = [r["row"] for r in groups.get("a581", [])]
    pairs = [r["row"] for r in groups.get("a583", [])]
    nav = [r["row"] for r in groups.get("a582", [])]
    info = [r["row"] for r in groups.get("a580", [])]
    result = dict(protocol_counts={k:len(v) for k,v in groups.items()},
        scope="Read-only received telemetry observation; hand pivot/translation and lever arm are not independently measured. A583 is not exposure synchronized.",
        factory_scale_changed=False, firmware_changed=False, rotation_compensation_qualified=False, flight_ready=False)
    if not core or not mtf:
        result["insufficient_data"] = True
        return result
    keys = ["m1_us","m2_us","m3_us","m4_us","physical_m1_us","physical_m2_us","physical_m3_us","physical_m4_us"]
    result["all_unarmed_and_reported_pwm1000"] = all(not (r["flags"] & (16|32)) and all(r[k] == 1000 for k in keys) for r in core)
    result["build_ids"] = sorted({r["build_id"] for r in info})
    result["pose_cdeg"] = {k:span([r[k] for r in core]) for k in ["roll_cdeg","pitch_cdeg","yaw_relative_cdeg"]}
    result["baseline_pose_cdeg"] = {k:statistics.median([r[k] for r in core[:15]]) for k in ["roll_cdeg","pitch_cdeg"]}
    result["end_pose_cdeg"] = {k:statistics.median([r[k] for r in core[-15:]]) for k in ["roll_cdeg","pitch_cdeg"]}
    result["core_counter_deltas"] = {k:core[-1][k]-core[0][k] for k in ["rejected_count","controller_fault_count","gate_interruption_count","gate_revoke_count"]}
    counters = ["checksum_errors","length_errors","uart_errors","packet_timeouts","module_missing","module_duplicates","module_restarts","integration_breaks"]
    result["module_counter_deltas"] = {k:mtf[-1][k]-mtf[0][k] for k in counters}
    result["module_range_mm"] = span([r["distance_mm"] for r in mtf])
    result["module_flow_quality"] = span([r["flow_quality"] for r in mtf])
    result["module_max_source_age_ms"] = max(r["source_age_ms"] for r in mtf)
    result["module_packets"] = mtf[-1]["sample_count"]-mtf[0]["sample_count"]
    result["cumulative_xy_mm"] = {}
    for k in ["x_mm_x100000","y_mm_x100000"]:
        vals=[r[k]/100000 for r in mtf]
        result["cumulative_xy_mm"][k] = dict(span_mm=max(vals)-min(vals),
            end_minus_start_mm=statistics.median(vals[-15:])-statistics.median(vals[:15]))
    result["receipt_pairs"] = dict(count=len(pairs), valid=sum(bool(p.get("receipt_pair_valid")) for p in pairs),
        gyro_deg_s={k:span([p[k] for p in pairs]) for k in ["gx_deg_s","gy_deg_s","gz_deg_s"]},
        factory_body_velocity_mm_s={k:span([p[k] for p in pairs]) for k in ["body_forward_mm_s","body_right_mm_s"]})
    result["fused_velocity_mm_s"] = {k:span([n[k]/65536 for n in nav]) for k in ["fused_vx_q16","fused_vy_q16"]}
    result["height_ready_fraction"] = sum(bool(n.get("height_fusion_ready")) for n in nav)/len(nav) if nav else None
    return result

def finish(folder, human):
    folder = Path(folder).resolve()
    assert folder.is_relative_to(OUT.resolve())
    start = json.loads((folder/"start.json").read_text(encoding="utf-8"))
    s = state()
    sid = start["source_session"]
    log = LOGS / sid
    end = dict(utc=utc(), human=human, telemetry_end=(log/"telemetry.jsonl").stat().st_size,
        event_end=(log/"events.jsonl").stat().st_size, state=s)
    assert s["recording"]["session_id"] == sid, "Receiver session changed; preserve markers and do not merge epochs"
    dump(folder/"end.json", end)
    with (log/"telemetry.jsonl").open("rb") as f:
        f.seek(start["telemetry_offset"])
        data = f.read(end["telemetry_end"]-start["telemetry_offset"])
    rows=[];bad=0
    for line in data.splitlines():
        try: rows.append(json.loads(line))
        except (ValueError, UnicodeDecodeError): bad+=1
    selected=folder/"selected_telemetry.jsonl"
    selected.write_text("".join(json.dumps(x,ensure_ascii=False)+"\n" for x in rows),encoding="utf-8")
    result=analyze(rows)
    result.update(utc=utc(), human=human, source_session=sid, source_offset=[start["telemetry_offset"],end["telemetry_end"]],
        skipped_partial_lines=bad, selected_telemetry_sha256=sha(selected), start_sha256=sha(folder/"start.json"),
        end_sha256=sha(folder/"end.json"), final_live_stopped=bool(stopped(s)))
    dump(folder/"review.json",result)
    active=OUT/"active_motion.json"
    if active.exists() and json.loads(active.read_text(encoding="utf-8")).get("folder")==str(folder):
        dump(active,dict(folder=str(folder),axis=start["axis"],status="complete",utc=utc(),review_sha256=sha(folder/"review.json")))
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    sub=parser.add_subparsers(dest="command",required=True)
    a=sub.add_parser("start");a.add_argument("axis",choices=["roll","pitch","static"])
    a=sub.add_parser("finish");a.add_argument("folder");a.add_argument("--human",required=True)
    args=parser.parse_args()
    start(args.axis) if args.command=="start" else finish(args.folder,args.human)
