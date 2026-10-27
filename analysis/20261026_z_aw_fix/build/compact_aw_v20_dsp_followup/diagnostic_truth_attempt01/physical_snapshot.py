"""Read-only compact snapshot; terminal receipts, not file presence, establish exits."""
from pathlib import Path
import json,re
O=Path(__file__).resolve().parent;R=O.parents[3];ROOT=R/'out/z_aw_fix_20261026/compact_aw_v20'
def read(p):return json.loads(p.read_text()) if p.is_file() else None
from terminal_diagnostics import terminal_status
rows=[]
for label in ['physical_p3r0_dsploc_01']:
    v=ROOT/label/'verification';a=O/label
    text=(v/'physical.log').read_text(errors='replace') if (v/'physical.log').is_file() else ''
    stages=re.findall(r'^.*(?:\[\d+%\]|Running (?:placement|routing)|Placement and routing completed|Bitstream generation completed|PHYSICAL_COMMAND_RETURNED_EOF).*$' ,text,re.M)
    vendor=read(v/'physical_exit.json');runner=read(a/'runner_exit.json');audit=read(v/'physical_audit.json');result=read(v/'build_result.json');failure=read(v/'build_failure.json')
    unrouted=[int(x) for x in re.findall(r'total\s+(\d+)\s+unrouted nets',text,re.I)]
    passed,classification=terminal_status(result,vendor,runner,audit,unrouted,text)
    row=dict(profile=label,last_stage=stages[-1].strip() if stages else None,
        log_bytes=(v/'physical.log').stat().st_size if (v/'physical.log').is_file() else 0,
        vendor_actual_p_wait=vendor.get('actual_p_wait') if isinstance(vendor,dict) else None,
        runner_actual_p_wait=runner.get('actual_p_wait') if isinstance(runner,dict) else None,
        full_gate_pass=passed,
        terminal=bool(runner),unrouted=unrouted)
    if audit:row.update(fmax_mhz=audit['fmax_mhz'],criteria=audit['criteria'],setup_endpoints=audit['setup_violated_endpoints'],hold_endpoints=audit['hold_violated_endpoints'])
    if failure:row['failure']=failure.get('exception')
    if runner and not row['full_gate_pass']:
        row['failure_class']=classification
    rows.append(row)
print(json.dumps(rows,indent=2))
