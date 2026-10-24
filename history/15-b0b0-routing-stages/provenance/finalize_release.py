"""Freeze independently verified offline evidence; never access hardware."""
from pathlib import Path
import datetime,hashlib,importlib.util,json
ROOT=Path(__file__).resolve().parent
FIX=ROOT/'fixture'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    spec=importlib.util.spec_from_file_location('release_builder',FIX/'build_project.py')
    b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
    b.static_contract()
    q=json.loads((ROOT/'qualification.json').read_text(encoding='utf8'))
    m=json.loads((FIX/'build_manifest.json').read_text(encoding='utf8'))
    assert q['offline_tests_passed'] and m['verified']
    assert q['sources_sha256']==m['sources_sha256']==b.source_hashes()
    actual=b.verify(q['sources_sha256'])
    for key in ['bitstream','artifact_sha256','fmax_mhz','io_count','unrouted_nets','slack','pins']:
        assert actual[key]==m[key],('Build evidence changed',key)
    for name,digest in q['evidence_sha256'].items():assert sha(ROOT/name)==digest,('Proof changed',name)
    report=dict(candidate='B0B0',created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),offline_verified=True,
        qualification_sha256=sha(ROOT/'qualification.json'),build_manifest_sha256=sha(FIX/'build_manifest.json'),
        verifier_sha256=sha(FIX/'build_project.py'),source_contract_sha256=sha(ROOT/'source_contract.json'),
        bitstream=m['bitstream'],fmax_mhz=m['fmax_mhz'],unrouted_nets=m['unrouted_nets'],io_count=m['io_count'],slack=m['slack'],
        hardware_programmed=False,flash_changed=False,flight_ready=False,
        parent=json.loads((ROOT/'baseline.json').read_text(encoding='utf8'))['parent'],
        operator_notes_sha256=sha(ROOT/'OPERATOR_NOTES.txt'),
        remaining=['Targeted props-off B0B0 loss/manual-pilot/stop/recovery acceptance','Default Flash update only with explicit authorization and cold-start validation','Historical loaded power-loss investigation and actual flight qualification'])
    (ROOT/'offline_release.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    print(json.dumps(report,indent=2))
if __name__=='__main__':main()
