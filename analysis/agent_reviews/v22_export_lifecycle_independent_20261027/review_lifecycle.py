"""Read-only lifecycle patch review plus one temporary genuine55 roundtrip."""
from pathlib import Path
import ast,datetime,hashlib,importlib.util,json,shutil,sys,tempfile
sys.dont_write_bytecode=True
O=Path(__file__).resolve().parent;R=O.parents[2];D=R/'analysis/agent_reviews/release_lifecycle_20261027'
P=R/'analysis/20261026_z_aw_fix/build/export_qualified_v4.py';VERIFY=R/'firmware/B0B4/verify_release.py'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();read=lambda p:json.loads(Path(p).read_text())
expected_scripts={str(P):'cab893924c892327dc4168254064dfade00c2a4db3c19908dd34c5f58f6552f1',str(VERIFY):'0ba2c0cdca20b7bcf60b34c4d7f2c059762e7f1723f78fa977b0ad4884353cbf'}
assert {p:sha(p) for p in expected_scripts}==expected_scripts
seal_path=D/'RELEASE_LIFECYCLE_VALIDATION_SEALED.json';assert sha(seal_path)=='676f0fda2eda9460dd6c6553ff622572f14f057f9a008789203f8caf8eebc2f1'
seal=read(seal_path);assert seal['passed'] is True and seal['focused_tests']==14 and seal['test_groups']=={'strict_wait_regression':6,'real55_lifecycle':8}
assert seal['real_qualified_package_created'] is False
for path,h in seal['tested_source_script_hashes'].items():assert sha(path)==h,path
for name,row in seal['actual_child_waits'].items():
    path=D/(name+'_exit.json');assert sha(path)==row['receipt_sha256'];j=read(path)
    assert j['normal_wait_return'] is True and type(j['actual_p_wait']) is int and j['actual_p_wait']==0
    for stream in ['stdout','stderr']:assert sha(D/(name+'.'+stream+'.log'))==j[stream+'_sha256']
