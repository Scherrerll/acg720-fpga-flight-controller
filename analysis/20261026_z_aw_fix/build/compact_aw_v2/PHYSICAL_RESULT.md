# compact_aw_v2 P2R0：实际路由失败

fresh `out/z_aw_fix_20261026/compact_aw_v2/physical_p2r0_01` 于 `2026-10-26T05:46:45.387162Z` 正常取得实际 `p.wait()=1`。原始日志为 `DesRoute failed`、`PR0004: total792unrouted nets`；**无TR/FS，没有物理或时序资格通过结论。** 开始时间 `04:52:50.255769Z`，vendor53456、helper38552；不是SYN阶段或项目解析错误。

该尝试仅使用已实际SYN正常退出0且映射审计通过的精确VG `497200b2627194c9047d459402f239592fa75e16c491e39251d20c6b4238a39f`，source hold `afc656820788d8cbf7c61d8c4e7526bec3dceb950673de9df18cb68a7d0632f3`。复制canonical55至新fixture；项目为单UTF-8 XML声明、恰VG/CST/SDC三项，实际日志已确认open成功与skip SYN，没有重新综合。

实际执行选项为P2/R0、map2/repl0、timing_driven1、global50、UserCodeB4；SDC20.000ns未变。source/build.tcl中的P3/R0保持原字节，单独physical.tcl选择P2。原 `build_candidate.py` 的run_phase/physical_audit gate未改；因实际exit1，在全部产物/20ns时序门之前停止，没有生成假PASS audit。

| 原始physical rpt项目 | 实际值 |
|---|---:|
| 未布通nets | 792 |
| Logic | 46003/59904，77% |
| physical LUT / ALU | 36216 / 9787 |
| Register | 27786/60780，46%（27782 logicFF+4 IOFF） |
| CLS | 26562/29952，89% |
| PRIMARY / LW | 各8/8，100% |

这里是physical rpt计数，与单独SYN XML的资源计数按各自阶段保留，不能互换。原始全局分配表摘要保存在 `PHYSICAL_RESOURCE_EXCERPT.txt`；这些计数不识别792条net的具体身份或唯一失败原因。

终态后逐项重新核对：v2 canonical55、physical源55、SYN donor源55、donor四项proof/VG、执行helper及原runner全部与启动前一致。原B4、旧02、v1、v3或其他活动尝试未写。v2静态 `SYNTHESIS_REPORT.md` 与 `SYN_EVIDENCE_MANIFEST.json` 不改；本失败由独立 `PHYSICAL_RESULT.json` 和 `PHYSICAL_EVIDENCE_MANIFEST.json` 绑定。

新physical runner SHA `0e64fd77e1cc9529eec4b890fb94828db9c741255e344b26cc3377bec82d45dc`；原helper SHA `abb5246c203b73c111f80bc91f8db6c8220463f7d4c5cf48dbfe2167ef49db84`。退出/日志/报告/执行Tcl及全部输入哈希在RESULT中；没有源更改、门槛放宽、硬件或Git操作。v3 NT0及P1R2为另有授权的独立尝试，结果不混入本报告。
