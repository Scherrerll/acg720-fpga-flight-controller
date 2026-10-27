"""Archive completed v11 SYN/source; derive unchanged strict exact-VG P3/P2 runners."""
from pathlib import Path
import ast,hashlib,json
O=Path(__file__).resolve().parent;D=O.parent/'compact_aw_v9';R=O.parents[3]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
summary=json.loads((R/'out/z_aw_fix_20261026/compact_aw_v11/build_attempt_01/verification/synthesis_summary.json').read_text())
exit=json.loads((O/'runner_exit.json').read_text());assert summary['passed'] and exit['actual_p_wait']==0
vg=summary['netlist_sha256'];assert vg=='f239c61b25007920c57057d8b5f1a34b3b63b4acfa7e19f60acc8f1f6a489d43'
oldvg='e99d1ec0928fa9c1650cbc6a7ac9c08d4b2ef0758cdb3a9eec11b04af5d0eb20'
for name in ['seal_synthesis.py','seal_source_snapshot.py','run_physical.py','launch_physical_hidden.py','seal_terminal.py','independent_raw_review.py','physical_snapshot.py']:
    assert not (O/name).exists()
    t=(D/name).read_text().replace('compact_aw_v9','compact_aw_v11').replace(oldvg,vg).replace("O/'proofs_retry02/","O/'proofs/")
    if name=='seal_synthesis.py':
        t=t.replace("'SYN passed; physical trials started; not qualified for installation'","'SYN passed; physical trials prepared, not yet started; not qualified for installation'")
        t=t.replace("'PNR_started':True","'PNR_started':False").replace('completed v9','completed v11')
    if name=='seal_source_snapshot.py':
        t=t.replace('v9_v4_guard','v11_same_clock_pub_age').replace('v9 changes','v11 changes').replace('v9 changes','v11 changes')
    if name=='run_physical.py':
        t=t.replace("PRIOR=R/'out/z_aw_fix_20261026/compact_aw_v4/canonical/source'","PRIOR=R/'out/z_aw_fix_20261026/compact_aw_v9/canonical/source'")
        t=t.replace('baseline_v4_map2_source55','baseline_v9_map2_source55').replace('v4_source55','v9_source55').replace('exact-v9-VG','exact-v11-VG').replace('source override is v9','source override is v11').replace('exact-VG v9','exact-VG v11')
        marker="    evidence += [O/'proofs/results.json',O/'proofs/runner_exit.json']\n";assert t.count(marker)==1
        t=t.replace(marker,marker+"    binding=json.loads((O/'PROOF_BINDING.json').read_text());assert binding['passed'] and binding['source55']==expected and binding['actual_proof_runner_wait']==0\n    evidence += [O/'PROOF_BINDING.json']\n")
    if name=='physical_snapshot.py':
        needle="for label in ['physical_p3r0_01','physical_p3r0_inc_v4_01']:";assert t.count(needle)==1
        t=t.replace(needle,"for label in ['physical_p3r0_01','physical_p2r0_01']:")
    ast.parse(t);(O/name).write_text(t)
for p in [3,2]:(O/f'physical_p{p}r0_01').mkdir()
(O/'PHYSICAL_PREPARATION.json').write_text(json.dumps({'scope':'Exact audited v11 mapped VG; fresh P3/P2 physical-only with original20ns/sole radio pad exception/18pins/B4 gates; no seed or new synthesis.',
    'source55':summary['source_sha256'],'VG_sha256':vg,'proof_binding_sha256':sha(O/'PROOF_BINDING.json'),'period_ns':20,
    'SYN_actual_vendor_wait':0,'SYN_actual_runner_wait':0,'PNR_started':False,
    'scripts':{n:sha(O/n) for n in ['run_physical.py','launch_physical_hidden.py','seal_terminal.py','independent_raw_review.py','physical_snapshot.py']}},indent=2)+'\n')
print('Prepared exact-v11 P3/P2 physical runners; archive scripts ready, no PNR launch here.')