assert 'Ran 8 tests' in (D/'lifecycle8.stderr.log').read_text() and '\nOK\n' in (D/'lifecycle8.stderr.log').read_text()
assert sha(D/'TEST_MEASUREMENTS.json')==seal['inputs']['test_measurements_sha256']
assert sha(D/'VALIDATION_RESULT.json')==seal['inputs']['validation_result_sha256']
assert sha(D/'previous_48_snapshot/MANIFEST.json')==seal['previous48_snapshot_manifest_sha256']
old_path=O/'export_before_lifecycle_fix.py';assert sha(old_path)=='c52c889b913f9b5d1d0bfcd8d15bd50475b3550175c9245767efbff4dd26e3d2'
oldtree=ast.parse(old_path.read_text());newtree=ast.parse(P.read_text());dump=lambda n:ast.dump(n,include_attributes=False)
oldclass=next(n for n in oldtree.body if isinstance(n,ast.ClassDef) and n.name=='EvidenceCollector');newclass=next(n for n in newtree.body if isinstance(n,ast.ClassDef) and n.name=='EvidenceCollector')
oldmethods={n.name:n for n in oldclass.body if isinstance(n,ast.FunctionDef)};newmethods={n.name:n for n in newclass.body if isinstance(n,ast.FunctionDef)}
assert set(newmethods)==set(oldmethods)|{'freeze_overwrites'}
assert [name for name in oldmethods if dump(oldmethods[name])!=dump(newmethods[name])]==['__init__','blob','_write']
oldfuncs={n.name:n for n in oldtree.body if isinstance(n,ast.FunctionDef)};newfuncs={n.name:n for n in newtree.body if isinstance(n,ast.FunctionDef)}
assert set(newfuncs)==set(oldfuncs) and all(dump(n)==dump(newfuncs[name]) for name,n in oldfuncs.items() if name!='main')
main=newfuncs['main'];freeze_if=[n for n in main.body if isinstance(n,ast.If) and any(isinstance(x,ast.Call) and isinstance(x.func,ast.Attribute) and x.func.attr=='freeze_overwrites' for x in ast.walk(n))]
assert len(freeze_if)==1;idx=main.body.index(freeze_if[0]);assert isinstance(main.body[idx-1],ast.Assert) and isinstance(main.body[idx+1],ast.For)
assert 'backup' in ast.unparse(main.body[idx-1]) and 'before' in ast.unparse(main.body[idx-1])
assert "shutil.copy2(S / p, B4 / 'source' / p)" in ast.unparse(main.body[idx+1])
main.body.remove(freeze_if[0]);assert dump(main)==dump(oldfuncs['main'])
# Source prototypes are read and hashed only, never promoted or edited here.
spec=importlib.util.spec_from_file_location('independent_lifecycle_current_export',P);x=importlib.util.module_from_spec(spec);spec.loader.exec_module(x);v=x.validation
bindings=read(x.HERE.parent/'handoff_20261026/SOURCE_BINDINGS.json')
before=next(value for key,value in bindings['source_sha256'].items() if Path(bindings['roots'][key]).resolve()==(R/'firmware/B0B4/source').resolve())
prototype=R/'firmware/B0B4/source';selected=R/'out/z_aw_fix_20261026/compact_aw_v22/physical_p3r0_01/source'
expected=read(x.HERE/'compact_aw_v22/source_freeze.json')['source55']
assert len(before)==len(expected)==55 and set(before)==set(expected)
assert {n:sha(prototype/n) for n in before}==before and {n:sha(selected/n) for n in expected}==expected
conflicts=[n for n in expected if before[n]!=expected[n]];assert len(conflicts)==10
with tempfile.TemporaryDirectory(prefix='independent_lifecycle_',dir=O) as value:
    root=Path(value).resolve();assert root.is_relative_to(O.resolve())
    old,new,backup,package=[root/n for n in ['initial/source','selected/source','backup55','package']]
    for n in expected:
        for source,dest in [(prototype/n,old/n),(prototype/n,backup/n),(selected/n,new/n),(selected/n,package/'source'/n)]:
            dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,dest)
    c=x.EvidenceCollector(new,expected,dict(repo=R,metadata=root/'meta',source=new,proofs=root/'proofs',donor=root/'donor',attempt=root/'attempt',report=root/'report'))
    for n in expected:c.check(old/n,before[n]);c.check(new/n,expected[n])
    ordinary=root/'unplanned_input.v';ordinary.write_bytes(b'unchanged control input');c.blob(ordinary)
    c.freeze_overwrites({old/n:(backup/n,before[n]) for n in expected})
    assert len(c.frozen_overwrites)==55 and set(c.frozen_overwrites)=={v.evidence_key(old/n) for n in expected}
    for n in expected:shutil.copy2(new/n,old/n)
    assert {n:sha(old/n) for n in expected}==expected
    index_path=c.finish(package);index=read(index_path);archive=v.ArchivedEvidence(package,index)
    for n in expected:
        assert hashlib.sha256(c.blob(old/n,before[n])).hexdigest()==before[n]
        assert hashlib.sha256(archive.blob(old/n,before[n])).hexdigest()==before[n]
        assert hashlib.sha256(archive.blob(new/n,expected[n])).hexdigest()==expected[n]
        assert index['files'][v.evidence_key(old/n)]['sha256']==before[n]
    for n in conflicts:assert not index['files'][v.evidence_key(old/n)]['archive_path'].startswith('source/')
    rejected=[]
    try:c.blob(old/conflicts[0],expected[conflicts[0]])
    except AssertionError as error:rejected.append({'case':'relabel_old_original_key_as_selected','reason':str(error)})
    ordinary.write_bytes(b'changed outside explicit overwrite scope');key=v.evidence_key(ordinary)
    try:c._write(key,package,c.files[key]['archive_path'])
    except AssertionError as error:rejected.append({'case':'unplanned_input_late_drift','reason':str(error)})
    key=v.evidence_key(old/conflicts[0]);c.frozen_overwrites[key]=b'tampered in-memory frozen bytes'
    try:c._write(key,package,c.files[key]['archive_path'])
    except AssertionError as error:rejected.append({'case':'frozen_bytes_tampering','reason':str(error)})
    assert len(rejected)==3 and not (package/'qualification.json').exists()
    fixture_counts={'original_keys':55,'selected_keys':55,'extra_control_key':1,'indexed_keys':len(index['files']),'frozen_keys':55,'actual_conflicts':10}
assert {n:sha(prototype/n) for n in before}==before and {p:sha(p) for p in expected_scripts}==expected_scripts
assert not (R/'firmware/B0B4/qualification.json').exists() and not (R/'firmware/B0B4/release').exists()
result={'approved_lifecycle_fix':True,'reviewed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'production_script_hashes':expected_scripts,'owner_lifecycle_seal_sha256':sha(seal_path),'prepatch_export_sha256':sha(old_path),'confirmed_prepatch_cause':'The old implementation copied selected55 over B4/source before late finish reread10 differing original-key files. verify_release.py and export script are outside the promoted source directory and are not written by main.','patch_scope':'Only explicit55 planned overwrite paths freeze validated backup bytes after complete backup55 hash validation and before promotion. Original-key hash/index is unchanged; selected origins stay separate; blob/_write rehash cached bytes and byte counts; every other input remains live-strict.','main_other_statements_AST_unchanged':True,'all_other_collector_methods_AST_unchanged':True,'owner_actual_test_groups_wait0':{'lifecycle8':0,'strict_wait6':0},'independent_temporary_real55_roundtrip_passed':True,'independent_fixture_counts':fixture_counts,'independent_rejected_cases':rejected,'real_B4_source55_unchanged':True,'real_source_or_production_files_edited':False,'real_qualified_file_or_release_created':False,'vendor_or_hardware_run':False,'full48_suite_rerun_by_reviewer':False,'temporary_archive_cleaned_by_context':True,'review_script_sha256':sha(Path(__file__)),'findings':[],'scope':'Approval of the exact lifecycle patch and focused genuine-byte temporary archive test. This reviewer does not execute real export/promotion or manufacture physical qualification.'}
dest=O/'REVIEW.json';assert not dest.exists();dest.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
