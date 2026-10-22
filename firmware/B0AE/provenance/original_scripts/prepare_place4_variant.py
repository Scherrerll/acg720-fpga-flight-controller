from pathlib import Path
import hashlib,json,re,shutil,datetime
R=Path(__file__).resolve().parent;F=R/'fixture';D=R/'variants/place4';DF=D/'fixture'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
q=json.loads((R/'qualification.json').read_text());assert q['offline_tests_passed']
for n,h in q['sources_sha256'].items():assert sha(F/n)==h,('qualification not current',n)
for n,h in q['evidence_sha256'].items():assert sha(R/n)==h,('proof changed',n)
D.mkdir(parents=True,exist_ok=False)
files=set(q['evidence_sha256'])|{'qualification.json','baseline.json','说明.txt','实物验收要点.txt','DO_NOT_PROGRAM'}
files|={str(p.relative_to(R)).replace('\\','/') for p in R.glob('*.py')}
files|={'fixture/'+n for n in q['sources_sha256']}
files|={'fixture/'+n for n in json.loads((R/'baseline.json').read_text())['baseline_sources']}
files|={'fixture/build_project.py'}
for n in sorted(files):
 p=R/n
 if p.is_file():
  dest=D/n;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
script=DF/'build.tcl';s=script.read_text();assert s.count('set_option -place_option 3')==1
script.write_text(s.replace('set_option -place_option 3','set_option -place_option 4'),encoding='utf8')
driver=DF/'build_project.py';s=driver.read_text();assert s.count("'place_option':'3'")==1 and s.count("actual_pnr.get('place_option')!='3'")==1
driver.write_text(s.replace("'place_option':'3'","'place_option':'4'").replace("actual_pnr.get('place_option')!='3'","actual_pnr.get('place_option')!='4'"),encoding='utf8')
for n,h in q['sources_sha256'].items():assert n=='build.tcl' or sha(DF/n)==h
q['sources_sha256']['build.tcl']=sha(script)
q['build_configuration_requalification']=dict(parent_qualification_sha256=sha(R/'qualification.json'),
 change='place_option3 to4 only; route0, replication,50MHz unchanged',rtl_changed=False,
 existing_proofs_revalidated=True,created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
(D/'qualification.json').write_text(json.dumps(q,indent=2),encoding='utf8')
(D/'status.json').write_text(json.dumps(dict(phase='place4_comparison',hardware_programmed=False,flash_changed=False,flight_ready=False),indent=2))
print(str(D),flush=True)
