"""Physical-only netlist recipe; source build.tcl remains exact STD22 max200."""
from pathlib import Path
import re
def make_physical_recipe(build_tcl):
    raw=Path(build_tcl).read_bytes();lines=raw.decode('utf8').splitlines()
    assert lines.count('run all')==lines.count('exit')==1
    assert lines.count('set_option -max_fanout 200')==1
    text='\n'.join('run pnr' if x=='run all' else 'open_project physical.gprj' if x=='open_project acg720_ano_port.gprj' else 'set_option -max_fanout 100' if x=='set_option -max_fanout 200' else x for x in lines if x.strip()!='exit')+'\nputs PHYSICAL_COMMAND_RETURNED_EOF\nflush stdout\n'
    original=re.findall(r'^set_option -(\S+)\s+(\S+)\s*$', '\n'.join(lines),re.M)
    actual=re.findall(r'^set_option -(\S+)\s+(\S+)\s*$', text,re.M)
    assert len(dict(original))==len(original) and len(dict(actual))==len(actual)
    assert dict(actual)==dict(original,max_fanout='100')
    for key,value in [('place_option','3'),('route_option','0'),('map_option','2'),('replicate_resources','0'),('timing_driven','1'),('route_maxfan','23'),('global_freq','50'),('user_code','0000B0B4')]:assert dict(actual)[key]==value
    assert text.count('run pnr\n')==1 and 'run syn' not in text and 'run all' not in text
    assert Path(build_tcl).read_bytes()==raw
    return text
