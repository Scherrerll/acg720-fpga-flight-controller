"""Read existing HTTP telemetry only; never opens serial or sends aircraft commands."""
import argparse
import datetime
import json
from pathlib import Path
import time
import urllib.request

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("label")
    a = p.parse_args()
    root = Path(__file__).resolve().parent / "bench/hardware"
    folder = root / (a.label + "_" + datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ"))
    folder.mkdir()
    (root / "active_capture.json").write_text(json.dumps(dict(folder=str(folder), label=a.label), indent=2))
    print(str(folder), flush=True)
    keys = ["status", "fresh", "sequence", "flight_info", "flight_info_fresh", "data", "mtf_sensor", "navigation", "mtf_fresh", "navigation_fresh", "height_loss_fallback_active", "stats", "receiver_profile", "serial_writes", "physical_pwm_is_live_measurement"]
    start = time.monotonic()
    with (folder / "samples.jsonl").open("w", encoding="utf8") as f:
        while time.monotonic() - start < 600 and not (folder / "STOP").exists():
            record = dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), elapsed_s=time.monotonic() - start)
            try:
                with urllib.request.urlopen("http://127.0.0.1:8767/api/state", timeout=3) as r:
                    state = json.load(r)
                record.update({k: state.get(k) for k in keys})
            except Exception as e:
                record["capture_error"] = str(e)
            f.write(json.dumps(record, separators=(",", ":"), ensure_ascii=False) + "\n")
            f.flush()
            time.sleep(.15)
    print("Read-only capture finished", flush=True)
