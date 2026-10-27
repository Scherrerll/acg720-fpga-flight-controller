"""Small in-memory negative checks of the exact old42 v22 failure exception only."""
from pathlib import Path
import copy,hashlib,importlib.util,json,sys
sys.dont_write_bytecode=True
O=Path(__file__).resolve().parent;R=O.parents[2];D=R/'analysis/agent_reviews/release_20261027'
seal=json.loads((D/'V22_RELEASE_VALIDATION_SEALED.json').read_text());sha=lambda data:hashlib.sha256(data).hexdigest()
code=O/'reviewed_production_42/verify_release.py';assert sha(code.read_bytes())=='ce54d5e501769bf6450f4a17a3e71211353efc5d33fec56957bcc07396b178eb'
spec=importlib.util.spec_from_file_location('review_old42_verifier_snapshot',code);v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
v.ROOT=R/'firmware/B0B4';v.REPO=R
archive=seal['proof_SYN_and_preparation_test_archives']['v22'];index_path=Path(archive['path']);assert sha(index_path.read_bytes())==archive['sha256']
index=json.loads(index_path.read_text());package=index_path.parents[2]
base=v.ArchivedEvidence(package,copy.deepcopy(index));meta=base.origins['metadata'];a=v.original_join(meta,'proofs_attempt01');d=v.original_join(meta,'proofs_completion02')
immutable=v.validate_v22_failed_inputs(base);assert len(base.invalid_failed_inputs)==2
real_exception_names=set(base.invalid_failed_inputs);assert real_exception_names=={v.original_join(a,f'functional_runner.{s}.log') for s in ['stdout','stderr']}
proof=base.read(v.original_join(meta,'PROOF_BINDING.json'));expected=proof['source55']
assert proof['original_attempt_root_actual_wait']==proof['original_failed_alias_compile_wait']==1
assert proof['actual_alias_retry_root_wait']==proof['actual_completion_runner_wait']==0
# One already-stored v22 archive replay validates the target proof/SYN chain;
# no tests, simulators, export or package generation are invoked.
q={'variant':'v22_p3','source_sha256':expected,'functional_binding_sha256':sha(base.blob(v.original_join(meta,'PROOF_BINDING.json'))),'netlist_sha256':seal['DSP22']['source_SYN_VG_sha256']}
v.validate_functional(base,q);v.validate_synthesis(base,q)
def overlay_case(mode):
    e=v.ArchivedEvidence(package,copy.deepcopy(index));original_blob=e.blob;overrides={}
    p=e.read(v.original_join(meta,'PROOF_BINDING.json'));current=e.read(v.original_join(d,'inputs.json'));old=e.read(v.original_join(a,'inputs.json'))
    stdout=v.original_join(a,'functional_runner.stdout.log')
    oldkey=next(k for k in old['bound_inputs'] if v.original_identity(k) not in {v.original_identity(x) for x in real_exception_names})
    if mode=='third_excluded_output':current['excluded_original_misclassified_outputs'].append(v.original_join(a,'unrelated.stdout.log'))
    elif mode=='waive_unrelated_old_hash':old['bound_inputs'][oldkey]=hashlib.sha256(b'').hexdigest()
    elif mode=='old_self_log_nonempty_declared_sha':old['bound_inputs'][stdout]='0'*64
    elif mode=='current_terminal_log_empty_sha':
        key=next(k for k in current['bound_inputs'] if v.v22_reference(meta,a,k)==stdout);current['bound_inputs'][key]=hashlib.sha256(b'').hexdigest()
    elif mode=='index_extra_exception':e.invalid_failed_inputs[v.original_join(a,'unrelated.log')]=copy.deepcopy(next(iter(e.invalid_failed_inputs.values())))
    elif mode=='index_omitted_exceptions':e.invalid_failed_inputs={}
    else:raise AssertionError(mode)
    def store(path,j):
        data=(json.dumps(j,indent=2)+'\n').encode();overrides[v.evidence_key(path)]=data;return sha(data)
    oldpath=v.original_join(a,'inputs.json');oldsha=store(oldpath,old)
    key=next(k for k in current['bound_inputs'] if v.v22_reference(meta,a,k)==oldpath);current['bound_inputs'][key]=oldsha
    p['inputs_sha256']=store(v.original_join(d,'inputs.json'),current);store(v.original_join(meta,'PROOF_BINDING.json'),p)
    # Match coherent amended inventory hash in the in-memory index references;
    # the case must fail for its semantic exception boundary, not a stale hash.
    for item in e.invalid_failed_inputs.values():item['inventory_sha256']=oldsha
    def blob(path,expected=None):
        key=v.evidence_key(path)
        if key in overrides:
            data=overrides[key]
            if expected is not None:v.require(sha(data)==expected,'Overlay declared hash mismatch')
            return data
        return original_blob(path,expected)
    e.blob=blob
    try:v.validate_v22_failed_inputs(e)
    except (SystemExit,AssertionError) as error:return {'case':mode,'rejected':True,'reason':str(error)}
    return {'case':mode,'rejected':False}
cases=[overlay_case(mode) for mode in ['third_excluded_output','waive_unrelated_old_hash','old_self_log_nonempty_declared_sha','current_terminal_log_empty_sha','index_extra_exception','index_omitted_exceptions']]
assert all(x['rejected'] for x in cases)
out={'passed_exception_boundary_review':True,'reviewed_snapshot_sha256':sha(code.read_bytes()),'sealed_v22_archive_index_sha256':sha(index_path.read_bytes()),'existing_real_functional_and_SYN_archive_replay_passed':True,'real_invalid_failed_reference_count':2,'real_invalid_failed_reference_names':sorted(real_exception_names),'all_other_original_immutable_inputs_checked':len(immutable),'targeted_in_memory_cases':cases,'qualified_or_exported_file_created':False,'producer_or_archive_edited':False,'DUT_tests_or_vendor_executed':False,'scope':'Existing nonqualified proof/SYN test archive read-only replay and in-memory semantic mutations only; no full42 suite rerun.'}
dest=O/'FAILED_INPUT_EXCEPTION_REVIEW.json';assert not dest.exists();dest.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))
