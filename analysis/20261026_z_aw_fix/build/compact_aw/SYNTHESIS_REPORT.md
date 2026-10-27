# Compact AW：独立存储复用候选

本候选保持B4 conditional-Z-I算法、state66/67、同一B4参数协议及1000/350默认值，仅复用已过生命周期的工作暂存。原 `firmware/B0B4/source` 和原物理attempt01/02/03未改；没有硬件/Git操作。

**最终状态：SYN/MAP通过；实际P3/R0布线失败746根未布通，无TR/FS/PR，不可交付。** 下述启动记录保留当时事实，终态补记在末尾。没有在该候选上继续修改或重新优化。

源路径：`out/z_aw_fix_20261026/compact_aw_v1/canonical/source`。55文件中只有 `position/mtf_xyz_hold_control.v` 相对B4-v1变化，SHA `479f757149a57ac0b5f9e0334dab80cae475a5345b834fde9c5130c701057ac3`；54文件逐字节相同。完整前后哈希见 `source_freeze.json`（SHA `ac7e467453007878cd6749e3c5c98e70bdbe01b965d4bf0256906d6ae62d63f0`），实际差异见 `candidate.diff`，生命周期/宽度证明见上级 `compact_aw_design.md`。

## 实际综合与映射

`build_attempt_01` 完整顶层Icarus展开实际wait0。独立Gowin SYN于04:14:26Z启动，04:17:37.488416Z **真实p.wait=0**，原日志包含 `SYNTHESIS_COMMAND_RETURNED_EOF`；没有用日志“完成”替代进程退出。该阶段只执行 `run syn`，没有PNR。

新VG SHA：`b7691fd2d04abfc95e1fa458b0cb22e1c8ebcb2eb810db16e7a706fa8e73a87b`。

| 实际XML资源 | B4-v1 | compact | delta |
|---|---:|---:|---:|
| 全top FF | 27905 | 27786 | −119 |
| 全top LUT | 36784 | 36332 | −452 |
| 全top ALU | 9651 | 9658 | +7 |
| controller FF | 3414 | 3298 | −116 |
| controller LUT | 4867 | 4951 | +84 |
| controller ALU | 1664 | 1675 | +11 |

DSP各类型和BSRAM数量相同。不能把全top LUT减少误写为controller LUT减少；除本模块以外的源没有变化，但全设计综合的优化/资源归属结果也会随逻辑连接变化。资源节省不是布线首因证明，也没有由SYN推断CLS/路由/STA已通过。

映射图审计检查27786个FF、27888个时钟pin，非clk50且非GND的时钟pin为0；UART pad仍仅进入既定rx_meta FF，meta Q仍仅进入rx_sync FF，radio_rx仅pad→首级的原false_path保持，20ns SDC未改。两套canonical55和build快照55在该阶段结束后再次匹配。

关键真实回执（均在 `out/.../compact_aw_v1/build_attempt_01/verification/`）：

* `synthesis_exit.json` SHA `00fe4f6e92495cffe93ea6ad2cd20458d32a34fe6fe46bb0c9650cdf9bace7eb`。
* `synthesis_summary.json` SHA `df9566845e0f375154ac16a5df92f60eb78d4d4587d32ed6c5be9a42e8a86788`。
* `mapped_audit.json` SHA `4f245ca892f544153198cd86800d48835a7c110c2d763f76c6935d9218e7d363`。
* `resource_comparison.json` SHA `1eae13fa59c008265a1e066713c9666bf3431701fac44049503dca7cbcfa184f`。

`run_synthesis.py` 明确把CANON override到这个新候选，只import原helper的进程/映射审计函数，不调用会自动PNR的原main。真实phase回执中的runner_sha指import helper源码 `abb5246c...49db84`；执行入口脚本本身的SHA另记录在build_input/synthesis_input，二者不混淆。原helper文件未修改。

## 已授权的独立物理试验

资源下降后，根任务授权fresh同VG P3/R0、map2、replicate0、20ns、UserCodeB4、不重综合。

首个 `physical_p3r0_01` 是**项目生成器错误**：Python ET使用encoding别名`utf8`自动添第二个XML声明，Gowin在open_project立即报invalid project file，实际wait1，未进入placement/route。原项目、原runner、log和exit全部保留，不能算为RTL/布线/时序失败。`project_retry_provenance.json`绑定这些原始哈希。

新的 `physical_p3r0_02` 使用与原helper一致的`utf-8`序列化，新增“恰一个XML声明、恰三项netlist/CST/SDC”检查；没有改任何RTL、VG或原失败文件。04:24:18Z实际启动Gowin PID20076（launcher54068），原log确认Open project成功、Skip synthesis及进入placement。执行入口 `run_physical_p3r0_retry02.py` SHA `dde005a089e5df0b9e409b4779687142c57860936f3b1d18a2ac773ff4c061fc`。

该试验当前运行中，**没有物理通过结论**。必须仍通过真实p.wait0、完整route/FS、20ns五表非负、setup/hold端点0、实际Fmax≥50、18pins、B4 FS/CFG及精确VG/55源的原完整gate。功能等价/行为回归由根任务另行执行；SYN或部分回归不替代完整资格。

## 终态封存

physical_p3r0_02于2026-10-26 05:07:10.260251Z真实wait返回1；原log为DesRoute failed、PR0004=746 unrouted，有RPT但无TR/FS/PR。它是**布线失败，没有STA结果**。未因相对v1的1416未布通减少而宣称根因已确定或时序已改善。

`finish_stage.py` 再次验证原B4-v1 canonical、compact canonical、综合快照、两个物理快照的各55文件及所有VG副本均未变。并额外按每个DFF的CLK逐项检查：27786个FF全部直接属于clk50等价网，无GND-clock FF；`strict_ff_clock_check.json` 保存实际图解析结果。原helper较宽的DSP/RAM未用GND-clock允许条件没有掩盖任何非50MHz FF。

终态 `FINAL_STATUS.json` SHA `b03e4e36b149144ead857365b0de65b90b9ad7d28a819fb72f44e4c1c8b1fdd8` 绑定完整源检查及外部原证据。physical02原log SHA `6db422b922c77c65a49c5fdd63c740913a27547195ebfdd295f0374bb39374a1`；exit SHA `8e3dc6434b6c0f674a9bf39c6566b3a2a993f005de5264c5b5e51d939220fe44`；RPT SHA `7c99b075eff1662647ff88d07a976b537a84a9f6ef9fd28dde5f95d151ac0cc6`。原始build输出未改写；该分支没有启动新的物理重试。
