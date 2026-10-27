"""Parse the exact authored physical Tcl expression; never evaluate Tcl or start tools."""
from pathlib import Path
import ast,hashlib,json,re,tkinter
O=Path(__file__).resolve().parent;R=O.parents[3]
runner=O/'run_physical.py';tree=ast.parse(runner.read_text(encoding='utf8'))
values=[n.value for n in ast.walk(tree) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='tcl' for t in n.targets)]
assert len(values)==1
lines=(R/'out/z_aw_fix_20261026/compact_aw_v15/canonical/source/build.tcl').read_text(encoding='utf8').splitlines()
interp=tkinter.Tcl();checks={}
for place in [2,3]:
    # This evaluates only the exact known Python string/comprehension expression;
    # Tcl is solely passed to info complete, never to eval or any vendor command.
    tcl=eval(compile(ast.Expression(values[0]),str(runner),'eval'),{'__builtins__':{},'lines':lines,'PLACE':place},{})
    assert interp.call('info','complete',tcl)==1
    for option,value in [('place_option',str(place)),('route_option','0'),('map_option','2'),('replicate_resources','0'),('global_freq','50'),('user_code','0000B0B4')]:
        assert re.findall(r'^set_option -'+option+r'\s+(\S+)\s*$',tcl,re.M)==[value]
    assert tcl.count('run pnr\n')==1 and 'run syn' not in tcl and 'run all' not in tcl
    assert 'inc_pnr' not in tcl and 'inc_place' not in tcl
    checks[str(place)]={'Tcl_complete':True,'options_verified':True,'Tcl_sha256':hashlib.sha256(tcl.encode()).hexdigest()}
dest=O/'PHYSICAL_TCL_PREFLIGHT.json';assert not dest.exists()
dest.write_text(json.dumps({'scope':'Exact prepared Python Tcl expression evaluated as strings and Tcl syntax completeness checked; no Tcl execution or vendor/hardware start.',
    'runner_sha256':hashlib.sha256(runner.read_bytes()).hexdigest(),'profiles':checks},indent=2)+'\n',encoding='utf8')
print(json.dumps({'physical_Tcl_preflight_passed':True,'profiles':[2,3],'vendor_started':False}))
