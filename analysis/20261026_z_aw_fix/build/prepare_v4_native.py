"""Prepare proven near-target v4 source for the same native full-project flow."""
from pathlib import Path
import ast, datetime, hashlib, importlib.util, json, shutil, sys, tkinter
O=Path(__file__).resolve().parent;R=O.parents[2];P=O/'compact_aw_v13_native';M=O/'compact_aw_v4_native'
OLD=R/'out/z_aw_fix_20261026/compact_aw_v4/canonical/source'
NEW=R/'out/z_aw_fix_20261026/compact_aw_v4_native/canonical/source'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf8'))
assert not M.exists() and not NEW.exists()
proof_dir=O/'v4_release_proofs';proof_path=proof_dir/'RESULT.json';proof=read(proof_path);root=read(proof_dir/'runner_exit.json')
expected=proof['source55']
assert proof['passed'] and proof['top13_new_exact_source_actual_wait']==root['actual_p_wait']==0 and root['normal_wait_return']
for name,key in [('inputs.json','inputs_sha256'),('runner_exit.json','runner_exit_sha256'),('top_safety_results.json','top13_result_sha256')]:assert sha(proof_dir/name)==proof[key]
assert len(expected)==55 and {n:sha(OLD/n) for n in expected}==expected
b3=read(R/'firmware/B0B3/qualification.json')['source_sha256'];assert len([n for n in expected if expected[n]!=b3[n]])==3
assert expected['position/mtf_xyz_hold_control.v']=='ffddb029cb34a8d2ac8995cc43d85866e273d3d147bb650cfd5d3c66c580b642'
M.mkdir();shutil.copytree(OLD,NEW)
review=M/'source_review.md'
review.write_text('''# v4 同源完整原生工程对照

55份源码逐字节等于冻结v4，仍为B3相对三文件变化：已证明的宽位Z抗积分饱和、共享水平INIT/reset wire1000/350及B4构建身份。普通未饱和P2算式、64位/Q16精度、保护/降级/着陆条件不改。该源曾完整布通49.456MHz、setup−0.220ns/32端点，因此仍不合格，不能下载。

本轮只换构建入口：保留原RTL工程，在一个真实gw_sh进程内完成SYN、实际网表审计成功后PNR。map2/replicate0/area/P3或P2/R0、50MHz/20ns、18引脚和唯一原radio_rx例外不改。原helper字节不动；流程审计区分实际原生SYN与旧VG导入，不改50MHz/五余量/端点/位流/引脚/B4身份/实际退出门。不补造独立SYN进程wait0。

功能由v4_release_proofs/RESULT.json绑定：新跑的准确v4 top13 root实际wait0；五场景、FRAC边界、四客户端及地面站测试按原已验证依赖哈希复用，无新仿真声明。所有失败、v4原始源和旧布通证据保留。

选择该对照是因它仍是最接近50MHz的完整布通参考。若原生流仍差少量时序，但实际完整路由成功，可进一步检查这个真实工程的布局/回标；不能伪造GUI状态或把49.456当50通过。当前只准备，未开始vendor或任何硬件操作。
''',encoding='utf8')
(M/'source_freeze.json').write_text(json.dumps({'prepared_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'source55':expected,'baseline_source55':expected,'changed_files':[],'source_review_sha256':sha(review),
    'parent_proof_binding_sha256':sha(proof_path),'workflow':'native_RTL_project_SYN_audit_PNR_one_vendor_process'},indent=2)+'\n')
(M/'PROOF_BINDING.json').write_text(json.dumps({'passed':True,'source55':expected,'actual_proof_runner_wait':root['actual_p_wait'],
    'parent_proof':str(proof_path),'parent_proof_sha256':sha(proof_path),'actual_top13_runner_exit_sha256':sha(proof_dir/'runner_exit.json'),
    'scope':'Exact v4 source55 reuses actual v4 top13 root0 plus its hash-verified controller/math/ground dependencies. No new simulation claim.'},indent=2)+'\n')
scripts=['run_physical.py','audit_synthesis.py','native_physical_audit.py','seal_terminal.py','independent_raw_review.py','launch_physical_hidden.py','physical_snapshot.py']
for name in scripts:
    text=(P/name).read_text(encoding='utf8').replace('compact_aw_v13_native','compact_aw_v4_native')
    if name=='run_physical.py':
        before="O.parent/'compact_aw_v13/PROOF_BINDING.json'";assert text.count(before)==1
        text=text.replace(before,"O.parent/'v4_release_proofs/RESULT.json'")
    if name in ['run_physical.py','audit_synthesis.py']:
        before='assert len(helper.EXPECTED_CHANGES)==8';assert text.count(before)==1;text=text.replace(before,'assert len(helper.EXPECTED_CHANGES)==3')
    if name=='audit_synthesis.py':
        text=text.replace('compact_aw_v13/build_attempt_01','compact_aw_v4/build_attempt_01').replace('parent_v13_map2','parent_v4_map2')
    ast.parse(text);(M/name).write_text(text,encoding='utf8')
adapt=read(P/'GATE_ADAPTATION.json')
adapt['cloned_native_v13_preparation_sha256']=sha(P/'PREPARATION.json')
adapt['parent_independent_parser_sha256']=sha(P/'independent_raw_review.py')
adapt['new_independent_parser_sha256']=sha(M/'independent_raw_review.py')
adapt['new_physical_auditor_sha256']=sha(M/'native_physical_audit.py')
(M/'GATE_ADAPTATION.json').write_text(json.dumps(adapt,indent=2)+'\n',encoding='utf8')
saved=sys.argv;sys.argv=['run_physical.py','3']
try:
    spec=importlib.util.spec_from_file_location('v4_native_Tcl_only',M/'run_physical.py');worker=importlib.util.module_from_spec(spec);spec.loader.exec_module(worker)
finally:sys.argv=saved
interp=tkinter.Tcl();checks={}
for place in [2,3]:
    tcl=worker.build_tcl((NEW/'build.tcl').read_text(encoding='utf8').splitlines(),place)
    assert interp.call('info','complete',tcl)==1 and tcl.index('run syn')<tcl.index('exec {')<tcl.index('run pnr')
    checks[str(place)]={'Tcl_complete':True,'phase_order_valid':True,'tcl_sha256':hashlib.sha256(tcl.encode()).hexdigest()}
(M/'PREPARATION.json').write_text(json.dumps({'prepared_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'prepared_not_started':True,'script_sha256':{name:sha(M/name) for name in scripts},'Tcl_parse_preflight':checks,
    'parent_native_v13_preparation_sha256':sha(P/'PREPARATION.json'),'scope':'Identical proven v4 RTL55, native flow only. Syntax/Tcl parse only; no vendor/hardware started.'},indent=2)+'\n')
print(json.dumps({'prepared_not_started':True,'source_files':55,'B3_relative_changes':3,'scripts_syntax_valid':7,'vendor_started':False}))
