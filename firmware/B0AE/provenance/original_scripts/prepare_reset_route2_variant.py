from pathlib import Path
import hashlib,json,shutil,datetime
R=Path(__file__).resolve().parent;S=R/'variants/reset_global';F=S/'fixture';D=R/'variants/reset_global_route2';DF=D/'fixture'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
q=json.loads((S/'qualification.json').read_text());assert q['offline_tests_passed']
for n,h in q['sources_sha256'].items():assert sha(F/n)==h,('qualification not current',n)
for n,h in q['evidence_sha256'].items():assert sha(S/n)==h,('proof changed',n)
D.mkdir(parents=True,exist_ok=False)
files=set(q['evidence_sha256'])|{'qualification.json','baseline.json','说明.txt','实物验收要点.txt','DO_NOT_PROGRAM'}
files|={str(p.relative_to(S)).replace('\\','/') for p in S.glob('*.py')}
files|={'fixture/'+n for n in q['sources_sha256']}
files|={'fixture/'+n for n in json.loads((S/'baseline.json').read_text())['baseline_sources']}
files|={'fixture/build_project.py'}
for n in sorted(files):
 p=S/n
 if p.is_file():
  dest=D/n;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
p=DF/'build.tcl';s=p.read_text();assert s.count('set_option -route_option 0')==1
p.write_text(s.replace('set_option -route_option 0','set_option -route_option 2'),encoding='utf8')
p=DF/'build_project.py';s=p.read_text();assert s.count("'route_option':'0'")==1 and s.count("actual_pnr.get('route_option')!='0'")==1
p.write_text(s.replace("'route_option':'0'","'route_option':'2'").replace("actual_pnr.get('route_option')!='0'","actual_pnr.get('route_option')!='2'"),encoding='utf8')
for n,h in q['sources_sha256'].items():assert n=='build.tcl' or sha(DF/n)==h
q['sources_sha256']['build.tcl']=sha(DF/'build.tcl')
q['build_configuration_requalification'].update(parent_reset_global_qualification_sha256=sha(S/'qualification.json'),route_option=2,
 route_change_reason='Independent route2 comparison reached380 unrouted vs route0=660; same reset allocation, same RTL')
(D/'qualification.json').write_text(json.dumps(q,indent=2),encoding='utf8')
(D/'status.json').write_text(json.dumps(dict(phase='reset_global_route2',hardware_programmed=False,flash_changed=False,flight_ready=False),indent=2))
print(str(D),flush=True)
