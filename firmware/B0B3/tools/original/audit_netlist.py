"""Mapped-netlist clock and new async-boundary audit, no hardware."""
from pathlib import Path
import importlib.util,json,hashlib,collections,sys
R=Path(__file__).resolve().parent;P=R/'tools/read_cones.py'
F=R/sys.argv[1] if len(sys.argv)>1 else R
N=F/'source/impl/gwsynthesis/acg720_ano_port.vg'
spec=importlib.util.spec_from_file_location('read_cones',P);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
g=m.Graph(N)
same=lambda a,b:g.find(a)==g.find(b)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
ib=[(n,c)for n,c in g.cells.items() if c['type']=='IBUF' and c['pins'].get('I')==['radio_rx']]
assert len(ib)==1
pad=ib[0][1]['pins']['O'][0]
loads=[]
for n,c in g.cells.items():
 for pin,nets in c['pins'].items():
  if pin not in ('Q','F','O','G','V') and any(same(net,pad) for net in nets):loads.append((n,pin,c['type']))
assert {n for n,p,t in loads}=={'parameter_uart/rx_meta_s0','parameter_uart/rx_meta_s1'},loads
assert all(p=='D' and t.startswith('DFF')for n,p,t in loads)
meta=g.cells['parameter_uart/rx_meta_s1'];sync=g.cells['parameter_uart/rx_sync_s1']
assert same(meta['pins']['Q'][0],sync['pins']['D'][0])
meta_loads=[]
for n,c in g.cells.items():
 for pin,nets in c['pins'].items():
  if pin not in ('Q','F','O','G','V') and any(same(net,meta['pins']['Q'][0])for net in nets):meta_loads.append((n,pin))
assert {n for n,p in meta_loads}=={'parameter_uart/rx_sync_s0','parameter_uart/rx_sync_s1'} and all(p=='D'for n,p in meta_loads),meta_loads
clock=[(n,c)for n,c in g.cells.items()if c['type']=='IBUF' and c['pins'].get('I')==['clk50']]
assert len(clock)==1;clocknet=clock[0][1]['pins']['O'][0]
ground={g.find(net)for c in g.cells.values()if c['type']=='GND'for net in c['pins']['G']}
badclocks=[(n,pin,net)for n,c in g.cells.items()for pin,nets in c['pins'].items()if pin in ('CLK','CLKA','CLKB','WCLK','RCLK')for net in nets if not same(net,clocknet) and g.find(net) not in ground]
assert not badclocks,badclocks[:10]
gainregs={prefix:[n for n in g.regs if n.startswith(prefix)]for prefix in ['parameters/active_p_','parameters/active_i_','native_navigation/controller_proof/work_p_','native_navigation/controller_proof/work_i_']}
assert all(len(names)>=14 for names in gainregs.values()),gainregs
out=dict(passed=True,netlist_sha256=sha(N),parser_sha256=sha(P),cells=len(g.cells),flipflops=len(g.regs),
 asynchronous_pad=pad,direct_pad_loads=loads,first_stage_Q_loads=meta_loads,
 exception='set_false_path -from radio_rx applies only to first-stage D pins; meta-Q -> sync-D and downstream remain timed',
 single_clock='clk50 through one IBUF; all clock pins checked',gain_register_counts={p:len(n)for p,n in gainregs.items()},
 note='Gowin syn_preserve retains INIT0 shadow flops alongside functional INIT1 meta/sync flops; both first-stage pad loads enumerated. No downstream logic is on the raw pad.')
(R/'verification/netlist_audit.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
