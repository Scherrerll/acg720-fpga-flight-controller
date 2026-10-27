"""Freeze completed v12 SYN/source and derive exact-VG P2/P3 physical-only gates."""
from pathlib import Path
import ast,hashlib,json
O=Path(__file__).resolve().parent;D=O.parent/'compact_aw_v11';R=O.parents[3]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
s=json.loads((R/'out/z_aw_fix_20261026/compact_aw_v12/build_attempt_01/verification/synthesis_summary.json').read_text());x=json.loads((O/'runner_exit.json').read_text())
assert s['passed'] and s['actual_p_wait']==x['actual_p_wait']==0 and x['normal_wait_return']
old='f239c61b25007920c57057d8b5f1a34b3b63b4acfa7e19f60acc8f1f6a489d43';new=s['netlist_sha256'];assert new=='f18ac77212a4b17ded9c5a6025a034dda91f8af8d13ca77bbf12caaa033eb0c1'
for name in ['seal_synthesis.py','seal_source_snapshot.py','run_physical.py','launch_physical_hidden.py','seal_terminal.py','independent_raw_review.py','physical_snapshot.py']:
    assert not (O/name).exists()
    t=(D/name).read_text().replace('compact_aw_v11','compact_aw_v12').replace(old,new)
    if name=='run_physical.py':
        t=t.replace("PRIOR=R/'out/z_aw_fix_20261026/compact_aw_v9/canonical/source'","PRIOR=R/'out/z_aw_fix_20261026/compact_aw_v11/canonical/source'")
        t=t.replace('baseline_v9_map2_source55','baseline_v11_map2_source55').replace('v9_source55','v11_source55').replace('v11_p','v12_p').replace('exact-v11-VG','exact-v12-VG').replace('exact-VG v11','exact-VG v12').replace('source override is v11','source override is v12')
    if name=='seal_source_snapshot.py':t=t.replace('v11_same_clock_pub_age','v12_next_age_compare').replace('v11 changes','v12 changes')
    if name=='seal_synthesis.py':t=t.replace('completed v11','completed v12')
    ast.parse(t);(O/name).write_text(t)
for place in [2,3]:(O/f'physical_p{place}r0_01').mkdir()
(O/'PHYSICAL_PREPARATION.json').write_text(json.dumps({'scope':'Exact audited v12 VG/source55/proof0; ordinary P2/P3 physical-only, unchanged50MHz/20ns/sole radio pad exception/18pins/B4. No seed, no physical clock/data overrides, no new SYN.',
    'reason_first_P2':'Comparable guard candidates tended to have fewer unrouted nets on P2; vendor documents P2 timing-priority. v12 improves age predicate topology at v9-like mapped area. No route/STA result inferred.',
    'source55':s['source_sha256'],'VG_sha256':new,'proof_binding_sha256':sha(O/'PROOF_BINDING.json'),'period_ns':20,'first_profile':2,'PNR_started':False,
    'scripts':{n:sha(O/n) for n in ['run_physical.py','launch_physical_hidden.py','seal_terminal.py','independent_raw_review.py','physical_snapshot.py']}},indent=2)+'\n')
print('Prepared exact-v12 P2/P3 and archive scripts; no PNR launched here.')
