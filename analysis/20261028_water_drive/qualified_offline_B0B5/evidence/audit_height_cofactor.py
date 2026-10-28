"""Compare tracked LUT/ALU/mux paths from published geometry height to core CE."""
from pathlib import Path
import argparse,hashlib,importlib.util,json
GRAPH_READER=Path('C:/Users/ScherrerL/Desktop/apple/runtime_xy_pi_20261026/tools/read_cones.py')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def inspect(netlist):
    spec=importlib.util.spec_from_file_location('height_graph_reader',GRAPH_READER)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    graph=module.Graph(netlist)
    sources=[n for n,c in graph.cells.items() if n.startswith('native_navigation/geometry/height_mm') and c['type'].startswith('DFF')]
    targets=[(n,pin,net) for n,c in graph.cells.items() if n.startswith('core/') and c['type'].startswith('DFF') for pin in ('CE','RESET','SET') for net in c['pins'].get(pin,[])]
    assert sources and len(targets)>1000,(sources,len(targets))
    hits=[]
    for source in sources:
        paths=graph.paths(graph.cells[source]['pins']['Q'][0])
        for target,pin,net in targets:
            path=paths.get(graph.find(net))
            if path:hits.append(dict(source=source,target=target+'/'+pin,depth=path[0]))
    return dict(netlist_sha256=sha(netlist),height_registers=sources,target_pin_count=len(targets),
        reachable_pin_pairs=len(hits),maximum_depth=max((x['depth'] for x in hits),default=None),
        longest_examples=sorted(hits,key=lambda x:-x['depth'])[:20])

def audit(netlist,before):
    old=inspect(before);new=inspect(netlist)
    assert old['reachable_pin_pairs']>0 and new['reachable_pin_pairs']==0,(old['reachable_pin_pairs'],new['reachable_pin_pairs'])
    return dict(passed=True,before=old,after=new,graph_reader_sha256=sha(GRAPH_READER),
        scope='Tracked combinational LUT/ALU/mux topology, stops at FFs/unsupported primitives. Not formal verification or physical timing qualification. Bounded-producer source proof and complete navigation cycle comparison are separate required evidence.')

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('netlist',type=Path);parser.add_argument('before',type=Path);parser.add_argument('output',type=Path);args=parser.parse_args()
    result=audit(args.netlist,args.before);args.output.write_text(json.dumps(result,indent=2),encoding='utf8')
    print('PASS height->core control topology:',result['before']['reachable_pin_pairs'],'to',result['after']['reachable_pin_pairs'],'tracked pin pairs')
