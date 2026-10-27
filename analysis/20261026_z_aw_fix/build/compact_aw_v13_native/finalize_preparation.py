"""Syntax/preflight only. Does not execute a build, Tcl script, or audit hook."""
from pathlib import Path
import ast, datetime, hashlib, importlib.util, json, re, sys, tkinter
O=Path(__file__).resolve().parent;R=O.parents[3];P=O.parent/'compact_aw_v13'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert not (O/'PREPARATION.json').exists()
for name in ['launch_physical_hidden.py','physical_snapshot.py']:
    target=O/name;assert not target.exists()
    text=(P/name).read_text(encoding='utf8').replace('compact_aw_v13','compact_aw_v13_native')
    ast.parse(text);target.write_text(text,encoding='utf8')
scripts=['run_physical.py','audit_synthesis.py','native_physical_audit.py','seal_terminal.py','independent_raw_review.py','launch_physical_hidden.py','physical_snapshot.py']
for name in scripts:ast.parse((O/name).read_text(encoding='utf8'))
saved=sys.argv;sys.argv=['run_physical.py','3']
try:
    spec=importlib.util.spec_from_file_location('native_Tcl_generation_only',O/'run_physical.py')
    worker=importlib.util.module_from_spec(spec);spec.loader.exec_module(worker)
finally:sys.argv=saved
source=R/'out/z_aw_fix_20261026/compact_aw_v13_native/canonical/source'
lines=(source/'build.tcl').read_text(encoding='utf8').splitlines()
interp=tkinter.Tcl();checks={}
for place in [2,3]:
    tcl=worker.build_tcl(lines,place)
    assert interp.call('info','complete',tcl)==1
    assert tcl.index('run syn')<tcl.index('exec {')<tcl.index('run pnr')<tcl.index('puts PHYSICAL_COMMAND_RETURNED_EOF')
    assert re.findall(r'^set_option -place_option\s+(\S+)$',tcl,re.M)==[str(place)]
    assert re.findall(r'^set_option -map_option\s+(\S+)$',tcl,re.M)==['2']
    assert re.findall(r'^set_option -global_freq\s+(\S+)$',tcl,re.M)==['50']
    checks[str(place)]={'Tcl_complete':True,'phase_order_valid':True,'tcl_sha256':hashlib.sha256(tcl.encode()).hexdigest()}
assert not any((R/'out/z_aw_fix_20261026/compact_aw_v13_native'/f'physical_p{place}r0_01').exists() for place in [2,3])
helper=R/'firmware/B0B4/build_candidate.py';assert sha(helper)=='abb5246c203b73c111f80bc91f8db6c8220463f7d4c5cf48dbfe2167ef49db84'
result={'prepared_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'prepared_not_started':True,
    'script_sha256':{name:sha(O/name) for name in scripts},'Tcl_parse_preflight':checks,
    'original_helper_sha256':sha(helper),'gate_adaptation_sha256':sha(O/'GATE_ADAPTATION.json'),
    'scope':'Tcl info-complete parses only; no Tcl evaluation, vendor, hook, simulation or hardware action. At most two physical jobs before launch.'}
(O/'PREPARATION.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
print(json.dumps({'prepared_not_started':True,'scripts_syntax_valid':len(scripts),'Tcl_parse_preflight':checks,'vendor_started':False}))
