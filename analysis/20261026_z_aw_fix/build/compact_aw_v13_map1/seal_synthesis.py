"""Freeze real SYN result and LUT mapping distribution; no physical launch."""
from collections import Counter
from pathlib import Path
import datetime, hashlib, json
O=Path(__file__).resolve().parent;R=O.parents[3]
read=lambda p:json.loads(p.read_text(encoding='utf8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
A=R/'out/z_aw_fix_20261026/compact_aw_v13_map1/build_attempt_01';V=A/'verification'
root=read(O/'runner_exit.json');vendor=read(V/'synthesis_exit.json');summary=read(V/'synthesis_summary.json')
assert root['normal_wait_return'] and vendor['normal_wait_return']
assert root['actual_p_wait']==vendor['actual_p_wait']==summary['actual_p_wait']==0 and summary['passed']
assert read(V/'build_input.json')['synthesis_options']=={'map_option':1,'replicate_resources':0}
for name in ['mapped_audit.json','gain_port_audit.json','strict_ff_clock_audit.json']:
    assert read(V/name)['passed'] and sha(V/name)==summary[name.replace('.json','_sha256')]
assert read(V/'strict_ff_clock_audit.json')['all_FF_CLK50']
expected=read(O/'source_freeze.json')['source55']
assert summary['source_sha256']==expected==read(O/'PROOF_BINDING.json')['source55']
assert {n:sha(A/'source'/n) for n in expected}==expected
assert {n:sha(R/'out/z_aw_fix_20261026/compact_aw_v13/canonical/source'/n) for n in expected}==expected
assert sha(A/'source/impl/gwsynthesis/acg720_ano_port.vg')==summary['netlist_sha256']
hist={}
for tag in ['v13','v13_map1']:
    vg=R/f'out/z_aw_fix_20261026/compact_aw_{tag}/build_attempt_01/source/impl/gwsynthesis/acg720_ano_port.vg'
    kinds={'LUT'+str(i) for i in range(1,9)}
    histogram=Counter(line.split()[0] for line in vg.read_text().splitlines() if line.startswith('  LUT') and line.split()[0] in kinds)
    hist[tag]={'VG_sha256':sha(vg),'unflattened_definition_LUT_histogram':dict(sorted(histogram.items()))}
assert hist['v13']['unflattened_definition_LUT_histogram'].get('LUT5')==1303
assert hist['v13_map1']['unflattened_definition_LUT_histogram'].get('LUT5',0)==0
result={'sealed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'passed_SYN_only':True,
    'vendor_actual_wait':vendor['actual_p_wait'],'runner_actual_wait':root['actual_p_wait'],
    'source55':expected,'netlist_sha256':summary['netlist_sha256'],'resources':summary['resources'],
    'definition_histograms':hist,'physical_started':False,
    'scope':'Same exact proven RTL55, new actual map1 netlist and mapped audits. Histograms count module definitions, not flattened physical occupancy. No route/STA/hardware qualification.',
    'decision':'Retain as a packing alternative: measured physical-equivalent LUT resource +1, FF/ALU/DSP/BSRAM unchanged, definitions no longer use LUT5. Packing/routing benefit is only a hypothesis until a physical trial.'}
output=O/'SYNTHESIS_RESULT.json';assert not output.exists()
output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
print(json.dumps({'SYN_only_passed':True,'vg_sha256':summary['netlist_sha256'],'histograms':hist,'physical_started':False},indent=2))
