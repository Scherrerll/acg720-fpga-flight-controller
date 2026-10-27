"""Preserve actual terminal evidence once; no gate changes, process controls or rebuild."""
from pathlib import Path
import datetime,gzip,hashlib,json,re,shutil,sys
O=Path(__file__).resolve().parent;R=O.parents[3];ROOT=R/'out/z_aw_fix_20261026/compact_aw_v22'
assert len(sys.argv)==2 and sys.argv[1] in ['3'];label='physical_p3r0_01'
ATTEMPT=ROOT/label;V=ATTEMPT/'verification';REPORT=O/label
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text())
def successful_receipt(receipt):
    return (isinstance(receipt,dict) and receipt.get('normal_wait_return') is True
            and type(receipt.get('actual_p_wait')) is int and receipt.get('actual_p_wait')==0)

def terminal_status(result,vendor,runner,audit=None,unrouted=None,physical_log=''):
    result_passed=isinstance(result,dict) and result.get('passed') is True
    passed=result_passed and successful_receipt(vendor) and successful_receipt(runner)
    if passed:return True,'full_gate_pass'
    physical_gate_passed=result_passed or (isinstance(audit,dict) and audit.get('passed') is True)
    if (physical_gate_passed and successful_receipt(vendor) and isinstance(runner,dict)
        and runner.get('normal_wait_return') is True and type(runner.get('actual_p_wait')) is int
        and runner.get('actual_p_wait')!=0):return False,'runner_failed_after_physical_gate_pass'
    if not isinstance(vendor,dict):return False,'missing_vendor_exit_receipt'
    if not isinstance(runner,dict):return False,'waiting_for_runner_exit_receipt'
    if vendor.get('normal_wait_return') is not True:return False,'vendor_receipt_not_normal'
    if type(vendor.get('actual_p_wait')) is not int:return False,'vendor_wait_missing_or_invalid'
    if vendor.get('actual_p_wait')!=0:
        return False,'route_failure' if any(unrouted or []) or 'DesRoute failed.' in physical_log else 'vendor_nonzero_unclassified'
    if runner.get('normal_wait_return') is not True:return False,'runner_receipt_not_normal'
    if type(runner.get('actual_p_wait')) is not int:return False,'runner_wait_missing_or_invalid'
    full_route=(isinstance(audit,dict) and isinstance(audit.get('criteria'),dict)
                and audit['criteria'].get('full_route') is True)
    if full_route:return False,'completed_full_route_timing_failure'
    return False,'physical_gate_or_artifact_failure'

runner=read(REPORT/'runner_exit.json') if (REPORT/'runner_exit.json').is_file() else None
vendor=read(V/'physical_exit.json') if (V/'physical_exit.json').is_file() else None
# Missing receipts are never passing; wait for both actual terminal receipts before sealing.
assert isinstance(runner,dict) and isinstance(vendor,dict),'Cannot seal before both terminal receipts exist'
manifest=REPORT/'TERMINAL_MANIFEST.json';copies=REPORT/'terminal_receipts'
assert not manifest.exists() and not copies.exists()
from physical_input_contract import validate22
assert validate22(require_preparation=True)['passed']
expected=read(O/'source_freeze.json')['source55']
assert {p:sha(ATTEMPT/'source'/p) for p in expected}==expected
assert {p:sha(ROOT/'canonical/source'/p) for p in expected}==expected
VG=read(O/'SYNTHESIS_RESULT.json')['netlist_sha256']
assert sha(ATTEMPT/'source/impl/gwsynthesis/acg720_ano_port.vg')==VG
bound=read(V/'donor_evidence_binding.json')['artifacts']
assert all(sha(Path(p))==x['sha256'] and Path(p).stat().st_size==x['bytes'] for p,x in bound.items())
audit=read(V/'physical_audit.json') if (V/'physical_audit.json').exists() else None
failure=read(V/'build_failure.json') if (V/'build_failure.json').exists() else None
build_result=read(V/'build_result.json') if (V/'build_result.json').is_file() else None
physical_log=(V/'physical.log').read_text(errors='replace')
unrouted=[int(x) for x in re.findall(r'total\s+(\d+)\s+unrouted nets',physical_log,re.I)]
passed,classification=terminal_status(build_result,vendor,runner,audit,unrouted,physical_log)
paths=[REPORT/'runner_exit.json',REPORT/'runner_process.json',REPORT/'runner.stdout.log',REPORT/'runner.stderr.log']
paths += [V/n for n in ['physical_exit.json','physical_process.json','physical_input.json','build_input.json','physical.log','physical_audit.json','build_failure.json','build_result.json','project_serialization_check.json','donor_evidence_binding.json','functional_evidence_binding.json']]
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
    vendor_actual_p_wait=vendor.get('actual_p_wait'),runner_actual_p_wait=runner.get('actual_p_wait'),passed=passed,
    vendor_normal_wait_return=vendor.get('normal_wait_return'),runner_normal_wait_return=runner.get('normal_wait_return'),
    source55_unchanged=True,vg_sha256=VG,donor_evidence_unchanged=True,source55=expected,unrouted_reports=unrouted,
    criteria=audit['criteria'] if audit else None,fmax_mhz=audit['fmax_mhz'] if audit else None,
    local_hint_effect_audit_sha256=read(O/'PHYSICAL_PREPARATION.json')['local_hint_effect_audit_sha256'],baseline_version='v20',protected_v4_separately_bound=True,
    checks=audit['checks'] if audit else None,setup_endpoints=audit['setup_violated_endpoints'] if audit else None,
    hold_endpoints=audit['hold_violated_endpoints'] if audit else None,failure=failure,artifacts=items)
manifest.write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
print(json.dumps(dict(manifest=str(manifest),sha256=sha(manifest),classification=classification,passed=passed),indent=2))
