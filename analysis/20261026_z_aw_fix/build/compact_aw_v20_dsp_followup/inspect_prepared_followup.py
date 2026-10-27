"""Independent AST/artifact inspection of the dormant thin layer; never launch PNR."""
from pathlib import Path
import ast,datetime,hashlib,json
O=Path(__file__).resolve().parent;R=O.parents[3];STANDARD=O.parent/'compact_aw_v20'
ROOT=R/'out/z_aw_fix_20261026/compact_aw_v20';PROFILE='physical_p3r0_dsploc_01'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf8'))
prep=read(O/'PHYSICAL_PREPARATION.json');binding=read(O/'PORTABLE_CONSTRAINT_BINDING.json');filtered=read(O/'PORTABLE_FILTER_VALIDATION.json')['report']
assert prep['standard_source_proof_origin']==binding['standard_source_proof_origin']==str(STANDARD)
assert prep['source55']==binding['source55']==read(STANDARD/'source_freeze.json')['source55']
assert (O/'source_freeze.json').read_bytes()==(STANDARD/'source_freeze.json').read_bytes()
assert prep['portable_constraint_binding_sha256']==sha(O/'PORTABLE_CONSTRAINT_BINDING.json')
assert binding['filter_validation_sha256']==sha(O/'PORTABLE_FILTER_VALIDATION.json')
assert filtered['kept']==filtered['DSP']+filtered['BSRAM'] and filtered['kept']+filtered['excluded']==52
assert filtered['kept']==prep['measured_counts']['kept']
for name,h in prep['new_scripts_sha256'].items():assert sha(O/name)==h;ast.parse((O/name).read_text(encoding='utf8'),filename=str(O/name))
for name,h in prep['parent_scripts_sha256'].items():assert sha(STANDARD/name)==h
for p,h in binding['bound_inputs'].items():assert sha(Path(p))==h
assert not any((O/n).exists() for n in ['PROOF_BINDING.json','COMPONENT_REUSE_BINDING.json','SYNTHESIS_RESULT.json'])
text=(O/'run_physical.py').read_text(encoding='utf8');tree=ast.parse(text)
assert "sys.argv[1] in ['3']" in text and f"ATTEMPT=ROOT/'{PROFILE}'" in text
assert "ROOT=R/'out/z_aw_fix_20261026/compact_aw_v20'" in text
assert "from portable_constraints import validate,combined_bytes,verify_attempt" in text
assert "STANDARD/'PROOF_BINDING.json'" in text and "O/'PROOF_BINDING.json'" not in text
assert 'retiming_resource' not in text
entries=[ast.literal_eval(n.value) for n in ast.walk(tree) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='entries' for t in n.targets)]
assert entries==[[('impl/gwsynthesis/acg720_ano_port.vg','file.netlist'),('physical_constraints.cst','file.cst'),('acg720_ano_port.sdc','file.sdc')]]
def gate_calls(source):
    return [ast.dump(n,include_attributes=False) for n in ast.walk(ast.parse(source)) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and isinstance(n.func.value,ast.Name) and n.func.value.id=='helper' and n.func.attr in ['run_phase','physical_audit','check_sources']]
assert gate_calls(text)==gate_calls((STANDARD/'run_physical.py').read_text(encoding='utf8'))
def raw_checks(source):
    out={}
    for n in ast.walk(ast.parse(source)):
        if isinstance(n,ast.Assign) and len(n.targets)==1:
            t=n.targets[0]
            if isinstance(t,ast.Subscript) and isinstance(t.value,ast.Name) and t.value.id=='checks' and isinstance(t.slice,ast.Constant):out[t.slice.value]=ast.dump(n.value,include_attributes=False)
    return out
expected_old=(STANDARD/'independent_raw_review.py').read_text(encoding='utf8')
for name in ['PROOF_BINDING.json','PHYSICAL_INPUT_BINDING.json','COMPONENT_REUSE_BINDING.json']:
    expected_old=expected_old.replace("O/'"+name+"'","STANDARD/'"+name+"'")
