"""Verify this bounded archive, optionally its exact staged Git bytes; read-only."""
from pathlib import Path
import hashlib,json,subprocess,sys

ROOT=Path(__file__).resolve().parents[1]
M=ROOT/'docs/WORK_ARCHIVE_20261025_26.json'
def digest(p,algorithm='sha256',git_blob=False):
 h=hashlib.new(algorithm)
 if git_blob:h.update(b'blob '+str(p.stat().st_size).encode()+b'\0')
 with p.open('rb')as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()

def main():
 assert digest(M)==M.with_suffix('.sha256').read_text().split()[0]
 m=json.loads(M.read_text(encoding='utf8'))
 for n,v in m['files'].items():
  p=(ROOT/n).resolve();assert p.is_relative_to(ROOT)and p.is_file(),n
  assert p.stat().st_size==v['bytes']and digest(p)==v['sha256'],n
 if '--check-index'in sys.argv:
  assert subprocess.check_output(['git','rev-parse','--show-object-format'],cwd=ROOT,text=True).strip()=='sha1'
  index={}
  for row in subprocess.check_output(['git','ls-files','--stage','-z'],cwd=ROOT).split(b'\0'):
   if not row:continue
   info,path=row.split(b'\t',1);mode,oid,stage=info.decode().split();assert stage=='0'
   index[path.decode('utf8')]=oid
  expected=set(m['files'])|{'docs/WORK_ARCHIVE_20261025_26.json','docs/WORK_ARCHIVE_20261025_26.sha256'}
  staged={n.decode('utf8')for n in subprocess.check_output(['git','diff','--cached','--name-only','-z'],cwd=ROOT).split(b'\0')if n}
  assert staged==expected,('Unexpected/missing staged paths',sorted(staged^expected))
  for n in expected:assert index.get(n)==digest(ROOT/n,'sha1',True),('Index bytes differ',n)
 print(json.dumps(dict(passed=True,verified_files=len(m['files']),
  omitted_local_files=len(m['omitted_local_files']),staged_index_checked='--check-index'in sys.argv,
  scope='Exact current archive hashes; no original full-package/hardware replay'),indent=2))
if __name__=='__main__':main()
