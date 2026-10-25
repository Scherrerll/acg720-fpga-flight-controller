"""Focused B0B1 passive-tap proof; temporary products stay in repo/out/B0B1/tap."""
from pathlib import Path
import argparse, hashlib, json, os, re, shutil, subprocess

ROOT = Path(__file__).resolve().parents[1]
OWNED = ["imu_pipeline_pipelined.v", "imu_temporal_check_pipelined.v",
         "imu_checked_guard_pipelined.v", "ano_attitude_estimator.v"]

def tokens(text):
    text = re.sub(r"//[^\n]*|/\*.*?\*/", "", text, flags=re.S)
    return re.findall(r"\w+|[^\s]", text)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--iverilog")
    ap.add_argument("--baseline", type=Path, default=ROOT.parent / "B0B0/source_snapshot")
    args = ap.parse_args()
    manifest = json.loads((ROOT / "baseline.json").read_text())
    baseline = args.baseline.resolve()
    for relative, expected in manifest["source_sha256"].items():
        actual = hashlib.sha256((baseline / relative).read_bytes()).hexdigest()
        assert actual == expected, f"frozen baseline hash mismatch: {relative}"
    result = {"baseline_hashes_verified": len(manifest["source_sha256"]),
              "baseline": str(baseline), "control_token_equivalence": {}}
    for name in OWNED:
        original = (baseline / "core" / name).read_text()
        changed = (ROOT / "source/core" / name).read_text()
        stripped = re.sub(r"// DIAG_TAP_BEGIN\n.*?// DIAG_TAP_END\n", "", changed, flags=re.S)
        assert tokens(original) == tokens(stripped), f"control source changed: {name}"
        result["control_token_equivalence"][name] = True
    # This proves the complete original token stream survives unchanged after
    # deleting diagnostic-only ports, taps and classification assignments.
    exe = args.iverilog or shutil.which("iverilog")
    if not exe:
        exe = str(Path.home() / "Desktop/apple/.tools/iverilog/app/bin/iverilog.exe")
    vvp = str(Path(exe).with_name("vvp.exe" if os.name == "nt" else "vvp"))
    temp = ROOT.parents[1] / "out/B0B1/tap"
    temp.mkdir(parents=True, exist_ok=True)
    env = {**os.environ, **{key: str(temp) for key in ("TMP", "TEMP", "TMPDIR")}}
    out = temp / "tap_tb.vvp"
    subprocess.run([exe, "-g2012", "-s", "tap_tb", "-o", str(out),
                    str(ROOT / "tests/tap_tb.v"), str(ROOT / "source/core/imu_diagnostic_tap.v")],
                   check=True, env=env, cwd=ROOT)
    ran = subprocess.run([vvp, str(out)], check=True, env=env, cwd=ROOT,
                         capture_output=True, text=True)
    result["tap_simulation"] = ran.stdout.strip()
    for name, extra in [("tap_temporal_tb", ["imu_temporal_check_pipelined.v"]),
                        ("tap_estimator_tb", ["ano_attitude_estimator.v", "cordic_atan2.v"]),
                        ("tap_starvation_tb", ["imu_temporal_check_pipelined.v", "imu_checked_guard_pipelined.v", "imu_diagnostic_tap.v"])]:
        additional = []
        if name == "tap_estimator_tb":
            golden = (baseline / "core/ano_attitude_estimator.v").read_text()
            for module in ("ano_attitude_estimator", "ano_attitude_mul32", "ano_attitude_div64", "ano_attitude_sqrt64"):
                golden = re.sub(r"\b" + module + r"\b", "gold_" + module, golden)
            golden_path = temp / "gold_ano_attitude_estimator.v"
            golden_path.write_text(golden)
            additional.append(golden_path)
        product = temp / (name + ".vvp")
        subprocess.run([exe, "-g2012", "-s", name, "-o", str(product),
                        str(ROOT / "tests" / (name + ".v")),
                        *[str(ROOT / "source/core" / item) for item in extra], *map(str, additional)],
                       check=True, env=env, cwd=ROOT)
        ran = subprocess.run([vvp, str(product)], check=True, env=env, cwd=ROOT,
                             capture_output=True, text=True)
        result[name] = ran.stdout.strip()
    sources = [ROOT / "source/core" / n for n in OWNED]
    sources += [ROOT / "source/core" / n for n in
                ("imu_diagnostic_tap.v", "bmi088_reader.v", "spi_uart_modules.v", "cordic_atan2.v")]
    subprocess.run([exe, "-g2012", "-s", "imu_pipeline", "-o", str(temp / "pipeline.vvp"),
                    *map(str, sources)], check=True, env=env, cwd=ROOT)
    result["pipeline_elaboration"] = "PASS"
    product = temp / "tap_pipeline_tb.vvp"
    subprocess.run([exe, "-g2012", "-s", "tap_pipeline_tb", "-o", str(product),
                    str(ROOT / "tests/tap_pipeline_tb.v"), *map(str, sources)],
                   check=True, env=env, cwd=ROOT)
    ran = subprocess.run([vvp, str(product)], check=False, env=env, cwd=ROOT,
                         capture_output=True, text=True)
    result["tap_pipeline_tb"] = ran.stdout.strip()
    result["source_sha256"] = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}
    (ROOT / "evidence/tap_tests.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    if ran.returncode:
        raise SystemExit(ran.returncode)

if __name__ == "__main__":
    main()
