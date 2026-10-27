"""Pure SYN recipe construction; only max_fanout differs from sealed STD22 SYN."""
from pathlib import Path
import re
O=Path(__file__).resolve().parent;R=O.parents[3]
PARENT=R/'out/z_aw_fix_20261026/compact_aw_v22/build_attempt_01/synth_only.tcl'
def make_recipe(source_build):
    raw=Path(source_build).read_bytes();lines=raw.decode('utf8').splitlines()
    assert lines.count('run all')==lines.count('exit')==1
    baseline='\n'.join('run syn' if line=='run all' else line for line in lines if line.strip()!='exit')+'\nputs SYNTHESIS_COMMAND_RETURNED_EOF\nflush stdout\n'
    assert baseline==PARENT.read_text(encoding='utf8')
    assert baseline.count('set_option -max_fanout 200\n')==1
    effective=baseline.replace('set_option -max_fanout 200\n','set_option -max_fanout 100\n',1)
    original=re.findall(r'^set_option -(\S+)\s+(\S+)\s*$',baseline,re.M)
    actual=re.findall(r'^set_option -(\S+)\s+(\S+)\s*$',effective,re.M)
    assert len(dict(original))==len(original) and len(dict(actual))==len(actual)
    assert dict(actual)==dict(original,max_fanout='100')
    assert [(k,a,b) for (k,a),(j,b) in zip(original,actual) if a!=b]==[('max_fanout','200','100')]
    assert effective.count('run syn\n')==1 and 'run all' not in effective and 'run pnr' not in effective
    assert Path(source_build).read_bytes()==raw
    return effective
