"""Run current candidate RTL checks, then the source-bound final proof gate."""
from test_tools import *
from control_contract import verify
verify()
for script in ['test_declarations.py','test_component.py','test_fallback_core.py','test_published_anchor.py','test_nominal_equivalence.py','test_tools.py','test_wire.py']:
 p=subprocess.run([os.sys.executable,str(ROOT/script)],capture_output=True,text=True,encoding='utf-8',errors='replace',env=ENV,timeout=600)
 (ROOT/'tests'/('qualification_'+Path(script).stem+'.log')).write_text(p.stdout+p.stderr,encoding='utf8')
 if p.returncode:raise RuntimeError(script+': '+(p.stdout+p.stderr)[-3000:])
 print(script+' PASS',flush=True)
subprocess.run([os.sys.executable,str(ROOT/'finalize_current_proofs.py')],check=True,env=ENV)
