"""Rerun only failed alias compile with writable local TMP; fixtures unchanged."""
from pathlib import Path
import hashlib,json,os,shutil,subprocess,sys
O=Path(__file__).resolve().parent;R=O.parents[3];A=O/'proofs_attempt01';D=O/'proofs_alias_retry02'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf8'))
write=lambda p,j:p.write_text(json.dumps(j,indent=2)+'\n',encoding='utf8')
f=read(O/'source_freeze.json');expected=f['source55'];S=Path(f['source_root'])
assert read(A/'functional_runner_exit.json')['actual_p_wait']==1 and read(A/'alias_compile_exit.json')['actual_p_wait']==1
failure=(A/'alias_compile.stderr.log').read_text();assert 'Error opening temporary file' in failure and 'Please check TMP or TMPDIR' in failure
assert not (A/'alias_vvp_exit.json').exists()
files=['actual_functions.v','alias_tb.v','STRUCTURAL_IDENTITY.json']
for n in files:assert not (D/n).exists();shutil.copy2(A/'alias'/n,D/n);assert (D/n).read_bytes()==(A/'alias'/n).read_bytes()
B=R.parents[1]/'.tools/iverilog/app/bin';IV=B/'iverilog.exe';VVP=B/'vvp.exe'
bound={str(p):sha(p) for p in [Path(__file__),O/'launch_alias_compile_retry02.py',O/'source_freeze.json',O/'prepare_alias.py',O/'prepare_alias_retry02.py',O/'prepare_alias_retry02_resolved.py',A/'functional_runner_exit.json',A/'alias_compile_exit.json',A/'alias_compile.stderr.log',IV,VVP,*[A/'alias'/n for n in files],*[D/n for n in files]]}
assert {n:sha(S/n) for n in expected}==expected
write(D/'inputs.json',{'source55':expected,'bound_inputs':bound,'only_correction':'Supply dedicated writable TMP/TEMP/TMPDIR to Icarus. Actual function, alias, signed64 reference, vectors and assertions copied byte-exact; original failed compile1/root1 preserved.'})
(D/'tmp').mkdir();env=dict(os.environ,TMP=str(D/'tmp'),TEMP=str(D/'tmp'),TMPDIR=str(D/'tmp'))
def run(name,cmd):
 with (D/f'{name}.stdout.log').open('wb') as out,(D/f'{name}.stderr.log').open('wb') as err:
  p=subprocess.Popen(cmd,stdout=out,stderr=err,stdin=subprocess.DEVNULL,env=env,creationflags=subprocess.CREATE_NO_WINDOW);code=p.wait(timeout=120)
 j={'command':cmd,'normal_wait_return':True,'actual_p_wait':code,'pid':p.pid,'TMP':str(D/'tmp'),'stdout_sha256':sha(D/f'{name}.stdout.log'),'stderr_sha256':sha(D/f'{name}.stderr.log')};write(D/f'{name}_exit.json',j)
 assert code==0,(name,code)
run('compile',[str(IV),'-g2012','-s','tb','-o',str(D/'alias.vvp'),str(D/'alias_tb.v'),str(D/'actual_functions.v')])
run('vvp',[str(VVP),str(D/'alias.vvp')])
line='PASS actual_alias vectors=53116 signed64=42768 fourstate=10348 all_upper13=8192 low16_reduction_classes=2 function_byte_identical=1'
assert line in (D/'vvp.stdout.log').read_text()
assert {p:sha(Path(p)) for p in bound}==bound and {n:sha(S/n) for n in expected}==expected
write(D/'RESULT.json',{'passed':True,'source55':expected,'inputs_sha256':sha(D/'inputs.json'),'pass_line':line,'source_function_and_fixture_byte_exact_to_failed_compile':True,'original_compile_actual_wait':1,'original_suite_actual_root_wait':1,'exit_receipts':{n:sha(D/n) for n in ['compile_exit.json','vvp_exit.json']},'artifacts':{n:sha(D/n) for n in ['compile.stdout.log','compile.stderr.log','vvp.stdout.log','vvp.stderr.log','alias.vvp','actual_functions.v','alias_tb.v','STRUCTURAL_IDENTITY.json']}})
print(line,flush=True)
