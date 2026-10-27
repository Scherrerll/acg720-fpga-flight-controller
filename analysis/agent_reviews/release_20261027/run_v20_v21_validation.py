"""Run only the offline evidence tests and bind their actual child wait and logs."""
from pathlib import Path
import ast
import datetime
import hashlib
import json
import os
import subprocess
import sys

sys.dont_write_bytecode = True
D = Path(__file__).resolve().parent
R = D.parents[2]
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
files = [R / 'analysis/20261026_z_aw_fix/build/export_qualified_v4.py', R / 'firmware/B0B4/verify_release.py',
         R / 'firmware/B0B4/build_candidate.py', D / 'test_release_evidence.py', Path(__file__)]
before = {str(p): sha(p) for p in files}
for p in files: ast.parse(p.read_text(encoding='utf8'))
assert before[str(files[2])] == 'abb5246c203b73c111f80bc91f8db6c8220463f7d4c5cf48dbfe2167ef49db84'
command = [sys.executable, '-u', '-B', str(D / 'test_release_evidence.py')]
record = dict(command=command, cwd=str(R), started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
              parent_pid=os.getpid(), source_script_hashes=before, scope='Offline source/proof/SYN archive tests only; no export, vendor, audit retry, hardware or promotion.')
with (D / 'v20_v21_validation.stdout.log').open('wb') as out, (D / 'v20_v21_validation.stderr.log').open('wb') as err:
    child = subprocess.Popen(command, cwd=R, stdin=subprocess.DEVNULL, stdout=out, stderr=err,
                             creationflags=subprocess.CREATE_NO_WINDOW, close_fds=True)
    record['pid'] = child.pid
    result = child.wait()
record.update(actual_p_wait=result, normal_wait_return=True, ended_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
              stdout_sha256=sha(D / 'v20_v21_validation.stdout.log'), stderr_sha256=sha(D / 'v20_v21_validation.stderr.log'))
assert {str(p): sha(p) for p in files} == before, 'Tested source changed during validation'
(D / 'v20_v21_validation_exit.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf8')
print(json.dumps(record))
raise SystemExit(result)
