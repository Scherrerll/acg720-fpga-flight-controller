import re,json,hashlib,pathlib
root=pathlib.Path(__file__).resolve().parents[1]
paths=[root/'variants'/v/'fixture/impl/gwsynthesis/acg720_ano_port.vg' for v in ('p1_r1','p3_r1')]
texts=[p.read_text() for p in paths]
report={'files':[str(p) for p in paths],'sha256':[hashlib.sha256(p.read_bytes()).hexdigest() for p in paths],'method':'Ordered lexical comparison per module, with a consistent bijection restricted to explicitly declared generated internal wire identifiers. All other tokens, including instance names, ports, literals, primitive types, directives and punctuation must match exactly. Full-line metadata comments only are excluded.'}
clean=[]
for t in texts:
 lines=t.splitlines()
 assert not any(re.search(r'^\s*//\s*(synthesis|synopsys|pragma|translate)\b',l,re.I) for l in lines if l.lstrip().startswith('//') and not l.startswith('//Written by GowinSynthesis'))
 clean.append('\n'.join(l for l in lines if not l.lstrip().startswith('//')))
pat=r'\bmodule\s+(\\\S+|\w+)\b(.*?)\bendmodule\b'
mods=[list(re.finditer(pat,t,re.S)) for t in clean]
assert len(mods[0])==len(mods[1])
token=re.compile(r'\\\S+|[A-Za-z_$][A-Za-z0-9_$]*|\s+|.',re.S)
def tokens(s):return [x for x in token.findall(s) if not x.isspace()]
reviews=[]
for a,b in zip(*mods):
 assert a.group(1)==b.group(1)
 wires=[]
 for m in (a,b):
  # Deliberately only accept plain scalar wire declarations, never ports/buses.
  wires.append(set(re.findall(r'^wire\s+(n\d+(?:_\d+)+);\s*$',m.group(2),re.M)))
 aa,bb=tokens(a.group(0)),tokens(b.group(0));forward={};reverse={};errors=[];changes=0
 if len(aa)!=len(bb):errors.append({'token_lengths':[len(aa),len(bb)]})
 for i,(x,y) in enumerate(zip(aa,bb)):
  if x in wires[0] and y in wires[1]:
   if forward.get(x,y)!=y or reverse.get(y,x)!=x:errors.append({'index':i,'reason':'nonbijective','a':x,'b':y})
   forward[x]=y;reverse[y]=x
   if x!=y:changes+=1
  elif x!=y:errors.append({'index':i,'a':x,'b':y,'context_a':aa[max(0,i-8):i+9],'context_b':bb[max(0,i-8):i+9]})
 reviews.append({'module':a.group(1),'tokens':[len(aa),len(bb)],'changed_occurrences':changes,'renames':{k:v for k,v in forward.items() if k!=v},'mismatches':errors})
# Ensure no non-module token content is silently ignored.
outside=[tokens(re.sub(pat,'',t,flags=re.S)) for t in clean]
report.update(modules=reviews,outside_modules_identical=outside[0]==outside[1],passed=outside[0]==outside[1] and not any(r['mismatches'] for r in reviews))
report['limitation']='This proves the emitted Verilog token/connectivity description differs only by permitted internal wire renames if passed; it does not prove RTL-to-netlist correctness or physical implementation/timing.'
out=root/'hardware/p3_r1_netlist_delta_review.json';out.write_text(json.dumps(report,indent=2))
print(json.dumps({'passed':report['passed'],'modules':len(reviews),'renames':sum(len(r['renames']) for r in reviews),'mismatches':sum(len(r['mismatches']) for r in reviews),'output':str(out)}))

