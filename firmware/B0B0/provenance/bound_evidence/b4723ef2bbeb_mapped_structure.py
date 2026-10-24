"""Exact reduced BDD decoding of all720 physical serializer payload bits; no clocks."""
from pathlib import Path
import re,json,hashlib,functools,sys
C=Path(__file__).resolve().parents[1]
P=Path(sys.argv[1]) if len(sys.argv)>1 else Path(json.loads((C/'synthesis_study.json').read_text())['folder'])/'impl/gwsynthesis/acg720_ano_port.vg'
compact=lambda x:re.sub(r'\s+','',x)
def num(s):
 m=re.fullmatch(r"(\d+)'([bhd])([0-9a-fA-F]+)",s);assert m,s
 return int(m[3],{'b':2,'h':16,'d':10}[m[2]])
def scalar(s,widths):
 s=compact(s)
 if s in widths:
  a,b=widths[s];return [f'{s}[{i}]' for i in range(b,a+1)]
 m=re.fullmatch(r'(.+)\[(\d+):(\d+)\]',s)
 if m:return [f'{m[1]}[{i}]' for i in range(int(m[3]),int(m[2])+1)]
 return [s]
mods={}
for m in re.finditer(r'\bmodule (\w+) \(.*?endmodule',P.read_text(),re.S):
 name=m[1]
 if name not in ['acg720_ano_port','mtf_xyz_navigation_control','telemetry_tx']:continue
 s=m.group();widths={};ports={}
 for d in re.finditer(r'(?m)^(input|output|wire)\s+(?:\[(\d+):(\d+)\]\s*)?(\\\S+|\w+)\s*;',s):
  kind,a,b,n=d.groups();n=compact(n)
  if a is not None:widths[n]=(int(a),int(b))
  if kind in ['input','output']:ports[n]=(kind,scalar(n,widths))
 params={compact(a):num(b)for a,b in re.findall(r'defparam\s+(.*?)\.INIT\s*=\s*([^;]+);',s)}
 cells={};drivers={}
 for k in re.finditer(r'(?m)^  (\w+)\s+(\\\S+|\w+)\s*\((.*?)\);',s,re.S):
  typ,inst,body=k.groups();inst=compact(inst);pins={compact(a):compact(b)for a,b in re.findall(r'\.([^\s(]+)\s*\((.*?)\)',body,re.S)};cells[inst]=(typ,pins,params.get(inst))
  out='F' if typ.startswith('LUT') else 'Q' if typ.startswith('DFF') else 'O' if typ.startswith('MUX') else 'V' if typ=='VCC' else 'G' if typ=='GND' else None
  if out:
   assert out in pins,(typ,inst)
   drivers[pins[out]]=(inst,out)
 mods[name]=dict(widths=widths,ports=ports,cells=cells,drivers=drivers)
# Build parent bindings for the only three modules participating in this cone.
top=mods['acg720_ano_port'];bindings={}
for inst,(typ,pins,init)in top['cells'].items():
 if typ not in mods or typ=='acg720_ano_port':continue
 assert typ not in bindings,('Duplicate audited module instance',typ)
 mod=mods[typ];bindings[typ]={}
 for port,expr in pins.items():
  kind,bits=mod['ports'][port];values=scalar(expr,top['widths']);assert len(bits)==len(values),(typ,port,expr)
  for bit,value in zip(bits,values):
   if kind=='input':bindings[typ][bit]=value
   else:top['drivers'][value]=(typ,bit)
assert set(bindings)=={'mtf_xyz_navigation_control','telemetry_tx'}
# BDD terminal0/1; variables are ordered by their full names.
nodes={};unique={};serial=2
@functools.lru_cache(None)
def node(v,lo,hi):
 global serial
 if lo==hi:return lo
 key=(v,lo,hi)
 if key not in unique:unique[key]=serial;nodes[serial]=key;serial+=1
 return unique[key]
