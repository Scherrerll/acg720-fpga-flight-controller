"""Read-only verification of copied candidate and inherited workspace evidence."""
import hashlib
import json
from pathlib import Path

R = Path(__file__).resolve().parent
P = R / "B0B0_51_608MHz_verified"
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    m = json.loads((P / "manifest.json").read_text(encoding="utf8"))
    assert m["offline_candidate_verified"] and m["unrouted_nets"] == 0 and m["fmax_mhz"] >= 50
    assert m["constraint_period_ns"] <= 20 and len(m["pins"]) == 17
    for kind in ["setup", "hold"]:
        assert m["slack"][kind] == dict(tns_ns=0.0, violated_endpoints=0)
    for name, digest in m["copied_sha256"].items():
        assert sha(P / name) == digest, name
    for name, digest in m["logical_source_sha256"].items():
        assert sha(P / "source_snapshot" / name) == digest, name
    for name, digest in m["physical_inputs_sha256"].items():
        assert sha(P / "fixture" / name) == digest, name
    for name, digest in m["inherited_workspace_evidence_sha256"].items():
        assert sha(name) == digest, name
    assert sha(m["bitstream"]["path"]) == m["bitstream"]["sha256"]
    result = dict(passed=True, manifest_sha256=sha(P / "manifest.json"), copied_files=len(m["copied_sha256"]),
        source_files=len(m["logical_source_sha256"]), bound_workspace_evidence=len(m["inherited_workspace_evidence_sha256"]),
        fmax_mhz=m["fmax_mhz"], bitstream_sha256=m["bitstream"]["sha256"], hardware_accessed=False, flight_ready=False,
        verifier_sha256=sha(__file__))
    (R / "package_verification.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf8")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
