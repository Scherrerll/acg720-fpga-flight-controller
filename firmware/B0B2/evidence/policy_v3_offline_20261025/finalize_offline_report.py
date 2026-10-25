"""Freeze the actual offline outcome; never treats routed-but-slow as qualified."""
from datetime import datetime,timezone
from pathlib import Path
import hashlib,importlib.util,json
ROOT=Path(__file__).resolve().parent
REPO=ROOT.parent/'github_publish/acg720-fpga-flight-controller'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
groups=[(ROOT,['final_p1r0','final_p3r0','final_p4r0','final_logic_globals_p2r0','final_live_globals_p4r0','final_replicated_p4r0']),(ROOT/'pwm_timing_candidate_v2',['pwm_p4r0','pwm_live_globals_p4r0'])]
rows=[]
for index,(base,names)in enumerate(groups):
    spec=importlib.util.spec_from_file_location('final_audit_'+str(index),base/'audit_final_policy.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    for name in names:
        trial=base/name;d=module.audit(trial)
        assert d['inputs_passed']
        (trial/'final_policy_audit.json').write_text(json.dumps(d,indent=2)+'\n')
        rows.append(dict(trial=str(trial.relative_to(ROOT)).replace('\\','/'),vendor_returncode=d['vendor_returncode'],routing_passed=d['routing_passed'],unrouted_nets=d['unrouted_nets'],fmax_mhz=d['sta']['fmax_mhz']if d['sta']else None,setup_violations=d['sta']['summaries']['setup']['violated_endpoints']if d['sta']else None,worst_setup_slack_ns=d['sta']['worst_reported_slack_ns']['setup']if d['sta']else None,full_timing_passed=d['full_timing_passed'],pins_passed=d['pins_passed'],identity_passed=d['identity_passed'],canonical_source_matches=d['canonical_source_matches'],netlist_sha256=d['netlist_sha256'],audit_sha256=sha(trial/'final_policy_audit.json')))
best=max((r for r in rows if r['routing_passed']and r['canonical_source_matches']),key=lambda r:r['fmax_mhz'])
assert best['trial']=='final_p4r0'and best['fmax_mhz']==39.234
binding=json.loads((ROOT/'synthesis_final_binding.json').read_text())
result=dict(updated_utc=datetime.now(timezone.utc).isoformat(),status='Routed successfully; required timing remains unresolved',canonical_source=str(REPO/'firmware/B0B2/source'),policy_document=str(REPO/'firmware/B0B2/POLICY_V3.md'),canonical_policy_v3_merged=True,pwm_candidate_merged=False,best_retained_trial=best,physical_qualification_passed=any(r['full_timing_passed']and r['canonical_source_matches']for r in rows),actual_clock_hz=50000000,constraint_period_ns=19.5,timing_exceptions_added=False,source_sha256=binding['source_sha256'],trials=rows,rtl_policy_tests_passed=True,protocol_bytes=644,protocol_frames=7,core_integration_candidate_passed_but_not_adopted=True,cancelled_rejected_prototype='pwm_timing_candidate: component proof passed; actual core raw-command telemetry counterexample found; fixed in v2; old physical jobs safely stopped',owned_active_jobs=[],hardware_accessed=False,flash_changed=False,flight_ready=False,remaining='Long live qualification/geometry/control paths and placement congestion; migrated measures have not closed required timing')
(ROOT/'FINAL_RESULT.json').write_text(json.dumps(result,indent=2)+'\n')
lines=['当前结论：已能布通，50MHz 时序仍未解决。','',
'已将可迁移的优化与用户确认的超时策略落入当前 B0B2 源码。保留的配置为 P4/R0、资源复制关闭，原 17 引脚和 19.5ns 时钟约束保持。供应商正常结束、零未布通、位流身份与引脚检查通过，但 Fmax 仅 39.234MHz；setup 有 1,194 个违例，最差余量 −5.988ns。hold、recovery、removal、最小脉宽均无负余量。','',
'实际 RTL 的策略回归、启动和坏帧/数值拒绝、真实 dt 与恢复、RC/MTF/控制及几何边界检查通过。实际顶层字节状态机输出 644B/7 帧，接收解析与年龄 unavailable/null 语义通过。未伪造样本、dt 或新鲜度。','',
'| 试验 | 未布通 | Fmax MHz | setup 违例 |','|---|---:|---:|---:|']
for r in rows:lines.append(f'| {r["trial"]} | {r["unrouted_nets"]} | {r["fmax_mhz"]if r["fmax_mhz"]is not None else"无完整时序"} | {r["setup_violations"]if r["setup_violations"]is not None else"—"} |')
lines+=['','PWM 第二版通过了 4,194,304 组组件选择/锁存用例、额外 40,000 周期对比，以及实际 flight_core 的原始命令遥测/锁存/PWM 集成对比；但两种物理配置均更慢，因此没有合入。第一版的遥测反例与取消凭据保留。','',
'当前最佳最差路径：IMU 资格有效位 → 姿态/导航有效性 → 高度回退 → 输出锁存，数据路径约 81% 延迟来自连线。资源复制的较差结果把最差路径转移至遥测 bank 选择，PWM 定向副本又转移至偏航有效位和导航控制事件；现有措施不足以完成全局时序收敛。','',
'没有任何候选通过完整物理验收。源码、综合网表哈希、准确配置、完整 STA 和各组失败证据均已保存；没有下载、刷 Flash、串口操作、上电或电机操作。']
(ROOT/'FINAL_RESULT.md').write_text('\n'.join(lines)+'\n',encoding='utf8')
work=json.loads((ROOT/'WORK_STATE.json').read_text());work.update(updated_utc=result['updated_utc'],status=result['status'],owned_active_runs=[],next_actions='No owned vendor jobs active. See FINAL_RESULT.md; no qualified50MHz bitstream. Current canonical source retained; slower PWM proposals not merged.',final_report='FINAL_RESULT.json',physical_qualification_passed=False);(ROOT/'WORK_STATE.json').write_text(json.dumps(work,indent=2)+'\n')
session=json.loads((ROOT/'SESSION_STATE.json').read_text());session.update(updated_utc=result['updated_utc'],sessions={},status=result['status'],pwm_v2_canonical_merged=False,final_report='FINAL_RESULT.json');(ROOT/'SESSION_STATE.json').write_text(json.dumps(session,indent=2)+'\n')
print(json.dumps(dict(status=result['status'],best=best,trials=len(rows),hardware_accessed=False),indent=2))
