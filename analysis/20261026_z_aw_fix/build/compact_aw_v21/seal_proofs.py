"""Seal successful retry02 plus exact inherited dependencies; no SYN/PNR claim."""
from pathlib import Path
import datetime,hashlib,json
O=Path(__file__).resolve().parent;R=O.parents[3];D=O/'proofs_retry02';P=O.parent/'compact_aw_v18'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf8'))
result=read(D/'RESULT.json');root=read(O/'proof_retry02_runner_exit.json');freeze=read(O/'source_freeze.json')
expected=freeze['source55'];before=freeze['baseline_source55'];C=R/'out/z_aw_fix_20261026/compact_aw_v21/canonical/source'
assert result['passed'] and result['source55']==expected and result['baseline_source55']==before and result['actual_proof_retry02_runner_wait']==0
assert root['normal_wait_return'] and root['actual_p_wait']==0 and sha(O/'proof_retry02_runner_exit.json')==result['root_exit_sha256']
assert sha(O/'run_proofs_retry02.py')==root['runner_sha256'] and sha(O/'supervise_proofs_retry02.py')==root['supervisor_script_sha256']
assert root['stdout_sha256']==sha(O/'proof_retry02_runner.stdout.log') and root['stderr_sha256']==sha(O/'proof_retry02_runner.stderr.log')
inputs=read(D/'inputs.json');assert sha(D/'inputs.json')==result['inputs_sha256'] and inputs['source55']==expected
for p,h in inputs['bound_files'].items():assert sha(Path(p))==h,p
assert all(sha(C/n)==h for n,h in expected.items())
assert {p.relative_to(C).as_posix() for p in C.rglob('*') if p.is_file()}==set(expected)
roles=['integration8_compile','integration8_vvp','integration12000_compile','integration12000_vvp','top13_default_compile','top13_default_vvp','top13_vendor_compile','top13_vendor_vvp']
exits={}
for role in roles:
    p=D/(role+'_exit.json');rec=read(p)
    assert rec['normal_wait_return'] and rec['actual_p_wait']==0 and not rec.get('terminated_after_timeout')
    assert sha(p)==result['exit_receipts'][p.name]
    for channel in ['stdout','stderr']:assert rec[channel+'_sha256']==sha(D/(role+'.'+channel+'.log'))
    exits[p.relative_to(O).as_posix()]=sha(p)
exits['proof_retry02_runner_exit.json']=sha(O/'proof_retry02_runner_exit.json')
reuse=read(O/'REUSED_BINDINGS_RECHECK.json');assert reuse['passed'] and reuse['source55']==expected and reuse['parent_v18_source55']==before
for p,h in reuse['bound_files'].items():assert sha(Path(p))==h,p
assert len(result['framing'])==6 and all(x['independent_checksums_crc'] and x['bytes']==644 and x['frames']==7 for x in result['framing'])
assert len(result['integration'])==2 and all(x['elaboration']['actual_SP_instances']==28 and x['elaboration']['actual_GSR_instances']==1 and not x['elaboration']['portable_FF_branch'] for x in result['integration'])
assert len(result['top13'])==2 and all(x['passed'] and x['cases']==13 and x['original_stimulus_byte_identical'] for x in result['top13'])
parent=read(P/'PROOF_BINDING.json');assert sha(P/'PROOF_BINDING.json')==reuse['parent_v18_proof_binding_sha256']
out=dict(passed=True,sealed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),source55=expected,baseline_source55=before,
    actual_proof_runner_wait=0,proof_directory='proofs_retry02',inputs_sha256=sha(D/'inputs.json'),new_proof_results_sha256=sha(D/'RESULT.json'),
    exit_receipts=exits,source_review_sha256=sha(O/'source_review.md'),source_equivalence_basis_sha256=sha(O/'SOURCE_EQUIVALENCE_BASIS.json'),
    new_vendor_SP_integration=dict(passed=True,periods=[8,12000],actual_SP_instances=28,actual_GSR_instances=1,extension_bits=888,
        all_public_top_outputs_compared=13,complete_protocol_groups=6,frames=42,bytes=3864,independent_sequence_XOR_CRC=True,
        hold_and_serializer_scheduling_natural=True,forced_boundaries=inputs['integration_forced_boundaries'],no_internal_state_force_or_preload=True,
        pass_lines=[line for item in result['integration'] for line in item['pass_lines']]),
    top13_default=next(x for x in result['top13'] if not x['vendor_branch']),top13_vendor=next(x for x in result['top13'] if x['vendor_branch']),
    parent_v18_proof_binding_sha256=sha(P/'PROOF_BINDING.json'),
    reused_core_FSM=dict(passed=True,reused_not_rerun=True,parent_result=parent['flight_state_miter'],source_dependencies=reuse['reused_core_FSM_dependencies'],parent_full_source55_differs=True),
    reused_VY_components=dict(passed=True,reused_not_rerun=True,parent_result_sha256=reuse['reused_VY_result_sha256'],source_dependencies=reuse['reused_VY_component_dependencies'],parent_full_source55_differs=True),
    reused_controller_dependencies=reuse['six_exact_controller_dependencies'],ground_inputs_rehashed=43,
    preserved_failed_attempt=dict(directory='proofs',root_exit_sha256=sha(O/'proof_runner_exit.json'),actual_root_wait=1,cause='Old fixture sibling module name collision; no behavioral failure or candidate edit.'),
    scope=inputs['scope']+' Parent controller/coreFSM/VY/ground evidence is reused only for exact unchanged dependencies and keeps its original source55; no new physical/SYN acceptance is claimed.')
assert not (O/'PROOF_BINDING.json').exists();(O/'PROOF_BINDING.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf8')
reuse['new_v21_proof_binding_sha256']=sha(O/'PROOF_BINDING.json');reuse['proof_sealer_sha256']=sha(Path(__file__))
(O/'REUSED_BINDINGS_RECHECK.json').write_text(json.dumps(reuse,indent=2)+'\n',encoding='utf8')
(D/'top_safety_results.json').write_text(json.dumps(dict(passed=True,cases=13,original_stimulus_unchanged=True,default_branch_passed=True,vendor_branch_passed=True,vendor_SP_instances=28,scope='Original top13 bytes and inherited forces unchanged; fixture-only GSR root added outside tb.'),indent=2)+'\n',encoding='utf8')
print(json.dumps(dict(passed=True,new_integration_frames=42,top13_default_and_vendor=True,actual_successful_receipts=9,source55_differs_from_parent=True,physical_or_SYN_claim=False)))
