"""Rebind only unexecuted v22 physical identity wording; no SYN/vendor execution."""
from pathlib import Path
import ast,datetime,difflib,hashlib,importlib.util,json,subprocess,sys
sys.dont_write_bytecode=True
O=Path(__file__).resolve().parent;R=O.parents[3];SAVED=O/'prepared_revisions/revision_01'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf8'))
write=lambda p,j:p.write_text(json.dumps(j,indent=2)+'\n',encoding='utf8')
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def check_protected(manifest):
    for path,h in manifest['protected_SYN_source_and_standard_v20_inputs'].items():assert sha(Path(path))==h,path
    for n,x in manifest['artifacts'].items():assert sha(SAVED/n)==x['sha256'] and (SAVED/n).stat().st_size==x['bytes']
    assert not (R/'out/z_aw_fix_20261026/compact_aw_v22/physical_p3r0_01').exists()
    assert (O/'physical_p3r0_01').is_dir() and not any((O/'physical_p3r0_01').iterdir())
manifest=read(SAVED/'MANIFEST.json');check_protected(manifest)
old_prep=read(SAVED/'PHYSICAL_PREPARATION.json');old_binding=read(SAVED/'PHYSICAL_INPUT_BINDING.json')
assert sha(O/'PHYSICAL_PREPARATION.json')==manifest['old_PHYSICAL_PREPARATION_sha256']
assert sha(O/'prepare_v22_physical.py')=='3267acebea47a591ee3ab679e50929e91ad381227d3f04ec913c24a598845946'
preparer=load('v22_identity_corrected_preparer_no_main',O/'prepare_v22_physical.py')
originals,scripts=preparer.authored_scripts()
assert set(scripts)==set(old_prep['new_scripts_sha256']) and len(scripts)==7
run_edits=[
 ('"""Deferred sealed exact-v20 map2','"""Deferred sealed exact-v22 map2'),
 ("'scope':'Fresh sealed exact-v20 VG physical-only trial;","'scope':'Fresh sealed exact-v22 VG physical-only trial;"),
 ("'scope':'Physical artifact gate only;","'scope':'v22 physical artifact gate only;")]
launch_edits=[('single deferred v19 P3/R0 profile.','single deferred v22 P3/R0 profile.')]
edits={'run_physical.py':run_edits,'launch_physical_hidden.py':launch_edits}
for n,s in scripts.items():
    assert sha(O/n)==old_prep['new_scripts_sha256'][n]==sha(SAVED/n),n
    reconstructed=s
    for a,b in reversed(edits.get(n,[])):
        assert reconstructed.count(b)==1,(n,b);reconstructed=reconstructed.replace(b,a,1)
    assert reconstructed==(SAVED/n).read_text(encoding='utf8'),n
    ast.parse(s,filename=str(O/n));compile(s,str(O/n),'exec')
assert 'sealed exact-v20' not in scripts['run_physical.py'] and 'deferred v19' not in scripts['launch_physical_hidden.py']
assert "baseline_version='v20'" in scripts['seal_terminal.py']
assert "baseline20=functional_contract['baseline_source55']" in scripts['run_physical.py']
assert "compact_aw_v4/source_freeze.json" in scripts['run_physical.py']
for n in edits:(O/n).write_text(scripts[n],encoding='utf8',newline='\n')
derivation=''.join(''.join(difflib.unified_diff(originals.get(n,'').splitlines(True),s.splitlines(True),fromfile='sealed_v20/'+n,tofile='v22/'+n)) for n,s in scripts.items())
(O/'PHYSICAL_SCRIPT_DERIVATION.diff').write_text(derivation,encoding='utf8')
validator=load('v22_identity_rebinding_contract',O/'physical_input_contract.py')
validation=validator.validate22(require_preparation=False)
assert validation['source55']==old_binding['validation']['source55']==old_prep['source55']
assert validation['baseline_source55']==old_binding['validation']['baseline_source55']==old_prep['baseline_source55']
assert validation['protected_v4_source55']==old_binding['validation']['protected_v4_source55']==old_prep['protected_v4_source55']
assert validation['VG_sha256']==old_prep['VG_sha256']
assert validation['local_hint_effect_audit_sha256']==old_prep['local_hint_effect_audit_sha256']
binding=dict(old_binding);binding.update(validation=validation,preparer_sha256=sha(O/'prepare_v22_physical.py'),identity_revision=2,immutable_prior_preparation_manifest_sha256=sha(SAVED/'MANIFEST.json'))
write(O/'PHYSICAL_INPUT_BINDING.json',binding)
# The old preflight is preserved in immutable revision_01 before regenerating
# its runner binding. Its Tcl expression must stay byte-identical.
target=O/'PHYSICAL_TCL_PREFLIGHT.json';assert sha(target)==manifest['artifacts'][target.name]['sha256'];target.unlink()
command=[sys.executable,'-B','-X','utf8',str(O/'preflight_physical_recipe.py')]
with (O/'physical_preflight.stdout.log').open('wb') as out,(O/'physical_preflight.stderr.log').open('wb') as err:
    p=subprocess.Popen(command,cwd=R,stdin=subprocess.DEVNULL,stdout=out,stderr=err,creationflags=subprocess.CREATE_NO_WINDOW)
    code=p.wait(timeout=60)
