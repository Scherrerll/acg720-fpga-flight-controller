"""Independent little-endian payload checks on the saved physical-motion data."""
import hashlib
import json
from pathlib import Path
import struct
import statistics
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent
SESSION = ROOT / "roll_20261024T033604Z"
SOURCE = SESSION / "selected_telemetry.jsonl"
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()

def main():
    records = [json.loads(line) for line in SOURCE.read_text(encoding="utf-8").splitlines()]
    groups = {}
    mismatches = []
    count = 0
    for item in records:
        r = item["row"]
        groups.setdefault(r["sequence"], {})[r["_protocol"]] = item
        if r["_protocol"] != "a581":
            continue
        count += 1
        packet = bytes.fromhex(r["module_raw_hex"])
        checks = dict(frame_size=len(packet)==27, header=packet[:4]==b"\xef\x0f\x00\x51",
            length=packet[5]==20, checksum=sum(packet[:-1])%256==packet[-1])
        timestamp, distance = struct.unpack_from("<II", packet, 6)
        fx, fy = struct.unpack_from("<hh", packet, 18)
        checks.update(timestamp=timestamp==r["module_time_ms"], distance=distance==r["distance_mm"],
            flow_x=fx==r["normalized_flow_x"], flow_y=fy==r["normalized_flow_y"],
            quality=packet[22]==r["flow_quality"], tof_status=packet[16]==r["tof_status"],
            flow_status=packet[23]==r["flow_status"], sequence=packet[4]==r["module_sequence"])
        eligible = r["range_provisionally_valid"] and distance>=80 and packet[23]==1 and packet[22]!=0
        checks.update(factory_velocity_x=r["vx_mmps_x100"]==(fx*distance if eligible else 0),
            factory_velocity_y=r["vy_mmps_x100"]==(fy*distance if eligible else 0))
        for k, ok in checks.items():
            if not ok:
                mismatches.append(dict(sequence=r["sequence"],check=k))
    aligned=[]
    for seq, bundle in groups.items():
        if all(k in bundle for k in ["a579","a581","a582","a583"]):
            c=bundle["a579"]["row"];m=bundle["a581"]["row"];n=bundle["a582"]["row"];a=bundle["a583"]["row"]
            aligned.append(dict(sequence=seq,elapsed_s=bundle["a579"]["elapsed_s"],
                roll_deg=c["roll_cdeg"]/100,pitch_deg=c["pitch_cdeg"]/100,yaw_deg=c["yaw_relative_cdeg"]/100,
                gyro_x_deg_s=a["gx_deg_s"],gyro_y_deg_s=a["gy_deg_s"],gyro_z_deg_s=a["gz_deg_s"],
                distance_mm=m["distance_mm"],module_x_mm=m["x_mm_x100000"]/100000,module_y_mm=m["y_mm_x100000"]/100000,
                factory_forward_mm_s=a["body_forward_mm_s"],factory_right_mm_s=a["body_right_mm_s"],
                fused_x_mm_s=n["fused_vx_q16"]/65536,fused_y_mm_s=n["fused_vy_q16"]/65536,
                quality=m["flow_quality"],height_ready=n["height_fusion_ready"],velocity_ready=n["velocity_fusion_ready"],
                sensor_ok=bool(c["flags"]&8),attitude_valid=bool(c["flags"]&4),attitude_fault=c["attitude_fault"]))
    aligned.sort(key=lambda r:r["elapsed_s"])
    t0=aligned[0]["elapsed_s"]
    for r in aligned:r["relative_s"]=r["elapsed_s"]-t0
    baseline=statistics.median([r["roll_deg"] for r in aligned[:15]])
    # Observational phase selection only, based on roll relative to the initial pose.
    phases={"positive_roll": [r for r in aligned if r["roll_deg"]-baseline>=2],
        "negative_roll": [r for r in aligned if r["roll_deg"]-baseline<=-2]}
    phase_summary={}
    for name, rows in phases.items():
        phase_summary[name]=dict(count=len(rows),time_range_s=[rows[0]["relative_s"],rows[-1]["relative_s"]],
            roll_range_deg=[min(r["roll_deg"] for r in rows),max(r["roll_deg"] for r in rows)],
            pitch_range_deg=[min(r["pitch_deg"] for r in rows),max(r["pitch_deg"] for r in rows)],
            yaw_span_deg=max(r["yaw_deg"] for r in rows)-min(r["yaw_deg"] for r in rows),
            module_xy_span_mm=[max(r[k] for r in rows)-min(r[k] for r in rows) for k in ["module_x_mm","module_y_mm"]])
    # Half-second-ish tail is insufficient for a baseline; keep a 3-second/15-frame endpoint.
    tail=aligned[-15:]
    result=dict(utc=datetime.now(timezone.utc).isoformat(),source_sha256=sha(SOURCE),script_sha256=sha(__file__),
        decoded_module_frames=count,independent_payload_checks_passed=not mismatches,mismatches=mismatches,
        aligned_received_snapshots=len(aligned),duration_s=aligned[-1]["relative_s"],
        all_sensor_ok=all(r["sensor_ok"] for r in aligned),all_attitude_valid=all(r["attitude_valid"] for r in aligned),
        all_attitude_fault_zero=all(r["attitude_fault"]==0 for r in aligned),
        all_height_ready=all(r["height_ready"] for r in aligned),all_velocity_ready=all(r["velocity_ready"] for r in aligned),
        phase_selection="Pose-relative +/-2 degrees for observation only; not independently marked pure-rotation phases.",phases=phase_summary,
        final_fused_velocity_mm_s={k:dict(median=statistics.median(r[k] for r in tail),max_abs=max(abs(r[k]) for r in tail)) for k in ["fused_x_mm_s","fused_y_mm_s"]},
        interpretation="Both roll directions and sensor continuity were observed. Whole-window translation/yaw from handling and unknown camera lever arm prevent isolating rotational optical flow. No correction coefficient or flight qualification inferred.",
        rotation_compensation_qualified=False,flight_ready=False)
    (SESSION/"aligned_samples.json").write_text(json.dumps(aligned,indent=2)+"\n",encoding="utf-8")
    (SESSION/"payload_and_phases.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,indent=2))
    assert count and not mismatches

if __name__=="__main__":main()
