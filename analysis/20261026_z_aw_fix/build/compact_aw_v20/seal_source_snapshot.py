"""Preserve twelve exact B3-relative v20 files in a new reconstruction history only."""
from pathlib import Path
import datetime,hashlib,json
from validation_contract import verify_contract
O=Path(__file__).resolve().parent;R=O.parents[3]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf8'))
contract=verify_contract(check_proof=True);C=Path(read(O/'source_freeze.json')['source_root']);expected=contract['source55'];changes=contract['B3_relative_changes']
assert len(changes)==12
D=R/'analysis/20261026_z_aw_fix/implementation_history/v20_az_vy_guard_composition';assert not D.exists();D.mkdir()
items={}
for n,h in changes.items():
    p=D/'source'/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((C/n).read_bytes());assert sha(p)==h;items[p.relative_to(D).as_posix()]={'sha256':h,'bytes':p.stat().st_size}
manifest={'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'Exact12 B3-relative v20 AZ/VY same-publication guard composition files; other43 reconstruct from immutable B3. New full source55 differs from either parent. Functional/source snapshot only; no SYN/physical/hardware qualification.',
    'baseline_B3_source55':read(R/'firmware/B0B3/qualification.json')['source_sha256'],'source55':expected,'artifacts':items,'changed_file_count':12,
    'source_freeze_sha256':sha(O/'source_freeze.json'),'composition_sha256':sha(O/'SOURCE_COMPOSITION.json'),'proof_binding_sha256':sha(O/'PROOF_BINDING.json'),'component_reuse_binding_sha256':sha(O/'COMPONENT_REUSE_BINDING.json'),
    'new_private_same_publication_predicate_bits':2,'legacy_public_output_cycle_change':0,'original_partial_preparation_failure_sha256':sha(O/'PREPARATION_FAILURE_01.json'),'functional_retry_correction_sha256':sha(O/'FUNCTIONAL_CORRECTION_02.json')}
(D/'MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf8',newline='\n')
assert {n:sha(C/n) for n in expected}==expected
print(json.dumps({'preserved_files':12,'reused_B3_files':43,'manifest_sha256':sha(D/'MANIFEST.json'),'vendor_started':False}))
