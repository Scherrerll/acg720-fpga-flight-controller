# Unqualified offline routing feasibility ONLY. No release APIs, synthesis, or hardware.
from pathlib import Path
import argparse,hashlib,json,re,subprocess,time,xml.etree.ElementTree as ET
F=Path(__file__).resolve().parent
T=F.parent
TOP='acg720_ano_port'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf8'))
def require(ok,msg):
 if not ok:raise ValueError(msg)
def preflight():
 c=read(T/'feasibility_contract.json');S=Path(c['study_manifest']);s=read(S)
 require(sha(S)==c['study_manifest_sha256'] and s['passed'] is True,'Actual studied SYN changed')
 require(c['policy']==dict(place_option=2,route_option=2,replicate_resources=0,route_maxfan=23,global_freq=50),'Policy changed')
 require(sha(Path(__file__))==c['runner_sha256'],'Runner changed')
 require(sha(Path(c['proposal']))==c['proposal_sha256']=='3d5c57327d08ac319e619dee834214a5079b5eb8df71f6c93b738c484a27dd8f','NAV proposal changed')
 folder=Path(s['folder'])
 for name,p in c['proposals'].items():require(sha(Path(p['path']))==p['sha256']==s['source_sha256'][name],'Exact NAV/heightfusion proposal changed: '+name)
 require(s['source_sha256']['sensor/mtf01p_reader.v']=='a2999acee160e936af18013ffd9fd9f9bd3c3649d6a7c5e0439aa0ec96d0f680','Selected reader changed')
 base=read(Path(c['baseline_manifest']));require(sha(Path(c['baseline_manifest']))==c['baseline_manifest_sha256'],'Baseline changed')
 require(set(s['source_sha256'])==set(base['source_sha256']),'Source family changed')
 for n,h in s['source_sha256'].items():
  if n not in ['mtf_xyz_navigation_control.v','position/mtf_shared_height_fusion.v']:require(h==base['source_sha256'][n],'Unapproved RTL/source change: '+n)
 opts={e.attrib['type']:e.attrib['value']for e in ET.parse(folder/'impl/gwsynthesis'/(TOP+'.prj')).findall('.//Option')}
 require(opts['map_option']=='2'and opts['opt_goal']=='area'and float(opts['global_freq'])==50 and opts['max_fanout']=='200','Actual studied options changed')
 require(s['source_sha256']['mtf_xyz_navigation_control.v']==c['proposal_sha256'],'Studied NAV differs from proposal')
 expected=(folder/'build.tcl').read_text().replace('set_option -replicate_resources 1','set_option -replicate_resources 0').replace('run all','set_option -route_maxfan 23\nrun pnr')
 expected=expected.replace('run pnr','set_option -inc_place {'+(F/c['reference_copy_relative']).as_posix()+'}\nrun pnr')
 require((F/'pnr_only.tcl').read_text()==expected,'PNRonly/incremental Tcl differs')
 require('inc_pnr'not in expected,'No ambiguous incremental-routing option')
 ref=Path(c['reference_checkpoint']);copy=F/c['reference_copy_relative']
 require(sha(ref)==sha(copy)==c['reference_checkpoint_sha256'],'Original/copied placement checkpoint changed')
 require(sha(Path(c['reference_source_vg']))==c['reference_source_vg_sha256']=='9e4ea068664dc558f6238f04c46311cfdb381b1d71ddb3ba68d7867c690f0b8d','Checkpoint sourceVG changed')
 prior=read(Path(c['reference_result']));require(sha(Path(c['reference_result']))==c['reference_result_sha256']and prior['routing_passed'] is True and prior['vg_sha256']==c['reference_source_vg_sha256'],'Reference was not complete-routed9e4ea')
 for n,h in s['source_sha256'].items():require(sha(folder/n)==h,'Original SYN snapshot changed: '+n)
 for n,h in s['evidence_sha256'].items():require(sha(folder/n)==h,'Original SYN evidence changed: '+n)
 for n,h in c['inputs_sha256'].items():require(sha(F/n)==h,'Trial input changed: '+n)
 vg=F/'impl/gwsynthesis'/(TOP+'.vg');require(sha(vg)==s['proposed_vg_sha256']==c['vg_sha256']=='8e32072310b6b8826c1431f4b7116f5a9d8cb95d2df17f63dd8e4014b6cd8445','VG identity changed')
 require(sha(F/(TOP+'.cst'))==s['source_sha256'][TOP+'.cst'] and sha(F/(TOP+'.sdc'))==s['source_sha256'][TOP+'.sdc'],'Constraint identity changed')
 p=ET.parse(F/(TOP+'.gprj'));require(p.find('.//Device').attrib==dict(name='GW5AT-60B',pn='GW5AT-LV60PG484AC1/I0'),'Device changed')
 files=[x.attrib for x in p.findall('.//File')]
 require(files==[dict(path='impl/gwsynthesis/'+TOP+'.vg',type='file.netlist',enable='1'),dict(path=TOP+'.cst',type='file.cst',enable='1'),dict(path=TOP+'.sdc',type='file.sdc',enable='1')],'Project must contain only exactVG/CST/SDC')
 require(set(x.name for x in (F/'impl/gwsynthesis').iterdir())=={TOP+'.vg'},'Unexpected SYN status/artifact')
 require((T/'DO_NOT_PROGRAM').is_file(),'Missing programming block')
 return c

