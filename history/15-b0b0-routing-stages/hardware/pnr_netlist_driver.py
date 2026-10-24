"""Netlist-only PNR settings trial. No HDL or synthesis status in project; never accesses hardware."""
from pathlib import Path
import argparse,datetime,hashlib,importlib.util,json,re,subprocess,sys,time,xml.etree.ElementTree as ET
HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
TOP='acg720_ano_port'
GW_SH='C:/Gowin/Gowin_V1.9.12.04_x64/IDE/bin/gw_sh.exe'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf8'))
def builder():
 c=load(ROOT/'trial_contract.json');P=Path(c['parent']);spec=importlib.util.spec_from_file_location('parent_builder',P/'fixture/build_project.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m,c,P
def source_hashes():
 return {n:sha(HERE/n)for n in [TOP+'.gprj',TOP+'.cst',TOP+'.sdc','impl/gwsynthesis/'+TOP+'.vg','build.tcl']}
def preflight():
 b,c,P=builder();assert sha(Path(__file__))==c['driver_sha256']
 assert c['policy'] in [dict(place_option=2,route_option=2,replicate_resources=0,route_maxfan=23,global_freq=50),dict(place_option=3,route_option=2,replicate_resources=1,route_maxfan=23,global_freq=50)]
 b.static_contract();assert b.source_hashes()==c['parent_sources_sha256']
 sys.path.insert(0,str(P));from inherited_context_bridge import verify as inherited
 assert inherited()['passed'] is True
 q=load(P/'qualification.json');assert sha(P/'qualification.json')==c['parent_qualification_sha256']
 assert q['offline_tests_passed'] is True and q['programming_authorized'] is False and q['sources_sha256']==c['parent_sources_sha256']
 assert len(q['evidence_sha256'])==34
 for n,h in q['evidence_sha256'].items():assert sha(P/n)==h,('Parent proof changed',n)
 assert source_hashes()==c['trial_sources_sha256'],'Netlist/constraint/project/Tcl input changed'
 assert sha(HERE/(TOP+'.cst'))==q['sources_sha256'][TOP+'.cst'] and sha(HERE/(TOP+'.sdc'))==q['sources_sha256'][TOP+'.sdc']
 project=ET.parse(HERE/(TOP+'.gprj'));device=project.find('.//Device');assert device.attrib['pn']=='GW5AT-LV60PG484AC1/I0' and device.attrib['name']=='GW5AT-60B'
 files=[e.attrib for e in project.findall('.//File')]
 assert files==[dict(path='impl/gwsynthesis/'+TOP+'.vg',type='file.netlist',enable='1'),dict(path=TOP+'.cst',type='file.cst',enable='1'),dict(path=TOP+'.sdc',type='file.sdc',enable='1')],'Only netlist+CST+SDC allowed; no RTL/dependency synthesis'
 expected=(P/'fixture/build.tcl').read_text().replace('set_option -place_option 2','set_option -place_option '+str(c['policy']['place_option'])).replace('set_option -replicate_resources 1','set_option -replicate_resources '+str(c['policy']['replicate_resources'])).replace('run all','set_option -route_maxfan 23\nrun pnr')
 assert (HERE/'build.tcl').read_text()==expected and (HERE/'pnr_only.tcl').read_text()==expected
 vg=HERE/'impl/gwsynthesis'/(TOP+'.vg');assert sha(vg)==c['audited_vg_sha256']=='a27dca89aa11e49bab4a370e5617bcac73c62db3ce5a9a5a4c8961cf31d207d8'
 assert sha(P/'fixture/impl/gwsynthesis'/(TOP+'.vg'))==sha(vg)
 aggregate=load(P/'hardware/mapped_init_review.json');assert aggregate['passed'] is True and aggregate['sources_sha256']==q['sources_sha256'] and aggregate['netlist_sha256']==sha(vg)
 assert aggregate['logical_bits_verified']==1696 and aggregate['nav_logical_bits']==720 and aggregate['mtf_logical_bits']==976 and aggregate['nav_passed'] is True and aggregate['mtf_passed'] is True
 for n in ['mapped_nav_review.json','mapped_mtf_review.json','synthesis_freshness_review.json']:assert load(P/'hardware'/n)['passed'] is True
 assert load(P/'hardware/synthesis_freshness_review.json')['netlist_sha256']==sha(vg)
 # This netlist-only project cannot supply HDL to synthesis. No SYN artifacts/status copied.
 assert set(p.name for p in (HERE/'impl/gwsynthesis').iterdir())=={TOP+'.vg'},'Unexpected synthesis artifact'
 assert (ROOT/'DO_NOT_PROGRAM').is_file()
 return dict(passed=True,sources_sha256=source_hashes(),parent_proof_scope='Original N q34 proofs at original paths; exact same audited mapped netlist, constraints, and device; PNR settings only',parent_qualification_sha256=sha(P/'qualification.json'),parent_evidence_sha256=q['evidence_sha256'],audited_vg_sha256=sha(vg),policy=c['policy'],hardware_accessed=False,programming_authorized=False)
def verify(inputs):
 proof=preflight();b,c,P=builder();assert source_hashes()==inputs
 started=load(ROOT/'run_state.json')['started_epoch']
 folder=HERE/'impl/pnr';cmdpath=folder/'cmd.do';text=cmdpath.read_text();actual=dict(re.findall(r'^-(\w+)[ 	]+(.+?)[ 	]*$',text,re.M))
 assert Path(actual['d']).resolve()==(HERE/'impl/gwsynthesis'/(TOP+'.vg')).resolve(),'PNR did not read trial VG'
 for key,rel in [('cst',TOP+'.cst'),('sdc',TOP+'.sdc')]:assert Path(actual[key]).resolve()==(HERE/rel).resolve()
 assert actual['p']=='GW5AT-60B-PBGA484A-1' and actual['pn']=='GW5AT-LV60PG484AC1/I0'
 assert actual['place_option']==str(c['policy']['place_option']) and actual['route_option']=='2' and actual['route_maxfan']=='23' and float(actual['global_freq'])==50
 assert bool(re.search(r'^-replicate\s*$',text,re.M))==bool(c['policy']['replicate_resources'])
 assert re.search(r'^-timing\s*$',text,re.M)
 outputs=[folder/(TOP+s)for s in ['.tr','.rpt.txt','.fs']]
 for p in outputs+[cmdpath]:assert p.is_file()and p.stat().st_mtime>=started,('Missing/stale PNR artifact',str(p))
 console=(HERE/'build_console.txt').read_text(errors='replace')
 assert not re.search(r'GowinSynthesis|Running synthesis|run syn',console,re.I),'Unexpected synthesis invocation'
 assert not re.search(r'ERROR\s*\(',console) and all(s in console for s in ['Placement and routing completed','Bitstream generation completed'])
 # Actual PNR log must name the exact copied trial Design File.
 logs=list(folder.glob('*.log'));assert logs,'Missing PNR log'
 logtext='\n'.join(p.read_text(errors='replace')for p in logs)
 normalized=logtext.replace('\\','/').lower();assert str((HERE/'impl/gwsynthesis'/(TOP+'.vg')).resolve()).replace('\\','/').lower() in normalized,'PNR log did not identify trial Design File'
 timing=outputs[0].read_text(errors='replace');resources=outputs[1].read_text(errors='replace')
 assert not re.search(r'ERROR\s*\(|\b[1-9][0-9]*\s+unrouted nets\b',resources)
 fmax=re.search(r'clk50\s+50\.000\(MHz\)\s+([0-9.]+)\(MHz\)',timing);assert fmax and float(fmax[1])>=50
 io=re.search(r'^\s*I/O Port\s+\|\s*([0-9]+)/([0-9]+)',resources,re.M);assert io and int(io[1])==17
 slack={}
 for kind in ['setup','hold']:
  match=re.search(r'clk50\s+'+kind+r'\s+(-?[0-9.]+)\s+([0-9]+)',timing);assert match and float(match[1])==0 and int(match[2])==0
  slack[kind]=dict(tns_ns=float(match[1]),violated_endpoints=int(match[2]))
 pins=dict(re.findall(r'^(\w+)\s+\|\s*-\s*\|\s*(\w+)/\d+\s*\|',resources,re.M));assert pins==b.PINS
 with outputs[2].open(encoding='ascii',errors='replace')as f:header=''.join(next(f,'')for _ in range(15))
 code=re.search(r'UserCode:\s*(0x[0-9A-Fa-f]+)',header);assert code and int(code[1],16)==0xB0B0
 cls=re.search(r'^\s*CLS\s+\|\s*([0-9]+)/([0-9]+)',resources,re.M);assert cls
 preflight()
 artifacts=outputs[:2]+[cmdpath,HERE/'build_console.txt']+logs
 return dict(verified=True,resource_timing_verified=True,profile='bmi088_mtf_ano_control_b0b0',top=TOP,sources_sha256=inputs,fmax_mhz=float(fmax[1]),io_count=17,unrouted_nets=0,slack=slack,pins=pins,cls_used=int(cls[1]),cls_total=int(cls[2]),bitstream=dict(path=str(outputs[2]),sha256=sha(outputs[2]),user_code=code[1]),artifact_sha256={str(p.relative_to(HERE)).replace('\\','/'):sha(p)for p in artifacts},parent_context=proof,policy=c['policy'],audited_vg_sha256=c['audited_vg_sha256'],hardware_accessed=False,hardware_programmed=False,flash_changed=False,physical_sensor_verified=False,flight_ready=False,programming_authorized=False)
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--preflight',action='store_true');parser.add_argument('--verify-existing',action='store_true');args=parser.parse_args()
 if args.preflight:print(json.dumps(preflight(),indent=2));return
 if args.verify_existing:
  manifest=load(HERE/'build_manifest.json');assert manifest['verified'] is True;actual=verify(manifest['sources_sha256'])
  for k in ['bitstream','artifact_sha256','pins','fmax_mhz','slack','unrouted_nets','sources_sha256']:assert actual[k]==manifest[k],('Manifest changed',k)
  print(json.dumps(actual,indent=2));return
 preflight();assert not(HERE/'impl/pnr').exists(),'Refuse to reuse existing PNR outputs'
 inputs=source_hashes();(HERE/'build_manifest.json').write_text(json.dumps(dict(verified=False,sources_sha256=inputs)))
 state=dict(started_epoch=time.time(),pnr_only=True,hardware_accessed=False);(ROOT/'run_state.json').write_text(json.dumps(state,indent=2))
 with(HERE/'build_console.txt').open('w')as log:
  process=subprocess.Popen([GW_SH,'pnr_only.tcl'],cwd=HERE,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
  state['owned_pid']=process.pid;(ROOT/'run_state.json').write_text(json.dumps(state,indent=2));print(json.dumps(state),flush=True)
  since=None
  while process.poll()is None:
   console=(HERE/'build_console.txt').read_text(errors='replace')
   if re.search(r'GowinSynthesis|Running synthesis|run syn',console,re.I):process.terminate();process.wait(timeout=10);raise RuntimeError('Unexpected synthesis; stopped owned process')
   if 'Bitstream generation completed'in console or 'ERROR'in console:
    if since is None:since=time.monotonic()
    if time.monotonic()-since>20:process.terminate();process.wait(timeout=10);break
   if time.time()-state['started_epoch']>5400:process.terminate();process.wait(timeout=10);raise RuntimeError('PNR timeout')
   time.sleep(1)
 result=verify(inputs);(HERE/'build_manifest.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
