"""Seal four successful stages plus an exact-fixture alias environment retry."""
from pathlib import Path
import datetime,hashlib,json,os,re,sys
sys.dont_write_bytecode=True
O=Path(__file__).resolve().parent;R=O.parents[3];A=O/'proofs_attempt01';D=O/'proofs_completion02';B=O/'proofs_alias_retry02'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf8'))
write=lambda p,j:p.write_text(json.dumps(j,indent=2)+'\n',encoding='utf8')
expected=read(O/'source_freeze.json')['source55'];S=R/'out/z_aw_fix_20261026/compact_aw_v22/canonical/source'
assert {n:sha(S/n) for n in expected}==expected
root=read(A/'functional_runner_exit.json');assert root['normal_wait_return'] and root['actual_p_wait']==1
for stream in ['stdout','stderr']:assert sha(A/f'functional_runner.{stream}.log')==root[f'{stream}_sha256']
error=(A/'functional_runner.stderr.log').read_text(encoding='utf8')
assert error.rstrip().endswith("AssertionError: ('alias_compile', 1)")
failed=read(A/'alias_compile_exit.json');assert failed['normal_wait_return'] and failed['actual_p_wait']==1
for stream in ['stdout','stderr']:assert sha(A/f'alias_compile.{stream}.log')==failed[f'{stream}_sha256']
assert 'Error opening temporary file' in (A/'alias_compile.stderr.log').read_text() and 'Please check TMP or TMPDIR' in (A/'alias_compile.stderr.log').read_text()
assert not (A/'alias_vvp_exit.json').exists()
assert not (A/'RESULT.json').exists() and not (D/'inputs.json').exists()
oldinputs=read(A/'inputs.json');assert oldinputs['source55']==expected
excluded={str(A/f'functional_runner.{stream}.log') for stream in ['stdout','stderr']}|{str(A/'functional_runner_process.json')}
assert excluded<=set(oldinputs['bound_inputs'])
assert sha(A/'functional_runner_process.json')==oldinputs['bound_inputs'][str(A/'functional_runner_process.json')]
assert oldinputs['bound_inputs'][str(A/'functional_runner.stdout.log')]==oldinputs['bound_inputs'][str(A/'functional_runner.stderr.log')]==hashlib.sha256(b'').hexdigest()
immutable={p:h for p,h in oldinputs['bound_inputs'].items() if p not in excluded}
assert all(sha(Path(p))==h for p,h in immutable.items())
assert sha(Path(root['command'][-1]))==root['runner_sha256']
receipts={}
def receipt(path):
 j=read(path)
 if 'actual_p_wait' in j:assert j['normal_wait_return'] and j['actual_p_wait']==0
 else:assert j['normal_return'] and j['actual_completedprocess_returncode']==0
 assert not j.get('terminated_after_timeout')
 receipts[Path(os.path.relpath(path,A)).as_posix()]=sha(path)
 return j
for stage in ['five','boundary','contention','top13']:
 j=receipt(A/f'{stage}_exit.json')
 for stream in ['stdout','stderr']:assert sha(A/f'{stage}.{stream}.log')==j[f'{stream}_sha256']
 idx=read(A/stage/'actual_child_receipts/INDEX.json');assert idx['passed']
 for x in idx['receipts']:assert sha(Path(x['path']))==x['sha256'];receipt(Path(x['path']))
alias_result=read(B/'RESULT.json');assert alias_result['passed'] and alias_result['source55']==expected and alias_result['inputs_sha256']==sha(B/'inputs.json')
assert {p:sha(Path(p)) for p in read(B/'inputs.json')['bound_inputs']}==read(B/'inputs.json')['bound_inputs']
for n,h in alias_result['artifacts'].items():assert sha(B/n)==h
for phase in ['compile','vvp']:
 j=receipt(B/f'{phase}_exit.json');assert sha(B/f'{phase}_exit.json')==alias_result['exit_receipts'][f'{phase}_exit.json']
 for stream in ['stdout','stderr']:assert sha(B/f'{phase}.{stream}.log')==j[f'{stream}_sha256']
alias_root=receipt(B/'runner_exit.json');assert sha(Path(alias_root['command'][-1]))==alias_root['runner_sha256']
for stream in ['stdout','stderr']:assert sha(B/f'runner.{stream}.log')==alias_root[f'{stream}_sha256']
for n in ['actual_functions.v','alias_tb.v','STRUCTURAL_IDENTITY.json']:assert (A/'alias'/n).read_bytes()==(B/n).read_bytes()
five=read(A/'five/results.json');assert five['passed'] and five['completed']==5 and len(five['results'])==5
for item in five['results']:
 assert item['exit_code']==0 and len(item['checks'])>=2
 assert sha(A/'five'/item['name']/'simulation.log')==item['log_sha256']
 assert sha(A/'five'/item['name']/'trace.csv')==item['trace_sha256']
