"""Keep fixture01 failure; complete declarations and forbid implicit nets in02."""
from pathlib import Path
import ast,hashlib,json
O=Path(__file__).resolve().parent;D=O/'proofs'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text())
ex=read(D/'runner_exit.json');cx=read(D/'diagnostic_compile_exit.json')
assert ex['actual_p_wait']==1 and cx['actual_p_wait']==4 and not (D/'diagnostic_simulation_exit.json').exists()
assert 'Unable to bind wire/reg/memory `z_reason' in (D/'diagnostic_compile.log').read_text()
t=(O/'verify_candidate.py').read_text().replace("D=O/'proofs'","D=O/'proofs_retry02'")
t=t.replace("decl='''module diag_@TAG@", "decl='''`default_nettype none\nmodule diag_@TAG@")
t=t.replace('input [639:0] payload','input [671:0] payload')
needle='wire [31:0] controller_target_height=payload[637:606];';assert t.count(needle)==1
t=t.replace(needle,needle+'\nwire [15:0] z_reason=payload[655:640];\nwire signed [15:0] z_throttle_delta;wire [15:0] z_collective;')
t=t.replace('reg [639:0] data=0','reg [671:0] data=0').replace('j<20;j=j+1','j<21;j=j+1')
t=t.replace("  if(n%17==0)data[111:96]=16'hxxxx;","  if(n%17==0)data[589:574]=16'hxxxx;\n  if(n%23==0)data[605:590]=16'hzzzz;")
t=t.replace("[str(IV),'-g2012','-s','tb'","[str(IV),'-g2012','-Wall','-s','tb'")
ast.parse(t);p=O/'verify_retry02.py';assert not p.exists();p.write_text(t)
t=(O/'launch_proofs_hidden.py').read_text().replace("D=O/'proofs'","D=O/'proofs_retry02'").replace("O/'verify_candidate.py'","O/'verify_retry02.py'")
ast.parse(t);p=O/'launch_retry02_hidden.py';assert not p.exists();p.write_text(t)
(O/'FIXTURE_CORRECTION.json').write_text(json.dumps({'failure_class':'extracted_fixture_missing_z_reason_and_explicit_mask_width_declarations',
    'original_compile_actual_wait':4,'original_runner_actual_wait':1,'original_compile_exit_sha256':sha(D/'diagnostic_compile_exit.json'),
    'original_runner_exit_sha256':sha(D/'runner_exit.json'),'original_driver_sha256':sha(O/'verify_candidate.py'),
    'corrected_driver_sha256':sha(O/'verify_retry02.py'),'RTL_changed':False,'original_failure_preserved':True,
    'correction':'Declare independent16bit z_reason and explicit16bit Z masked buses; default_nettype none and -Wall; directly inject X/Z into all three raw Z fields.'},indent=2)+'\n')
print('Prepared strict declared-net fixture retry02; original compile4/root1 preserved.')
