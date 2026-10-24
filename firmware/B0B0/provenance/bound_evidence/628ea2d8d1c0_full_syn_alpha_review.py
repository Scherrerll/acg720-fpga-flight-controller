"""Diagnostic only: exact token alignment under bijective module-local internal alpha renaming.
Never used to relax the release canonical-identity gate.
"""
from pathlib import Path
import re,json,hashlib
ROOT=Path(__file__).resolve().parents[1]
LEX=re.compile(r'\\\S+|"(?:\\.|[^"\\])*"|[A-Za-z_$][A-Za-z0-9_$]*|\s+|.',re.S)
ID=re.compile(r'(?:\\\S+|[A-Za-z_$][A-Za-z0-9_$]*)\Z')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def tokens(p):
 s=p.read_text();s=re.sub(r'/\*.*?\*/|//[^\n]*','',s,flags=re.S)
 return [x for x in LEX.findall(s)if not x.isspace()]
def modules(t):
 out=[];i=0
 while i<len(t):
  if t[i]!='module':i+=1;continue
  start=i;name=t[i+1];header=t.index(';',i);end=t.index('endmodule',header)
  ports=set();wires=set();instances=set();types=set();j=header+1
  while j<end:
   if t[j] in ('input','output','inout','wire'):
    kind=t[j];k=t.index(';',j);names=[];depth=0
    for v in t[j+1:k]:
     if v=='[':depth+=1
     elif v==']':depth-=1
     elif depth==0 and ID.fullmatch(v) and v not in ('wire','reg','signed','unsigned'):names.append(v)
    assert names,('Empty declaration',name,j)
    (wires if kind=='wire' else ports).update(names);j=k+1
   else:j+=1
  # All supported instances are scalar named calls; cell type token is protected.
  for j in range(header+1,end-2):
   if ID.fullmatch(t[j]) and ID.fullmatch(t[j+1]) and t[j+2]=='(' and t[j]not in ('module','function','task'):
    instances.add(t[j+1]);types.add(j)
  assert not instances & (wires|ports),('Namespace collision',name)
  out.append(dict(name=name,start=start,header=header,end=end,ports=ports,wires=wires-ports,instances=instances,types=types))
  i=end+1
 return out

def restricted_review():
 a=ROOT/'synthesis/20261023T175739_346753Z/impl/gwsynthesis/acg720_ano_port.vg';b=ROOT/'fixture/impl/gwsynthesis/acg720_ano_port.vg'
 ta,tb=tokens(a),tokens(b);report=dict(passed=False,purpose='Diagnosis only; final release still requires freshly reviewed actual full SYN and exact canonical identity',preliminary_netlist=str(a),actual_full_netlist=str(b),preliminary_sha256=sha(a),actual_sha256=sha(b),preliminary_tokens=len(ta),actual_tokens=len(tb),script_sha256=sha(Path(__file__)),hardware_accessed=False)
 try:
  assert len(ta)==len(tb),'Token count differs'
  ma,mb=modules(ta),modules(tb);assert len(ma)==len(mb),'Module count differs'
  report['module_port_name_differences']=[dict(module=x['name'],preliminary_only=sorted(x['ports']-y['ports']),actual_only=sorted(y['ports']-x['ports']))for x,y in zip(ma,mb)if x['ports']!=y['ports']]
  differing=[i for i,(u,v)in enumerate(zip(ta,tb))if u!=v]
  report['different_token_positions']=len(differing)
  report['first_raw_token_difference']=dict(token_index=differing[0],preliminary=ta[differing[0]],actual=tb[differing[0]])if differing else None

  changes=[];mapcount=0;module_reports=[];cursor=0
  for x,y in zip(ma,mb):
   assert x['name']==y['name'] and x['start']==y['start'] and x['header']==y['header'] and x['end']==y['end'],'Module structure differs'
   if ta[cursor:x['header']+1]!=tb[cursor:y['header']+1]:
    i=next(i for i in range(cursor,x['header']+1)if ta[i]!=tb[i])
    report['protected_header_difference']=dict(module=x['name'],token_index=i,preliminary=ta[i],actual=tb[i],preliminary_context=ta[max(cursor,i-8):i+9],actual_context=tb[max(cursor,i-8):i+9],preliminary_only_ports=sorted(x['ports']-y['ports']),actual_only_ports=sorted(y['ports']-x['ports']))
    raise AssertionError(('Module name/header/ports differ',x['name'],i,ta[i],tb[i]))
   assert x['ports']==y['ports'],('Module port declarations differ',x['name'])
   forward={};reverse={};local_changes=[]
   for i in range(x['header']+1,x['end']+1):
    u,v=ta[i],tb[i]
    # Dot-following tokens are named cell pins or defparam keys, never renameable.
    protected=ta[i-1]=='.' or tb[i-1]=='.' or i in x['types'] or i in y['types']
    kx='wire'if u in x['wires'] else 'instance'if u in x['instances'] else None
    ky='wire'if v in y['wires'] else 'instance'if v in y['instances'] else None
    if not protected and kx and ky and kx==ky:
     key=(kx,u);value=(ky,v)
     assert key not in forward or forward[key]==value,('Inconsistent rename',x['name'],i,u,v)
     assert value not in reverse or reverse[value]==key,('Nonbijective rename',x['name'],i,u,v)
     forward[key]=value;reverse[value]=key
     if u!=v and (kx,u,v) not in local_changes:local_changes.append((kx,u,v))
    else:assert u==v,('Non-alpha token difference',x['name'],i,u,v,ta[max(0,i-8):i+9],tb[max(0,i-8):i+9])
   expected_a={('wire',n)for n in x['wires']}|{('instance',n)for n in x['instances']}
   expected_b={('wire',n)for n in y['wires']}|{('instance',n)for n in y['instances']}
   assert set(forward)==expected_a and set(reverse)==expected_b,('Incomplete declaration bijection',x['name'])
   mapcount+=len(forward);changes.extend(dict(module=x['name'],kind=k,preliminary=u,actual=v)for k,u,v in local_changes)
   module_reports.append(dict(module=x['name'],internal_wires=len(x['wires']),instances=len(x['instances']),renamed_identifiers=len(local_changes),ports_preserved=len(x['ports'])))
   cursor=x['end']+1
  assert ta[cursor:]==tb[cursor:],'Trailing tokens differ'
  report.update(passed=True,result='Exact whole-netlist token sequence equality modulo bijective declared module-local internal wire/instance renaming',modules=module_reports,declared_identifier_pairs=mapcount,renamed_identifier_count=len(changes),renames=changes,preserved=['Module names and complete headers/ports','All cell types and named pins','Every width, constant, INIT and defparam value','Every assignment and connection topology, order and punctuation','All tokens except supported declared internal identifiers; comments/whitespace excluded'])
 except (AssertionError,ValueError)as e:report.update(result='Requested whole-netlist alpha proof not established',actual_difference=str(e))
 report['limitations']=['This is exact structural alpha comparison, not an independent vendor-primitive semantic model or RTL-to-netlist equivalence proof.','Comments and whitespace are excluded; source path/timestamp comments may differ.','No routing, timing, bitstream, physical hardware or power-loss conclusion follows.','Failure means this restricted proof did not establish equality; it does not establish a hardware defect.','Release gates remain unchanged and require actual-full-synthesis mapped/freshness audits.']
 return report

