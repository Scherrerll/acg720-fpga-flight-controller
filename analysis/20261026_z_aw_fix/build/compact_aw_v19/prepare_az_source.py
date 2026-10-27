"""Prepare an isolated exact v17/v9 composition; no vendor or hardware calls."""
from pathlib import Path
import datetime,difflib,hashlib,json,shutil

O=Path(__file__).resolve().parent
R=O.parents[3]
OUT=R/'out/z_aw_fix_20261026/compact_aw_v19'
C=OUT/'canonical/source'
B=O.parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf8'))
utc=lambda:datetime.datetime.now(datetime.timezone.utc).isoformat()
write=lambda p,j:p.write_text(json.dumps(j,indent=2,ensure_ascii=False)+'\n',encoding='utf8',newline='\n')
norm=lambda s:s.replace('\r\n','\n')

assert not OUT.exists(),OUT
assert sorted(p.name for p in O.iterdir())==[Path(__file__).name]
parents={}
for v in ['v4','v7','v8','v9','v17']:
    fp=B/f'compact_aw_{v}/source_freeze.json';f=read(fp)
    root=Path(f.get('source_root',R/f'out/z_aw_fix_20261026/compact_aw_{v}/canonical/source'))
    expected=f['source55'];assert len(expected)==55
    actual={p:sha(root/p) for p in expected};assert actual==expected,v
    parents[v]={'root':str(root),'source55':actual,'freeze_path':str(fp),'freeze_sha256':sha(fp)}
V17=Path(parents['v17']['root']);V9=Path(parents['v9']['root']);V8=Path(parents['v8']['root'])
guard=['position/pose_time_adapter.v','acg720_ano_port.v','mtf_xyz_navigation_control.v','position/mtf_shared_height_fusion.v']
retain=['core/ano_flight_state.v','core/flight_core.v','core/height_loss_fallback.v']
six=['position/mtf_xyz_hold_control.v','nav_math_service.v','position/position_math.v','position/ano_xy_stick.v','position/ano_xy_divide36.v','position/ano_z_stick.v']
assert all(parents['v9']['source55'][p]==parents['v8']['source55'][p] for p in guard)
assert all(parents['v9']['source55'][p]==parents['v17']['source55'][p] for p in six)
old=b' reg previous_pose_valid=0;'
new=b' reg previous_pose_valid /* synthesis syn_maxfan = 10 */ =0;'
top9=(V9/'acg720_ano_port.v').read_bytes();assert top9.count(old)==1
top17=(V17/'acg720_ano_port.v').read_bytes()
top4=(Path(parents['v4']['root'])/'acg720_ano_port.v').read_bytes()
assert top4.count(old)==1 and top17==top4.replace(old,new)

def logged_receipt(path,log_suffix='.log'):
    j=read(path);assert j['actual_p_wait']==0 and j['normal_wait_return']
    log=path.with_name(path.name.replace('_exit.json',log_suffix))
    assert sha(log)==j['log_sha256']
    return {'receipt_path':str(path),'receipt_sha256':sha(path),'actual_p_wait':j['actual_p_wait'],
            'normal_wait_return':j['normal_wait_return'],'log_path':str(log),'log_sha256':sha(log),'command':j['command']}

def root_receipt(path,expected):
    j=read(path);assert j['actual_p_wait']==expected and j['normal_wait_return']
    assert sha(Path(j['command'][-1]))==j['runner_sha256']
    for stream in ['stdout','stderr']:
        assert sha(path.parent/f'runner.{stream}.log')==j[f'{stream}_sha256']
    return {'path':str(path),'sha256':sha(path),'actual_p_wait':expected,'normal_wait_return':True,
            'runner_path':j['command'][-1],'runner_sha256':j['runner_sha256'],
            'stdout_sha256':j['stdout_sha256'],'stderr_sha256':j['stderr_sha256']}

P8=B/'compact_aw_v8';P9=B/'compact_aw_v9'
r8p=P8/'proofs_completion02/results.json';r8=read(r8p)
r9p=P9/'proofs_retry02/results.json';r9=read(r9p)
assert r8['passed'] and r9['passed'] and r9['source55']==parents['v9']['source55']
assert r8['source55']=={'v7':parents['v7']['source55'],'v8':parents['v8']['source55']}
for folder in ['proofs','proofs_completion02']:
    assert read(P8/folder/'inputs.json')['source55']==r8['source55']
