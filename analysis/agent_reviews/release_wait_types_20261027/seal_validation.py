"""Seal already-completed offline waits without rewriting any earlier seal."""
from pathlib import Path
import datetime,hashlib,json,re,sys
sys.dont_write_bytecode=True
D=Path(__file__).resolve().parent;R=D.parents[2]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf8'))
result=read(D/'VALIDATION_RESULT_RETRY02.json')
assert result['passed'] is True
for name,wanted in [('negative_types_retry02',6),('existing42_retry02',42)]:
    actual=read(D/(name+'_exit.json'))
    assert actual['normal_wait_return'] is True and type(actual['actual_p_wait']) is int and actual['actual_p_wait']==0
    for channel in ['stdout','stderr']:assert sha(D/(name+'.'+channel+'.log'))==actual[channel+'_sha256']
    log=(D/(name+'.stderr.log')).read_text()
    assert re.search(r'Ran '+str(wanted)+r' tests in [\d.]+s\s+OK\s*$',log)
for name,digest in result['source_script_hashes'].items():assert sha(Path(name))==digest
old_seal=R/'analysis/agent_reviews/release_20261027/V22_RELEASE_VALIDATION_SEALED.json'
assert sha(old_seal)=='5eb911a1fffe723212237b1478384aa797501833368427cb5c892b107b8d832a'
backup=read(D/'previous_42_snapshot/MANIFEST.json')
for name,item in backup['files'].items():assert sha(D/'previous_42_snapshot'/name)==item['sha256']
failed=read(D/'negative_types_exit.json')
assert type(failed['actual_p_wait']) is int and failed['actual_p_wait']==1
for channel in ['stdout','stderr']:assert sha(D/('negative_types.'+channel+'.log'))==failed[channel+'_sha256']
for name,digest in failed['source_script_hashes'].items():
    path=Path(name)
    if path.name in {'test_wait_types.py','run_validation.py'}:assert sha(path)==digest
output=D/'RELEASE_WAIT_TYPE_VALIDATION_SEALED.json';assert not output.exists()
data=dict(sealed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),passed=True,tests=48,
          test_groups={'new_receipt_scalar_negative_groups':6,'unchanged_existing_suite':42},
          actual_child_waits={k:v['actual_p_wait'] for k,v in result['actual_child_results'].items()},
          source_script_hashes=result['source_script_hashes'],previous42_seal_unchanged=sha(old_seal),
          previous42_readonly_snapshot_manifest_sha256=sha(D/'previous_42_snapshot/MANIFEST.json'),
          first_fixture_failure_preserved={'actual_wait':1,'reason':'Fixture expected AssertionError; verifier require deliberately raises SystemExit; retry changes only test expectations.',
                                           'receipt_sha256':sha(D/'negative_types_exit.json')},
          scope='Receipt exit-code type hardening only. Offline proofs/SYN/preparation test archives; no vendor, hardware, release export/promotion or qualified package generated.',
          bindings={p.name:sha(p) for p in [D/'VALIDATION_RESULT_RETRY02.json',D/'negative_types_retry02_exit.json',D/'existing42_retry02_exit.json',Path(__file__)]})
output.write_text(json.dumps(data,indent=2)+'\n',encoding='utf8')
print(json.dumps({'seal':str(output),'sha256':sha(output),'tests':48,'passed':True}))
