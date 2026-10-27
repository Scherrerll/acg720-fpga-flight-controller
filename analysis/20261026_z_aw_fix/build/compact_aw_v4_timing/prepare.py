"""Exact v4 RTL, one explicit synthesis-goal override area->timing."""
from pathlib import Path
import ast,hashlib,json,shutil
O=Path(__file__).resolve().parent;R=O.parents[3]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
V4=O.parent/'compact_aw_v4';OLD=R/'out/z_aw_fix_20261026/compact_aw_v4/canonical/source'
NEW=R/'out/z_aw_fix_20261026/compact_aw_v4_timing/canonical/source'
expected=json.loads((V4/'source_freeze.json').read_text())['source55']
assert len(expected)==55 and {p:sha(OLD/p) for p in expected}==expected and not NEW.exists()
shutil.copytree(OLD,NEW)
(O/'source_freeze.json').write_text(json.dumps({'scope':'Exact v4 source55 unchanged; only executed SYN Tcl goal changes area to timing. Clock50MHz/map2/repl0 unchanged.',
    'source_root':str(NEW),'baseline_source55':expected,'source55':expected,'changed_files':[],
    'source_review_sha256':sha(O/'source_review.md'),'synthesis_started':False,'physical_started':False},indent=2)+'\n')
donor=V4/'run_synthesis.py';text=donor.read_text().replace('v4','v4_timing').replace('v3','v4')
old="assert prior['position/mtf_xyz_hold_control.v']=='9aa6a51a6cb2168ef46f3f5a61a23e3c4db8546601be7c0e562d4d16ab2cd6aa'";assert text.count(old)==1
text=text.replace(old,"assert prior['position/mtf_xyz_hold_control.v']==HOLD_SHA")
old="assert [p for p in expected if expected[p]!=prior[p]]==['position/mtf_xyz_hold_control.v']";assert text.count(old)==1
text=text.replace(old,"assert expected==prior==freeze['baseline_source55']")
text=text.replace("'changed_from_v4':['position/mtf_xyz_hold_control.v']","'changed_from_v4':[]")
old="'synthesis_options':{'map_option':2,'replicate_resources':0}";assert text.count(old)==1
text=text.replace(old,"'synthesis_options':{'map_option':2,'replicate_resources':0,'opt_goal':'timing'}")
old="tcl='\\n'.join('run syn' if line=='run all' else line for line in lines";assert text.count(old)==1
text=text.replace(old,"tcl='\\n'.join('run syn' if line=='run all' else 'set_option -opt_goal timing' if line=='set_option -opt_goal area' else line for line in lines")
marker="    assert 'run pnr' not in tcl and 'run all' not in tcl\n";assert text.count(marker)==1
text=text.replace(marker,marker+"    assert re.findall(r'^set_option -opt_goal\\s+(\\S+)\\s*$',tcl,re.M)==['timing']\n    assert re.findall(r'^set_option -global_freq\\s+(\\S+)\\s*$',tcl,re.M)==['50']\n")
text=text.replace('O=Path(__file__)','import sys\nsys.dont_write_bytecode=True\nO=Path(__file__)',1)
marker="    helper=load('v4_timing_original_vendor_gates',HELPER)\n";assert text.count(marker)==1
text=text.replace(marker,"    proof=json.loads((R/'analysis/20261026_z_aw_fix/build/compact_aw_v9/proofs_retry02/results.json').read_text())\n    assert proof['passed']\n    assert all(expected[p]==proof['source55'][p] for p in ['position/mtf_xyz_hold_control.v','nav_math_service.v','position/position_math.v','position/ano_xy_stick.v','position/ano_xy_divide36.v','position/ano_z_stick.v'])\n"+marker)
ast.parse(text);(O/'run_synthesis.py').write_text(text)
(O/'launch_synthesis_hidden.py').write_bytes((O.parent/'compact_aw_v10/launch_synthesis_hidden.py').read_bytes())
manual=Path('C:/Gowin/Gowin_V1.9.12.04_x64/IDE/doc/EN/SUG1220-2.1E_Gowin Software Tcl Commands User Guide.pdf')
(O/'PREPARATION.json').write_text(json.dumps({'scope':'One non-redundant SYN-goal timing experiment. All55 source bytes equal v4; actual SYN override is explicit.',
    'source55':expected,'donor_runner_sha256':sha(donor),'new_runner_sha256':sha(O/'run_synthesis.py'),
    'manual':str(manual),'manual_sha256':sha(manual),'manual_pdf_pages':[29,30],'one_change':'opt_goal area -> timing in executed SYN Tcl only',
    'unchanged_options':{'global_freq':50,'map_option':2,'replicate_resources':0},'PNR_started':False},indent=2)+'\n')
print('Prepared exact v4 source with timing-only SYN goal override; no PNR.')
