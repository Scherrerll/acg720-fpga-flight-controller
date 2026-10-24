"""Read-only exact BDD audit of mapped MTF snapshot. Usage: python mapped_mtf_audit.py NEW.vg [report.json]. Fails closed; never invokes synthesis."""
from pathlib import Path
import re,sys,json,hashlib,functools
compact=lambda s:re.sub(r'\s+','',s)
def num(s):
 m=re.fullmatch(r"(\d+)'([bhd])([0-9a-fA-F]+)",compact(s));assert m,s
 return int(m[3],{'b':2,'h':16,'d':10}[m[2]])
nodes={};unique={}
@functools.lru_cache(None)
def node(v,l,h):
 if l==h:return l
 k=(v,l,h)
 if k not in unique:unique[k]=len(unique)+2;nodes[unique[k]]=k
 return unique[k]
@functools.lru_cache(None)
def ite(c,t,e):
 if c==0:return e
 if c==1:return t
 if t==e:return t
 v=min(nodes[x][0]for x in (c,t,e)if x>1)
 def b(x,i):return nodes[x][i+1]if x>1 and nodes[x][0]==v else x
 return node(v,ite(b(c,0),b(t,0),b(e,0)),ite(b(c,1),b(t,1),b(e,1)))
def AND(a,b):return ite(a,b,0)
def NOT(a):return ite(a,0,1)
def bits(s,w):
 s=compact(s)
 if s in w:return [f'{s}[{i}]'for i in range(w[s][1],w[s][0]+1)]
 m=re.fullmatch(r'(.+)\[(\d+):(\d+)\]',s)
 if m:return [f'{m[1]}[{i}]'for i in range(int(m[3]),int(m[2])+1)]
 if s.startswith('{'):
  return sum((bits(x,w)for x in reversed(s[1:-1].split(','))),[])
 m=re.fullmatch(r"(\d+)'([bhd])([0-9a-fA-F]+)",s)
 if m:return ["1'b"+str((num(s)>>i)&1)for i in range(int(m[1]))]
 return [s]