def collect(start):
 c=preflight();P=F/'impl/pnr';console=(F/'console.txt').read_text(errors='replace')
 paths=[p for p in P.glob('*')if p.is_file()]if P.exists()else[]
 result=dict(verified=False,functional_qualification_pending=True,programming_authorized=False,hardware_accessed=False,flight_ready=False,release_eligible=False,scope='Routing/timing feasibility only; does not establish functional qualification or authorize programming',policy=c['policy'],vg_sha256=c['vg_sha256'],inputs_sha256=c['inputs_sha256'],actual_outputs_sha256={str(p.relative_to(F)):sha(p)for p in paths+[F/'console.txt']},routing_passed=False,timing_passed=False,feasibility_passed=False)
 try:
  cmd=P/'cmd.do';require(cmd.is_file()and cmd.stat().st_mtime>=start,'Missing/stale actual cmd.do')
  text=cmd.read_text();a=dict(re.findall(r'^-(\w+)[ \t]+(.+?)[ \t]*$',text,re.M))
  require(Path(a['d']).resolve()==(F/'impl/gwsynthesis'/(TOP+'.vg')).resolve(),'ActualPNR did not read copiedVG')
  for k,n in [('cst',TOP+'.cst'),('sdc',TOP+'.sdc')]:require(Path(a[k]).resolve()==(F/n).resolve(),'Actual constraint path changed')
  require(a['p']=='GW5AT-60B-PBGA484A-1'and a['pn']=='GW5AT-LV60PG484AC1/I0','Actual device changed')
  require(a['place_option']=='2'and a['route_option']=='2'and a['route_maxfan']=='23'and float(a['global_freq'])==50,'Actual policy changed')
  require(not re.search(r'^-replicate\s*$',text,re.M)and re.search(r'^-timing\s*$',text,re.M),'Actualreplicate/timing changed')
  require(not re.search(r'GowinSynthesis|Running synthesis|run syn',console,re.I),'Implicit synthesis occurred')
  rpt=P/(TOP+'.rpt.txt');require(rpt.is_file()and rpt.stat().st_mtime>=start,'Missing/stale report');r=rpt.read_text(errors='replace')
  errors=re.findall(r'ERROR[^\r\n]*',r);un=re.search(r'total\s+(\d+)\s+unrouted nets',r)
  result.update(errors=errors,unrouted_nets=int(un[1])if un else None)
  pins=dict(re.findall(r'^(\w+)\s+\|\s*-\s*\|\s*(\w+)/\d+\s*\|',r,re.M));require(pins==c['pins'],'Placed17pin map differs');result['pins']=pins
  result['routing_passed']=not errors and not(un and int(un[1]))and 'Placement and routing completed'in console
  tr=P/(TOP+'.tr');fs=P/(TOP+'.fs')
  if tr.is_file():
   require(tr.stat().st_mtime>=start,'Stale TR');t=tr.read_text(errors='replace');fm=re.search(r'clk50\s+50\.000\(MHz\)\s+([0-9.]+)\(MHz\)',t);slack={}
   for k in ['setup','hold']:
    m=re.search(r'clk50\s+'+k+r'\s+(-?[0-9.]+)\s+([0-9]+)',t)
    if m:slack[k]=dict(tns_ns=float(m[1]),violated_endpoints=int(m[2]))
   result.update(fmax_mhz=float(fm[1])if fm else None,slack=slack)
   result['timing_passed']=bool(fm and float(fm[1])>=50 and all(slack.get(k)==dict(tns_ns=0.0,violated_endpoints=0)for k in ['setup','hold']))
  if fs.is_file():
   require(fs.stat().st_mtime>=start,'Stale FS')
   with fs.open(encoding='ascii',errors='replace')as stream:header=''.join(next(stream,'')for _ in range(15))
   code=re.search(r'UserCode:\s*(0x[0-9A-Fa-f]+)',header);require(code and int(code[1],16)==0xB0B0,'FSUserCode differs')
   result['bitstream']=dict(path=str(fs),sha256=sha(fs),user_code=code[1])
  result['feasibility_passed']=bool(result['routing_passed']and result['timing_passed']and result.get('bitstream')and 'Bitstream generation completed'in console)
 except(ValueError,KeyError,FileNotFoundError)as e:result['acceptance_error']=str(e)
 # Request identity is checked, but vendor checkpoint reuse is not presumed.
 logs='\n'.join(p.read_text(errors='replace')for p in paths if p.suffix=='.log')
 cmdtext=(P/'cmd.do').read_text(errors='replace')if(P/'cmd.do').exists()else''
 copy=(F/c['reference_copy_relative']).as_posix().lower()
 seen=copy in (cmdtext+'\n'+logs).replace('\\','/').lower()
 result.update(incremental_request_bound=True,incremental_reference_seen_in_actual_cmd_or_log=seen,vendor_incremental_reuse_confirmed=None,incremental_reference_sha256=c['reference_checkpoint_sha256'],incremental_actual_cmd_lines=[l for l in cmdtext.splitlines()if 'inc'in l.lower()or'9e4ea_complete.p'in l.lower()],incremental_vendor_log_lines=[l for l in logs.splitlines()if 'increment'in l.lower()or'9e4ea_complete.p'in l.lower()],incremental_status='Requested official inc_place; actual command/log requires review for whether and how placement was reused')
 if not seen:
  result['feasibility_passed']=False;result['incremental_acceptance_pending']='Reference path not identified in actual cmd/log; routing/timing facts remain separate'
 preflight() # Reference copy and original remain immutable after PNR too.
 (T/'feasibility_result.json').write_text(json.dumps(result,indent=2)+'\n');return result