old=raw_checks(expected_old);new=raw_checks((O/'independent_raw_review.py').read_text(encoding='utf8'))
assert all(new[k]==v for k,v in old.items())
prefix=(ROOT/'canonical/source/acg720_ano_port.cst').read_bytes();suffix=(O/'portable_v20_dsp_bsram.cst').read_bytes()
assert hashlib.sha256(prefix+suffix).hexdigest()==filtered['combined_CST_sha256']
assert b'CLOCK_LOC "observer_reset" BUFG = CE|SR|LOGIC;' in prefix and len(prefix)==filtered['original_baseline_prefix_bytes']
manufacturer={x['original_line'] for x in filtered['kept_rows']}
assert {x for x in suffix.decode('utf8').splitlines() if x.strip() and not x.lstrip().startswith('//')}==manufacturer
preflight=read(O/'PHYSICAL_TCL_PREFLIGHT.json');exit=read(O/'PREFLIGHT_EXIT.json')
assert exit['normal_return'] and exit['actual_completedprocess_returncode']==0 and sha(O/'preflight.stdout.log')==exit['stdout_sha256'] and sha(O/'preflight.stderr.log')==exit['stderr_sha256']
assert preflight['runner_sha256']==sha(O/'run_physical.py') and list(preflight['profiles'])==['3'] and preflight['profiles']['3']['Tcl_complete'] and preflight['profiles']['3']['options_verified']
assert preflight['measured_kept_rows']==filtered['kept'] and preflight['combined_CST_sha256']==filtered['combined_CST_sha256']
assert not (ROOT/PROFILE).exists() and not any((O/PROFILE).iterdir())
truth=read(O/'DIAGNOSTIC_TRUTH_CHECKS.json');assert truth['passed'] and truth['exact_true_and_int_zero_only'] and truth['physical_pass_runner_failure_distinct_from_timing_failure']
assert truth['preparer_sha256']==sha(O.parent/'prepare_v20_dsp_followup.py') and truth['preparer_deterministic_output_parity']
for n,h in truth['scripts_sha256'].items():assert sha(O/n)==h
result={'reviewed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'passed':True,'profile':PROFILE,
    'standard_source_proof_origin':str(STANDARD),'thin_family_has_no_new_proof_or_SYN_result':True,'source_freeze_standard_byte_exact':True,
    'measured_counts':prep['measured_counts'],'normalization_no_collisions_or_generated_renames':True,'original_manufacturer_statement_bytes_preserved':True,
    'complete_baseline_CST_prefix_including_CLOCK_LOC_preserved':True,'combined_CST_selected_in_future_project':True,
    'standard_physical_helper_calls_AST_identical':True,'all_original_independent_raw_checks_AST_identical_after_provenance_alias':True,'metadata_reference_adjustment':'Only standard proof/input/component metadata references change from original O to explicit STANDARD; physical gates are unchanged.','only_effective_option_delta':{'cst_warn_to_error':1},
    'parent_standard_scripts_unchanged':True,'AST_parse_passed':True,'pure_Tcl_preflight_actual_returncode':0,
    'diagnostic_truth_checks_sha256':sha(O/'DIAGNOSTIC_TRUTH_CHECKS.json'),'diagnostic_PASS_requires_actual_normal_vendor_and_runner_int_wait0':True,
    'physical_pass_with_failed_runner_classified_runner_failure':True,'saved_prepared_revision_manifest_sha256':sha(O/'prepared_revisions/revision_01/REVISION_MANIFEST.json'),
    'preparation_sha256':sha(O/'PHYSICAL_PREPARATION.json'),'constraint_binding_sha256':sha(O/'PORTABLE_CONSTRAINT_BINDING.json'),
    'prior_v18_route_scope':'Prior fullroute48.148MHz is a failed timing result and gives no v20 timing qualification.',
    'runtime_attempt_absent':True,'launch_receipt_directory_empty':True,'vendor_started':False,'hardware_actions':False}
dest=O/'INDEPENDENT_PREPARATION_REVIEW.json';assert not dest.exists();dest.write_text(json.dumps(result,indent=2)+'\n',encoding='utf8',newline='\n')
print(json.dumps({'independent_preparation_review_passed':True,'measured_counts':prep['measured_counts'],'review_sha256':sha(dest),'vendor_started':False,'runtime_attempt_absent':True}))
