"""Keep exact changed candidate bytes outside ignored out/, once."""
from pathlib import Path
import datetime,hashlib,json
O=Path(__file__).resolve().parent;R=O.parents[3]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
freeze=json.loads((O/'source_freeze.json').read_text())
S=Path(freeze['source_root']);D=R/'analysis/20261026_z_aw_fix/implementation_history/v8_precomputed_az'
assert not D.exists()
assert {p:sha(S/p) for p in freeze['source55']}==freeze['source55']
D.mkdir(parents=True);artifacts={}
for rel in freeze['changed_files']:
    p=D/'source'/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((S/rel).read_bytes())
    assert sha(p)==freeze['source55'][rel]
    artifacts[p.relative_to(D).as_posix()]={'sha256':sha(p),'bytes':p.stat().st_size}
(D/'MANIFEST.json').write_text(json.dumps({'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'scope':'v8 four changed source files, exact bytes. Other51 have frozen v7 hashes; no physical qualification.',
    'source55':freeze['source55'],'source_freeze_sha256':sha(O/'source_freeze.json'),'artifacts':artifacts},indent=2)+'\n')
print('Preserved exact four v8 changes with full55 source binding.')
