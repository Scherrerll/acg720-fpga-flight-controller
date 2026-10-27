"""Read-only exact frozen fan100 SYN preparation review; no vendor/runtime calls."""
from pathlib import Path
import ast,collections,datetime,hashlib,importlib.util,json,re,sys
sys.dont_write_bytecode=True
O=Path(__file__).resolve().parent;R=O.parents[2];B=R/'analysis/20261026_z_aw_fix/build'
T=B/'compact_aw_v22_fan100';STD=B/'compact_aw_v22';C=R/'out/z_aw_fix_20261026/compact_aw_v22/canonical/source'
ROOT=R/'out/z_aw_fix_20261026/compact_aw_v22_fan100';PARENT=C.parent.parent/'build_attempt_01'
seen={}
def sha(p):
    p=Path(p)
    for part in p.parts:
        s=part.lower().rstrip(' .');assert not s.startswith('.env') and not s.endswith('.env') and '.env' not in [x.lower() for x in Path(s).suffixes]
    for q in [p,*p.parents]:assert not q.is_symlink() and not (hasattr(q,'is_junction') and q.is_junction())
    h=hashlib.sha256(p.read_bytes()).hexdigest();k=str(p.resolve());assert k not in seen or seen[k]==h,(k,'changed during review');seen[k]=h;return h
def read(p):sha(p);return json.loads(Path(p).read_text(encoding='utf8'))
def bind(p,h):assert sha(p)==h,str(p)
def load(name,p):
    sha(p);s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def tree(p):sha(p);return ast.parse(p.read_text(encoding='utf8'),filename=str(p))
def dump(x):return ast.dump(x,include_attributes=False)
def calls(p,root,names):return [dump(n) for n in ast.walk(tree(p)) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and isinstance(n.func.value,ast.Name) and n.func.value.id==root and n.func.attr in names]
bind(T/'OFFLINE_READY.json','1d0c681e6cf205b66f14003632e1417de0f10e68148d1753f39feed47854402d')
ready=read(T/'OFFLINE_READY.json');prep=read(T/'SYNTHESIS_PREPARATION.json');reuse=read(T/'SOURCE_REUSE_BINDING.json');req=read(T/'REVIEW_REQUIREMENTS.json')
assert ready['passed_offline_preparation'] and not ready['vendor_started'] and not ready['new_fan100_result_claimed']
bind(T/'SYNTHESIS_PREPARATION.json','b70b6dc61df2367c41f4639d4990a9b26cc96cc3ea3297cf962fbf35e13f74b2')
bind(T/'SOURCE_REUSE_BINDING.json','c65bfc6d54e606529cefe41745fecd676b395397b93df5ddd48562156dfcddd4')
assert ready['preparation_sha256']==req['preparation_sha256']==sha(T/'SYNTHESIS_PREPARATION.json')
assert ready['source_reuse_binding_sha256']==req['source_reuse_binding_sha256']==sha(T/'SOURCE_REUSE_BINDING.json')
assert ready['review_requirements_sha256']==sha(T/'REVIEW_REQUIREMENTS.json')
assert ready['scripts_sha256']==req['reviewed_scripts_sha256']==prep['scripts_sha256'] and len(prep['scripts_sha256'])==9
for n,h in prep['scripts_sha256'].items():bind(T/n,h);compile(tree(T/n),str(T/n),'exec')
for p,h in reuse['bound_inputs'].items():bind(p,h)
contract=load('review_fan100_contract',T/'input_contract.py');base=contract.validate()
for p,h in base['bound_inputs'].items():bind(p,h)
expected=base['source55'];assert len(expected)==55 and expected==reuse['source55']==prep['source55']==ready['source55']
assert (T/'source_freeze.json').read_bytes()==(STD/'source_freeze.json').read_bytes()
assert all(sha(C/n)==h for n,h in expected.items())
assert reuse['canonical_source_root']==prep['canonical_source_root']==str(C)
assert reuse['standard_source_proof_origin']==prep['standard_source_proof_origin']==str(STD)
assert not ROOT.exists() and not any((T/n).exists() for n in ['PROOF_BINDING.json','COMPONENT_REUSE_BINDING.json','VY_BINDING.json','SYNTHESIS_RESULT.json','SYN_REVIEW_GATE.json','runner_process.json','runner_exit.json'])
proof=read(STD/'PROOF_BINDING.json');assert proof['source55']==expected and proof['original_attempt_root_actual_wait']==proof['original_failed_alias_compile_wait']==1
assert proof['actual_alias_retry_root_wait']==proof['actual_completion_runner_wait']==0 and len(proof['fresh_actual_exit_receipts'])==22
assert proof['fresh_five_cases']==5 and proof['fresh_fraction_cases']==[0,16] and proof['fresh_four_client'] and proof['fresh_top13']['cases']==13
assert not proof['old_six_controller_byte_identity_reuse_claimed'] and proof['fresh_controller_six_dependencies']['position/mtf_xyz_hold_control.v']==expected['position/mtf_xyz_hold_control.v']
for x in proof['fresh_actual_exit_receipts']:
    bind(x['path'],x['sha256']);j=read(x['path']);assert j[x['normal_field']] is True and type(j[x['actual_wait_field']]) is int and j[x['actual_wait_field']]==0
