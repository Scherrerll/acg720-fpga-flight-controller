"""Independent read-only prelaunch review; no runtime/vendor execution or thin edits."""
from pathlib import Path
import ast,datetime,hashlib,importlib.util,itertools,json,re,sys,xml.etree.ElementTree as ET
sys.dont_write_bytecode=True
O=Path(__file__).resolve().parent;R=O.parents[2];BUILD=R/'analysis/20261026_z_aw_fix/build'
T=BUILD/'compact_aw_v22_dsp_followup';S=BUILD/'compact_aw_v22';C=R/'out/z_aw_fix_20261026/compact_aw_v22/canonical/source'
ROOT=C.parents[1];PROFILE='physical_p3r0_dsploc_01';seen={}
def safe(p):
    p=Path(p)
    for part in p.parts:
        n=part.lower().rstrip(' .');assert not n.startswith('.env') and not n.endswith('.env') and '.env' not in [x.lower() for x in Path(n).suffixes]
    for q in [p,*p.parents]:assert not q.is_symlink() and not (hasattr(q,'is_junction') and q.is_junction()),str(p)
    return p
def sha(p):
    p=safe(p);h=hashlib.sha256(p.read_bytes()).hexdigest();key=str(p.resolve());assert key not in seen or seen[key]==h,(key,'changed during review');seen[key]=h;return h
def read(p):sha(p);return json.loads(Path(p).read_text(encoding='utf8'))
def bind(p,h):assert sha(p)==h,str(p)
def load(name,path):
    sha(path);spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def tree(path):sha(path);return ast.parse(path.read_text(encoding='utf8'),filename=str(path))
def dump(x):return ast.dump(x,include_attributes=False)
def function_ast(path,names):return [n for n in tree(path).body if isinstance(n,ast.FunctionDef) and n.name in names]
def calls(path,root,names):return [dump(n) for n in ast.walk(tree(path)) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and isinstance(n.func.value,ast.Name) and n.func.value.id==root and n.func.attr in names]
assert len(sys.argv)==2 and re.fullmatch('[a-f0-9]{64}',sys.argv[1])
bind(T/'OFFLINE_READY.json',sys.argv[1]);ready=read(T/'OFFLINE_READY.json');assert ready['passed_offline_preparation'] and not ready['qualified_physical'] and not ready['vendor_started']
prep=read(T/'PHYSICAL_PREPARATION.json');req=read(T/'PRELAUNCH_REVIEW_REQUIREMENTS.json');binding=read(T/'PORTABLE_CONSTRAINT_BINDING.json');filterj=read(T/'PORTABLE_FILTER_VALIDATION.json');filtered=filterj['report']
for n,key in [('PHYSICAL_PREPARATION.json','PHYSICAL_PREPARATION_sha256'),('PORTABLE_CONSTRAINT_BINDING.json','PORTABLE_CONSTRAINT_BINDING_sha256'),('PORTABLE_FILTER_VALIDATION.json','PORTABLE_FILTER_VALIDATION_sha256'),('INDEPENDENT_PREPARATION_REVIEW.json','INDEPENDENT_PREPARATION_REVIEW_sha256'),('PRELAUNCH_REVIEW_REQUIREMENTS.json','REVIEW_REQUIREMENTS_sha256')]:bind(T/n,ready[key])
assert prep['profile']==req['profile'] if 'profile' in req else prep['profile']==PROFILE
assert prep['profile']==PROFILE and Path(prep['ATTEMPT'])==ROOT/PROFILE and Path(prep['receipt_directory'])==T/PROFILE
assert ready['standard_source_proof_origin']==req['standard_source_proof_origin']==prep['standard_source_proof_origin']==binding['standard_source_proof_origin']==str(S)
for n,h in req['scripts_sha256'].items():bind(T/n,h)
for n,h in prep['new_scripts_sha256'].items():bind(T/n,h);compile(tree(T/n),str(T/n),'exec')
for n,h in prep['parent_scripts_sha256'].items():bind(S/n,h)
for p,h in binding['bound_inputs'].items():bind(p,h)
stable=read(T/'STANDARD22_STABILITY.json')
for p,h in stable['bound_inputs'].items():bind(p,h)
for p,h in ready['actual_check_receipts'].items():
    bind(p,h);j=read(p)
    assert (j.get('normal_wait_return') is True and type(j.get('actual_p_wait')) is int and j['actual_p_wait']==0) or (j.get('normal_return') is True and type(j.get('actual_completedprocess_returncode')) is int and j['actual_completedprocess_returncode']==0)
