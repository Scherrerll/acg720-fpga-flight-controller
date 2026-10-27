"""Derive one v8 SYN-only run; require exact focused proof and frozen v7 donor."""
from pathlib import Path
import ast,hashlib,json
O=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
proof=json.loads((O/'proofs_completion02/results.json').read_text())
exit=json.loads((O/'proofs_completion02/runner_exit.json').read_text())
freeze=json.loads((O/'source_freeze.json').read_text())
assert proof['passed'] and exit['actual_p_wait']==0 and exit['normal_wait_return']
assert proof['source55']['v8']==freeze['source55']
donor=O.parent/'compact_aw_v7/run_synthesis.py'
text=donor.read_text().replace('v7','v8').replace('v5','v7')
old="assert prior['position/mtf_xyz_hold_control.v']=='04e75ada52551d5622af060efe38fda9aa66ff25199bfb67651f9ec5315ed873'"
assert text.count(old)==1
text=text.replace(old,"assert prior['position/mtf_xyz_hold_control.v']==HOLD_SHA")
old="assert [p for p in expected if expected[p]!=prior[p]]==['position/mtf_xyz_hold_control.v']"
assert text.count(old)==1
text=text.replace(old,"assert sorted(p for p in expected if expected[p]!=prior[p])==sorted(freeze['changed_files'])")
old="    assert sha(O.parent/'sign_step_bound.md')==freeze['proof_sha256']\n"
assert text.count(old)==1
text=text.replace(old,"    proof=json.loads((O/'proofs_completion02/results.json').read_text());proof_exit=json.loads((O/'proofs_completion02/runner_exit.json').read_text())\n    assert proof['passed'] and proof_exit['actual_p_wait']==0 and proof_exit['normal_wait_return'] and proof['source55']['v8']==expected\n")
old="helper.EXPECTED_CHANGES={**helper.EXPECTED_CHANGES,'position/mtf_xyz_hold_control.v':HOLD_SHA}"
assert text.count(old)==1
text=text.replace(old,"helper.EXPECTED_CHANGES={**helper.EXPECTED_CHANGES,**{p:expected[p] for p in freeze['changed_files']},'position/mtf_xyz_hold_control.v':HOLD_SHA}")
text=text.replace("'changed_from_v7':['position/mtf_xyz_hold_control.v']","'changed_from_v7':freeze['changed_files']")
needle="'source_review_sha256':sha(O/'source_review.md'),'runner_sha256':sha(Path(__file__)),"
assert text.count(needle)==1
text=text.replace(needle,"'source_review_sha256':sha(O/'source_review.md'),'focused_proof_sha256':sha(O/'proofs_completion02/results.json'),'proof_runner_exit_sha256':sha(O/'proofs_completion02/runner_exit.json'),'runner_sha256':sha(Path(__file__)),")
ast.parse(text)
dest=O/'run_synthesis.py';assert not dest.exists();dest.write_text(text)
supdonor=O.parent/'compact_aw_v7/launch_synthesis_hidden.py'
sup=supdonor.read_text()
ast.parse(sup)
dest=O/'launch_synthesis_hidden.py';assert not dest.exists();dest.write_text(sup)
(O/'synthesis_runner_derivation.json').write_text(json.dumps({'source_runner':str(donor),'source_runner_sha256':sha(donor),
    'derived_runner_sha256':sha(O/'run_synthesis.py'),'supervisor_source_sha256':sha(supdonor),
    'focused_proof_sha256':sha(O/'proofs_completion02/results.json'),'proof_runner_actual_wait':0,
    'scope':'One full-top SYN only; frozen vendor/mapped/clock/radio/gain/18-port gates unchanged. No PNR.'},indent=2)+'\n')
print('Prepared one proof-gated v8 SYN-only runner.')
