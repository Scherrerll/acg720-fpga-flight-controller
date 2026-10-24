from test_tools import *
import importlib.util, datetime
from control_contract import verify
verify()
from verify_diagnostic_proof import verify as verify_diagnostic
from verify_published_anchor import verify as verify_anchor
verify_anchor()
review=json.loads((ROOT/'hardware/independent_control_review.json').read_text())
assert review['findings']==[]
for name,value in review['sha256'].items():assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==value,('Independent control review stale',name)
spec=importlib.util.spec_from_file_location('builder',FIX/'build_project.py')
b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
before=b.source_hashes()
subprocess.run([os.sys.executable,str(ROOT/'test_declarations.py')],check=True,env=ENV)
logs=['qualification_'+Path(script).stem+'.log' for script in ['test_declarations.py','test_component.py','test_fallback_core.py','test_published_anchor.py','test_nominal_equivalence.py','test_tools.py','test_wire.py']]
for name in logs:
 assert (ROOT/'tests'/name).is_file(),name
p=subprocess.run([os.sys.executable,'-m','unittest','discover','-s',str(ROOT/'ground'),'-p','test_*.py'],capture_output=True,text=True,env=ENV,timeout=60)
(ROOT/'tests/host_tests.log').write_text(p.stdout+p.stderr,encoding='utf8')
if p.returncode:raise RuntimeError(p.stdout+p.stderr)
assert 'Ran 24 tests' in p.stderr and 'OK' in p.stderr
host_proof=dict(passed=True,tests=24,source_sha256={str(x.relative_to(ROOT)):hashlib.sha256(x.read_bytes()).hexdigest()for x in (ROOT/'ground').glob('*.py')},log_sha256=hashlib.sha256((ROOT/'tests/host_tests.log').read_bytes()).hexdigest())
(ROOT/'tests/host_tests.proof.json').write_text(json.dumps(host_proof,indent=2)+'\n')
verify();assert before==b.source_hashes(),'Sources changed during qualification'
for name in ['fallback_component','fallback_core','published_anchor','nominal_core_equivalence','top','legacy_telemetry_wire','fallback_telemetry_wire']:
    proof=json.loads((ROOT/'tests'/f'{name}.proof.json').read_text())
    assert proof['passed']
    for path,digest in proof['source_sha256'].items():
        source=Path(path);source=source if source.is_absolute() else ROOT/source
        assert hashlib.sha256(source.read_bytes()).hexdigest()==digest,('Stale test proof',source)
from diagnostic_context_bridge import freeze as freeze_bridge
freeze_bridge();verify_diagnostic()
paths=[ROOT/'diagnostic_context_bridge.py',ROOT/'hardware/diagnostic_context_bridge.json',ROOT/'hardware/partial_current_full_top/status.json',ROOT/'finalize_current_proofs.py',ROOT/'control_contract.py',ROOT/'source_contract.json',ROOT/'baseline.json',ROOT/'qualify.py']
paths+=list((ROOT/'hardware/forward_net_reproduction').rglob('*'))
paths+=list((ROOT/'hardware/diagnostic_reset_proof').rglob('*'))
paths+=[ROOT/'hardware/independent_control_review.json',ROOT/'hardware/published_anchor_validation.md',ROOT/'OPERATOR_NOTES.txt',ROOT/'verify_published_anchor.py',ROOT/'published_anchor_delta.json',ROOT/'hardware/published_anchor.patch',ROOT/'tests/published_anchor.prefix_failure.json',ROOT/'tests/published_anchor.prefix_failure.log',ROOT/'diagnostic_delta.json',ROOT/'verify_diagnostic_proof.py',ROOT/'verify_mapped_binding.py',FIX/'build_project.py']
paths+=list((ROOT/'hardware/mapped_probe').glob('*'))
paths+=[ROOT/'hardware/review_synthesis_freshness.py',ROOT/'hardware/synthesis_freshness_review.json']
paths+=list((ROOT/'hardware').glob('mapped_*.json'))+list((ROOT/'hardware').glob('mapped_*.py'))
paths+=list((ROOT/'tests').glob('*.proof.json'))+list((ROOT/'tests').glob('*.v'))
paths+=list(ROOT.glob('test_*.py'))+list((ROOT/'ground').glob('*'))
paths+=[ROOT/'tests'/n for n in logs]+[ROOT/'tests/host_tests.log']
evidence={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths if p.is_file()}
result=dict(reused_current_source_proofs=True,qualification_execution='Individual simulation proofs from current source hashes; finalizer reran declaration/gate and host tests. Modified qualify.py was not rerun in full.',candidate='B0B0',created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),offline_tests_passed=True,
    sources_sha256=before,evidence_sha256=evidence,programming_authorized=False,hardware_programmed=False,flight_ready=False,
    pnr_verified=False,current_full_top_simulation_passed=False,diagnostic_proof_kind='Original-source simulation evidence plus explicit current-context algebraic compositional bridge',scope='Published-anchor repair: directed publication/low-anchor/queued-result regression, fallback component/core, nominal equivalence, UART and host tests. No PNR or hardware acceptance.')
(ROOT/'qualification.json').write_text(json.dumps(result,indent=2),encoding='utf8')
print(json.dumps(dict(offline_tests_passed=True,pnr_verified=False,hardware_accessed=False)))
