"""Independent sealed fan100 SYN result and actual mapped-load review. Read-only inputs."""
from pathlib import Path
import collections,datetime,hashlib,importlib.util,json,re,sys,xml.etree.ElementTree as ET
sys.dont_write_bytecode=True
O=Path(__file__).resolve().parent;R=O.parents[2];B=R/'analysis/20261026_z_aw_fix/build';T=B/'compact_aw_v22_fan100';STD=B/'compact_aw_v22'
ROOT=R/'out/z_aw_fix_20261026/compact_aw_v22_fan100';A=ROOT/'build_attempt_01';S=A/'source';V=A/'verification';C=R/'out/z_aw_fix_20261026/compact_aw_v22/canonical/source'
PARENT=C.parent.parent/'build_attempt_01';seen={}
def sha(p):
    p=Path(p)
    for part in p.parts:
        n=part.lower().rstrip(' .');assert not n.startswith('.env') and not n.endswith('.env') and '.env' not in [x.lower() for x in Path(n).suffixes]
    for q in [p,*p.parents]:assert not q.is_symlink() and not (hasattr(q,'is_junction') and q.is_junction())
    h=hashlib.sha256(p.read_bytes()).hexdigest();key=str(p.resolve());assert key not in seen or seen[key]==h,(key,'changed during review');seen[key]=h;return h
def read(p):sha(p);return json.loads(Path(p).read_text(encoding='utf8'))
def bind(p,h):assert sha(p)==h,str(p)
def load(name,p):
    sha(p);spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
contract=load('read_only_fan100_result_contract',T/'input_contract.py');base=contract.validate();gate=contract.review_gate();expected=base['source55']
prior=read(R/'analysis/agent_reviews/v22_fan100_independent_20261027/REVIEW.json');assert prior['approved_preparation'] and prior['source55']==expected
for n,key in [('SYNTHESIS_PREPARATION.json','SYNTHESIS_PREPARATION_sha256'),('SOURCE_REUSE_BINDING.json','SOURCE_REUSE_BINDING_sha256')]:bind(T/n,prior[key])
for n,h in gate['reviewed_scripts_sha256'].items():bind(T/n,h)
for p,h in read(T/'SOURCE_REUSE_BINDING.json')['bound_inputs'].items():bind(p,h)
assert len(expected)==55 and {n:sha(C/n) for n in expected}=={n:sha(S/n) for n in expected}==expected
assert not (ROOT/'canonical').exists() and not (S/'impl/pnr').exists()
syn=read(T/'SYNTHESIS_RESULT.json');summary=read(V/'synthesis_summary.json');manifest=read(A/'synthesis_freeze_manifest_final.json')
assert syn['passed_SYN_only'] is True and syn['source55']==expected and syn['vendor_actual_wait']==syn['audit_actual_wait']==syn['runner_actual_wait']==0
bind(V/'synthesis_summary.json',syn['synthesis_summary_sha256']);bind(A/'synthesis_freeze_manifest_final.json',syn['synthesis_freeze_sha256'])
assert manifest['source_sha256']==expected and manifest['vendor_actual_wait']==manifest['audit_actual_wait']==manifest['runner_actual_wait']==0
root=read(T/'runner_exit.json');vendor=read(V/'synthesis_exit.json');audit=read(V/'audit_exit.json')
for j in [root,vendor,audit]:assert j.get('normal_wait_return') is True and type(j.get('actual_p_wait')) is int and j['actual_p_wait']==0
bind(T/'runner_exit.json',manifest['root_exit_sha256'])
assert root['command']==[sys.executable,'-B','-X','utf8',str(T/'run_synthesis.py')]
bind(T/'run_synthesis.py',root['runner_sha256']);bind(T/'launch_synthesis_hidden.py',root['supervisor_sha256'])
for stream in ['stdout','stderr']:bind(T/f'runner.{stream}.log',root[f'{stream}_sha256'])
for phase,j in [('synthesis',vendor),('audit',audit)]:
    assert j['stage']==phase and j['parent_pid']==root['pid'] and Path(j['cwd'])==S and Path(j['log'])==V/f'{phase}.log'
    bind(V/f'{phase}.log',j['log_sha256']);assert j['runner_sha256']=='abb5246c203b73c111f80bc91f8db6c8220463f7d4c5cf48dbfe2167ef49db84'
