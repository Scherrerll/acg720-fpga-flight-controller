"""Original parent evidence retained at original paths; explicit two-file MTF substitution."""
from pathlib import Path
import hashlib,json,subprocess,sys,re
ROOT=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def verify():
 from control_contract import verify as contract
 contract(); c=json.loads((ROOT/'source_contract.json').read_text());C=Path(c['parent']);P=Path(c['plan'])
 q=json.loads((C/'qualification.json').read_text());assert q['offline_tests_passed'] is True
 for name,h in q['evidence_sha256'].items():assert sha(C/name)==h,('Parent evidence changed',name)
 # Invoke the immutable original context verifier in its original source directory.
 result=subprocess.run([sys.executable,str(C/'verify_diagnostic_proof.py')],cwd=C,capture_output=True,text=True)
 assert result.returncode==0,result.stderr
 assert json.loads(result.stdout)['passed'] is True
 for name,h in c['plan_evidence_sha256'].items():assert sha(P/name)==h,('MTF proof changed',name)
 proof=json.loads((P/'proof.json').read_text());assert proof['passed'] is True and proof['cycles']==50000 and proof['logical_width_bits']==976
 for name,h in proof['source_sha256'].items():assert sha(Path(name))==h
 for n,proposal in [('acg720_ano_port.v','acg720_ano_port.proposed.v'),('sensor/mtf01p_reader.v','mtf01p_reader.proposed.v')]:assert sha(ROOT/'fixture'/n)==sha(P/proposal)
 top=(ROOT/'fixture/acg720_ano_port.v').read_text();reader=(ROOT/'fixture/sensor/mtf01p_reader.v').read_text()
 assert '.STARTUP_ONLY_DIAGNOSTIC_RESET(1)' in top
 assert re.search(r'STARTUP_ONLY_DIAGNOSTIC_RESET\s*=\s*0',reader)
 assert all(proof[k] is True for k in ['payload_preserved_verbatim','sole_bank_driver_verified','telemetry_only_no_control_feedback_verified','top_boot_single_release_verified'])
 assert proof['startup_cases']==8 and proof['generic_runtime_reset_cases']==2
 # Source identity to the reviewed proof's exact proposal closes the algebraic boundary.
 # Both banks begin at zero. Before the sole release, old reset writes zero and
 # new bank holds zero. Afterwards both use the identical capture/hold predicate
 # and verbatim976-bit payload, so equality is preserved each edge. The bank is
 # telemetry-only, so substitution preserves the unchanged control context.

 return dict(passed=True,parent_evidence_count=len(q['evidence_sha256']),parent_evidence_scope='Original C source-bound context; not new N simulation',current_sources_sha256={n:sha(ROOT/'fixture'/n)for n in q['sources_sha256']},substitution='Exact reviewed top parameter plus976-bit diagnostic bank substitution under single-release boot; default runtime reset retained',current_full_top_simulation_passed=False,mapped_audit_passed=False,pnr_passed=False,hardware_accessed=False)
if __name__=='__main__':print(json.dumps(verify(),indent=2))
