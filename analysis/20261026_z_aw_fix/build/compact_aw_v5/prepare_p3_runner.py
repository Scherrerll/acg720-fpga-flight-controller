from pathlib import Path
import ast,hashlib,json
O=Path(__file__).resolve().parent
p=O.parent/'compact_aw_v4/run_physical_p3r0.py';q=O/'run_physical_p3r0.py'
h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert h(p)=='0c767d0b89740bdb62b02709a9f274b9685befbbee5f6027631e59bd41ff9561'
assert not q.exists()
s=p.read_text()
changes=[('v4 map2 P3/R0','v5 map2 P3/R0'),
 ('out/z_aw_fix_20261026/compact_aw_v4','out/z_aw_fix_20261026/compact_aw_v5'),
 ('out/z_aw_fix_20261026/compact_aw_v3/canonical/source','out/z_aw_fix_20261026/compact_aw_v4/canonical/source'),
 ('e67bcab6336757e08645756258d39dd13726b452c392d470de4c900a159aaa8f','2d670218e97041bb3d4cc7c67218f4bef12e5bf96261225b9b97203ce3b4a1c9'),
 ('ffddb029cb34a8d2ac8995cc43d85866e273d3d147bb650cfd5d3c66c580b642','04e75ada52551d5622af060efe38fda9aa66ff25199bfb67651f9ec5315ed873'),
 ('baseline_v3_map2_source55','baseline_v4_map2_source55'),('v4_exact_original_physical_gate','v5_exact_original_physical_gate'),
 ('Fresh exact-VG v4 physical-only trial','Fresh exact-VG v5 physical-only trial'),('source override is v4.','source override is v5.'),
 ('v3_source55','v4_source55'),('compact_aw_v4 exact-VG P3/R0 full physical gate PASS','compact_aw_v5 exact-VG P3/R0 full physical gate PASS')]
assert all(a in s for a,b in changes)
for a,b in changes:s=s.replace(a,b)
assert "('route_option','0'),('map_option','2')" in s
s=s.replace("('route_option','0'),('map_option','2')","('route_option','0'),('timing_driven','1'),('map_option','2')")
s=s.replace("'map_option':2,'replicate_resources':0}","'map_option':2,'replicate_resources':0,'timing_driven':1}")
ast.parse(s)
q.write_text(s,encoding='utf8',newline='\n')
(O/'p3_runner_derivation.json').write_text(json.dumps({'base_entry_sha256':h(p),'entry_sha256':h(q),
 'scope':'Fresh v5 path/source/VG/donor keys plus explicit TD1 guard; original ABB physical gate unchanged.',
 'no_vendor_or_profile_created_by_prepare':True},indent=2)+'\n')
print(h(q))
