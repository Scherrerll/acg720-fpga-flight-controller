"""Seal v13 actual successful proof receipts; no test rerun or vendor operation."""
from pathlib import Path
import datetime, hashlib, json
O=Path(__file__).resolve().parent;R=O.parents[3];D=O/'proofs'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf8'))
output=O/'PROOF_BINDING.json';assert not output.exists()
inputs=read(D/'inputs.json');results=read(D/'results.json');root=read(D/'runner_exit.json')
assert results['passed'] and root['actual_p_wait']==0 and root['normal_wait_return']
assert sha(O/'run_proofs.py')==root['runner_sha256']
assert sha(O/'source_review.md')==inputs['source_review_sha256']
assert sha(D/'runner.stdout.log')==root['stdout_sha256'] and sha(D/'runner.stderr.log')==root['stderr_sha256']
for tag,key in [('v12','baseline_source55'),('v13','source55')]:
    source=R/f'out/z_aw_fix_20261026/compact_aw_{tag}/canonical/source'
    assert {n:sha(source/n) for n in inputs[key]}==inputs[key]
assert len(inputs['fixtures'])==6
assert all(sha(D/n)==h for n,h in inputs['fixtures'].items())
assert len(results['stages'])==7 and len(results['UART'])==2 and results['top13']['passed']
for stage in results['stages']:assert stage['normal_wait_return'] and stage['actual_p_wait']==0
actual_stages=[]
for p in D.glob('*_exit.json'):
    receipt=read(p);assert receipt['normal_wait_return'] and receipt['actual_p_wait']==0
    if 'log_sha256' in receipt:assert sha(D/p.name.replace('_exit.json','.log'))==receipt['log_sha256']
    if p.name!='runner_exit.json':actual_stages.append(receipt)
assert sorted(map(json.dumps,actual_stages))==sorted(map(json.dumps,results['stages']))
assert all(sha(Path(name))==digest for name,digest in inputs['tools'].items())
assert 'PASS inductive vectors=105632' in (D/'inductive_simulation.log').read_text()
for mode in [0,1]:
    assert f'PASS UART MODE={mode} ' in (D/f'uart_mode{mode}_simulation.log').read_text()
parent=O.parent/'compact_aw_v12/PROOF_BINDING.json'
assert sha(parent)==inputs['parent_proof_binding_sha256']
previous=read(parent);assert previous['passed'] and previous['source55']==inputs['baseline_source55']
for name,item in previous['artifacts'].items():
    path=R/name
    assert path.resolve().is_relative_to(R) and path.name.lower()!='deployment.env' and '.env' not in path.suffixes
    assert sha(path)==item['sha256'] and path.stat().st_size==item['bytes']
artifacts={p.relative_to(R).as_posix():{'sha256':sha(p),'bytes':p.stat().st_size}
           for p in D.rglob('*') if p.is_file() and p.suffix!='.vvp' and 'tmp' not in p.parts}
output.write_text(json.dumps({'sealed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'passed':True,'actual_proof_runner_wait':0,'source55':inputs['source55'],
    'immutable_fixtures':inputs['fixtures'],'UART':results['UART'],'top13':results['top13'],
    'parent_v12_proof_binding_sha256':sha(parent),'parent_artifacts_rechecked':len(previous['artifacts']),
    'parent_source_difference':['sensor/mtf01p_reader.v'],'artifacts':artifacts,
    'scope':'Reader same-clock equivalence and reused exact unchanged v12 dependencies; no SYN/PNR/hardware qualification.'},indent=2)+'\n')
print(json.dumps({'proofs_sealed':True,'actual_stage_waits0':7,'actual_root_wait':0,
                  'inductive_vectors':105632,'parent_artifacts_rechecked':len(previous['artifacts'])}))