class Graph:
 def __init__(self,path):
  self.path=Path(path);self.sha=hashlib.sha256(self.path.read_bytes()).hexdigest();self.mods={};self.ctx={};self.mode='normal';self.bank=0;self.bank_labels={}
  for z in re.finditer(r'\bmodule (\w+) \(.*?endmodule',self.path.read_text(),re.S):
   s=z.group();w={};ports={}
   for d in re.finditer(r'(?m)^(input|output|wire)\s+(?:\[(\d+):(\d+)\]\s*)?(\\\S+|\w+)\s*;',s):
    k,a,b,n=d.groups();n=compact(n)
    if a is not None:w[n]=(int(a),int(b))
    if k in ('input','output'):ports[n]=(k,bits(n,w))
   params={compact(a):num(b)for a,b in re.findall(r'defparam\s+(.*?)\.INIT\s*=\s*([^;]+);',s)};alu_modes={compact(a):int(b)for a,b in re.findall(r'defparam\s+(.*?)\.ALU_MODE\s*=\s*(\d+);',s)};cells={};drivers={}
   for c in re.finditer(r'(?m)^  (\w+)\s+(\\\S+|\w+)\s*\((.*?)\);',s,re.S):
    typ,inst,body=c.groups();inst=compact(inst);pins={compact(a):compact(b)for a,b in re.findall(r'\.([^\s(]+)\s*\((.*?)\)',body,re.S)};cells[inst]=(typ,pins,params.get(inst))
    out='F'if typ.startswith('LUT')else 'Q'if typ.startswith('DFF')else 'O'if typ.startswith('MUX')else 'V'if typ=='VCC'else 'G'if typ=='GND'else None
    if typ=='ALU':
     cells[inst]=(typ,pins,alu_modes[inst])
     for pin in ('SUM','COUT'):
      if pin in pins:assert pins[pin]not in drivers;drivers[pins[pin]]=inst
    if out:assert pins[out]not in drivers;drivers[pins[out]]=inst
   self.mods[z[1]]=(w,ports,cells,drivers)
  self.build('','acg720_ano_port',None,{})
  self.mtf=next(p for p,v in self.ctx.items()if v['mod']=='mtf01p_reader');self.tx=next(p for p,v in self.ctx.items()if v['mod']=='telemetry_tx')
 def build(self,path,mod,parent,bindings):
  w,ports,cells,drivers=self.mods[mod];v=dict(mod=mod,parent=parent,bindings=bindings,drivers=dict(drivers));self.ctx[path]=v
  for inst,(typ,pins,init)in cells.items():
   if typ not in self.mods:continue
   child=path+'/'+inst;bind={}
   for port,expr in pins.items():
    kind,local=self.mods[typ][1][port];outer=bits(expr,w);assert len(local)==len(outer),(mod,inst,port)
    for a,b in zip(local,outer):
     if kind=='input':bind[a]=b
     else:assert b not in v['drivers'];v['drivers'][b]=(child,a)
   self.build(child,typ,path,bind)
 @functools.lru_cache(None)
 def ev(self,path,s):
  if s in ("1'b0",'GND'):return 0
  if s in ("1'b1",'VCC'):return 1
  v=self.ctx[path];mod=v['mod']
  if path==self.tx and self.mode in ('map','init'):
   if s=='sending_mtf':return 1
   if s in ('sending_nav','sending_rotation'):return 0
   m=re.fullmatch(r'index\[(\d+)\]',s)
   if m:return ((self.bank*8)>>int(m[1]))&1
  if s in v['bindings']:return self.ev(v['parent'],v['bindings'][s])
  d=v['drivers'].get(s)
  if d is None:
   assert v['parent'] is None or s in sum((p[1]for p in self.mods[mod][1].values()),[]),('undriven internal',path,s)
   return node(path+'.'+s,0,1)
  if isinstance(d,tuple):return self.ev(*d)
  typ,pins,init=self.mods[mod][2][d]
  if typ.startswith('DFF'):
   if self.mode=='init':assert init in (0,1),(path,d,init);return init
   m=re.fullmatch(r'diagnostic_body_(\d+)_.*',d)if path==self.mtf else None
   return node(self.bank_labels.get(m[1],'MTF_BANK_'+m[1])if m else path+'.'+s,0,1)
  if typ=='VCC':return 1
  if typ=='GND':return 0
  if typ.startswith('LUT'):
   n=int(typ[3:]);assert init is not None
   ins=[self.ev(path,pins['I'+str(i)])for i in range(n)]
   def f(i,x):return (init>>x)&1 if i==n else ite(ins[i],f(i+1,x|(1<<i)),f(i+1,x))
   return f(0,0)
  if typ=='MUX2':return ite(self.ev(path,pins['S0']),self.ev(path,pins['I1']),self.ev(path,pins['I0']))
  if typ=='ALU':
   assert init==0,('Only ALU add mode0 supported',path,d,init)
   assert self.ev(path,pins['I3'])==1,('ALU mode0 unexpected I3',path,d)
   a,b,c=[self.ev(path,pins[k])for k in ('I0','I1','CIN')];xor=ite(a,NOT(b),b)
   return ite(xor,NOT(c),c) if pins.get('SUM')==s else ite(xor,c,a)
  raise AssertionError(('unsupported cone primitive',path,s,typ,d))
 def setmode(self,mode):self.mode=mode;self.ev.cache_clear()
 def packet(self,mode):
  self.setmode(mode);out=[]
  for self.bank in range(16):
   self.ev.cache_clear();out.extend(self.ev(self.tx,f'decoded_bank[{i}]')for i in range(63,-1,-1))
  return out[32:1008]
 def bankcells(self):return {i:(t,p,n)for i,(t,p,n)in self.mods['mtf01p_reader'][2].items()if i.startswith('diagnostic_body_')and t.startswith('DFF')}
def expression(n):
 if n<2:return n
 v,l,h=nodes[n]
 return v if l==0 and h==1 else [v,expression(l),expression(h)]