for prefix,name in [('prepare','PREPARATION_EXIT.json'),('preflight','PREFLIGHT_EXIT.json')]:
    j=read(T/name);assert j['normal_wait_return'] is True and type(j['actual_p_wait']) is int and j['actual_p_wait']==0
    assert sha(Path(j['command'][-1]))==j['script_sha256']
    for stream in ['stdout','stderr']:bind(T/f'{prefix}.{stream}.log',j[f'{stream}_sha256'])
recipe=load('review_fan100_recipe',T/'effective_recipe.py');source_build=(C/'build.tcl').read_bytes();parent_tcl=(PARENT/'synth_only.tcl').read_bytes()
new_tcl=recipe.make_recipe(C/'build.tcl').encode();assert new_tcl.replace(b'set_option -max_fanout 100\n',b'set_option -max_fanout 200\n',1)==parent_tcl
assert (C/'build.tcl').read_bytes()==source_build and sha(C/'build.tcl')==expected['build.tcl']
oldopts=re.findall(rb'^set_option -(\S+)\s+(\S+)\s*$',parent_tcl,re.M);newopts=re.findall(rb'^set_option -(\S+)\s+(\S+)\s*$',new_tcl,re.M)
assert [(k,a,b) for (k,a),(j,b) in zip(oldopts,newopts) if a!=b]==[(b'max_fanout',b'200',b'100')]
assert dict(newopts)==dict(dict(oldopts),max_fanout=b'100') if False else dict(newopts)=={**dict(oldopts),b'max_fanout':b'100'}
assert new_tcl.count(b'run syn\n')==1 and b'run all' not in new_tcl and b'run pnr' not in new_tcl and b'SYNTHESIS_COMMAND_RETURNED_EOF' in new_tcl
preflight=read(T/'PREFLIGHT_RESULT.json');assert preflight['passed'] and preflight['effective_Tcl_sha256']==hashlib.sha256(new_tcl).hexdigest()
assert preflight['parent_execution_Tcl_sha256']==sha(PARENT/'synth_only.tcl') and preflight['source_build_Tcl_sha256']==sha(C/'build.tcl')
assert calls(T/'run_synthesis.py','h',['run_phase','check_sources'])==calls(STD/'run_synthesis.py','h',['run_phase','check_sources'])
assert calls(T/'audit_synthesis_only.py','helper',['mapped_audit','check_sources'])==calls(STD/'audit_synthesis_only.py','helper',['mapped_audit','check_sources'])
assert calls(T/'audit_synthesis_only.py','auditor',['extended_audit'])==calls(STD/'audit_synthesis_only.py','auditor',['extended_audit'])
bind(R/'firmware/B0B4/build_candidate.py','abb5246c203b73c111f80bc91f8db6c8220463f7d4c5cf48dbfe2167ef49db84')
bind(B/'compact_aw_v2/run_synthesis.py','23fe046b259c6713536fc27862eb80a3b392808a77e842aac2085c3f91f3d658')
def assign_value(p,name):
    vals=[n.value for n in ast.walk(tree(p)) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id==name for t in n.targets)];assert len(vals)==1;return vals[0]
for name in ['clocks','bad']:assert dump(assign_value(T/'audit_synthesis_only.py',name))==dump(assign_value(STD/'audit_synthesis_only.py',name))
# Resolve only path assignments; none of the runner/auditor/sealer bodies execute.
def path_namespace(p):
    selected=[];names={'O','R','STANDARD','ROOT','C','A','S','V','PARENT'}
    for n in tree(p).body:
        if isinstance(n,ast.Assign) and all(isinstance(t,ast.Name) and t.id in names for t in n.targets):selected.append(n)
    ns={'Path':Path,'__file__':str(p)};exec(compile(ast.Module(body=selected,type_ignores=[]),'pure_paths_only','exec'),ns);return ns
for n in ['run_synthesis.py','audit_synthesis_only.py']:
    ns=path_namespace(T/n);assert ns['C']==C and ns['A']==ROOT/'build_attempt_01' and ns['S']==ROOT/'build_attempt_01/source'
ns=path_namespace(T/'audit_synthesis_only.py');assert ns['PARENT']==PARENT/'source/impl/gwsynthesis'
assert sha(ns['PARENT']/'acg720_ano_port.vg')==base['VG_sha256']=='e84a81f4a5abb4c15c9e599cc4c2d2e77397a328c9372d0a94c8949fbbf7f4f8'
# Sealer's three actual receipts must reject all coercible/nonzero/null states.
seal=tree(T/'seal_synthesis.py');loops=[n for n in seal.body if isinstance(n,ast.For) and isinstance(n.target,ast.Name) and n.target.id=='j' and isinstance(n.iter,ast.List)]
assert len(loops)==1 and len(loops[0].body)==1 and isinstance(loops[0].body[0],ast.Assert)
expr=loops[0].body[0].test
receipts=[None,{},[],{'normal_wait_return':True},{'actual_p_wait':0},{'normal_wait_return':True,'actual_p_wait':None},{'normal_wait_return':True,'actual_p_wait':False},{'normal_wait_return':True,'actual_p_wait':'0'},{'normal_wait_return':True,'actual_p_wait':0.0},{'normal_wait_return':1,'actual_p_wait':0},{'normal_wait_return':False,'actual_p_wait':0},{'normal_wait_return':True,'actual_p_wait':1},{'normal_wait_return':True,'actual_p_wait':0}]
for j in receipts:
    actual=eval(compile(ast.Expression(expr),'strict_receipt_gate_only','eval'),{'j':j})
    wanted=isinstance(j,dict) and j.get('normal_wait_return') is True and type(j.get('actual_p_wait')) is int and j['actual_p_wait']==0
    assert actual is wanted
