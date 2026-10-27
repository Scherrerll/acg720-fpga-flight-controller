"""Prepare same-v4-VG P3/R0 with documented high-fanout PNR replication only."""
from pathlib import Path
import ast,datetime,hashlib,importlib.util,json,sys,tkinter
O=Path(__file__).resolve().parent/'compact_aw_v4_rep1_followup';D=O.parent/'compact_aw_v4_p1_followup'
R=O.parents[3];assert not O.exists();O.mkdir()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
(O/'source_freeze.json').write_bytes((D/'source_freeze.json').read_bytes())
label='physical_p3r0_rep1_01'
names=['run_physical.py','launch_physical_hidden.py','seal_terminal.py','independent_raw_review.py','physical_snapshot.py']
for name in names:
    t=(D/name).read_text(encoding='utf8').replace('physical_p1r0_01',label)
    if name=='run_physical.py':
        old="'set_option -place_option 1' if line=='set_option -place_option 3'"
        assert t.count(old)==1
        t=t.replace(old,"'set_option -replicate_resources 1' if line=='set_option -replicate_resources 0'")
        t=t.replace("('place_option','1')","('place_option','3')").replace("('replicate_resources','0')","('replicate_resources','1')")
        # SYN provenance remains replicate_resources=0; only PNR dictionaries change.
        t=t.replace("'physical_options':{'place':1,'route':0,'map_option':2,'replicate_resources':0,'route_maxfan':23}","'physical_options':{'place':3,'route':0,'map_option':2,'replicate_resources':1,'route_maxfan':23}")
        t=t.replace('P1/R0 routability-priority','P3/R0 high-fanout PNR replication')
    ast.parse(t);(O/name).write_text(t,encoding='utf8')
(O/label).mkdir()
runner=(O/'run_physical.py').read_text(encoding='utf8')
assert "din['synthesis_options']=={'map_option':2,'replicate_resources':0}" in runner
assert runner.count("'physical_options':{'place':3,'route':0,'map_option':2,'replicate_resources':1,'route_maxfan':23}")==2
assert "('replicate_resources','1')" in runner
# Parse the exact effective Tcl transformation without evaluating vendor commands.
source=R/'out/z_aw_fix_20261026/compact_aw_v4/canonical/source/build.tcl'
lines=source.read_text(encoding='utf8').splitlines()
tcl='\n'.join('run pnr' if line=='run all' else 'open_project physical.gprj' if line=='open_project acg720_ano_port.gprj' else 'set_option -replicate_resources 1' if line=='set_option -replicate_resources 0' else line for line in lines if line.strip()!='exit')+'\nputs PHYSICAL_COMMAND_RETURNED_EOF\nflush stdout\n'
assert tkinter.Tcl().call('info','complete',tcl)==1
assert 'set_option -place_option 3' in tcl and 'set_option -route_maxfan 23' in tcl
(O/'PREPARATION.json').write_text(json.dumps({'prepared_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'scope':'Exact v4 canonical55 and frozen SYN VG e67bcab6. Change only PNR replicate_resources0 to1; no RTL, resynthesis, seed, LOC, clock or exception changes.',
    'basis':'Full-route v4 raw worst setup misses0.220ns and contains fanout115/long control nets. Official PNR replication targets high-fanout timing. Distinct v5 rep1 previously failed route, so no transferable success claim.',
    'manual':'SUG1220-2.1E PDF46, replicate_resources0/1; physical optimization may duplicate resources without modifying source-cycle behavior.',
    'physical_options':{'place':3,'route':0,'replicate_resources':1,'route_maxfan':23},'period_ns':20,
    'script_sha256':{name:sha(O/name) for name in names},'parent_preparation_sha256':sha(D/'PREPARATION.json'),
    'effective_Tcl_sha256':hashlib.sha256(tcl.encode()).hexdigest(),'syntax_and_Tcl_parse_only':True,'PNR_started':False},indent=2)+'\n',encoding='utf8')
print(json.dumps({'prepared_not_started':True,'source_files':55,'physical_replicate_resources':1,'scripts_syntax_valid':len(names),'hardware_operation':False}))