assert r9['reused_v8_guard_proofs']['results_sha256']==sha(r8p)
assert r9['reused_v8_guard_proofs']['runner_exit_sha256']==sha(P8/'proofs_completion02/runner_exit.json')
actual_stages=[]
for folder,names in [('proofs',['adapter_compile','adapter_simulation','fusion_pre0_compile','fusion_pre0_simulation']),
                     ('proofs_completion02',['fusion_pre1_compile','fusion_pre1_simulation'])]:
    for name in names:actual_stages.append(logged_receipt(P8/folder/f'{name}_exit.json'))
reuse_links=[]
for name in ['adapter_compile','adapter_simulation','fusion_pre0_compile','fusion_pre0_simulation']:
    p=P8/'proofs_completion02'/f'{name}_reuse.json';j=read(p)
    assert j['actual_p_wait']==0 and sha(Path(j['receipt']))==j['receipt_sha256'] and sha(Path(j['log']))==j['log_sha256']
    reuse_links.append({'path':str(p),'sha256':sha(p),**j})
roots={
    'v8_original_failed_root':root_receipt(P8/'proofs/runner_exit.json',1),
    'v8_completion02_success_root':root_receipt(P8/'proofs_completion02/runner_exit.json',0),
    'v9_original_failed_root':root_receipt(P9/'proofs/runner_exit.json',1),
    'v9_retry02_success_root':root_receipt(P9/'proofs_retry02/runner_exit.json',0),
}
v9stages=[]
for kind in ['five','boundary','top','contention']:
    p=P9/'proofs_retry02'/f'{kind}_exit.json';j=read(p)
    assert j['actual_p_wait']==0 and j['normal_wait_return']
    for stream in ['stdout','stderr']:assert sha(p.parent/f'{kind}.{stream}.log')==j[f'{stream}_sha256']
    v9stages.append({'receipt_path':str(p),'receipt_sha256':sha(p),**j})
assert all(r9[k]['passed'] for k in ['five','boundary','top13','contention'])
fixture=R/'analysis/20261026_z_aw_fix/numeric_guard_fusion/completion03/tb.v'
assert sha(fixture)==r8['original_fusion_fixture_sha256']
assert sha(R/'analysis/20261026_z_aw_fix/aw_storage_integration/verify_top_safety.py')==r8['original_top_fixture_sha256']
for folder in ['proofs','proofs_completion02']:
    tb=(P8/folder/'fusion_tb.v').read_text(encoding='utf8');assert 'force ' not in tb and 'release ' not in tb
assert 'force ' not in (P8/'proofs/adapter_tb.v').read_text(encoding='utf8')
for folder in ['proofs','proofs_completion02']:
    assert norm((P8/folder/'v8_height.v').read_text(encoding='utf8'))==norm((V8/'position/mtf_shared_height_fusion.v').read_text(encoding='utf8')).replace('module mtf_shared_height_fusion #(','module height_v8 #(',1)

guard_reuse={
    'rechecked_utc':utc(),'v8_results_path':str(r8p),'v8_results_sha256':sha(r8p),
    'v9_results_path':str(r9p),'v9_results_sha256':sha(r9p),
    'actual_producer_fusion_stages':actual_stages,'completion02_reuse_links':reuse_links,'roots':roots,'v9_stages':v9stages,
    'same_guard_dependencies':{p:parents['v9']['source55'][p] for p in r9['reused_v8_guard_proofs']['identical_dependencies']},
    'six_controller_dependencies':{p:parents['v17']['source55'][p] for p in six},
    'producer_coverage':r8['adapter'],'fusion_coverage':r8['fusion'],
    'scope':{
        'producer_and_fusion_no_DUT_force_or_private_preload':True,
        'producer_four_state_same_public_tuple_checks':444003,
        'fusion_total_cycles':3194862,
        'fusion_PRE0_PRE1_are_range_age_modes':'PRECHECKED_AZ_RANGE=1 on new side in both runs',
        'fusion_fixture_acceleration':'CLK_HZ=5000000 and accelerated sample admission; actual acc_dt_us=11000 and full RTL math services',
        'top13_has_controlled_private_forces':'gate.low_ready/high_hold_count; controller state/cancel; decoded RX and core gate dependencies',
        'historical_failures':'Original v8 proof root failed parsing the completed PRE0 log; completion02 root succeeded. Original v9 launcher failed before tests; retry02 root succeeded. Both original actual_wait1 receipts retained and bound.',
        'limits':'Finite behavior/contract proof, no standalone full-flight, physical timing, or installation qualification',
    },
}

