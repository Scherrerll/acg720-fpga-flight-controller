"""Wait for the current source-bound proof, then invoke the strict50MHz build."""
from pathlib import Path
import hashlib,json,re,subprocess,sys,time
R=Path(__file__).resolve().parent;F=R/'fixture'
def current():
 names=re.findall(r'<File path="([^"]+)"',(F/'acg720_ano_port.gprj').read_text())+['acg720_ano_port.gprj','build.tcl']
 return {n:hashlib.sha256((F/n).read_bytes()).hexdigest()for n in names}
expected=current();start=time.monotonic()
print('Waiting for current source-bound offline qualification; no hardware access.',flush=True)
while True:
 if current()!=expected:raise RuntimeError('Source changed while awaiting qualification')
 try:q=json.loads((R/'qualification.json').read_text())
 except (OSError,json.JSONDecodeError):q={}
 if q.get('offline_tests_passed') and q.get('sources_sha256')==expected:break
 if time.monotonic()-start>900:raise RuntimeError('Qualification not available; build not started')
 time.sleep(1)
print('Current qualification found. Starting synthesis/place/route;50MHz acceptance remains mandatory.',flush=True)
p=subprocess.run([sys.executable,str(F/'build_project.py')],cwd=F)
raise SystemExit(p.returncode)
