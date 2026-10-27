"""Copy the exact v17 frozen55, then apply four same-publication-edge edits."""
from pathlib import Path
import datetime, difflib, hashlib, json, shutil

O=Path(__file__).resolve().parent
R=O.parents[3]
OLD=R/'out/z_aw_fix_20261026/compact_aw_v17/canonical/source'
NEW=R/'out/z_aw_fix_20261026/compact_aw_v18/canonical/source'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
freeze=O.parent/'compact_aw_v17/source_freeze.json'
expected=json.loads(freeze.read_text(encoding='utf8'))['source55']
assert len(expected)==55 and not NEW.exists()
assert all(not any(part.lower().startswith('.env') for part in Path(n).parts) for n in expected)
assert all(sha(OLD/n)==h for n,h in expected.items())
for n in expected:
    p=NEW/n;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(OLD/n,p)
assert {n:sha(NEW/n) for n in expected}==expected
changes={}
def edit(n,a,b):
    p=NEW/n;s=p.read_text(encoding='utf8');assert s.count(a)==1,(n,a)
    p.write_text(s.replace(a,b),encoding='utf8',newline='')
    changes.setdefault(n,[]).append([a,b])
n='sensor/mtf01p_reader.v'
edit(n,' output reg signed [31:0] vx_x100=0,output reg signed [31:0] vy_x100=0,',
       ' output reg signed [31:0] vx_x100=0,output reg signed [31:0] vy_x100=0,\n output reg velocity_range_ok=1,')
edit(n," wire signed [30:0] product_y=$signed(flow_y)*$signed({1'b0,distance_mm[13:0]});",
       " wire signed [30:0] product_y=$signed(flow_y)*$signed({1'b0,distance_mm[13:0]});\n // Cache the range of the exact signed words published on this same sample edge.\n // Invalid numeric observations publish zero; reset and holds match the words.\n wire signed [31:0] next_vx_x100=flow_numeric_ok ? {product_x[30],product_x}:32'sd0;\n wire signed [31:0] next_vy_x100=flow_numeric_ok ? {product_y[30],product_y}:32'sd0;\n wire next_velocity_range_ok=next_vx_x100>=-32'sd1000000 && next_vx_x100<=32'sd1000000 &&\n  next_vy_x100>=-32'sd1000000 && next_vy_x100<=32'sd1000000;")
edit(n,'   vx_x100<=0;vy_x100<=0;x_x100000<=0;y_x100000<=0;saturated<=0;integrated<=0;',
       '   vx_x100<=0;vy_x100<=0;velocity_range_ok<=1;x_x100000<=0;y_x100000<=0;saturated<=0;integrated<=0;')
edit(n,"    vx_x100<=flow_numeric_ok ? {{1{product_x[30]}},product_x}:32'sd0;\n    vy_x100<=flow_numeric_ok ? {{1{product_y[30]}},product_y}:32'sd0;",
       '    vx_x100<=next_vx_x100;vy_x100<=next_vy_x100;\n    velocity_range_ok<=next_velocity_range_ok;')
edit(n,' output wire signed [31:0] metric_vx_x100,metric_vy_x100\n',
       ' output wire signed [31:0] metric_vx_x100,metric_vy_x100,\n output wire metric_velocity_range_ok\n')
edit(n,'  .vx_x100(vx_x100),.vy_x100(vy_x100),.x_x100000(x_x100000),',
       '  .vx_x100(vx_x100),.vy_x100(vy_x100),.velocity_range_ok(metric_velocity_range_ok),.x_x100000(x_x100000),')
n='sensor/mtf_shared_geometry.v'
edit(n,'MAPPING_VERIFIED=0,PRECHECKED_YAW_RANGE=0,PRECHECKED_HEIGHT_TILT4500=0,PRECHECKED_FLOW_TILT1500=0',
       'MAPPING_VERIFIED=0,PRECHECKED_YAW_RANGE=0,PRECHECKED_HEIGHT_TILT4500=0,PRECHECKED_FLOW_TILT1500=0,PRECHECKED_INPUT_VELOCITY=0')
edit(n,' input wire signed [31:0] vx_x100,vy_x100,',
       ' input wire signed [31:0] vx_x100,vy_x100,\n input wire velocity_range_ok,')
edit(n,' wire input_velocity_ok=vx_x100>=-1000000 && vx_x100<=1000000 &&\n  vy_x100>=-1000000 && vy_x100<=1000000;',
       ' // Default callers retain the original signed32 comparison. The enabled\n // caller supplies the predicate committed with these exact velocity words.\n wire input_velocity_ok=PRECHECKED_INPUT_VELOCITY ?velocity_range_ok:\n  (vx_x100>=-1000000 && vx_x100<=1000000 &&\n   vy_x100>=-1000000 && vy_x100<=1000000);')