boundary=read(A/'boundary/results.json');assert boundary['passed'] and boundary['completed']==2
assert [x['fraction'] for x in boundary['results']]==[0,16]
for x in boundary['results']:assert x['exit_code']==0 and x['pass_lines'] and sha(A/'boundary'/f"fraction_{x['fraction']}"/'simulation.log')==x['log_sha256']
contention=read(A/'contention/contention/results.json');assert contention['passed']
assert read(A/'top13/top_safety_results.json')['passed'] and read(A/'top13/top_safety_results.json')['cases']==13
assert (A/'top13/top_safety_tb.v').read_bytes()==(O.parent/'v4_release_proofs/top_safety_tb.v').read_bytes()
for a,b in [('five/aw_tb.v',O.parent/'compact_aw_v9/proofs_retry02/five/aw_tb.v'),('boundary/boundary_tb.v',O.parent/'compact_aw_v9/proofs_retry02/boundary/boundary_tb.v'),('contention/contention/contention_tb.v',O.parent/'compact_aw_v9/proofs_retry02/contention/contention/contention_tb.v')]:assert (A/a).read_bytes()==b.read_bytes(),a
assert 'PASS actual_alias vectors=53116 signed64=42768 fourstate=10348 all_upper13=8192 low16_reduction_classes=2 function_byte_identical=1' in (B/'vvp.stdout.log').read_text()
identity=read(A/'alias/STRUCTURAL_IDENTITY.json');assert identity['passed'] and identity['actual_function_byte_identical']
parent=R/'out/z_aw_fix_20261026/compact_aw_v20/canonical/source/position/mtf_xyz_hold_control.v';candidate=S/'position/mtf_xyz_hold_control.v'
assert identity['source_controller_sha256']=={'v20':sha(parent),'v22':sha(candidate)}
fn=r' function signed \[31:0\] quantized_climb_q16;.*? end endfunction'
f0=re.findall(fn,parent.read_text(),re.S);f1=re.findall(fn,candidate.read_text(),re.S);assert len(f0)==len(f1)==1 and f0==f1
assert hashlib.sha256(f0[0].encode()).hexdigest()==identity['function_sha256']
all_old={p.relative_to(A).as_posix():sha(p) for p in A.rglob('*') if p.is_file() and 'tmp' not in p.relative_to(A).parts}
all_old.update({Path(os.path.relpath(p,A)).as_posix():sha(p) for p in B.rglob('*') if p.is_file() and 'tmp' not in p.relative_to(B).parts})
extras=[Path(__file__),O/'launch_completion02.py',O/'run_alias_compile_retry02.py',O/'launch_alias_compile_retry02.py',O/'prepare_source.py',O/'prepare_alias.py',O/'prepare_alias_retry02.py',O/'prepare_alias_retry02_resolved.py',O/'ALIAS_PREPARATION_CORRECTION_02.json',O/'alias_preparation_retry02_exit.json',O/'alias_preparation_retry02.stdout.log',O/'alias_preparation_retry02.stderr.log',O/'FIXTURE_ADAPTATIONS.json',O/'source_freeze.json',O/'SOURCE_CHANGES.json',O/'record_stage.py']
bound={**immutable,**{str(p):sha(p) for p in extras},**{str(S/n):h for n,h in expected.items()},**{str(A/n):h for n,h in all_old.items()}}
write(D/'inputs.json',{'source55':expected,'bound_inputs':bound,'original_attempt_root_actual_wait':1,'original_root_exit_sha256':sha(A/'functional_runner_exit.json'),'original_failure':'alias_compile1: Icarus default TMP/TMPDIR could not open a temporary file; no alias simulation ran in attempt01. Exact-fixture retry with local TMP actually passed compile/vvp/root0.','excluded_original_misclassified_outputs':sorted(excluded),'latent_issue_not_actual_original_failure':'The old runner also misclassified active self stdout/stderr as immutable inputs; it did not reach that final check. Completion binds only finished stable outputs and actual immutable inputs.','scope':'All four original substantive stages are terminal and successful, and the failed alias compile is preserved plus actually rerun with byte-identical fixture in its own retry directory. Source/scripts/oldinputs/receipts are unchanged; no failed DUT assertion is waived.'})
assert {p:sha(Path(p)) for p in bound}==bound
write(D/'RESULT.json',{'passed':True,'source55':expected,'fresh_proof_directory':str(A),'alias_retry_directory':str(B),'actual_alias_retry_root_wait':0,'inputs_sha256':sha(D/'inputs.json'),'original_attempt_root_actual_wait':1,'original_failed_alias_compile_wait':1,'original_root_receipt':str(A/'functional_runner_exit.json'),'original_root_receipt_sha256':sha(A/'functional_runner_exit.json'),'completion_root_receipt_pending_actual_supervisor_wait':True,'exit_receipts_base':str(A),'exit_receipts':receipts,'artifact_base':str(A),'artifacts':all_old,'fresh_controller_dependency_hashes':{n:expected[n] for n in ['position/mtf_xyz_hold_control.v','nav_math_service.v','position/position_math.v','position/ano_xy_stick.v','position/ano_xy_divide36.v','position/ano_z_stick.v']},'new_controller_not_claimed_byte_identical_to_parent':True,'fresh_top13_cases':13,'fresh_five_cases':5,'fresh_fraction_cases':[0,16],'four_client':contention,'alias_identity_sha256':sha(A/'alias/STRUCTURAL_IDENTITY.json'),'scope':'Offline RTL proof plus corrected immutable-input sealing. Four actual successful terminal stages plus exact-fixture alias retry compile/vvp/root0 checked. Original compile1/root1 preserved as TMP environment failure; no failed assertion waived. Completion root must be bound separately after actual p.wait0. Top13 retains original disclosed private forces; other fresh tests have no private DUT force/preload. No vendor or physical timing claim.'})
print(json.dumps({'passed_offline_component_checks':True,'original_attempt_root_actual_wait':1,'actual_completion_root_wait_not_yet_claimed':True,'RESULT_sha256':sha(D/'RESULT.json'),'successful_exit_receipts':len(receipts)}),flush=True)
