"""Evaluate the actual work-gain mapped CE cone over all mapped state bits."""
from pathlib import Path
import hashlib,json,re
C=Path(__file__).resolve().parent;O=C/'verification';N=C/'source/impl/gwsynthesis/acg720_ano_port.vg'
text=N.read_text(errors='replace');body=re.search(r'^module mtf_xyz_hold_control\s*\(.*?^endmodule',text,re.M|re.S)[0]
cells={name:dict(type=typ,pins=dict(re.findall(r'\.(\S+)\(([^()]*)\)',cons)))for typ,name,cons in re.findall(r'^  (\S+)\s+(\S+)\s*\((.*?)\)\s*;',body,re.M|re.S)}
drivers={net:name for name,c in cells.items()for pin,net in c['pins'].items()if pin in ('F','O','Q')}
rows=[c for c in cells.values()if c['type'].startswith('DFF')and c['pins'].get('Q','').startswith(('work_p[','work_i['))]
nets={c['pins']['CE']for c in rows};assert len(rows)==32 and len(nets)==1
ce=next(iter(nets));saved=[c for c in cells.values()if c['type'].startswith('DFF')and c['pins'].get('Q','').startswith(('saved_ix[','saved_iy['))];assert len(saved)==54 and all(c['pins']['CE']==ce for c in saved);cone={};leaves=set()
def visit(net):
 name=drivers[net];c=cells[name]
 if c['type'].startswith('DFF'):
  assert re.fullmatch(r'state\[[0-6]\]',net),(net,name);leaves.add(net);return
 assert c['type'].startswith('LUT'),(net,c)
 init=re.search(r'defparam\s+'+re.escape(name)+r'\.INIT=(\d+)\'h([0-9a-fA-F]+)',body);assert init,(name,c)
 cone[net]=dict(cell=name,type=c['type'],INIT=init[0].split('=')[1],table=int(init[2],16),pins=c['pins'])
 for pin,value in c['pins'].items():
  if re.fullmatch(r'I\d+',pin):visit(value)
visit(ce)
assert leaves=={f'state[{i}]'for i in range(7)}
assert not any(c['pins'].get('Q')=='state[7]'for c in cells.values()if c['type'].startswith('DFF'))
def evaluate(net,state):
 match=re.fullmatch(r'state\[(\d+)\]',net)
 if match:return(state>>int(match[1]))&1
 c=cone[net];index=sum(evaluate(value,state)<<int(pin[1:])for pin,value in c['pins'].items()if re.fullmatch(r'I\d+',pin))
 return(c['table']>>index)&1
truth=[evaluate(ce,state)for state in range(128)];assert truth==[1]+[0]*127
out=dict(passed=True,work_gain_CE=ce,work_gain_FF=32,saved_integral_FF=54,idle_CE_FF=86,actual_mapped_boolean='state[6:0] == 0',all_mapped_state_combinations_checked=128,only_asserted_state=0,source_scope='Unchanged reachable source state graph uses states0..101; source state[7] optimized away. This is a small mapped-LUT decode truth-table check, not full sequential netlist equivalence.',cone=cone,state_leaves=sorted(leaves),netlist_sha256=hashlib.sha256(N.read_bytes()).hexdigest(),script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
(O/'idle_decode_audit.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