assert vendor['command']==['C:\\Gowin\\Gowin_V1.9.12.04_x64\\IDE\\bin\\gw_sh.exe',str(A/'synth_only.tcl')]
assert audit['command']==[sys.executable,'-B','-X','utf8',str(T/'audit_synthesis_only.py')]
assert 'SYNTHESIS_COMMAND_RETURNED_EOF' in (V/'synthesis.log').read_text(errors='replace')
assert summary['passed'] is True and summary['source_sha256']==expected and summary['actual_vendor_wait']==summary['actual_audit_wait']==0
for n,h in summary['artifacts_sha256'].items():bind(V/n,h)
native=read(V/'native_synthesis_audit.json');vg=S/'impl/gwsynthesis/acg720_ano_port.vg';parent_vg=PARENT/'source/impl/gwsynthesis/acg720_ano_port.vg'
assert native['passed'] is True and native['source55']==expected and sha(vg)==native['netlist_sha256']==summary['netlist_sha256']==syn['netlist_sha256']=='bf2c2de81c82f16bd3c0badd8790aa0a4c216ad9bf8273bbcd1e79a3f997508e'
assert sha(parent_vg)==base['VG_sha256']==syn['parent_VG_sha256']
assert native['hook_pid']==audit['pid'] and native['hook_parent_pid']==root['pid'];bind(T/'audit_synthesis_only.py',native['hook_sha256'])
for n,h in native['artifacts_sha256'].items():bind(V/n,h)
mapped=read(V/'mapped_audit.json');gain=read(V/'gain_port_audit.json');clock=read(V/'strict_ff_clock_audit.json')
assert mapped['passed'] and mapped['source_sha256']==expected and mapped['netlist_sha256']==sha(vg)
assert gain['passed'] and gain['netlist_sha256']==sha(vg) and len(gain['top_ports'])==18 and gain['gains']['p']['init_wire']==1000 and gain['gains']['i']['init_wire']==350
assert clock['passed'] and clock['all_FF_CLK50'] and not clock['bad'] and clock['vg_sha256']==sha(vg)
inputs=read(V/'build_input.json');assert inputs['source_sha256']==expected and inputs['effective_option_delta']=={'max_fanout':{'from':200,'to':100}}
for p,h in {**inputs['bound_inputs'],**inputs['tools']}.items():bind(p,h)
recipe=load('read_only_actual_effective_recipe',T/'effective_recipe.py');assert (A/'synth_only.tcl').read_text()==recipe.make_recipe(S/'build.tcl')
assert sha(S/'build.tcl')==sha(C/'build.tcl')==expected['build.tcl']
for rel,x in manifest['artifacts'].items():
    p=A/rel;assert p.resolve().is_relative_to(A.resolve());bind(p,x['sha256']);assert p.stat().st_size==x['bytes']
actual_files={p.relative_to(A).as_posix() for p in A.rglob('*') if p.is_file() and 'tmp' not in p.relative_to(A).parts}
assert actual_files==set(manifest['artifacts'])|{'synthesis_freeze_manifest_final.json'}
# XML resource counts are parsed independently of the bound audit helper.
def xml_resources(path):
    sha(path);out={}
    def walk(n,prefix):
        name=prefix+n.attrib['name'];out[name]={k:int(v.split('(')[0]) for k,v in n.attrib.items() if k.startswith('T_')}
        for child in n:walk(child,name+'/')
    walk(ET.parse(path).getroot(),'');return out
