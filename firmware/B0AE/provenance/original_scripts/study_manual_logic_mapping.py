from pathlib import Path
import datetime,hashlib,json,re,shutil,subprocess,time,xml.etree.ElementTree as ET
R=Path(__file__).resolve().parent;F=R/'fixture';TOP='acg720_ano_port'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
q=json.loads((R/'qualification.json').read_text());inputs=q['sources_sha256']
assert all(sha(F/n)==h for n,h in inputs.items())
dest=R/'synthesis'/('manual_logic_'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ'));dest.mkdir(parents=True)
for n in inputs:
 p=dest/n;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(F/n,p)
p=dest/'core/rtl/ano_manual_angles.v';s=p.read_text();assert s.count('\n);')==1
p.write_text(s.replace('\n);','\n) /* synthesis syn_dspstyle="logic" */;'),encoding='utf8')
script=(dest/'build.tcl').read_text();assert script.splitlines().count('run all')==1
(dest/'study.tcl').write_text(script.replace('run all','run syn'),encoding='utf8')
log=dest/'console.txt'
with log.open('w',encoding='utf8') as stream:
 process=subprocess.Popen(['C:/Gowin/Gowin_V1.9.12.04_x64/IDE/bin/gw_sh.exe','study.tcl'],cwd=dest,stdout=stream,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
 start=time.monotonic();done=None
 while process.poll() is None:
  if 'GowinSynthesis finish' in log.read_text(encoding='utf8',errors='replace'):
   if done is None:done=time.monotonic()
   if time.monotonic()-done>10:process.terminate();process.wait(timeout=10);break
  if time.monotonic()-start>600:process.terminate();process.wait(timeout=10);raise RuntimeError('study timeout')
  time.sleep(1)
assert 'GowinSynthesis finish' in log.read_text(encoding='utf8',errors='replace')
assert all(sha(F/n)==h for n,h in inputs.items()),'Main source changed during isolated study'
node=ET.parse(dest/'impl/gwsynthesis'/(TOP+'_syn_rsc.xml')).getroot()
result=dict(offline_synthesis_only=True,pnr_run=False,hardware_accessed=False,
 experiment='ano_manual_angles module syn_dspstyle logic (no RTL equation changes)',
 parent_sources_sha256=inputs,resources=node.attrib,manual=[x.attrib for x in node.iter() if x.get('name')=='manual_angles'],folder=str(dest))
(dest/'study.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2),flush=True)
