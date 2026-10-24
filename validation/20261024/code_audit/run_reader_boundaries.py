"""Run a read-only source-bound UART/metric test; no serial hardware access."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT.parent / "B0B0_51_608MHz_verified/source_snapshot/sensor/mtf01p_reader.v"
BIN = ROOT.parents[1] / ".tools/iverilog/app/bin"
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()

def main():
    manifest = ROOT.parent / "B0B0_51_608MHz_verified/manifest.json"
    expected = json.loads(manifest.read_text(encoding="utf-8"))["logical_source_sha256"]["sensor/mtf01p_reader.v"]
    assert sha(SOURCE) == expected
    env = dict(os.environ)
    env["PATH"] = str(BIN) + os.pathsep + env.get("PATH", "")
    env["TEMP"] = env["TMP"] = str(ROOT)
    commands = [
        [str(BIN / "iverilog.exe"), "-g2012", "-s", "reader_boundaries", "-o", str(ROOT / "reader_boundaries.vvp"), str(ROOT / "reader_boundaries.v"), str(SOURCE)],
        [str(BIN / "vvp.exe"), str(ROOT / "reader_boundaries.vvp")],
    ]
    records = []
    for cmd in commands:
        proc = subprocess.run(cmd, cwd=ROOT, env=env, text=True, capture_output=True, timeout=45)
        records.append(dict(command=cmd, returncode=proc.returncode, stdout=proc.stdout, stderr=proc.stderr))
        if proc.returncode:
            break
    passed = len(records) == 2 and all(r["returncode"] == 0 for r in records) and "PASS: 13" in records[-1]["stdout"]
    result = dict(utc=datetime.now(timezone.utc).isoformat(), passed=passed,
        source=str(SOURCE), source_sha256=sha(SOURCE), manifest_sha256=sha(manifest),
        bench_sha256=sha(ROOT / "reader_boundaries.v"), runner_sha256=sha(__file__),
        scope="Actual frozen UART/parser/metric source only; simulated 1 MHz clock with rounded 9-tick UART bits. No hardware operations or whole-top equivalence claim.", records=records)
    (ROOT / "reader_boundaries_result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    assert passed

if __name__ == "__main__":
    main()
