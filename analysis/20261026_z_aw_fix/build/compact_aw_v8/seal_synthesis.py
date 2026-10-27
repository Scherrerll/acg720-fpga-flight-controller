"""Archive completed v8 SYN receipts and exact VG digest, once."""
from pathlib import Path
import datetime,gzip,hashlib,json
O=Path(__file__).resolve().parent;R=O.parents[3]
A=R/'out/z_aw_fix_20261026/compact_aw_v8/build_attempt_01';V=A/'verification'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text())
summary=read(V/'synthesis_summary.json');vendor=read(V/'synthesis_exit.json');runner=read(O/'runner_exit.json')
assert summary['passed'] and vendor['actual_p_wait']==runner['actual_p_wait']==0
assert vendor['normal_wait_return'] and runner['normal_wait_return']
assert sha(V/'synthesis.log')==vendor['log_sha256']
expected=read(O/'source_freeze.json')['source55']; assert expected==summary['source_sha256']
for root in [A/'source',R/'out/z_aw_fix_20261026/compact_aw_v8/canonical/source']:
    assert {p:sha(root/p) for p in expected}==expected
vg=A/'source/impl/gwsynthesis/acg720_ano_port.vg'
assert sha(vg)==summary['netlist_sha256']=='5f3637446527bd5b1c83b20c5493027ca7101d664b845630104d9a51b035a33e'
D=O/'synthesis_receipts';assert not D.exists();D.mkdir();items={}
paths=[V/n for n in ['build_input.json','synthesis_input.json','synthesis_summary.json','synthesis_exit.json','synthesis.log','mapped_audit.json','gain_port_audit.json','strict_ff_clock_audit.json','resource_comparison.json']]
paths += [vg,A/'source/impl/gwsynthesis/acg720_ano_port_syn_rsc.xml']
for p in paths:
    dest=D/p.name
    if p.suffix in ['.log','.vg','.xml']:
        dest=dest.with_suffix(dest.suffix+'.gz')
        with gzip.GzipFile(filename=str(dest),mode='wb',mtime=0) as f:f.write(p.read_bytes())
    else:dest.write_bytes(p.read_bytes())
    items[str(p.relative_to(R))]={'sha256':sha(p),'bytes':p.stat().st_size,'preserved':str(dest.relative_to(R)),'preserved_sha256':sha(dest)}
result={'sealed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'SYN passed, PNR not started, not qualified for installation',
    'source55':expected,'netlist_sha256':sha(vg),'vendor_actual_wait':0,'runner_actual_wait':0,'resources':summary['resources'],
    'proofs_sha256':sha(O/'proofs_completion02/results.json'),'proof_runner_exit_sha256':sha(O/'proofs_completion02/runner_exit.json'),
    'clock_radio_gain_18ports_passed':True,'PNR_started':False,'physical_qualified':False,'artifacts':items}
out=O/'SYNTHESIS_RESULT.json';assert not out.exists();out.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'vg_sha256':sha(vg),'vendor_wait':0,'runner_wait':0,'source55':55,'archived_receipts':len(items)},indent=2))
