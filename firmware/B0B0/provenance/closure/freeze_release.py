"""Freeze the successful offline candidate; no hardware or flight approval."""
import hashlib
import json
from pathlib import Path
import shutil

R = Path(__file__).resolve().parent
H = R.parent / "routing_rescue_20261015/mtf01p_b0b0_synthesis_fix/hardware"
T = R / "fine_global_guardband195"
DEST = R / "B0B0_51_608MHz_verified"
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
read = lambda p: json.loads(Path(p).read_text(encoding="utf-8-sig"))


def main():
    evidence = {}

    def bind(p, expected=None):
        p = Path(p).resolve()
        digest = sha(p)
        assert expected is None or digest == expected, str(p)
        assert str(p) not in evidence or evidence[str(p)] == digest
        evidence[str(p)] = digest

    def bindings(mapping, base=None):
        for name, digest in mapping.items():
            bind(Path(base) / name if base else name, digest)

    result = read(T / "result.json")
    timing = read(T / "timing_audit.json")
    contract = read(T / "contract.json")
    assert result["feasibility_passed"] and result["routing_passed"] and result["timing_passed"] and timing["passed"]
    assert result["fmax_mhz"] == 51.608 and result["unrouted_nets"] == 0 and len(result["pins"]) == 17
    assert timing["constraint_period_ns"] == 19.5 and timing["timing_exceptions_added"] is False
    assert result["contract_sha256"] == sha(T / "contract.json")
    bind(contract["study_manifest"], contract["study_manifest_sha256"])
    study = read(contract["study_manifest"])
    source = Path(study["folder"])
    bindings(study["source_sha256"], source)
    bindings(study["evidence_sha256"], source)
    bindings(contract["inputs_sha256"], T / "fixture")
    bindings(result["actual_outputs_sha256"], T / "fixture")
    bindings(timing["evidence_sha256"])
    assert sha(T / "fixture/impl/gwsynthesis/acg720_ano_port.vg") == result["vg_sha256"] == study["proposed_vg_sha256"]
    for p in [T / "result.json", T / "timing_audit.json", T / "contract.json", R / "physical_refine.py", R / "audit_physical.py"]:
        bind(p)

    scope_file = H / "qualified_candidate_plan/scope_contract.pending.json"
    scope = read(scope_file)
    bind(scope_file)
    assert scope["source_context_review_complete"] and scope["independent_review_complete"]
    bind(scope["independent_review_record"], scope["independent_review_record_sha256"])
    bindings(scope["additional_scoped_evidence"])
    for edge in scope["source_context_edges"]:
        a, b = read(edge["parent_manifest"]), read(edge["child_manifest"])
        assert set(a["source_sha256"]) == set(b["source_sha256"])
        assert sorted(n for n in a["source_sha256"] if a["source_sha256"][n] != b["source_sha256"][n]) == sorted(edge["exact_changed_files"])
        bind(edge["parent_manifest"])
        bind(edge["child_manifest"])
        bindings(edge["scoped_evidence_sha256"])
    for name in scope["inherited_qualifications"]:
        q = read(name)
        assert q["offline_tests_passed"] is True
        bind(name)
        bindings(q["evidence_sha256"], Path(name).parent)

    receipt_path = R / "verification/execution_receipt.json"
    receipt = read(receipt_path)
    assert receipt["passed"] and len(receipt["jobs"]) == 3
    bind(receipt_path)
    bind(R / "run_scoped_proofs.py", receipt["adapter_sha256"])
    for job in receipt["jobs"]:
        assert job["passed"]
        bind(job["script"], job["original_script_sha256"])
        bind(job["executed_script"], job["executed_script_sha256"])
        bind(job["proof"], job["proof_sha256"])
        bind(job["log"], job["log_sha256"])
        proof = read(job["proof"])
        bindings(proof["bindings"])
        bindings(proof["evidence_hashes"], Path(job["proof"]).parent)

    stages = [Path(scope["source_context_edges"][-1]["child_manifest"])] + [
        H / "published_tilt4500_proposal/synthesis_only/20261024T005225_383171Z/study.json",
        H / "control_ready_factoring_plan/synthesis_only/20261024T013341_913278Z/study.json",
        source / "study.json",
    ]
    expected = [
        {"acg720_ano_port.v", "core/flight_core.v", "core/imu_pipeline_pipelined.v", "core/ano_attitude_estimator.v", "sensor/mtf_shared_geometry.v", "mtf_xyz_navigation_control.v"},
        {"sensor/mtf_shared_geometry.v", "position/mtf_shared_height_fusion.v", "mtf_xyz_navigation_control.v"},
        {"position/mtf_shared_height_fusion.v", "mtf_xyz_navigation_control.v"},
    ]
    for a, b, changed in zip(stages, stages[1:], expected):
        sa, sb = read(a)["source_sha256"], read(b)["source_sha256"]
        assert set(sa) == set(sb) and {n for n in sa if sa[n] != sb[n]} == changed
        bind(a)
        bind(b)
    assert read(stages[-1])["source_sha256"] == study["source_sha256"]

    assert not DEST.exists(), "Never overwrite a frozen candidate"
    DEST.mkdir()
    for name in study["source_sha256"]:
        target = DEST / "source_snapshot" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source / name, target)
    for name in set(contract["inputs_sha256"]) | set(result["actual_outputs_sha256"]):
        target = DEST / "fixture" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(T / "fixture" / name, target)
    for name in ["result.json", "timing_audit.json", "contract.json"]:
        shutil.copy2(T / name, DEST / name)
    shutil.copytree(R / "verification", DEST / "verification")
    (DEST / "DO_NOT_PROGRAM_WITHOUT_STOPPED_BENCH_STATE").write_text("Offline candidate only; no Flash or flight release.\n")
    copied = {str(p.relative_to(DEST)): sha(p) for p in DEST.rglob("*") if p.is_file()}
    manifest = dict(offline_candidate_verified=True, fmax_mhz=result["fmax_mhz"], constraint_period_ns=19.5,
        hardware_clock_mhz=50, unrouted_nets=0, slack=result["slack"], pins=result["pins"],
        bitstream=dict(path=str(DEST / "fixture/impl/pnr/acg720_ano_port.fs"), sha256=result["bitstream"]["sha256"]),
        logical_source_sha256=study["source_sha256"], physical_inputs_sha256=contract["inputs_sha256"],
        copied_sha256=copied, inherited_workspace_evidence_sha256=evidence,
        scope="Inherited source-bound regressions plus three changed-cone source/local producer proofs; physical STA independently audited. No new whole-top/whole-mapped or hardware flight claim.",
        harness_repairs=receipt["repair"], hardware_accessed=False, flash_changed=False, flight_ready=False,
        remaining=["Stopped startup and healthy-height physical PWM acceptance", "Height-loss/manual-pilot/latched-recovery/SWA stop checks", "Resolve historical loaded-flight power-loss before flight approval"],
        freeze_script_sha256=sha(__file__))
    (DEST / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf8")
    print(json.dumps(dict(offline_candidate_verified=True, destination=str(DEST), copied_files=len(copied), bound_workspace_evidence=len(evidence), bitstream_sha256=result["bitstream"]["sha256"], hardware_accessed=False)))


if __name__ == "__main__":
    main()
