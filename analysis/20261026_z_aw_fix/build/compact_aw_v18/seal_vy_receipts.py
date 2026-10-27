"""Bind successful actual waits to a uniform schema without changing originals."""
from pathlib import Path
import datetime,hashlib,json
O=Path(__file__).resolve().parent;P=O/'vy_proofs';R=O.parents[3]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf8'))
result=P/'RESULT.json';data=read(result);assert data['passed']
D=Path(data['attempt_directory']);assert D.resolve().is_relative_to(P.resolve())
inputs=D/'inputs.json';bound=read(inputs)
assert sha(inputs)==data['inputs_sha256']
assert all(sha(Path(p))==h for p,h in bound['bound_files'].items())
record=read(O/'VY_SOURCE_CHANGES.json')
assert data['source55']==record['source55']==bound['source55'] and len(data['source55'])==55
for prefix,key in [('compact_aw_v17','baseline_source55'),('compact_aw_v18','source55')]:
    assert all(sha(R/'out/z_aw_fix_20261026'/prefix/'canonical/source'/n)==h for n,h in data[key].items())
root=Path(data['supervisor_exit_receipt']);root_record=read(root)
assert sha(root)==data['supervisor_exit_receipt_sha256']
assert root_record['normal_wait_return'] and root_record['actual_proof_supervisor_child_wait']==0
assert root_record['supervisor_script_sha256']==sha(O/'supervise_vy_proofs.py')
assert root_record['runner_sha256']==sha(O/'run_vy_proofs.py')
assert root_record['stdout_sha256']==sha(P/(D.name+'_supervisor.stdout.log'))
assert root_record['stderr_sha256']==sha(P/(D.name+'_supervisor.stderr.log'))
files=[('root',root,'actual_proof_supervisor_child_wait')]
for stage in ['metric_compile','metric_vvp','uart_mode0_compile','uart_mode0_vvp','uart_mode1_compile','uart_mode1_vvp','geometry_compile','geometry_vvp']:
    p=D/(stage+'_exit.json');s=read(p)
    assert s['normal_wait_return'] and s['actual_child_p_wait']==0 and not s.get('terminated_after_timeout')
    assert s['stdout_sha256']==sha(D/(stage+'.stdout.log')) and s['stderr_sha256']==sha(D/(stage+'.stderr.log'))
    files.append((stage,p,'actual_child_p_wait'))
A=P/'successful_wait_receipts';assert not A.exists();A.mkdir()
exits={};originals={}
for name,p,key in files:
    source=read(p);adapter=A/(name+'_exit.json')
    original_relative=p.relative_to(P).as_posix()
    adapter.write_text(json.dumps(dict(normal_wait_return=source['normal_wait_return'],actual_p_wait=source[key],
        original_receipt=original_relative,original_receipt_sha256=sha(p),original_actual_wait_field=key,
        schema_adapter_only=True,scope='The original recorded actual Popen.wait return is preserved. This file maps its descriptive field name to the common release-validator schema; no process is rerun.'),indent=2)+'\n',encoding='utf8')
    exits[adapter.relative_to(P).as_posix()]=sha(adapter);originals[original_relative]=sha(p)
data.update(exit_receipts_base='Paths are relative to this vy_proofs directory.',exit_receipts=exits,
    original_actual_wait_receipts=originals,actual_successful_root_wait=0,successful_compile_and_vvp_waits=[0]*8,
    inputs_file=inputs.relative_to(P).as_posix(),sealed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    receipt_sealer_sha256=sha(Path(__file__)),all_successful_receipts_only=True)
result.write_text(json.dumps(data,indent=2)+'\n',encoding='utf8')
print(json.dumps(dict(passed=True,result=str(result),successful_receipts=len(exits),source55=len(data['source55']),attempt=D.name)))
