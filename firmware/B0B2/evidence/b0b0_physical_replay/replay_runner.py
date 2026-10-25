"""Single exact B0B0 PNR-only replay; no synthesis, acceptance or hardware API."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,os,re,subprocess,sys
HERE=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def write(name,value):
 with (HERE/name).open('x',encoding='utf-8',newline='\n') as f:json.dump(value,f,indent=2);f.write('\n')
def now():return datetime.now(timezone.utc).isoformat()
def verify(m):
 for name,digest in m['physical_inputs_sha256'].items():
  if sha(HERE/'fixture'/name)!=digest:raise ValueError('Replay input changed: '+name)
 for name,path in m['original_input_paths'].items():
  if sha(Path(path))!=m['physical_inputs_sha256'][name]:raise ValueError('Original selected input changed: '+name)
 if sha(Path(m['original_manifest_path']))!=m['original_manifest_sha256']:raise ValueError('Frozen original manifest changed')
 if sha(Path(m['gowin_executable']))!=m['gowin_executable_sha256']:raise ValueError('Gowin executable changed')
m=json.loads((HERE/'inputs.json').read_text(encoding='utf-8'));verify(m)
if (HERE/'process_start.json').exists() or (HERE/'console.log').exists():raise ValueError('Replay already started; never rerun')
command=[m['gowin_executable'],'pnr_only.tcl']
with (HERE/'console.log').open('xb') as log:
 p=subprocess.Popen(command,cwd=HERE/'fixture',stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
 write('process_start.json',dict(started_utc=now(),wrapper_pid=os.getpid(),gowin_pid=p.pid,command=command,cwd=str(HERE/'fixture'),hardware_accessed=False,one_round_only=True))
 print(json.dumps(dict(started=True,wrapper_pid=os.getpid(),gowin_pid=p.pid,log=str(HERE/'console.log'))),flush=True)
 code=p.wait()
write('vendor_exit_code.json',dict(returncode=code,finished_utc=now(),hardware_accessed=False))
verified=True;verification_error=None
try:verify(m)
except Exception as exc:verified=False;verification_error=repr(exc)
console=(HERE/'console.log').read_text(encoding='utf-8',errors='replace')
report=dict(schema='b0b0.physical-replay-completion.v1',finished_utc=now(),vendor_returncode=code,inputs_unchanged=verified,input_verification_error=verification_error,
 skip_synthesis_observed='Skip synthesis, because there is only one netlist file in this project' in console,
 unexpected_synthesis=bool(re.search(r'\bGowinSynthesis\b|\bCompiling module\b|Running netlist conversion',console)),
 placement_and_routing_completed='Placement and routing completed' in console,bitstream_generation_completed='Bitstream generation completed' in console,
 inputs_sha256=sha(HERE/'inputs.json'),runner_sha256=sha(Path(__file__)),console_sha256=sha(HERE/'console.log'),
 output_files_sha256={p.relative_to(HERE).as_posix():sha(p) for p in (HERE/'fixture/impl/pnr').glob('*') if p.is_file()},
 hardware_accessed=False,flash_changed=False,b0b2_acceptance_created=False,new_bitstream_hardware_qualified=False,flight_ready=False)
write('replay_complete.json',report)
print(json.dumps({k:v for k,v in report.items() if k!='output_files_sha256'}),flush=True)
sys.exit(code if verified else 1)
