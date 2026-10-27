"""Prepare identical proven v13 source for a native RTL-project flow; no build."""
from pathlib import Path
import datetime, hashlib, json, shutil
O=Path(__file__).resolve().parent;R=O.parents[2];P=O/'compact_aw_v13';M=O/'compact_aw_v13_native'
OLD=R/'out/z_aw_fix_20261026/compact_aw_v13/canonical/source'
NEW=R/'out/z_aw_fix_20261026/compact_aw_v13_native/canonical/source'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf8'))
assert not M.exists() and not NEW.exists()
parent=read(P/'PROOF_BINDING.json');expected=parent['source55']
assert parent['passed'] and parent['actual_proof_runner_wait']==0 and len(expected)==55
assert {n:sha(OLD/n) for n in expected}==expected
for name,item in parent['artifacts'].items():
    path=R/name;assert path.resolve().is_relative_to(R) and not path.name.lower().endswith('.env') and not path.name.lower().startswith('.env')
    assert sha(path)==item['sha256']
M.mkdir();shutil.copytree(OLD,NEW)
review=M/'source_review.md'
review.write_text('''# v13 同源完整原生工程流程

55份源码逐字节等于已通过功能证明的v13。仍按原map2/replicate0/area/P3或P2/R0、50MHz/20ns、原18引脚、唯一radio_rx输入例外和B4 UserCode构建。本实验保留原RTL .gprj，在同一gw_sh进程中先run syn，再执行独立Python网表审计，审计成功才run pnr。它不以VG文件替换工程FileList。

依据：现有build_candidate.py及所有接续物理脚本均在独立SYN后创建只含VG/CST/SDC的新physical.gprj；旧自种子增量试验匹配仅2.82%。是否因导入方式丢失上下文仍是未证实的假设。本实验只改变原生工程流程，不改RTL、算法、时钟、精度或接口，也不声称一定改善资源/时序。

原build_candidate.py及其所有旧门保持原字节。新流程的审计明确用真实SYN完成、同进程审计成功、实际原RTL工程和新VG绑定来识别流程，不再把“跳过综合”当作此流程的要求；20ns、50MHz、五类余量非负、setup/hold端点0、完整路由和位流、18引脚/B4身份、vendor与runner真实退出0的验收标准保留。独立raw复核同样要求这些门。若综合审计拒绝，原生脚本必须非零退出，不能继续PNR。

单一gw_sh过程包含SYN和PNR，因此只有该完整vendor进程和Python根驱动的真实p.wait收据；不补造一个单独SYN进程退出0。SYN子阶段由实际EOF、原始报告和审计绑定记录。功能证明按相同55源复用v13及其父链，无新增仿真声明。当前只准备，未启动任何vendor或硬件操作。
''',encoding='utf8')
(M/'source_freeze.json').write_text(json.dumps({'prepared_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'source55':expected,'baseline_source55':expected,'changed_files':[],'source_review_sha256':sha(review),
    'parent_proof_binding_sha256':sha(P/'PROOF_BINDING.json'),'workflow':'native_RTL_project_SYN_audit_PNR_one_vendor_process'},indent=2)+'\n')
(M/'PROOF_BINDING.json').write_text(json.dumps({'passed':True,'source55':expected,'actual_proof_runner_wait':0,
    'parent_proof':str(P/'PROOF_BINDING.json'),'parent_proof_sha256':sha(P/'PROOF_BINDING.json'),
    'parent_artifacts_rechecked':len(parent['artifacts']),'scope':'Identical proven v13 source55 reuses original functional receipts. No new simulation or physical qualification.'},indent=2)+'\n')
print('Prepared identical source55 for native RTL project flow; no vendor/hardware started.')
