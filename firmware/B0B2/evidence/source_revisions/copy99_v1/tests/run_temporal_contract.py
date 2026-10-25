"""Isolated actual-stage timing/metadata/legacy-parameter contract proof.

No UART, hardware, place/route, or programmer is used. Guard/estimator behavior
belongs to the separate full policy-chain suite, not this narrow contract test.
"""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iverilog", type=Path)
    parser.add_argument("--vvp", type=Path)
    parser.add_argument("--output", type=Path, help="New output directory; never overwritten")
    args = parser.parse_args(argv)
    iv = args.iverilog or shutil.which("iverilog")
    if not iv:
        iv = REPO.parents[1] / ".tools" / "iverilog" / "app" / "bin" / ("iverilog.exe" if os.name == "nt" else "iverilog")
    iv = Path(iv).resolve()
    vvp = (args.vvp or iv.with_name("vvp.exe" if os.name == "nt" else "vvp")).resolve()
    if not iv.is_file() or not vvp.is_file():
        parser.error("provide installed iverilog/vvp executables")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    output = (args.output or REPO / "out/B0B2" / ("temporal_contract_" + stamp)).resolve()
    try:
        output.mkdir(parents=True, exist_ok=False)
    except FileExistsError:
        parser.error("output already exists; choose a new directory")
    source = ROOT / "source/core/imu_temporal_check_pipelined.v"
    bench = ROOT / "tests/temporal_contract_tb.v"
    inputs = {"temporal_stage.v": source, "temporal_contract_tb.v": bench}
    for name, original in inputs.items():
        (output / name).write_bytes(original.read_bytes())
    hashes = {name: digest(output / name) for name in inputs}
    product = output / "temporal_contract.vvp"
    env = {**os.environ, **{key: str(output) for key in ("TMP", "TEMP", "TMPDIR")}}
    compile_cmd = [str(iv), "-g2012", "-Wall", "-s", "temporal_contract_tb",
                   "-o", str(product), str(output / "temporal_contract_tb.v"),
                   str(output / "temporal_stage.v")]
    compiled = subprocess.run(compile_cmd, cwd=output, env=env, capture_output=True,
                              text=True, timeout=60)
    compile_log = compiled.stdout + compiled.stderr
    (output / "compile.log").write_text(compile_log, encoding="utf-8")
    run_code, simulation_log = None, ""
    if compiled.returncode == 0:
        run = subprocess.run([str(vvp), str(product)], cwd=output, env=env,
                             capture_output=True, text=True, timeout=60)
        run_code, simulation_log = run.returncode, run.stdout + run.stderr
    (output / "simulation.log").write_text(simulation_log, encoding="utf-8")
    match = re.search(r"TEMPORAL_CONTRACT_PASS cases=(\d+) checks=(\d+) publications=(\d+) cycles=(\d+)", simulation_log)
    stable = hashes == {name: digest(original) for name, original in inputs.items()}
    abi_warning = bool(re.search(r"parameter .*not found|parameter .*does not exist", compile_log, re.I))
    passed = bool(compiled.returncode == 0 and run_code == 0 and match
                  and int(match[1]) == 7 and int(match[3]) == 12 and stable and not abi_warning)
    result = dict(schema="b0b2.temporal-contract.v1", passed=passed, started_utc=stamp,
        hardware_accessed=False, serial_opened=False, flash_changed=False,
        flight_ready=False, programmable_receipt=False,
        output=str(output), compiler=str(iv), simulator=str(vvp), compile_command=compile_cmd,
        compiler_sha256=digest(iv), simulator_sha256=digest(vvp),
        compile_returncode=compiled.returncode, simulation_returncode=run_code,
        unknown_parameter_warning=abi_warning,
        input_sha256=hashes, source_stable_during_simulation=stable,
        runner_sha256=digest(Path(__file__)),
        coverage=dict(cases=int(match[1]), checks=int(match[2]), publications=int(match[3]),
                      cycles=int(match[4])) if match else None,
        case_markers=re.findall(r"CASE_PASS ([^\r\n]+)", simulation_log),
        limitations="Actual temporal stage only; no guard/estimator/dt/closed-loop qualification claimed",
        logs_sha256={name:digest(output/name) for name in ("compile.log", "simulation.log")})
    (output / "result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    evidence = ROOT / "evidence"
    evidence.mkdir(exist_ok=True)
    serialized = json.dumps(result, indent=2) + "\n"
    (evidence / ("temporal_contract_" + stamp + ".json")).write_text(serialized, encoding="utf-8")
    (evidence / "temporal_contract.json").write_text(serialized, encoding="utf-8")
    print(simulation_log, end="")
    if compile_log:
        print(compile_log, end="", file=sys.stderr)
    print(json.dumps(dict(passed=passed, evidence=str(evidence / "temporal_contract.json")), ensure_ascii=False))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
