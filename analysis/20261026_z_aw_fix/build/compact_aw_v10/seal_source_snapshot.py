"""Archive all seven B3-relative source changes so ignored out/ is reconstructible."""
from pathlib import Path
import datetime,hashlib,json
O=Path(__file__).resolve().parent;R=O.parents[3]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
freeze=json.loads((O/'source_freeze.json').read_text());source=Path(freeze['source_root'])
baseline=json.loads((R/'firmware/B0B3/qualification.json').read_text())['source_sha256']
expected=freeze['source55'];assert len(expected)==len(baseline)==55
assert {p:sha(source/p) for p in expected}==expected
assert {p:sha(R/'firmware/B0B3/source'/p) for p in baseline}==baseline
changes=[p for p in expected if expected[p]!=baseline[p]];assert len(changes)==7
D=R/'analysis/20261026_z_aw_fix/implementation_history/v10_z_diag_snapshot';assert not D.exists();D.mkdir()
items={}
for rel in changes:
    p=D/'source'/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((source/rel).read_bytes());assert sha(p)==expected[rel]
    items[p.relative_to(D).as_posix()]={'sha256':sha(p),'bytes':p.stat().st_size}
(D/'MANIFEST.json').write_text(json.dumps({'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'scope':'Exact seven B3-relative v10 changes; remaining48 use immutable firmware/B0B3/source bytes. No physical qualification.',
    'baseline_B3_source55':baseline,'source55':expected,'artifacts':items,'source_freeze_sha256':sha(O/'source_freeze.json')},indent=2)+'\n')
print('Preserved seven v10 changes and all55 reconstruction bindings outside out/.')
