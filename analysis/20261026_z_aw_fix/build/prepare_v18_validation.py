"""Independently bind actual component waits and prepare the full candidate proof/SYN contract."""
from pathlib import Path
import ast,datetime,hashlib,json,shutil
O=Path(__file__).resolve().parent;R=O.parents[2];P=O/'compact_aw_v17';M=O/'compact_aw_v18'
C=R/'out/z_aw_fix_20261026/compact_aw_v18/canonical/source';OLD=R/'out/z_aw_fix_20261026/compact_aw_v4/canonical/source'
def safe(p):
    p=Path(p);assert not p.name.lower().startswith('.env') and not p.name.lower().endswith('.env') and '.env' not in [s.lower() for s in p.suffixes]
    assert not p.is_symlink();return p
sha=lambda p:hashlib.sha256(safe(p).read_bytes()).hexdigest()
read=lambda p:json.loads(safe(p).read_text(encoding='utf8'))
change=read(M/'VY_SOURCE_CHANGES.json');expected=change['source55'];parent=read(P/'source_freeze.json');before=parent['baseline_source55']
assert len(expected)==55 and change['baseline_source55']==parent['source55']
assert all(sha(C/n)==h for n,h in expected.items()) and all(sha(OLD/n)==h for n,h in before.items())
D=M/'vy_proofs';result=read(D/'RESULT.json');assert result['passed'] and result['source55']==expected and result['actual_successful_root_wait']==0
assert sha(D/result['inputs_file'])==result['inputs_sha256']
inputs=read(D/result['inputs_file']);assert inputs['source55']==expected and inputs['baseline_source55']==parent['source55']
assert all(sha(Path(n))==h for n,h in inputs['bound_files'].items())
receipts={}
for rel,h in result['exit_receipts'].items():
    path=(D/rel).resolve();assert path.is_relative_to(D.resolve()) and sha(path)==h
    adapter=read(path);assert adapter['normal_wait_return'] and adapter['actual_p_wait']==0 and adapter['schema_adapter_only']
    raw=(D/adapter['original_receipt']).resolve();assert raw.is_relative_to(D.resolve())
    assert sha(raw)==adapter['original_receipt_sha256']==result['original_actual_wait_receipts'][adapter['original_receipt']]
    actual=read(raw);assert actual['normal_wait_return'] and actual[adapter['original_actual_wait_field']]==0
    stem=raw.name.removesuffix('_exit.json').removesuffix('.exit.json')
    for stream in ['stdout','stderr']:
        log=raw.parent/(stem+'.'+stream+'.log');assert sha(log)==actual[stream+'_sha256']
    receipts[rel]=dict(adapter_sha256=h,original_receipt=adapter['original_receipt'],original_sha256=sha(raw),actual_original_wait_field=adapter['original_actual_wait_field'],actual_original_wait=0)
assert len(receipts)==9
binding=dict(verified_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),passed=True,source55=expected,result_sha256=sha(D/'RESULT.json'),inputs_sha256=sha(D/result['inputs_file']),actual_successful_root_wait=0,successfully_rechecked_receipts=receipts,component_source_and_fixture_bindings_rehashed=len(inputs['bound_files']),scope='Independent rehash of real component original Popen waits and log receipts; adapters only rename actual fields. No invented exit or physical qualification.')
assert not (M/'VY_BINDING.json').exists();(M/'VY_BINDING.json').write_text(json.dumps(binding,indent=2)+'\n',encoding='utf8')
basis=read(P/'SOURCE_EQUIVALENCE_BASIS.json')
for n,edits in change['exact_reversible_normalized_text_edits'].items():
    if n in basis['transformations']:basis['transformations'][n]['edits']+=edits
    else:basis['transformations'][n]=dict(edits=edits,baseline_sha256=before[n],reverse_exact_normalized_text=True)
    basis['transformations'][n]['candidate_sha256']=expected[n]
    if (OLD/n).read_bytes()!=(OLD/n).read_text(encoding='utf8').encode() and n not in basis['line_endings_normalized']:basis['line_endings_normalized'].append(n)
for n,t in basis['transformations'].items():
    text=(C/n).read_text(encoding='utf8')
    for a,b in reversed(t['edits']):assert text.count(b)==1;text=text.replace(b,a)
    assert text==(OLD/n).read_text(encoding='utf8')
