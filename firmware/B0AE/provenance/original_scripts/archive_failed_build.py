from pathlib import Path
import datetime,hashlib,json,re,shutil
R=Path(__file__).resolve().parent;F=R/'fixture'
report=(F/'impl/pnr/acg720_ano_port.rpt.txt').read_text(errors='replace')
count=re.search(r'([0-9]+) unrouted nets',report)
assert count, 'Only archive a reported routing failure'
dest=R/'attempts'/('route'+count.group(1)+'_'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
dest.mkdir(parents=True,exist_ok=False)
q=json.loads((R/'qualification.json').read_text())
names=set(q['evidence_sha256'])|{'qualification.json','status.json','说明.txt','source_diff.patch','实物验收要点.txt'}
names|={'fixture/'+n for n in q['sources_sha256']}
names|={'fixture/build_project.py','fixture/build_manifest.json','fixture/build_console.txt'}
names|={str(p.relative_to(R)).replace('\\','/') for p in (F/'impl').rglob('*') if p.is_file()}
copied={}
for n in sorted(names):
 p=R/n
 if not p.is_file():continue
 target=dest/n;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,target)
 copied[n]=hashlib.sha256(target.read_bytes()).hexdigest()
(dest/'archive.json').write_text(json.dumps(dict(unrouted_nets=int(count.group(1)),files=copied),indent=2),encoding='utf8')
print(str(dest))
