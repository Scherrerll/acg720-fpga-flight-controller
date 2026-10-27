"""Derive a P1-only runner without touching the running P2/P3 scripts."""
from pathlib import Path
import ast,hashlib,json
O=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
old=O/'run_physical.py';old_supervisor=O/'launch_physical_hidden.py'
assert sha(old)=='a25b6377c37014b7f6d6f92e2bd766c644d7a2363527118b3666bdf93edb24e0'
assert sha(old_supervisor)=='bf50260a5a7c2489739d038043f64972047369d8c1ccf01c68ebaebc3dfeb194'
new=O/'run_physical_p1r0.py';supervisor=O/'launch_physical_p1_hidden.py';report=O/'physical_p1r0_01'
assert not new.exists() and not supervisor.exists() and not report.exists()
text=old.read_text();assert text.count("sys.argv[1] in ['2','3']")==1
text=text.replace("sys.argv[1] in ['2','3']","sys.argv[1] in ['1']").replace('P3/R0 or P2/R0','P1/R0')
ast.parse(text);new.write_text(text,encoding='utf8')
text=old_supervisor.read_text();assert text.count("sys.argv[1] in ['2','3']")==1 and text.count("runner=BASE/'run_physical.py'")==1
text=text.replace("sys.argv[1] in ['2','3']","sys.argv[1] in ['1']").replace("runner=BASE/'run_physical.py'","runner=BASE/'run_physical_p1r0.py'")
ast.parse(text);supervisor.write_text(text,encoding='utf8');report.mkdir()
assert sha(old)=='a25b6377c37014b7f6d6f92e2bd766c644d7a2363527118b3666bdf93edb24e0'
assert sha(old_supervisor)=='bf50260a5a7c2489739d038043f64972047369d8c1ccf01c68ebaebc3dfeb194'
(report/'runner_derivation.json').write_text(json.dumps(dict(scope='Root-authorized final extra v6 P1/R0 profile only; copied P3/P2 logic, no gate/source/timing change.',
    original_runner_sha256=sha(old),original_supervisor_sha256=sha(old_supervisor),runner_sha256=sha(new),supervisor_sha256=sha(supervisor)),indent=2)+'\n',encoding='utf8')
print('P1-only runner and hidden supervisor ready; existing scripts unchanged')
