"""Inspect the mapped same-cycle predicate cache; no device access."""
from pathlib import Path
import argparse, hashlib, importlib.util, json

GRAPH_READER=Path('C:/Users/ScherrerL/Desktop/apple/runtime_xy_pi_20261026/tools/read_cones.py')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def audit(netlist):
    spec=importlib.util.spec_from_file_location('water_mtf_graph',GRAPH_READER)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    graph=module.Graph(netlist)
    names=[n for n,c in graph.cells.items() if 'payload_range_ok_q' in n and c['type'].startswith('DFF')]
    assert len(names)==1,names
    cache=graph.cells[names[0]];frame=graph.cells['mtf/parser/raw_frame_118_s0']
    for pin in ('CLK','RESET','CE'):
        assert [graph.find(n) for n in cache['pins'][pin]]==[graph.find(n) for n in frame['pins'][pin]],pin
    target=graph.cells['core/manual_angles/pending_dt_10_s0']['pins']['CE'][0]
    cached_path=graph.trace(cache['pins']['Q'][0],target)
    assert cached_path and cached_path['depth']>0
    flow_names=[n for n,c in graph.cells.items() if 'payload_flow_ok_q' in n and c['type'].startswith('DFF')]
    assert len(flow_names)<=1,flow_names
    flow_audit=None
    if flow_names:
        flow=graph.cells[flow_names[0]]
        for pin in ('CLK','RESET','CE'):
            assert [graph.find(n) for n in flow['pins'][pin]]==[graph.find(n) for n in frame['pins'][pin]],pin
        flow_output=graph.trace(flow['pins']['Q'][0],'mtf/flow_ok');assert flow_output
        flow_audit=dict(register=flow_names[0],cell=flow,clock_reset_enable_identical=True,
            cache_to_flow_output=flow_output,cache_to_manual_angles_ce=graph.trace(flow['pins']['Q'][0],target))
    return dict(passed=True,netlist_sha256=sha(netlist),graph_reader_sha256=sha(GRAPH_READER),
        register=names[0],cell=cache,frame_register='mtf/parser/raw_frame_118_s0',
        clock_reset_enable_identical=True,cache_to_manual_angles_ce=cached_path,
        flow_cache=flow_audit,
        remaining_raw_distance_to_ce=graph.trace(frame['pins']['Q'][0],target),
        scope='Mapped topology only. Raw distance still feeds other geometry predicates; this is not a claim that every critical path was shortened or timing passed.')

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('netlist',type=Path);parser.add_argument('output',type=Path)
    args=parser.parse_args();result=audit(args.netlist)
    args.output.write_text(json.dumps(result,indent=2),encoding='utf8')
    print('PASS mapped predicate cache:',result['register'],'same CLK/RESET/CE as raw frame; cached CE depth',result['cache_to_manual_angles_ce']['depth'])
