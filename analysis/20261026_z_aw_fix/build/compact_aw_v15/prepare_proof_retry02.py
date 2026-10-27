"""Preserve first actual compile3; correct only invalid testbench identifiers/ANSI declarations."""
from pathlib import Path
import ast, hashlib, json, re, shutil
O=Path(__file__).resolve().parent;old=O/'run_proofs.py';new=O/'run_proofs_retry02.py'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert not new.exists() and not (O/'proofs_retry02').exists()
text=old.read_text(encoding='utf8').replace("D=O/'proofs'", "D=O/'proofs_retry02'")
# ANSI output initialization is separate from the output declaration for this Iverilog build.
text=text.replace('output reg saw_prepared=0,saw_takeoff=0,saw_flying=0,saw_land=0);','output reg saw_prepared,saw_takeoff,saw_flying,saw_land);\ninitial begin saw_prepared=0;saw_takeoff=0;saw_flying=0;saw_land=0;end')
# automatic is a reserved Verilog lifetime keyword; only this standalone bench identifier changes.
text=re.sub(r'\bautomatic\b','auto_value',text)
ast.parse(text);new.write_text(text,encoding='utf8')
(O/'proofs_retry02').mkdir();shutil.copy2(O/'proofs/run_top13.py',O/'proofs_retry02/run_top13.py')
record=dict(first_compile_actual_wait=3,first_compile_receipt_sha256=sha(O/'proofs/fsm_compile_exit.json'),first_inputs_sha256=sha(O/'proofs/inputs.json'),first_runner_sha256=sha(old),new_runner_sha256=sha(new),changes=['Bench identifier automatic to auto_value','Bench initialized output registers declared then initialized explicitly'],stimulus_and_all_assertions_unchanged=True,RTL_unchanged=True)
(O/'PROOF_RETRY02_DERIVATION.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf8')
print(json.dumps(record))
