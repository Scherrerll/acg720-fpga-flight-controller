"""Bound a static-observation summary to the final 20 seconds of a saved log."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import statistics
import struct

sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()

def main(folder):
    folder=Path(folder)
    source=folder/"selected_telemetry.jsonl"
    records=[json.loads(line) for line in source.read_text(encoding="utf-8").splitlines()]
    checks=0;mismatches=[]
    for item in records:
        r=item["row"]
        if r["_protocol"]!="a581":continue
        checks+=1;b=bytes.fromhex(r["module_raw_hex"])
        t,d=struct.unpack_from("<II",b,6);x,y=struct.unpack_from("<hh",b,18)
        expected=dict(frame_size=len(b)==27,header=b[:4]==b"\xef\x0f\x00\x51",length=b[5]==20,
            checksum=sum(b[:-1])%256==b[-1],time=t==r["module_time_ms"],distance=d==r["distance_mm"],
            raw_x=x==r["normalized_flow_x"],raw_y=y==r["normalized_flow_y"],quality=b[22]==r["flow_quality"],
            tof_status=b[16]==r["tof_status"],flow_status=b[23]==r["flow_status"])
        valid=r["range_provisionally_valid"] and d>=80 and b[23]==1 and b[22]!=0
        expected.update(product_x=r["vx_mmps_x100"]==(x*d if valid else 0),product_y=r["vy_mmps_x100"]==(y*d if valid else 0))
        mismatches.extend(dict(sequence=r["sequence"],field=k) for k,v in expected.items() if not v)
    end=max(i["elapsed_s"] for i in records)
    tail=[i for i in records if i["elapsed_s"]>=end-20]
    g={}
    for i in tail:g.setdefault(i["row"]["_protocol"],[]).append(i["row"])
    m=g["a581"];c=g["a579"];n=g["a582"];p=g["a583"]
    seconds=(m[-1]["module_time_ms"]-m[0]["module_time_ms"])/1000
    delta=[(m[-1][k]-m[0][k])/100000 for k in ["x_mm_x100000","y_mm_x100000"]]
    def velocity(k):
        a=[i[k]/65536 for i in n];aa=sorted(abs(v) for v in a)
        return dict(median=statistics.median(a),rms=math.sqrt(sum(v*v for v in a)/len(a)),p95_abs=aa[int(len(aa)*.95)],max_abs=aa[-1])
    result=dict(utc=datetime.now(timezone.utc).isoformat(),scope="Final received 20-second window of the operator-confirmed stationary observation; receipt snapshots are 5 Hz, module cumulative integrals include accepted 100 Hz intervals.",
        source_sha256=sha(source),end_marker_sha256=sha(folder/"end.json"),script_sha256=sha(__file__),
        full_window_payload_checks=checks,payload_checks_passed=not mismatches,payload_mismatches=mismatches,
        duration_s=seconds,frames=len(m),module_packets=m[-1]["sample_count"]-m[0]["sample_count"],
        all_stopped=all(not(i["flags"]&(16|32)) and all(i[k]==1000 for k in ["m1_us","m2_us","m3_us","m4_us","physical_m1_us","physical_m2_us","physical_m3_us","physical_m4_us"]) for i in c),
        all_imu_healthy=all((i["flags"]&12)==12 and i["attitude_fault"]==0 for i in c),
        all_height_velocity_ready=all(i["height_fusion_ready"] and i["velocity_fusion_ready"] for i in n),
        module_counter_deltas={k:m[-1][k]-m[0][k] for k in ["checksum_errors","length_errors","uart_errors","packet_timeouts","module_missing","module_duplicates","module_restarts","integration_breaks"]},
        source_age_max_ms=max(i["source_age_ms"] for i in m),range_mm=[min(i["distance_mm"] for i in m),max(i["distance_mm"] for i in m)],
        quality=[min(i["flow_quality"] for i in m),max(i["flow_quality"] for i in m)],
        pose_ranges_deg={k:[min(i[k] for i in c)/100,max(i[k] for i in c)/100] for k in ["roll_cdeg","pitch_cdeg"]},
        module_delta_xy_mm=delta,module_mean_velocity_xy_mm_s=[d/seconds for d in delta],
        module_snapshot_nonzero_fraction=sum(i["normalized_flow_x"]!=0 or i["normalized_flow_y"]!=0 for i in m)/len(m),
        fused_velocity_mm_s={k:velocity(k) for k in ["fused_vx_q16","fused_vy_q16"]},
        gyro_rms_deg_s={k:math.sqrt(sum(i[k]**2 for i in p)/len(p)) for k in ["gx_deg_s","gy_deg_s","gz_deg_s"]},
        root_cause="undetermined; nonzero observations are present in committed raw module payloads, with matching numeric conversion",
        limits=["Cumulative position drift alone is not proof of a code fault; current ANO XY control uses fused velocity rather than this diagnostic position integral.",
                "No stationary-error acceptance envelope was specified in advance; this is an observation-quality comparison, not an invented binary threshold.",
                "Scene illumination, optics, and sensor power were not independently measured."],
        firmware_changed=False,factory_scale_changed=False,rotation_compensation_qualified=False,flight_ready=False)
    (folder/"static20_telemetry.jsonl").write_text("".join(json.dumps(i,ensure_ascii=False)+"\n" for i in tail),encoding="utf-8")
    (folder/"static20_review.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,indent=2));assert checks and not mismatches

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("folder");main(p.parse_args().folder)
