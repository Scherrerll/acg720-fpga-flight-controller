from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def verify():
 c=json.loads((ROOT/'source_contract.json').read_text());parent=Path(c['parent'])
 assert sha(parent/'qualification.json')==c['parent_qualification_sha256']
 for name,h in c['parent_fixture_sha256'].items():
  assert sha(parent/'fixture'/name)==h,('Frozen parent changed',name)
  assert sha(ROOT/'fixture'/name)==c['allowed_changes'].get(name,h),('Candidate source changed',name)
 assert set(c['allowed_changes'])=={'acg720_ano_port.v','sensor/mtf01p_reader.v','build_project.py'}
 assert (ROOT/'DO_NOT_PROGRAM').is_file()
 return dict(passed=True,parent_unmodified=True,hardware_accessed=False)
if __name__=='__main__':print(json.dumps(verify()))
