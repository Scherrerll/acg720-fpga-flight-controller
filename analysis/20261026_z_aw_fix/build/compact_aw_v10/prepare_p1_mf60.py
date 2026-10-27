"""Same audited v10 VG; routability-priority placement and documented maxfan60."""
from pathlib import Path
import ast,hashlib,json,re
O=Path(__file__).resolve().parent;R=O.parents[3]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert not (R/'out/z_aw_fix_20261026/compact_aw_v10/physical_p1r0_mf60_01').exists()
donor=O/'run_physical.py';text=donor.read_text()
text,n=re.subn(r"assert len\(sys.argv\)==2[^\n]+;PLACE=int\(sys.argv\[1\]\)","assert len(sys.argv)==1;PLACE=1",text,count=1);assert n==1
text=text.replace("LABEL=f'physical_p{PLACE}r0_01'","LABEL='physical_p1r0_mf60_01'")
old="f'set_option -place_option {PLACE}'}";assert text.count(old)==1
text=text.replace(old,"f'set_option -place_option {PLACE}','set_option -route_maxfan 23':'set_option -route_maxfan 60'}")
old="('timing_driven','1'),('map_option','2')";assert text.count(old)==1
text=text.replace(old,"('timing_driven','1'),('route_maxfan','60'),('map_option','2')")
old="'timing_driven':1},'period_ns':20";assert text.count(old)==1
text=text.replace(old,"'timing_driven':1,'route_maxfan':60},'period_ns':20")
text=text.replace('Fresh exact-VG v10 physical-only trial','Exact-VG v10 P1R0 maxfan60 routability trial')
ast.parse(text);p=O/'run_p1_mf60.py';assert not p.exists();p.write_text(text)
sup=(O/'launch_physical_hidden.py').read_text().replace("assert len(sys.argv)==2 and sys.argv[1] in ['2','3']","assert len(sys.argv)==1")
sup=sup.replace("PLACE=sys.argv[1];O=BASE/f'physical_p{PLACE}r0_01'","PLACE='1';O=BASE/'physical_p1r0_mf60_01'")
sup=sup.replace("BASE/'run_physical.py'","BASE/'run_p1_mf60.py'").replace('str(runner),PLACE]','str(runner)]')
ast.parse(sup);(O/'launch_p1_mf60_hidden.py').write_text(sup)
for src,dest in [('seal_terminal.py','seal_p1_mf60.py'),('independent_raw_review.py','independent_p1_mf60_raw_review.py')]:
    text=(O/src).read_text()
    if src=='seal_terminal.py':
        old="assert len(sys.argv)==2 and sys.argv[1] in ['2','3'];label=f'physical_p{sys.argv[1]}r0_01'"
        assert text.count(old)==1;text=text.replace(old,"assert len(sys.argv)==1;label='physical_p1r0_mf60_01'")
    else:
        old="assert len(sys.argv)==2 and sys.argv[1] in ['2','3']\nlabel=f'physical_p{sys.argv[1]}r0_01'"
        assert text.count(old)==1;text=text.replace(old,"assert len(sys.argv)==1\nlabel='physical_p1r0_mf60_01'")
    ast.parse(text);(O/dest).write_text(text)
snapshot=O/'physical_snapshot.py';text=snapshot.read_text();old="for place in [3]:\n    label=f'physical_p{place}r0_01';";assert text.count(old)==1
text=text.replace(old,"for label in ['physical_p3r0_01','physical_p1r0_mf60_01']:\n    ")
ast.parse(text);snapshot.write_text(text)
manual=Path('C:/Gowin/Gowin_V1.9.12.04_x64/IDE/doc/EN/SUG1220-2.1E_Gowin Software Tcl Commands User Guide.pdf')
(O/'P1_MF60_PREPARATION.json').write_text(json.dumps({'scope':'No source/SYN change. One physical scheme to address dense CLS/routing usage.',
    'reason':'Official P1 prioritizes routability; Route Maxfan1..100 and default23, smaller can cause route failure;60 is documented example.50MHz and every gate unchanged.',
    'manual':str(manual),'manual_sha256':sha(manual),'manual_pdf_pages':[44,49],
    'VG_sha256':'607efaa6573e13c53802c7db227bc831a34778a6358de6da6b79962a413dc680',
    'physical_options':{'place':1,'route':0,'map_option':2,'replicate_resources':0,'timing_driven':1,'route_maxfan':60},
    'period_ns':20,'template_runner_sha256':sha(donor),'new_runner_sha256':sha(O/'run_p1_mf60.py'),'PNR_started':False},indent=2)+'\n')
print('Prepared v10 exact-VG P1R0/maxfan60; no source or clock changes.')