def hierarchical_review():
 a=ROOT/'synthesis/20261023T175739_346753Z/impl/gwsynthesis/acg720_ano_port.vg';b=ROOT/'fixture/impl/gwsynthesis/acg720_ano_port.vg'
 ta,tb=tokens(a),tokens(b);out=dict(passed=False,scope='Whole VG exact aligned-token comparison under bijective module-local wire/instance and consistently bound user-module port renaming; top external ports and vendor pins protected')
 try:
  assert len(ta)==len(tb),'Token count differs'
  ma,mb=modules(ta),modules(tb);assert len(ma)==len(mb),'Module count differs'
  pairs={};portmaps={};reverseports={};summaries=[];renames=[]
  for x,y in zip(ma,mb):
   assert x['name']==y['name'] and x['start']==y['start'] and x['header']==y['header'] and x['end']==y['end'],'Module layout differs'
   name=x['name'];pairs[name]=(x,y);f={};r={}
   # Header token positions define the bijection; every non-port header token stays exact.
   for i in range(x['start'],x['header']+1):
    u,v=ta[i],tb[i]
    if u in x['ports'] and v in y['ports']:
     assert u not in f or f[u]==v,('Header mapping inconsistent',name,u,v)
     assert v not in r or r[v]==u,('Header mapping nonbijective',name,u,v)
     f[u]=v;r[v]=u
    else:assert u==v,('Non-port header token differs',name,i,u,v)
   assert set(f)==x['ports'] and set(r)==y['ports'],('Unsupported header/port declaration',name)
   if name=='acg720_ano_port':assert len(f)==17 and all(k==v for k,v in f.items()),'External17port names differ'
   portmaps[name]=f;reverseports[name]=r
  assert 'acg720_ano_port' in pairs,'Missing protected top'
  def namedpins(t,x):
   bindings={};instance_callees={}
   for j in sorted(x['types']):
    callee=t[j];inst=t[j+1];assert inst not in instance_callees,('Duplicate instance',x['name'],inst)
    instance_callees[inst]=callee;depth=1;k=j+3
    while k<x['end'] and depth:
     if t[k]=='(':depth+=1
     elif t[k]==')':depth-=1
     elif depth==1 and t[k]=='.':
      assert ID.fullmatch(t[k+1]) and t[k+2]=='(',('Unsupported named binding',x['name'],k)
      bindings[k+1]=callee
     k+=1
    assert depth==0,('Unclosed instance',x['name'],inst)
   return bindings,instance_callees
  cursor=0
  for name,(x,y)in pairs.items():
   assert ta[cursor:x['start']]==tb[cursor:y['start']],'Intermodule tokens differ'
   pa,ia=namedpins(ta,x);pb,ib=namedpins(tb,y);assert set(pa)==set(pb),'Named binding positions differ'
   forward={('port',u):('port',v)for u,v in portmaps[name].items()};reverse={v:k for k,v in forward.items()};local=[]
   for i in range(x['start'],x['end']+1):
    u,v=ta[i],tb[i]
    if i in pa:
     assert pa[i]==pb[i],('Callee type differs',name,i)
     callee=pa[i]
     if callee in portmaps:
      assert portmaps[callee].get(u)==v,('User-module named binding inconsistent',name,callee,i,u,v)
     else:assert u==v,('Vendor pin differs',name,callee,i,u,v)
     continue
    protected=(i>0 and (ta[i-1]=='.' or tb[i-1]=='.')) or i in x['types'] or i in y['types'] or i==x['start']+1
    def kind(t,m):
     return 'port'if t in m['ports'] else 'wire'if t in m['wires'] else 'instance'if t in m['instances'] else None
    ka,kb=kind(u,x),kind(v,y)
    if not protected and ka and ka==kb:
     key=(ka,u);value=(kb,v)
     assert key not in forward or forward[key]==value,('Inconsistent local rename',name,i,u,v)
     assert value not in reverse or reverse[value]==key,('Nonbijective local rename',name,i,u,v)
     forward[key]=value;reverse[value]=key
     if u!=v and (ka,u,v)not in local:local.append((ka,u,v))
    else:assert u==v,('Non-alpha token differs',name,i,u,v,ta[max(0,i-5):i+6],tb[max(0,i-5):i+6])
   expected_a={('port',n)for n in x['ports']}|{('wire',n)for n in x['wires']}|{('instance',n)for n in x['instances']}
   expected_b={('port',n)for n in y['ports']}|{('wire',n)for n in y['wires']}|{('instance',n)for n in y['instances']}
   assert set(forward)==expected_a and set(reverse)==expected_b,('Incomplete local bijection',name)
   # Named calls must retain exact callee type for every renamed instance.
   for inst,callee in ia.items():assert ib[forward[('instance',inst)][1]]==callee,('Instance callee changed',name,inst)
   summaries.append(dict(module=name,ports=len(x['ports']),wires=len(x['wires']),instances=len(x['instances']),named_bindings=len(pa),renamed_identifiers=len(local)))
   renames.extend(dict(module=name,kind=k,preliminary=u,actual=v)for k,u,v in local)
   cursor=x['end']+1
  assert ta[cursor:]==tb[cursor:],'Trailing tokens differ'
  out.update(passed=True,result='Exact whole-VG structural equality modulo explicit bijective hierarchical alpha renaming',modules=summaries,renamed_identifier_count=len(renames),renames=renames,top_external_ports_preserved=17,preserved=['Module names, header order, port kinds and widths','Every cell type, vendor primitive pin, constant, INIT and defparam value','Every named user-module call binding under the callee-specific port bijection','All declaration/assignment/connection token topology and order','Top acg720_ano_port17external port names exactly'])
 except (AssertionError,ValueError,KeyError)as e:out.update(result='Hierarchical alpha proof not established',actual_difference=str(e))
 return out


