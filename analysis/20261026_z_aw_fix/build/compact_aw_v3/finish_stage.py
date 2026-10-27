from pathlib import Path
import hashlib,json,re
O=Path(__file__).resolve().parent;R=O.parents[3];ROOT=R/'out/z_aw_fix_20261026/compact_aw_v3';S=ROOT/'build_attempt_01';P=ROOT/'physical_p3r0_01'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
expected=json.loads((O/'source_freeze.json').read_text())['source55'];info=json.loads((S/'verification/build_input.json').read_text())
checks=[]
for root,values in [(ROOT/'canonical/source',expected),(S/'source',expected),(P/'source',expected),(R/'firmware/B0B4/source',info['original_B4_source55']),(R/'out/z_aw_fix_20261026/compact_aw_v2/canonical/source',info['compact_v2_map2_source55'])]:
    assert len(values)==55 and all(sha(root/n)==h for n,h in values.items());checks.append({'source':str(root),'source55_match':True})
vg=S/'source/impl/gwsynthesis/acg720_ano_port.vg';vgsha=sha(vg)
assert vgsha==sha(P/'source/impl/gwsynthesis/acg720_ano_port.vg')=='4f329e5313eba5966394828734c61867a3483b3eed8c3c37c724a453285c8a0c'
ex=json.loads((P/'verification/physical_exit.json').read_text());log=(P/'verification/physical.log').read_text()
assert ex['actual_p_wait']==1 and ex['log_sha256']==sha(P/'verification/physical.log')
assert 'DesRoute failed' in log and re.findall(r'total\s+(\d+)\s+unrouted nets',log)==['898']
assert all(not (P/('source/impl/pnr/acg720_ano_port.'+s)).exists() for s in ['tr','fs','pr'])
assert json.loads((S/'verification/synthesis_exit.json').read_text())['actual_p_wait']==0
assert json.loads((S/'verification/strict_ff_clock_audit.json').read_text())['all_FF_CLK50'] is True
paths=[S/'verification'/n for n in ['build_input.json','synthesis_input.json','synthesis_exit.json','synthesis.log','synthesis_summary.json','mapped_audit.json','gain_port_audit.json','strict_ff_clock_audit.json','resource_comparison.json']]
paths += [vg,S/'source/impl/gwsynthesis/acg720_ano_port_syn_rsc.xml']
paths += [P/'verification'/n for n in ['build_input.json','physical_input.json','physical_process.json','physical_exit.json','physical.log','build_failure.json','project_serialization_check.json']]
paths += [P/'physical.tcl',P/'source/physical.gprj',P/'source/impl/pnr/acg720_ano_port.rpt.txt',P/'source/impl/pnr/device.cfg']
data={'scope':'Final v3 map2 P3R0 build status. SYN/MAP pass; physical realexit1/898unrouted/noTRFS, not timing-qualified or accepted. No hardware.',
 'hold_sha256':expected['position/mtf_xyz_hold_control.v'],'netlist_sha256':vgsha,'source55_checks':checks,
 'synthesis_actual_p_wait':0,'physical_actual_p_wait':1,'physical_ended_utc':ex['ended_utc'],'unrouted':898,
 'physical_options':{'place':3,'route':0,'map_option':2,'replicate_resources':0,'timing_driven':1},
 'tr_fs_pr_present':False,'accepted_for_delivery':False,'classification':'route failure, no STA evidence',
 'external_evidence':{p.relative_to(R).as_posix():{'bytes':p.stat().st_size,'sha256':sha(p)} for p in paths}}
(O/'FINAL_STATUS.json').write_text(json.dumps(data,indent=2)+'\n')
print(json.dumps({'final_status_sha256':sha(O/'FINAL_STATUS.json'),'exit_sha256':sha(P/'verification/physical_exit.json'),'log_sha256':sha(P/'verification/physical.log'),'rpt_sha256':sha(P/'source/impl/pnr/acg720_ano_port.rpt.txt')},indent=2))
