"""Keep exact v4/P3 inputs; route1 trades compilation time for a better route."""
from pathlib import Path
import ast,hashlib,json
O=Path(__file__).resolve().parent;R=O.parents[3];D=O.parent/'compact_aw_v4_p2_followup'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert not (R/'out/z_aw_fix_20261026/compact_aw_v4/physical_p3r1_01').exists()
assert not (O/'source_freeze.json').exists();(O/'source_freeze.json').write_bytes((D/'source_freeze.json').read_bytes())
text=(D/'run_physical.py').read_text().replace('physical_p2r0_01','physical_p3r1_01').replace('P2/R0','P3/R1')
old="'set_option -place_option 2' if line=='set_option -place_option 3'";assert text.count(old)==1
text=text.replace(old,"'set_option -route_option 1' if line=='set_option -route_option 0'")
text=text.replace("('place_option','2')","('place_option','3')").replace("('route_option','0')","('route_option','1')")
text=text.replace("'place':2,'route':0","'place':3,'route':1")
ast.parse(text);(O/'run_physical.py').write_text(text)
for name in ['launch_physical_hidden.py','seal_terminal.py','independent_raw_review.py']:
    text=(D/name).read_text().replace('physical_p2r0_01','physical_p3r1_01')
    ast.parse(text);(O/name).write_text(text)
text=(D/'physical_snapshot.py').read_text()
old="for place in [2]:\n    label=f'physical_p{place}r0_01';";assert text.count(old)==1
text=text.replace(old,"for label in ['physical_p3r1_01']:\n    ")
ast.parse(text);(O/'physical_snapshot.py').write_text(text)
manuals={
    'C:/Gowin/Gowin_V1.9.12.04_x64/IDE/doc/EN/SUG1220-2.1E_Gowin Software Tcl Commands User Guide.pdf':{'pages_pdf':[44,49,51]},
    'C:/Gowin/Gowin_V1.9.12.04_x64/IDE/doc/EN/SUG100-4.4.7E_Gowin Software User Guide.pdf':{'pages_pdf':[51,52,55]}}
for name,value in manuals.items():value['sha256']=sha(Path(name))
(O/'PREPARATION.json').write_text(json.dumps({'scope':'New physical-only P3R1 with unchanged v4 source55 and exact SYN VG; frozen source/evidence not modified.',
    'reason':'v4 P3R0 full route49.456MHz/setup−0.220ns; preserve P3 and change route0 to route1 for greater routing search time.',
    'official_manuals':manuals,'manual_summary':{'place1':'routability priority','place2':'timing priority','route1':'trades compilation time for a better route','route2':'routing speed priority','route_maxfan':'1..100; default23 here; smaller values may cause route failure; no long-wire/clock-route control'},
    'source_freeze_sha256':sha(O/'source_freeze.json'),'VG_sha256':'e67bcab6336757e08645756258d39dd13726b452c392d470de4c900a159aaa8f',
    'physical_options':{'place':3,'route':1,'map_option':2,'replicate_resources':0,'timing_driven':1,'route_maxfan':23},
    'new_scripts':{p.name:sha(p) for p in O.glob('*.py')},'period_ns':20,'PNR_started':False},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print('Prepared exact v4 P3R1;50MHz and all physical gates unchanged.')
