"""Preserve all five B3-relative v17 source files and exact55 reconstruction hashes."""
from pathlib import Path
import datetime,hashlib,json
O=Path(__file__).resolve().parent;R=O.parents[3];C=R/'out/z_aw_fix_20261026/compact_aw_v17/canonical/source'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf8'))
expected=read(O/'source_freeze.json')['source55'];b3=read(R/'firmware/B0B3/qualification.json')['source_sha256']
assert len(expected)==len(b3)==55 and {n:sha(C/n) for n in expected}==expected
assert {n:sha(R/'firmware/B0B3/source'/n) for n in b3}==b3
changes=[n for n in expected if expected[n]!=b3[n]];assert len(changes)==7
D=R/'analysis/20261026_z_aw_fix/implementation_history/v17_landing_fanout_pose';assert not D.exists();D.mkdir()
items={}
for name in changes:
    path=D/'source'/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes((C/name).read_bytes());assert sha(path)==expected[name]
    items[path.relative_to(D).as_posix()]={'sha256':sha(path),'bytes':path.stat().st_size}
(D/'MANIFEST.json').write_text(json.dumps({'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'scope':'Exact7 B3-relative v17 source changes, remaining48 reuse immutable B3 source bytes. Functional/source snapshot only, no physical qualification.',
    'baseline_B3_source55':b3,'source55':expected,'artifacts':items,
    'source_freeze_sha256':sha(O/'source_freeze.json'),'proof_binding_sha256':sha(O/'PROOF_BINDING.json'),
    'reuse_recheck_sha256':sha(O/'REUSED_BINDINGS_RECHECK.json')},indent=2)+'\n',encoding='utf8')
print('Preserved7 exact v17 source changes and all55 reconstruction bindings; no PNR acceptance claim.')
