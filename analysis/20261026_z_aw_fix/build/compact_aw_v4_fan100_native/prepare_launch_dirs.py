"""Correct missing empty report directories before any native build starts."""
from pathlib import Path
import datetime,hashlib,json
O=Path(__file__).resolve().parent;R=O.parents[3]
assert not (O/'PRESTART_CORRECTION.json').exists()
for place in [2,3]:
    report=O/f'physical_p{place}r0_01'
    assert not report.exists() and not (R/'out/z_aw_fix_20261026/compact_aw_v4_fan100_native'/report.name).exists()
    report.mkdir()
(O/'PRESTART_CORRECTION.json').write_text(json.dumps({'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'issue':'First Start-Process invocation returned supervisor PID61344 but the required empty physical report directories had not been prepared. No runner_process/runner_exit/vendor attempt or vendor process receipt was produced. The launcher asserts O.is_dir() before creating its child.',
    'first_supervisor_actual_wait':None,'first_supervisor_exit_not_reconstructed':True,'no_vendor_attempt_created':True,
    'correction':'Created the two missing empty report directories. Frozen source and all runner scripts unchanged. Fresh invocation will capture supervisor stdout/stderr as well as its original child wait receipts.',
    'preparation_sha256':hashlib.sha256((O/'PREPARATION.json').read_bytes()).hexdigest()},indent=2)+'\n',encoding='utf8')
print('Prepared both empty report directories; no vendor process started by this correction.')
