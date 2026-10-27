"""Read-only compact snapshot; terminal receipts, not file presence, establish exits."""
from pathlib import Path
import json,re
O=Path(__file__).resolve().parent;R=O.parents[3];ROOT=R/'out/z_aw_fix_20261026/compact_aw_v22'
def read(p):return json.loads(p.read_text()) if p.is_file() else None
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

rows=[]
for label in ['physical_p3r0_dsploc_01']:
    v=ROOT/label/'verification';a=O/label
    text=(v/'physical.log').read_text(errors='replace') if (v/'physical.log').is_file() else ''
    stages=re.findall(r'^.*(?:\[\d+%\]|Running (?:placement|routing)|Placement and routing completed|Bitstream generation completed|PHYSICAL_COMMAND_RETURNED_EOF).*$' ,text,re.M)
    vendor=read(v/'physical_exit.json');runner=read(a/'runner_exit.json');audit=read(v/'physical_audit.json');result=read(v/'build_result.json');failure=read(v/'build_failure.json')
    full_gate_pass,failure_class=terminal_status(result,vendor,runner,audit,
        [int(x) for x in re.findall(r'total\s+(\d+)\s+unrouted nets',text,re.I)],text)
    row=dict(profile=label,last_stage=stages[-1].strip() if stages else None,
        log_bytes=(v/'physical.log').stat().st_size if (v/'physical.log').is_file() else 0,
        vendor_actual_p_wait=vendor.get('actual_p_wait') if isinstance(vendor,dict) else None,
        runner_actual_p_wait=runner.get('actual_p_wait') if isinstance(runner,dict) else None,
        full_gate_pass=full_gate_pass,
        vendor_normal_wait_return=vendor.get('normal_wait_return') if isinstance(vendor,dict) else None,
        runner_normal_wait_return=runner.get('normal_wait_return') if isinstance(runner,dict) else None,
        terminal=isinstance(runner,dict) and runner.get('normal_wait_return') is True and type(runner.get('actual_p_wait')) is int,unrouted=[int(x) for x in re.findall(r'total\s+(\d+)\s+unrouted nets',text,re.I)])
    if audit:row.update(fmax_mhz=audit['fmax_mhz'],criteria=audit['criteria'],setup_endpoints=audit['setup_violated_endpoints'],hold_endpoints=audit['hold_violated_endpoints'])
    if failure:row['failure']=failure.get('exception')
    if not row['full_gate_pass']:row['failure_class']=failure_class
    rows.append(row)
print(json.dumps(rows,indent=2))
