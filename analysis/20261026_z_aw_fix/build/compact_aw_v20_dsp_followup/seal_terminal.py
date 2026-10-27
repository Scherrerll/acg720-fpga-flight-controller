"""Preserve terminal evidence once; diagnostic PASS requires actual successful waits."""
from pathlib import Path
import datetime,gzip,hashlib,json,re,shutil,sys
O=Path(__file__).resolve().parent;R=O.parents[3];ROOT=R/'out/z_aw_fix_20261026/compact_aw_v20'
assert len(sys.argv)==2 and sys.argv[1] in ['3'];label='physical_p3r0_dsploc_01'
ATTEMPT=ROOT/label;V=ATTEMPT/'verification';REPORT=O/label
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text()) if p.is_file() else None
from terminal_diagnostics import terminal_status
assert (REPORT/'runner_exit.json').is_file() and (V/'physical_exit.json').is_file(), 'Both terminal receipt files must exist before sealing'
runner=read(REPORT/'runner_exit.json')
vendor=read(V/'physical_exit.json')
manifest=REPORT/'TERMINAL_MANIFEST.json';copies=REPORT/'terminal_receipts'
assert not manifest.exists() and not copies.exists()
from portable_constraints import validate,verify_attempt
assert validate()['passed'] and verify_attempt(ATTEMPT/'source')['passed']
expected=read(O/'source_freeze.json')['source55']
assert {p:sha(ATTEMPT/'source'/p) for p in expected}==expected
assert {p:sha(ROOT/'canonical/source'/p) for p in expected}==expected
VG='bb2d4a6d20184a0c38739b550d2fc04adf9fe9ce219106064a2051edbc26274f'
assert sha(ATTEMPT/'source/impl/gwsynthesis/acg720_ano_port.vg')==VG
bound=read(V/'donor_evidence_binding.json')['artifacts']
assert all(sha(Path(p))==x['sha256'] and Path(p).stat().st_size==x['bytes'] for p,x in bound.items())
audit=read(V/'physical_audit.json') if (V/'physical_audit.json').exists() else None
failure=read(V/'build_failure.json') if (V/'build_failure.json').exists() else None
build_result=read(V/'build_result.json')
physical_log=(V/'physical.log').read_text(errors='replace')
unrouted=[int(x) for x in re.findall(r'total\s+(\d+)\s+unrouted nets',physical_log,re.I)]
passed,classification=terminal_status(build_result,vendor,runner,audit,unrouted,physical_log)
paths=[REPORT/'runner_exit.json',REPORT/'runner_process.json',REPORT/'runner.stdout.log',REPORT/'runner.stderr.log']
paths += [V/n for n in ['physical_exit.json','physical_process.json','physical_input.json','build_input.json','physical.log','physical_audit.json','build_failure.json','build_result.json','project_serialization_check.json','donor_evidence_binding.json','functional_evidence_binding.json','portable_constraint_binding.json']]
paths += [ATTEMPT/'physical.tcl',ATTEMPT/'source/physical.gprj',ATTEMPT/'source/physical_constraints.cst',O/'PORTABLE_FILTER_VALIDATION.json',O/'PORTABLE_CONSTRAINT_BINDING.json',O/'portable_v20_dsp_bsram.cst',O/'PHYSICAL_PREPARATION.json',O/'PHYSICAL_TCL_PREFLIGHT.json']
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
    vendor_actual_p_wait=vendor.get('actual_p_wait') if isinstance(vendor,dict) else None,
    runner_actual_p_wait=runner.get('actual_p_wait') if isinstance(runner,dict) else None,passed=passed,
    vendor_normal_wait_return=vendor.get('normal_wait_return') if isinstance(vendor,dict) else None,
    runner_normal_wait_return=runner.get('normal_wait_return') if isinstance(runner,dict) else None,
    source55_unchanged=True,vg_sha256=VG,donor_evidence_unchanged=True,source55=expected,unrouted_reports=unrouted,
    criteria=audit['criteria'] if audit else None,fmax_mhz=audit['fmax_mhz'] if audit else None,
    checks=audit['checks'] if audit else None,setup_endpoints=audit['setup_violated_endpoints'] if audit else None,
    hold_endpoints=audit['hold_violated_endpoints'] if audit else None,failure=failure,artifacts=items)
manifest.write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
print(json.dumps(dict(manifest=str(manifest),sha256=sha(manifest),classification=classification,passed=passed),indent=2))
