"""Original N/C proofs plus exact reviewed INFO caller substitution; no new full-top PASS."""
from pathlib import Path
import json,hashlib,subprocess,sys
ROOT=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def verify():
 from control_contract import verify as contract
 contract();c=json.loads((ROOT/'source_contract.json').read_text());N=Path(c['parent']);P=Path(c['info_plan'])
 q=json.loads((N/'qualification.json').read_text());assert q['offline_tests_passed'] is True and len(q['evidence_sha256'])==34
 for n,h in q['evidence_sha256'].items():assert sha(N/n)==h,('Original N evidence changed',n)
 r=subprocess.run([sys.executable,str(N/'inherited_context_bridge.py')],cwd=N,capture_output=True,text=True);assert r.returncode==0,r.stderr
 assert json.loads(r.stdout)['passed'] is True
 for n,h in c['info_evidence_sha256'].items():assert sha(P/n)==h,('Original INFO evidence changed',n)
 proof=json.loads((P/'proof.json').read_text());assert proof['passed'] is True
 for k in ['wire_cycles_equal','sequence_crc_xor_checked','default_generic_preserved','caller_source_contract_verified']:assert proof[k] is True
 assert proof['real_uart_cases']==1 and proof['bytes_checked']==34020
 for n,h in proof['source_sha256'].items():assert sha(Path(n))==h
 for n in ['acg720_ano_port.v','telemetry_tx.v']:assert sha(ROOT/'fixture'/n)==sha(P/n.replace('.v','.proposed.v'))
 study=json.loads((P/'synthesis_resource_study.json').read_text());assert study['passed'] is True and study['strict_connectivity_diagnostics_passed'] is True
 folder=Path(study['folder'])
 for n,h in study['source_sha256'].items():assert sha(folder/n)==sha(ROOT/'fixture'/n)==h,('Actual study source mismatch',n)
 for n,h in study['evidence_sha256'].items():assert sha(folder/n)==h
 assert sha(Path(study['proposed_vg']))==study['proposed_vg_sha256']=='aa2de0222dc404ae2326da2d068fc079833296dece1b726f1af0b10f5bb9f941'
 return dict(passed=True,parent_proof_scope='Original N34 and C128 proofs at original paths; exact INFO substitution supported by source induction and original real-UART/boundary/default evidence',parent_evidence_count=34,info_plan=str(P),sources_sha256=study['source_sha256'],current_full_top_simulation_passed=False,hardware_accessed=False,induction=['Caller flight_info_q is initialized zero and holds under telemetry_snapshot_hold.','At snapshot_begin, hold is high before the edge; old local bank samples the same held caller Q. Caller Q stays held through serialization.','Direct vs retained internal payload differences between frames are unconsumed; next frame reacquires identical held Q. Unchanged serializer and hold timing preserve bytes and control context.'])
if __name__=='__main__':print(json.dumps(verify(),indent=2))
