# B0B4 物理验收 gate 独立只读复核

初次检查时间：2026-10-26 03:48 UTC。最新状态为 **B4-v1 attempt01 P3/R0与attempt03 P3/R1布线失败，attempt02 P2/R0待完成通知；尚无交付通过结论**。本文件对这三次原B4-v1尝试的复核未启动、停止或干预它们，没有执行 build_candidate.py，也没有修改它们的源或冻结RTL证据。以下初次检查记录保留其当时的pending状态，实际失败复核追加在末尾。另有根授权的compact构建由本代理在独立路径负责，其构建日志/报告单列于 `compact_aw/`，不与本文件的独立v1复核混淆。

审阅对象：`firmware/B0B4/build_candidate.py`，SHA256 `abb5246c203b73c111f80bc91f8db6c8220463f7d4c5cf48dbfe2167ef49db84`。构建目录为 `out/z_aw_fix_20261026/build_attempt_01/`。

## 源级 gate 判定

未发现当前调用链的阻塞性 gate 缺陷。各验收项不是只依赖 Fmax 一栏：

| 要求 | 实际代码与独立核对 |
|---|---|
| 正常真实退出 | `run_phase:57–62` 保存真正 `proc.wait()` 返回码，随后 `assert code==0`；main `:189` 成功返回后才调用 physical_audit。`normal_wait_return=true`只表示wait返回，非0仍拒绝；不能单看该布尔字段判成功。 |
| 真20ns约束 | `physical_audit:132,140` 解析TR Base-clock行的Period并要求等于20；映射审计另检查原SDC create_clock恰为20.000。没有用 `-global_freq50` 替代原始TR验证。 |
| 实际Fmax≥50 | `:133,140` 取正则第二个捕获，即 **Actual Fmax**，不是第一个Constraint值。已对照真实已验收B3原TR表头：Constraint50.000、Actual50.257，字段含义明确。B3数值仅作格式对照，不是B4证据。 |
| 五类slack | `:120–131,141` 分别要求Setup/Hold/Recovery/Removal/Minimum Pulse Width各有可解析行，计算各表最小slack，要求全部有限且≥0；没有仅凭Setup或Fmax判通过。 |
| 全局setup/hold endpoints | `:135,141` 另外要求两类Violated Endpoints均为0。 |
| 完整route/bitstream | `:139,142–144` 要求真实log出现Placement and routing completed、Bitstream generation completed、EOF返回sentinel，且原log/RPT中任何解析到的unrouted数都不得非0。缺完成标志、缺关键文件或非0退出都不能进入成功结果。 |
| 精确VG | main `:181,183–188` 把综合后的VG哈希绑定到仅含该netlist+CST+SDC的physical.gprj；`:143–144` 要求skip-synthesis原日志与结束后VG哈希仍相同，避免重综合替换donor。 |
| 55源绑定 | main `:159–169` 比较B3资格中的同一55路径，只允许固定三文件变化哈希；每个phase前后检查canonical与build快照的这55输入，最终再次检查。物理审计把该55哈希及原始输出哈希一起记录。 |
| B4 UserCode | `:138,146–147` 分别检查FS原始头部与生成device.cfg均为0000B0B4。单独cfg符合不能替代FS/实际物理完成。 |
| 18pins | `:136–137,145` 原CST IO_LOC与RPT已bonded pin表必须都恰18项并逐名逐位置相等；另明确radio_rx=B16/in、radio_tx=B15/out。 |

`physical_audit()`本身不重新执行wait，而依赖main先完成 `run_phase('physical')` 的真实0退出；独立验收最终文件时必须核对这个入口和 `physical_exit.json`，不能脱离调用链单独引用 `physical_audit.passed`。

## 已有原始绑定（不是PNR通过）

本次只读逐项计算确认：

* canonical与构建快照的55输入均匹配 `build_input.json`，差异相对已验收B3只有 `build.tcl`、`xy_pi_parameters.v`、`position/mtf_xyz_hold_control.v`。
* 新VG：`f63ae79edcd75c9905a0e55b53c3d8d9d94c239d8e67038a73fade80ffaa958a`。
* build_input SHA：`f9ecd09e05d150eeaf5dc89f8f87516bdf3e3886c1be31c97732c708e53adf9d`。
* physical_input SHA：`2829cacd8bcb2c920934b73af21ca088763c5affe19231a34570e47b969bcbda`。
* 综合真实 `actual_p_wait=0`；该事实不能代替物理退出。
* 实际physical.tcl为P3/R0/map2/replicate0、user_codeB4、run pnr后EOF sentinel；physical进程回执记录PID15128、父65620，启动03:36:58Z。未据PID存在或CPU活动推断成功。
* 当前device.cfg已经设置B4；它只是生成中间资料，不是Flash/SRAM安装证明。

