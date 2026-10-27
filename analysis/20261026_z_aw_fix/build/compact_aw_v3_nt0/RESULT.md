# v3 P2R0 timing_driven0：实际路由失败

本独立诊断尝试真实 `p.wait()=1`、`normal_wait_return=true`；原log为 `DesRoute failed`、`PR0004: total1073unrouted nets`。无TR/FS，未完成完整路由，不能称为时序通过或完整路由后缺STA。没有追加STA命令、重新综合、约束放宽、硬件/Git操作或后续profile。

- fixture：`out/z_aw_fix_20261026/compact_aw_v3/physical_p2r0_nt0_01`。vendor49580/helper41472；开始 `2026-10-26T05:34:12.793524+00:00`，结束 `2026-10-26T06:11:50.443011+00:00`。
- hold：`9aa6a51a6cb2168ef46f3f5a61a23e3c4db8546601be7c0e562d4d16ab2cd6aa`；VG：`4f329e5313eba5966394828734c61867a3483b3eed8c3c37c724a453285c8a0c`。
- 实际配置：place2/route0/map2/repl0/timing_driven0/global50/UserCodeB4。source/build.tcl仍timing_driven1，只有独立执行Tcl改0；SDC20.000ns及50MHz/Fmax≥50/五表非负/端点0/18pins/完整route/FS/真实wait等原gate全部保持。
- fresh源55+精确VG，单UTF-8 XML声明、恰VG/CST/SDC三项；原log已确认open成功、skip SYN。donor的SYN input/normal exit0/summary/mapaudit/执行Tcl/VG全部哈希绑定并复制轻量proof。
- 原始physical rpt：Logic46009/59904=77%（36252LUT+9757ALU），FF27786，CLS26689/29952=90%，PRIMARY/LW各8/8。完整命名分配原文在`RESOURCE_EXCERPT.txt`；数量不能识别具体failed net或单一原因。
- 终态后canonical55、fixture55、donor55、所有记录的donor proof/VG及两个runner哈希均未变；其他活动尝试未写。

新runner SHA `cdb7e9b5e947a308f9e8c297406b77bf836db67973f2a4062475b1a7c16cbbec`；原gate helper SHA `abb5246c203b73c111f80bc91f8db6c8220463f7d4c5cf48dbfe2167ef49db84`。`RESULT.json`记录完整source55、执行Tcl/项目/SDC/CST/log/exit/rpt及失败回执SHA；`EVIDENCE_MANIFEST.json`绑定本目录与外部轻量证据。原始失败保留，验收门没有因timing_driven0而改变。
