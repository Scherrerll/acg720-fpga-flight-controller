from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def verify():
 d=json.loads((ROOT/'published_anchor_delta.json').read_text());parent=Path(d['reference'])
 assert set(d['files'])=={'core/flight_core.v','core/height_loss_fallback.v'}
 for n,h in d['files'].items():assert sha(parent/'fixture'/n)==h['reference_sha256'] and sha(ROOT/'fixture'/n)==h['candidate_sha256']
 assert sha(ROOT/'hardware/published_anchor.patch')==d['reviewed_patch_sha256']
 pre=json.loads((ROOT/'tests/published_anchor.prefix_failure.json').read_text())
 assert pre['expected_failure_observed'] is True and pre['passed'] is False and pre['checks']==13 and pre['failure_count']==10
 assert pre['bench_sha256']==sha(ROOT/'tests/published_anchor.v')
 for n,h in pre['rtl_sha256'].items():assert sha(Path(n))==h
 assert pre['log_sha256']==sha(ROOT/'tests/published_anchor.prefix_failure.log')
 post=json.loads((ROOT/'tests/published_anchor.proof.json').read_text());assert post['passed'] is True
 for n,h in post['source_sha256'].items():
  p=Path(n);assert sha(p if p.is_absolute()else ROOT/p)==h
 assert '13 checks' in (ROOT/'tests/published_anchor.log').read_text()
 return dict(passed=True,pre_fix_failures=10,post_fix_checks=13,scope='Exact same directed bench; preserved old RTL failure and current two-file repair success; physical gates separately tested by full core regression.')
if __name__=='__main__':print(json.dumps(verify()))
