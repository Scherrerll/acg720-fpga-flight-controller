"""Append-only source evidence, derived current catalogue. No builds/process control."""
from pathlib import Path
import collections,datetime,gzip,hashlib,json,re
O=Path(__file__).resolve().parent;R=O.parents[2]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf8'))
normalized={'routefail':'route_failure','route_failure':'route_failure',
    'prephysical_audit_rejection':'prephysical_audit_rejection',
    'fullroute_timingfail':'fullroute_timing_failure','completed_full_route_timing_failure':'fullroute_timing_failure',
    'xml_startupfail':'project_XML_failure','root_requested_duplicate_fallback_cancellation':'cancelled_duplicate_fallback',
    'orchestration_interruption_unknown_exit':'unknown_exit',
    'cancelled_incremental_fallback':'cancelled_duplicate_fallback','full_gate_pass':'qualified_physical_pass',
    'vendor_nonzero_unclassified':'vendor_failure_unclassified',
    'cancelled_dense_mapping_deprioritized':'cancelled_resource_priority',
    'cancelled_after_qualified_selection':'cancelled_after_qualified_selection',
    'cancelled_orphan_after_runner_assertion':'cancelled_orphan_after_runner_assertion'}
rows=[];bindings={}
def bind(p):
    bindings[str(p.relative_to(R))]={'sha256':sha(p),'bytes':p.stat().st_size}
    return str(p.relative_to(O))
for rel in ['raw_terminal_receipts/frozen_11_terminal_20261026/MANIFEST.json','raw_terminal_receipts/followup_closed/MANIFEST.json']:
    path=O/rel;doc=read(path);ref=bind(path)
    for a in doc['attempts']:
        rows.append({'id':a['id'],'classification':normalized[a['classification']],
            'vendor_actual_wait':a.get('actual_p_wait'),'runner_actual_wait':None,
            'runner_wait_note':'See original per-attempt evidence; not reconstructed in this derived catalogue.',
            'unrouted_nets':a.get('unrouted_nets'),'fmax_mhz':None,'source_manifest':ref,'qualified':False})
p=O/'compact_aw_v5_repl1/final/FINAL_STATUS.json';a=read(p)
log=(p.parent/'raw/physical.log').read_text(errors='replace')
counts=re.findall(r'total\s+(\d+)\s+unrouted nets',log,re.I);assert counts
rows.append({'id':'compact_v5_repl1_p3r0','classification':normalized[a['classification']],
    'vendor_actual_wait':a['actual_p_wait'],'runner_actual_wait':None,'unrouted_nets':int(counts[-1]),
    'source_manifest':bind(p),'qualified':False})