def negative_checks():
 global tokens
 original=tokens
 A=ROOT/'synthesis/20261023T175739_346753Z/impl/gwsynthesis/acg720_ano_port.vg';B=ROOT/'fixture/impl/gwsynthesis/acg720_ano_port.vg'
 a,b=original(A),original(B);mods=modules(b)
 idx_init=next(i+2 for i,t in enumerate(b[:-2])if t=='INIT' and b[i+1]=='=')
 idx_pin=next(i+1 for i in range(len(b)-3)if b[i]=='.' and b[i+1]=='I0' and b[i+2]=='(')
 top=next(x for x in mods if x['name']=='acg720_ano_port');idx_top=next(i for i in range(top['start']+2,top['header'])if b[i]in top['ports'])
 checks={}
 try:
  for name,index in [('INIT_literal',idx_init),('vendor_pin',idx_pin),('external_top_port',idx_top)]:
   changed=b.copy();changed[index]='999'if name=='INIT_literal' else b[index]+'_CORRUPTED'
   tokens=lambda path,changed=changed:a if path==A else changed
   r=hierarchical_review();assert r['passed']is False,(name,r)
   checks[name]=dict(rejected=True,reason=r['actual_difference'])
 finally:tokens=original
 return checks

if __name__=='__main__':
 restricted=restricted_review();hierarchical=hierarchical_review()
 result=dict(passed=hierarchical['passed'],purpose='Diagnostic only; no release gate or canonical comparator changed',preliminary_sha256=restricted['preliminary_sha256'],actual_sha256=restricted['actual_sha256'],script_sha256=sha(Path(__file__)),restricted_local=restricted,hierarchical_alpha=hierarchical,limitations=restricted['limitations'],hardware_accessed=False)
 import sys
 if '--negative-checks' in sys.argv:result['in_memory_negative_checks']=negative_checks()
 (ROOT/'hardware/full_syn_alpha_review.json').write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps(dict(passed=result['passed'],restricted_local_passed=restricted['passed'],hierarchical_result=hierarchical['result'],actual_difference=hierarchical.get('actual_difference'),renamed_identifier_count=hierarchical.get('renamed_identifier_count')),indent=2))
