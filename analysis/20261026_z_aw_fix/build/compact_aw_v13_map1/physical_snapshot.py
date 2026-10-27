"""Read-only compact snapshot; terminal receipts, not file presence, establish exits."""
from pathlib import Path
import json,re
O=Path(__file__).resolve().parent;R=O.parents[3];ROOT=R/'out/z_aw_fix_20261026/compact_aw_v13_map1'
def read(p):return json.loads(p.read_text()) if p.is_file() else None
rows=[]
for label in ['physical_p3r0_01','physical_p2r0_01']:
    v=ROOT/label/'verification';a=O/label
    text=(v/'physical.log').read_text(errors='replace') if (v/'physical.log').is_file() else ''
    stages=re.findall(r'^.*(?:\[\d+%\]|Running (?:placement|routing)|Placement and routing completed|Bitstream generation completed|PHYSICAL_COMMAND_RETURNED_EOF).*$' ,text,re.M)
    vendor=read(v/'physical_exit.json');runner=read(a/'runner_exit.json');audit=read(v/'physical_audit.json');result=read(v/'build_result.json');failure=read(v/'build_failure.json')
    row=dict(profile=label,last_stage=stages[-1].strip() if stages else None,
        log_bytes=(v/'physical.log').stat().st_size if (v/'physical.log').is_file() else 0,
        vendor_actual_p_wait=vendor['actual_p_wait'] if vendor else None,
        runner_actual_p_wait=runner['actual_p_wait'] if runner else None,
        full_gate_pass=bool(result and result.get('passed')),
        terminal=bool(runner),unrouted=[int(x) for x in re.findall(r'total\s+(\d+)\s+unrouted nets',text,re.I)])
    if audit:row.update(fmax_mhz=audit['fmax_mhz'],criteria=audit['criteria'],setup_endpoints=audit['setup_violated_endpoints'],hold_endpoints=audit['hold_violated_endpoints'])
    if failure:row['failure']=failure.get('exception')
    if runner and not row['full_gate_pass']:
        if vendor and vendor['actual_p_wait']!=0:row['failure_class']='vendor_nonzero_route_failure' if any(row['unrouted']) else 'vendor_nonzero_unclassified'
        elif audit:row['failure_class']='completed_vendor_physical_gate_failure'
        elif vendor:row['failure_class']='completed_vendor_missing_or_unparseable_artifact'
        else:row['failure_class']='runner_ended_without_vendor_exit_receipt'
    rows.append(row)
print(json.dumps(rows,indent=2))
