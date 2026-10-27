"""Freeze the separate-chat input snapshot before dispatch. No firmware promotion."""
from pathlib import Path
import datetime, hashlib, json, shutil

R = Path(__file__).resolve().parents[2]
A = R / 'analysis/20261026_z_aw_fix'
W = R / 'out/z_aw_fix_20261026/clock49_working'
D = Path('C:/Users/ScherrerL/Desktop/apple/runtime_b0b4_49mhz_20261027')
assert not D.exists(), 'Never overwrite another chat workspace'
progress = json.loads((W/'WORK_PROGRESS_04_RX_ORIGINAL_NOT_FOR_BUILD.json').read_text(encoding='utf8'))
expected = progress['working_source58']
assert len(expected) == 58
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
assert all(sha(W/'source'/n) == h for n,h in expected.items())
for n in expected:
    p = D/'input_snapshot/source58'/n
    p.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(W/'source'/n, p)
assert all(sha(D/'input_snapshot/source58'/n) == h for n,h in expected.items())
shutil.copy2(W/'WORK_PROGRESS_04_RX_ORIGINAL_NOT_FOR_BUILD.json', D/'input_snapshot/ORIGINAL_PROGRESS.json')
handoff = A/'HANDOFF_49MHZ_SEPARATE_CHAT_20261027.md'
shutil.copy2(handoff, D/'HANDOFF.md')
manifest = dict(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    scope='Incomplete source snapshot for the explicitly requested separate49MHz chat; not an installable firmware',
    main_chat='01a17788-4242-79e0-9a84-aa5021c9aad4',
    runtime=str(D), source58=expected, handoff_sha256=sha(handoff),
    source_state='Top, project list and actual clock remain50MHz. PLL files are not integrated. Original RX source restored.')
(D/'input_snapshot/MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf8')
(A/'SEPARATE_49MHZ_INPUT_SNAPSHOT.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf8')
print(json.dumps(dict(runtime=str(D),source_files=len(expected),snapshot_verified=True,handoff_sha256=sha(handoff)),indent=2))
