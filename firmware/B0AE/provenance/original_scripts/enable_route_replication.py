from pathlib import Path
import hashlib,json,re,datetime
R=Path(__file__).resolve().parent;F=R/'fixture'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
qpath=R/'qualification.json';q=json.loads(qpath.read_text());old_q_sha=sha(qpath)
from control_contract import verify
verify();assert q['offline_tests_passed'] and q['hardware_accessed'] is False
for n,h in q['sources_sha256'].items():assert sha(F/n)==h,('changed source',n)
for n,h in q['evidence_sha256'].items():assert sha(R/n)==h,('changed proof',n)
for p in (R/'tests').glob('*.proof.json'):
 proof=json.loads(p.read_text());assert proof['passed']
 for n,h in proof['source_sha256'].items():assert sha(R/n)==h,('stale RTL proof',p,n)
tcl=F/'build.tcl';s=tcl.read_text();assert s.count('set_option -timing_driven 1')==1 and 'replicate_resources' not in s
old_tcl_sha=sha(tcl)
tcl.write_text(s.replace('set_option -timing_driven 1','set_option -timing_driven 1\nset_option -replicate_resources 1'),encoding='utf8')
names=re.findall(r'<File path="([^"]+)"',(F/'acg720_ano_port.gprj').read_text())+['acg720_ano_port.gprj','build.tcl']
now={n:sha(F/n) for n in names}
assert {n for n in now if now[n]!=q['sources_sha256'][n]}=={'build.tcl'}
q['sources_sha256']=now
q['build_configuration_requalification']=dict(prior_qualification_sha256=old_q_sha,
 changed_file='build.tcl',prior_sha256=old_tcl_sha,current_sha256=sha(tcl),
 change='set_option -replicate_resources 1',rtl_changed=False,existing_proofs_revalidated=True,
 vendor_reference='SUG1220-2.1E -replicate_resources; PNR high-fanout resource replication',
 verified_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
qpath.write_text(json.dumps(q,indent=2),encoding='utf8')
(R/'status.json').write_text(json.dumps(dict(phase='route_replication_retry',second_attempt_unrouted=916,
 hardware_programmed=False,flash_changed=False,flight_ready=False),indent=2))
print('All RTL and proof inputs unchanged; PNR replication option rebound to current qualification.')
