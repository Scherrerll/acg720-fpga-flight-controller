"""Read-only actual mapped topology comparison; this is never STA qualification."""
from pathlib import Path
import hashlib, importlib.util, json, sys
sys.dont_write_bytecode=True
O=Path(__file__).resolve().parent;R=O.parents[3]
reader=R.parents[1]/'runtime_xy_pi_20261026/tools/read_cones.py'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(reader)=='a7d8faf9b8bd5c51b7bacf1ce54906c102df745b0d1c9913c2431ced9f5d09cc'
spec=importlib.util.spec_from_file_location('v13_readonly_cones',reader)
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
normalize=lambda n:n.lstrip('\\').replace('.','/')
variants={}
for tag in ['v13','v13_map1']:
    vg=R/f'out/z_aw_fix_20261026/compact_aw_{tag}/build_attempt_01/source/impl/gwsynthesis/acg720_ano_port.vg'
    g=module.Graph(vg)
    sources=[n for n in g.regs if normalize(n)=='mtf/age_ms_21_s1' or normalize(n).startswith(('mtf/age_below_1000_','mtf/age_below_200_'))]
    assert any(normalize(n)=='mtf/age_ms_21_s1' for n in sources)
    assert len(sources)==3
    targets=[n for n in g.regs if normalize(n) in ['staged_telemetry/extension_q_814_s0','staged_telemetry/extension_q_97_s6']
             or normalize(n).startswith(('mtf/age_below_1000_','mtf/age_below_200_'))]
    assert len(targets)==4
    traces={}
    for source in sources:
        pins=g.regs[source];assert len(pins['Q'])==1
        paths=g.paths(pins['Q'][0]);dest={}
        for target in targets:
            for pin in ['D','CE','RESET','SET']:
                for net in g.regs[target].get(pin,[]):
                    trace=paths.get(g.find(net))
                    if trace:dest[target+'/'+pin]={'depth':trace[0],'cells':trace[1]}
        traces[source]={'CLK':pins['CLK'],'paths':dest}
    variants[tag]={'VG_sha256':sha(vg),'sources':traces}
output=O/'MAPPED_MTF_AGE_CONE_REVIEW.json';assert not output.exists()
output.write_text(json.dumps({'scope':'All LUT input arcs and other combinational arcs are included. Topological overapproximation only, not sensitized paths or delay. Full physical gates are separate.',
    'graph_reader_sha256':sha(reader),'variants':variants},indent=2)+'\n')
print(json.dumps({tag:{source:{target:entry['depth'] for target,entry in data['paths'].items()}
                      for source,data in variant['sources'].items()} for tag,variant in variants.items()},indent=2))
