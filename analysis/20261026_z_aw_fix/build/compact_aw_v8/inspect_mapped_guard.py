"""Read mapped guard cones only; depth does not establish timing qualification."""
from pathlib import Path
import hashlib,importlib.util,json,sys
sys.dont_write_bytecode=True
O=Path(__file__).resolve().parent;R=O.parents[3]
reader=R.parents[1]/'runtime_xy_pi_20261026/tools/read_cones.py'
spec=importlib.util.spec_from_file_location('guard_cone_read_only',reader);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
out={}
for tag in ['v7','v8']:
    vg=R/f'out/z_aw_fix_20261026/compact_aw_{tag}/build_attempt_01/source/impl/gwsynthesis/acg720_ano_port.vg'
    g=m.Graph(vg)
    names=[n for n in g.regs if n.startswith('acc_time/output_az_') and ('range_ok' in n if tag=='v8' else n in ['acc_time/output_az_3_s0','acc_time/output_az_4_s0'])]
    assert names,(tag,'missing guard/source FF')
    rows=[]
    for name in names:
        p=g.regs[name];assert len(p['Q'])==1
        reached=g.paths(p['Q'][0]);targets=[]
        for n,pins in g.regs.items():
            if n.startswith(('native_navigation/diagnostic_q_','core/manual_angles/','core/flight_state/flying_ms_')):
                for pin in ['D','CE','RESET','SET']:
                    for net in pins.get(pin,[]):
                        result=reached.get(g.find(net))
                        if result:targets.append({'endpoint':n+'/'+pin,'combinational_cells':result[0],'cells':result[1]})
        targets.sort(key=lambda x:(-x['combinational_cells'],x['endpoint']))
        rows.append({'source_FF':name,'reachable_selected_endpoints':len(targets),'deepest_selected_paths':targets[:3]})
    out[tag]={'vg_sha256':sha(vg),'register_count':len(g.regs),'source_paths':rows}
assert any('range_ok' in row['source_FF'] for row in out['v8']['source_paths'])
destination=O/'MAPPED_GUARD_CONES.json';assert not destination.exists()
destination.write_text(json.dumps({'scope':'Mapped register and combinational topology only; no delay/STA/physical claim.',
    'graph_reader_sha256':sha(reader),'runs':out},indent=2)+'\n')
print(json.dumps({tag:[{'source':row['source_FF'],'deepest_cells':row['deepest_selected_paths'][0]['combinational_cells'] if row['deepest_selected_paths'] else None,'selected_endpoints':row['reachable_selected_endpoints']} for row in item['source_paths']] for tag,item in out.items()},indent=2))