basis.pop('no_new_state_or_cycle',None);basis['new_private_same_tuple_predicate_bits']=1;basis['no_new_legacy_output_cycle']=True;basis['unchanged_files']=48
basis['scope']='v17 exact original transformations plus same-publication velocity-range predicate. New private predicate FF is real state; all legacy words/cadence and default callers are preserved by separately bound full component proofs. Reverse edits delimit scope, not a replacement for behavioral proof.'
(M/'SOURCE_EQUIVALENCE_BASIS.json').write_text(json.dumps(basis,indent=2)+'\n',encoding='utf8')
review=(P/'source_review.md').read_text(encoding='utf8')+'''\n\n# v18：同拍缓存输入速度范围，保持原数据与公开时序\n\n在精确v17上仅新增四文件的MTF速度范围谓词。metric observer由明确signed32 next_vx/next_vy表达原先条件选择的同一32位字，在每个sample_valid（包括重复时间戳）同拍发布这两字及范围谓词；初始化/复位为零速度及true，未发布时一起保持。未修改解析器、metric_commit、积分/定点算术、有效性/年龄或任何时基。真实增加一位同元组谓词状态，不能声称RTL无新状态；不增加旧输出的周期延迟。nav/shared geometry的参数默认0，原调用者保持原signed32比较，顶层仅对正确连接的新元组显式启用。\n\n独立组件证明包含真实旧/新metric全signed16扫值及signed64参考、两种完整UART模式的全部旧公开位比较、正负999999/1000000/1000001边界与异常/重复/失联恢复、旧/prechecked/default三映射几何模块和9份真实数学服务。实际9份成功compile/vvp/父supervisor等待回执经主会话重新核验，原回执字段仅通过有原SHA的适配记录统一命名。组件证明不等于物理通过，也不能替代新的完整top13及50MHz布线。\n\n相对v4共7文件，48文件字节相同；相对B3共10文件。P/I1000/350gen0、原反积分控制器、50MHz/20ns、18引脚及原唯一radio_rx例外保持。上方各段为父候选沿革；本段说明最终新增范围。\n'''
(M/'source_review.md').write_text(review,encoding='utf8')
b3=read(R/'firmware/B0B3/qualification.json')['source_sha256'];assert sum(expected[n]!=b3[n] for n in expected)==10
freeze=dict(prepared_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),source55=expected,baseline_source55=before,changed_files=list(basis['transformations']),parent_v17_source55=parent['source55'],source_review_sha256=sha(M/'source_review.md'),source_equivalence_basis_sha256=sha(M/'SOURCE_EQUIVALENCE_BASIS.json'),VY_binding_sha256=sha(M/'VY_BINDING.json'))
(M/'source_freeze.json').write_text(json.dumps(freeze,indent=2)+'\n',encoding='utf8')
F=M/'proofs';F.mkdir()
top=(P/'proofs/run_top13.py').read_text(encoding='utf8').replace('compact_aw_v17','compact_aw_v18');(F/'run_top13.py').write_text(top,encoding='utf8')
s=(P/'run_proofs.py').read_text(encoding='utf8').replace('compact_aw_v17','compact_aw_v18').replace('v17','v18')
s=s.replace("basis=read(O/'SOURCE_EQUIVALENCE_BASIS.json')", "vy=read(O/'VY_BINDING.json');assert vy['passed'] and vy['source55']==expected and vy['result_sha256']==sha(O/'vy_proofs/RESULT.json')\nbasis=read(O/'SOURCE_EQUIVALENCE_BASIS.json')")
s=s.replace("[Path(__file__),O/'source_freeze.json'", "[Path(__file__),O/'VY_BINDING.json',O/'vy_proofs/RESULT.json',O/'source_freeze.json'")
s=s.replace("out=dict(passed=True,source55=expected,", "out=dict(passed=True,source55=expected,vy_binding_sha256=sha(O/'VY_BINDING.json'),vy_component_result_sha256=sha(O/'vy_proofs/RESULT.json'),")
s=s.replace("Exact unchanged six controller inputs and ground43 separately rehashed; no physical or installation claim.", "Additional full velocity producer/UART/geometry proof bound in VY_BINDING. Exact unchanged six controller inputs and ground43 separately rehashed; no physical or installation claim.")
ast.parse(s);(M/'run_proofs.py').write_text(s,encoding='utf8')
for n in ['verify_reused_bindings.py','run_synthesis.py','audit_synthesis_only.py','seal_synthesis.py','launch_synthesis_hidden.py']:
    s=(P/n).read_text(encoding='utf8').replace('compact_aw_v17','compact_aw_v18').replace('v17','v18').replace('len(h.EXPECTED_CHANGES)==7','len(h.EXPECTED_CHANGES)==10').replace('len(helper.EXPECTED_CHANGES)==7','len(helper.EXPECTED_CHANGES)==10')
    if n=='run_synthesis.py':s=s.replace("assert reuse['passed']", "vy=read(O/'VY_BINDING.json');assert vy['passed'] and vy['source55']==expected and vy['result_sha256']==sha(O/'vy_proofs/RESULT.json') and proof['vy_binding_sha256']==sha(O/'VY_BINDING.json')\n    assert reuse['passed']")
    ast.parse(s);(M/n).write_text(s,encoding='utf8')
(M/'SYNTHESIS_PREPARATION.json').write_text(json.dumps(dict(scope='v17 original SYN-only gates, explicit10 B3-relative files and successful component/combined proof binding required; all real50MHz gates retained',source55=expected,VY_binding_sha256=sha(M/'VY_BINDING.json')),indent=2)+'\n',encoding='utf8')
print(json.dumps(dict(prepared=True,source55=55,component_actual_receipts_rechecked=9,component_bound_files_rechecked=len(inputs['bound_files']),new_private_predicate_bits=1,new_legacy_output_cycles=0,full_top_and_FSM_pending=True)))
