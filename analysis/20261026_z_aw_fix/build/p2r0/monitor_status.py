"""Read-only build snapshot; writes only this monitor's own JSONL ledger."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[4]
ATTEMPT = ROOT / 'out/z_aw_fix_20261026/build_attempt_02'
VERIFY = ATTEMPT / 'verification'
expected = json.loads((VERIFY / 'build_input.json').read_text())['source_sha256']
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
log = VERIFY / 'physical.log'
text = log.read_text(errors='replace')
events = [line for line in text.splitlines() if re.search(
    r'(Placement Phase|Routing Phase|unrouted|ERROR|completed|RETURNED_EOF)', line)]
exit_path = VERIFY / 'physical_exit.json'
exit_receipt = json.loads(exit_path.read_text()) if exit_path.exists() else None
row = dict(utc=datetime.now(timezone.utc).isoformat(),
    helper_pid=15404, native_pid=7440, log_bytes=log.stat().st_size,
    last_event=events[-1] if events else '',
    actual_p_wait=exit_receipt.get('actual_p_wait') if exit_receipt else None,
    has_exit_receipt=exit_receipt is not None,
    tr_exists=(ATTEMPT / 'source/impl/pnr/acg720_ano_port.tr').exists(),
    fs_exists=(ATTEMPT / 'source/impl/pnr/acg720_ano_port.fs').exists(),
    canonical55_unchanged=all(sha(ROOT / 'firmware/B0B4/source' / n) == h for n, h in expected.items()),
    attempt55_unchanged=all(sha(ATTEMPT / 'source' / n) == h for n, h in expected.items()),
    vg_sha256=sha(ATTEMPT / 'source/impl/gwsynthesis/acg720_ano_port.vg'))
with Path(__file__).with_name('monitor.jsonl').open('a', encoding='utf8') as output:
    output.write(json.dumps(row) + '\n')
print(json.dumps(row))
