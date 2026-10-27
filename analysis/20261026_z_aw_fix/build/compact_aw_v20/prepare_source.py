"""Compose exact proved v18 VY and v19 AZ components in new v20 directories only."""
from pathlib import Path
import datetime,difflib,hashlib,json,shutil
O=Path(__file__).resolve().parent;R=O.parents[3];B=O.parent;OUT=R/'out/z_aw_fix_20261026/compact_aw_v20';C=OUT/'canonical/source'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf8'))
write=lambda p,j:p.write_text(json.dumps(j,indent=2,ensure_ascii=False)+'\n',encoding='utf8',newline='\n')
assert not C.exists() and not (O/'source_freeze.json').exists()
assert not OUT.exists() or ((OUT/'failed_preparation_01_source').is_dir() and (O/'PREPARATION_FAILURE_01.json').is_file())
parents={}
for v in ['v4','v8','v9','v17','v18','v19']:
    fp=B/f'compact_aw_{v}/source_freeze.json';f=read(fp);root=R/f'out/z_aw_fix_20261026/compact_aw_{v}/canonical/source'
    assert len(f['source55'])==55 and {n:sha(root/n) for n in f['source55']}==f['source55']
    parents[v]={'root':str(root),'source55':f['source55'],'freeze_path':str(fp),'freeze_sha256':sha(fp)}
V17=Path(parents['v17']['root']);V18=Path(parents['v18']['root']);V19=Path(parents['v19']['root'])
record_path=B/'compact_aw_v18/VY_SOURCE_CHANGES.json';record=read(record_path)
assert record['source55']==parents['v18']['source55'] and record['baseline_source55']==parents['v17']['source55']
C.mkdir(parents=True)
for n in parents['v19']['source55']:
    p=C/n;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(V19/n,p)
component_files={'position/pose_time_adapter.v':'v19','position/mtf_shared_height_fusion.v':'v19','sensor/mtf01p_reader.v':'v18','sensor/mtf_shared_geometry.v':'v18'}
for n,v in component_files.items():shutil.copyfile(Path(parents[v]['root'])/n,C/n)
shared=['acg720_ano_port.v','mtf_xyz_navigation_control.v'];shared_edits={};az_commuting_edits={}
for n in shared:
    s=(V19/n).read_text(encoding='utf8');edits=[]
    for a,b in record['exact_reversible_normalized_text_edits'][n]:
        if n=='mtf_xyz_navigation_control.v' and 'PRECHECKED_HEIGHT_ORIGIN=0)(' in a:
            a=a.replace('PRECHECKED_HEIGHT_ORIGIN=0)(','PRECHECKED_HEIGHT_ORIGIN=0,PRECHECKED_AZ_RANGE=0)(')
            b=b.replace('PRECHECKED_HEIGHT_ORIGIN=0,PRECHECKED_INPUT_VELOCITY=0)(','PRECHECKED_HEIGHT_ORIGIN=0,PRECHECKED_AZ_RANGE=0,PRECHECKED_INPUT_VELOCITY=0)(')
        if n=='acg720_ano_port.v' and '.PRECHECKED_HEIGHT_ORIGIN(1))' in a:
            a=a.replace('.PRECHECKED_HEIGHT_ORIGIN(1))','.PRECHECKED_HEIGHT_ORIGIN(1),.PRECHECKED_AZ_RANGE(1))')
            b=b.replace('.PRECHECKED_HEIGHT_ORIGIN(1),.PRECHECKED_INPUT_VELOCITY(1))','.PRECHECKED_HEIGHT_ORIGIN(1),.PRECHECKED_AZ_RANGE(1),.PRECHECKED_INPUT_VELOCITY(1))')
        assert s.count(a)==1,(n,a);s=s.replace(a,b,1);edits.append([a,b])
    reverse=s
    for a,b in reversed(edits):assert reverse.count(b)==1;reverse=reverse.replace(b,a,1)
    assert reverse==(V19/n).read_text(encoding='utf8');shared_edits[n]=edits
    # Independently compose the AZ delta over v18, adapting only shared parameter-list overlap.
    old=(V17/n).read_text(encoding='utf8').splitlines(True);new=(V19/n).read_text(encoding='utf8').splitlines(True)
    other=(V18/n).read_text(encoding='utf8');az=[]
    for tag,a,b,c,d in difflib.SequenceMatcher(a=old,b=new,autojunk=False).get_opcodes():
        if tag=='equal':continue
        if a==b:
            # Pure insertion: include one unchanged neighboring line as a unique anchor.
            if a>0:a-=1;c-=1
            else:b+=1;d+=1
        x,y=''.join(old[a:b]),''.join(new[c:d])
        x=x.replace('PRECHECKED_HEIGHT_ORIGIN=0)(','PRECHECKED_HEIGHT_ORIGIN=0,PRECHECKED_INPUT_VELOCITY=0)(')
        y=y.replace('PRECHECKED_HEIGHT_ORIGIN=0,PRECHECKED_AZ_RANGE=0)(','PRECHECKED_HEIGHT_ORIGIN=0,PRECHECKED_AZ_RANGE=0,PRECHECKED_INPUT_VELOCITY=0)(')
        x=x.replace('.PRECHECKED_HEIGHT_ORIGIN(1))','.PRECHECKED_HEIGHT_ORIGIN(1),.PRECHECKED_INPUT_VELOCITY(1))')
        y=y.replace('.PRECHECKED_HEIGHT_ORIGIN(1),.PRECHECKED_AZ_RANGE(1))','.PRECHECKED_HEIGHT_ORIGIN(1),.PRECHECKED_AZ_RANGE(1),.PRECHECKED_INPUT_VELOCITY(1))')
        assert other.count(x)==1,(n,x);other=other.replace(x,y,1);az.append([x,y])
    assert other==s,('shared composition does not commute',n)
    reverse=other
    for a,b in reversed(az):assert reverse.count(b)==1;reverse=reverse.replace(b,a,1)
    assert reverse==(V18/n).read_text(encoding='utf8');az_commuting_edits[n]=az
    (C/n).write_text(s,encoding='utf8',newline='\n')
