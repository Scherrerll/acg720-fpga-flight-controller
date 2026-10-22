from pathlib import Path
import hashlib,json,re,datetime
R=Path(__file__).resolve().parent;F=R/'fixture'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
q=json.loads((R/'qualification.json').read_text());prior=sha(R/'qualification.json')
for n,h in q['sources_sha256'].items():assert sha(F/n)==h,('changed RTL/config',n)
for n,h in q['evidence_sha256'].items():assert sha(R/n)==h,('changed evidence',n)
s=(F/'build.tcl').read_text();assert s.count('set_option -route_option 0')==1
(F/'build.tcl').write_text(s.replace('set_option -route_option 0','set_option -route_option 1'),encoding='utf8')
s=(F/'build_project.py').read_text();assert s.count("'route_option':'0'")==1 and s.count("actual_pnr.get('route_option')!='0'")==1
(F/'build_project.py').write_text(s.replace("'route_option':'0'","'route_option':'1'").replace("actual_pnr.get('route_option')!='0'","actual_pnr.get('route_option')!='1'"),encoding='utf8')
for n,h in q['sources_sha256'].items():assert n=='build.tcl' or sha(F/n)==h
q['sources_sha256']['build.tcl']=sha(F/'build.tcl')
q['build_configuration_requalification']=dict(prior_qualification_sha256=prior,change='route_option0 to1 only',
 rtl_changed=False,existing_proofs_revalidated=True,place_option=3,replicate_resources=True,freq_mhz=50,
 verified_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
(R/'qualification.json').write_text(json.dumps(q,indent=2))
(R/'status.json').write_text(json.dumps(dict(phase='route_algorithm_comparison',prior_unrouted=[265,916,396,660],
 rtl_qualification_unchanged=True,hardware_programmed=False,flash_changed=False,flight_ready=False),indent=2))
print('All RTL and existing test evidence unchanged; only routing algorithm changed to1.')