for tag,places in [('v6',[1,2,3]),('v7',[3,2]),('v8',[3,2]),('v9',[3,'inc']),('v4_p2_followup',[2]),('v4_p3r1_followup',[3]),('v10',[3,'p1mf60']),('v4_p3mf60_followup',[3]),('v4_timing',[3]),('v4_loc3_followup',[3]),('v4_incplace_loc3_followup',[3]),('v4_p1_followup',[1]),('v4_partial_floorplan_followup',[3]),('v4_data_routing_followup',[3,2]),('v11',[3,2]),('v12',[2,3]),('v13',[3,2]),('v13_map1',[3,2]),('v13_native',[3,2]),('v4_native',[3,2]),('v4_clockbuf1_followup',[3]),('v4_rep1_followup',[3]),('v4_fan100_native',[3,2]),('v14',[3,2]),('v4_incplace_native',[3]),('v15',[3,2]),('v16',[3,2]),('v17',[3,2]),('v18',[3,2]),('v18_dsp_followup',[3]),('v19',[3]),('v20',[3]),('v20_dsp_followup',[3]),('v21',[3]),('v22',[3]),('v22_dsp_followup',[3]),('v22_fan100',[3])]:
    for place in places:
        profile='physical_p3r0_inc_v4_01' if place=='inc' else f'physical_p{place}r0_01'
        if tag=='v4_p3r1_followup':profile='physical_p3r1_01'
        if tag=='v4_p3mf60_followup':profile='physical_p3r0_mf60_01'
        if tag=='v4_loc3_followup':profile='physical_p3r0_inc_loc3_01'
        if tag=='v4_incplace_loc3_followup':profile='physical_p3r0_incplace_loc3_01'
        if tag=='v4_partial_floorplan_followup':profile='physical_p3r0_partial_01'
        if tag=='v4_data_routing_followup':profile=f'physical_p{place}r0_data_route_01'
        if tag=='v4_clockbuf1_followup':profile='physical_p3r0_clkbuf1_01'
        if tag=='v4_rep1_followup':profile='physical_p3r0_rep1_01'
        if place=='p1mf60':profile='physical_p1r0_mf60_01'
        if tag in ['v18_dsp_followup','v20_dsp_followup','v22_dsp_followup']:profile='physical_p3r0_dsploc_01'
        p=O/f'compact_aw_{tag}'/profile/'TERMINAL_MANIFEST.json'
        if not p.is_file():continue
        a=read(p)
        if a['passed']:
            review=read(p.parent/'INDEPENDENT_RAW_REVIEW.json')
            assert review['passed'] and a['vendor_actual_p_wait']==a['runner_actual_p_wait']==0
        unrouted=a.get('unrouted_reports',[])
        if not unrouted:
            raw=p.parent/'terminal_receipts/physical.log.gz'
            if raw.is_file():unrouted=[int(x) for x in re.findall(r'total\s+(\d+)\s+unrouted nets',gzip.decompress(raw.read_bytes()).decode(errors='replace'),re.I)]
        rows.append({'id':f'compact_{tag}_inc_v4_p3r0' if place=='inc' else f'compact_{tag}_p{place}r0','classification':normalized[a['classification']],
            'vendor_actual_wait':a['vendor_actual_p_wait'],'runner_actual_wait':a['runner_actual_p_wait'],
            'unrouted_nets':unrouted[-1] if unrouted else None,
            'fmax_mhz':a.get('fmax_mhz'),'setup_slack_ns':a['checks']['setup']['worst_slack_ns'] if a.get('checks') else None,
            'source_manifest':bind(p),'qualified':a['passed']})
assert len({r['id'] for r in rows})==len(rows)
counts=dict(collections.Counter(r['classification'] for r in rows));qualified=sum(bool(r['qualified']) for r in rows)
out={'generated_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'scope':'Recorded physical trials only. Unknown exit remains unknown; cancellation is separate; running trials omitted. Original manifests unchanged.',
    'recorded_attempts':len(rows),'classification_counts':counts,'qualified_attempts':qualified,
    'attempts':rows,'source_manifests':bindings,
    'note':'The frozen11 manifest is authority for legacy v4 full-route timing detail; fmax fields not present there remain null here. No fabricated historical runner waits.'}
(O/'COMPLETED_ATTEMPTS_CURRENT.json').write_text(json.dumps(out,indent=2)+'\n')
lines=['# 当前已归档物理尝试分类','',f"共{len(rows)}条记录："+'，'.join(f'{k}={v}' for k,v in counts.items())+f'。完整物理门及独立raw复核通过{qualified}项；实体安装另验。', '',
    '| ID | 分类 | vendor/runner wait | 未布通 | Fmax MHz | 原始清单 |','|---|---|---|---|---|---|']
for row in rows:
    val=lambda x:'未知/未收录' if x is None else str(x)
    lines.append(f"| {row['id']} | {row['classification']} | {val(row['vendor_actual_wait'])}/{val(row['runner_actual_wait'])} | {val(row.get('unrouted_nets'))} | {val(row.get('fmax_mhz'))} | [原证据]({row['source_manifest']}) |")
lines += ['', '原始冻结索引、Manifest及失败日志均不改写。unknown-exit不补造退出码；取消不算正常完成；完整布线但setup失败不算合格。当前运行任务见[接续状态](../CONTINUATION_STATUS.md)。', '',
    '最初v8验证驱动解析失败属于软件编排记录，单列在[更正回执](compact_aw_v8/ORCHESTRATION_CORRECTION.json)，不混入物理route失败计数。']
(O/'COMPLETED_ATTEMPTS_CURRENT.md').write_text('\n'.join(lines)+'\n',encoding='utf8')
print(json.dumps({'recorded_attempts':len(rows),'classification_counts':counts,'qualified':qualified},indent=2))