# Whole standard contract is the actual new-controller source/proof/SYN chain.
bind(S/'PHYSICAL_PREPARATION.json','643b37d7789951e2e777b01d554cf9e2a67125cf7113df597d721b304df14cec')
bind(S/'PHYSICAL_INPUT_BINDING.json','53d1c9087592329c9c6fcfca5a2af3e7a64e4c0b55864989863fb0e16d42f27f')
bind(S/'physical_input_contract.py','e8fcc82c361fbd65f2eb93109cfeef63993c738740fe0a712db3e10fca45aac0')
base=load('independent_review_standard22_contract',S/'physical_input_contract.py').validate22(require_preparation=True)
assert base['passed'] and base['VG_sha256']=='e84a81f4a5abb4c15c9e599cc4c2d2e77397a328c9372d0a94c8949fbbf7f4f8'
for p,h in base['bound_inputs'].items():bind(p,h)
f=read(S/'source_freeze.json');assert prep['source55']==binding['source55']==f['source55']==base['source55'] and len(f['source55'])==55
assert (T/'source_freeze.json').read_bytes()==(S/'source_freeze.json').read_bytes()
for n,h in f['source55'].items():bind(C/n,h)
assert not any((T/n).exists() for n in ['PROOF_BINDING.json','COMPONENT_REUSE_BINDING.json','SYNTHESIS_RESULT.json'])
proof=read(S/'PROOF_BINDING.json');assert proof['passed'] and proof['original_attempt_root_actual_wait']==proof['original_failed_alias_compile_wait']==1
assert proof['actual_alias_retry_root_wait']==proof['actual_completion_runner_wait']==proof['actual_proof_runner_wait']==0
assert proof['fresh_five_cases']==5 and proof['fresh_fraction_cases']==[0,16] and proof['fresh_four_client'] and proof['fresh_top13']['cases']==13
assert proof['fresh_controller_six_dependencies']['position/mtf_xyz_hold_control.v']==f['source55']['position/mtf_xyz_hold_control.v']=='df5baa0ffc8135c2818271b42ff1fb14ea0cd3ce5131289b66a7cd5d0ff5b976'
assert not proof['old_six_controller_byte_identity_reuse_claimed'] and len(proof['fresh_actual_exit_receipts'])==22
for x in proof['fresh_actual_exit_receipts']:
    bind(x['path'],x['sha256']);j=read(x['path']);assert j[x['normal_field']] is True and type(j[x['actual_wait_field']]) is int and j[x['actual_wait_field']]==0
