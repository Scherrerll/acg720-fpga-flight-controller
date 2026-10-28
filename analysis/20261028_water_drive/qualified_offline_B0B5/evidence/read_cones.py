"""Read-only Gowin LUT/carry logic-cone inspection for these fixed candidates."""
from pathlib import Path
import re,json,collections,sys
ROOT=Path(__file__).resolve().parents[1]
TRIALS={
 'baseline':ROOT.parent/'timeout_policy_20261025/synthesis_final/fixture/impl/gwsynthesis/acg720_ano_port.vg',
 'factor':ROOT/'control_factor_syn/fixture/impl/gwsynthesis/acg720_ano_port.vg',
 'factor_v2':ROOT/'control_factor_v2_syn/fixture/impl/gwsynthesis/acg720_ano_port.vg',
}
class Graph:
 def __init__(self,path):
  self.modules={};self.p={};self.edges=[];self.regs={};self.cells={};self.ports={};self.assign=[]
  s=path.read_text(errors='replace')
  for m in re.finditer(r'^module\s+(\S+)\s*\((.*?)\)\s*;(.*?)^endmodule',s,re.S|re.M):
   name,_,body=m.groups();ports={}
   for d in re.finditer(r'^(input|output|inout)\s+(?:wire\s+)?(?:\[(-?\d+):(-?\d+)\]\s+)?(\S+)\s*;',body,re.M):
    _,hi,lo,n=d.groups();ports[n]=[n]if hi is None else[f'{n}[{i}]'for i in range(int(hi),int(lo)+(1 if int(lo)>int(hi)else-1),1 if int(lo)>int(hi)else-1)]
   instances=[]
   for c in re.finditer(r'^  (\S+)\s+(\S+)\s*\((.*?)\)\s*;',body,re.S|re.M):
    typ,inst,cons=c.groups();pins=dict(re.findall(r'\.(\S+)\(([^()]*)\)',cons));instances.append((typ,inst,pins))
   assigns=re.findall(r'^assign\s+(.*?)\s*=\s*(.*?)\s*;',body,re.M)
   self.modules[name]=(ports,instances,assigns)
  self.flatten('acg720_ano_port','')
  self.adj=collections.defaultdict(list)
  for a,b,cell in self.edges:self.adj[self.find(a)].append((self.find(b),cell))
 def find(self,x):
  self.p.setdefault(x,x)
  if self.p[x]!=x:self.p[x]=self.find(self.p[x])
  return self.p[x]
 def union(self,a,b):self.p[self.find(a)]=self.find(b)
 def bits(self,expr,prefix):
  expr=expr.strip()
  if expr.startswith('{'):
   return [v for e in expr[1:-1].split(',')for v in self.bits(e,prefix)]
  r=re.fullmatch(r'(\S+)\[(\d+):(\d+)\]',expr)
  if r:
   n,hi,lo=r.groups();return[prefix+n+'['+str(i)+']'for i in range(int(hi),int(lo)+(1 if int(lo)>int(hi)else-1),1 if int(lo)>int(hi)else-1)]
  return[prefix+expr]
 def flatten(self,typ,prefix):
  ports,insts,assigns=self.modules[typ]
  for left,right in assigns:
   lb,rb=self.bits(left,prefix),self.bits(right,prefix)
   if len(lb)==len(rb):
    for a,b in zip(lb,rb):self.union(a,b)
  for celltyp,inst,pins in insts:
   full=prefix+inst
   if celltyp in self.modules:
    childports=self.modules[celltyp][0]
    for pin,expr in pins.items():
     bs=self.bits(expr,prefix);cs=[full+'/'+v for v in childports[pin]]
     if len(bs)!=len(cs):
      # Bare whole vectors: Gowin only omits a range when widths match.
      if len(bs)==1 and len(cs)>1 and '['not in expr and "'"not in expr:
       bs=[prefix+expr+v[v.index('['):]for v in childports[pin]]
      else:raise ValueError((full,pin,expr,len(bs),len(cs)))
     for a,b in zip(bs,cs):self.union(a,b)
    self.flatten(celltyp,full+'/')
   else:
    p={k:self.bits(v,prefix) for k,v in pins.items()}
    self.cells[full]=dict(type=celltyp,pins=p)
    if celltyp.startswith('DFF'):
     self.regs[full]=p;continue
    if celltyp.startswith('LUT'):outs=['F'];ins=[k for k in p if k.startswith('I')]
    elif celltyp=='ALU':outs=['SUM','COUT'];ins=['I0','I1','I3','CIN']
    elif celltyp in ['MUX2','MUX2_LUT5','MUX2_LUT6','MUX2_LUT7','MUX2_LUT8']:outs=['O'];ins=['I0','I1','S0']
    elif celltyp in ['INV','BUF','BUFG']:outs=['O'];ins=['I']
    else:continue
    for o in outs:
     for b in p.get(o,[]):
      for i in ins:
       for a in p.get(i,[]):self.edges.append((a,b,full))
 def paths(self,source):
  source=self.find(source);best={source:(0,[])};q=collections.deque([source]);relax=0
  while q:
   a=q.popleft();d,path=best[a]
   for b,cell in self.adj[a]:
    if d+1>best.get(b,(-1,[]))[0]:
     if cell in path:continue
     best[b]=(d+1,path+[cell]);q.append(b);relax+=1
     if relax>1000000:raise ValueError('Unexpected combinational cycle')
  return best
 def trace(self,source,target):
  path=self.paths(source).get(self.find(target));return None if path is None else dict(depth=path[0],cells=path[1])
 def report(self):
  src='nav_vertical_ready';best=self.paths(src);out={}
  for reg,p in self.regs.items():
   if reg in ['core/controller_run_s0']or reg.startswith('core/outputs/latched3_')or reg.startswith('native_navigation/control_epoch_'):
    for pin in ['D','CE','RESET','SET']:
     for net in p.get(pin,[]):
      if self.find(net)in best:
       depth,cells=best[self.find(net)];out[reg+'/'+pin]=dict(depth=depth,cells=cells)
  # List direct core outputs and named fallback cells reached from V.
  for reg in ['core/fallback_control/height_fallback_active_s','core/fallback_control/height_fallback_active_s0','core/fallback_control/height_fallback_active_s1']:
   if reg in self.cells:
    for net in self.cells[reg]['pins'].get('F',[]):out[reg+'/F']=self.trace(src,net)
  return dict(cells=len(self.cells),registers=len(self.regs),nav_ready_reachable=out)
if __name__=='__main__':
 out={}
 for name,path in TRIALS.items():
  if path.exists():
   print('Reading '+name,flush=True);g=Graph(path);out[name]=g.report()
 (ROOT/'control_factor/logic_cones.json').write_text(json.dumps(out,indent=2)+'\n')
 print(json.dumps(out,indent=2))
