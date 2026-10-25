"""Prepare an isolated B0B2-compatible SiK receiver; never opens a serial port."""
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
RECEIPT = "B0B2_PREPARATION_RECEIPT.json"


DASHBOARD_EXTENSION = "\n\nLegacyDashboard=Dashboard\nclass Dashboard(LegacyDashboard):\n    def __init__(self,port):\n        super().__init__(port)\n        self.imu_diagnostic=None;self.imu_diagnostic_time=None\n\n    def ingest(self,row):\n        if row.get('_protocol')=='a585':\n            with self.lock:\n                self.imu_diagnostic=dict(row);self.imu_diagnostic_time=self.clock()\n            return\n        if row.get('_protocol')=='a580':\n            with self.lock:\n                if self.info and (self.info['build_id']!=row['build_id'] or row['uptime_ms']<self.info['uptime_ms']):\n                    self.imu_diagnostic_time=None\n        super().ingest(row)\n\n    def connection(self,connected,error=None):\n        super().connection(connected,error)\n        if not connected:\n            with self.lock:self.imu_diagnostic_time=None\n\n    def clear_source(self,port):\n        super().clear_source(port)\n        with self.lock:self.imu_diagnostic=None;self.imu_diagnostic_time=None\n\n    def snapshot(self):\n        result=super().snapshot()\n        info=result.get('flight_info')\n        with self.lock:\n            row=dict(self.imu_diagnostic) if self.imu_diagnostic else None\n            fresh=bool(row and self.connected and self.imu_diagnostic_time is not None and\n                0<=self.clock()-self.imu_diagnostic_time<.5 and result.get('flight_info_fresh') and\n                isinstance(info,dict) and info.get('build_id')==row['build_id'] and\n                isinstance(info.get('uptime_ms'),int) and abs(info['uptime_ms']-row['uptime_ms'])<1000)\n        result.update(imu_diagnostic=row,imu_diagnostic_fresh=fresh)\n        return result\n"

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
    allowed = (repository / "out" / "B0B2").resolve()
    if output == allowed or not output.is_relative_to(allowed):
        raise ValueError("output must be a new child directory under repository/out/B0B2")
    if output.exists():
        raise FileExistsError(f"refusing to overwrite existing directory: {output}")
    if not source.is_dir() or not (repository / "support" / "bmi_dashboard.py").is_file():
        raise ValueError("expected frozen ground/B0B0 and repository support modules")
    source_hashes = file_hashes(source)
    if any(p.is_symlink() for p in source.rglob("*")):
        raise ValueError("source symlinks are not supported")
    output.parent.mkdir(parents=True, exist_ok=True)
    patches = {}
    with tempfile.TemporaryDirectory(prefix=".b0b2-sik-stage-", dir=output.parent) as temp:
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
        replace("protocol.py", "0xb0b0)", "0xb0b0,0xb0b2)", 5)
        replace("analysis.py", "0xb0b0)", "0xb0b0,0xb0b2)", 2)
        replace("nav_protocol.py", "0xb0b0: 5}", "0xb0b0: 5, 0xb0b2: 5}", 1)
        replace("nav_protocol.py", "0xb0b0: 2}", "0xb0b0: 2, 0xb0b2: 2}", 1)
        nav_text = (staged / "nav_protocol.py").read_bytes().decode("utf-8")
        nl = "\r\n" if "\r\n" in nav_text else "\n"
        replace("nav_protocol.py", "def firmware_label(build):",
                "def firmware_label(build):" + nl + "    if build==0xb0b2:" + nl +
                "        return 'B0B2 · 动态样本策略修复候选 · 待验收'", 1)
        # Copied tests must not reuse the frozen receiver's old output directory.
        replace("test_system.py", "OUT=ROOT/'out/b0b0_ground_tests'",
                "OUT=Path(__file__).resolve().parent/'test_output'", 1)
        replace("test_mtf.py", "OUT=Path(__file__).resolve().parents[2]/'out/b0b0_ground_tests'",
                "OUT=Path(__file__).resolve().parent/'test_output'", 1)
        # Add only the independent versioned CRC decoder to the frozen copy.
        diagnostic_source = pathlib.Path(__file__).resolve().parents[1] / "ground" / "protocol.py"
        shutil.copyfile(diagnostic_source, staged / "sik_diagnostic_protocol.py")
        shutil.copyfile(diagnostic_source.with_name('policy_protocol.py'),staged/'policy_protocol.py')
        replace("protocol.py", "from rotation_protocol import decode_rotation",
                "from rotation_protocol import decode_rotation" + nl + "from sik_diagnostic_protocol import decode as decode_imu_diagnostic", 1)
        replace("protocol.py", "    result.protocols[b'\\xa5\\x83']=(48,decode_rotation)",
                "    result.protocols[b'\\xa5\\x83']=(48,decode_rotation)" + nl +
                "    result.protocols[b'\\xa5\\x85']=(76,decode_imu_diagnostic)", 1)
        replace('protocol.py','from sik_diagnostic_protocol import decode as decode_imu_diagnostic',
                'from sik_diagnostic_protocol import decode as decode_imu_diagnostic'+nl+'from policy_protocol import install_aliases,decode_mtf_v3',1)
        replace('protocol.py',"    result.protocols[b'\\xa5\\x81']=(128,decode_mtf)",
                "    result.protocols[b'\\xa5\\x81']=(128,lambda packet:decode_mtf_v3(packet,decode_mtf))",1)
        replace('protocol.py',"    result.protocols[b'\\xa5\\x85']=(76,decode_imu_diagnostic)",
                "    result.protocols[b'\\xa5\\x85']=(76,decode_imu_diagnostic)"+nl+'    install_aliases(result,decode_info,decode_rotation)',1)
        replace('nav_protocol.py',"def mtf_identity_matches(info, mtf):", "def mtf_identity_matches(info, mtf):"+nl+"    if info and info.get('build_id')==0xb0b2 and info.get('version')==5:"+nl+"        return bool(mtf and mtf.get('version')==3)",1)
        replace('analysis.py',"pose_age_ms=r['pose_age_ticks']/50000,", "pose_age_ms=r['pose_age_ticks']/50000 if isinstance(r.get('pose_age_ticks'),int) else None,",1)
        p = staged / "protocol.py"
        before, after = patches["protocol.py"]
        after += nl + DASHBOARD_EXTENSION.replace("\n", nl)
        p.write_bytes(after.encode("utf-8")); patches["protocol.py"][1] = after
        replace("ground_server.py", "mtf01p.b0b0_synthesis_fix.v7", "mtf01p.b0b2_timeout_policy.v3", 1)
        replace("nav_protocol.py", "mtf01p.b0b0_synthesis_fix.v7", "mtf01p.b0b2_timeout_policy.v3", 1)
        replace("test_system.py", "mtf01p.b0b0_synthesis_fix.v7", "mtf01p.b0b2_timeout_policy.v3", 1)
        if file_hashes(source) != source_hashes:
            raise ValueError("frozen source changed while preparing receiver")
        output_hashes = file_hashes(staged)
        diffs = "".join("".join(difflib.unified_diff(before.splitlines(keepends=True),
                     after.splitlines(keepends=True), fromfile=f"ground/B0B0/{name}",
                     tofile=f"B0B2/sik_receiver/{name}"))
                     for name, (before, after) in sorted(patches.items()))
        receipt = dict(schema="b0b2.sik-receiver-preparation.v1",
            created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
            source=str(source), output=str(output),
            generator_sha256=sha(pathlib.Path(__file__).read_bytes()),
            source_files_sha256=source_hashes, source_tree_sha256=tree_hash(source_hashes),
            output_files_sha256=output_hashes, output_tree_sha256=tree_hash(output_hashes),
            patch_sha256=sha(diffs.encode("utf-8")), unified_patch=diffs,
            changed_files=sorted(patches),
            supported_a585_versions=[1,2,3],
            age_free_wire_headers=['a586','a587','a588','a589'],
            v3_unavailable_fields=['first_protection_pose_age_ticks'],
            v2_unavailable_fields=["latest_rejected_source_id","first_protection_time_ms_low32"],
            scope="B0B2 policy v3: explicit age-free headers and unavailable age metadata; legacy packets remain supported; module online1s distinct from metric200ms/control100ms",
            serial_opened=False, serial_writes=False,
            output_hash_scope="Files at preparation, excluding this receipt; later runtime/test outputs are separate")
        (staged / RECEIPT).write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding="utf-8")
        staged.rename(output)
    return receipt


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=pathlib.Path,
                        default=REPOSITORY / "out" / "B0B2" / "sik_receiver")
    args = parser.parse_args(argv)
    try:
        prepare(args.output)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    print(str((args.output.resolve() / RECEIPT)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
