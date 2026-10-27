"""Independent read-only v22 review. Writes this review directory only; no vendor."""
from pathlib import Path
import ast, datetime, hashlib, importlib.util, json, re, sys
sys.dont_write_bytecode = True
O = Path(__file__).resolve().parent
R = O.parents[2]
M = R/'analysis/20261026_z_aw_fix/build/compact_aw_v22'
A = M/'proofs_attempt01'
B = M/'proofs_alias_retry02'
D = M/'proofs_completion02'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
read = lambda p: json.loads(p.read_text(encoding='utf8'))
checked = {}
def bind(p, expected=None):
    p = Path(p)
    assert not p.name.lower().startswith('.env')
    h = sha(p)
    if expected is not None: assert h == expected, p
    checked[str(p)] = h
    return h
def receipt(p, expected_code=0, supervisor=None, prefix=None):
    j = read(p); bind(p)
    field = 'actual_p_wait' if 'actual_p_wait' in j else 'actual_completedprocess_returncode'
    assert j[field] == expected_code and j.get('normal_wait_return', j.get('normal_return')) is True, p
    assert not j.get('terminated_after_timeout'), p
    if 'runner_sha256' in j: bind(Path(j['command'][-1]), j['runner_sha256'])
    if supervisor is not None: bind(supervisor, j['supervisor_sha256'])
    for stream in ['stdout', 'stderr']:
        if stream+'_path' in j: bind(j[stream+'_path'], j[stream+'_sha256'])
        elif prefix is not None: bind(p.parent/f'{prefix}.{stream}.log', j[stream+'_sha256'])
    return j

ready = read(M/'OFFLINE_READY.json')
bind(M/'OFFLINE_READY.json', '7853eb103ea6bc0fd27e290c9bf4255743f58f8f7196fbb023ffc3c1df65435b')
bind(M/'source_freeze.json', ready['source_freeze_sha256'])
bind(M/'PROOF_BINDING.json', ready['proof_binding_sha256'])
bind(D/'RESULT.json', ready['proof_result_sha256'])
source_review = read(O/'SOURCE_REVIEW.json')
bind(O/'SOURCE_REVIEW.json', '24d418758d744c78754991aa896706f7131c89d9e865de8145a20e145b8b73ea')
assert source_review['source_freeze_sha256'] == ready['source_freeze_sha256']
freeze = read(M/'source_freeze.json'); source = Path(freeze['source_root'])
expected = freeze['source55']
assert expected == source_review['source55'] == ready['source55']
for n, h in expected.items(): bind(source/n, h)
assert len(expected) == 55
pb = read(M/'PROOF_BINDING.json'); result = read(D/'RESULT.json')
assert pb['passed'] and result['passed'] and pb['source55'] == result['source55'] == expected
assert pb['inputs_sha256'] == result['inputs_sha256'] == bind(D/'inputs.json')
for p, h in read(D/'inputs.json')['bound_inputs'].items(): bind(p, h)
for p, h in pb['additional_bound_inputs'].items(): bind(p, h)
for p, h in result['artifacts'].items(): bind(A/p, h)
assert len(pb['fresh_actual_exit_receipts']) == 22
receipt_rows = []
for x in pb['fresh_actual_exit_receipts']:
    p = Path(x['path']); bind(p, x['sha256']); j = receipt(p)
    assert j[x['actual_wait_field']] == 0 and j[x['normal_field']] is True
    receipt_rows.append({'path':str(p),'sha256':sha(p),'actual_wait':0,'command':j['command']})
for stage, count in [('five',6), ('boundary',4), ('contention',2), ('top13',2)]:
    receipt(A/f'{stage}_exit.json', prefix=stage)
    index = read(A/stage/'actual_child_receipts/INDEX.json')
    assert index['passed'] and len(index['receipts']) == count
    bind(A/stage/'run.py' if stage != 'top13' else A/stage/'run_top13.py', index['target_sha256'])
    bind(M/'record_stage.py', index['recorder_sha256'])
    for x in index['receipts']: bind(x['path'], x['sha256']); receipt(Path(x['path']))

original = receipt(A/'functional_runner_exit.json', 1, M/'launch_proofs.py', 'functional_runner')
failed = receipt(A/'alias_compile_exit.json', 1, prefix='alias_compile')
assert (A/'functional_runner.stderr.log').read_text().rstrip().endswith("AssertionError: ('alias_compile', 1)")
assert 'Error opening temporary file' in (A/'alias_compile.stderr.log').read_text()
assert 'Please check TMP or TMPDIR' in (A/'alias_compile.stderr.log').read_text()
assert not (A/'alias_vvp_exit.json').exists() and not (A/'RESULT.json').exists()
old_inputs = read(A/'inputs.json')
excluded = set(read(D/'inputs.json')['excluded_original_misclassified_outputs'])
assert excluded == {str(A/f'functional_runner.{s}.log') for s in ['stdout','stderr']} | {str(A/'functional_runner_process.json')}
for p,h in old_inputs['bound_inputs'].items():
    if p not in excluded: bind(p,h)
