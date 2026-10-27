"""Rehash exact inherited component evidence; never relabel parent source55 as v21."""
from pathlib import Path
import datetime,hashlib,json
O=Path(__file__).resolve().parent;R=O.parents[3];P=O.parent/'compact_aw_v18'
C=R/'out/z_aw_fix_20261026/compact_aw_v21/canonical/source'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf8'))
current=read(O/'source_freeze.json');expected=current['source55'];before=current['baseline_source55']
assert len(expected)==len(before)==55 and expected!=before
assert [n for n in expected if expected[n]!=before[n]]==['acg720_ano_port.v']
assert all(sha(C/n)==h for n,h in expected.items())
bound={}
def check(path,digest):
    p=Path(path)
    assert not any(part.lower().startswith('.env') or part.lower().endswith('.env') or '.env' in [s.lower() for s in Path(part).suffixes] for part in p.parts)
    assert sha(p)==digest,(str(p),digest);bound[str(p)]=digest
def checked_json(path,digest=None):
    check(path,digest or sha(path));return read(path)
def receipt(path,digest=None,field='actual_p_wait'):
    d=checked_json(path,digest)
    assert d.get('normal_wait_return') is True and d[field]==0 and not d.get('terminated_after_timeout')
    stem=Path(path).name.removesuffix('_exit.json').removesuffix('.exit.json')
    for channel in ['stdout','stderr']:
        if channel+'_sha256' in d:check(Path(path).parent/(stem+'.'+channel+'.log'),d[channel+'_sha256'])
    if 'log_sha256' in d and 'log' in d:check(Path(d['log']),d['log_sha256'])
    return d
parent=checked_json(P/'PROOF_BINDING.json');assert parent['passed'] and parent['source55']==before and parent['actual_proof_runner_wait']==0
parent_inputs=checked_json(P/'proofs/inputs.json',parent['inputs_sha256'])
assert parent_inputs['source55']==before
for p,h in parent_inputs['bound_files'].items():check(p,h)
fsm_deps=['core/ano_flight_state.v','core/height_loss_fallback.v','core/flight_core.v']
assert all(expected[n]==before[n] for n in fsm_deps)
assert parent['flight_state_miter']['passed'] and parent['flight_state_miter']['threshold_vectors']==2097152 and parent['flight_state_miter']['all_internal_and_public_state_bits']
for phase in ['fsm_compile','fsm_vvp']:receipt(P/'proofs'/(phase+'_exit.json'))
assert b'completeFSM' in (P/'proofs/fsm_vvp.stdout.log').read_bytes()
v4=O.parent/'v4_release_proofs';v4result=checked_json(v4/'RESULT.json',parent['parent_proof_sha256'])
v4inputs=checked_json(v4/'inputs.json',v4result['inputs_sha256']);receipt(v4/'runner_exit.json',v4result['runner_exit_sha256'])
controller=Path(v4inputs['reused_controller_proofs']);control=checked_json(controller/'results.json',v4inputs['reused_results_sha256'])
assert control['passed'];receipt(controller/'runner_exit.json')
six=v4inputs['exact_dependencies'];assert len(six)==6
for n,h in six.items():assert expected[n]==before[n]==v4result['source55'][n]==control['source55'][n]==h;check(C/n,h)
assert control['five']['passed'] and control['five']['completed']==5 and control['boundary']['passed'] and control['boundary']['completed']==2 and control['contention']['passed']
assert len(control['stages'])==4
for name,stage in zip(['five','boundary','top','contention'],control['stages']):
    d=receipt(controller/(name+'_exit.json'));assert all(d.get(k)==v for k,v in stage.items())
for case in control['five']['results']:
    assert case['exit_code']==0;base=controller/'five'/case['name'];check(base/'simulation.log',case['log_sha256']);check(base/'trace.csv',case['trace_sha256'])
for case in control['boundary']['results']:
    assert case['exit_code']==0;check(controller/'boundary'/('fraction_'+str(case['fraction']))/'simulation.log',case['log_sha256'])
