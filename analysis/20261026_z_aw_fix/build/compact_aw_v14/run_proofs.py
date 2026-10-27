"""v14 proof supervisor: exact semantic source reversion plus unchanged full top13 stimulus."""
from pathlib import Path
import datetime,hashlib,json,os,subprocess,sys
sys.dont_write_bytecode=True
O=Path(__file__).resolve().parent;R=O.parents[3];D=O/'proofs';P=O.parent/'v4_release_proofs'
C=R/'out/z_aw_fix_20261026/compact_aw_v14/canonical/source'
OLD=R/'out/z_aw_fix_20261026/compact_aw_v4/canonical/source'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf8'))
utc=lambda:datetime.datetime.now(datetime.timezone.utc).isoformat()
assert not (D/'runner_process.json').exists() and not (O/'PROOF_BINDING.json').exists()
freeze=read(O/'source_freeze.json');expected=freeze['source55'];before=freeze['baseline_source55']
assert len(expected)==55 and {n:sha(C/n) for n in expected}==expected
assert {n:sha(OLD/n) for n in before}==before
assert sha(O/'source_review.md')==freeze['source_review_sha256']
assert sha(O/'SOURCE_EQUIVALENCE_BASIS.json')==freeze['source_equivalence_basis_sha256']
basis=read(O/'SOURCE_EQUIVALENCE_BASIS.json');semantic={};normalised=[]
for name,change in basis['transformations'].items():
    actual=(C/name).read_text(encoding='utf8');original=(OLD/name).read_text(encoding='utf8')
    assert actual.count(change['after'])==1
    restored=actual.replace(change['after'],change['before'])
    assert restored==original and sha(C/name)==change['candidate_sha256']
    if (OLD/name).read_bytes()!=original.encode():normalised.append(name)
    semantic[name]={'normalized_original_text_sha256':hashlib.sha256(original.encode()).hexdigest(),
        'reverted_candidate_text_sha256':hashlib.sha256(restored.encode()).hexdigest(),
        'original_bytes_sha256':sha(OLD/name),'candidate_bytes_sha256':sha(C/name),'exact_normalized_text_equal':True}
assert [n for n in expected if expected[n]!=before[n]]==list(basis['transformations'])
parent=read(P/'RESULT.json');parent_exit=read(P/'runner_exit.json')
assert parent['passed'] and parent['source55']==before and parent_exit['actual_p_wait']==0 and parent_exit['normal_wait_return']
for name,key in [('inputs.json','inputs_sha256'),('runner_exit.json','runner_exit_sha256'),('top_safety_results.json','top13_result_sha256')]:assert sha(P/name)==parent[key]
derivation=read(O/'TOP13_RUNNER_DERIVATION.json')
assert sha(P/'run_top13.py')==derivation['parent_runner_sha256'] and sha(D/'run_top13.py')==derivation['new_runner_sha256']
bound={str(p):sha(p) for p in [O/'source_freeze.json',O/'source_review.md',O/'SOURCE_EQUIVALENCE_BASIS.json',O/'TOP13_RUNNER_DERIVATION.json',P/'RESULT.json',P/'inputs.json',P/'runner_exit.json',P/'top_safety_tb.v',D/'run_top13.py',Path(__file__)]}
(D/'inputs.json').write_text(json.dumps({'source55':expected,'parent_source55':before,'bound_files':bound,
    'source_semantic_reversions':semantic,'line_endings_normalized_without_token_change':normalised,
    'scope':'Only a synthesis comment and plain combinational wire alias/comment differ after newline normalization; no control expression, operator, state, FF or clock changes. Existing v4 controller/FRAC/arbitration/ground proof dependency bindings reused. New full top13 runs below.'},indent=2)+'\n',encoding='utf8')
command=[sys.executable,'-B','-X','utf8',str(D/'run_top13.py')]
record={'command':command,'started_utc':utc(),'supervisor_pid':os.getpid(),'supervisor_sha256':sha(Path(__file__))}
with (D/'runner.stdout.log').open('wb') as output,(D/'runner.stderr.log').open('wb') as error:
    child=subprocess.Popen(command,stdin=subprocess.DEVNULL,stdout=output,stderr=error,cwd=R,creationflags=subprocess.CREATE_NO_WINDOW)
    record['pid']=child.pid;(D/'runner_process.json').write_text(json.dumps(record,indent=2)+'\n')
    code=child.wait()
record.update(actual_p_wait=code,normal_wait_return=True,ended_utc=utc(),stdout_sha256=sha(D/'runner.stdout.log'),stderr_sha256=sha(D/'runner.stderr.log'))
(D/'runner_exit.json').write_text(json.dumps(record,indent=2)+'\n')
assert code==0
assert read(D/'top_safety_results.json')['passed'] and read(D/'top_safety_results.json')['cases']==13
assert all(read(D/(name+'_exit.json'))['normal_return'] and read(D/(name+'_exit.json'))['actual_completedprocess_returncode']==0 for name in ['compile','vvp'])
assert sha(D/'top_safety_tb.v')==sha(P/'top_safety_tb.v'),'Original testbench stimulus bytes changed'
assert {str(p):sha(p) for p in map(Path,bound)}==bound
assert {n:sha(C/n) for n in expected}==expected and {n:sha(OLD/n) for n in before}==before
result={'passed':True,'source55':expected,'actual_proof_runner_wait':code,'parent_proof':str(P/'RESULT.json'),
    'parent_proof_sha256':sha(P/'RESULT.json'),'inputs_sha256':sha(D/'inputs.json'),'actual_top13_runner_exit_sha256':sha(D/'runner_exit.json'),
    'top13_result_sha256':sha(D/'top_safety_results.json'),'top13':{'passed':True,'cases':13,'actual_root_wait':code,'compile_and_vvp_actual_waits':[0,0]},
    'source_semantic_reversions':semantic,'line_endings_normalized_without_token_change':normalised,
    'scope':'New exact-source top13 plus mechanically checked source-only synthesis hints and combinational identity alias. Exact unchanged controller/math/parameter/ground dependencies reuse parent actual successful proofs. No new five-case run, SYN, physical, installation or flight claim.'}
(O/'PROOF_BINDING.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
print(json.dumps({'passed':True,'source_files':55,'new_top13_cases':13,'actual_root_wait':code,'compile_and_vvp_actual_waits':[0,0],'source_reversion_passed':True,'hardware_operation':False}))
