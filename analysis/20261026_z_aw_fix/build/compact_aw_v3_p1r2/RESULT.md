# v3 P1R2：实际路由失败

本独立尝试真实 `p.wait()=1`、`normal_wait_return=true`，原log为 `PR0004: total1096unrouted nets`。无TR/FS，没有完整路由或时序资格通过结论。终态复核时vendor15024/helper47552的CIM项均不存在；不以先前容量错误或进程消失代替实际退出回执。

- fixture：`out/z_aw_fix_20261026/compact_aw_v3/physical_p1r2_01`。开始 `2026-10-26T05:41:27.578470+00:00`，结束 `2026-10-26T06:16:42.057750+00:00`。
- hold：`9aa6a51a6cb2168ef46f3f5a61a23e3c4db8546601be7c0e562d4d16ab2cd6aa`；精确VG：`4f329e5313eba5966394828734c61867a3483b3eed8c3c37c724a453285c8a0c`。
- 实际配置：place1/route2/map2/repl0/timing_driven1/global50/UserCodeB4。source/build.tcl仍3/0/TD1，只有独立执行Tcl改place1/route2；SDC20.000ns和Fmax≥50、全部五表非负、setup/hold端点0、18pins、CLK/RX/完整route/FS/真实wait等原gate均保持。
- fresh源55+精确VG、单UTF-8 XML声明、恰VG/CST/SDC三项。原log确认open成功、skip SYN；donor SYN input/normal exit0/summary/mapaudit/执行Tcl/VG全哈希绑定并复制轻量proof，没有重新综合。
- physical rpt：Logic46001/59904=77%（36252LUT+9749ALU），FF27786，CLS26475/29952=89%，PRIMARY/LW各8/8。全局分配原文在`RESOURCE_EXCERPT.txt`；计数不识别具体failed nets或唯一原因。
- 终态后canonical55、fixture55、donor55及所有记录的donor proof/VG、新runner/原helper哈希均未变；未写其他源、旧fixture、旧B3/R/H或操作硬件/Git。

只读核对已安装官方SUG1220-2.1E PDF第44页（印刷37）：place1面向可布线性优先，route2面向更快布线；这只支持选择该有界实验，不证明结果成功。原PDF路径与SHA `c8ee7e8cb8486220a8639424f71debe9f4c3dff0d4c365860474c24782ded08c` 已绑定launch receipt；没有复制整本手册。

新runner SHA `389cca7a94f4aa428034c4910b68086056fdc8c122b648041168a8bb40f33c97`；原gate helper SHA `abb5246c203b73c111f80bc91f8db6c8220463f7d4c5cf48dbfe2167ef49db84`。`RESULT.json`列完整source55、原log/exit/rpt/Tcl/项目/SDC/CST等证据SHA；`EVIDENCE_MANIFEST.json`绑定本目录和外部轻量证据。原始失败保留，不新增profile、SYN/PNR或STA命令。
