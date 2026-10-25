"""Candidate-only paired protocol, real UART and late-ready contract checks."""
from pathlib import Path
import hashlib,json,subprocess,sys
C=Path(__file__).resolve().parent;R=C.parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def tree(root):return {p.relative_to(root).as_posix():sha(p)for p in root.rglob('*')if p.is_file() and 'impl'not in p.parts and p.suffix not in ('.log','.bak','.user')}
record=json.loads((C/'change.json').read_text());assert tree(R/'source')==record['canonical_source_sha256'];assert tree(C/'source')==record['candidate_source_sha256']
for name in ['verify_pair.py','verify_link.py','verify_contract.py']:
 c=subprocess.run([sys.executable,'-B',str(C/name)],cwd=R,capture_output=True,text=True)
 (C/'verification'/f'{name}.stdout.log').write_text(c.stdout+c.stderr)
 print(c.stdout+c.stderr,flush=True);assert c.returncode==0,(name,c.stdout+c.stderr)
assert tree(R/'source')==record['canonical_source_sha256'];assert tree(C/'source')==record['candidate_source_sha256']
print('PASS response-only fallback checks; canonical55 files unchanged',flush=True)
