"""Archive actual timing-goal SYN and compare the known late control cones."""
from pathlib import Path
import collections,datetime,gzip,hashlib,importlib.util,json,re,sys
sys.dont_write_bytecode=True
O=Path(__file__).resolve().parent;R=O.parents[3]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text())
A=R/'out/z_aw_fix_20261026/compact_aw_v4_timing/build_attempt_01';V=A/'verification'
s=read(V/'synthesis_summary.json');ex=read(V/'synthesis_exit.json');rx=read(O/'runner_exit.json')
assert s['passed'] and ex['actual_p_wait']==rx['actual_p_wait']==0 and ex['normal_wait_return'] and rx['normal_wait_return']
expected=read(O/'source_freeze.json')['source55']
assert expected==s['source_sha256'] and {p:sha(A/'source'/p) for p in expected}==expected
assert {p:sha(R/'out/z_aw_fix_20261026/compact_aw_v4/canonical/source'/p) for p in expected}==expected
input=read(V/'build_input.json');assert input['synthesis_options']=={'map_option':2,'replicate_resources':0,'opt_goal':'timing'}
tcl=(A/'synth_only.tcl').read_text();assert 'set_option -opt_goal timing' in tcl and 'set_option -global_freq 50' in tcl and 'run pnr' not in tcl
vg=A/'source/impl/gwsynthesis/acg720_ano_port.vg';assert sha(vg)==s['netlist_sha256']
reader=R.parents[1]/'runtime_xy_pi_20261026/tools/read_cones.py'
spec=importlib.util.spec_from_file_location('goal_compare_readonly',reader);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
cones={}
for tag,path in [('area',R/'out/z_aw_fix_20261026/compact_aw_v4/build_attempt_01/source/impl/gwsynthesis/acg720_ano_port.vg'),('timing',vg)]:
    g=m.Graph(path);loads=collections.defaultdict(set)
    for n,c in g.cells.items():
        for pin,nets in c['pins'].items():
            if pin not in ['Q','F','O','SUM','COUT','G','V']:
                for net in nets:loads[g.find(net)].add((n,pin))
    sources=[n for n in g.regs if re.fullmatch(r'acc_time/output_az_[34]_s\d+',n)]
    assert sources
    rows=[]
    for n in sources:
        q=g.regs[n]['Q'][0];reach=g.paths(q)
        for target,pins in g.regs.items():
            if not target.startswith('core/flight_state/flying_ms_'):continue
            for pin in ['D','CE','RESET','SET']:
                for net in pins.get(pin,[]):
                    if g.find(net) not in reach:continue
                    depth,cells=reach[g.find(net)];fanouts=[len(loads[g.find(q)])]
                    for cell in cells:
                        for p in ['F','O','SUM','COUT']:
                            fanouts.extend(len(loads[g.find(x)]) for x in g.cells[cell]['pins'].get(p,[]))
                    rows.append({'source':n,'endpoint':target+'/'+pin,'combinational_cells':depth,'max_net_pin_fanout_on_path':max(fanouts),'cells':cells})
    rows.sort(key=lambda x:(-x['combinational_cells'],-x['max_net_pin_fanout_on_path'],x['endpoint']))
    cones[tag]={'VG_sha256':sha(path),'mapped_FF':len(g.regs),'selected_reachable_paths':len(rows),'deepest_paths':rows[:3]}
D=O/'synthesis_receipts';assert not D.exists();D.mkdir();items={}
for p in [V/n for n in ['build_input.json','synthesis_input.json','synthesis_summary.json','synthesis_exit.json','synthesis.log','mapped_audit.json','gain_port_audit.json','strict_ff_clock_audit.json','resource_comparison.json']]+[vg,A/'source/impl/gwsynthesis/acg720_ano_port_syn_rsc.xml',A/'synth_only.tcl']:
    dest=D/p.name
    if p.suffix in ['.log','.vg','.xml']:
        dest=dest.with_suffix(dest.suffix+'.gz')
        with gzip.GzipFile(filename=str(dest),mode='wb',mtime=0) as f:f.write(p.read_bytes())
    else:dest.write_bytes(p.read_bytes())
    items[str(p.relative_to(R))]={'sha256':sha(p),'bytes':p.stat().st_size,'preserved':str(dest.relative_to(R)),'preserved_sha256':sha(dest)}
result={'sealed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'passed_SYN_only':True,'physical_qualified':False,
    'source55':expected,'VG_sha256':sha(vg),'actual_vendor_wait':0,'actual_runner_wait':0,'effective_synthesis_options':input['synthesis_options'],
    'period_ns':20,'resources':s['resources'],'mapped_cones':cones,'cone_scope':'Topological overapproximation only, not delay/sensitization/STA proof.',
    'official_Tcl_pdf_pages':[29,30],'artifacts':items}
out=O/'SYNTHESIS_RESULT.json';assert not out.exists();out.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'actual_vendor_runner_wait':[0,0],'VG_sha256':sha(vg),'top_resource_delta':s['resources']['acg720_ano_port']['delta'],
    'cones':{tag:{'paths':a['selected_reachable_paths'],'deepest_cells':a['deepest_paths'][0]['combinational_cells'] if a['deepest_paths'] else None,
                   'path_max_fanout':a['deepest_paths'][0]['max_net_pin_fanout_on_path'] if a['deepest_paths'] else None} for tag,a in cones.items()}},indent=2))
