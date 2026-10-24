from pathlib import Path
import os,subprocess,re,json,hashlib
ROOT=Path(__file__).resolve().parent
FIX=ROOT/'fixture';WS=next(p for p in ROOT.parents if (p/'.tools/iverilog/app/bin/iverilog.exe').is_file())
IV=WS/'.tools/iverilog/app/bin/iverilog.exe';VVP=IV.with_name('vvp.exe')
TMP=ROOT/'tmp';TMP.mkdir(exist_ok=True)
ENV=dict(os.environ,PATH=str(IV.parent)+os.pathsep+os.environ['PATH'],TMP=str(TMP),TMPDIR=str(TMP),TEMP=str(TMP))
def simulate(name,sources,bench=None,top='tb',run=True):
 proof_inputs=list(sources)+([bench] if bench else [])
 sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
 before={str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else str(p):sha(p) for p in proof_inputs}
 out=ROOT/'tests'/name
 cmd=[str(IV),'-g2012','-I',str(FIX),'-s',top,'-o',str(out.with_suffix('.vvp')),*map(str,sources)]
 if bench:cmd.append(str(bench))
 p=subprocess.run(cmd,capture_output=True,text=True,env=ENV,timeout=120)
 out.with_suffix('.compile.log').write_text(p.stdout+p.stderr)
 if p.returncode:raise RuntimeError(p.stdout+p.stderr)
 if run:
  p=subprocess.run([str(VVP),str(out.with_suffix('.vvp'))],capture_output=True,text=True,env=ENV,cwd=ROOT/'tests',timeout=300)
  out.with_suffix('.log').write_text(p.stdout+p.stderr)
  if p.returncode:raise RuntimeError(p.stdout+p.stderr)
  print(name,p.stdout.strip(),flush=True)
 after={str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else str(p):sha(p) for p in proof_inputs}
 if before!=after:raise RuntimeError('Proof source changed during test: '+name)
 result=dict(name=name,passed=True,source_sha256=before)
 out.with_suffix('.proof.json').write_text(json.dumps(result,indent=2))
 return result
def full_top():
 sources=[FIX/n for n in re.findall(r'<File path="([^"]+\.v)"',(FIX/'acg720_ano_port.gprj').read_text())]
 return simulate('top',sources,top='acg720_ano_port',run=False)
if __name__=='__main__':print(full_top())