before=xml_resources(parent_vg.with_name('acg720_ano_port_syn_rsc.xml'));after=xml_resources(vg.with_name('acg720_ano_port_syn_rsc.xml'))
resources=read(V/'resource_comparison.json');assert resources['source55']==expected and resources['parent_VG_sha256']==sha(parent_vg) and resources['current_VG_sha256']==sha(vg)
for name,x in resources['resources'].items():
    assert x['sealed_STD22_max200']==before[name] and x['same_source_fan100']==after[name]
    assert x['delta']=={k:after[name].get(k,0)-before[name].get(k,0) for k in before[name].keys()|after[name].keys()}
comparison=read(V/'mapped_fanout_comparison.json');assert comparison['source55']==expected
graph_path=R.parents[1]/'runtime_xy_pi_20261026/tools/read_cones.py';bind(graph_path,comparison['graph_reader_sha256'])
graph=load('read_only_result_primitive_graph',graph_path);outputs={'Q','F','O','G','V','SUM','COUT','DO','DOUT'}
def independently_check(path,reported):
    assert reported['VG_sha256']==sha(path);g=graph.Graph(path);assert reported['primitive_cells']==len(g.cells) and reported['FF_count']==len(g.regs)
    loads=collections.defaultdict(list)
    for name,cell in g.cells.items():
        for pin,nets in cell['pins'].items():
            if pin not in outputs:
                for net in nets:loads[g.find(net)].append((name,pin,cell['type']))
    indices={n:p for n,p in g.regs.items() if re.fullmatch(r'core/imu/estimator/index_\d+_s\d+(?:_\d+)?',n)}
    assert set(indices)=={x['cell'] for x in reported['index_registers']}
    index_roots={g.find(net) for p in indices.values() for net in p.get('Q',[])}
    direct={n for n,c in g.cells.items() if n.startswith('core/imu/estimator/') and c['type'].startswith('LUT') and any(g.find(net) in index_roots for p,nets in c['pins'].items() if p.startswith('I') for net in nets)}
    assert direct=={x['cell'] for x in reported['direct_index_driven_LUTs']}
    named={n for n,c in g.cells.items() if n.startswith('core/imu/estimator/n8507_s') and c['type'].startswith('LUT')}
    assert named=={x['cell'] for x in reported['named_n8507_decoder_family']}
    for item in reported['index_registers']+reported['named_n8507_decoder_family']+reported['direct_index_driven_LUTs']:
        cell=g.cells[item['cell']];roots=[g.find(n) for n in cell['pins'][item['output_pin']]]
        assert roots==item['canonical_output_nets'];pins=[x for root in roots for x in loads[root]]
        assert len(pins)==item['mapped_pin_loads'] and len({x[0] for x in pins})==item['unique_load_cells']
        assert collections.Counter(pins)==collections.Counter((x['cell'],x['pin'],x['type']) for x in item['load_pins'])
    # Inspect INIT parameters in the exact estimator module selected by hierarchy.
    typ='acg720_ano_port'
    for instance in ['core','imu','estimator']:
        choices=[child for child,inst,pins in g.modules[typ][1] if inst==instance];assert len(choices)==1;typ=choices[0]
    bodies={m[0]:m[1] for m in re.findall(r'^module\s+(\S+)\s*\(.*?\)\s*;(.*?)^endmodule',path.read_text(),re.S|re.M)};body=bodies[typ]
    def parameters(full):
        local=full.rsplit('/',1)[1]
        return tuple(sorted(re.findall(r'^defparam\s+'+re.escape(local)+r'\.([A-Za-z0-9_]+)\s*=\s*([^;]+);',body,re.M)))
    lut_signatures={}
    for name in sorted(named):
        c=g.cells[name];lut_signatures[name]={'type':c['type'],'parameters':parameters(name),'inputs':{p:[g.find(x) for x in nets] for p,nets in c['pins'].items() if p.startswith('I')}}
    assert len({json.dumps(x,sort_keys=True) for x in lut_signatures.values()})==1
    assert all(x['type']=='LUT2' and dict(x['parameters'])['INIT']=="4'h9" for x in lut_signatures.values())
    groups=collections.defaultdict(list)
    for name in indices:
        c=g.cells[name];sig=(c['type'],parameters(name),tuple(sorted((p,tuple(g.find(x) for x in nets)) for p,nets in c['pins'].items() if p!='Q')))
        groups[sig].append(name)
    return {'index_FF_count':len(indices),'index_FF_max_pin_loads':max(x['mapped_pin_loads'] for x in reported['index_registers']),
            'index_FF_exact_input_parameter_groups':[sorted(names) for names in groups.values()],
            'named_decoder_count':len(named),'named_decoder_pin_loads':{x['cell']:x['mapped_pin_loads'] for x in reported['named_n8507_decoder_family']},
            'named_decoder_max_pin_loads':reported['named_decoder_max_pin_loads'],'named_decoder_signatures':lut_signatures,
            'direct_index_LUT_count':len(direct),'direct_index_LUT_max_pin_loads':reported['direct_index_LUT_max_pin_loads'],
            'decoder_load_pin_set':sorted((x['cell'],x['pin'],x['type']) for row in reported['named_n8507_decoder_family'] for x in row['load_pins'])}
