from pathlib import Path
import hashlib,json,subprocess,sys,re,os,concurrent.futures
ROOT=Path(__file__).resolve().parent;FIX=ROOT/'fixture'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def inputs():
 names=re.findall(r'<File path="([^"]+)"',(FIX/'acg720_ano_port.gprj').read_text())+['acg720_ano_port.gprj','build.tcl']
 return {n:sha(FIX/n)for n in names}
def run(name):
 p=subprocess.run([sys.executable,str(ROOT/name)],cwd=ROOT,capture_output=True,text=True,encoding='utf8',errors='replace',timeout=600)
 (ROOT/'tests'/(name+'.run.log')).write_text(p.stdout+p.stderr,encoding='utf8')
 if p.returncode:raise RuntimeError(name+'\n'+p.stdout+p.stderr)
 print(name+' PASS',flush=True)
def main():
 before=inputs()
 from control_contract import verify
 verify();run('build_reference.py')
 # These callbacks write separate fixtures/reports. Height test creates the
 # coherent base fixture used by the XY/race benches, so run it first.
 run('test_height_reference.py')
 jobs=['test_state_reference.py','test_sticks_reference.py','test_xy_reference.py','test_core.py','test_bounds_races.py','test_wire.py','test_geometry.py','test_navigation.py','test_divide36.py','test_manual_reference.py','test_manual_handoff.py']
 with concurrent.futures.ThreadPoolExecutor(max_workers=2)as pool:list(pool.map(run,jobs))
 run('test_tools.py')
 run('test_storage_equivalence.py')
 run('test_operand_equivalence.py')
 run('test_mask_retiming.py')
 p=subprocess.run([sys.executable,'-m','unittest','discover','-s',str(ROOT/'ground'),'-p','test_*.py'],capture_output=True,text=True,encoding='utf8',timeout=120)
 (ROOT/'tests/host_tests.log').write_text(p.stdout+p.stderr)
 if p.returncode:raise RuntimeError(p.stdout+p.stderr)
 for name in ['dashboard.js','mtf-ui.js']:
  subprocess.run(['C:/Program Files/nodejs/node.exe','--check',str(ROOT/'ground'/name)],check=True,timeout=30)
 assert inputs()==before,'source changed during qualification';verify()
 evidence={}
 for proof in (ROOT/'tests').glob('*.proof.json'):
  q=json.loads(proof.read_text());assert q['passed']
  for n,h in q['source_sha256'].items():
   path=ROOT/n
   assert sha(path)==h,('stale proof',proof,n)
 for name in ['state_reference.json','sticks_reference.json','height_reference.json','xy_reference.json','manual_reference.json']:
  assert json.loads((ROOT/'tests'/name).read_text())['passed']
 files=[p for p in (ROOT/'tests').iterdir()if p.is_file()and p.suffix in ('.json','.log','.hex','.txt','.cpp','.v','.exe')]
 files += [ROOT/'control_contract.py',ROOT/'CONTROL_CONTRACT.txt',ROOT/'baseline.json',ROOT/'build_reference.py',ROOT/'qualify.py']
 files += [ROOT/'test_mask_retiming.py',ROOT/'test_operand_equivalence.py',ROOT/'test_storage_equivalence.py',ROOT/'test_tools.py',ROOT/'test_wire.py',ROOT/'test_core.py']
 files += [p for p in (ROOT/'reference').rglob('*')if p.is_file()]
 files += [p for p in (ROOT/'ground').iterdir()if p.is_file()]
 evidence={str(p.relative_to(ROOT)).replace('\\','/'):sha(p)for p in files}
 q=dict(offline_tests_passed=True,sources_sha256=before,evidence_sha256=evidence,
  programming_authorized=False,hardware_accessed=False,flight_ready=False,
  reference='Original ANO C functions; hardware/safety adapters in CONTROL_CONTRACT.txt')
 (ROOT/'qualification.json').write_text(json.dumps(q,indent=2))
 print('SOURCE_BOUND_OFFLINE_QUALIFICATION_PASS',flush=True)
if __name__=='__main__':main()
