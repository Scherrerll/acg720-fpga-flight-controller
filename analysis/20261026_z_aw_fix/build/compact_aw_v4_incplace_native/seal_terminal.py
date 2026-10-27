"""Seal actual completed native-flow receipts; no build or hardware operation."""
from pathlib import Path
import datetime,gzip,hashlib,json,re,sys
O=Path(__file__).resolve().parent;R=O.parents[3]
assert len(sys.argv)==2 and sys.argv[1] in ['2','3'];label=f'physical_p{sys.argv[1]}r0_01'
A=R/'out/z_aw_fix_20261026/compact_aw_v4_incplace_native'/label;V=A/'verification';REPORT=O/label
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf8'))
runner=read(REPORT/'runner_exit.json');vendor=read(V/'physical_exit.json')
assert runner['normal_wait_return'] and vendor['normal_wait_return']
expected=read(O/'source_freeze.json')['source55']
assert {n:sha(A/'source'/n) for n in expected}==expected
assert {n:sha(R/'out/z_aw_fix_20261026/compact_aw_v4_incplace_native/canonical/source'/n) for n in expected}==expected
binding=read(V/'donor_evidence_binding.json')['artifacts']
assert all(sha(Path(n))==item['sha256'] and Path(n).stat().st_size==item['bytes'] for n,item in binding.items())
audit=read(V/'physical_audit.json') if (V/'physical_audit.json').is_file() else None
passed=bool((V/'build_result.json').is_file() and read(V/'build_result.json')['passed'])
log=(V/'physical.log').read_text(errors='replace')
unrouted=[int(x) for x in re.findall(r'total\s+(\d+)\s+unrouted nets',log,re.I)]
classification='cancelled_duplicate_incremental_fallback' if (V/'incremental_fallback_cancel.json').is_file() else 'full_gate_pass' if passed else 'prephysical_audit_rejection' if 'NATIVE_SYNTHESIS_AUDIT_REJECTED' in log else 'completed_full_route_timing_failure' if audit and audit['criteria']['full_route'] and vendor['actual_p_wait']==0 else 'route_failure' if vendor['actual_p_wait']!=0 and (any(unrouted) or 'DesRoute failed.' in log) else 'vendor_nonzero_unclassified' if vendor['actual_p_wait']!=0 else 'physical_gate_or_artifact_failure'
vg=A/'source/impl/gwsynthesis/acg720_ano_port.vg'
paths=[REPORT/n for n in ['runner_process.json','runner_exit.json','runner.stdout.log','runner.stderr.log']]
paths += [V/n for n in ['physical_exit.json','physical_process.json','physical_input.json','build_input.json','physical.log',
    'incremental_flow_observation.json','incremental_fallback_cancel.json','physical_audit.json','build_result.json','build_failure.json','native_synthesis_audit.json','native_synthesis_audit_failure.json',
    'mapped_audit.json','gain_port_audit.json','strict_ff_clock_audit.json','resource_comparison.json',
    'project_serialization_check.json','donor_evidence_binding.json','executed_run_physical.py','executed_audit_synthesis.py','executed_native_physical_audit.py']]
paths += [A/'physical.tcl',A/'source/acg720_ano_port.gprj',vg,A/'source/impl/gwsynthesis/acg720_ano_port_syn_rsc.xml']
paths += [A/'source/impl/pnr'/n for n in ['acg720_ano_port.tr','acg720_ano_port.rpt.txt','acg720_ano_port.fs','acg720_ano_port.pr','device.cfg']]
paths=[p for p in paths if p.is_file()]
output=REPORT/'TERMINAL_MANIFEST.json';copies=REPORT/'terminal_receipts';assert not output.exists() and not copies.exists();copies.mkdir()
items={}
for path in paths:
    dest=copies/path.name;assert not dest.exists();data=path.read_bytes()
    if path.suffix in ['.vg','.tr','.txt','.log','.xml']:
        dest=dest.with_name(dest.name+'.gz')
        with gzip.GzipFile(filename=str(dest),mode='wb',mtime=0) as stream:stream.write(data)
    else:dest.write_bytes(data)
    assert sha(path)==hashlib.sha256(data).hexdigest()
    items[str(path.relative_to(R))]={'sha256':sha(path),'bytes':len(data),'preserved':str(dest.relative_to(R)),'preserved_sha256':sha(dest)}
result={'sealed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'workflow':'native_RTL_project_SYN_audit_PNR_one_vendor_process',
    'profile':label,'classification':classification,'passed':passed,'vendor_actual_p_wait':vendor['actual_p_wait'],
    'runner_actual_p_wait':runner['actual_p_wait'],'standalone_SYN_p_wait_claimed':False,'source55':expected,'source55_unchanged':True,
    'vg_sha256':sha(vg) if vg.is_file() else None,'unrouted_reports':unrouted,'criteria':audit['criteria'] if audit else None,
    'fmax_mhz':audit['fmax_mhz'] if audit else None,'checks':audit['checks'] if audit else None,
    'setup_endpoints':audit['setup_violated_endpoints'] if audit else None,'hold_endpoints':audit['hold_violated_endpoints'] if audit else None,
    'failure':read(V/'build_failure.json') if (V/'build_failure.json').is_file() else None,'artifacts':items}
output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
print(json.dumps({'sealed':True,'manifest_sha256':sha(output),'classification':classification,'passed':passed}))