write(O/'PHYSICAL_PREFLIGHT_EXIT.json',{'command':command,'normal_wait_return':True,'actual_p_wait':code,'pid':p.pid,'stdout_sha256':sha(O/'physical_preflight.stdout.log'),'stderr_sha256':sha(O/'physical_preflight.stderr.log'),'scope':'Actual Python-only Tcl syntax preflight after identity-only wording correction; no vendor or Tcl command execution.'})
assert code==0
preflight=read(target);old_preflight=read(SAVED/'PHYSICAL_TCL_PREFLIGHT.json')
assert preflight['profiles']==old_preflight['profiles'] and preflight['runner_sha256']==sha(O/'run_physical.py')
prep=dict(old_prep)
prep.update(prepared_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),input_binding_sha256=sha(O/'PHYSICAL_INPUT_BINDING.json'),new_scripts_sha256={n:sha(O/n) for n in scripts},derivation_sha256=sha(O/'PHYSICAL_SCRIPT_DERIVATION.diff'),preparer_sha256=sha(O/'prepare_v22_physical.py'),preflight_actual_returncode=code,preflight_exit_sha256=sha(O/'PHYSICAL_PREFLIGHT_EXIT.json'),physical_Tcl_preflight_sha256=sha(target),identity_revision=2,immutable_prior_preparation_manifest_path=str(SAVED/'MANIFEST.json'),immutable_prior_preparation_manifest_sha256=sha(SAVED/'MANIFEST.json'))
write(O/'PHYSICAL_PREPARATION.json',prep)
assert validator.validate22(require_preparation=True)['passed']
check_protected(manifest)
assert sha(O/'seal_terminal.py')==sha(SAVED/'seal_terminal.py') and sha(O/'physical_snapshot.py')==sha(SAVED/'physical_snapshot.py')
report={'passed':True,'scope':'Identity wording only; precise reverse text edits reconstruct both old generated scripts. Five other generated scripts and all source/proof/SYN/standard-v20 inputs unchanged. No runtime physical or vendor launch.','preparer_sha256':sha(O/'prepare_v22_physical.py'),'PHYSICAL_PREPARATION_sha256':sha(O/'PHYSICAL_PREPARATION.json'),'PHYSICAL_INPUT_BINDING_sha256':sha(O/'PHYSICAL_INPUT_BINDING.json'),'immutable_prior_manifest_sha256':sha(SAVED/'MANIFEST.json'),'exact_generated_text_edits':edits,'changed_generated_scripts':list(edits),'all7_AST_compile_only_passed':True,'status_helpers_scripts_byte_exact':True,'previous_truth_check_sha256':sha(SAVED/'prepare_v22_physical.revision02_checks.json'),'source55_unchanged':True,'baseline_v20_unchanged':True,'protected_v4_unchanged':True,'VG_unchanged':old_prep['VG_sha256'],'actual_Python_preflight_wait':code,'Tcl_profiles_byte_identical':True,'protected_inputs_rehashed':len(manifest['protected_SYN_source_and_standard_v20_inputs']),'runtime22_absent':True,'profile_receipt_directory_empty':True,'vendor_started':False,'rebind_script_sha256':sha(Path(__file__))}
dest=O/'PHYSICAL_IDENTITY_REVISION02.json';assert not dest.exists();write(dest,report)
print(json.dumps(report))
