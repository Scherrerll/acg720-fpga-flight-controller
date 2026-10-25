"""Actual mapped resources, gain-enable pin loads and clock/radio-boundary audit."""
from pathlib import Path
import collections,hashlib,importlib.util,json,re,xml.etree.ElementTree as ET
C=Path(__file__).resolve().parent;R=C.parents[1];S=C/'source';O=C/'verification'
record=json.loads((C/'change.json').read_text());B=Path(record['baseline'])
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
N=S/'impl/gwsynthesis/acg720_ano_port.vg';BN=B/'impl/gwsynthesis/acg720_ano_port.vg'
X=S/'impl/gwsynthesis/acg720_ano_port_syn_rsc.xml';BX=B/'impl/gwsynthesis/acg720_ano_port_syn_rsc.xml'
assert json.loads((O/'synthesis_exit.json').read_text())['actual_p_wait']==0
for rel,digest in record['baseline_source_sha256'].items():assert sha(B/rel)==digest
for rel,digest in record['candidate_source_sha256'].items():assert sha(S/rel)==digest
def resource(path):
 root=ET.parse(path).getroot()
 def values(node):return {k:int(re.match(r'\d+',v)[0])for k,v in node.attrib.items()if k.startswith('T_')}
 return {'top':values(root),'controller':values(next(n for n in root.iter()if n.attrib.get('name')=='controller_proof')),'bank':values(next(n for n in root.iter()if n.attrib.get('name')=='parameters'))}
oldres,newres=resource(BX),resource(X)
delta={scope:{k:newres[scope].get(k,0)-oldres[scope].get(k,0)for k in oldres[scope].keys()|newres[scope].keys()}for scope in oldres}
def inventory(path,module):
 text=path.read_text(errors='replace');body=re.search(r'^module\s+'+module+r'\s*\(.*?^endmodule',text,re.M|re.S)[0]
 cells={};loads=collections.defaultdict(list);regs=[];groups=collections.defaultdict(list)
 outputs={'F','Q','O','G','V','SUM','COUT'}
 for cell in re.finditer(r'^  (\S+)\s+(\S+)\s*\((.*?)\)\s*;',body,re.M|re.S):
  typ,name,cons=cell.groups();pins=dict(re.findall(r'\.(\S+)\(([^()]*)\)',cons));cells[name]={'type':typ,'pins':pins}
  for pin,net in pins.items():
   if pin not in outputs:loads[net].append((name,pin,typ))
  if typ.startswith('DFF'):
   row={'cell':name,'type':typ,**pins};regs.append(row);groups[pins['Q'].split('[')[0]].append(row)
 def ce(net):
  rows=[r for r in regs if r.get('CE')==net]
  drivers=[{'cell':name,**v}for name,v in cells.items()if any(v['pins'].get(pin)==net for pin in outputs)]
  for d in drivers:
   init=re.search(r'defparam\s+'+re.escape(d['cell'])+r'\.INIT=([^;]+)',body)
   if init:d['INIT']=init[1]
  return dict(net=net,total_direct_input_pins=len(loads[net]),pin_counts=dict(collections.Counter(pin for _,pin,_ in loads[net])),CE_FF_pins=len(rows),CE_Q_groups=dict(collections.Counter(r['Q'].split('[')[0]for r in rows)),drivers=drivers)
 names=['work_p','work_i','saved_ix','saved_iy','saved_afx','saved_afy','ix_store','iy_store']
 selected={name:dict(mapped_FF=len(groups[name]),indices=sorted(int(re.search(r'\[(\d+)\]',r['Q'])[1])for r in groups[name]),CE_nets=dict(collections.Counter(r.get('CE','<none>')for r in groups[name])),rows=groups[name])for name in names}
 relevant=set(r['CE']for name in names for r in groups[name]if 'CE'in r)
 return dict(all_mapped_FF=len(regs),selected=selected,relevant_CE={n:ce(n)for n in sorted(relevant)},all_FF=regs)
old,new=inventory(BN,'mtf_xyz_hold_control'),inventory(N,'mtf_xyz_hold_control')
def only_ce(inv,name):
 nets=inv['selected'][name]['CE_nets'];assert len(nets)==1,(name,nets);return next(iter(nets))
old_snapshot=only_ce(old,'saved_ix');new_snapshot=only_ce(new,'saved_afx');new_work=only_ce(new,'work_p')
purpose=dict(reference_snapshot=old['relevant_CE'][old_snapshot],candidate_snapshot=new['relevant_CE'][new_snapshot],candidate_work=new['relevant_CE'][new_work])
assert old['relevant_CE'][old_snapshot]['CE_FF_pins']==183
assert only_ce(old,'work_p')==only_ce(old,'work_i')!=old_snapshot
assert only_ce(new,'work_i')==new_work and new_work!=new_snapshot
assert new['relevant_CE'][new_snapshot]['CE_FF_pins']==129,purpose
assert new['relevant_CE'][new_work]['CE_FF_pins']==86,purpose
assert new['relevant_CE'][new_work]['CE_Q_groups']=={'work_p':16,'work_i':16,'saved_ix':27,'saved_iy':27},purpose
for name,width in [('work_p',16),('work_i',16),('saved_ix',27),('saved_iy',27),('saved_afx',33),('saved_afy',33),('ix_store',27),('iy_store',27)]:
 assert old['selected'][name]['mapped_FF']==new['selected'][name]['mapped_FF']==width
 assert new['selected'][name]['indices']==list(range(width))
