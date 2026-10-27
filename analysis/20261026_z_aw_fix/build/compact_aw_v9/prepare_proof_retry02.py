"""Preserve failed launcher01; correct only its fixture self-filename in new02."""
from pathlib import Path
import ast,hashlib,json,shutil
O=Path(__file__).resolve().parent;old=O/'proofs';new=O/'proofs_retry02'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text())
ex=read(old/'runner_exit.json');fx=read(old/'five_exit.json')
assert ex['actual_p_wait']==fx['actual_p_wait']==1
assert 'FileNotFoundError' in (old/'five.stderr.log').read_text() and 'run_regression.py' in (old/'five.stderr.log').read_text()
assert not (old/'five/compile.log').exists() and not new.exists()
new.mkdir()
for kind in ['five','boundary','top','contention']:shutil.copytree(old/kind,new/kind)
p=new/'five/run.py';t=p.read_text();assert t.count("O/'run_regression.py'")==1
p.write_text(t.replace("O/'run_regression.py'","O/'run.py'"))
t=(O/'verify_candidate.py').read_text().replace("D=O/'proofs'","D=O/'proofs_retry02'")
ast.parse(t);(O/'verify_retry02.py').write_text(t)
t=(O/'launch_proofs_hidden.py').read_text().replace("D=O/'proofs'","D=O/'proofs_retry02'").replace("O/'verify_candidate.py'","O/'verify_retry02.py'")
ast.parse(t);(O/'launch_retry02_hidden.py').write_text(t)
(O/'PROOF_LAUNCH_CORRECTION.json').write_text(json.dumps({'failure_class':'fixture_self_filename_missing_before_compile_or_simulation',
    'original_runner_actual_wait':1,'original_five_actual_wait':1,'original_exit_sha256':sha(old/'runner_exit.json'),
    'original_driver_sha256':sha(old/'five/run.py'),'corrected_driver_sha256':sha(new/'five/run.py'),
    'change':"Copied driver references its new run.py filename; no assertions/RTL changed.",
    'no_original_receipts_overwritten':True,'no_completed_simulations_to_repeat':True},indent=2)+'\n')
print('Prepared proof retry02; launch01 failure retained and no simulation duplicated.')
