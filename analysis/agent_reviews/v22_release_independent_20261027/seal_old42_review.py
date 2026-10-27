"""Seal the old42 review and its confirmed wait-scalar finding, without edits/export."""
from pathlib import Path
import copy,datetime,hashlib,importlib.util,json,sys
sys.dont_write_bytecode=True
O=Path(__file__).resolve().parent;R=O.parents[2];D=R/'analysis/agent_reviews/release_20261027'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();read=lambda p:json.loads(Path(p).read_text())
seal_path=D/'V22_RELEASE_VALIDATION_SEALED.json';assert sha(seal_path)=='5eb911a1fffe723212237b1478384aa797501833368427cb5c892b107b8d832a';seal=read(seal_path)
assert seal['passed'] is True and seal['tests']==42 and seal['actual_child_wait']==0
record=Path(seal['test_exit_receipt']['path']);assert sha(record)==seal['test_exit_receipt']['sha256'];j=read(record)
assert j['normal_wait_return'] is True and type(j['actual_p_wait']) is int and j['actual_p_wait']==0 and j['source_script_hashes']==seal['tested_source_script_hashes']
for n,h in seal['logs'].items():assert sha(D/n)==h
assert 'Ran 42 tests' in (D/'v22_final_validation_01.stderr.log').read_text() and '\nOK\n' in (D/'v22_final_validation_01.stderr.log').read_text()
code=O/'reviewed_production_42/verify_release.py';export=O/'reviewed_production_42/export_qualified_v4.py'
assert sha(code)=='ce54d5e501769bf6450f4a17a3e71211353efc5d33fec56957bcc07396b178eb' and sha(export)=='e008e5f35ec0d8fed612c4773b87c57c21dbcb8d447affc54f5e966ec17e860f'
spec=importlib.util.spec_from_file_location('sealed_old42_release_for_review',code);v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v);v.ROOT=R/'firmware/B0B4';v.REPO=R
arc=seal['proof_SYN_and_preparation_test_archives']['v22_dsp'];index_path=Path(arc['path']);assert sha(index_path)==arc['sha256'];index=read(index_path);package=index_path.parents[2]
e=v.ArchivedEvidence(package,copy.deepcopy(index));meta=e.origins['metadata'];proof=e.read(v.original_join(meta,'PROOF_BINDING.json'))
q={'variant':'v22_dsp_p3','profile':v.DSP_PROFILE,'source_sha256':proof['source55'],'functional_binding_sha256':hashlib.sha256(e.blob(v.original_join(meta,'PROOF_BINDING.json'))).hexdigest(),'netlist_sha256':v.DSP22_VG_SHA}
portable=v.validate_v20_portable_preparation(e,q);assert portable['validation']['kept']==33
origin_cases=[]
for key,value in [('metadata',e.origins['physical_metadata']),('physical_metadata',e.origins['metadata']),('donor',v.original_join(e.origins['repo'],'out/z_aw_fix_20261026/compact_aw_v20/build_attempt_01'))]:
    mutated=v.ArchivedEvidence(package,copy.deepcopy(index));mutated.origins[key]=value
    try:v.validate_v20_portable_preparation(mutated,q);rejected=False;reason=''
    except SystemExit as error:rejected=True;reason=str(error)
    assert rejected;origin_cases.append({'changed_origin':key,'rejected':True,'reason':reason})
failed=seal['real_failed_DSP22_rejected'];assert sha(failed['terminal'])==failed['sha256'];terminal=read(failed['terminal'])
assert terminal['passed'] is False and terminal['classification']=='route_failure' and terminal['vendor_actual_p_wait']==terminal['runner_actual_p_wait']==1
exception=read(O/'FAILED_INPUT_EXCEPTION_REVIEW.json');assert exception['passed_exception_boundary_review'] and exception['real_invalid_failed_reference_count']==2
exact=read(O/'EMPTY_SHA_EXACT_KEY_PROBE.json');assert exact['passed']
result={'approved_old42_release_production':False,'reviewed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'Exact old42 source/seal review only; owner strict-wait revision is intentionally a separate closure. No whole42 rerun or qualified file creation.','old42_seal_sha256':sha(seal_path),'actual_42_validation_wait':0,'old_tested_production_hashes':{'export_qualified_v4.py':sha(export),'verify_release.py':sha(code)},'real_v22_TEMP_retry_completion_and_functional_SYN_archive_replay_passed':True,'exact_self_log_emptySHA_exception_count':2,'other_old_immutable_inputs_strictly_checked':17,'exception_negative_cases':exception['targeted_in_memory_cases'],'additional_exact_key_nonemptySHA_case':exact['case'],'standard_DSP_proof_SYN_origin_separation_passed':True,'origin_negative_cases':origin_cases,'real_DSP22_int1_int1_route_failure_retained_and_rejected':True,'original20ns_50MHz_five_slacks_zero_endpoints_18pins_B4_gates_retained':True,'findings':[{'priority':'P2','title':'Require exact integer wait status rather than numeric equality','file':'firmware/B0B4/verify_release.py','line':183,'related_lines':[347,387,1186,1187,1492],'confirmed_behavior':'check_receipt accepts boolFalse/float0.0 as successful actual_p_wait or CompletedProcess returncode; raw_success_receipt likewise. check_failed_receipt accepts boolTrue/float1.0 as original failure1. Proven with in-memory stubs; no qualified artifact generated.','impact':'Invalid scalar receipt types can pass the generic physical/proof/SYN success or preserved-failure gates, contrary to normal exact-int policy. Actual nonzero integer failures remain rejected.','suggestion':'Use type(value) is int with exact0/1 and normal flag isTrue at common and direct wait entry points. Owner has been notified and is fixing separately.'}],'evidence_files':{n:sha(O/n) for n in ['WAIT_TYPE_NEGATIVE_PROBE.json','WAIT_TYPE_ADDITIONAL_PROBE.json','FAILED_INPUT_EXCEPTION_REVIEW.json','EMPTY_SHA_EXACT_KEY_PROBE.json']},'production_or_archived_inputs_edited':False,'qualified_file_created':False,'vendor_or_hardware_used':False,'review_script_sha256':sha(Path(__file__))}
dest=O/'REVIEW_OLD42.json';assert not dest.exists();dest.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ['exception_negative_cases','origin_negative_cases','evidence_files']}))