for name in ['saved_afx','saved_afy']:assert only_ce(new,name)==new_snapshot
for name in ['saved_ix','saved_iy']:assert only_ce(new,name)==new_work
bank=inventory(N,'xy_pi_parameters')
bank_p=[r for r in bank['all_FF']if r['Q']in[f'parameter_response_{96+i}'for i in range(16)]]
bank_i=[r for r in bank['all_FF']if r['Q']in[f'parameter_response_{80+i}'for i in range(16)]]
assert len(bank_p)==len(bank_i)==16
P=R/'tools/read_cones.py';spec=importlib.util.spec_from_file_location('read_cones',P);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);g=m.Graph(N)
same=lambda a,b:g.find(a)==g.find(b)
ib=[(n,c)for n,c in g.cells.items()if c['type']=='IBUF'and c['pins'].get('I')==['radio_rx']];assert len(ib)==1
pad=ib[0][1]['pins']['O'][0];all_loads=collections.defaultdict(list)
for name,cell in g.cells.items():
 for pin,nets in cell['pins'].items():
  if pin not in ('Q','F','O','G','V','SUM','COUT'):
   for net in nets:all_loads[g.find(net)].append((name,pin,cell['type']))
padloads=all_loads[g.find(pad)]
assert {n for n,p,t in padloads}=={'parameter_uart/rx_meta_s0','parameter_uart/rx_meta_s1'} and all(p=='D'and t.startswith('DFF')for n,p,t in padloads),padloads
meta=g.cells['parameter_uart/rx_meta_s1'];sync=g.cells['parameter_uart/rx_sync_s1'];assert same(meta['pins']['Q'][0],sync['pins']['D'][0])
metaloads=all_loads[g.find(meta['pins']['Q'][0])]
assert {n for n,p,t in metaloads}=={'parameter_uart/rx_sync_s0','parameter_uart/rx_sync_s1'} and all(p=='D'for n,p,t in metaloads),metaloads
clock=[(n,c)for n,c in g.cells.items()if c['type']=='IBUF'and c['pins'].get('I')==['clk50']];assert len(clock)==1
clocknet=clock[0][1]['pins']['O'][0];ground={g.find(net)for c in g.cells.values()if c['type']=='GND'for net in c['pins']['G']}
clockpins=[(n,pin,net)for n,c in g.cells.items()for pin,nets in c['pins'].items()if pin in ('CLK','CLKA','CLKB','WCLK','RCLK')for net in nets]
bad=[x for x in clockpins if not same(x[2],clocknet)and g.find(x[2])not in ground];assert not bad,bad[:10]
gain_connections=[]
for name,base in [('work_p',96),('work_i',80)]:
 for row in new['selected'][name]['rows']:
  bit=int(re.search(r'\[(\d+)\]',row['Q'])[1]);d='native_navigation/controller_proof/'+row['D'];bankq='parameters/parameter_response_'+str(base+bit)
  assert same(d,bankq),(name,bit,d,bankq)
  gain_connections.append(dict(work=name,bit=bit,D=d,bank_Q=bankq))
source_old=(B/'position/mtf_xyz_hold_control.v').read_bytes();source_new=(S/'position/mtf_xyz_hold_control.v').read_bytes()
assert source_new[:source_new.index(b' // Width trial:')]==source_old[:source_old.index(b' // Width trial:')]
assert (S/'acg720_ano_port.sdc').read_bytes()==(B/'acg720_ano_port.sdc').read_bytes()
def top_ports(path):
 body=re.search(r'^module\s+acg720_ano_port\s*\(.*?^endmodule',path.read_text(errors='replace'),re.M|re.S)[0]
 return re.findall(r'^(input|output|inout)\s+(?:wire\s+)?(?:\[(-?\d+):(-?\d+)\]\s+)?(\S+)\s*;',body,re.M)
assert top_ports(N)==top_ports(BN)
out=dict(passed=True,purpose_realized=True,mode='synthesis only; PNR not started; no packed CLS/routing/timing claim',actual_p_wait=0,reference_resources=oldres,candidate_resources=newres,delta=delta,mapped_CE=purpose,controller_FF=dict(reference=old['all_mapped_FF'],candidate=new['all_mapped_FF']),selected_gain_and_saved_registers=new['selected'],clock_audit=dict(all_clock_pin_count=len(clockpins),non_clk50_non_ground=[],source='clk50 through one IBUF'),radio_audit=dict(raw_pad_loads=padloads,meta_Q_loads=metaloads,exception='unchanged sole false path radio_rx -> first synchronizer D; meta-Q -> sync-D remains timed'),gain_audit=dict(bank_p_FF=len(bank_p),bank_i_FF=len(bank_i),work_p_FF=16,work_i_FF=16,bank_to_work_connections=gain_connections,source_controller_ports_byte_identical=True),top_port_audit=dict(mapped_top_ports_equal=True,ports=top_ports(N)),files={str(p):sha(p)for p in [N,BN,X,BX,P,Path(__file__)]})
(O/'synthesis_comparison.json').write_text(json.dumps(out,indent=2))
print(json.dumps(dict(passed=True,purpose_realized=True,resources=dict(reference=oldres,candidate=newres,delta=delta),mapped_CE=purpose,clock_pins=len(clockpins),radio_pad_loads=padloads),indent=2),flush=True)
