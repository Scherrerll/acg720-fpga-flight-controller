import re,json,pathlib,hashlib
root=pathlib.Path(__file__).resolve().parents[1]
paths=[root/'variants'/v/'fixture/impl/gwsynthesis/acg720_ano_port.vg' for v in ('p1_r1','p3_r2_rep1')]
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
for name,body in mods[0].items():
 a=toks(body);b=toks(mods[1][name]);print(name,len(a),len(b),sorted(set((x,y) for x,y in zip(a,b) if x!=y))[:30]) if a!=b else None
