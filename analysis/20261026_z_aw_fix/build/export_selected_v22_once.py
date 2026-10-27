"""One-shot qualified offline export with an actual child wait receipt; no hardware."""
from pathlib import Path
import datetime, hashlib, json, subprocess, sys

sys.dont_write_bytecode = True
O = Path(__file__).resolve().parent
R = O.parents[2]
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
read = lambda p: json.loads(p.read_text(encoding='utf8'))
utc = lambda: datetime.datetime.now(datetime.timezone.utc).isoformat()
assert len(sys.argv) == 3, 'Expected independent lifecycle review path and its SHA256'
review = Path(sys.argv[1]).resolve()
assert review.is_relative_to(R / 'analysis/agent_reviews') and sha(review) == sys.argv[2]
assert read(review)['approved_lifecycle_fix'] is True and read(review)['independent_temporary_real55_roundtrip_passed'] is True
exporter = O / 'export_qualified_v4.py'
verifier = R / 'firmware/B0B4/verify_release.py'
assert sha(exporter) == 'cab893924c892327dc4168254064dfade00c2a4db3c19908dd34c5f58f6552f1'
assert sha(verifier) == '0ba2c0cdca20b7bcf60b34c4d7f2c059762e7f1723f78fa977b0ad4884353cbf'
seal = R / 'analysis/agent_reviews/release_lifecycle_20261027/RELEASE_LIFECYCLE_VALIDATION_SEALED.json'
assert sha(seal) == '676f0fda2eda9460dd6c6553ff622572f14f057f9a008789203f8caf8eebc2f1'
assert read(seal)['passed'] is True
raw = O / 'compact_aw_v22/physical_p3r0_01/INDEPENDENT_RAW_REVIEW.json'
assert sha(raw) == 'dafa8ed37f1d3912dc2d8e988030645fa880ace0d79f26b56f2bf83f586f2117'
assert read(raw)['passed'] is True and all(read(raw)['checks'].values())
assert not any(x['status'] == 'running' for x in read(O.parent / 'CONTINUATION_STATE.json')['runs'])
assert not (R / 'firmware/B0B4/qualification.json').exists()
assert read(O / 'compact_aw_v22_fan100/runner_exit.json')['actual_p_wait'] == 0
D = O / 'release_export_v22_20261027_01'
assert not D.exists(), 'Never overwrite export process evidence'
D.mkdir()
command = [sys.executable, '-B', '-X', 'utf8', str(exporter), 'v22_p3',
           '--independent-review-sha256', sha(raw)]
record = dict(command=command, cwd=str(R), started_utc=utc(), supervisor_pid=__import__('os').getpid(),
              runner_sha256=sha(Path(__file__)), exporter_sha256=sha(exporter),
              verifier_sha256=sha(verifier), lifecycle_review_sha256=sha(review),
              lifecycle_seal_sha256=sha(seal), stdin='DEVNULL', create_no_window=True)
with (D / 'stdout.log').open('wb') as output, (D / 'stderr.log').open('wb') as errors:
    child = subprocess.Popen(command, cwd=R, stdin=subprocess.DEVNULL, stdout=output,
                             stderr=errors, creationflags=subprocess.CREATE_NO_WINDOW, close_fds=True)
    record['pid'] = child.pid
    (D / 'process.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf8')
    code = child.wait()
record.update(actual_p_wait=code, normal_wait_return=True, ended_utc=utc(),
              stdout_sha256=sha(D / 'stdout.log'), stderr_sha256=sha(D / 'stderr.log'))
(D / 'exit.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf8')
print(json.dumps({'export_actual_wait': code, 'receipt': str(D / 'exit.json')}), flush=True)
print((D / 'stdout.log').read_text(encoding='utf8', errors='replace'), end='')
if code:
    print((D / 'stderr.log').read_text(encoding='utf8', errors='replace'), file=sys.stderr, end='')
raise SystemExit(code)