reference=read(O/'REFERENCE_MAPPING.json');kept=[x for x in reference['rows'] if x['kept']];dropped=[x for x in reference['rows'] if not x['kept']]
assert [x['instance'] for x in filtered['kept_rows']]==[x['instance'] for x in kept]
assert [x['instance'] for x in filtered['dropped_rows']]==[x['instance'] for x in dropped]
for x,y in zip(filtered['kept_rows'],kept):assert x['primitive']==y['primitive']==y['target_primitive'] and x['locations']==y['locations'] and x['original_line']==y['original_line']
assert [filtered[k] for k in ['official_export_rows','kept','excluded','DSP','BSRAM']]==[52,33,19,31,2]
prefix=(C/'acg720_ano_port.cst').read_bytes();suffix=(T/'portable_v22_dsp_bsram.cst').read_bytes()
assert len(prefix)==1891 and b'CLOCK_LOC "observer_reset" BUFG = CE|SR|LOGIC;' in prefix
assert [line for line in suffix.decode().splitlines() if line.strip() and not line.lstrip().startswith('//')]==[x['original_line'] for x in kept]
combined=prefix+suffix;assert len(combined)==4915 and hashlib.sha256(combined).hexdigest()==filtered['combined_CST_sha256']=='38df04847e0f5d6b36b60f28a60bff4e0a601c7395c33e2bf1a17d64eba7d4e0'
portable=load('independent_review_frozen_thin_contract',T/'portable_constraints.py').validate();assert portable['passed'] and portable['standard_contract']==base
# Actual deferred call graph uses the untouched helper's full physical gates.
assert calls(T/'run_physical.py','helper',['run_phase','physical_audit','check_sources'])==calls(S/'run_physical.py','helper',['run_phase','physical_audit','check_sources'])
bind(R/'firmware/B0B4/build_candidate.py','abb5246c203b73c111f80bc91f8db6c8220463f7d4c5cf48dbfe2167ef49db84')
runtext=(T/'run_physical.py').read_text();assert "sys.argv[1] in ['3']" in runtext and "ATTEMPT=ROOT/'physical_p3r0_dsploc_01'" in runtext
assert "STANDARD/'PROOF_BINDING.json'" in runtext and "STANDARD/'SYNTHESIS_RESULT.json'" in runtext and "O/'PROOF_BINDING.json'" not in runtext
entry_nodes=[n.value for n in ast.walk(tree(T/'run_physical.py')) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='entries' for t in n.targets)]
assert len(entry_nodes)==1 and ast.literal_eval(entry_nodes[0])==[('impl/gwsynthesis/acg720_ano_port.vg','file.netlist'),('physical_constraints.cst','file.cst'),('acg720_ano_port.sdc','file.sdc')]
tcl_nodes=[n.value for n in ast.walk(tree(T/'run_physical.py')) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='tcl' for t in n.targets)]
assert len(tcl_nodes)==1
lines=(C/'build.tcl').read_text().splitlines();tcl=eval(compile(ast.Expression(tcl_nodes[0]),'physical_tcl_string_only','eval'),{'__builtins__':{},'lines':lines,'PLACE':3},{})
original_options=dict(re.findall(r'^set_option -(\S+)\s+(\S+)\s*$', '\n'.join(lines),re.M));options=dict(re.findall(r'^set_option -(\S+)\s+(\S+)\s*$',tcl,re.M))
assert options=={**original_options,'cst_warn_to_error':'1'} and options['place_option']=='3' and options['route_option']=='0' and options['global_freq']=='50'
assert 'run syn' not in tcl and 'run all' not in tcl and tcl.count('run pnr\n')==1 and 'PHYSICAL_COMMAND_RETURNED_EOF' in tcl
assert 'open_project physical.gprj' in tcl
preflight=read(T/'PHYSICAL_TCL_PREFLIGHT.json');assert preflight['runner_sha256']==sha(T/'run_physical.py')
assert preflight['profiles']['3']['Tcl_sha256']==hashlib.sha256(tcl.encode()).hexdigest()
# Verify every original independent raw check survives the STANDARD metadata alias.
def raw_checks(source):
    out={}
    for n in ast.walk(ast.parse(source)):
        if isinstance(n,ast.Assign) and len(n.targets)==1 and isinstance(n.targets[0],ast.Subscript):
            t=n.targets[0]
            if isinstance(t.value,ast.Name) and t.value.id=='checks' and isinstance(t.slice,ast.Constant):out[t.slice.value]=dump(n.value)
    return out
old_raw=(S/'independent_raw_review.py').read_text()
for name in ['PROOF_BINDING.json','PHYSICAL_INPUT_BINDING.json','COMPONENT_REUSE_BINDING.json','SYNTHESIS_RESULT.json','PHYSICAL_PREPARATION.json']:old_raw=old_raw.replace("O/'"+name+"'","STANDARD/'"+name+"'")
old_checks,new_checks=raw_checks(old_raw),raw_checks((T/'independent_raw_review.py').read_text())
assert all(new_checks[k]==v for k,v in old_checks.items())
# Detect the originally found missing thin metadata reference, across all scripts.
for n in ['run_physical.py','seal_terminal.py','independent_raw_review.py','physical_snapshot.py']:
    for call in ast.walk(tree(T/n)):
        if isinstance(call,ast.Call) and isinstance(call.func,ast.Name) and call.func.id=='read' and call.args:
            arg=call.args[0]
            if isinstance(arg,ast.BinOp) and isinstance(arg.op,ast.Div) and isinstance(arg.left,ast.Name) and arg.left.id in ['O','STANDARD'] and isinstance(arg.right,ast.Constant) and isinstance(arg.right.value,str) and arg.right.value.endswith('.json'):
                path=(T if arg.left.id=='O' else S)/arg.right.value;assert path.is_file(),(n,call.lineno,'missing metadata reference',path)
