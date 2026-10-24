"""Prepared only: source-expression algebra/projection, no simulator/build invocation.
Run only on root authorization after the actual physical winner is selected.
"""
from pathlib import Path
import re,json,hashlib
D=Path(__file__).resolve().parent;P=D.parent;H=P.parent
B=H/'published_tilt4500_proposal/synthesis_only/20261024T005225_383171Z';N=P/'synthesis_only/20261024T013341_913278Z'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
compact=lambda s:re.sub(r'\s+','',s)
def outer(s):
 s=compact(s)
 while s.startswith('(') and s.endswith(')'):
  level=0;wrap=True
  for i,c in enumerate(s):
   level+=(c=='(')-(c==')')
   if level==0 and i<len(s)-1:wrap=False;break
  if not wrap:break
  s=s[1:-1]
 return s
def conjuncts(s):
 s=outer(s);level=0;start=0;parts=[];i=0
 while i<len(s):
  c=s[i];level+=(c=='(')-(c==')');assert level>=0
  if level==0 and s[i:i+2]=='&&':parts.append(s[start:i]);i+=2;start=i;continue
  i+=1
 assert level==0;parts.append(s[start:]);return parts

def expression(s,name):
 patterns=[r'(?m)^\s*assign\s+'+name+r'\s*=\s*(.*?);',r'(?m)^\s*(?:\(\*.*?\*\)\s*)?wire\s+(?:\[[^]]+\]\s*)?'+name+r'\s*=\s*(.*?);']
 found=[]
 for p in patterns:found+=re.findall(p,s,re.S)
 assert len(found)==1,(name,found)
 return found[0]
def instance(s,typ,name):
 m=re.search(r'\b'+typ+r'\s*#\((.*?)\)\s*'+name+r'\s*\((.*?)\);',s,re.S);assert m
 def pins(text):return {a:compact(b) for a,b in re.findall(r'\.(\w+)\s*\((.*?)\)',text,re.S)}
 return pins(m[1]),pins(m[2])
