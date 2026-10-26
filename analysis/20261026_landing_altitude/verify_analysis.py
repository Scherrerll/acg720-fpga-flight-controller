"""Verify the finite investigation receipt; does not rerun simulation or access hardware."""
from pathlib import Path
import argparse
import hashlib
import json

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[1]


def check(path, expected):
    if not path.is_file():
        raise SystemExit(f"Missing input: {path}")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != expected:
        raise SystemExit(f"SHA256 mismatch: {path}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--external-inputs", action="store_true")
    args = parser.parse_args()
    check(ROOT / "MANIFEST.json", (ROOT / "MANIFEST.sha256").read_text(encoding="utf-8").split()[0])
    manifest = json.loads((ROOT / "MANIFEST.json").read_text(encoding="utf-8"))
    for item in manifest["files"]:
        check(ROOT / item["path"], item["sha256"])
    checked = 0
    if args.external_inputs:
        receipt = json.loads((ROOT / "INPUTS.json").read_text(encoding="utf-8"))
        for item in receipt["dependencies"]:
            path = Path(item["path"])
            check(path if path.is_absolute() else REPO / path, item["sha256"])
            checked += 1
        snapshot = receipt["telemetry_snapshot"]
        check(Path(snapshot["snapshot"]), snapshot["snapshot_sha256"])
        checked += 1
    print(json.dumps({"passed": True, "packaged_files": len(manifest["files"]),
                      "external_inputs_checked": checked,
                      "scope": "Byte receipt only; no simulation rerun or aircraft validation."}))


if __name__ == "__main__":
    main()