assert sha(A/'functional_runner_process.json') == old_inputs['bound_inputs'][str(A/'functional_runner_process.json')]
for name in ['actual_functions.v','alias_tb.v','STRUCTURAL_IDENTITY.json']:
    assert (B/name).read_bytes() == (A/'alias'/name).read_bytes()
for phase in ['compile', 'vvp']: receipt(B/f'{phase}_exit.json', prefix=phase)
receipt(B/'runner_exit.json', supervisor=M/'launch_alias_compile_retry02.py', prefix='runner')
completion = receipt(D/'functional_runner_exit.json', supervisor=M/'launch_completion02.py', prefix='functional_runner')
assert pb['original_attempt_root_actual_wait'] == pb['original_failed_alias_compile_wait'] == 1
assert pb['actual_completion_runner_wait'] == pb['actual_alias_retry_root_wait'] == 0
assert 'PASS actual_alias vectors=53116 signed64=42768 fourstate=10348 all_upper13=8192 low16_reduction_classes=2 function_byte_identical=1' in (B/'vvp.stdout.log').read_text()
top = read(A/'top13/top_safety_results.json'); five = read(A/'five/results.json'); boundary = read(A/'boundary/results.json')
assert top['passed'] and top['cases'] == 13 and five['passed'] and five['completed'] == 5
assert boundary['passed'] and [x['fraction'] for x in boundary['results']] == [0,16]
assert read(A/'contention/contention/results.json')['passed']
assert (A/'top13/top_safety_tb.v').read_bytes() == (M.parent/'v4_release_proofs/top_safety_tb.v').read_bytes()
for local,parent in [('five/aw_tb.v','five/aw_tb.v'),('boundary/boundary_tb.v','boundary/boundary_tb.v'),('contention/contention/contention_tb.v','contention/contention/contention_tb.v')]:
    assert (A/local).read_bytes() == (M.parent/'compact_aw_v9/proofs_retry02'/parent).read_bytes()
for p in [A/'five/aw_tb.v',A/'boundary/boundary_tb.v',A/'contention/contention/contention_tb.v',B/'alias_tb.v']:
    assert not re.search(r'\b(?:force|release)\s+\w', p.read_text()), p
for case in five['results']:
    assert case['exit_code'] == 0 and len(case['checks']) >= 2
    bind(A/'five'/case['name']/'simulation.log',case['log_sha256'])
    bind(A/'five'/case['name']/'trace.csv',case['trace_sha256'])
for case in boundary['results']:
    assert case['exit_code'] == 0 and case['pass_lines']
    bind(A/'boundary'/f"fraction_{case['fraction']}"/'simulation.log',case['log_sha256'])
reuse = read(M/'COMPONENT_REUSE_BINDING.json'); assert reuse['passed'] and reuse['source55'] == expected
assert reuse['new_controller_requires_fresh_proof'] and not reuse['old_six_controller_hashes_claimed_current']
for p,h in reuse['bound_inputs'].items(): bind(p,h)
for group,deps in reuse['unchanged_dependency_sets'].items():
    for n,h in deps.items(): assert expected[n] == source_review['source55'][n] == h
for section,key in [('AZ','actual_compile_sim_receipts'),('VY','actual_compile_sim_receipts'),('reused_core_FSM','actual_compile_vvp_receipts')]:
    for x in reuse[section][key]:
        p=Path(x['path']);bind(p,x['sha256']);j=read(p)
        assert j[x['actual_wait_field']] == x['actual_wait'] == 0
for x in reuse['AZ']['roots_including_historical_failure1'].values():
    bind(x['path'],x['sha256']);assert read(Path(x['path']))['actual_p_wait'] == x['actual_p_wait']
