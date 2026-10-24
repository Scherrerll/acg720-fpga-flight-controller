"""Run frozen scoped proofs with documented harness compatibility repairs.

Original source, prepared manifests, assertions, helpers and bindings stay unchanged.
Their sha helper accepts only Path, while JSON bindings contain str. The tilt
bench also uses output-port initializers unsupported by its Icarus compiler.
Only Path coercion and equivalent time-zero bench initialization are repaired.
Receipts bind original and effective executed scripts, plus proof outputs.
"""
from contextlib import redirect_stdout, redirect_stderr
import hashlib
import json
from pathlib import Path
import sys
import traceback

ROOT = Path(__file__).resolve().parent
HARDWARE = ROOT.parent / "routing_rescue_20261015/mtf01p_b0b0_synthesis_fix/hardware"
OUT = ROOT / "verification"
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
JOBS = [
    ("published_tilt4500_proposal", "run_proof.py", "proof.json"),
    ("control_ready_factoring_plan", "prove_factoring.py", "factoring_proof.json"),
    ("control_fine_velocity_factoring_plan", "prove_fine_velocity.py", "fine_velocity_proof.json"),
]


def main():
    sys.dont_write_bytecode = True
    OUT.mkdir(exist_ok=True)
    old_receipt = OUT / "execution_receipt.json"
    if old_receipt.exists() and not (OUT / "first_failed_execution_receipt.json").exists():
        (OUT / "first_failed_execution_receipt.json").write_bytes(old_receipt.read_bytes())
    receipt = dict(adapter_sha256=sha(__file__), repair="Path coercion str->Path; tilt bench port initializers expressed as equivalent initial block; all assertions/vectors retained", jobs=[], passed=False, hardware_accessed=False)
    for folder, name, proof_name in JOBS:
        script = HARDWARE / folder / "post_route_pending" / name
        source = script.read_text(encoding="utf8")
        assert source.count("sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()") == 1
        prepared = script.parent / "prepared_inputs.json"
        manifest = json.loads(prepared.read_text(encoding="utf8"))
        for p, digest in manifest["bindings"].items():
            assert sha(p) == digest, p
        effective = source.replace("sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()", "sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()")
        if folder == "published_tilt4500_proposal":
            old = "output reg signed[15:0]roll_cdeg=0,pitch_cdeg=0,output reg tilt4500_ok=1);"
            new = "output reg signed[15:0]roll_cdeg,pitch_cdeg,output reg tilt4500_ok);\\ninitial begin roll_cdeg=0;pitch_cdeg=0;tilt4500_ok=1;end"
            # Keep a real newline inside the generated Verilog triple-quoted string.
            new = new.replace("\\n", "\n")
            assert effective.count(old) == 1
            effective = effective.replace(old, new)
            bench = script.parent / "tb.v"
            archived = OUT / "tilt_bench_initial_syntax_failure.v"
            if bench.exists() and not archived.exists():
                archived.write_bytes(bench.read_bytes())
        executed = OUT / (folder + ".executed.py")
        executed.write_text(effective, encoding="utf8")
        item = dict(script=str(script), original_script_sha256=sha(script), executed_script=str(executed), executed_script_sha256=sha(executed), prepared_sha256=sha(prepared), log=str(OUT / (folder + ".adapted.log")), passed=False)
        receipt["jobs"].append(item)
        try:
            with Path(item["log"]).open("w", encoding="utf8") as log, redirect_stdout(log), redirect_stderr(log):
                ns = dict(__file__=str(script), __name__="frozen_scoped_proof_with_recorded_harness_repairs")
                exec(compile(effective, str(executed), "exec"), ns)
                ns["main"]()
            proof = script.parent / proof_name
            result = json.loads(proof.read_text(encoding="utf8"))
            assert result["status"].startswith("PASS")
            for p, digest in result["bindings"].items():
                assert sha(p) == digest, p
            for name, digest in result["evidence_hashes"].items():
                assert sha(script.parent / name) == digest, name
            item.update(passed=True, proof=str(proof), proof_sha256=sha(proof), log_sha256=sha(item["log"]), status=result["status"])
            print(folder + ": " + result["status"], flush=True)
        except Exception:
            item["error"] = traceback.format_exc()
            print(item["error"], flush=True)
            (OUT / "execution_receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf8")
            raise
    receipt["passed"] = True
    (OUT / "execution_receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf8")


if __name__ == "__main__":
    main()