old=independently_check(parent_vg,comparison['parent_max200']);new=independently_check(vg,comparison['same_source_max100'])
redistributed_same_pin_set=old.pop('decoder_load_pin_set')==new.pop('decoder_load_pin_set')
assert old['index_FF_count']==11 and new['index_FF_count']==19 and old['index_FF_max_pin_loads']==200 and new['index_FF_max_pin_loads']==100
assert list(old['named_decoder_pin_loads'].values())==[174,174] and list(new['named_decoder_pin_loads'].values())==[48,100,100,100]
assert old['named_decoder_max_pin_loads']==old['direct_index_LUT_max_pin_loads']==174 and new['named_decoder_max_pin_loads']==new['direct_index_LUT_max_pin_loads']==100
for p,h in list(seen.items()):assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h,(p,'changed during review')
result={'passed_independent_SYN_result_review':True,'reviewed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'actual_vendor_audit_runner_waits':[0,0,0],'SYNTHESIS_RESULT_sha256':sha(T/'SYNTHESIS_RESULT.json'),'synthesis_manifest_sha256':sha(A/'synthesis_freeze_manifest_final.json'),'synthesis_summary_sha256':sha(V/'synthesis_summary.json'),'source55':expected,'parent_VG_sha256':sha(parent_vg),'VG_sha256':sha(vg),'manifest_complete_inventory':True,'manifest_artifact_count':len(manifest['artifacts']),'whole55_byte_unchanged':True,'only_effective_option_delta':{'max_fanout':{'from':200,'to':100}},'strict_clock_radio_gain18pin_gates_passed':True,'resource_comparison':resources['resources'],'independent_old_pin_measurement':old,'independent_new_pin_measurement':new,'decoder_copies_confirmed_by_same_LUT2_INIT9_and_identical_input_roots':True,'decoder_load_consumer_pin_set_unchanged':redistributed_same_pin_set,'conclusion':'Actual decoder duplication increased2->4 with equivalent LUT2 INIT0x9 on shared inputs, reducing per-copy loads174->max100. Matched index FF instances11->19 with maxpinloads200->100. Whole design +83FF/+83LUT, DSP/BSRAM/ALU unchanged. This is a mapped structural/pin-load improvement only; no STA, route or timing benefit is inferred.','STA_or_PNR_acceptance_claimed':False,'PNR_started_for_fan100':False,'source_or_bound_scripts_edited_by_reviewer':False,'vendor_started_by_reviewer':False,'reviewed_unique_inputs':len(seen),'reviewed_hashes':seen,'review_script_sha256':sha(Path(__file__)),'seal_artifacts_revalidated_without_inventing_a_sealer_wait_receipt':True,'findings':[]}
dest=O/'REVIEW.json';assert not dest.exists();dest.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k not in ['source55','reviewed_hashes','resource_comparison','independent_old_pin_measurement','independent_new_pin_measurement']}))
