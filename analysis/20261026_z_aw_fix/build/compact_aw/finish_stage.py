from pathlib import Path
import hashlib,importlib.util,json,re
O=Path(__file__).resolve().parent;R=O.parents[3];ROOT=R/'out/z_aw_fix_20261026/compact_aw_v1'
SYN=ROOT/'build_attempt_01';P1=ROOT/'physical_p3r0_01';P2=ROOT/'physical_p3r0_02'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
freeze=json.loads((O/'source_freeze.json').read_text());expected=freeze['variant_source55'];base=freeze['base_source55']
for root,expected_hashes in [(R/'firmware/B0B4/source',base),(ROOT/'canonical/source',expected),(SYN/'source',expected),(P1/'source',expected),(P2/'source',expected)]:
    assert len(expected_hashes)==55 and all(sha(root/p)==h for p,h in expected_hashes.items()),str(root)
vg=SYN/'source/impl/gwsynthesis/acg720_ano_port.vg';vgsha=sha(vg)
assert vgsha=='b7691fd2d04abfc95e1fa458b0cb22e1c8ebcb2eb810db16e7a706fa8e73a87b'
assert sha(P1/'source/impl/gwsynthesis/acg720_ano_port.vg')==sha(P2/'source/impl/gwsynthesis/acg720_ano_port.vg')==vgsha
reader=R.parents[1]/'runtime_xy_pi_20261026/tools/read_cones.py'
spec=importlib.util.spec_from_file_location('compact_final_clock_graph',reader);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
g=mod.Graph(vg)
clock=[c['pins']['O'][0] for c in g.cells.values() if c['type']=='IBUF' and c['pins'].get('I')==['clk50']]
assert len(clock)==1
bad=[]
for name,pins in g.regs.items():
    if len(pins.get('CLK',[]))!=1 or g.find(pins['CLK'][0])!=g.find(clock[0]):bad.append({'name':name,'clocks':pins.get('CLK',[])})
clock_receipt={'passed':not bad,'mapped_ff_count':len(g.regs),'all_ff_CLK50':not bad,'bad_ff_clock_count':len(bad),'bad':bad,'vg_sha256':vgsha,'reader_sha256':sha(reader)}
(O/'strict_ff_clock_check.json').write_text(json.dumps(clock_receipt,indent=2)+'\n')
assert not bad
ex1=json.loads((P1/'verification/physical_exit.json').read_text());ex2=json.loads((P2/'verification/physical_exit.json').read_text())
log1=(P1/'verification/physical.log').read_text();log2=(P2/'verification/physical.log').read_text()
assert ex1['actual_p_wait']==1 and 'invalid project file' in log1 and 'Running placement' not in log1
assert ex2['actual_p_wait']==1 and 'DesRoute failed' in log2 and re.findall(r'total\s+(\d+)\s+unrouted nets',log2)==['746']
assert all(not (P2/('source/impl/pnr/acg720_ano_port.'+suffix)).exists() for suffix in ['tr','fs','pr'])
synexit=json.loads((SYN/'verification/synthesis_exit.json').read_text());assert synexit['actual_p_wait']==0
files=[SYN/'verification/synthesis_input.json',SYN/'verification/synthesis_exit.json',SYN/'verification/synthesis.log',SYN/'verification/synthesis_summary.json',SYN/'verification/mapped_audit.json',SYN/'verification/resource_comparison.json',vg,SYN/'source/impl/gwsynthesis/acg720_ano_port_syn_rsc.xml']
for p in [P1,P2]:
    files += [p/'verification/build_input.json',p/'verification/physical_input.json',p/'verification/physical_exit.json',p/'verification/physical.log',p/'verification/build_failure.json',p/'physical.tcl',p/'source/physical.gprj']
files += [P2/'source/impl/pnr/acg720_ano_port.rpt.txt',P2/'source/impl/pnr/device.cfg']
receipt={'scope':'Final frozen independent compact AW v1 build status; no physical qualification, no hardware. Original B4 and all source55 copies unchanged.',
 'hold_sha256':expected['position/mtf_xyz_hold_control.v'],'vg_sha256':vgsha,'source55_count':55,'all_source55_checks_passed':True,
 'synthesis_actual_p_wait':0,'mapped_ff_clock_check_sha256':sha(O/'strict_ff_clock_check.json'),
 'physical_01':{'actual_p_wait':1,'classification':'duplicate-XML project generation error; rejected before placement, not routing/timing failure'},
 'physical_02':{'actual_p_wait':1,'ended_utc':ex2['ended_utc'],'physical_options':{'place':3,'route':0,'map_option':2,'replicate_resources':0},'classification':'route failure','unrouted':746,'tr_fs_pr_present':False,'timing_qualification':'unavailable; no TR','accepted_for_delivery':False},
 'external_evidence':{p.relative_to(R).as_posix():{'bytes':p.stat().st_size,'sha256':sha(p)} for p in files}}
(O/'FINAL_STATUS.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({'strict_FF_CLK50':True,'FFs':len(g.regs),'final_status_sha256':sha(O/'FINAL_STATUS.json'),'physical02_exit_sha256':sha(P2/'verification/physical_exit.json'),'physical02_log_sha256':sha(P2/'verification/physical.log'),'physical02_rpt_sha256':sha(P2/'source/impl/pnr/acg720_ano_port.rpt.txt')},indent=2))
