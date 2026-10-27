"""Bind the completed timing-goal SYN to a fresh P3 physical run; no RTL edits."""
from pathlib import Path
import ast,hashlib,json
O=Path(__file__).resolve().parent;D=O.parent/'compact_aw_v4_p3mf60_followup'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
label='physical_p3r0_01'
assert not (O/label).exists()
oldvg='e67bcab6336757e08645756258d39dd13726b452c392d470de4c900a159aaa8f'
newvg='f7a3acad9b1630dc7702bdff55a47bab6a766ef3415c8932d8be84a9962e2f00'
for name in ['run_physical.py','launch_physical_hidden.py','seal_terminal.py','independent_raw_review.py','physical_snapshot.py']:
    t=(D/name).read_text().replace('compact_aw_v4/', 'compact_aw_v4_timing/').replace("compact_aw_v4'","compact_aw_v4_timing'").replace('physical_p3r0_mf60_01',label).replace(oldvg,newvg)
    if name=='run_physical.py':
        t=t.replace("compact_aw_v3/canonical/source'","compact_aw_v4/canonical/source'").replace("din['baseline_v3_map2_source55']","din['baseline_v4_map2_source55']")
        t=t.replace("{'map_option':2,'replicate_resources':0}","{'map_option':2,'replicate_resources':0,'opt_goal':'timing'}")
        t=t.replace("DONOR/'synthesis_freeze_manifest_final.json'","O/'SYNTHESIS_RESULT.json'")
        t=t.replace("'set_option -route_maxfan 60' if line=='set_option -route_maxfan 23'", "'set_option -opt_goal timing' if line=='set_option -opt_goal area'")
        t=t.replace("('route_maxfan','60')","('route_maxfan','23'),('opt_goal','timing')").replace("'route_maxfan':60","'route_maxfan':23,'opt_goal':'timing'")
        t=t.replace('v4 exact-VG P3/R0 Maxfan60','v4 timing-SYN exact-VG P3/R0').replace('v4 map2 P3/R0 Maxfan60','v4 timing-SYN map2 P3/R0')
    ast.parse(t);(O/name).write_text(t)
(O/label).mkdir()
(O/'PHYSICAL_PREPARATION.json').write_text(json.dumps({'scope':'Exact audited timing-goal mapped VG, fresh P3/R0 physical-only; no RTL/clock/safety change.',
    'VG_sha256':newvg,'source_freeze_sha256':sha(O/'source_freeze.json'),'SYNTHESIS_RESULT_sha256':sha(O/'SYNTHESIS_RESULT.json'),
    'physical_options':{'place':3,'route':0,'route_maxfan':23,'opt_goal':'timing'},'PNR_started':False,
    'scripts':{n:sha(O/n) for n in ['run_physical.py','launch_physical_hidden.py','seal_terminal.py','independent_raw_review.py','physical_snapshot.py']}},indent=2)+'\n')
print('Timing-goal exact mapped VG P3 physical prepared.')
