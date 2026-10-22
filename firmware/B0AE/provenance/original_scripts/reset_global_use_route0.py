from pathlib import Path
import datetime,hashlib,json,shutil
R=Path(__file__).resolve().parent;D=R/'variants/reset_global';F=D/'fixture'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
q=json.loads((D/'qualification.json').read_text());prior=sha(D/'qualification.json')
for n,h in q['sources_sha256'].items():assert sha(F/n)==h
for n,h in q['evidence_sha256'].items():assert sha(D/n)==h
archive=D/'attempts'/('cancelled_route1_'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
archive.mkdir(parents=True)
names=set(q['evidence_sha256'])|{'qualification.json','status.json','fixture/build_project.py','fixture/build_manifest.json','fixture/build_console.txt'}
names|={'fixture/'+n for n in q['sources_sha256']}
names|={str(p.relative_to(D)).replace('\\','/') for p in (F/'impl').rglob('*') if p.is_file()}
for n in names:
 p=D/n
 if p.is_file():
  target=archive/n;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,target)
(archive/'cancellation.json').write_text(json.dumps(dict(reason='Route1 independently failed6150 nets; retain reset-resource experiment but use better route0',hardware_accessed=False,source_qualification_sha256=prior),indent=2))
p=F/'build.tcl';s=p.read_text();assert s.count('set_option -route_option 1')==1
p.write_text(s.replace('set_option -route_option 1','set_option -route_option 0'),encoding='utf8')
p=F/'build_project.py';s=p.read_text();assert s.count("'route_option':'1'")==1 and s.count("actual_pnr.get('route_option')!='1'")==1
p.write_text(s.replace("'route_option':'1'","'route_option':'0'").replace("actual_pnr.get('route_option')!='1'","actual_pnr.get('route_option')!='0'"),encoding='utf8')
q['sources_sha256']['build.tcl']=sha(F/'build.tcl')
q['build_configuration_requalification'].update(prior_reset_variant_qualification_sha256=prior,route_option=0,
 route_change_reason='route1 failed6150; choose route0 for reset-resource comparison')
(D/'qualification.json').write_text(json.dumps(q,indent=2),encoding='utf8')
print('Cancelled input archived; reset resource comparison now uses route0.')