C.mkdir(parents=True)
for rel in parents['v17']['source55']:
    dst=C/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(V17/rel,dst)
for rel in guard:
    if rel!='acg720_ano_port.v':shutil.copyfile(V9/rel,C/rel)
(C/'acg720_ano_port.v').write_bytes(top9.replace(old,new))
actual={p:sha(C/p) for p in parents['v17']['source55']}
assert sorted(p for p in actual if actual[p]!=parents['v17']['source55'][p])==sorted(guard)
assert all(actual[p]==parents['v17']['source55'][p] for p in retain+six)
assert all(actual[p]==parents['v9']['source55'][p] for p in guard if p!='acg720_ano_port.v')
assert len(list(C.rglob('*.*')))==55
diffs={}
for parent in ['v17','v4']:
    root=Path(parents[parent]['root']);diff=''
    for rel in actual:
        if actual[rel]!=parents[parent]['source55'][rel]:
            diff+=''.join(difflib.unified_diff((root/rel).read_text(encoding='utf8').splitlines(True),(C/rel).read_text(encoding='utf8').splitlines(True),fromfile=f'{parent}/{rel}',tofile=f'v19/{rel}'))
    p=O/f'source_changes_from_{parent}.diff';p.write_text(diff,encoding='utf8',newline='\n')
    diffs[parent]={'path':str(p),'sha256':sha(p),'full_diff':diff}
provenance={p:{'parent':'v17','path':str(V17/p),'sha256':parents['v17']['source55'][p]} for p in actual}
for p in guard:provenance[p]={'parent':'v9','path':str(V9/p),'parent_sha256':parents['v9']['source55'][p],'candidate_sha256':actual[p],'transformation':'Only exact previous_pose_valid synthesis syn_maxfan10 comment from v17' if p=='acg720_ano_port.v' else 'byte-exact copy'}
write(O/'GUARD_REUSE_RECHECK.json',guard_reuse)
write(O/'AZ_SOURCE_COMPOSITION.json',{
    'prepared_utc':utc(),'scope':'Isolated exact prior guard + retained v17 landing/fanout composition; DO_NOT_PROGRAM; main owns final freeze/proof binding and SYN/physical scheduling',
    'initial_targets':'OUT root absent; analysis directory contained only this newly created preparation script',
    'source_root':str(C),'parents':parents,'source55':actual,'file_provenance':provenance,'changed_from_v17':guard,
    'retained_v17_core_byte_exact':{p:actual[p] for p in retain},'six_unchanged_controller_dependencies':{p:actual[p] for p in six},
    'top_merge':{'v17_top_is_exact_v4_plus_only_comment':True,'v9_old_line':old.decode(),'v17_new_line':new.decode(),'occurrences_replaced':1},
    'diffs':diffs,'guard_reuse_recheck':{'path':str(O/'GUARD_REUSE_RECHECK.json'),'sha256':sha(O/'GUARD_REUSE_RECHECK.json')},
    'composition_reasoning':[
        'Three guarded module bodies byte-identical to v9/v8; top v9 wiring plus existing v17 synthesis-only previous_pose_valid comment.',
        'Producer initial/reset/cancel az0/flag1; ordinary publication commits held signed32 AZ and inclusive +/-30000 predicate together. Busy/fault/idle branches hold both. No extra public cycle.',
        'PRECHECKED_AZ_RANGE defaults0 in navigation and height fusion, preserving old signed32 compare for default named-port callers. Native top enables1 with same public tuple flag.',
        'No axis-width, original Q16, arithmetic, state-machine, publication-schedule or VY changes. Three v17 core landing/fallback files are byte-exact retained.',
        'Exact guard submodule dependency proofs and unchanged-six controller proofs are reusable local evidence. Fresh combined top13 is required; existing forced fixture scope remains explicit.',
        'Composition does not prove a fresh FPGA implementation or full-flight behavior. Main independently reviews retained core/FSM interaction and performs new source55 freeze, SYN and full real50MHz physical qualification.',
    ],'status':'source_prepared_fresh_top13_pending','no_vendor_or_hardware_actions':True,
})
print(json.dumps({'source_prepared':True,'source_files':55,'changed_from_v17':guard,'retained_core':retain,'guard_reuse_rechecked':True,'composition_sha256':sha(O/'AZ_SOURCE_COMPOSITION.json')}))
