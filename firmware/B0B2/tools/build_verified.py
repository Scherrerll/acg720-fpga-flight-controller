"""Reproduce qualified PNR from its immutable, source-bound synthesized netlist."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,hashlib,importlib.util,json,os,re,shutil,subprocess,time,uuid
FW=Path(__file__).resolve().parents[1];B=FW/'verified_timing_20261025';TOP='acg720_ano_port'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
manifest=lambda p:{f.relative_to(p).as_posix():sha(f)for f in p.rglob('*')if f.is_file()}
ap=argparse.ArgumentParser(description=__doc__)
mode=ap.add_mutually_exclusive_group();mode.add_argument('--prepare-only',action='store_true');mode.add_argument('--run',action='store_true')
ap.add_argument('--output',type=Path);ap.add_argument('--gowin',type=Path,default=Path('C:/Gowin/Gowin_V1.9.12.04_x64/IDE/bin/gw_sh.exe'))
a=ap.parse_args();m=json.loads((B/'manifest.json').read_text())
assert m['status']=='qualified_offline'and m['constraint_period_ns']==19.5
assert manifest(B/'source')==m['source_sha256']
assert manifest(FW/'source')==m['source_sha256'],'RTL changed; this pinned netlist cannot qualify edited source'
for folder,key in [('project','project_sha256'),('reports','report_sha256'),('bitstream','bitstream_sha256')]:
 for name,h in m[key].items():assert sha(B/folder/name)==h,name
assert sha(B/'full_sta.py')==m['full_sta_sha256']
print('PASS source, synthesized netlist,17-pin constraints, bitstream and report hashes',flush=True)
if not(a.prepare_only or a.run):raise SystemExit(0)
out=a.output.resolve()if a.output else FW/'builds'/('verified_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'_'+uuid.uuid4().hex[:8])
assert not out.exists(),'Choose a new output directory; existing data is never overwritten'
out.mkdir(parents=True)
for name,h in m['project_sha256'].items():
 target=out/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(B/'project'/name,target);assert sha(target)==h
(out/'reproduction_contract.json').write_text(json.dumps(dict(manifest_sha256=sha(B/'manifest.json'),source_sha256=m['source_sha256'],project_sha256=m['project_sha256'],hardware_accessed=False),indent=2)+'\n')
print(str(out),flush=True)
if a.prepare_only:raise SystemExit(0)
assert a.gowin.is_file(),a.gowin
started=time.time()
with(out/'console.txt').open('w')as log:
 r=subprocess.run([str(a.gowin),'build.tcl'],cwd=out,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt'else 0)
result=dict(physical_passed=False,vendor_returncode=r.returncode,hardware_accessed=False,flight_ready=False)
try:
 spec=importlib.util.spec_from_file_location('qualified_full_sta',B/'full_sta.py');sta_module=importlib.util.module_from_spec(spec);spec.loader.exec_module(sta_module)
 sta=sta_module.audit(out);pnr=out/'impl/pnr';report=(pnr/(TOP+'.rpt.txt')).read_text(errors='replace')
 pins=dict(re.findall(r'^(\w+)\s+\|\s*-\s*\|\s*(\w+)/\d+\s*\|',report,re.M))
 with(pnr/(TOP+'.fs')).open()as stream:head=''.join(next(stream,'')for _ in range(16))
 identity=all(re.search(p,head,re.I)for p in [r'//UserCode: 0x0000b0b2\b',r'//Part Number: GW5AT-LV60PG484AC1/I0',r'//Device-package: GW5AT-60B-PBGA484A\b'])
 part=bool(re.search(r'<Part Number>:\s*GW5AT-LV60PG484AC1/I0\s',report))
 fresh=all(p.stat().st_mtime>=started-2 for p in pnr.glob('*')if p.is_file())
 passed=bool(r.returncode==0 and sta['passed']and sta['constraint_period_ns']==19.5 and sta['fmax_mhz']>=51.282 and pins==m['pins']and identity and part and fresh)
 result.update(physical_passed=passed,sta=sta,pins_passed=pins==m['pins'],identity_passed=identity,part_passed=part,output_freshness_passed=fresh)
except Exception as exc:result['error']=str(exc)
(out/'reproduction_result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items()if k!='sta'},indent=2))
raise SystemExit(0 if result['physical_passed']else 1)