expected={n:sha(C/n) for n in parents['v19']['source55']}
for n,v in component_files.items():assert expected[n]==parents[v]['source55'][n]
core=['core/ano_flight_state.v','core/flight_core.v','core/height_loss_fallback.v']
assert all(expected[n]==parents['v18']['source55'][n]==parents['v19']['source55'][n] for n in core)
b3=read(R/'firmware/B0B3/qualification.json')['source_sha256'];b3changes={n:h for n,h in expected.items() if h!=b3[n]}
assert len(expected)==55 and len(b3changes)==12
assert sorted(n for n in expected if expected[n]!=parents['v19']['source55'][n])==sorted(['sensor/mtf01p_reader.v','sensor/mtf_shared_geometry.v',*shared])
diffs={}
for v in ['v4','v18','v19']:
    root=Path(parents[v]['root']);diff=''
    for n in expected:
        if expected[n]!=parents[v]['source55'][n]:diff+=''.join(difflib.unified_diff((root/n).read_text(encoding='utf8').splitlines(True),(C/n).read_text(encoding='utf8').splitlines(True),fromfile=v+'/'+n,tofile='v20/'+n))
    p=O/f'source_changes_from_{v}.diff';p.write_text(diff,encoding='utf8',newline='\n');diffs[v]={'path':str(p),'sha256':sha(p)}
composition={'prepared_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'New complete v20 source55 differs from both parents. Only named component source files are byte-identical to proved parents; shared top/navigation contain explicit merged wiring/parameters.',
    'source_root':str(C),'parents':parents,'source55':expected,'B3_relative_changes':b3changes,'component_files':{n:{'parent':v,'sha256':expected[n],'byte_exact':True} for n,v in component_files.items()},
    'retained_core_byte_exact':{n:expected[n] for n in core},'shared_VY_edits_over_v19':shared_edits,'shared_AZ_edits_over_v18':az_commuting_edits,'shared_composition_commutes_normalized':True,
    'diffs':diffs,'VY_source_record_path':str(record_path),'VY_source_record_sha256':sha(record_path),'new_private_same_publication_predicate_bits':2,'legacy_public_output_cycle_change':0,
    'no_full_source_parent_identity_claim':True,'vendor_started':False,'hardware_actions':False}
write(O/'SOURCE_COMPOSITION.json',composition)
transformations={}
V4=Path(parents['v4']['root'])
for n in expected:
    if expected[n]==parents['v4']['source55'][n]:continue
    old=(V4/n).read_text(encoding='utf8').splitlines(True);new=(C/n).read_text(encoding='utf8').splitlines(True);spans=[]
    for tag,a,b,c,d in difflib.SequenceMatcher(a=old,b=new,autojunk=False).get_opcodes():
        if tag!='equal':spans.append({'old_start':a,'old_end':b,'new_start':c,'new_end':d,'old_text':''.join(old[a:b]),'new_text':''.join(new[c:d])})
    restored=list(new)
    for e in reversed(spans):restored[e['new_start']:e['new_end']]=e['old_text'].splitlines(True)
    assert restored==old
    transformations[n]={'baseline_sha256':parents['v4']['source55'][n],'candidate_sha256':expected[n],'normalized_line_edit_spans':spans,'reverse_exact_normalized_text':True}
