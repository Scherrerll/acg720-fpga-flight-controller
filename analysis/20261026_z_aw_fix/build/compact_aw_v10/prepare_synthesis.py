"""Prepare one proof-gated v10 SYN-only run from exact v9 donor."""
from pathlib import Path
import ast,hashlib,json,re
O=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
proof=json.loads((O/'proofs_retry02/results.json').read_text());ex=json.loads((O/'proofs_retry02/runner_exit.json').read_text())
assert proof['passed'] and ex['actual_p_wait']==0 and ex['normal_wait_return']
donor=O.parent/'compact_aw_v9/run_synthesis.py';text=donor.read_text().replace('v9','v10').replace('v4','v9')
text,n=re.subn(r'    helper\.EXPECTED_CHANGES=.*\n','',text,count=1);assert n==1
marker="    baseline=json.loads((R/'firmware/B0B3/qualification.json').read_text())['source_sha256']\n";assert text.count(marker)==1
text=text.replace(marker,marker+"    helper.EXPECTED_CHANGES={p:expected[p] for p in expected if expected[p]!=baseline[p]}\n    assert len(helper.EXPECTED_CHANGES)==7\n")
ast.parse(text);p=O/'run_synthesis.py';assert not p.exists();p.write_text(text)
supervisor=O.parent/'compact_aw_v9/launch_synthesis_hidden.py';p=O/'launch_synthesis_hidden.py';assert not p.exists();p.write_bytes(supervisor.read_bytes())
(O/'synthesis_runner_derivation.json').write_text(json.dumps({'scope':'v9 exact donor, one diagnostic file change, all seven existing B3-relative paths frozen. Original physical/clock/radio/gain/18ports gates unchanged. SYN only.',
    'donor_runner_sha256':sha(donor),'derived_runner_sha256':sha(O/'run_synthesis.py'),'proofs_sha256':sha(O/'proofs_retry02/results.json'),
    'proof_runner_exit_sha256':sha(O/'proofs_retry02/runner_exit.json'),'proof_runner_actual_wait':0},indent=2)+'\n')
snapshot=(O.parent/'compact_aw_v9/seal_source_snapshot.py').read_text().replace('v9','v10').replace('v10_v4_guard','v10_z_diag_snapshot')
ast.parse(snapshot);(O/'seal_source_snapshot.py').write_text(snapshot)
print('Prepared one v10 SYN-only run; exact source snapshot script prepared.')
