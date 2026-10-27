"""Compare sealed raw physical resource reports; no timing or route pass inference."""
from pathlib import Path
import hashlib, json
O=Path(__file__).resolve().parent;R=O.parents[3]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf8'))
trials={
 'v4_fullroute_timing_failed':('compact_aw_v4_p3mf60_followup','compact_aw_v4','physical_p3r0_mf60_01'),
 'v13_p2_route_failed':('compact_aw_v13','compact_aw_v13','physical_p2r0_01')}
out={}
for label,(meta,root,profile) in trials.items():
    manifest=R/'analysis/20261026_z_aw_fix/build'/meta/profile/'TERMINAL_MANIFEST.json'
    sealed=read(manifest)
    report=R/'out/z_aw_fix_20261026'/root/profile/'source/impl/pnr/acg720_ano_port.rpt.txt'
    item=sealed['artifacts'][str(report.relative_to(R))]
    assert sha(report)==item['sha256']
    rows={}
    for line in report.read_text(errors='replace').splitlines():
        fields=[part.strip() for part in line.split('|')]
        if len(fields)>=3 and fields[0] in ['Logic','CLS','PRIMARY','LW','--Logic Register as FF']:
            rows[fields[0]]={'usage':fields[1],'utilization':fields[2]}
    assert all(name in rows for name in ['Logic','CLS','PRIMARY','LW'])
    out[label]={'manifest_sha256':sha(manifest),'report_sha256':sha(report),'resources':rows,
                'vendor_actual_wait':sealed['vendor_actual_p_wait'],'runner_actual_wait':sealed['runner_actual_p_wait'],
                'classification':sealed['classification']}
destination=O/'RAW_PACKING_COMPARISON.json';assert not destination.exists()
destination.write_text(json.dumps({'scope':'Raw resource occupancy only. The v13 report is from a route failure and contains no qualified TR/bitstream. PRIMARY/LW are global resources and are not additional logical FF clocks.',
    'reports':out,'decision_basis':'Retain the exact-source map1 alternative with no LUT5 definitions to test placement/packing. No routing or timing benefit is inferred from occupancy.'},indent=2)+'\n')
print(json.dumps(out,indent=2))
