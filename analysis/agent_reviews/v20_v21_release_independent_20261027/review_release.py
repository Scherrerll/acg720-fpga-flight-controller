"""Independent read-only review of sealed release-evidence support. No export/main/vendor."""
from pathlib import Path
import ast, datetime, hashlib, importlib.util, json, sys
sys.dont_write_bytecode=True
O=Path(__file__).resolve().parent;R=O.parents[2]
T=R/'analysis/agent_reviews/release_20261027'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf8'))
checked={}
def bind(p,h=None):
 p=Path(p);got=sha(p)
 if h is not None:assert got==h,p
 checked[str(p)]=got
 return got
seal=T/'V20_V21_VALIDATION_SEALED.json'
bind(seal,'6689f00e52332077d7f91ce82b72d83f63f3a6cc7c6a062e4eee5fc535b6f6f2')
s=read(seal);assert s['passed'] and s['actual_child_wait']==0 and s['tests_passed']==29
for p,h in s['production_and_test_sha256'].items():bind(p,h);ast.parse(Path(p).read_text(encoding='utf8'))
test_tree=ast.parse((T/'test_release_evidence.py').read_text())
assert len([n for n in ast.walk(test_tree) if isinstance(n,ast.FunctionDef) and n.name.startswith('test_')])==29
bind(s['test_exit_receipt']['path'],s['test_exit_receipt']['sha256'])
exit=read(Path(s['test_exit_receipt']['path']))
assert exit['normal_wait_return'] and exit['actual_p_wait']==0
assert exit['source_script_hashes']==s['production_and_test_sha256']
for n,h in s['logs'].items():bind(T/n,h)
assert 'Ran 29 tests in 77.349s' in (T/'v20_v21_validation.stderr.log').read_text()
assert (T/'v20_v21_validation.stderr.log').read_text().rstrip().endswith('OK')
export_path=R/'analysis/20261026_z_aw_fix/build/export_qualified_v4.py'
spec=importlib.util.spec_from_file_location('independent_release_export_readonly',export_path)
export=importlib.util.module_from_spec(spec);spec.loader.exec_module(export)
verify=export.validation
archives={};histories=[];actual={}
for family,item in s['proof_SYN_test_archives'].items():
 index_path=Path(item['index']);bind(index_path,item['sha256']);index=read(index_path)
 package=index_path.parents[2];e=verify.ArchivedEvidence(package,index)
 assert len(index['files'])==item['indexed_files'] and len(index['toolchain_prerequisites'])==item['external_toolchain_prerequisites']
 assert len(index['historical_versions'])==item['historical_fixture_versions']
 assert not (package/'qualification.json').exists()
 archives[family]={'index_sha256':sha(index_path),'indexed_files':len(index['files']),'historical_fixture_versions':len(index['historical_versions']),'accepted_physical_package':False}
 for original,versions in index['historical_versions'].items():
  for digest,saved in versions.items():
   data=e.blob(original,digest);assert data==e.blob(saved,digest) and hashlib.sha256(data).hexdigest()==digest
   current_sha=sha(Path(original));assert current_sha!=digest
   histories.append({'original':original,'declared_historical_sha256':digest,'saved':saved,'current_different_sha256':current_sha,'read_exact_saved_bytes':True})
 meta=index['origins']['metadata'];donor=index['origins']['donor']
 join=verify.original_join
 if family=='compact_aw_v20':
  p=e.read(join(meta,'PROOF_BINDING.json'))
  old=e.read(p['historical_failed_functional_root']['path'],p['historical_failed_functional_root']['sha256'])
  retry=e.read(join(verify.proof_directory(meta,p['proof_directory']),'functional_runner_exit.json'),p['functional_root_exit_sha256'])
  top=e.read(p['fresh_top13']['root_exit_path'])
  assert old['actual_p_wait']==1 and retry['actual_p_wait']==top['actual_p_wait']==0
  assert p['fresh_top13']['candidate_top13_total_actual_runs']==1 and p['fresh_top13']['reused_in_retry_after_exact_hash_check']
  assert p['new_private_same_publication_predicate_bits']==2 and p['legacy_public_output_cycle_change']==0
  actual[family]={'original_functional_root':1,'functional_retry_root':0,'unique_top13_root':0,'fresh_top13_actual_runs':1}
 elif family=='compact_aw_v21':
  completion=e.read(join(meta,'audit_retry02/completion_result.json'))
  for name,code in [('synthesis',0),('audit',1)]:assert e.read(join(donor,'verification',name+'_exit.json'))['actual_p_wait']==code
  assert e.read(join(meta,'runner_exit.json'))['actual_p_wait']==1
  for name in ['successful_audit_exit.json','completion_runner_exit.json']:assert e.read(join(meta,'audit_retry02',name))['actual_p_wait']==0
  assert completion['original_vendor_actual_wait']==0 and completion['original_audit_actual_wait']==completion['original_runner_actual_wait']==1
  assert completion['successful_audit_wait']==completion['actual_completion_root_wait']==completion['completion_runner_actual_wait']==0
  assert completion['SYN_rerun'] is False
  sp=e.read(join(meta,'audit_retry02/results_01/strict_SP_clock_audit.json'))
  assert sp['passed'] and sp['actual_SP_count']==28 and sp['all_SP_CLK50'] and sp['common_CE_matches_remaining_core_snapshot']
  assert (sp['READ_MODE'],sp['WRITE_MODE'],sp['BIT_WIDTH'],sp['byte_enable_address'])==(0,1,32,'000f')
  assert sp['reset_constant_zero'] and sp['all_declared_INIT_RAM_zero'] and sp['last_bank_padding_zero'] and sp['remaining_extension_FF']==[]
  actual[family]={'original_SYN':0,'original_audit':1,'original_root':1,'new_audit':0,'new_completion_root':0,'actual_SP':28,'SYN_rerun':False}
