"""Prepare archive/sealing helpers and strict new SYN; no vendor execution here."""
from pathlib import Path
import ast,hashlib,json
O=Path(__file__).resolve().parent;D=O.parent/'compact_aw_v11'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert not (O/'seal_proofs.py').exists()
t=(D/'seal_proofs.py').read_text()
old="for tag in ['v9','v11']:\n    s=R/f'out/z_aw_fix_20261026/compact_aw_{tag}/canonical/source';expected=inputs['source55'][tag]";assert t.count(old)==1
t=t.replace(old,"for role,tag in [('old','v11'),('new','v12')]:\n    s=R/f'out/z_aw_fix_20261026/compact_aw_{tag}/canonical/source';expected=inputs['source55'][role]")
t=t.replace('len(sources)==5','len(sources)==6').replace("inputs['source55']['v11']","inputs['source55']['new']").replace('Sealed v11','Sealed v12').replace('17 actual stage waits0','19 actual stage waits0').replace('five initial stimulus','six initial stimulus')
start="'initial_index_note':'";a=t.index(start);b=t.index("',\n",a)
t=t[:a]+"'initial_index_note':'Six immutable stimulus files only, all checked against initial hashes. Runtime logs are not indexed as stimuli."+t[b:]
marker="assert len(results['records'])==8 and results['top13']['passed']";assert t.count(marker)==1
t=t.replace(marker,marker+"\nassert len(results['stages'])==19 and 'PASS predicate vectors=200040 integer_limits=9' in (D/'predicate_simulation.log').read_text()")
ast.parse(t);(O/'seal_proofs.py').write_text(t)
t=(D/'run_synthesis.py').read_text()
t=t.replace("ROOT=R/'out/z_aw_fix_20261026/compact_aw_v11'","ROOT=R/'out/z_aw_fix_20261026/compact_aw_v12'").replace("PRIOR=R/'out/z_aw_fix_20261026/compact_aw_v9'","PRIOR=R/'out/z_aw_fix_20261026/compact_aw_v11'")
t=t.replace('compact-AW-v11','compact-AW-v12').replace('compact_aw_v11 fulltop','compact_aw_v12 fulltop').replace('baseline_v9','baseline_v11').replace('reference_v9','reference_v11').replace('changed_from_v9','changed_from_v11').replace('v9_canonical','v11_canonical').replace('candidate_v11','candidate_v12').replace('v11 SYN_ONLY','v12 SYN_ONLY')
ast.parse(t);(O/'run_synthesis.py').write_text(t)
t=(D/'launch_synthesis_hidden.py').read_text();ast.parse(t);(O/'launch_synthesis_hidden.py').write_text(t)
(O/'SYNTHESIS_PREPARATION.json').write_text(json.dumps({'scope':'One new strict full-top map2/replicate0/50MHz/area SYN for v12 one-expression rewrite. Must first seal proof root0,19 stage waits0 and six immutable stimuli.',
    'template_runner_sha256':sha(D/'run_synthesis.py'),'derived_runner_sha256':sha(O/'run_synthesis.py'),'seal_script_sha256':sha(O/'seal_proofs.py'),'SYN_started':False},indent=2)+'\n')
print('Prepared v12 proof seal and strict SYN scripts; no vendor launched.')
