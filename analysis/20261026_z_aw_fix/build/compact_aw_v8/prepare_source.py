"""Isolated v7 fork: publish exact az range predicate with the az tuple."""
from pathlib import Path
import difflib,hashlib,json,shutil
O=Path(__file__).resolve().parent; R=O.parents[3]
PRIOR=R/'out/z_aw_fix_20261026/compact_aw_v7/canonical/source'
CANON=R/'out/z_aw_fix_20261026/compact_aw_v8/canonical/source'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
expected=json.loads((O.parent/'compact_aw_v7/source_freeze.json').read_text())['source55']
assert len(expected)==55 and {p:sha(PRIOR/p) for p in expected}==expected
assert not CANON.exists() and not (O/'source_freeze.json').exists()
shutil.copytree(PRIOR,CANON)
changes={
 'position/pose_time_adapter.v':[
  (' output reg signed [31:0] output_az=0,',' output reg signed [31:0] output_az=0,\n // Exact original numeric predicate, registered beside its matching tuple.\n output reg output_az_range_ok=1,'),
  ('   output_ax<=0;output_ay<=0;output_az<=0;','   output_ax<=0;output_ay<=0;output_az<=0;output_az_range_ok<=1;'),
  ('    output_ax<=held_ax;output_ay<=held_ay;output_az<=held_az;output_acc_valid<=held_valid;',
   '    output_ax<=held_ax;output_ay<=held_ay;output_az<=held_az;output_acc_valid<=held_valid;\n    output_az_range_ok<=held_az>=-30000 && held_az<=30000;')],
 'acg720_ano_port.v':[
  (' wire signed [31:0] converted_ax,converted_ay,converted_az;',' wire signed [31:0] converted_ax,converted_ay,converted_az;\n wire converted_az_range_ok;'),
  ('  .output_acc_valid(converted_acc_valid),.busy(),.fault(time_adapter_fault));','  .output_az_range_ok(converted_az_range_ok),.output_acc_valid(converted_acc_valid),.busy(),.fault(time_adapter_fault));'),
  ('.PRECHECKED_HEIGHT_ORIGIN(1)) native_navigation(','.PRECHECKED_HEIGHT_ORIGIN(1),.PRECHECKED_AZ_RANGE(1)) native_navigation('),
  ('  .acc_valid(native_acc_valid),','  .acc_valid(native_acc_valid),.az_range_ok(converted_az_range_ok),')],
 'mtf_xyz_navigation_control.v':[
  ('PRECHECKED_HEIGHT_ORIGIN=0)(', 'PRECHECKED_HEIGHT_ORIGIN=0,PRECHECKED_AZ_RANGE=0)('),
  (' input wire acc_valid,acc_update,input wire [31:0] acc_dt_us,',' input wire acc_valid,acc_update,input wire [31:0] acc_dt_us,\n // If enabled, caller guarantees exact same-tuple original az range predicate.\n input wire az_range_ok,'),
  (' wire live_acc=acc_valid && pose_valid && !origin_reset;',' wire live_acc=acc_valid && pose_valid && !origin_reset;\n wire live_az_range_ok=PRECHECKED_AZ_RANGE ?az_range_ok:(az_up_mmps2>=-30000 && az_up_mmps2<=30000);'),
  ('.RANGE_AGE_PRECHECKED(1)) height_fusion(','.RANGE_AGE_PRECHECKED(1),.PRECHECKED_AZ_RANGE(PRECHECKED_AZ_RANGE)) height_fusion('),
  ('  .range_age_ticks(range_age_ticks),','  .range_age_ticks(range_age_ticks),.az_range_ok(az_range_ok),'),
  ('  az_up_mmps2>=-30000 && az_up_mmps2<=30000 && live_yaw_range_ok;', '  live_az_range_ok && live_yaw_range_ok;')],
 'position/mtf_shared_height_fusion.v':[
  (' parameter integer RANGE_AGE_PRECHECKED=0',' parameter integer RANGE_AGE_PRECHECKED=0,PRECHECKED_AZ_RANGE=0'),
  (' input wire range_valid,acc_valid,acc_update,',' input wire range_valid,acc_valid,acc_update,\n input wire az_range_ok,'),
  (' wire sources_ok=range_valid', ' wire az_numeric_ok=PRECHECKED_AZ_RANGE ?az_range_ok:(az_up_mmps2>=-30000 && az_up_mmps2<=30000);\n wire sources_ok=range_valid'),
  ('ref_height_mm>=0 && ref_height_mm<=5000 && az_up_mmps2>=-30000 && az_up_mmps2<=30000;', 'ref_height_mm>=0 && ref_height_mm<=5000 && az_numeric_ok;'),
  ('  az_up_mmps2>=-30000 && az_up_mmps2<=30000 && !cleanup', '  az_numeric_ok && !cleanup')]
}
diff=''
for rel,replacements in changes.items():
    p=CANON/rel;raw=p.read_bytes();new=raw
    for a,b in replacements:
        assert new.count(a.encode())==1,(rel,a,new.count(a.encode()))
        new=new.replace(a.encode(),b.encode())
    p.write_bytes(new)
    diff+=''.join(difflib.unified_diff(raw.decode().splitlines(True),new.decode().splitlines(True),fromfile='v7/'+rel,tofile='v8/'+rel))
actual={p:sha(CANON/p) for p in expected}
assert sorted(p for p in expected if actual[p]!=expected[p])==sorted(changes)
assert {p:sha(PRIOR/p) for p in expected}==expected
(O/'source_changes.diff').write_text(diff,encoding='utf8',newline='')
(O/'source_freeze.json').write_text(json.dumps({'scope':'v7 fork: exact az numeric predicate published with producer tuple; no extra latency or math changes',
    'source_root':str(CANON),'baseline_source55':expected,'source55':actual,'changed_files':list(changes),'source_review_sha256':sha(O/'source_review.md'),
    'synthesis_started':False,'physical_started':False},indent=2)+'\n',encoding='utf8')
print(json.dumps({'source55':len(actual),'changed_files':list(changes),'unchanged_files':55-len(changes),'hold_unchanged':actual['position/mtf_xyz_hold_control.v']==expected['position/mtf_xyz_hold_control.v']},indent=2))
