"""Publish completed, unchanged regression receipts with stable evidence hashes."""
from pathlib import Path
import datetime, hashlib, json

D = Path(__file__).resolve().parent
R = D.parents[3]
S = R / 'candidates/idle_gain_integral_ce/source'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
inputs = json.loads((D/'regression_input.json').read_text())
result = json.loads((D/'regression_results.json').read_text())
source = {p.relative_to(S).as_posix():sha(p) for p in S.rglob('*') if p.is_file() and 'impl' not in p.parts and p.suffix not in ('.log','.bak','.user')}
baseline = {p.relative_to(R/'test_baseline').as_posix():sha(p) for p in (R/'test_baseline').rglob('*') if p.is_file()}
assert source == inputs['candidate_source_sha256'] == result['candidate_source_sha256'] and len(source) == 55
assert baseline == inputs['test_baseline_sha256']
assert all(sha(R/n) == h for n,h in inputs['original_script_sha256'].items())
for name,filename in [('numerical','control_results.json'),('top_safety','top_safety_results.json'),('contention','results.json')]:
    exit_receipt = json.loads((D/name/'process_exit.json').read_text())
    suite_result = json.loads((D/name/filename).read_text())
    assert exit_receipt['exit_code'] == exit_receipt['p_wait_return'] == 0
    assert suite_result['passed'] is True
assert json.loads((D/'top_safety/top_safety_results.json').read_text())['cases'] == 13
assert result['passed'] is True
result['published_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
result['publication_note'] = ('Only stable evidence hashes and the requested results.json alias were finalized after the runner completed; test scripts, assertions, stimuli, source, and suite results were not changed. Orchestrator stdout/stderr and report files are excluded from evidence hashes to avoid self-reference.')
excluded = {'results.json','regression_results.json','orchestrator.stdout.log','orchestrator.stderr.log'}
result['evidence_sha256'] = {p.relative_to(D).as_posix():sha(p) for p in D.rglob('*') if p.is_file() and p.suffix not in ('.vvp','.pyc') and 'tmp' not in p.parts and '__pycache__' not in p.parts and not (p.parent == D and p.name in excluded)}
serialized = json.dumps(result, indent=2) + '\n'
(D/'regression_results.json').write_text(serialized)
(D/'results.json').write_text(serialized)
assert all(sha(D/n) == h for n,h in result['evidence_sha256'].items())
print(json.dumps(dict(passed=True, results_sha256=sha(D/'results.json'), numerical_groups=len(result['numerical_checks']), top_safety_cases=result['top_safety_cases'], contention=result['contention'], evidence_files=len(result['evidence_sha256'])), indent=2))