n='mtf_xyz_navigation_control.v'
edit(n,'PRECHECKED_FLOW_TILT1500=0,PRECHECKED_HEIGHT_ORIGIN=0)(',
       'PRECHECKED_FLOW_TILT1500=0,PRECHECKED_HEIGHT_ORIGIN=0,PRECHECKED_INPUT_VELOCITY=0)(')
edit(n,' input wire signed [31:0] vx_x100,vy_x100,',
       ' input wire signed [31:0] vx_x100,vy_x100,\n input wire velocity_range_ok,')
edit(n,'.PRECHECKED_FLOW_TILT1500(PRECHECKED_FLOW_TILT1500)) geometry(',
       '.PRECHECKED_FLOW_TILT1500(PRECHECKED_FLOW_TILT1500),.PRECHECKED_INPUT_VELOCITY(PRECHECKED_INPUT_VELOCITY)) geometry(')
edit(n,'  .vx_x100(vx_x100),.vy_x100(vy_x100),.pose_valid(pose_valid),',
       '  .vx_x100(vx_x100),.vy_x100(vy_x100),.velocity_range_ok(velocity_range_ok),.pose_valid(pose_valid),')
n='acg720_ano_port.v'
edit(n,' wire mtf_sample,mtf_range_ok,mtf_flow_ok,mtf_integrated;',
       ' wire mtf_sample,mtf_range_ok,mtf_flow_ok,mtf_integrated,mtf_velocity_range_ok;')
edit(n,'  .module_age_ms(mtf_age_ms),.metric_vx_x100(mtf_vx_x100),.metric_vy_x100(mtf_vy_x100));',
       '  .module_age_ms(mtf_age_ms),.metric_vx_x100(mtf_vx_x100),.metric_vy_x100(mtf_vy_x100),.metric_velocity_range_ok(mtf_velocity_range_ok));')
edit(n,'.PRECHECKED_HEIGHT_ORIGIN(1)) native_navigation(',
       '.PRECHECKED_HEIGHT_ORIGIN(1),.PRECHECKED_INPUT_VELOCITY(1)) native_navigation(')
edit(n,'  .vx_x100(mtf_vx_x100),.vy_x100(mtf_vy_x100),',
       '  .vx_x100(mtf_vx_x100),.vy_x100(mtf_vy_x100),.velocity_range_ok(mtf_velocity_range_ok),')
after={n:sha(NEW/n) for n in expected}
assert sorted(n for n in expected if after[n]!=expected[n])==sorted(changes)
assert len(changes)==4
diff=''
for n in sorted(changes):
    before=(OLD/n).read_text(encoding='utf8');now=(NEW/n).read_text(encoding='utf8')
    reverse=now
    for a,b in reversed(changes[n]):assert reverse.count(b)==1;reverse=reverse.replace(b,a)
    assert reverse==before
    diff+=''.join(difflib.unified_diff(before.splitlines(True),now.splitlines(True),fromfile='v17/'+n,tofile='v18/'+n))
(O/'source_changes.diff').write_text(diff,encoding='utf8',newline='')
record=dict(prepared_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    both_owned_directories_absent_before_initial_creation=True,baseline_source_root=str(OLD),candidate_source_root=str(NEW),
    baseline_source_freeze_sha256=sha(freeze),baseline_source55=expected,source55=after,changed_files=sorted(changes),
    exact_reversible_normalized_text_edits=changes,unchanged_files=51,source_changes_diff_sha256=sha(O/'source_changes.diff'),
    semantics=[
        'Signed16 flow times explicitly signed positive15 distance produces exact signed31 product.',
        'Numeric validity bounds full32 distance to80..12000, making low14 distance bits exact; invalid samples publish signed32zero.',
        'Compare explicit signed32 next words including exact ternary four-state merge; do not compare unsigned concatenations or shortcut numeric validity.',
        'Predicate initializes and synchronously resets true with both zero words; all three update on every sample_valid edge before duplicate/integration branches and hold otherwise.',
        'No predicate clear on link loss without sample. Reader metric_commit timing and all existing valid/age/hold/status decisions unchanged.',
        'Default-off nav/shared-geometry parameter keeps original signed32 comparisons for every non-opted-in caller.',
        'Parent v17 core/fallback/pose hints and all clocks, SDC, CST, gains and source55 membership preserved.'],
    limitations='Functional candidate only; component proofs and new top13/FSM/SYN/PNR qualification are separate.')
(O/'VY_SOURCE_CHANGES.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf8')
print(json.dumps(dict(passed=True,copied_frozen_files=55,changed_files=sorted(changes),unchanged_files=51)))