## 当前明确缺少的证据

初次检查时输出目录只有device.cfg，尚未生成可验收的B4 TR、RPT、FS、PR，也没有 `physical_exit.json`、最终 `physical_audit.json` 或 `build_result.json`。因此以下内容全部 **pending**：实际20ns五表数值、实际Fmax、端点数、完整路由、18pins最终表、FS UserCode、实际p.wait0及最终原文件哈希闭合。不能沿用B3时序、综合0退出或cfg来补齐。

后续只在构建代理通知完成/失败后复核原始资料；不忙轮询、不自行重试或执行构建。若本次失败，保留失败原证据，新的试验需另有新路径与明确绑定，不能改写本次状态。此处尚无实际PNR失败或通过判定。

## 完成通知后：attempt01 已确认布线失败

只读复核原始回执和日志，确认该次实际配置为 **P3/R0/map2/replicate0**；“Routing Phase 1”是厂商阶段名称，不是route_option1。

* physical真实wait返回 **1**，结束于2026-10-26 04:01:46.942057Z；`normal_wait_return=true`没有被误当为成功。`build_failure.json`准确记录非0退出，main在调用physical_audit前即拒绝。
* 原日志明确包含 `Error: DesRoute failed.` 与 `ERROR (PR0004): ...1416 unrouted nets`。没有Placement and routing completed/Bitstream generation completed或返回EOF sentinel。
* 生成了RPT/pin报告，但没有TR、FS、PR。**这是布线失败，不是时序失败**；没有可引用的该次五表slack、实际Fmax或FS。不能以已生成RPT/CFG、综合成功或功能回归PASS代替完整物理资格。
* 再次独立计算确认canonical55与本次快照55仍匹配原build_input，VG仍为 `f63ae79edcd75c9905a0e55b53c3d8d9d94c239d8e67038a73fade80ffaa958a`。

| 原始失败证据 | SHA256 |
|---|---|
| `build_attempt_01/physical.tcl` | `4a90cce4f2eff9c6554bf37943f5d9efe9f5b46023ada83636a8dd30c291d25f` |
| `verification/physical.log` | `fb94d9008150f3095152a180f157d09ad54b73c28207166c99b7f02e9792c126` |
| `verification/physical_exit.json` | `59d0f1dd282e7e7fe09632f7ee8a81672bc36bd1e710f7287314a722eb578619` |
| `verification/build_failure.json` | `3dc8d32635924b3d5dd07529ae27797174ba1bd83acea0973a78de1d4b9b1771` |

根任务另授权同VG的独立新尝试：02应为P2/R0，03应为P3/R1；均保持20ns/map2/replicate0、跳综合和原55源。本报告尚未把这些调度消息当作实际配置/退出/时序证据。等待各构建代理完成通知后，逐次核对各自Tcl、精确donor/55源、实际wait、完整原TR五表、FS/CFG/pins及哈希。首个完整通过原全部门槛者才可成为交付候选；无须因纯物理重试重跑未改源的RTL/软件测试。

## 完成通知后：attempt03 亦确认布线失败

收到该构建代理的结束通知后，独立读取 `build_attempt_03` 原始资料。实际Tcl为 **P3/R1/map2/replicate0**，仍为同一精确f63ae79e…aa958a VG；canonical55与该快照55均再次逐项匹配。

实际wait返回 **1**，结束04:58:45.841848Z；原log明确 `PR0004 ...10483 unrouted nets`。虽然Routing Phase1/2/3里程碑均已出现，也没有生成TR、FS或PR，因此仍是**route failure，没有STA可验收或宣称timing fail**。route_option1的较长运行/阶段完成不能作为质量成功证据；未按原gate接受该输出。

| attempt03原始证据 | SHA256 |
|---|---|
| `physical.tcl` | `56d268ff8c76b27db5879389dfc5a9834da77d517a94cda3c37001f4426fc630` |
| `verification/physical.log` | `fb63b6958650ca43b9b3cacf32880779e7ad01b2e864a583b87c5006fe4505cb` |
| `verification/physical_exit.json` | `0d2df22fe7aa99289a14fdcb19b3a4c5c13fd9485ea8a7b013f59c4bf6076db1` |

attempt02仍只等待其负责人完成通知；本次没有借03结束去轮询02或改动其输入。compact的资源结果与另一路P3/R0运行也不能替代这三次v1试验的失败/待定状态。
