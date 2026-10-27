# 普通 FF/LUT 布局导出：只读文档调查

2026-10-27。结论：这四份本地官方手册没有给出可直接复现的普通 FF/LUT 全量 LOC 导出接口。目前不能据此恢复 exact v4 的完整布局基座。最有价值的线索是定向 `report_timing`，但“打开既有 routed 数据库后只执行 STA”的入口仍缺官方文档支持；不能用 `run pnr` 代替。

| 方法 | 文档和实际证据 | 可执行步骤、成本与限制 |
|---|---|---|
| 定向时序路径取得 LOC | SUG940 §5.5.1 支持 `-to get_regs`、`-through get_pins` 和 `-max_paths`；§4.2 明确 LOC 是物理位置。原 v4 `.tr` 第277–288行实际同时给出 LUT `F`、FF `D/CLK` 和坐标。 | 在**已确认使用原 routed DB 的 STA 环境**中，逐 FF 查询 endpoint、逐 LUT 查询其真实输出 pin。每对象一个成功路径即可获取该对象位置，并顺带覆盖路径上的其他单元。成本为 O(FF+LUT) 条定向请求和较大的文本输出，运行时间未知。无可报告路径、被原有例外排除或未放置的对象必须登记为缺失；不能把全局最大路径数增大当作完整覆盖证明。 |
| FloorPlanner 实际 Place View | SUG1541 §3.3.4 支持 All Instance / All LUT / All DFF，悬停显示实例名，选择 Netlist 实例后 Highlight 其实际位置；项目已成功 P&R 时可使用。原 native v4 GUI 记录已确认工具可读取其布局数据库。 | 打开原成功 full-route 项目，使用 Show Place View，逐对象关联实例名和坐标；Copy Location 文档只保证复制选中位置/区域。没有已文档化的“全实例 name→LOC 表格复制/CSV 导出”。用于少量遗漏对象可信，数万单元需数万次人工关联，且必须确认 CFU 子槽，不能把区域坐标冒充精确单元位置。 |

定向命令模板（SDC 报告语法；不是已确认可在 IDE Project Tcl Console 独立执行的命令）：

```tcl
report_timing -setup -to [get_regs {EXACT_FF_NAME}] -max_paths 1
report_timing -hold  -to [get_regs {EXACT_FF_NAME}] -max_paths 1
report_timing -setup -through [get_pins {EXACT_LUT_NAME/F}] -max_paths 1
```

对象名和输出 pin 必须来自同一原始 VG。`get_regs` 仅取 FF；通配符 `*` 可跨层级。先用原报告已知的 `core/flight_state/flying_ms_3_s0` 和 `core/flight_state/n56_s3/F` 做小样本，要求坐标分别与原 `R54C122[0][A]`、`R54C122[1]` 一致，再考虑批量。成功后按原 VG 的普通 FF/LUT 清单统计唯一实例覆盖率、缺失和冲突；只有足够覆盖且槽位合法，才值得讨论新布局约束。SUG1541 §2.4 确实支持对 LUT/DFF 使用 `INS_LOC`，但这不能证明提取完整或未来可布通。

其他接口的明确边界：

- **MPW/clock sinks 无 LOC**：SUG940 §5.5.4 的 `report_min_pulse_width -nworst N -detail [get_regs {*}]` 能扩大 FF/时钟路径报告，但原 v4 `.tr` 第5465–5493行的实际表头仅 AT/DELAY/TYPE/RF/NODE，完全没有 LOC，不能作为位置导出方案。本次四份手册也未找到 `report_clock_tree`。
- **不是通用 cell property API**：SUG1220 §3.3.8、§3.3.11 的 `list_property` / `report_property` 明确仅用于 IPFlow 的 IP 配置；没有找到 `get_cells` / cell LOC property 查询。不能借用其他厂商 Tcl 语法。
- **现有格式没有新增已证实的全量出口**：`-gen_posp` / `.posp` 明确只含 BSRAM；`.vo/.vho/.sdf` 被定义为时序仿真文件，手册未保证携带实例 LOC。`.p/.pr` 仅按官方增量流程使用，本次未读取、解码或解密其内容。
- **GUI 表格范围有限**：Primitive Constraints 表格是“当前约束”的 name/type/location，Save As 导出当前约束；并非所有自动放置单元。BackAnnotate 的一般文字不能覆盖已观察到的 Port/BSRAM/DSP/PLL/DSPLite 类型限制，已有52宏导出不包含普通 FF/LUT。
- **旧数据库 STA 入口仍是阻点**：SUG1220 §3.3.13 的 `run` 只支持 `syn/pnr/all`；SUG940 Timing Constraints Editor 是加载网表、编辑/保存 SDC；SUG100 只描述打开既有静态报告及 P&R 生成报告，没有记录 read-DB/report-only STA 调用。本次不编造 `run sta`、`read_db` 或假设修改 SDC 后打开旧报告会重新分析。