# Pure status functions, not any physical top-level, are executed for truth checks.
results=[None,{},[],{'passed':False},{'passed':None},{'passed':0},{'passed':1},{'passed':True}]
receipts=[None,{},[],{'normal_wait_return':True},{'actual_p_wait':0},{'normal_wait_return':False,'actual_p_wait':0},{'normal_wait_return':1,'actual_p_wait':0},{'normal_wait_return':True,'actual_p_wait':None},{'normal_wait_return':True,'actual_p_wait':False},{'normal_wait_return':True,'actual_p_wait':0.0},{'normal_wait_return':True,'actual_p_wait':'0'},{'normal_wait_return':True,'actual_p_wait':1},{'normal_wait_return':True,'actual_p_wait':0}]
truth=0
for n in ['seal_terminal.py','physical_snapshot.py']:
    functions=function_ast(T/n,['successful_receipt','terminal_status']);assert len(functions)==2 and [dump(x) for x in functions]==[dump(x) for x in function_ast(S/n,['successful_receipt','terminal_status'])]
    ns={};exec(compile(ast.Module(body=functions,type_ignores=[]),'pure_status_only','exec'),ns)
    for result,vendor,runner in itertools.product(results,receipts,receipts):
        expected=isinstance(result,dict) and result.get('passed') is True and all(isinstance(q,dict) and q.get('normal_wait_return') is True and type(q.get('actual_p_wait')) is int and q['actual_p_wait']==0 for q in [vendor,runner])
        passed,label=ns['terminal_status'](result,vendor,runner,{'passed':True,'criteria':{'full_route':True}});assert passed is expected and ((label=='full_gate_pass') is expected);truth+=1
    assert ns['terminal_status']({'passed':True},{'normal_wait_return':True,'actual_p_wait':0},{'normal_wait_return':True,'actual_p_wait':1})==(False,'runner_failed_after_physical_gate_pass')
launch=(T/'launch_physical_hidden.py').read_text();assert "sys.argv[1] in ['3']" in launch and "O=BASE/'physical_p3r0_dsploc_01'" in launch and 'code=process.wait()' in launch and 'actual_p_wait=code,normal_wait_return=True' in launch and 'CREATE_NO_WINDOW' in launch
assert not (ROOT/PROFILE).exists() and (T/PROFILE).is_dir() and not any((T/PROFILE).iterdir())
assert not (ROOT/'physical_p3r0_01').exists()
for path,h in list(seen.items()):assert hashlib.sha256(Path(path).read_bytes()).hexdigest()==h,(path,'changed during review')
out={'approved_preparation':True,'qualified_physical':False,'reviewed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'PHYSICAL_PREPARATION_sha256':sha(T/'PHYSICAL_PREPARATION.json'),'PORTABLE_CONSTRAINT_BINDING_sha256':sha(T/'PORTABLE_CONSTRAINT_BINDING.json'),'OFFLINE_READY_sha256':sha(T/'OFFLINE_READY.json'),'PRELAUNCH_REVIEW_REQUIREMENTS_sha256':sha(T/'PRELAUNCH_REVIEW_REQUIREMENTS.json'),'VG_sha256':base['VG_sha256'],'source55':base['source55'],'counts':{'official':52,'kept':33,'excluded':19,'DSP':31,'BSRAM':2},'original_CST_prefix_bytes':1891,'combined_CST_bytes':4915,'combined_CST_sha256':hashlib.sha256(combined).hexdigest(),'successful_fresh_proof_receipts':22,'original_TEMP_compile_and_root_waits':[1,1],'alias_retry_and_completion_waits':[0,0],'fresh_controller_cases':{'five':5,'FRAC':[0,16],'four_client':True,'top13':13},'strict_status_truth_cases':truth,'original_full_physical_helper_calls_AST_unchanged':True,'all_original_independent_raw_checks_preserved':True,'only_effective_option_delta':{'cst_warn_to_error':'1'},'initial_finding_resolved':True,'initial_finding_path':str(O/'FINDING_attempt01.json'),'examined_unique_file_hashes':len(seen),'reviewed_hashes':seen,'review_script_sha256':sha(Path(__file__)),'runtime_attempt_absent':True,'receipt_directory_empty':True,'vendor_started_by_reviewer':False,'thin_or_standard_files_edited_by_reviewer':False,'findings':[],'scope':'Approval of the exact frozen offline single-P3 preparation only. No vendor run, physical qualification, timing acceptance, runtime completion or launch authorization.'}
dest=O/'REVIEW.json';assert not dest.exists();dest.write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({k:v for k,v in out.items() if k not in ['source55','reviewed_hashes']}))
