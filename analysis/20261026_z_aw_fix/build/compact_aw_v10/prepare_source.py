"""Move only Z diagnostic masks across their existing same-tuple snapshot."""
from pathlib import Path
import difflib,hashlib,json,shutil
O=Path(__file__).resolve().parent;R=O.parents[3]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
OLD=R/'out/z_aw_fix_20261026/compact_aw_v9/canonical/source';NEW=R/'out/z_aw_fix_20261026/compact_aw_v10/canonical/source'
prior=json.loads((O.parent/'compact_aw_v9/source_freeze.json').read_text())['source55']
assert {p:sha(OLD/p) for p in prior}==prior and not NEW.exists() and not (O/'source_freeze.json').exists()
shutil.copytree(OLD,NEW);rel='mtf_xyz_navigation_control.v';raw=(OLD/rel).read_bytes()
old1=b'position_x_q8,position_y_q8,controller_roll,controller_pitch,z_throttle_delta,shadow_flags,\n  {7\'d0,mapping_verified},{7\'d0,rotation_compensated},z_collective,z_reason,z_target_height};'
new1=b'position_x_q8,position_y_q8,controller_roll,controller_pitch,controller_delta,shadow_flags,\n  {7\'d0,mapping_verified},{7\'d0,rotation_compensated},controller_collective,z_reason,controller_target_height};'
old2=b"  diagnostic_q[85] ?diagnostic_q[127:112]:16'd0,diagnostic_q[111:0]};"
new2=b"  diagnostic_q[85] ?diagnostic_q[127:112]:16'd0,\n  diagnostic_q[84] ?diagnostic_q[111:96]:16'd0,diagnostic_q[95:64],\n  diagnostic_q[84] ?diagnostic_q[63:48]:16'd0,diagnostic_q[47:32],\n  diagnostic_q[84] ?diagnostic_q[31:0]:32'd0};"
assert raw.count(old1)==raw.count(old2)==1
new=raw.replace(old1,new1).replace(old2,new2)
marker=b' // XY-active is shadow_flags[5], diagnostic_q[85]. Capture raw targets'
assert new.count(marker)==1
new=new.replace(marker,b' // Z-active is shadow_flags[4], diagnostic_q[84]. The same snapshot flag\n // masks raw Z delta/collective/target after capture, exactly as XY below.\n'+marker)
(NEW/rel).write_bytes(new)
actual={p:sha(NEW/p) for p in prior};assert [p for p in prior if prior[p]!=actual[p]]==[rel]
(O/'source_changes.diff').write_text(''.join(difflib.unified_diff(raw.decode().splitlines(True),new.decode().splitlines(True),fromfile='v9/'+rel,tofile='v10/'+rel)),encoding='utf8',newline='')
(O/'source_freeze.json').write_text(json.dumps({'scope':'v9 fork: Z diagnostic snapshot mask commutation only. No control output, state, precision or cycle change.',
    'source_root':str(NEW),'baseline_source55':prior,'source55':actual,'changed_files':[rel],'source_review_sha256':sha(O/'source_review.md'),
    'synthesis_started':False,'physical_started':False},indent=2)+'\n')
print('Prepared isolated v10: one diagnostic-only file change;54 unchanged.')