def main():
 assert len(sys.argv)>=2,'Provide the actual new synthesis VG path'
 here=Path(__file__).resolve().parent;root=next(p for p in here.parents if (p/'variants/published_anchor_p2_r2_rep1').is_dir())
 old=Graph(root/'variants/published_anchor_p2_r2_rep1/fixture/impl/gwsynthesis/acg720_ano_port.vg');new=Graph(sys.argv[1]);assert old.sha!=new.sha,'New VG must differ from reference'
 for g in (old,new):
  raw=g.packet('map');aliases={}
  for i,x in enumerate(raw):
   if x>1:
    label=expression(x);assert isinstance(label,str) and label.startswith('MTF_BANK_'),('Complex mapped output',i,label)
    aliases.setdefault(label.removeprefix('MTF_BANK_'),[]).append(975-i)
  assert len(aliases)==len(g.bankcells()),'Some bank FF lacks an audited logical output'
  g.bank_labels={k:'MTF_LOGICAL_'+','.join(map(str,v))for k,v in aliases.items()}
 om=old.packet('map');nm=new.packet('map');assert om==nm,'Logical 976-bit bank/constant/alias mapping changed'
 assert old.packet('init')==new.packet('init')==[0]*976,'Logical output INIT changed'
 ob=old.bankcells();nb=new.bankcells();assert len(ob)==827,('Reference bank count drift',len(ob));old_by_bit={old.bank_labels[re.fullmatch(r'diagnostic_body_(\d+)_.*',i)[1]]:i for i in ob}; new_by_bit={new.bank_labels[re.fullmatch(r'diagnostic_body_(\d+)_.*',i)[1]]:i for i in nb}; assert len(old_by_bit)==len(ob) and len(new_by_bit)==len(nb); assert set(old_by_bit)==set(new_by_bit),'Bank alias classes changed'
 old.setmode('normal');new.setmode('normal');ces=set();resets=set();mapping=[]
 for inst,(ot,op,oi)in ob.items():
  candidate_inst=new_by_bit[old.bank_labels[re.fullmatch(r'diagnostic_body_(\d+)_.*',inst)[1]]]; nt,np,ni=nb[candidate_inst];assert oi==ni==0,(inst,'INIT');assert nt in ('DFFCE','DFFRE'),(inst,'unexpected reset/set primitive',nt)
  assert set(np)-{'Q','D','CLK','CE'} <= {'CLEAR','RESET','SET','PRESET'},(inst,'unexpected port',np)
  assert all(new.ev(new.mtf,np[k])==0 for k in set(np)-{'Q','D','CLK','CE'}),(inst,'active reset/set port',np)
  assert ot=='DFFRE'and set(op)=={'Q','D','CLK','CE','RESET'},(inst,ot,op)
  assert old.ev(old.mtf,op['D'])==new.ev(new.mtf,np['D']),(inst,'D/payload cone changed')
  assert old.ev(old.mtf,op['CLK'])==new.ev(new.mtf,np['CLK']),(inst,'clock changed')
  reset=old.ev(old.mtf,op['RESET']);ce=old.ev(old.mtf,op['CE']);nce=new.ev(new.mtf,np['CE'])
  assert nce==AND(NOT(reset),ce),(inst,'CE != released reset AND original capture')
  ces.add(nce);resets.add(reset);mapping.append(dict(reference_cell=inst,candidate_cell=candidate_inst,q=np['Q']))
 assert len(ces)==len(resets)==1
 # Verify the actual mapped boot state transition exhaustively over all 256 states.
 for g in (old,new):
  matches=[(p,s)for p,v in g.ctx.items()for s in v['drivers']if re.fullmatch(r'boot\[\d+\]',s) and isinstance(v['drivers'][s],str)]
  paths=sorted(set(p for p,s in matches)); assert paths
  if g is old:
   release=1
   for i in range(8):release=AND(release,g.ev('',f'boot[{i}]'))
   assert next(iter(resets))==NOT(release),'Reference reset not inverse top boot==255'
  for bp in paths:
   assert sum(p==bp for p,s in matches)==8
   boot=[g.ev(bp,f'boot[{i}]')for i in range(8)];release=1
   for b in boot:release=AND(release,b)
   for i in range(8):
    inst=g.ctx[bp]['drivers'][f'boot[{i}]'];t,p,init=g.mods[g.ctx[bp]['mod']][2][inst];assert init==0
    assert t in ('DFFCE','DFFRE')and set(p)-{'Q','D','CLK','CE'} <= {'RESET','CLEAR'},('boot primitive needs review',t,p)
    assert all(g.ev(bp,p[k])==0 for k in set(p)-{'Q','D','CLK','CE'}),('boot reset not inactive',p)
    actual=ite(g.ev(bp,p['CE']),g.ev(bp,p['D']),boot[i])
    # Ripple increment, saturated at 255.
    carry=1
    for j in range(i):carry=AND(carry,boot[j])
    increment=ite(carry,NOT(boot[i]),boot[i]);expected=ite(release,boot[i],increment)
    assert actual==expected,('mapped boot not saturating increment',i)
 report=dict(passed=True,reference_vg_sha256=old.sha,candidate_vg_sha256=new.sha,logical_bits=976,physical_bank_ffs=len(nb),all_logical_init_zero=True,all_bank_init_zero=True,logical_mapping_msb_first=[expression(x)for x in nm],physical_mapping=mapping,capture_condition=expression(next(iter(ces))),d_payload_boolean_equal=True,boot_init_zero_and_saturating=True,scope='Exact combinational BDD equivalence with named nonbank Q/input boundaries. Does not prove nonbank sequential state equivalence, full serializer timing, PNR, or hardware behavior. Candidate VG hash must match the later full build.')
 out=Path(sys.argv[2])if len(sys.argv)>2 else here/'mapped_mtf_audit.json';out.write_text(json.dumps(report,indent=2)+'\n');print('PASS MTF976 / 827 bank FF; '+new.sha)
if __name__=='__main__':main()