for n,h in control['contention']['evidence_sha256'].items():
    base=controller/'contention/contention';p=Path(n)
    if not p.is_absolute():p=(controller/'contention' if n=='run.py' else base)/n
    check(p,h)
ground=R/'ground/B0B4/test_results/verification.json';g=checked_json(ground,v4inputs['ground_verification_sha256'])
assert g['result']=='PASS' and len(g['input_sha256'])==43
for n,h in g['input_sha256'].items():
    p=R/n;assert p.resolve().is_relative_to(R);check(p,h)
for tool in ['python','node']:
    assert g[tool]['actual_exit_code']==0;check(ground.parent/(tool+'.log'),g[tool]['log_sha256'])
vybinding=checked_json(P/'VY_BINDING.json',parent['vy_binding_sha256']);vyroot=P/'vy_proofs'
vy=checked_json(vyroot/'RESULT.json',vybinding['result_sha256'])
assert vybinding['passed'] and vybinding['source55']==before and vy['passed'] and vy['source55']==before
assert parent['vy_component_result_sha256']==vybinding['result_sha256']
roles=['root','metric_compile','metric_vvp','uart_mode0_compile','uart_mode0_vvp','uart_mode1_compile','uart_mode1_vvp','geometry_compile','geometry_vvp']
assert set(vy['exit_receipts'])=={'successful_wait_receipts/'+s+'_exit.json' for s in roles}
for n,h in vy['exit_receipts'].items():
    adapter=receipt(vyroot/n,h);original=vyroot/adapter['original_receipt']
    assert vy['original_actual_wait_receipts'][adapter['original_receipt']]==adapter['original_receipt_sha256']
    receipt(original,adapter['original_receipt_sha256'],adapter['original_actual_wait_field'])
vyinputs=checked_json(vyroot/vy['inputs_file'],vy['inputs_sha256']);assert vyinputs['source55']==before
for p,h in vyinputs['bound_files'].items():check(p,h)
vydeps=['sensor/mtf01p_reader.v','sensor/mtf_shared_geometry.v','sensor/mtf_native_geometry.v','position/position_math.v','nav_math_service.v']
assert all(expected[n]==before[n] for n in vydeps)
standalone=R/'analysis/agent_reviews/extension_bram_20261027';sp=checked_json(standalone/'RESULT.json')
assert sp['passed'] and sp['source55']==before and sp['actual_root_wait']==0 and sp['elaboration']['actual_SP_instances']==28
spi=checked_json(standalone/sp['inputs_file'],sp['inputs_sha256'])
for p,h in spi['bound_files'].items():check(p,h)
for n,h in sp['exit_receipts'].items():receipt(standalone/n,h)
assert expected['gw5_snapshot_bram.v']==before['gw5_snapshot_bram.v']
out=dict(passed=True,verified_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),source55=expected,parent_v18_source55=before,
    full_source55_differs=True,exact_changed_files=['acg720_ano_port.v'],parent_v18_proof_binding_sha256=sha(P/'PROOF_BINDING.json'),
    six_exact_controller_dependencies=six,ground_current_inputs_rehashed=43,reused_core_FSM_dependencies={n:expected[n] for n in fsm_deps},
    reused_VY_component_dependencies={n:expected[n] for n in vydeps},reused_VY_result_sha256=vybinding['result_sha256'],
    actual_parent_proof_root_wait=parent['actual_proof_runner_wait'],reused_standalone_vendor_SP_result_sha256=sha(standalone/'RESULT.json'),
    bound_files=bound,tests_rerun=False,
    scope='Parent results retain their actual v18/full prior source55 identity. Only exact unchanged controller/FSM/VY components and ground43 inputs are reused after rehash; the changed top is covered by new v21 default/vendor top13 and actual vendor-SP integration. No new controller/FSM/VY simulations or physical claim.')
assert not (O/'REUSED_BINDINGS_RECHECK.json').exists()
(O/'REUSED_BINDINGS_RECHECK.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf8')
print(json.dumps(dict(passed=True,source55_differs=True,controller_dependencies=6,ground_inputs=43,reused_FSM_dependencies=3,reused_VY_dependencies=5,files_rehashed=len(bound),tests_rerun=False)))
