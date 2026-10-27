"""Read and reconcile the frozen handoff without changing its bytes."""
from pathlib import Path
import datetime, hashlib, json

O=Path(__file__).resolve().parent; R=O.parents[3]
A=R/'analysis/20261026_z_aw_fix/handoff_20261026'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf8',errors='replace'))
manifest=read(A/'MANIFEST.json')
assert sha(A/'MANIFEST.json')==(A/'MANIFEST.sha256').read_text().split()[0]
archive=[]
for item in manifest['files']:
    p=A/item['path']; assert sha(p)==item['sha256'] and p.stat().st_size==item['bytes']
    archive.append(item['path'])
state=read(A/'STATE.json'); refs=[]
for name,item in state['evidence_refs'].items():
    p=R/name; resolved_by_hash=False
    if not p.is_file():
        matches=[q for q in (R/'ground/B0B4').iterdir() if q.is_file() and q.stat().st_size==item['bytes'] and sha(q)==item['sha256']]
        assert len(matches)==1,(name,'unresolved reference')
        p=matches[0]; resolved_by_hash=True
    assert sha(p)==item['sha256'] and p.stat().st_size==item['bytes']
    refs.append({'archive_path':name,'actual_path':p.relative_to(R).as_posix(), 'matched':True,'resolved_by_unique_hash':resolved_by_hash})
freeze=read(O/'source_freeze.json'); source=Path(state['v7']['source_root'])
assert len(freeze['source55'])==55
assert {p:sha(source/p) for p in freeze['source55']}==freeze['source55']
assert sha(Path(state['v7']['VG']))==state['v7']['VG_sha256']
aw=read(R/'analysis/20261026_z_aw_fix/aw_storage_regression/results.json')
assert aw['completed']==5 and aw['passed'] is True and len(aw['results'])==5
assert all(item['exit_code']==0 for item in aw['results'])
stability=read(R/'analysis/20261026_z_aw_fix/aw_storage_regression/source_stability.json')
assert stability['B3_source55_unchanged'] and stability['B4_source55_unchanged']
runner=read(O/'runner_exit.json'); vendor=read(Path(state['v7']['VG']).parents[3]/'verification/synthesis_exit.json')
assert runner['actual_p_wait']==vendor['actual_p_wait']==0
assert runner['normal_wait_return'] and vendor['normal_wait_return']
out=O/'HANDOFF_RECONCILED.json'; assert not out.exists()
out.write_text(json.dumps({'checked_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'repo':str(R),'archive_manifest_pass':True,'archive_files':archive,'evidence_references':refs,
    'source55_matched':True,'hold_sha256':freeze['source55']['position/mtf_xyz_hold_control.v'],
    'VG_sha256':state['v7']['VG_sha256'],'synthesis_vendor_wait':vendor['actual_p_wait'],'synthesis_runner_wait':runner['actual_p_wait'],
    'AW5_completed':aw['completed'],'AW5_each_actual_exit0':True,
    'AW5_root_batch_actual_exit0_provenance':'Inherited original-session completion and hash-bound STATE.json v7.AW5.actual_root_batch_exit_code=0; no standalone batch wait receipt was present. No reconstruction of a historical wait.',
    'approval':'Original user confirmed continuation; archival awaiting approval fields are historical. See analysis/20261026_z_aw_fix/handoff_20261026_APPROVED.md.',
    'no_hardware_or_serial_actions':True},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'archive_pass':True,'source55':55,'VG_matched':True,'AW5_completed':5,'synthesis_vendor_runner_exit0':True,'references':len(refs),'encoded_reference_resolved':sum(x['resolved_by_unique_hash'] for x in refs)},indent=2))
