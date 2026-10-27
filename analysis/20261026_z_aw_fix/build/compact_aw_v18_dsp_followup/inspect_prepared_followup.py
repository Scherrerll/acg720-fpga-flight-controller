"""Independent AST/metadata inspection of dormant follow-up; never runs physical code."""
from pathlib import Path
import ast,datetime,hashlib,json

O=Path(__file__).resolve().parent;R=O.parents[3];P=O.parent/'compact_aw_v18'
PROFILE='physical_p3r0_dsploc_01';ROOT=R/'out/z_aw_fix_20261026/compact_aw_v18'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf8'))
prep=read(O/'PHYSICAL_PREPARATION.json');binding=read(O/'PORTABLE_CONSTRAINT_BINDING.json')
assert prep['profile']==PROFILE and prep['runtime_ROOT']==str(ROOT) and prep['ATTEMPT']==str(ROOT/PROFILE)
assert prep['portable_constraint_binding_sha256']==sha(O/'PORTABLE_CONSTRAINT_BINDING.json')
assert (O/'source_freeze.json').read_bytes()==(P/'source_freeze.json').read_bytes()
for n,h in prep['new_scripts_sha256'].items():
    assert sha(O/n)==h;ast.parse((O/n).read_text(encoding='utf8'),filename=str(O/n))
for n,h in prep['parent_scripts_sha256'].items():assert sha(P/n)==h
for p,h in binding['bound_inputs'].items():assert sha(Path(p))==h
original=ROOT/'canonical/source/acg720_ano_port.cst';portable=Path(binding['portable_constraint_path'])
prefix=original.read_bytes();suffix=portable.read_bytes();assert prefix.endswith(b'\n')
assert b'CLOCK_LOC "observer_reset" BUFG = CE|SR|LOGIC;' in prefix
assert hashlib.sha256(prefix+suffix).hexdigest()==binding['validation']['combined_CST_sha256']
assert len(prefix)==binding['validation']['original_IO_prefix_bytes']
assert binding['validation']['original_CLOCK_LOC_statements_preserved']==['CLOCK_LOC "observer_reset" BUFG = CE|SR|LOGIC;']
text=(O/'run_physical.py').read_text(encoding='utf8');tree=ast.parse(text)
assert "sys.argv[1] in ['3']" in text and f"ATTEMPT=ROOT/'{PROFILE}'" in text
entries=[ast.literal_eval(n.value) for n in ast.walk(tree) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='entries' for t in n.targets)]
assert entries==[[('impl/gwsynthesis/acg720_ano_port.vg','file.netlist'),('physical_constraints.cst','file.cst'),('acg720_ano_port.sdc','file.sdc')]]
assert text.index('constraint_check=validate()')<text.index('ATTEMPT.mkdir(')<text.index("helper.run_phase('physical'")
assert text.index('assert verify_attempt(SOURCE)')<text.index("helper.run_phase('physical'")
assert "combined.write_bytes(combined_bytes())" in text and "assert hash55(SOURCE,expected)==expected" in text
def gate_calls(source):
    out=[]
    for n in ast.walk(ast.parse(source)):
        if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and isinstance(n.func.value,ast.Name) and n.func.value.id=='helper' and n.func.attr in ['run_phase','physical_audit','check_sources']:
            out.append(ast.dump(n,include_attributes=False))
    return out
assert gate_calls(text)==gate_calls((P/'run_physical.py').read_text(encoding='utf8'))
def check_assignments(source):
    out={}
    for n in ast.walk(ast.parse(source)):
        if isinstance(n,ast.Assign) and len(n.targets)==1:
            t=n.targets[0]
            if isinstance(t,ast.Subscript) and isinstance(t.value,ast.Name) and t.value.id=='checks' and isinstance(t.slice,ast.Constant):
                out[t.slice.value]=ast.dump(n.value,include_attributes=False)
    return out
old_checks=check_assignments((P/'independent_raw_review.py').read_text(encoding='utf8'))
new_checks=check_assignments((O/'independent_raw_review.py').read_text(encoding='utf8'))
assert all(new_checks[k]==v for k,v in old_checks.items())
preflight=read(O/'PHYSICAL_TCL_PREFLIGHT.json');exit=read(O/'PREFLIGHT_EXIT.json')
assert preflight['runner_sha256']==sha(O/'run_physical.py') and list(preflight['profiles'])==['3']
assert preflight['profiles']['3']['Tcl_complete'] and preflight['profiles']['3']['options_verified']
assert exit['normal_return'] and exit['actual_completedprocess_returncode']==0
assert sha(O/'preflight.stdout.log')==exit['stdout_sha256'] and sha(O/'preflight.stderr.log')==exit['stderr_sha256']
preflight_source=(O/'preflight_physical_recipe.py').read_text(encoding='utf8')
assert "interp.call('info','complete',tcl)" in preflight_source and 'interp.eval' not in preflight_source
assert not (ROOT/PROFILE).exists() and (O/PROFILE).is_dir() and not any((O/PROFILE).iterdir())
review={'reviewed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'passed':True,
    'profile':PROFILE,'source_freeze_byte_exact':True,'parent_scripts_unchanged':True,'AST_parse_passed':True,
    'original_physical_gate_calls_AST_identical':True,'original_independent_raw_checks_AST_identical':True,
    'physical_project_selects_only_combined_CST':True,'original_baseline_prefix_byte_exact':True,
    'existing_CLOCK_LOC_preserved':'CLOCK_LOC "observer_reset" BUFG = CE|SR|LOGIC;',
    'prefix_definition':'Complete frozen original v18 CST, including IO attributes and its existing CLOCK_LOC; not an IO-only subset',
    'new_suffix_only':'Exact portable46 DSP/BSRAM INS_LOC rows and comments; no new IO/clock/SDC directives',
    'sole_option_delta':{'cst_warn_to_error':1},'pure_Tcl_info_complete_actual_returncode':0,
    'preparation_sha256':sha(O/'PHYSICAL_PREPARATION.json'),'constraint_binding_sha256':sha(O/'PORTABLE_CONSTRAINT_BINDING.json'),
    'runtime_attempt_absent':True,'launch_receipt_directory_empty':True,'vendor_started':False,'hardware_actions':False}
dest=O/'INDEPENDENT_PREPARATION_REVIEW.json';assert not dest.exists()
dest.write_text(json.dumps(review,indent=2)+'\n',encoding='utf8',newline='\n')
print(json.dumps({'independent_preparation_review_passed':True,'profile':PROFILE,'review_sha256':sha(dest),'runtime_attempt_absent':True,'vendor_started':False}))
