"""One normal EOF/DEVNULL/NO_WINDOW synthesis after all isolated proofs pass."""
from pathlib import Path
import datetime,hashlib,json,os,subprocess,sys
C=Path(__file__).resolve().parent;S=C/'source';O=C/'verification';R=C.parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
record=json.loads((C/'change.json').read_text());baseline=Path(record['baseline'])
def check_sources():
 for rel,digest in record['baseline_source_sha256'].items():assert sha(baseline/rel)==digest,rel
 for rel,digest in record['candidate_source_sha256'].items():assert sha(S/rel)==digest,rel
 assert len(record['candidate_source_sha256'])==55 and len(record['changed_files'])==1
check_sources()
prerequisites=[O/'cycle_pair/results.json',O/'regressions/results.json']
for p in prerequisites:assert json.loads(p.read_text())['passed'],p
assert not (O/'synthesis_input.json').exists(),'Only one synthesis invocation authorized'
tcl=(S/'build.tcl').read_bytes();assert tcl.count(b'run all')==1
tcl=tcl.replace(b'run all',b'run syn');assert b'run pnr'not in tcl and b'run all'not in tcl
(C/'synth_only.tcl').write_bytes(tcl)
tool=Path('C:/Gowin/Gowin_V1.9.12.04_x64/IDE/bin/gw_sh.exe')
inputs=dict(started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),source_sha256=record['candidate_source_sha256'],baseline_source_sha256=record['baseline_source_sha256'],tool=str(tool),tool_sha256=sha(tool),tcl_sha256=sha(C/'synth_only.tcl'),prerequisites_sha256={str(p):sha(p)for p in prerequisites},mode='exactly one run syn; ordinary EOF script; stdin DEVNULL; CREATE_NO_WINDOW; actual child wait exit code recorded; no PNR')
(O/'synthesis_input.json').write_text(json.dumps(inputs,indent=2))
with (O/'synthesis.log').open('w')as log:
 proc=subprocess.Popen([str(tool),str(C/'synth_only.tcl')],cwd=S,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
 (O/'synthesis_process.json').write_text(json.dumps(dict(runner_pid=os.getpid(),gowin_pid=proc.pid),indent=2))
 print(f'Gowin synthesis child PID{proc.pid}; normal EOF/DEVNULL/NO_WINDOW',flush=True)
 code=proc.wait()
(O/'synthesis_exit.json').write_text(json.dumps(dict(exit_code=code,actual_p_wait=code,finished_utc=datetime.datetime.now(datetime.timezone.utc).isoformat()),indent=2))
print(f'Actual p.wait()={code}',flush=True);assert code==0,code
check_sources()
assert (S/'impl/gwsynthesis/acg720_ano_port.vg').exists()
assert (S/'impl/gwsynthesis/acg720_ano_port_syn_rsc.xml').exists()
subprocess.run([sys.executable,'-B',str(C/'audit_synthesis.py')],check=True,stdin=subprocess.DEVNULL,creationflags=subprocess.CREATE_NO_WINDOW)
