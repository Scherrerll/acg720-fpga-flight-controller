"""Exact audited v15 mapped logic review; topology is not STA."""
from pathlib import Path
import collections,hashlib,importlib.util,json,sys
O=Path(__file__).resolve().parent;R=O.parents[3]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf8'))
new=R/'out/z_aw_fix_20261026/compact_aw_v17/build_attempt_01'
assert read(O/'runner_exit.json')['actual_p_wait']==0
audit=read(new/'verification/native_synthesis_audit.json');assert audit['passed']
old=R/'out/z_aw_fix_20261026/compact_aw_v4/build_attempt_01'
reader=R.parents[1]/'runtime_xy_pi_20261026/tools/read_cones.py'
assert sha(reader)=='a7d8faf9b8bd5c51b7bacf1ce54906c102df745b0d1c9913c2431ced9f5d09cc'
spec=importlib.util.spec_from_file_location('mapped_landing_comparison',reader);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
families=['core/fallback_control/active_fanout_limited','core/fallback_collective_below_landing','core/auto_collective_below_landing','core/selected_collective_below_landing','core/fallback_control/height_fallback_active_s','previous_pose_valid_s']
pairs=[('acc_time/output_az_3_s0','core/flight_state/flying_ms_3_s0','D'),('acc_time/output_az_3_s0','core/flight_state/landing_ms_3_s0','D'),('previous_pose_valid_s0','native_navigation/multiply_service/held_a_38_s0','D')]
results={}
for label,attempt in [('v4',old),('v17',new)]:
    vg=attempt/'source/impl/gwsynthesis/acg720_ano_port.vg';assert sha(vg)==('e67bcab6336757e08645756258d39dd13726b452c392d470de4c900a159aaa8f' if label=='v4' else audit['netlist_sha256'])
    g=module.Graph(vg);loads=collections.defaultdict(set)
    for n,c in g.cells.items():
        for pin,nets in c['pins'].items():
            if pin in ['Q','F','O','G','V','SUM','COUT']:continue
            for net in nets:loads[g.find(net)].add((n,pin))
    cells=[]
    for n,c in g.cells.items():
        if not any(n.startswith(p) for p in families):continue
        for pin in ['F','Q','O']:
            for net in c['pins'].get(pin,[]):cells.append(dict(cell=n,primitive=c['type'],output=pin,loads=len(loads[g.find(net)])))
    paths=[]
    for source,target,pin in pairs:
        if source in g.regs and target in g.regs:
            paths.append(dict(source=source,target=target+'/'+pin,trace=g.trace(g.regs[source]['Q'][0],g.regs[target][pin][0])))
        else:paths.append(dict(source=source,target=target+'/'+pin,missing_original_instance_name=True))
    results[label]=dict(vg_sha256=sha(vg),FF_count=len(g.regs),selected_cells=cells,selected_paths=paths)
out=dict(scope='Actual mapped graph overapproximate depth and loads only, not timing or routability. Original20ns/50MHz physical gates remain mandatory.',results=results,resources=read(new/'verification/resource_comparison.json')['resources'],resource_label_correction='The inherited local_fanout_map2 key denotes v17: v15 pre-mux landing predicate plus active-driver syn_maxfan50 and previous_pose_valid syn_maxfan10 hints. Actual mapped drivers must be checked below.')
dest=O/'MAPPED_LANDING_COMPARISON.json';assert not dest.exists();dest.write_text(json.dumps(out,indent=2)+'\n',encoding='utf8')
print(json.dumps({n:dict(FF=r['FF_count'],selected_cells=r['selected_cells'],depths=[x.get('trace',{}).get('depth') if x.get('trace') else None for x in r['selected_paths']]) for n,r in results.items()},indent=2))
