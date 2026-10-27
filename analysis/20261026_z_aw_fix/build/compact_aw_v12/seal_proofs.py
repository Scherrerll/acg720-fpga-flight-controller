"""Seal real completed proof receipts and immutable stimulus files, without reruns."""
from pathlib import Path
import datetime,hashlib,json
O=Path(__file__).resolve().parent;R=O.parents[3];D=O/'proofs'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text())
q=O/'PROOF_BINDING.json';assert not q.exists()
inputs=read(D/'inputs.json');results=read(D/'results.json');root=read(D/'runner_exit.json')
assert results['passed'] and root['actual_p_wait']==0 and root['normal_wait_return']
assert sha(O/'run_proofs.py')==root['runner_sha256']==inputs['runner_sha256']
for role,tag in [('old','v11'),('new','v12')]:
    s=R/f'out/z_aw_fix_20261026/compact_aw_{tag}/canonical/source';expected=inputs['source55'][role]
    assert {p:sha(s/p) for p in expected}==expected
sources={n:h for n,h in inputs['fixtures'].items() if n.endswith('.v') or n.replace('\\','/')=='top/run.py'}
assert len(sources)==6 and all(sha(D/n)==h for n,h in sources.items())
for stage in results['stages']:
    assert stage['normal_wait_return'] and stage['actual_p_wait']==0
for p in D.glob('*_exit.json'):
    x=read(p);assert x['normal_wait_return'] and x['actual_p_wait']==0
    if 'log_sha256' in x:
        log=D/p.name.replace('_exit.json','.log');assert sha(log)==x['log_sha256']
assert len(results['records'])==8 and results['top13']['passed']
assert len(results['stages'])==19 and 'PASS predicate vectors=200040 integer_limits=9' in (D/'predicate_simulation.log').read_text()
items={str(p.relative_to(R)):{'sha256':sha(p),'bytes':p.stat().st_size} for p in D.rglob('*') if p.is_file() and p.suffix not in ['.vvp'] and 'tmp' not in p.parts}
q.write_text(json.dumps({'sealed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'passed':True,'actual_proof_runner_wait':0,
    'source55':inputs['source55']['new'],'immutable_fixture_subset':sources,'records':results['records'],'top13':results['top13'],
    'initial_index_note':'Six immutable stimulus files only, all checked against initial hashes. Runtime logs are not indexed as stimuli.',
    'artifacts':items,'scope':'Functional equivalence/expiry only; no SYN/physical/hardware qualification.'},indent=2)+'\n')
print('Sealed v12: eight fusion/expiry cases,top13,19 actual stage waits0,root wait0; six initial stimulus hashes unchanged.')
