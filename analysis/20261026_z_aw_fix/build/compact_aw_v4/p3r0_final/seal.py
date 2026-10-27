from pathlib import Path
import hashlib,json
O=Path(__file__).resolve().parent;R=O.parents[4];A=R/'out/z_aw_fix_20261026/compact_aw_v4/physical_p3r0_01';V=A/'verification'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
inp=json.loads((V/'build_input.json').read_text());expected=inp['source_sha256'];ex=json.loads((V/'physical_exit.json').read_text());audit=json.loads((V/'physical_audit.json').read_text())
assert ex['actual_p_wait']==0 and audit['passed'] is False and audit['criteria']['full_route'] is True
assert audit['period_ns']==20.0 and audit['fmax_mhz']==49.456
assert audit['checks']['setup']['worst_slack_ns']==-0.220 and audit['setup_violated_endpoints']==32 and audit['hold_violated_endpoints']==0
assert expected['position/mtf_xyz_hold_control.v']=='ffddb029cb34a8d2ac8995cc43d85866e273d3d147bb650cfd5d3c66c580b642'
for root,values in [(Path(inp['canonical_override']),expected),(A/'source',expected),(R/'firmware/B0B4/source',inp['original_B4_source55']),(R/'out/z_aw_fix_20261026/compact_aw_v3/canonical/source',inp['v3_source55'])]:
    assert len(values)==55 and all(sha(root/p)==h for p,h in values.items())
assert sha(A/'source/impl/gwsynthesis/acg720_ano_port.vg')=='e67bcab6336757e08645756258d39dd13726b452c392d470de4c900a159aaa8f'
paths=[V/n for n in ['build_input.json','physical_input.json','physical_process.json','physical_exit.json','physical.log','physical_audit.json','build_failure.json','project_serialization_check.json']]
paths += [A/'physical.tcl',A/'source/physical.gprj']
paths += [A/'source/impl/pnr'/('acg720_ano_port.'+s) for s in ['tr','rpt.txt','fs','pr','pin.html']]
paths += [A/'source/impl/pnr/device.cfg',A/'source/acg720_ano_port.sdc',A/'source/acg720_ano_port.cst',A/'source/impl/gwsynthesis/acg720_ano_port.vg']
paths += [O.parent/n for n in ['run_physical_p3r0.py','physical_p3_runner.stdout.log','physical_p3_runner.stderr.log','physical_p3_runner_process.json']]
data={'scope':'Frozen v4 P3R0 terminal evidence: complete routing and realwait0, but fails20ns STA. No acceptance/download/hardware.',
 'actual_p_wait':0,'physical_ended_utc':ex['ended_utc'],'classification':'STA failure after full route','accepted_for_delivery':False,
 'period_ns':audit['period_ns'],'fmax_mhz':audit['fmax_mhz'],'slacks_ns':{n:x['worst_slack_ns'] for n,x in audit['checks'].items()},
 'setup_violated_endpoints':audit['setup_violated_endpoints'],'hold_violated_endpoints':audit['hold_violated_endpoints'],
 'all_criteria':audit['criteria'],'source55':expected,'source55_checks_passed':True,
 'raw_tr_path':str((A/'source/impl/pnr/acg720_ano_port.tr').resolve()),
 'external_evidence':{p.relative_to(R).as_posix():{'bytes':p.stat().st_size,'sha256':sha(p)} for p in paths}}
(O/'FINAL_STATUS.json').write_text(json.dumps(data,indent=2)+'\n')
print(json.dumps({'final_status_sha256':sha(O/'FINAL_STATUS.json'),'tr_sha256':sha(A/'source/impl/pnr/acg720_ano_port.tr'),'fs_sha256':sha(A/'source/impl/pnr/acg720_ano_port.fs'),'exit_sha256':sha(V/'physical_exit.json'),'audit_sha256':sha(V/'physical_audit.json')},indent=2))