def run():
 preflight();require(not(F/'impl/pnr').exists(),'Refuse existingPNR outputs');state=dict(started_epoch=time.time(),functional_qualification_pending=True,programming_authorized=False)
 (T/'run_state.json').write_text(json.dumps(state,indent=2))
 with(F/'console.txt').open('w')as log:
  p=subprocess.Popen(['C:/Gowin/Gowin_V1.9.12.04_x64/IDE/bin/gw_sh.exe','pnr_only.tcl'],cwd=F,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
  state['owned_pid']=p.pid;(T/'run_state.json').write_text(json.dumps(state,indent=2));print(json.dumps(state),flush=True);since=None
  while p.poll()is None:
   text=(F/'console.txt').read_text(errors='replace')
   if re.search(r'GowinSynthesis|Running synthesis|run syn',text,re.I)or time.time()-state['started_epoch']>5400:p.terminate();p.wait(timeout=10);break
   if 'Bitstream generation completed'in text or 'ERROR'in text:
    if since is None:since=time.monotonic()
    if time.monotonic()-since>20:p.terminate();p.wait(timeout=10);break
   time.sleep(1)
 print(json.dumps(collect(state['started_epoch']),indent=2))
if __name__=='__main__':
 p=argparse.ArgumentParser();g=p.add_mutually_exclusive_group(required=True);g.add_argument('--preflight',action='store_true');g.add_argument('--run',action='store_true');args=p.parse_args()
 if args.preflight:preflight();print(json.dumps(dict(inputs_bound=True,functional_qualification_pending=True,programming_authorized=False,release_eligible=False)))
 else:run()
