"""Prepare exact-v10 physical scripts and SYN archive; launch no PNR."""
from pathlib import Path
import ast,hashlib,json
O=Path(__file__).resolve().parent;R=O.parents[3]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
summary=json.loads((R/'out/z_aw_fix_20261026/compact_aw_v10/build_attempt_01/verification/synthesis_summary.json').read_text())
sx=json.loads((O/'runner_exit.json').read_text());px=json.loads((O/'proofs_retry02/runner_exit.json').read_text())
assert summary['passed'] and sx['actual_p_wait']==px['actual_p_wait']==0 and sx['normal_wait_return'] and px['normal_wait_return']
oldvg='e99d1ec0928fa9c1650cbc6a7ac9c08d4b2ef0758cdb3a9eec11b04af5d0eb20';vg=summary['netlist_sha256'];items={}
for name in ['run_physical.py','launch_physical_hidden.py','seal_terminal.py','independent_raw_review.py']:
    donor=O.parent/'compact_aw_v9'/name;text=donor.read_text().replace('v9','v10').replace('v4','v9').replace(oldvg,vg)
    ast.parse(text);p=O/name;assert not p.exists();p.write_text(text);items[name]={'donor_sha256':sha(donor),'derived_sha256':sha(p)}
donor=O.parent/'compact_aw_v8/physical_snapshot.py';text=donor.read_text().replace('v8','v10').replace('for place in [3,2]:','for place in [3]:')
ast.parse(text);(O/'physical_snapshot.py').write_text(text)
text=(O.parent/'compact_aw_v9/seal_synthesis.py').read_text().replace('v9','v10').replace(oldvg,vg)
text=text.replace('SYN passed; physical trials started; not qualified for installation','SYN passed; physical trial not started; not qualified for installation')
text=text.replace("'PNR_started':True","'PNR_started':False")
ast.parse(text);(O/'seal_synthesis.py').write_text(text)
(O/'physical_runner_derivation.json').write_text(json.dumps({'scope':'Exact v10 source/VG with unchanged full physical gates. One planned fresh P3R0 after a compute slot frees; no PNR launched by preparation.',
    'VG_sha256':vg,'source55':summary['source_sha256'],'items':items},indent=2)+'\n')
print(json.dumps({'VG_sha256':vg,'physical_prepared':True,'PNR_launched':False},indent=2))