def main():
 frozen=json.loads((D/'prepared_inputs.json').read_text());assert all(sha(p)==h for p,h in frozen['bindings'].items())
 names=['sensor/mtf_shared_geometry.v','position/mtf_shared_height_fusion.v','mtf_xyz_navigation_control.v'];olds={n:(B/n).read_text() for n in names};news={n:(N/n).read_text() for n in names}
 # Exact producer source projection: removes only appended output and kept-tail block.
 for n,port,marker in [(names[0],'height_ready_state_numeric_tail',' // Caller supplies rst_n,'),(names[1],'estimate_ready_state_numeric_tail',' // Caller supplies range_valid,')]:
  s=news[n];start=s.index(marker);end=s.index('\n',s.index(' assign '+port+'=',start))+1;s=s[:start]+s[end:]
  addition=',\n output wire '+port+('' if n==names[0] else '\n');assert s.count(addition)==1;s=s.replace(addition,'');assert s==olds[n],n
 # Exact NAV reverse projection, preserving every old state/connection/diagnostic expression.
 s=news[names[2]];o=olds[names[2]]
 s=s.replace(' localparam integer CONTROL_POSE_AGE_LIMIT=3000000,CONTROL_HEIGHT_AGE_LIMIT=5000000;\n wire geometry_height_state_numeric_tail,height_estimate_state_numeric_tail;\n','')
 s=s.replace('.AGE_LIMIT(CONTROL_HEIGHT_AGE_LIMIT),.POSE_AGE_LIMIT(CONTROL_POSE_AGE_LIMIT),','').replace('.AGE_LIMIT(CONTROL_HEIGHT_AGE_LIMIT),','')
 s=s.replace('.height_ready_state_numeric_tail(geometry_height_state_numeric_tail),','').replace('.estimate_ready_state_numeric_tail(height_estimate_state_numeric_tail),','')
 oldH=expression(o,'height_ready');newH=expression(s,'height_ready');s=s.replace(' // Expand original Q && E && G && module_fresh && live_acc; keep original G/E/FSM paths.\n','');s=s.replace(' assign height_ready='+newH+';',' assign height_ready='+oldH+';');assert s==o
 outputs=[]
 for label,src in [('old',olds),('new',news)]:
  g,f,nav=[src[n] for n in names];gp,gpins=instance(nav,'mtf_shared_geometry','geometry');fp,fpins=instance(nav,'mtf_shared_height_fusion','height_fusion')
  assert gp.get('HEIGHT_TILT_LIMIT_CDEG')=='4500' and fp['RANGE_AGE_PRECHECKED']=='1'
  # Exact existing numeric defaults and explicit new parameter binding.
  assert 'AGE_LIMIT=5000000,POSE_AGE_LIMIT=3000000' in g and 'AGE_LIMIT=5000000' in f
  if label=='new':
   assert gp['AGE_LIMIT']==fp['AGE_LIMIT']=='CONTROL_HEIGHT_AGE_LIMIT' and gp['POSE_AGE_LIMIT']=='CONTROL_POSE_AGE_LIMIT'
   assert 'CONTROL_POSE_AGE_LIMIT=3000000,CONTROL_HEIGHT_AGE_LIMIT=5000000;' in nav
  assert gpins['range_valid']=='range_valid' and gpins['pose_valid']=='pose_valid' and gpins['origin_reset']=='origin_reset'
  assert fpins['range_valid']=='geometry_height_ready&&module_fresh' and fpins['acc_valid']=='live_acc'
  assert fpins['acc_age_ticks']=='pose_age_ticks' and fpins['ref_height_mm']=='height_mm'
  source={'G':g,'F':f,'N':nav};aliases={'G':{},'F':{},'N':{}}
  for x in ['height_ready','sources_ok','pose_ok','range_ok']:aliases['G'][x]=('G',expression(g,x))
  for x in ['estimate_ready','sources_ok']:aliases['F'][x]=('F',expression(f,x))
  for x in ['module_fresh','live_acc']:aliases['N'][x]=('N',expression(nav,x))
  aliases['N']['geometry_height_ready']=('G',expression(g,'height_ready'));aliases['N']['height_estimate_ready']=('F',expression(f,'estimate_ready'));aliases['N']['height_qualified_ready']=('F','qualified_ready')
  for x in ['rst_n','origin_reset','range_valid','pose_valid','pose_age_ticks','distance_mm']:aliases['G'][x]=('N',gpins[x])
  for x in ['origin_reset','range_valid','acc_valid','range_age_ticks','acc_age_ticks','ref_height_mm','az_up_mmps2']:aliases['F'][x]=('N',fpins[x])
  if label=='new':
   for ctx,port,wire,callpins in [('G','height_ready_state_numeric_tail','geometry_height_state_numeric_tail',gpins),('F','estimate_ready_state_numeric_tail','height_estimate_state_numeric_tail',fpins)]:
    assert callpins[port]==wire;aliases[ctx][port]=(ctx,expression(source[ctx],port));kept=port+'_kept';aliases[ctx][kept]=(ctx,expression(source[ctx],kept));aliases['N'][wire]=(ctx,port)
  constants={'G':{'AGE_LIMIT':'5000000','POSE_AGE_LIMIT':'3000000'},'F':{'AGE_LIMIT':'5000000','RANGE_AGE_PRECHECKED':'1'},'N':{'CONTROL_POSE_AGE_LIMIT':'3000000','CONTROL_HEIGHT_AGE_LIMIT':'5000000'}}
  def atom(ctx,text):
   def token(m):
    x=m[0]
    if x in constants[ctx]:return constants[ctx][x]
    if x in aliases[ctx]:
     c,e=aliases[ctx][x]
     assert re.fullmatch(r'\w+',e),(ctx,x,e,'complex alias inside indivisible atom')
     return atom(c,e)
    return ctx+'.'+x
   return re.sub(r'\b[A-Za-z_]\w*\b',token,outer(text))
  def expand(ctx,text):
   terms=conjuncts(text)
   if len(terms)>1:
    result=set()
    for term in terms:result|=expand(ctx,term)
    return result
   term=outer(text)
   if term in aliases[ctx]:
    c,e=aliases[ctx][term];return expand(c,e)
   return {atom(ctx,term)}
  outputs.append(dict(label=label,atoms=sorted(expand('N',expression(nav,'height_ready'))),gp=gp,fp=fp,gpins=gpins,fpins=fpins))
 assert outputs[0]['atoms']==outputs[1]['atoms'],dict(only_old=set(outputs[0]['atoms'])-set(outputs[1]['atoms']),only_new=set(outputs[1]['atoms'])-set(outputs[0]['atoms']))
 assert all(sha(p)==h for p,h in frozen['bindings'].items())
 report=dict(status='PASS executed exact-source projection plus AND-atom normalization',bindings=frozen['bindings'],normalization=outputs,atom_count=len(outputs[0]['atoms']),limits=['Pure source Boolean algebra; no whole mapped or timing proof','OR age guard retained indivisible same-source atom; no numeric predicate dropped','Q qualified_ready remains arbitrary unchanged state atom','No fullFSM/core/host/parser matrix'],parent_tilt_proof_inheritance=frozen['parent_tilt_proof_inheritance'],functional_compile_run=False,synthesis_run=False,pnr_run=False)
 report['evidence_hashes']={p.name:sha(p) for p in [D/'prove_factoring.py',D/'prepared_inputs.json']};(D/'factoring_proof.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
if __name__=='__main__':main()
