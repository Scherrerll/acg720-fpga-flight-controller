"""Exact nearest full-route v4/P3/R0, change only routing maxfan23->60."""
from pathlib import Path
import ast,hashlib,json
O=Path(__file__).resolve().parent;R=O.parents[3];D=O.parent/'compact_aw_v4_p3r1_followup'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
label='physical_p3r0_mf60_01'
assert not (R/'out/z_aw_fix_20261026/compact_aw_v4'/label).exists()
assert not (O/'source_freeze.json').exists();(O/'source_freeze.json').write_bytes((D/'source_freeze.json').read_bytes())
text=(D/'run_physical.py').read_text().replace('physical_p3r1_01',label).replace('P3/R1','P3/R0 Maxfan60')
old="'set_option -route_option 1' if line=='set_option -route_option 0'";assert text.count(old)==1
text=text.replace(old,"'set_option -route_maxfan 60' if line=='set_option -route_maxfan 23'")
text=text.replace("('route_option','1')","('route_option','0')").replace("'route':1","'route':0")
old="('replicate_resources','0'),('user_code','0000B0B4')";assert text.count(old)==1
text=text.replace(old,"('replicate_resources','0'),('timing_driven','1'),('route_maxfan','60'),('user_code','0000B0B4')")
old="'physical_options':{'place':3,'route':0,'map_option':2,'replicate_resources':0}";assert text.count(old)==2
text=text.replace(old,"'physical_options':{'place':3,'route':0,'map_option':2,'replicate_resources':0,'route_maxfan':60}")
ast.parse(text);(O/'run_physical.py').write_text(text)
for name in ['launch_physical_hidden.py','seal_terminal.py','independent_raw_review.py','physical_snapshot.py']:
    text=(D/name).read_text().replace('physical_p3r1_01',label)
    ast.parse(text);(O/name).write_text(text)
manual=Path('C:/Gowin/Gowin_V1.9.12.04_x64/IDE/doc/EN/SUG100-4.4.7E_Gowin Software User Guide.pdf')
(O/'PREPARATION.json').write_text(json.dumps({'scope':'Exact v4 source/SYN/P3/R0 unchanged; one physical routing knob only, no synthesis/hardware.',
    'reason':'Original v4 P3R0 fully routed49.456MHz/setup−0.220ns. Route Maxfan60 is within documented1..100; smaller values may cause route failure. Keep all other baseline options.',
    'official_manual':str(manual),'official_manual_sha256':sha(manual),'pdf_page':52,
    'source_freeze_sha256':sha(O/'source_freeze.json'),'VG_sha256':'e67bcab6336757e08645756258d39dd13726b452c392d470de4c900a159aaa8f',
    'physical_options':{'place':3,'route':0,'map_option':2,'replicate_resources':0,'timing_driven':1,'route_maxfan':60},'period_ns':20,
    'new_scripts':{p.name:sha(p) for p in O.glob('*.py')},'PNR_started':False},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print('Prepared exact v4 P3R0 with only route_maxfan23->60.')
