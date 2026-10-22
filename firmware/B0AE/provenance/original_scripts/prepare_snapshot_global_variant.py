from pathlib import Path
import hashlib,json,shutil,datetime
R=Path(__file__).resolve().parent;F=R/'fixture';D=R/'variants/snapshot_global_route2';DF=D/'fixture'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
q=json.loads((R/'qualification.json').read_text());assert q['offline_tests_passed']
for n,h in q['sources_sha256'].items():assert sha(F/n)==h
for n,h in q['evidence_sha256'].items():assert sha(R/n)==h
D.mkdir(parents=True,exist_ok=False)
files=set(q['evidence_sha256'])|{'qualification.json','baseline.json','说明.txt','实物验收要点.txt','DO_NOT_PROGRAM'}
files|={str(p.relative_to(R)).replace('\\','/') for p in R.glob('*.py')}
files|={'fixture/'+n for n in q['sources_sha256']}
files|={'fixture/'+n for n in json.loads((R/'baseline.json').read_text())['baseline_sources']}
files|={'fixture/build_project.py'}
for n in files:
 p=R/n
 if p.is_file():
  dest=D/n;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
line='CLOCK_LOC "staged_telemetry.core_q_453_16" BUFG = CE;'
p=DF/'acg720_ano_port.cst';s=p.read_text();assert 'CLOCK_LOC' not in s
p.write_text(s.rstrip()+'\n'+line+'\n',encoding='utf8')
p=DF/'build.tcl';s=p.read_text();assert s.count('set_option -route_option 1')==1
p.write_text(s.replace('set_option -route_option 1','set_option -route_option 2'),encoding='utf8')
p=D/'control_contract.py';s=p.read_text();assert s.count("'acg720_ano_port.gprj','build.tcl','build_project.py'}")==1
s=s.replace("'acg720_ano_port.gprj','build.tcl','build_project.py'}","'acg720_ano_port.gprj','acg720_ano_port.cst','build.tcl','build_project.py'}")
needle=" parent=Path(b['parent'])\n";assert s.count(needle)==1
extra=" parent=Path(b['parent'])\n clock_line="+repr(line)+"\n cst=(FIX/'acg720_ano_port.cst').read_text()\n original_path=parent/'fixture/acg720_ano_port.cst'\n if sha(original_path)!=b['baseline_sources']['acg720_ano_port.cst']:raise ValueError('Parent pin constraints changed')\n if cst!=original_path.read_text().rstrip()+'\\n'+clock_line+'\\n':raise ValueError('Only the single snapshot resource constraint may differ; IO unchanged')\n"
p.write_text(s.replace(needle,extra),encoding='utf8')
p=DF/'build_project.py';s=p.read_text();assert s.count("'route_option':'1'")==1 and s.count("actual_pnr.get('route_option')!='1'")==1
s=s.replace("'route_option':'1'","'route_option':'2'").replace("actual_pnr.get('route_option')!='1'","actual_pnr.get('route_option')!='2'")
needle="    if re.search(r'ERROR\\s*\\(',resources)";assert s.count(needle)==1
s=s.replace(needle,"    if not re.search(r'^\\s*staged_telemetry\\.core_q_453_16\\s*\\|\\s*PRIMARY',resources,re.M):raise ValueError('Snapshot clock-resource constraint was not implemented')\n"+needle)
p.write_text(s,encoding='utf8')
for n,h in q['sources_sha256'].items():assert n in ['build.tcl','acg720_ano_port.cst'] or sha(DF/n)==h
for n in ['build.tcl','acg720_ano_port.cst']:q['sources_sha256'][n]=sha(DF/n)
q['evidence_sha256']['control_contract.py']=sha(D/'control_contract.py')
q['build_configuration_requalification']=dict(parent_qualification_sha256=sha(R/'qualification.json'),change=line,
 route_option=2,rtl_changed=False,io_constraints_unchanged=True,existing_proofs_revalidated=True,
 vendor_reference='SUG1541-1.0E section2.8 CLOCK_LOC BUFG=CE',created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
(D/'qualification.json').write_text(json.dumps(q,indent=2))
(D/'status.json').write_text(json.dumps(dict(phase='snapshot_global_route2',hardware_programmed=False,flash_changed=False,flight_ready=False),indent=2))
print(str(D),flush=True)
