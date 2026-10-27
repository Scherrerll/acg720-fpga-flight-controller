# 最低杆修复候选：物理尝试索引

生成UTC：`2026-10-26T06:31:50.270988+00:00`。仅索引已有回执；没有新构建、进程操作或改写封存记录。

**10项真实终态：9项路由失败、1项项目XML解析失败；全部actual p.wait=1，均无TR/FS。当前没有选中或通过完整物理门的候选。**

所有正常profile保持20ns、global50、map按表、repl0、UserCodeB4；TD0只改变该条执行优化优先级，验收门未放宽。时间均为UTC。

| ID / 源hold前缀 | Place/Route · map · TD | 开始→真实结束 | wait | 结果 / unrouted | TR/FS | 终态导航 |
|---|---|---|---:|---|---|---|
| `first_p3r0` / `5a928e0a` | 3/0 · 2 · 1 | 03:36:58→04:01:46 | 1 | 路由失败 / 1416 | 无/无 | [报告](attempt_01_failure.json) · [原exit](../../../out/z_aw_fix_20261026/build_attempt_01/verification/physical_exit.json) |
| `first_p2r0` / `5a928e0a` | 2/0 · 2 · 1 | 04:03:13→04:37:46 | 1 | 路由失败 / 721 | 无/无 | [报告](p2r0/PHYSICAL_RESULT.md) · [原exit](../../../out/z_aw_fix_20261026/build_attempt_02/verification/physical_exit.json) |
| `first_p3r1` / `5a928e0a` | 3/1 · 2 · 1 | 04:04:13→04:58:45 | 1 | 路由失败 / 10483 | 无/无 | [报告](attempt_03_failure.json) · [原exit](../../../out/z_aw_fix_20261026/build_attempt_03/verification/physical_exit.json) |
| `compact_v1_project01` / `479f7571` | 3/0 · 2 · 1（仅请求） | 04:22:16→04:22:17 | 1 | XML解析失败；未进入布局 | 无/无 | [报告](compact_aw/project_retry_provenance.json) · [原exit](../../../out/z_aw_fix_20261026/compact_aw_v1/physical_p3r0_01/verification/physical_exit.json) |
| `compact_v1_p3r0` / `479f7571` | 3/0 · 2 · 1 | 04:24:18→05:07:10 | 1 | 路由失败 / 746 | 无/无 | [报告](compact_aw/FINAL_STATUS.json) · [原exit](../../../out/z_aw_fix_20261026/compact_aw_v1/physical_p3r0_02/verification/physical_exit.json) |
| `compact_v2_map2_p2r0` / `afc65682` | 2/0 · 2 · 1 | 04:52:50→05:46:45 | 1 | 路由失败 / 792 | 无/无 | [报告](compact_aw_v2/PHYSICAL_RESULT.md) · [原exit](../../../out/z_aw_fix_20261026/compact_aw_v2/physical_p2r0_01/verification/physical_exit.json) |
| `compact_v2_map1_p3r0` / `afc65682` | 3/0 · 1 · 1 | 05:05:16→05:43:21 | 1 | 路由失败 / 667 | 无/无 | [报告](compact_aw_v2_map1/physical_failure.json) · [原exit](../../../out/z_aw_fix_20261026/compact_aw_v2/map1_physical_p3r0_01/verification/physical_exit.json) |
| `compact_v3_p3r0` / `9aa6a51a` | 3/0 · 2 · 1 | 05:27:30→06:06:03 | 1 | 路由失败 / 898 | 无/无 | [报告](compact_aw_v3/FINAL_STATUS.json) · [原exit](../../../out/z_aw_fix_20261026/compact_aw_v3/physical_p3r0_01/verification/physical_exit.json) |
| `compact_v3_p2r0_nt0` / `9aa6a51a` | 2/0 · 2 · 0 | 05:34:12→06:11:50 | 1 | 路由失败 / 1073 | 无/无 | [报告](compact_aw_v3_nt0/RESULT.md) · [原exit](../../../out/z_aw_fix_20261026/compact_aw_v3/physical_p2r0_nt0_01/verification/physical_exit.json) |
| `compact_v3_p1r2` / `9aa6a51a` | 1/2 · 2 · 1 | 05:41:27→06:16:42 | 1 | 路由失败 / 1096 | 无/无 | [报告](compact_aw_v3_p1r2/RESULT.md) · [原exit](../../../out/z_aw_fix_20261026/compact_aw_v3/physical_p1r2_01/verification/physical_exit.json) |

XML项目错误单独保留，unrouted为null，不能记为“0条未布通”或算作算法路由失败。其后fresh重建项目的尝试另有独立条目。每项完整源55指纹、实际VG哈希、执行Tcl/profile、raw exit/log/rpt/input及轻量终态报告/manifest哈希均在 [ATTEMPTS.json](ATTEMPTS.json)，没有复制vendor大文件。map1条的source/build.tcl仍map2，实际map1通过独立执行配置和对应不同donor VG绑定。

## 未结束任务：仅历史快照

快照UTC：`2026-10-26T06:31:50.237291+00:00`。下列v4任务由其他agent独占；此索引只读原process/input/log前缀，未查询进程活性、未监控或操作任务，不纳入10项终态。

| fixture | profile | receipt PID（vendor/helper） | 快照所见 |
|---|---|---|---|
| `out/z_aw_fix_20261026/compact_aw_v4/physical_p3r0_01` | 3/0 · map2 · TD1 | 27944/61420 | 无exit回执；TR/FS=False/False；[70%] Routing Phase 1 completed |
| `out/z_aw_fix_20261026/compact_aw_v4/physical_p4r0_01` | 4/0 · map2 · TD1 | 9908/61780 | 无exit回执；TR/FS=False/False；[60%] Routing Phase 0 completed |

## 源码保留与后续选择

五个固定实现原始字节在 [implementation_history/HISTORY.json](../implementation_history/HISTORY.json)：5份hold、共同bank与build.tcl，共8文件。校验五套55路径相同，除hold外54逐字节相同；所有原件复制前后未变。完整source55哈希和复制件SHA均已记录，供后续promote后仍可对照初版及各资源变体。

后续可由root/本agent追加终态条目及pending历史快照；不要覆写旧attempt或旧收据。选择时只更新`current_selected_attempt_id`并向`selection_events`追加带理由和证据的事件；保留此前事件。源码归档原字节保持不改。若需更正索引事实，追加`correction_events`，不静默覆盖历史。

该索引说明已有结果与出处，不把资源利用率/未布通数量解释为具体失败net或单一根因，也不构成硬件/飞行验收。
