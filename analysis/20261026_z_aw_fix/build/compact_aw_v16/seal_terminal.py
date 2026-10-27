"""Preserve actual terminal evidence once; no gate changes, process controls or rebuild."""
from pathlib import Path
import datetime,gzip,hashlib,json,re,shutil,sys
O=Path(__file__).resolve().parent;R=O.parents[3];ROOT=R/'out/z_aw_fix_20261026/compact_aw_v16'
assert len(sys.argv)==2 and sys.argv[1] in ['2','3'];label=f'physical_p{sys.argv[1]}r0_01'
ATTEMPT=ROOT/label;V=ATTEMPT/'verification';REPORT=O/label
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text())
runner=read(REPORT/'runner_exit.json');assert runner['normal_wait_return'] is True
vendor=read(V/'physical_exit.json');assert vendor['normal_wait_return'] is True
manifest=REPORT/'TERMINAL_MANIFEST.json';copies=REPORT/'terminal_receipts'
assert not manifest.exists() and not copies.exists()
expected=read(O/'source_freeze.json')['source55']
assert {p:sha(ATTEMPT/'source'/p) for p in expected}==expected
assert {p:sha(ROOT/'canonical/source'/p) for p in expected}==expected
VG='ce776628cc9c7b2fd9a1700aa7961d9640c7957fd37242bf0fc093539d669a10'
assert sha(ATTEMPT/'source/impl/gwsynthesis/acg720_ano_port.vg')==VG
bound=read(V/'donor_evidence_binding.json')['artifacts']
assert all(sha(Path(p))==x['sha256'] and Path(p).stat().st_size==x['bytes'] for p,x in bound.items())
audit=read(V/'physical_audit.json') if (V/'physical_audit.json').exists() else None
failure=read(V/'build_failure.json') if (V/'build_failure.json').exists() else None
passed=(V/'build_result.json').is_file() and read(V/'build_result.json')['passed'] is True
physical_log=(V/'physical.log').read_text(errors='replace')
unrouted=[int(x) for x in re.findall(r'total\s+(\d+)\s+unrouted nets',physical_log,re.I)]
classification='full_gate_pass' if passed else 'completed_full_route_timing_failure' if audit and audit['criteria']['full_route'] and vendor['actual_p_wait']==0 else 'route_failure' if vendor['actual_p_wait']!=0 and (any(unrouted) or 'DesRoute failed.' in physical_log) else 'vendor_nonzero_unclassified' if vendor['actual_p_wait']!=0 else 'physical_gate_or_artifact_failure'
paths=[REPORT/'runner_exit.json',REPORT/'runner_process.json',REPORT/'runner.stdout.log',REPORT/'runner.stderr.log']
paths += [V/n for n in ['physical_exit.json','physical_process.json','physical_input.json','build_input.json','physical.log','physical_audit.json','build_failure.json','build_result.json','project_serialization_check.json','donor_evidence_binding.json']]
paths += [ATTEMPT/'physical.tcl',ATTEMPT/'source/physical.gprj']
paths += [ATTEMPT/'source/impl/pnr'/n for n in ['acg720_ano_port.tr','acg720_ano_port.rpt.txt','acg720_ano_port.fs','acg720_ano_port.pr','device.cfg']]
paths=[p for p in paths if p.is_file()];copies.mkdir()
items={}
for p in paths:
    data=p.read_bytes();dest=copies/p.name
    if p.suffix in ['.log','.tr','.txt']:
        dest=dest.with_name(dest.name+'.gz')
        with gzip.GzipFile(filename=str(dest),mode='wb',mtime=0) as output:output.write(data)
    else:dest.write_bytes(data)
    assert sha(p)==hashlib.sha256(data).hexdigest()
    items[str(p.relative_to(R))]={'sha256':sha(p),'bytes':len(data),'preserved':str(dest.relative_to(R)),'preserved_sha256':sha(dest)}
result=dict(sealed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),profile=label,classification=classification,
    vendor_actual_p_wait=vendor['actual_p_wait'],runner_actual_p_wait=runner['actual_p_wait'],passed=passed,
    source55_unchanged=True,vg_sha256=VG,donor_evidence_unchanged=True,source55=expected,unrouted_reports=unrouted,
    criteria=audit['criteria'] if audit else None,fmax_mhz=audit['fmax_mhz'] if audit else None,
    checks=audit['checks'] if audit else None,setup_endpoints=audit['setup_violated_endpoints'] if audit else None,
    hold_endpoints=audit['hold_violated_endpoints'] if audit else None,failure=failure,artifacts=items)
manifest.write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
print(json.dumps(dict(manifest=str(manifest),sha256=sha(manifest),classification=classification,passed=passed),indent=2))
