"""Read exact audited VGs with the original graph helper; topology is not STA."""
from pathlib import Path
import collections,hashlib,importlib.util,json,sys
sys.dont_write_bytecode=True
O=Path(__file__).resolve().parent;R=O.parents[3]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf8'))
reader=R.parents[1]/'runtime_xy_pi_20261026/tools/read_cones.py'
assert sha(reader)=='a7d8faf9b8bd5c51b7bacf1ce54906c102df745b0d1c9913c2431ced9f5d09cc'
spec=importlib.util.spec_from_file_location('unchanged_mapped_composition_reader',reader);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
assert read(O/'SYNTHESIS_RESULT.json')['passed_SYN_only']
hashes={'v4':'e67bcab6336757e08645756258d39dd13726b452c392d470de4c900a159aaa8f','v17':'9a0194f0f1410b85472bdaddc70e1966f04e73c8ff70706316ccd91d5ea6ef6f','v18':'64e76270fe35298e698bfe5b14b9d9e267469f746d3c2382a8a15284c5942d4f','v19':'72808bc54f1a2b6c199a109cfa6f71e35139508d1573f10abba2bcd2774ae7af'}
def semantic(n):return '/'.join(s[1:] if s.startswith('\\') else s for s in n.split('/'))
pairs=[('acc_time/output_az_3_s0','core/flight_state/flying_ms_3_s0','D'),('acc_time/output_az_3_s0','core/flight_state/landing_ms_3_s0','D'),('previous_pose_valid_s0','native_navigation/multiply_service/held_a_38_s0','D'),('previous_pose_valid_s0','native_navigation/multiply_service/held_a_42_s0','D'),('mtf/metric/vy_x100_28_s0','staged_telemetry.extension_q_814_s0','D'),('mtf/metric/velocity_range_ok_s0','staged_telemetry.extension_q_814_s0','D')]
results={}
for label,expected in hashes.items():
    vg=R/f'out/z_aw_fix_20261026/compact_aw_{label}/build_attempt_01/source/impl/gwsynthesis/acg720_ano_port.vg';assert sha(vg)==expected
    g=module.Graph(vg);regs={}
    for n in g.regs:
        s=semantic(n);assert s not in regs;regs[s]=n
    loads=collections.defaultdict(set)
    for n,c in g.cells.items():
        for pin,nets in c['pins'].items():
            if pin in ['Q','F','O','G','V','SUM','COUT']:continue
            for net in nets:loads[g.find(net)].add((n,pin))
    paths=[]
    for source,target,pin in pairs:
        if source not in regs or target not in regs:paths.append({'source':source,'target':target+'/'+pin,'source_or_target_absent':True});continue
        a,b=regs[source],regs[target]
        paths.append({'source':a,'target':b+'/'+pin,'trace':g.trace(g.regs[a]['Q'][0],g.regs[b][pin][0])})
    selected=[]
    families=['previous_pose_valid_s','acc_time/output_az_range_ok','core/fallback_control/active_fanout_limited','core/fallback_control/height_fallback_active_s','core/fallback_collective_below_landing','core/auto_collective_below_landing','core/selected_collective_below_landing','mtf/metric/velocity_range_ok','mtf/metric_velocity_range_ok']
    for n,c in g.cells.items():
        if not any(semantic(n).startswith(p) for p in families):continue
        for pin in ['F','Q','O']:
            for net in c['pins'].get(pin,[]):selected.append({'cell':n,'primitive':c['type'],'output':pin,'loads':len(loads[g.find(net)])})
    guards=[]
    for source,pins in g.regs.items():
        if not semantic(source).startswith('acc_time/output_az_range_ok'):continue
        reached=g.paths(pins['Q'][0]);endpoints=[]
        for target,tp in g.regs.items():
            if not semantic(target).startswith(('core/flight_state/flying_ms_','core/flight_state/landing_ms_')):continue
            for pin in ['D','CE','RESET','SET']:
                for net in tp.get(pin,[]):
                    trace=reached.get(g.find(net))
                    if trace:endpoints.append({'endpoint':target+'/'+pin,'depth':trace[0],'cells':trace[1]})
        endpoints.sort(key=lambda x:(-x['depth'],x['endpoint']))
        guards.append({'source':source,'reachable_landing_FSM_endpoints':len(endpoints),'deepest_paths':endpoints[:4]})
    results[label]={'VG_sha256':expected,'FF_count':len(g.regs),'selected_driver_loads':selected,'selected_paths':paths,'AZ_predicate_to_landing_FSM':guards}
out={'scope':'Exact mapped combinational graph overapproximation and output pin loads only. Null trace means no path in this graph; depths/loads do not establish timing or routability. Original20ns/50MHz full physical gates mandatory.',
     'graph_reader_sha256':sha(reader),'results':results,'v19_resources_vs_v4':read(R/'out/z_aw_fix_20261026/compact_aw_v19/build_attempt_01/verification/resource_comparison.json')['resources'],
     'VY_source_scope':'v19 preserves v17/v4 VY numeric path; only v18 has the separately proved VY range publication bit. No VY source edit is introduced in v19.'}
dest=O/'MAPPED_AZ_POSE_VY_TOPOLOGY.json';assert not dest.exists();dest.write_text(json.dumps(out,indent=2)+'\n',encoding='utf8',newline='\n')
summary={label:{'FF':row['FF_count'],'path_depths':[p.get('trace',{}).get('depth') if p.get('trace') else None for p in row['selected_paths']],
                'AZ_predicate_FFs':[{'source':p['source'],'deepest':p['deepest_paths'][0]['depth'] if p['deepest_paths'] else None} for p in row['AZ_predicate_to_landing_FSM']],
                'previous_pose_output_loads':[p['loads'] for p in row['selected_driver_loads'] if semantic(p['cell']).startswith('previous_pose_valid_s')]} for label,row in results.items()}
print(json.dumps(summary,indent=2))
