"""Preserve exact ten B3-relative v19 files without changing any source55."""
from pathlib import Path
import datetime,hashlib,json
from validation_contract import verify_contract
O=Path(__file__).resolve().parent;R=O.parents[3];C=R/'out/z_aw_fix_20261026/compact_aw_v19/canonical/source'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf8'))
contract=verify_contract(check_proof=True);expected=contract['source55'];b3=read(R/'firmware/B0B3/qualification.json')['source_sha256']
assert len(expected)==len(b3)==55 and {n:sha(R/'firmware/B0B3/source'/n) for n in b3}==b3
changes={n:h for n,h in expected.items() if h!=b3[n]};assert len(changes)==10
D=R/'analysis/20261026_z_aw_fix/implementation_history/v19_az_guard_composition'
assert not D.exists();D.mkdir()
items={}
for name in changes:
    p=D/'source'/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((C/name).read_bytes());assert sha(p)==expected[name]
    items[p.relative_to(D).as_posix()]={'sha256':sha(p),'bytes':p.stat().st_size}
manifest={'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'scope':'Exact ten B3-relative v19 AZ guard/landing/fanout source files; other45 reconstruct from immutable B3 bytes. Functional/source snapshot and actual SYN-only evidence, no physical/hardware acceptance.',
    'baseline_B3_source55':b3,'source55':expected,'artifacts':items,'changed_file_count':10,
    'source_freeze_sha256':sha(O/'source_freeze.json'),'proof_binding_sha256':sha(O/'PROOF_BINDING.json'),
    'guard_binding_sha256':sha(O/'GUARD_REUSE_RECHECK.json'),'reuse_recheck_sha256':sha(O/'REUSED_BINDINGS_RECHECK.json'),
    'actual_SYN_result_sha256':sha(O/'SYNTHESIS_RESULT.json'),'new_same_publication_predicate_bits':1,'legacy_output_cycle_change':0}
(D/'MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf8',newline='\n')
assert {n:sha(C/n) for n in expected}==expected
print(json.dumps({'preserved_source_files':10,'reused_B3_files':45,'manifest':str(D/'MANIFEST.json'),'manifest_sha256':sha(D/'MANIFEST.json')}))
