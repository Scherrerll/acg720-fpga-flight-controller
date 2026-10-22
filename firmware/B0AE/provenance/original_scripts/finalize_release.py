from pathlib import Path
import hashlib,importlib.util,json,datetime
R=Path(__file__).resolve().parent;F=R/'fixture'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
spec=importlib.util.spec_from_file_location('verified_builder',F/'build_project.py')
b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
b.static_contract()
q=json.loads((R/'qualification.json').read_text());m=json.loads((F/'build_manifest.json').read_text())
assert q['offline_tests_passed'] and m['verified'] and m['sources_sha256']==q['sources_sha256']
actual=b.verify(q['sources_sha256'])
assert actual['bitstream']==m['bitstream'] and actual['artifact_sha256']==m['artifact_sha256']
for key in ['fmax_mhz','io_count','unrouted_nets','slack','sources_sha256','pins','cls_used']:
 assert actual[key]==m[key],('build manifest metric changed',key)
for n,h in q['evidence_sha256'].items():assert sha(R/n)==h,('proof changed',n)
metrics={}
for name in ['state_reference','sticks_reference','height_reference','xy_reference','manual_reference']:
 metrics[name]=json.loads((R/'tests'/f'{name}.json').read_text())
release=dict(candidate='B0AE',created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
 offline_verified=True,flight_ready=False,hardware_programmed=False,flash_changed=False,
 qualification_sha256=sha(R/'qualification.json'),build_manifest_sha256=sha(F/'build_manifest.json'),
 independent_verifier_sha256=sha(F/'build_project.py'),pnr_configuration_verified=True,pnr_resource_replication_enabled=False,
 configuration_requalification=q.get('build_configuration_requalification'),
 bitstream=m['bitstream'],fmax_mhz=m['fmax_mhz'],io_count=m['io_count'],unrouted_nets=m['unrouted_nets'],slack=m['slack'],
 source_reference='reference_ano/quadrotor_tm_v1_20261012/Quadrotor_TM_V1',
 hardware_adaptations='CONTROL_CONTRACT.txt',numerical_reference_results=metrics,
 rollback=json.loads((R/'baseline.json').read_text())['parent'],
 last_pre_task_sram_observation='B0AD',default_flash_unchanged='B0AC',
 remaining_acceptance=['New props-off physical control validation','Vertical sensor failure/fallback limitation (no barometer)','Flight qualification and historical loaded power-loss investigation'])
(R/'offline_release.json').write_text(json.dumps(release,indent=2),encoding='utf8')
(R/'status.json').write_text(json.dumps(dict(phase='offline_verified_await_physical_acceptance',flight_ready=False,hardware_programmed=False,flash_changed=False,bitstream=m['bitstream'],offline_release_sha256=sha(R/'offline_release.json')),indent=2))
print(json.dumps(dict(offline_verified=True,candidate='B0AE',fmax_mhz=m['fmax_mhz'],bitstream=m['bitstream'],flight_ready=False,hardware_programmed=False),indent=2),flush=True)
