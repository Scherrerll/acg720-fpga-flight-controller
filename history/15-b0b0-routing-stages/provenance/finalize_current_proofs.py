from test_tools import *
import importlib.util, datetime
from control_contract import verify
verify()
spec=importlib.util.spec_from_file_location('builder',FIX/'build_project.py')
b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
before=b.source_hashes()
subprocess.run([os.sys.executable,str(ROOT/'test_declarations.py')],check=True,env=ENV)
logs=['qualification_'+Path(script).stem+'.log' for script in ['test_declarations.py','test_component.py','test_fallback_core.py','test_nominal_equivalence.py','test_tools.py','test_wire.py']]
for name in logs:
 assert (ROOT/'tests'/name).is_file(),name
p=subprocess.run([os.sys.executable,'-m','unittest','discover','-s',str(ROOT/'ground'),'-p','test_*.py'],capture_output=True,text=True,env=ENV,timeout=60)
(ROOT/'tests/host_tests.log').write_text(p.stdout+p.stderr,encoding='utf8')
if p.returncode:raise RuntimeError(p.stdout+p.stderr)
verify();assert before==b.source_hashes(),'Sources changed during qualification'
for name in ['fallback_component','fallback_core','nominal_core_equivalence','top','legacy_telemetry_wire','fallback_telemetry_wire']:
    proof=json.loads((ROOT/'tests'/f'{name}.proof.json').read_text())
    assert proof['passed']
    for path,digest in proof['source_sha256'].items():
        source=Path(path);source=source if source.is_absolute() else ROOT/source
        assert hashlib.sha256(source.read_bytes()).hexdigest()==digest,('Stale test proof',source)
paths=[ROOT/'finalize_current_proofs.py',ROOT/'control_contract.py',ROOT/'source_contract.json',ROOT/'baseline.json',ROOT/'qualify.py']
paths+=list((ROOT/'hardware/forward_net_reproduction').rglob('*'))
paths+=list((ROOT/'tests').glob('*.proof.json'))+list((ROOT/'tests').glob('*.v'))
paths+=list(ROOT.glob('test_*.py'))+list((ROOT/'ground').glob('*'))
paths+=[ROOT/'tests'/n for n in logs]+[ROOT/'tests/host_tests.log']
evidence={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths if p.is_file()}
result=dict(reused_current_source_proofs=True,qualification_execution='Individual simulation proofs from current source hashes; finalizer reran declaration/gate and host tests. Modified qualify.py was not rerun in full.',candidate='B0B0',created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),offline_tests_passed=True,
    sources_sha256=before,evidence_sha256=evidence,programming_authorized=False,hardware_programmed=False,flight_ready=False,
    pnr_verified=False,scope='Height-loss fallback component/core/nominal equivalence/UART/replay tests. No PNR or hardware acceptance.')
(ROOT/'qualification.json').write_text(json.dumps(result,indent=2),encoding='utf8')
print(json.dumps(dict(offline_tests_passed=True,pnr_verified=False,hardware_accessed=False)))
