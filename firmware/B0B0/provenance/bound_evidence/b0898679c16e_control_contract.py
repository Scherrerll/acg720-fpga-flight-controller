from pathlib import Path
import json,hashlib
ROOT=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def verify():
 c=json.loads((ROOT/'source_contract.json').read_text());N=Path(c['parent'])
 assert sha(N/'qualification.json')==c['parent_qualification_sha256']
 assert set(c['allowed_changes'])=={'acg720_ano_port.v','telemetry_tx.v','build_project.py'}
 for n,h in c['parent_sources_sha256'].items():
  assert sha(N/'fixture'/n)==h,('Parent changed',n)
  assert sha(ROOT/'fixture'/n)==c['allowed_changes'].get(n,h),('Current source changed',n)
 assert sha(Path(c['independent_mtf_reference']))==c['independent_mtf_reference_sha256']
 assert (ROOT/'DO_NOT_PROGRAM').is_file()
 return dict(passed=True,hardware_accessed=False)
if __name__=='__main__':print(json.dumps(verify()))
