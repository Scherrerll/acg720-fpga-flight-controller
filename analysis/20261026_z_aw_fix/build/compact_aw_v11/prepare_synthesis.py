"""Derive same strict full-top SYN gates from v9; adapt only v11 dependency bindings."""
from pathlib import Path
import ast,hashlib,json
O=Path(__file__).resolve().parent;D=O.parent/'compact_aw_v9'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
proof=json.loads((O/'PROOF_BINDING.json').read_text());assert proof['passed'] and proof['actual_proof_runner_wait']==0
assert not (O/'run_synthesis.py').exists()
t=(D/'run_synthesis.py').read_text()
t=t.replace("ROOT=R/'out/z_aw_fix_20261026/compact_aw_v9'","ROOT=R/'out/z_aw_fix_20261026/compact_aw_v11'")
t=t.replace("PRIOR=R/'out/z_aw_fix_20261026/compact_aw_v4'","PRIOR=R/'out/z_aw_fix_20261026/compact_aw_v9'")
t=t.replace('compact-AW-v9','compact-AW-v11').replace('compact_aw_v9 fulltop','compact_aw_v11 fulltop').replace("O/'proofs_retry02/","O/'proofs/")
t=t.replace('baseline_v4','baseline_v9').replace('reference_v4','reference_v9').replace('changed_from_v4','changed_from_v9').replace('v4_canonical','v9_canonical').replace('candidate_v9','candidate_v11')
old="{p:expected[p] for p in freeze['changed_files']}";assert t.count(old)==1
t=t.replace(old,"{p:expected[p] for p in ['position/pose_time_adapter.v','acg720_ano_port.v','mtf_xyz_navigation_control.v','position/mtf_shared_height_fusion.v']}")
marker="    assert hash55(CANON,expected)==expected\n";assert t.count(marker)==1
t=t.replace(marker,marker+"    binding=json.loads((O/'PROOF_BINDING.json').read_text());assert binding['passed'] and binding['actual_proof_runner_wait']==0 and binding['source55']==expected\n")
t=t.replace("'v9 SYN_ONLY raw artifact freeze","'v11 SYN_ONLY raw artifact freeze")
ast.parse(t);(O/'run_synthesis.py').write_text(t)
t=(D/'launch_synthesis_hidden.py').read_text();ast.parse(t);(O/'launch_synthesis_hidden.py').write_text(t)
(O/'SYNTHESIS_PREPARATION.json').write_text(json.dumps({'scope':'One new full-top SYN for changed publication-age implementation. Exact new55, proof root0, same map2/replicate0/50MHz/area and strict clock/radio/1000-350gain/18ports gates.',
    'proof_binding_sha256':sha(O/'PROOF_BINDING.json'),'template_runner_sha256':sha(D/'run_synthesis.py'),'derived_runner_sha256':sha(O/'run_synthesis.py'),'SYN_started':False},indent=2)+'\n')
print('Prepared v11 full-top SYN with unchanged gates.')
