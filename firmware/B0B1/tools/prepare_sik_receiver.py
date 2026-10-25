"""Prepare an isolated B0B1-compatible SiK receiver; never opens a serial port."""
from __future__ import annotations

import argparse
import datetime
import difflib
import hashlib
import json
import pathlib
import shutil
import tempfile

REPOSITORY = pathlib.Path(__file__).resolve().parents[3]
RECEIPT = "B0B1_PREPARATION_RECEIPT.json"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def file_hashes(root):
    return {str(p.relative_to(root).as_posix()): sha(p.read_bytes())
            for p in sorted(root.rglob("*"))
            if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc"}


def tree_hash(hashes):
    return sha(json.dumps(hashes, sort_keys=True, separators=(",", ":")).encode("utf-8"))


def prepare(output, repository=REPOSITORY):
    repository = pathlib.Path(repository).resolve()
    source = repository / "ground" / "B0B0"
    output = pathlib.Path(output).resolve()
    allowed = (repository / "out" / "B0B1").resolve()
    if output == allowed or not output.is_relative_to(allowed):
        raise ValueError("output must be a new child directory under repository/out/B0B1")
    if output.exists():
        raise FileExistsError(f"refusing to overwrite existing directory: {output}")
    if not source.is_dir() or not (repository / "support" / "bmi_dashboard.py").is_file():
        raise ValueError("expected frozen ground/B0B0 and repository support modules")
    source_hashes = file_hashes(source)
    if any(p.is_symlink() for p in source.rglob("*")):
        raise ValueError("source symlinks are not supported")
    output.parent.mkdir(parents=True, exist_ok=True)
    patches = {}
    with tempfile.TemporaryDirectory(prefix=".b0b1-sik-stage-", dir=output.parent) as temp:
        staged = pathlib.Path(temp) / "receiver"
        shutil.copytree(source, staged, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        if file_hashes(staged) != source_hashes:
            raise ValueError("source changed during copy")

        def replace(name, old, new, expected):
            path = staged / name
            before = path.read_bytes().decode("utf-8")
            if before.count(old) != expected:
                raise ValueError(f"unexpected source shape: {name}: {old!r}")
            after = before.replace(old, new)
            path.write_bytes(after.encode("utf-8"))
            patches.setdefault(name, [before, after])[1] = after

        replace("protocol.py", "ROOT=Path(__file__).resolve().parents[2]",
                "ROOT=next(p for p in Path(__file__).resolve().parents if (p/'support/bmi_dashboard.py').is_file())", 1)
        replace("protocol.py", "0xb0b0)", "0xb0b0,0xb0b1)", 5)
        replace("analysis.py", "0xb0b0)", "0xb0b0,0xb0b1)", 2)
        replace("nav_protocol.py", "0xb0b0: 5}", "0xb0b0: 5, 0xb0b1: 5}", 1)
        replace("nav_protocol.py", "0xb0b0: 2}", "0xb0b0: 2, 0xb0b1: 2}", 1)
        nav_text = (staged / "nav_protocol.py").read_bytes().decode("utf-8")
        nl = "\r\n" if "\r\n" in nav_text else "\n"
        replace("nav_protocol.py", "def firmware_label(build):",
                "def firmware_label(build):" + nl + "    if build==0xb0b1:" + nl +
                "        return 'B0B1 · 姿态链诊断候选 · 待验收'", 1)
        # Copied tests must not reuse the frozen receiver's old output directory.
        replace("test_system.py", "OUT=ROOT/'out/b0b0_ground_tests'",
                "OUT=Path(__file__).resolve().parent/'test_output'", 1)
        replace("test_mtf.py", "OUT=Path(__file__).resolve().parents[2]/'out/b0b0_ground_tests'",
                "OUT=Path(__file__).resolve().parent/'test_output'", 1)
        if file_hashes(source) != source_hashes:
            raise ValueError("frozen source changed while preparing receiver")
        output_hashes = file_hashes(staged)
        diffs = "".join("".join(difflib.unified_diff(before.splitlines(keepends=True),
                     after.splitlines(keepends=True), fromfile=f"ground/B0B0/{name}",
                     tofile=f"B0B1/sik_receiver/{name}"))
                     for name, (before, after) in sorted(patches.items()))
        receipt = dict(schema="b0b1.sik-receiver-preparation.v1",
            created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
            source=str(source), output=str(output),
            generator_sha256=sha(pathlib.Path(__file__).read_bytes()),
            source_files_sha256=source_hashes, source_tree_sha256=tree_hash(source_hashes),
            output_files_sha256=output_hashes, output_tree_sha256=tree_hash(output_hashes),
            patch_sha256=sha(diffs.encode("utf-8")), unified_patch=diffs,
            changed_files=sorted(patches),
            scope="B0B1 identity allowlists + B0B1 label + relocated support/test paths; wire fields and units unchanged",
            serial_opened=False, serial_writes=False,
            output_hash_scope="Files at preparation, excluding this receipt; later runtime/test outputs are separate")
        (staged / RECEIPT).write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding="utf-8")
        staged.rename(output)
    return receipt


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=pathlib.Path,
                        default=REPOSITORY / "out" / "B0B1" / "sik_receiver")
    args = parser.parse_args(argv)
    try:
        prepare(args.output)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    print(str((args.output.resolve() / RECEIPT)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
