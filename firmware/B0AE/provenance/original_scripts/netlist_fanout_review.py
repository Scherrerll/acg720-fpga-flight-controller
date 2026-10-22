from pathlib import Path
import collections,json,re
R=Path(__file__).resolve().parent
archive=sorted((R/'attempts').glob('route916_*'))[-1]
p=archive/'fixture/impl/gwsynthesis/acg720_ano_port.vg'
s=p.read_text(errors='replace')
c=collections.Counter(); pins=collections.defaultdict(collections.Counter)
for mod,body in re.findall(r'\bmodule\s+(\\?[^\s(]+)\s*\((.*?)\bendmodule',s,re.S):
 for kind,instance,connections in re.findall(r'^  ((?:LUT|DFF|ALU|MULT|PADD|MUX|BSRAM|SP|DP|SDP)\w*)\s+(\\?[^\s(]+)\s*\((.*?)\);',body,re.M|re.S):
  for port,expression in re.findall(r'\.([A-Za-z0-9_]+)\s*\(([^()]*)\)',connections):
   if port in ['INIT','Q','QN','O','F','COUT','DO','DOUT','P','SOUT','CASO']:continue
   for signal in re.findall(r'\\[^\s,{}]+|\b[A-Za-z_][A-Za-z0-9_$]*(?:\[[0-9]+\])?',expression):
    if signal in ['GND','VCC','clk50_d']:continue
    key=mod+'::'+signal;c[key]+=1;pins[key][port]+=1
rows=[dict(signal=n,pin_loads=v,pins=dict(pins[n])) for n,v in c.most_common(40)]
(R/'tools_notes/netlist_fanout.json').write_text(json.dumps(dict(source=str(p),approximate_primitive_loads=True,nets=rows),indent=2))
for row in rows[:16]:print(row)
