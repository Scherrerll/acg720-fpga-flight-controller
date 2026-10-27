"""Resolve every previous_pose_valid FF copy to exact shared-math target names."""
from pathlib import Path
import hashlib,importlib.util,json,sys
sys.dont_write_bytecode=True
O=Path(__file__).resolve().parent;R=O.parents[3]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
reader=R.parents[1]/'runtime_xy_pi_20261026/tools/read_cones.py'
assert sha(reader)=='a7d8faf9b8bd5c51b7bacf1ce54906c102df745b0d1c9913c2431ced9f5d09cc'
spec=importlib.util.spec_from_file_location('unchanged_pose_copy_graph',reader);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
semantic=lambda n:'/'.join(s[1:] if s.startswith('\\') else s for s in n.split('/'))
hashes={'v4':'e67bcab6336757e08645756258d39dd13726b452c392d470de4c900a159aaa8f','v17':'9a0194f0f1410b85472bdaddc70e1966f04e73c8ff70706316ccd91d5ea6ef6f','v19':'72808bc54f1a2b6c199a109cfa6f71e35139508d1573f10abba2bcd2774ae7af'}
results={}
for v,h in hashes.items():
    vg=R/f'out/z_aw_fix_20261026/compact_aw_{v}/build_attempt_01/source/impl/gwsynthesis/acg720_ano_port.vg';assert sha(vg)==h
    g=module.Graph(vg);sources=[n for n in g.regs if semantic(n).startswith('previous_pose_valid_s')]
    targets=[n for n in g.regs if semantic(n).startswith(('native_navigation/multiply_service/held_a_38_','native_navigation/multiply_service/held_a_42_'))]
    assert sources and targets
    rows=[]
    for src in sources:
        reached=g.paths(g.regs[src]['Q'][0])
        for target in targets:
            for net in g.regs[target].get('D',[]):
                trace=reached.get(g.find(net));rows.append({'actual_source':src,'actual_target':target+'/D','trace':None if trace is None else {'depth':trace[0],'cells':trace[1]}})
    results[v]={'VG_sha256':h,'source_copies':sources,'exact_targets':targets,'paths':rows}
dest=O/'MAPPED_PREVIOUS_POSE_COPY_PATHS.json';assert not dest.exists()
dest.write_text(json.dumps({'scope':'Mapped topology only; every actual previous_pose_valid source copy considered, no inferred generated rename, no timing qualification.','graph_reader_sha256':sha(reader),'results':results},indent=2)+'\n',encoding='utf8',newline='\n')
print(json.dumps({v:[{'source':r['actual_source'],'target':r['actual_target'],'depth':r['trace']['depth'] if r['trace'] else None} for r in x['paths']] for v,x in results.items()},indent=2))
