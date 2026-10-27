"""Prepare untried v4 exact-VG routability-priority P1/R0; no RTL/SYN/seed/LOC."""
from pathlib import Path
import ast,hashlib,json
O=Path(__file__).resolve().parent/'compact_aw_v4_p1_followup';D=O.parent/'compact_aw_v4_p3mf60_followup'
assert not O.exists();O.mkdir();sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
(O/'source_freeze.json').write_bytes((D/'source_freeze.json').read_bytes())
label='physical_p1r0_01'
for name in ['run_physical.py','launch_physical_hidden.py','seal_terminal.py','independent_raw_review.py','physical_snapshot.py']:
    t=(D/name).read_text().replace('physical_p3r0_mf60_01',label)
    if name=='run_physical.py':
        t=t.replace("'set_option -route_maxfan 60' if line=='set_option -route_maxfan 23'", "'set_option -place_option 1' if line=='set_option -place_option 3'")
        t=t.replace("('place_option','3')","('place_option','1')").replace("('route_maxfan','60')","('route_maxfan','23')").replace("'place':3","'place':1").replace("'route_maxfan':60","'route_maxfan':23").replace('P3/R0 Maxfan60','P1/R0 routability-priority')
    ast.parse(t);(O/name).write_text(t)
(O/label).mkdir()
(O/'PREPARATION.json').write_text(json.dumps({'scope':'Exact known full-route v4 VG/source55, original constraints, no seed/LOC/SYN. Change place3 to documented routability-priority place1 only.',
    'reason':'v4 P3 complete-routed but misses0.220ns; P2/P4/R1 and small LOC trial fail. P1 was not tried on this exact VG. Earlier distinct v6 P1 did complete-route, which motivates trying this placement strategy without claiming transferable timing.',
    'manual':'C:/Gowin/Gowin_V1.9.12.04_x64/IDE/doc/EN/SUG1220-2.1E_Gowin Software Tcl Commands User Guide.pdf','manual_pdf_page':44,
    'physical_options':{'place':1,'route':0,'route_maxfan':23},'period_ns':20,'PNR_started':False,
    'scripts':{p.name:sha(p) for p in O.glob('*.py')}},indent=2)+'\n')
print('Prepared exact-v4 P1/R0 only.')