@functools.lru_cache(None)
def ite(c,t,e):
 if c==0:return e
 if c==1:return t
 if t==e:return t
 v=min(nodes[x][0]for x in [c,t,e]if x>1)
 def branch(x,b):return nodes[x][1+b]if x>1 and nodes[x][0]==v else x
 return node(v,ite(branch(c,0),branch(t,0),branch(e,0)),ite(branch(c,1),branch(t,1),branch(e,1)))
mode='symbols';bank=0
@functools.lru_cache(None)
def ev(mod,signal):
 signal=compact(signal)
 if signal in ["1'b0",'GND']:return 0
 if signal in ["1'b1",'VCC']:return 1
 if mod=='telemetry_tx' and mode in ['init','symbols']:
  if signal=='sending_nav':return 1
  if signal=='sending_rotation':return 0
  z=re.fullmatch(r'index\[(\d+)\]',signal)
  if z:return ((bank*8)>>int(z[1]))&1
 M=mods[mod]
 if signal in bindings.get(mod,{}):return ev('acg720_ano_port',bindings[mod][signal])
 d=M['drivers'].get(signal)
 if not d:return node(mod+'.'+signal,0,1)
 inst,out=d
 if inst in mods:return ev(inst,out)
 typ,pins,init=M['cells'][inst]
 if typ.startswith('DFF'):
  if mode=='init':assert init in [0,1];return init
  match=re.match(r'diagnostic_q_(\d+)_',inst) if mod=='mtf_xyz_navigation_control'else None
  return node('q%03d'%int(match[1]) if match else mod+'.'+signal,0,1)
 if typ=='VCC':return 1
 if typ=='GND':return 0
 if typ.startswith('LUT'):
  N=int(typ[3:]);assert init is not None
  ins=[ev(mod,pins['I'+str(i)])for i in range(N)]
  def f(level,value):
   if level==N:return (init>>value)&1
   return ite(ins[level],f(level+1,value|(1<<level)),f(level+1,value))
  return f(0,0)
 if typ=='MUX2':return ite(ev(mod,pins['S0']),ev(mod,pins['I1']),ev(mod,pins['I0']))
 raise AssertionError((mod,signal,typ,inst))
def expr(n):
 if n<2:return n
 v,lo,hi=nodes[n]
 if lo==0 and hi==1:return v
 return [v,expr(lo),expr(hi)]
results={}
for mode in ['init','symbols']:
 packet=[]
 for bank in range(12):
  ev.cache_clear();packet.extend(ev('telemetry_tx',f'decoded_bank[{i}]')for i in range(63,-1,-1))
 results[mode]=packet[32:752]
 if mode=='init':assert all(n in [0,1]for n in results[mode])
mode='control';ev.cache_clear()
bank_ces={pins['CE']for inst,(typ,pins,init)in mods['mtf_xyz_navigation_control']['cells'].items()if inst.startswith('diagnostic_q_') and typ.startswith('DFF')}
assert len(bank_ces)==1
ce_expression=expr(ev('mtf_xyz_navigation_control',next(iter(bank_ces))))
boot_condition=1
for bit in range(8):boot_condition=ite(ev('acg720_ano_port',f'boot[{bit}]'),boot_condition,0)
result={'capture_condition':ce_expression,'capture_with_boot':expr(ite(boot_condition,ev('mtf_xyz_navigation_control',next(iter(bank_ces))),0)),'netlist_sha256':hashlib.sha256(P.read_bytes()).hexdigest(),'init_hex':f'{int("".join(map(str,results["init"])),2):0180x}','mapping_msb_first':[expr(n)for n in results['symbols']],'bdd_nodes':len(nodes)}
(Path(sys.argv[2]) if len(sys.argv)>2 else C/'hardware/mapped_720_bdd.json').write_text(json.dumps(result,indent=2)+'\n');print(result['init_hex'],len(nodes));print('mapcomplex',[(719-i,x)for i,x in enumerate(result['mapping_msb_first'])if isinstance(x,list)][:36])