assert len(histories)==2
thin=R/'analysis/20261026_z_aw_fix/build/compact_aw_v20_dsp_followup'
binding=read(thin/'PORTABLE_CONSTRAINT_BINDING.json');bind(thin/'PORTABLE_CONSTRAINT_BINDING.json')
assert binding['measured_counts']=={'official_export_rows':52,'kept':41,'excluded':11,'DSP':39,'BSRAM':2}
assert binding['VG_sha256']=='bb2d4a6d20184a0c38739b550d2fc04adf9fe9ce219106064a2051edbc26274f'
assert Path(binding['standard_source_proof_origin'])==thin.parent/'compact_aw_v20'
assert not (thin/'PROOF_BINDING.json').exists()
assert export.profiles['v20_dsp_p3']==('compact_aw_v20_dsp_followup','compact_aw_v20','physical_p3r0_dsploc_01')
assert export.functional_metadata('v20_dsp_p3',thin)==thin.parent/'compact_aw_v20'
assert sha(export_path)==s['production_and_test_sha256'][str(export_path)]
verifier=R/'firmware/B0B4/verify_release.py';assert sha(verifier)==s['production_and_test_sha256'][str(verifier)]
out={'passed':True,'reviewer':'dsp_export_scout','reviewed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'actionable_findings':[],'production_files_modified':False,'vendor_started':False,'export_or_promotion_performed':False,
 'scope':'Independent code review of production exporter/verifier; reused the exact sealed actual29-test evidence, without rerunning that suite. Additional read-only demonstration resolves both historical versions from the saved archive by declared SHA.',
 'production_sha256':{str(export_path):sha(export_path),str(verifier):sha(verifier)},
 'sealed_test_manifest_sha256':sha(seal),'sealed_tests':{'actual_child_wait':0,'passed':29,'receipt_sha256':sha(Path(s['test_exit_receipt']['path']))},
 'actual_archived_history':actual,'historical_resolution':histories,'proof_SYN_archives':archives,
 'DSP20_counts':binding['measured_counts'],'DSP20_proof_origin':binding['standard_source_proof_origin'],
 'facts':[
  {'file':str(export_path),'line':45,'fact':'Historical versions register immutable in-repo saved copies by expected digest; blob/read/size select that version before checking/reading bytes. Current snapshots and old receipts are not rewritten.'},
  {'file':str(verifier),'line':97,'fact':'ArchivedEvidence checks index/origin paths, tool prerequisites and saved version digests; expected-SHA lookup resolves saved bytes before read parses them.'},
  {'file':str(verifier),'line':401,'fact':'v20 uses its own source55/B3-relative12, retry functional root0, unique original-byte top13 childroot0, integration/default callers, original root1, exact historic snapshots and named parent components.'},
  {'file':str(verifier),'line':481,'fact':'v21 uses source55 distinct from v18 baseline, eight compile/simulation roles plus actual root, official full model, actual28SP/GSR elaboration, standalone vendor proof and preserved initial proof failure.'},
  {'file':str(verifier),'line':964,'fact':'v21 preserves original SYN0/audit1/root1 and requires reviewed audit-only completion with successful audit0/completion0 on original VG. Explicit escaped aliases/CE Boolean proof and protected strict SP mode/address/reset/init/padding/CLK50 gates remain required.'},
  {'file':str(verifier),'line':706,'fact':'DSP20 thin family uses standardv20 source/proof/SYN origin, fixed actual sealed VG, exact52-to41 filter (39DSP+2BSRAM), complete original CST prefix including observer_reset CLOCK_LOC, suffix-only INS_LOC and cst_warn_to_error1.'},
  {'file':str(export_path),'line':275,'fact':'No promotion before successful terminal/raw review, actual physical vendor/root0, full source/VG/raw artifact hashes and nonnegative50MHz timing gates; full evidence closure validates before B4 source replacement.'},
  {'file':str(verifier),'line':876,'fact':'Release verification additionally requires exact five finite nonnegative slack types,20ns/50MHz/zero endpoints,18pin raw review, source/VG/fs/project/constraints and actual exits, donor/SYN/functional closure.'},
  {'file':str(R/'firmware/B0B4/build_candidate.py'),'line':140,'fact':'Unchanged helper criteria retain fullroute/bitstream/no-unrouted, EOF, netlist-only,18pin/B16/B15,B4 fs+cfg and five timing gates; raw review independently parses these.'},
  {'file':str(verifier),'line':1243,'fact':'v20/v21 archive index and every object must be release-manifest bound before standard evidence validation. These test archives have no qualification.json and cannot qualify a physical release.'}],
 'limits':['No release export or source promotion was attempted; standardv20 active physical execution was not inspected or changed.','Saved artifact verification does not rerun simulation, mapped audit, routing or hardware. Actual29 tests cover positive proof/SYN archive roundtrip and missing/wrong-role/hash/source/SP/history/physical negatives, not a successful50MHz physical package.'],
 'checked_files':checked}