assert 'code=p.wait()' in (T/'launch_synthesis_hidden.py').read_text() and 'actual_p_wait=code,normal_wait_return=True' in (T/'launch_synthesis_hidden.py').read_text()
assert 'code = proc.wait()' in (R/'firmware/B0B4/build_candidate.py').read_text()
mapped=load('review_mapped_fanout',T/'mapped_fanout.py');measurement=mapped.measure(PARENT/'source/impl/gwsynthesis/acg720_ano_port.vg')
assert measurement==read(T/'PARENT_MAPPED_FANOUT.json')
# Independently recount every declared output-root load of the measured named LUTs.
graph=load('review_unchanged_graph',mapped.GRAPH);g=graph.Graph(PARENT/'source/impl/gwsynthesis/acg720_ano_port.vg')
outputs={'Q','F','O','G','V','SUM','COUT','DO','DOUT'};loads=collections.defaultdict(list)
for name,cell in g.cells.items():
    for pin,nets in cell['pins'].items():
        if pin not in outputs:
            for net in nets:loads[g.find(net)].append((name,pin,cell['type']))
for item in measurement['index_registers']+measurement['named_n8507_decoder_family']+measurement['direct_index_driven_LUTs']:
    observed=[x for root in item['canonical_output_nets'] for x in loads[root]]
    assert len(observed)==item['mapped_pin_loads'] and len({x[0] for x in observed})==item['unique_load_cells']
    assert collections.Counter(observed)==collections.Counter((x['cell'],x['pin'],x['type']) for x in item['load_pins'])
assert measurement['named_decoder_family_count']==2 and measurement['named_decoder_max_pin_loads']==measurement['direct_index_LUT_max_pin_loads']==174
assert all('No' in measurement['scope'] or measurement['scope'] for _ in [0])
assert all(not isinstance(n,ast.Assert) or ('mapped_pin_loads' not in ast.unparse(n.test) and 'named_decoder_family_count' not in ast.unparse(n.test)) for n in ast.walk(tree(T/'mapped_fanout.py')))
assert 'measure(parent_vg)' in (T/'audit_synthesis_only.py').read_text() and 'measure(vg)' in (T/'audit_synthesis_only.py').read_text()
assert not ROOT.exists() and not (T/'SYN_REVIEW_GATE.json').exists()
for p,h in list(seen.items()):assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h,(p,'changed during review')
report={'approved_preparation':True,'approved_scope':'Exact-hash dormant same-source SYN_ONLY max_fanout200->100 preparation; no vendor or physical launch authorization.','reviewed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'OFFLINE_READY_sha256':sha(T/'OFFLINE_READY.json'),'SYNTHESIS_PREPARATION_sha256':sha(T/'SYNTHESIS_PREPARATION.json'),'SOURCE_REUSE_BINDING_sha256':sha(T/'SOURCE_REUSE_BINDING.json'),'REVIEW_REQUIREMENTS_sha256':sha(T/'REVIEW_REQUIREMENTS.json'),'source55':expected,'parent_VG_sha256':base['VG_sha256'],'only_effective_option_delta':{'max_fanout':{'from':200,'to':100}},'source_build_tcl_byte_unchanged':True,'reverse_effective_recipe_byte_equals_sealed_STD22':True,'fresh_STD22_successful_proof_receipts':22,'original_TEMP_compile_and_root_waits':[1,1],'alias_retry_and_completion_waits':[0,0],'all_original_process_mapped_gain18pin_and_strict_CLK50_gates_preserved':True,'strict_normal_exact_int0_vendor_audit_root_sealer':True,'parent_only_measured_decoder_count':2,'parent_only_measured_max_pin_loads':174,'new_fan100_effect_claimed':False,'replication_or_timing_improvement_inferred':False,'measurement_scope':'Actual future new/current XML resources and actual old/new index FF, direct-index LUT and named n8507 family pin loads. Missing/renamed families allowed as observed; no load<=100 or benefit threshold.','examined_unique_files':len(seen),'reviewed_hashes':seen,'review_script_sha256':sha(Path(__file__)),'producer_files_edited':False,'vendor_started_by_reviewer':False,'runtime_attempt_absent':True,'physical_started_by_reviewer':False,'findings':[]}
dest=O/'REVIEW.json';assert not dest.exists();dest.write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k not in ['source55','reviewed_hashes']}))
