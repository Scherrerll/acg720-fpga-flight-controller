"""Use the nearest full-route v4 controller with the exact proven v8 guard."""
from pathlib import Path
import difflib,hashlib,json,shutil
O=Path(__file__).resolve().parent;R=O.parents[3]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text())
V4=R/'out/z_aw_fix_20261026/compact_aw_v4/canonical/source'
V8=R/'out/z_aw_fix_20261026/compact_aw_v8/canonical/source'
CANON=R/'out/z_aw_fix_20261026/compact_aw_v9/canonical/source'
b4=read(O.parent/'compact_aw_v4/source_freeze.json')['source55']
b8=read(O.parent/'compact_aw_v8/source_freeze.json')['source55']
assert len(b4)==len(b8)==55 and b4['position/mtf_xyz_hold_control.v']=='ffddb029cb34a8d2ac8995cc43d85866e273d3d147bb650cfd5d3c66c580b642'
assert {p:sha(V4/p) for p in b4}==b4 and {p:sha(V8/p) for p in b8}==b8
guard=['position/pose_time_adapter.v','acg720_ano_port.v','mtf_xyz_navigation_control.v','position/mtf_shared_height_fusion.v']
assert sorted(p for p in b4 if b4[p]!=b8[p])==sorted(guard+['position/mtf_xyz_hold_control.v'])
assert not CANON.exists() and not (O/'source_freeze.json').exists()
shutil.copytree(V4,CANON);diff=''
for rel in guard:
    (CANON/rel).write_bytes((V8/rel).read_bytes())
    diff+=''.join(difflib.unified_diff((V4/rel).read_text().splitlines(True),(CANON/rel).read_text().splitlines(True),fromfile='v4/'+rel,tofile='v9/'+rel))
actual={p:sha(CANON/p) for p in b4}
assert [p for p in actual if actual[p]!=b4[p]]==[p for p in b4 if p in guard]
assert [p for p in actual if actual[p]!=b8[p]]==['position/mtf_xyz_hold_control.v']
(O/'source_changes.diff').write_text(diff,encoding='utf8',newline='')
(O/'source_freeze.json').write_text(json.dumps({'scope':'v4 full-route reference plus byte-identical v8 producer guard. No new algorithm, state or timing schedule.',
    'source_root':str(CANON),'baseline_source55':b4,'source55':actual,'changed_files':guard,
    'v8_source55':b8,'changed_from_v8':['position/mtf_xyz_hold_control.v'],'source_review_sha256':sha(O/'source_review.md'),
    'synthesis_started':False,'physical_started':False},indent=2)+'\n')
print('Prepared v9: exact v4 controller + exact four v8 guard files;55 frozen files.')