建议后续先取得厂商对“加载已完成布局数据库、保持布局/布线不变、执行新增 report_timing”的正式接口说明，或在另行授权的小范围官方 UI 检查中确认该入口。入口未确认前，不启动数万条报告任务、不为此重跑 P&R。若只能逐实例 GUI 查看，投入与完整性风险都很高。原 partial109 LOC 和增量匹配2.82%均已失败，本报告不建议重复；原 exact v4 49.456MHz / setup−0.220ns 仍未满足50MHz。

证据定位（页码是手册印刷页）：

- [SUG940 pp44–46：LOC 定义](C:/Users/ScherrerL/Desktop/apple/routing_rescue_20261015/mtf01p_b0b0_synthesis_fix/hardware/doc_diagnostics/SUG940.txt:1458)、[pp73–76：定向 report_timing](C:/Users/ScherrerL/Desktop/apple/routing_rescue_20261015/mtf01p_b0b0_synthesis_fix/hardware/doc_diagnostics/SUG940.txt:2471)、[p55：集合](C:/Users/ScherrerL/Desktop/apple/routing_rescue_20261015/mtf01p_b0b0_synthesis_fix/hardware/doc_diagnostics/SUG940.txt:1676)、[pp78–79：MPW](C:/Users/ScherrerL/Desktop/apple/routing_rescue_20261015/mtf01p_b0b0_synthesis_fix/hardware/doc_diagnostics/SUG940.txt:2719)。
- [SUG1541 pp56–58：Place View / Copy Location](<C:/Users/ScherrerL/Desktop/apple/timeout_policy_20261025/vendor_manuals/SUG1541-1.0E_Gowin Software Physical Constraints User Guide.txt:2210>)、[p62：当前约束表](<C:/Users/ScherrerL/Desktop/apple/timeout_policy_20261025/vendor_manuals/SUG1541-1.0E_Gowin Software Physical Constraints User Guide.txt:2377>)、[pp7–8：INS_LOC](<C:/Users/ScherrerL/Desktop/apple/timeout_policy_20261025/vendor_manuals/SUG1541-1.0E_Gowin Software Physical Constraints User Guide.txt:510>)。
- [SUG1220 pp14–16：IP properties](<C:/Users/ScherrerL/Desktop/apple/timeout_policy_20261025/vendor_manuals/SUG1220-2.1E_Gowin Software Tcl Commands User Guide.txt:718>)、[p17：run flows](<C:/Users/ScherrerL/Desktop/apple/timeout_policy_20261025/vendor_manuals/SUG1220-2.1E_Gowin Software Tcl Commands User Guide.txt:857>)、[p33：posp 仅 BSRAM](<C:/Users/ScherrerL/Desktop/apple/timeout_policy_20261025/vendor_manuals/SUG1220-2.1E_Gowin Software Tcl Commands User Guide.txt:1628>)。
- [SUG100 p37：输出文件](<C:/Users/ScherrerL/Desktop/apple/routing_rescue_20261015/mtf01p_b0ae_ano_control/tools_notes/SUG100-4.4.7E_Gowin Software User Guide.txt:1834>)、[P&R 与只读报告](<C:/Users/ScherrerL/Desktop/apple/routing_rescue_20261015/mtf01p_b0ae_ano_control/tools_notes/SUG100-4.4.7E_Gowin Software User Guide.txt:2657>)、[附录：文件格式](<C:/Users/ScherrerL/Desktop/apple/routing_rescue_20261015/mtf01p_b0ae_ano_control/tools_notes/SUG100-4.4.7E_Gowin Software User Guide.txt:3697>)。
- [原 v4 真实 LOC 行](C:/Users/ScherrerL/Desktop/apple/github_publish/acg720-fpga-flight-controller/out/z_aw_fix_20261026/compact_aw_v4/physical_p3r0_01/source/impl/pnr/acg720_ano_port.tr:277)、[原 MPW 无 LOC 表头](C:/Users/ScherrerL/Desktop/apple/github_publish/acg720-fpga-flight-controller/out/z_aw_fix_20261026/compact_aw_v4/physical_p3r0_01/source/impl/pnr/acg720_ano_port.tr:5465)、[已有 GUI 实际观察](C:/Users/ScherrerL/Desktop/apple/github_publish/acg720-fpga-flight-controller/analysis/20261026_z_aw_fix/build/compact_aw_v4_native/GUI_VIEW_RESULT.json:13)。

本次仅阅读上述公开手册文本、原文本 STA 报告与既有 JSON 记录；仅新增本报告和 EVIDENCE.json。未启动 vendor、UI、硬件或新候选，未修改两生产文件或冻结证据，未读取凭据或受保护布局数据库。
