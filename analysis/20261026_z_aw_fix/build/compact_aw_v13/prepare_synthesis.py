"""Prepare v13 SYN-only runner from the actual v12 recipe; do not start it."""
from pathlib import Path
import ast, hashlib, json
O=Path(__file__).resolve().parent;P=O.parent/'compact_aw_v12'
assert not (O/'run_synthesis.py').exists() and not (O/'launch_synthesis_hidden.py').exists()
text=(P/'run_synthesis.py').read_text()
text=text.replace('v12','__CURRENT__').replace('v11','v12').replace('__CURRENT__','v13')
needle="['position/pose_time_adapter.v','acg720_ano_port.v','mtf_xyz_navigation_control.v','position/mtf_shared_height_fusion.v']"
assert text.count(needle)==1
text=text.replace(needle,"['position/pose_time_adapter.v','acg720_ano_port.v','mtf_xyz_navigation_control.v','position/mtf_shared_height_fusion.v','sensor/mtf01p_reader.v']")
ast.parse(text)
(O/'run_synthesis.py').write_text(text,encoding='utf8')
(O/'launch_synthesis_hidden.py').write_bytes((P/'launch_synthesis_hidden.py').read_bytes())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
(O/'SYNTHESIS_PREPARATION.json').write_text(json.dumps({'prepared_only':True,
    'parent_recipe_sha256':sha(P/'run_synthesis.py'),'runner_sha256':sha(O/'run_synthesis.py'),
    'scope':'Same map2/replicate0/area SYN recipe; extra changed reader allowed by explicit expected source hash. No PNR or vendor launched.'},indent=2)+'\n')
print('Prepared v13 SYN-only recipe; no vendor launched.')
