"""Compare actual mapped fanout/selected cones after actual new SYN wait0 and strict audit; not STA."""
from pathlib import Path
import collections,hashlib,importlib.util,json,sys
sys.dont_write_bytecode=True
O=Path(__file__).resolve().parent;R=O.parents[3]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf8'))
new=R/'out/z_aw_fix_20261026/compact_aw_v14/build_attempt_01'
assert read(O/'runner_exit.json')['actual_p_wait']==0
audit=read(new/'verification/native_synthesis_audit.json');assert audit['passed']
old=R/'out/z_aw_fix_20261026/compact_aw_v4/build_attempt_01'
reader=R.parents[1]/'runtime_xy_pi_20261026/tools/read_cones.py'
assert sha(reader)=='a7d8faf9b8bd5c51b7bacf1ce54906c102df745b0d1c9913c2431ced9f5d09cc'
spec=importlib.util.spec_from_file_location('read_only_fanout_graph',reader);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
raw=R/'out/z_aw_fix_20261026/compact_aw_v4/physical_p3r0_01/source/impl/pnr/acg720_ano_port.tr'
assert sha(raw)=='c62307f8f84c2a0b742e1b5ba09211ad17158d9b6e6807e0c59146775ba80b82'
families=['core/fallback_control/active_fanout_limited', 'core/fallback_control/height_fallback_active_s','native_navigation/nav_vertical_ready_s','core_vertical_available_s','previous_pose_valid_s']
pathpairs=[('acc_time/output_az_3_s0','core/flight_state/flying_ms_3_s0','D'),
    ('mtf/metric/vy_x100_28_s0','staged_telemetry.extension_q_814_s0','D'),
    ('previous_pose_valid_s0','native_navigation/multiply_service/held_a_38_s0','D')]
runs={}
for name,attempt in [('original_max200',old),('new_local_hints',new)]:
    vg=attempt/'source/impl/gwsynthesis/acg720_ano_port.vg'
    assert sha(vg)==('e67bcab6336757e08645756258d39dd13726b452c392d470de4c900a159aaa8f' if name=='original_max200' else audit['netlist_sha256'])
    g=module.Graph(vg);loads=collections.defaultdict(set)
    for cell,c in g.cells.items():
        for pin,nets in c['pins'].items():
            if pin in ['Q','F','O','G','V','SUM','COUT']:continue
            for net in nets:loads[g.find(net)].add((cell,pin))
    selected={}
    for prefix in families:
        rows=[]
        for cell,c in g.cells.items():
            if not cell.startswith(prefix):continue
            output='Q' if c['type'].startswith('DFF') else 'F' if c['type'].startswith('LUT') else 'O'
            for net in c['pins'].get(output,[]):
                ls=loads[g.find(net)]
                rows.append({'cell':cell,'primitive':c['type'],'output_pin':output,'mapped_pin_loads':len(ls),
                    'clock_pin_loads':sum(pin in ['CLK','CLKA','CLKB','WCLK','RCLK'] for _,pin in ls)})
        selected[prefix]=rows
    paths=[]
    for source,target,pin in pathpairs:
        if source not in g.regs or target not in g.regs:
            paths.append({'source':source,'target':target+'/'+pin,'not_present_under_original_name':True});continue
        a=g.regs[source]['Q'][0];b=g.regs[target][pin][0];trace=g.trace(a,b)
        paths.append({'source':source,'target':target+'/'+pin,'overapprox_combinational_path':trace})
    runs[name]={'vg_sha256':sha(vg),'FF_count':len(g.regs),'selected_fanout':selected,'selected_topology':paths}
destination=O/'MAPPED_FANOUT_COMPARISON.json';assert not destination.exists()
destination.write_text(json.dumps({'scope':'Actual SYN netlist pin-load counts and overapproximate combinational topology only. No physical timing or routability claim. Selected families come from the original v4 raw setup paths; new physical reports remain mandatory.',
    'raw_basis_TR_sha256':sha(raw),'new_actual_SYN_audit_sha256':sha(new/'verification/native_synthesis_audit.json'),
    'graph_reader_sha256':sha(reader),'runs':runs},indent=2)+'\n',encoding='utf8')
print(json.dumps({n:{'FF':x['FF_count'],'fanout':{p:[{'cell':r['cell'],'pin_loads':r['mapped_pin_loads']} for r in rows] for p,rows in x['selected_fanout'].items()},
    'selected_combinational_depths':[r.get('overapprox_combinational_path',{}).get('depth') if r.get('overapprox_combinational_path') else None for r in x['selected_topology']]} for n,x in runs.items()},indent=2))