assert reuse['ground_current_inputs_rehashed'] == 43
prep = read(M/'SYNTHESIS_PREPARATION.json'); req = read(M/'SYN_REVIEW_GATE_REQUIREMENTS.json')
assert prep['source55'] == expected and prep['proof_binding_sha256'] == sha(M/'PROOF_BINDING.json')
assert prep['guard_binding_sha256'] == pb['guard_binding_sha256'] == sha(M/'COMPONENT_REUSE_BINDING.json')
assert prep['scripts_sha256'] == req['reviewed_scripts_sha256']
for n,h in prep['scripts_sha256'].items(): bind(M/n,h);ast.parse((M/n).read_text())
bind(R/'firmware/B0B4/build_candidate.py',prep['unchanged_original_helper_sha256'])
bind(M.parent/'compact_aw_v2/run_synthesis.py',prep['unchanged_gain_18port_auditor_sha256'])
assert prep['synthesis_options'] == {'map_option':2,'replicate_resources':0,'max_fanout':200,'opt_goal':'area'}
assert (source/'build.tcl').read_bytes() == (R/'out/z_aw_fix_20261026/compact_aw_v20/canonical/source/build.tcl').read_bytes()
spec=importlib.util.spec_from_file_location('v22_independent_readonly_contract',M/'validation_contract.py')
contract=importlib.util.module_from_spec(spec);spec.loader.exec_module(contract)
assert contract.verify_contract(check_proof=True)['passed']
assert not (M/'SYN_REVIEW_GATE.json').exists()
assert not (R/'out/z_aw_fix_20261026/compact_aw_v22/build_attempt_01').exists()
report={
 'reviewer':'dsp_export_scout','reviewed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'passed':True,'actionable_findings':[],'independent_agent_review_passed':True,
 'scope':'Final source, actual fresh/reused functional proof and dormant SYN-only scripts. Root must independently review and create exact-hash SYN gate; no vendor launched by reviewer.',
 'source_review_sha256':sha(O/'SOURCE_REVIEW.json'),'source_freeze_sha256':sha(M/'source_freeze.json'),
 'proof_binding_sha256':sha(M/'PROOF_BINDING.json'),'guard_binding_sha256':sha(M/'COMPONENT_REUSE_BINDING.json'),
 'offline_ready_sha256':sha(M/'OFFLINE_READY.json'),'completion_result_sha256':sha(D/'RESULT.json'),
 'syn_preparation_sha256':sha(M/'SYNTHESIS_PREPARATION.json'),'reviewed_scripts_sha256':prep['scripts_sha256'],
 'fresh_successful_receipt_count':len(receipt_rows),'actual_wait_history':{'original_suite':1,'original_alias_compile':1,'five_stage':0,'boundary_stage':0,'contention_stage':0,'top13_stage':0,'alias_retry_compile':0,'alias_retry_vvp':0,'alias_retry_root':0,'completion_root':0},
 'original_failure':'Actual alias_compile TEMP/TMPDIR error; no original alias simulation and no original final immutable-input assertion. Old growing self-output inventory is only a latent separate issue.',
 'fresh_coverage':{'five_controller_cases':5,'FRAC':[0,16],'four_clients':True,'top13':13,'alias_vectors':53116,'alias_known_signed64':42768,'alias_fourstate':10348},
 'reuse':'AZ/VY/core FSM exact source dependencies and actual parent receipts/log/input hashes rechecked; 43 unchanged ground inputs. Old controller hash evidence is context only. No whole55 parent identity claim.',
 'gates_reviewed':['source55/B3-relative12','dualguard component binding','actual proof failure history and completion0','two independent reviews bound to five exact script hashes','SYN-only run syn/EOF/no PNR','unchanged original helper + mapped radio/clock + live gain1000/350/18scalar ports','all mapped FF CLK50 + true20ns only original radio falsepath','actual vendor/audit/root0 and raw logs before seal','actual resource/hint effect measurement against sealed v20, no presumed DSP reduction'],
 'limitations':['Original top13 retains controlled private forces/decoded RX and core dependencies; other fresh fixtures have no DUT force/preload.','Contention uses accelerated arrivals, component proof is not full-flight or physical timing.','SUG550 local wire hint is supported; whether function-result hint changes mapping remains actual SYN experiment.','Citation-only erratum: bound source_review.md priority example page31 should be printed page34; candidate docs remain unchanged.'],
 'receipt_rows':receipt_rows,'checked_files':checked,
 'vendor_started':False,'candidate_files_modified':False}
assert not (O/'FINAL_REVIEW.json').exists()
(O/'FINAL_REVIEW.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
(O/'FINAL_REVIEW.md').write_text('v22 final independent offline review passed; no actionable findings.\n\nSource55 and one-file inverse match remain exact. The original root1 is the actual alias TEMP compilation failure; four successful stages, exact-fixture alias compile/vvp/root0, and completion root0 are separately checked. All22 successful receipts, logs, immutable inputs and unchanged guard/FSM/ground dependencies were rehashed. Original top13 is byte-exact and retains its disclosed forces. No whole-flight or physical timing proof is claimed.\n\nThe five exact-hash SYN scripts retain SYN-only, original helper, CLK50/20ns, radio, gain1000/350,18scalar ports, actual vendor/audit/root0 and complete sealing gates. The supported signal-level hint still needs actual mapping measurement. Root must supply its independent review before creating the gate. No vendor was launched and no candidate file was edited.\n\nCitation erratum only: the priority example in SUG550 is printed page34, not31.\n',encoding='utf8')
print(json.dumps({'passed':True,'successful_receipts':22,'checked_files':len(checked),'FINAL_REVIEW_sha256':sha(O/'FINAL_REVIEW.json'),'vendor_started':False}))
