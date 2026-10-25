"""Isolate the checked-in numerical/top13/contention suites; no RTL edits."""
from pathlib import Path
import ast,datetime,difflib,hashlib,json,os,subprocess,sys
D=Path(__file__).resolve().parent;R=D.parents[3];C=R/'candidates/idle_gain_integral_ce';S=C/'source'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def source_tree(root):return {p.relative_to(root).as_posix():sha(p)for p in root.rglob('*')if p.is_file()and 'impl'not in p.parts and p.suffix not in('.log','.bak','.user')}
def all_files(root):return {p.relative_to(root).as_posix():sha(p)for p in root.rglob('*')if p.is_file()}
assert not(D/'regression_input.json').exists(),'One frozen regression run per directory'
source=source_tree(S);assert len(source)==55 and source['position/mtf_xyz_hold_control.v']=='b7eef6d33789523cd1e8ff81b05e75db91ab3c67bf76e03483dec356055fa1a6'
baseline=all_files(R/'test_baseline');originals={};suite_rows=[]
specs=[('numerical',R/'verify_control.py'),('top_safety',R/'verify_top_safety.py'),('contention',R/'review/verify_contention.py')]
original_control_init="R=Path(__file__).resolve().parent;O=R/'verification';T=O/'tmp';B=R.parent/'.tools/iverilog/app/bin'"
original_top_init="R=Path(__file__).resolve().parent;S=R/'source';O=R/'verification';T=O/'tmp';B=R.parent/'.tools/iverilog/app/bin'"
original_contention_init="R=Path(__file__).resolve().parents[1];O=Path(__file__).resolve().parent/'contention';O.mkdir(exist_ok=True)"
def unchanged_assertions(old,new):
 a,b=ast.parse(old),ast.parse(new)
 assert [ast.dump(x,include_attributes=False)for x in ast.walk(a)if isinstance(x,ast.Assert)]==[ast.dump(x,include_attributes=False)for x in ast.walk(b)if isinstance(x,ast.Assert)]
 assert [ast.dump(x,include_attributes=False)for x in a.body if isinstance(x,(ast.FunctionDef,ast.AsyncFunctionDef))]==[ast.dump(x,include_attributes=False)for x in b.body if isinstance(x,(ast.FunctionDef,ast.AsyncFunctionDef))]
 for name in ['tb','ports']:
  get=lambda tree:[ast.dump(x.value,include_attributes=False)for x in tree.body if isinstance(x,ast.Assign)and any(isinstance(t,ast.Name)and t.id==name for t in x.targets)]
  assert get(a)==get(b),name+' stimulus/assertion template changed'
for name,origin in specs:
 O=D/name;O.mkdir();(O/'tmp').mkdir();old=origin.read_text(encoding='utf8');adapted=old
 if name=='numerical':
  assert adapted.count(original_control_init)==1
  adapted=adapted.replace(original_control_init,f"R=Path({str(R)!r});S=Path({str(S)!r});O=Path({str(O)!r});T=O/'tmp';B=R.parent/'.tools/iverilog/app/bin'")
 elif name=='top_safety':
  assert adapted.count(original_top_init)==1
  adapted=adapted.replace(original_top_init,f"R=Path({str(R)!r});S=Path({str(S)!r});O=Path({str(O)!r});T=O/'tmp';B=R.parent/'.tools/iverilog/app/bin'")
  adapted="import sys\nsys.path.insert(0,"+repr(str(R))+')\n'+adapted
 else:
  assert adapted.count(original_contention_init)==1
  adapted=adapted.replace(original_contention_init,f"R=Path({str(R)!r});S=Path({str(S)!r});O=Path({str(O)!r});O.mkdir(exist_ok=True)")
 adapted=adapted.replace("R/'source/","S/'")
 unchanged_assertions(old,adapted)
 original_copy=O/'original_checked_in.py';original_copy.write_bytes(origin.read_bytes())
 adapter=O/'run_original_suite.py';adapter.write_text(adapted,encoding='utf8')
 (O/'path_adaptation.diff').write_text(''.join(difflib.unified_diff(old.splitlines(True),adapted.splitlines(True),fromfile=origin.relative_to(R).as_posix(),tofile=adapter.relative_to(R).as_posix())),encoding='utf8')
 originals[origin.relative_to(R).as_posix()]=sha(origin)
 suite_rows.append(dict(name=name,original=str(origin.relative_to(R)),original_sha256=sha(origin),adapter=str(adapter.relative_to(D)),adapter_sha256=sha(adapter),all_assertions_functions_tb_ports_AST_identical=True,outputs=str(O.relative_to(C))))
inputs=dict(started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope='Three original production-RTL suites; only source/output/import path adaptation; baseline fixed',candidate_source_sha256=source,test_baseline_sha256=baseline,original_script_sha256=originals,suites=suite_rows)
(D/'regression_input.json').write_text(json.dumps(inputs,indent=2))
env=dict(os.environ,PYTHONUTF8='1');jobs=[]
for row in suite_rows:
 O=D/row['name'];out=(O/'runner.stdout.log').open('w');err=(O/'runner.stderr.log').open('w')
 p=subprocess.Popen([sys.executable,'-B',str(D/row['adapter'])],cwd=R,stdin=subprocess.DEVNULL,stdout=out,stderr=err,close_fds=True,creationflags=0x08000000,env=env)
 jobs.append((row,p,out,err));(O/'process.json').write_text(json.dumps(dict(runner_pid=os.getpid(),suite_pid=p.pid,started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat()),indent=2))
print('START '+json.dumps([{k:v for k,v in row.items()if k in ['name','outputs']}|{'pid':p.pid}for row,p,_,_ in jobs]),flush=True)
codes={}
for row,p,out,err in jobs:
 code=p.wait();out.close();err.close();codes[row['name']]=code
 (D/row['name']/'process_exit.json').write_text(json.dumps(dict(exit_code=code,p_wait_return=code,finished_utc=datetime.datetime.now(datetime.timezone.utc).isoformat()),indent=2))
 assert source_tree(S)==source and all_files(R/'test_baseline')==baseline
assert all(code==0 for code in codes.values()),codes
results={name:json.loads((D/folder/file).read_text())for name,folder,file in [('numerical','numerical','control_results.json'),('top_safety','top_safety','top_safety_results.json'),('contention','contention','results.json')]}
assert all(x['passed']is True for x in results.values())and results['top_safety']['cases']==13
assert source_tree(S)==source and all_files(R/'test_baseline')==baseline and all(sha(R/n)==h for n,h in originals.items())
result=dict(passed=True,finished_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope='Unmodified assertion/stimulus original suites against frozen idle_gain_ce RTL; paths isolated; no SYN/PNR/hardware',candidate_source_sha256=source,test_baseline_unchanged=True,original_scripts_unchanged=True,original_assertions_and_TB_AST_unchanged=True,suite_exit_codes=codes,numerical_checks=results['numerical']['checks'],top_safety_cases=13,contention={k:v for k,v in results['contention'].items()if k not in ['source_sha256','evidence_sha256']},evidence_sha256={p.relative_to(D).as_posix():sha(p)for p in D.rglob('*')if p.is_file()and p.suffix not in('.vvp','.pyc')and 'tmp'not in p.parts and p.name not in('regression_results.json','runner.stdout.log','runner.stderr.log')})
(D/'regression_results.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2),flush=True)
