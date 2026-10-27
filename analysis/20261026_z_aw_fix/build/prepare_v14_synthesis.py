"""Prepare SYN-only v14 using unchanged vendor runner and a documented audit clone."""
from pathlib import Path
import ast,hashlib,json,tkinter
O=Path(__file__).resolve().parent;M=O/'compact_aw_v14';P=O/'compact_aw_v4_native'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert json.loads((M/'PROOF_BINDING.json').read_text(encoding='utf8'))['passed']
assert json.loads((M/'REUSED_BINDINGS_RECHECK.json').read_text(encoding='utf8'))['passed']
t=(P/'audit_synthesis.py').read_text(encoding='utf8').replace('compact_aw_v4_native','compact_aw_v14')
old="assert len(sys.argv)==2 and sys.argv[1] in ['2','3']";assert t.count(old)==1;t=t.replace(old,"assert len(sys.argv)==1")
old="A=R/'out/z_aw_fix_20261026/compact_aw_v14'/f'physical_p{sys.argv[1]}r0_01'";assert t.count(old)==1;t=t.replace(old,"A=R/'out/z_aw_fix_20261026/compact_aw_v14/build_attempt_01'")
assert t.count('assert len(helper.EXPECTED_CHANGES)==3')==1;t=t.replace('assert len(helper.EXPECTED_CHANGES)==3','assert len(helper.EXPECTED_CHANGES)==5')
old="    expected=read(O/'source_freeze.json')['source55']";assert t.count(old)==1
t=t.replace(old,"    ex=read(V/'synthesis_exit.json');assert ex['normal_wait_return'] and ex['actual_p_wait']==0\n"+old)
t=t.replace("'native_map2':new[n]","'local_fanout_map2':new[n]")
t=t.replace('Same-source map2 SYN resources; no route/STA pass inference.','Actual v14 local fanout synthesis versus v4; no physical timing claim.')
t=t.replace('Successful executed SYN audit hook only. Its exec return is confirmed by subsequent Tcl EOF. No standalone SYN process wait is claimed; the full gw_sh vendor process is still running.',
    'SYN_ONLY audit after an actual successful vendor process wait0, independently recorded in synthesis_exit.json. This audit process has its own actual exit receipt; no PNR or combined-native flow claim.')
ast.parse(t);assert not (M/'audit_synthesis_only.py').exists();(M/'audit_synthesis_only.py').write_text(t,encoding='utf8')
(M/'SYNTHESIS_PREPARATION.json').write_text(json.dumps({'prepared_only':True,'scope':'New source SYN_ONLY; no PNR. Exact old helper and cloned strict native mapped/clock/radio/gain/18port auditor with v14 paths and five B3-relative changes.',
    'parent_audit_sha256':sha(P/'audit_synthesis.py'),'audit_sha256':sha(M/'audit_synthesis_only.py'),
    'proof_binding_sha256':sha(M/'PROOF_BINDING.json'),'reuse_recheck_sha256':sha(M/'REUSED_BINDINGS_RECHECK.json')},indent=2)+'\n',encoding='utf8')
print('Prepared v14 strict SYN-only auditor; no compiler or PNR started.')
