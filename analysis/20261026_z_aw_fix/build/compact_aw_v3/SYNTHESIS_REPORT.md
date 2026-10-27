# compact_aw_v3：显式共享Z加法器

源位语义审查见 `source_review.md`。v3只有hold相对v2变化，54文件逐字节相同；hold SHA `9aa6a51a6cb2168ef46f3f5a61a23e3c4db8546601be7c0e562d4d16ab2cd6aa`。这三处signed64加法的共享不新增FF/周期/算法分支；是否改善物理结果仍需实测。

**本报告对应的P3/R0最终状态：实际wait1、898 unrouted，无TR/FS/PR，不可交付。** 启动记录保留其当时事实，终态列在末尾；其他人负责的独立profile不属于本次封存。

## 已完成的实际SYN/MAP

源为 `out/z_aw_fix_20261026/compact_aw_v3/canonical/source`；新输出为其 `build_attempt_01`。完整top elaboration实际wait0；Gowin SYN于2026-10-26 05:18:28Z启动，05:23:13.135978Z实际wait0，EOF sentinel已在原日志中。只执行run syn，无PNR混入。

精确VG：`4f329e5313eba5966394828734c61867a3483b3eed8c3c37c724a453285c8a0c`。

同配置map2对map2（不是对v2的另一个map1 profile）：

| 实际XML资源 | v2 map2 | v3 map2 | delta |
|---|---:|---:|---:|
| top FF | 27786 | 27786 | 0 |
| top ALU | 9592 | 9559 | −33 |
| top LUT | 36369 | 36405 | +36 |
| controller FF | 3298 | 3298 | 0 |
| controller ALU | 1609 | 1576 | −33 |
| controller LUT | 4985 | 5029 | +44 |

DSP及BSRAM不变。结果体现carry单元减少、MUX/LUT增加的权衡，**不是净面积节省或布线改善证明**，也没有推断CLS或时序通过。

真实映射审计通过：27786个DFF全部CLK50；27888个原始时钟pin没有非50MHz/非GND来源；UART pad/meta/sync链保持既定关系；18个scalar顶层port与CST名称集合一致；参数bank保留P/I各16个live FF，实际INIT=1000/350。原B4、v2 canonical、v3 canonical和v3构建快照55源前后不变。

SYN原始回执位于 `out/.../compact_aw_v3/build_attempt_01/verification/`：

* summary SHA `75c0c775dc93bc65c12b0d63f88626d94f5a38dd6882548328f4d428ca1511ec`。
* actual-exit SHA `ed46b409fa3293c5979db7d14344ec43ee7e28ccc5f1dac9b414a579942cd303`。
* mapped audit SHA `cdd326c80bfd755f7626c154b2b8b7621f05ae189e3254f28b44f6c523873e64`。
* gain/port audit SHA `bfe2f8d895e0d445355e74dbed607cd2aa118a59f8f802f43aca8256a34b2b6e`。
* strict FF clock audit SHA `84f312ffea5adddf781e373d4a4a8ab19a26effbe04a4d5bde1fa321a4497709`。
* resource comparison SHA `9d3950d24b9cd684df74d00704c6b0e4d6bfb05888eb77ba07fc3f1cff3b665b`。

## 另行授权的物理尝试（当前待定）

根任务依据carry占用减少的实际权衡，另行授权fresh `out/.../compact_aw_v3/physical_p3r0_01`。它克隆同55源和上述精确VG，不重综合；P3/R0/map2/replicate0、20ns、UserCodeB4、18pins及原完整五表/退出/全路由/FS gate保持。

项目使用UTF-8且恰一个XML声明，只含VG/CST/SDC；donor实际正常退出、mapped、gain INIT、18port及strict-clock审计哈希全部绑定。05:27:30Z真实启动Gowin PID19176（launcher49960），原log确认skip synthesis并进入placement。执行入口 `run_physical_p3r0.py` SHA `f2a1a00c9e1bd688cb1df05facb7e8efd26c81949d0a60559aa6ba7093be1d5a`。

此时没有TR/FS或物理通过结论。全功能/逐cycle等价由根任务独立运行，不把本报告的SYN成功当作替代。任何进一步配置/物理重试仍需根任务授权；原v1/v2/原B4与旧fixture/脚本均未修改，没有硬件或Git操作。

## P3/R0终态（不再追加monitor）

真实wait=1，结束2026-10-26 06:06:03.746083Z。原log为DesRoute failed、PR0004=898 unrouted；有RPT，无TR/FS/PR，是route failure而非STA失败。未凭ALU减少推断路由改善或降低验收门槛。

`finish_stage.py` 已逐项复核原B4、v2、v3 canonical以及v3 SYN/P3快照55源，并确认SYN与P3的VG均为上述4f329e53…85c8a0c，均未改写。`FINAL_STATUS.json` SHA `81d86b72f1aa49d3a030a4edebbdaf40f857d23120cffb6695849daafb0d4acc` 绑定所有原始回执和源检查。

P3原log SHA `0d68c37894b3fa7949aab86f09d72018a1354329f90c22f23bce750256c5a034`；exit SHA `606f7d837c907f916d0c52c0ebe5b362ee1c61b6aaac63e4da786a810c7c76c8`；RPT SHA `504a3d9b35344b19fb86f507f28e59fb5572c0b24ea413d58a0eba5464c35223`。只封存本P3及其SYN诊断，不代表其他独立profile已终止或得到相同结果。
