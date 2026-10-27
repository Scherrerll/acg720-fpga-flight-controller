"""Prepare documented incremental placement from .p; do not launch another job."""
from pathlib import Path
import ast,hashlib,json
O=Path(__file__).resolve().parent/'compact_aw_v4_incplace_loc3_followup';D=O.parent/'compact_aw_v4_loc3_followup';R=O.parents[3]
assert not O.exists();O.mkdir()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
seed=R/'out/z_aw_fix_20261026/compact_aw_v4/physical_p3r0_01/source/impl/pnr/acg720_ano_port.p'
old='ba20959930d4ddac2f4841d3ce4962d4ee1c84c2b65feaf004b9def3a6f76a1e';new=sha(seed)
(O/'source_freeze.json').write_bytes((D/'source_freeze.json').read_bytes())
label='physical_p3r0_incplace_loc3_01'
for name in ['run_physical.py','launch_physical_hidden.py','seal_terminal.py','independent_raw_review.py','physical_snapshot.py']:
    t=(D/name).read_text().replace('physical_p3r0_inc_loc3_01',label).replace('v4_P3R0.pr','v4_P3R0.p').replace('physical_p3r0_01/source/impl/pnr/acg720_ano_port.pr','physical_p3r0_01/source/impl/pnr/acg720_ano_port.p').replace(old,new)
    if name=='run_physical.py':
        t=t.replace('-inc_pnr ','-inc_place ').replace('copied same-VG seed','copied same-VG placement seed')
    ast.parse(t);(O/name).write_text(t)
(O/label).mkdir()
(O/'PREPARATION.json').write_text(json.dumps({'scope':'Same exact v4 VG/source55 and same three LOC commands as prior trial; use documented .p incremental placement instead of .pr incremental place-and-route.',
    'reason':'Even byte-identical v4 VG with its own .pr reports2.82% match and default fallback. Both local vendor manuals agree that -inc_place accepts .p. Test the placement-only interface; actual matching/fallback and fresh full-route50MHz gates remain required.',
    'seed':str(seed),'seed_sha256':new,'seed_bytes':seed.stat().st_size,'period_ns':20,
    'official_manuals':{'Tcl_SUG1220_PDF51':'inc_place file specifies *.p','UserGuide_SUG100_PDF55':'Incremental Placement Only specifies *.p'},
    'PNR_started':False,'scripts':{p.name:sha(p) for p in O.glob('*.py')}},indent=2)+'\n')
print('Prepared only:',label,'seed',new)