assert not (O/'REVIEW.json').exists()
(O/'REVIEW.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf8')
(O/'REVIEW.md').write_text('Independent release support review passed; no actionable findings.\n\nReviewed exporter0aca1135 and verifier645e3024 against sealed actual29-test wait0 evidence6689f00e. The test suite was not rerun. Both historical v20 snapshots independently resolve by declared SHA to their immutable saved bytes, while current paths have different hashes. v20 retains oldroot1/retry0 and one fresh top13; v21 retains SYN0/audit1/root1 plus audit0/completion0, with actual28SP/escaped-port/CE Boolean/CLK50/mode/init/padding gates.\n\nDSP20 remains a41-row physical thin layer with standardv20 proof/SYN origin and full original CST prefix. Fullroute,20ns/50MHz, five finite nonnegative slacks, zero endpoints,18pins,B4 and actual vendor/root0 gates remain in the unchanged helper, independent raw review and export/verification evidence closure. Stored proof/SYN test archives have no accepted physical qualification.\n\nNo production file, source, old receipt or live attempt was changed. No vendor, export, promotion or hardware operation occurred. See REVIEW.json for exact path:line facts and evidence hashes.\n',encoding='utf8')
print(json.dumps({'passed':True,'findings':0,'reused_actual_tests':29,'historical_saved_versions_independently_resolved':2,'REVIEW_sha256':sha(O/'REVIEW.json')}))