assert len(transformations)==9
write(O/'SOURCE_EQUIVALENCE_BASIS.json',{'scope':'Complete reverse reconstruction establishes change scope only. Added AZ/VY state correctness relies on exact component sources/actual prior receipts and fresh merged-wrapper integration/top13, not reversal.',
    'transformations':transformations,'baseline_source55':parents['v4']['source55'],'unchanged_v4_files':46,'new_private_same_publication_predicate_bits':2,'legacy_public_output_cycle_change':0,
    'default_caller_contract':'PRECHECKED_AZ_RANGE=0 and PRECHECKED_INPUT_VELOCITY=0 select the original full signed32 numeric expressions. Native top enables both and routes each same-publication predicate beside its matching words.',
    'AZ_contract':'initial/reset/cancel AZ0 and flag1; held signed32 AZ and exact inclusive +/-30000 flag publish together; other branches hold public word+flag; original acc validity/fault behavior retained.',
    'VY_contract':'metric vx/vy signed32 words and exact inclusive +/-1000000 flag publish on every sample edge, before duplicate/integration branches; reset zero words/flag1, no-sample holds including link loss; original full-distance numeric validity controls zero publication.',
    'component_proof_limits':'Finite actual component traces and real math with disclosed timer/cadence acceleration; top13 uses controlled private gate/controller/RX forces. Fresh integration must use ordinary producer inputs without forcing DUT state.',
    'core_proof_reuse':'Three retained core files are byte-identical to actual v18 miter inputs. Rehash its real compile/vvp receipts/logs/testbench; no unnecessary new identical FSM run.',
    'no_general_four_state_landing_algebra_or_full_flight_physical_claim':True})
(O/'source_review.md').write_text('''# v20: exact same-publication AZ and velocity guard composition

This is a new55-file input, not a whole-file proof reuse of either parent. It starts from frozen v19 and copies v18 sensor/mtf01p_reader.v and sensor/mtf_shared_geometry.v exactly. The AZ adapter and shared height consumer remain byte-exact v19/v9/v8. Top and navigation wrapper combine only the two parameter/interface/wiring groups. Applying VY over v19 and AZ over v18 yields identical normalized shared sources; both inverse edits reconstruct the respective parent. All three v17 landing/fanout core files remain byte-identical in v18/v19/v20.

There are exactly two new private same-publication predicate bits relative to v4/B3: AZ output range and metric velocity range. Every legacy public word/output retains its original publication cycle. Signed32 axes and velocity words, full64-bit arithmetic and original Q16 precision remain unchanged. AZ reset/cancel gives zero/true, faults and busy/idle holds preserve tuple matching. Velocity reset gives zero words/true; all sample edges publish words and predicate together, including duplicate samples and invalid observations publishing zero; no-sample link-loss holds retain the matching tuple. Both new precheck parameters default off and select the original signed numeric comparisons; native top opts in to both exact predicates.

Complete reverse reconstruction proves edit scope and unchanged residual only. Component correctness must be independently rehashed from actual AZ producer/fusion and VY producer/UART/old-prechecked-default geometry receipts/logs plus exact compiled source dependencies. Shared top/navigation are new and need a fresh full original13-case top test with byte-identical TB and a focused real producer/consumer integration proof. Parent controlled-force top tests and accelerated component timer/cadence scope remain disclosed. No whole-flight behavior or physical timing claim follows.

The unchanged core miter is reused by exact core/testbench/source/log/real compile-vvp receipt hashes; six unchanged controller/math/stick dependencies and43 ground inputs are also rehashed. No identical core miter is rerun. Final SYN-only preparation preserves original helper/auditor hashes and real50MHz qualification gates, with exact12 B3-relative changes. Main and another agent must independently review the new full source/proof preparation before any SYN launch. No vendor, hardware, export or promotion action is performed here.
''',encoding='utf8',newline='\n')
write(O/'source_freeze.json',{'prepared_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'New merged v20 source55 for component-reuse recheck, fresh integration/top13 and reviewed SYN_ONLY; no physical qualification',
    'source_root':str(C),'source55':expected,'baseline_source55':parents['v4']['source55'],'B3_relative_changes':b3changes,'B3_relative_change_count':12,'changed_files':list(transformations),
    'parent_v18_source55':parents['v18']['source55'],'parent_v19_source55':parents['v19']['source55'],'new_private_same_publication_predicate_bits':2,'legacy_public_output_cycle_change':0,
    'source_review_sha256':sha(O/'source_review.md'),'source_equivalence_basis_sha256':sha(O/'SOURCE_EQUIVALENCE_BASIS.json'),'composition_sha256':sha(O/'SOURCE_COMPOSITION.json')})
print(json.dumps({'prepared':True,'source_files':55,'B3_relative_changes':12,'v4_changes':9,'new_private_predicate_bits':2,'legacy_public_output_cycle_change':0,'shared_composition_commutes':True,'vendor_started':False}))
