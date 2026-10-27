"""Measured primitive pin loads only; no timing or functional-copy prediction."""
from pathlib import Path
import collections,hashlib,importlib.util,re
R=Path(__file__).resolve().parents[4]
GRAPH=R.parents[1]/'runtime_xy_pi_20261026/tools/read_cones.py'
GRAPH_SHA='a7d8faf9b8bd5c51b7bacf1ce54906c102df745b0d1c9913c2431ced9f5d09cc'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def measure(vg):
    assert sha(GRAPH)==GRAPH_SHA
    spec=importlib.util.spec_from_file_location('unchanged_fanout_graph',GRAPH);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);g=m.Graph(vg)
    loads=collections.defaultdict(list)
    outputs={'Q','F','O','G','V','SUM','COUT','DO','DOUT'}
    for name,cell in g.cells.items():
        for pin,nets in cell['pins'].items():
            if pin not in outputs:
                for net in nets:loads[g.find(net)].append({'cell':name,'pin':pin,'type':cell['type']})
    indices={n:p for n,p in g.regs.items() if re.fullmatch(r'core/imu/estimator/index_\d+_s\d+(?:_\d+)?',n)}
    index_roots=collections.defaultdict(list)
    for n,p in indices.items():
        for net in p.get('Q',[]):index_roots[g.find(net)].append(n)
    def entry(name,cell,pin):
        out=cell['pins'].get(pin,[])
        fan=[x for net in out for x in loads[g.find(net)]]
        return {'cell':name,'primitive':cell['type'],'output_pin':pin,'canonical_output_nets':[g.find(n) for n in out],
                'mapped_pin_loads':len(fan),'unique_load_cells':len({x['cell'] for x in fan}),
                'input_pins':{p:[{'net':g.find(n),'index_FF_drivers':index_roots.get(g.find(n),[])} for n in nets] for p,nets in cell['pins'].items() if p.startswith('I')},
                'load_pins':fan}
    named=[entry(n,c,'F') for n,c in g.cells.items() if n.startswith('core/imu/estimator/n8507_s') and c['type'].startswith('LUT')]
    direct=[entry(n,c,'F') for n,c in g.cells.items() if n.startswith('core/imu/estimator/') and c['type'].startswith('LUT') and any(g.find(net) in index_roots for p,nets in c['pins'].items() if p.startswith('I') for net in nets)]
    registers=[entry(n,g.cells[n],'Q') for n in indices]
    return {'VG_sha256':sha(vg),'primitive_cells':len(g.cells),'FF_count':len(g.regs),
            'index_registers':registers,'named_n8507_decoder_family':named,'direct_index_driven_LUTs':direct,
            'named_decoder_family_count':len(named),'named_decoder_max_pin_loads':max((x['mapped_pin_loads'] for x in named),default=None),
            'direct_index_LUT_max_pin_loads':max((x['mapped_pin_loads'] for x in direct),default=None),
            'scope':'Actual flattened primitive pin loads and exact observed instance names only. A generated-name family count is descriptive and does not prove replicas are Boolean-equivalent. Missing/renamed families are reported, not inferred. No STA or routability claim; no fanout<=100 acceptance assumption.'}
