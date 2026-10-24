import re,json,pathlib,hashlib
root=pathlib.Path(__file__).resolve().parents[1]
paths=[root/'variants'/v/'fixture/impl/gwsynthesis/acg720_ano_port.vg' for v in ('p1_r1','p2_r2_rep1')]
texts=[p.read_text() for p in paths]
lex=re.compile(r'\\\S+|"(?:\\.|[^"\\])*"|[A-Za-z_$][A-Za-z0-9_$]*|\s+|.',re.S)
def toks(t):return [v for v in lex.findall(t) if not v.isspace()]
clean=[]
for t in texts:
 lines=t.splitlines()
 assert not any(re.match(r'\s*//\s*(synthesis|synopsys|pragma|translate)\b',l,re.I) for l in lines)
 clean.append('\n'.join(l for l in lines if not l.lstrip().startswith('//')))
mp=re.compile(r'\bmodule\s+(\w+)\b(.*?)\bendmodule\b',re.S)
mods=[{m.group(1):m.group(0) for m in mp.finditer(t)} for t in clean]
assert list(mods[0])==list(mods[1])
mapping={'pose_time_adapter':{'n3666_6':'n3640_6','n3666_s2':'n3640_s2'}}
ports=[]
for mm in mods:
 pd={}
 for name,body in mm.items():
  # Non-ANSI interface; original token comparison checks widths and order.
  pd[name]=set(re.findall(r'^\s*(?:input|output|inout)\s+(?:\[[^\]]+\]\s*)?(\\\S+|\w+)\s*;',body,re.M))
 ports.append(pd)
checks=[];fail=[];bindings=[]
for name,body in mods[0].items():
 other=mods[1][name];rename=mapping.get(name,{})
 assert len(set(rename.values()))==len(rename)
 aa=toks(body);bb=toks(other)
 assert len(aa)==len(bb)
 for old,new in rename.items():
  # Every renamed symbol must be a declared signal or explicit primitive instance.
  for text,sym in ((body,old),(other,new)):
   assert re.search(r'^\s*(?:wire|input|output|inout)\s+'+re.escape(sym)+r'\s*;',text,re.M) or re.search(r'^\s*LUT4\s+'+re.escape(sym)+r'\s*\(',text,re.M)
  assert new not in aa and old not in bb
 assert {rename.get(p,p) for p in ports[0][name]}==ports[1][name]
 if name=='acg720_ano_port':assert not(set(rename)&ports[0][name]) and ports[0][name]==ports[1][name]
 # Identify child-module instantiations by exact module type and balanced parentheses.
 pinmap={};child_spans=[]
 for i in range(len(aa)-2):
  if aa[i] in mods[0] and aa[i+2]=='(' and (i==0 or aa[i-1]!='module'):
   child=aa[i];depth=1;j=i+3
   while depth:
    if aa[j]=='(':depth+=1
    elif aa[j]==')':depth-=1
    j+=1
   child_spans.append((i,j,child,aa[i+1]))
   for k in range(i+3,j-2):
    if aa[k]=='.' and aa[k+2]=='(':
     assert aa[k+1] in ports[0][child]
     pinmap[k+1]=mapping.get(child,{}).get(aa[k+1],aa[k+1])
     if pinmap[k+1]!=aa[k+1]:bindings.append({'caller':name,'instance':aa[i+1],'child':child,'old_pin':aa[k+1],'new_pin':pinmap[k+1]})
 # Non-child dot labels are primitive pins or defparam member names: exact.
 normalized=[]
 for i,x in enumerate(aa):
  if i in pinmap:y=pinmap[i]
  elif i and aa[i-1]=='.':y=x
  else:y=rename.get(x,x)
  normalized.append(y)
 mismatches=[{'index':i,'original':aa[i],'expected':x,'actual':bb[i]} for i,x in enumerate(normalized) if x!=bb[i]]
 fail.extend({'module':name,**e} for e in mismatches)
 checks.append({'module':name,'token_count':len(aa),'renames':rename,'child_instances_checked':len(child_spans),'mismatch_count':len(mismatches)})
outside=[toks(mp.sub('',t)) for t in clean]
r={'passed':not fail and outside[0]==outside[1],'sha256':[hashlib.sha256(p.read_bytes()).hexdigest() for p in paths],'files':[str(p) for p in paths],'method':'Ordered per-module token comparison with explicit collision-free declared-symbol bijections; child named pins mapped only through their declared module interface; vendor/primitive pins unchanged. All other tokens exact, including port direction/width/order, literals, types, operators, strings, attributes and positional bindings. Top ports unchanged. Only full-line metadata comments excluded.','modules':checks,'renamed_child_bindings':bindings,'mismatches':fail,'outside_modules_identical':outside[0]==outside[1],'limits':'Structural emitted-netlist rename equivalence only; not RTL-to-synthesis equivalence, timing, routing or hardware validation.'}
p=root/'hardware/p2_rep1_hierarchical_rename_review.json';p.write_text(json.dumps(r,indent=2));print(json.dumps({'passed':r['passed'],'mismatches':fail[:8],'bindings':bindings,'output':str(p)}))



