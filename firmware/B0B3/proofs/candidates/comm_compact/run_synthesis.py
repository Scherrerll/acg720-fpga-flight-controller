"""Synthesis-only fallback characterization. Never runs PNR or hardware."""
from pathlib import Path
import datetime,hashlib,json,os,re,subprocess,sys,xml.etree.ElementTree as ET
C=Path(__file__).resolve().parent;R=C.parents[1];S=C/'source';O=C/'verification';T=O/'tmp'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def tree(root):return {p.relative_to(root).as_posix():sha(p)for p in root.rglob('*')if p.is_file() and 'impl'not in p.parts and p.suffix not in ('.log','.bak','.user')}
record=json.loads((C/'change.json').read_text());assert tree(R/'source')==record['canonical_source_sha256'];assert tree(S)==record['candidate_source_sha256']
for name in ['link_results.json','contract_results.json']:assert json.loads((O/name).read_text())['passed']
tcl=(S/'build.tcl').read_text();assert tcl.count('run all')==1
tcl=tcl.replace('run all','run syn');assert 'run pnr'not in tcl and 'run all'not in tcl
(C/'synth_only.tcl').write_text(tcl)
inputs=dict(started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),source_sha256=tree(S),canonical_source_sha256=tree(R/'source'),gowin_sha256=sha(Path('C:/Gowin/Gowin_V1.9.12.04_x64/IDE/bin/gw_sh.exe')),mode='run syn only; PNR prohibited')
(O/'synthesis_input.json').write_text(json.dumps(inputs,indent=2))
with (O/'synthesis.log').open('w')as log:
 proc=subprocess.Popen(['C:/Gowin/Gowin_V1.9.12.04_x64/IDE/bin/gw_sh.exe',str(C/'synth_only.tcl')],cwd=S,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
 (O/'synthesis_process.json').write_text(json.dumps(dict(runner_pid=os.getpid(),gowin_pid=proc.pid),indent=2));code=proc.wait()
(O/'synthesis_exit.json').write_text(json.dumps(dict(exit_code=code,finished_utc=datetime.datetime.now(datetime.timezone.utc).isoformat()),indent=2));assert code==0,code
N=S/'impl/gwsynthesis/acg720_ano_port.vg';X=S/'impl/gwsynthesis/acg720_ano_port_syn_rsc.xml';assert N.exists()and X.exists()
base=R/'builds/release_width36/source'
semantic=[p.relative_to(S).as_posix()for p in S.rglob('*')if p.suffix in ('.v','.vh') and 'impl'not in p.parts and p.is_file()and sha(p)!=sha(base/p.relative_to(S))]
assert semantic==['telemetry_tx.v'],semantic
def resources(path):
 node=ET.parse(path).getroot()
 def data(n):return {k:int(re.match(r'\d+',v)[0])for k,v in n.attrib.items()if k.startswith('T_')}
 return dict(top=data(node),telemetry=data(next(n for n in node if n.attrib['name']=='telemetry')))
old=resources(base/'impl/gwsynthesis/acg720_ano_port_syn_rsc.xml');new=resources(X)
delta={part:{k:new[part].get(k,0)-old[part].get(k,0)for k in old[part].keys()|new[part].keys()}for part in old}
assert tree(S)==inputs['source_sha256'];assert tree(R/'source')==inputs['canonical_source_sha256']
out=dict(passed=True,mode='synthesis only',selected_for_canonical=False,canonical_unchanged=True,candidate_netlist_sha256=sha(N),candidate_resources_xml_sha256=sha(X),reference_netlist_sha256=sha(base/'impl/gwsynthesis/acg720_ano_port.vg'),reference_resources_xml_sha256=sha(base/'impl/gwsynthesis/acg720_ano_port_syn_rsc.xml'),reference=old,candidate=new,delta=delta,CLS='Not reported by synthesis; cannot claim actual packed CLS reduction without PNR',timing_closed=False,PNR_started=False)
(O/'synthesis_comparison.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2),flush=True)
