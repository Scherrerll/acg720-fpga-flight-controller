# IMU index 局部扇出：下一候选的最小设计建议

建议先测试 **index 局部 `syn_maxfan=100` ＋ LPF 前一槽地址 bit1 的显式组合 wire hint**；若组合 hint 未命中，再考虑同拍维护的 **1 位私有 predecode cache**。完整32位 one-hot 是更大的备选，不是第一步。本报告没有候选实现或物理收益结论。

现有 v22 estimator SHA=`72c7e1fe…dea3ea0a`，仍与 v18 相同。v18 DSP 的真实 Path9 为 index FF→低2位 XNOR→LPF previous-word mux→共享减法→m_a，setup−0.563ns；首 decoder INIT=`9`、174负载，路由延迟占14.149/20.505ns。当前 v22 global100 的实际 SYN/audit/root 均0，index最大负载200→100，n8507两份174变为四份48/100/100/100，全芯片+83FF/+83LUT，算术/DSP/BRAM数量不变。这证明复制机制有效，不能证明局部 hint 一定命中或 PNR 会改善。

## 方案一：组合解码明确命名，只约束真正的数据选择网络

SUG550 §5.11 允许 `syn_maxfan` 作用于 reg/wire，必要时复制寄存器或组合逻辑；§5作用范围明确仅该 reg/wire。它不适用于 clock、CE、reset/set。故只给 `index` 加属性只约束 index 的直接负载，不能保证后级174负载 decoder 也被限制；`wire alias=index` 更没有新增组合驱动，不能当成 decoder 优化。

关键代数是：`(index-1)[1] = ~(index[1] ^ index[0])`，正好对应实际 n8507 的 INIT9。最小显式方案是命名这个**真实被消费**的 bit1 wire，并给它 `syn_maxfan=100`；LPF previous 地址使用“原减1地址的其他位＋该 wire 的 bit1”。只替换 FILTER_MUL 的 previous-word 读地址，保留 current-word、余数存储、循环写回和原有减法/乘法调用。无新寄存器、状态或等待周期。仅新增一个未被消费的 XNOR wire 没有作用。

原表达式 `index-1` 含32位无尺寸常数，不能不说明就改窄地址。5位减1在 index=0 时得到31，原得到32'hffffffff，二者对24槽数组都越界；1–31时槽选择一致。后续 miter 仍须核对全部32个二进制 index、非法/未知选择的 X 行为、29位存储的32位符号扩展。也可保留原32位减1表达式的位宽，只替换 bit1，减少这种语义差异。

初次不要附加 `syn_keep` / `syn_dont_touch` 等组合属性。若 named wire 被折叠或约束不传播，此实验应判“未命中”；再依据实际 SYN 日志和 VG 决定是否需要 §5.9 的 net keep。`syn_keep` 保留 net，不等于扇出复制或时序优化保证。对整个 estimator 模块加 maxfan 会涵盖子模块，范围明显大于本方案。

SYN 成功标准必须检查：XNOR 输出及其等价复制网络的每份实际 pin-load≤100、LPF previous mux 确实由这些网驱动；不能只看 index FF≤100 或只找同名 n8507。还需检查新增 FF/LUT 的层级、原共享32位减法未变成24套减法、所有 FF 仍为 CLK50，不能把下游高扇出转移到其他无审计网。

## 方案二：优先1位同步 predecode，完整 one-hot 后置

可以只缓存上述 `prev_bit1`，保留原5位 index 和所有消费者。这比32位 one-hot 更小，并有机会移走关键路径的首 XNOR：cache 初始1；每次 index归零同拍置1；每次 index递增同拍更新为 `pred(index+1)`；其余同拍保持。对于已知二进制 index，`pred(index+1)` 恰等于旧 `index[1]`，因此不需要宽加法反馈。若要求模拟器也保留未知 index 的四态传播，应先保留显式 next-index/pred 表达式再做四态 miter，不能把二态恒等式当四态恒等式。

**不能每拍执行 `cache<=pred(index)`**：index改变当拍会滞后一拍。也不能在 reset/invalidate 里擅自置1：原 index 在这些分支保持旧值。对 cache 加 maxfan 仍需确认实际复制和驱动；若综合把新 cache 吸收为原组合网络，也不算命中。未运行综合，无法保证新增1位最终只占1FF或一定减少路由。

若需要重构整个读选择，再考虑私有32位 one-hot：初始bit0，归零置bit0，递增循环左移，其他保持，逐拍证明 `onehot == (32'b1 << index)`。只用它先选 current/previous **32位有符号数据字**，随后保留原共享减法；不展开每槽算术。它会新增32位状态及宽 word-selection 网络，也可能制造新的高扇出。不得以“零选中返回0”的 OR mux 改写原越界/X 读语义；24–31、index=0的 previous非法读以及未选中数组的 X 值都需单独比较。因此它的证明与映射成本高于1位 cache。

## index 的完整更新清单

源码实际是 **10处归零＋6处递增＝16个 NBA 赋值点**，另有声明初始0；第478行同时含归零和递增。任何新 cache 必须在相同条件和优先级下更新。

| 动作 | 分支与原文件行号 |
|---|---|
| 归零10处 | DECIDE413；ALPHA419；ACC_ROOT_DONE458；ACC_DIV_DONE463；SEED471；NORM_ROOT_DONE476；NORM_DIV_DONE478(index==3)；MATRIX_CONT493；QUAT_TERM571(component==3)；TRIM_FINE_STORE614(axis==2) |
| 递增6处 | FILTER结果49态443(index!=23)；NORM_SUM474(index!=3)；NORM_DIV_DONE478(index!=3)；MATRIX_STORE486(index!=8)；CROSS_STORE499(index!=5)；TRIM_MATRIX_STORE630(index!=4且trim开启) |
| 保持 | reset347–358；invalidate task335及其所有调用；link loss、reject、busy sample取消分支；乘除/root等待；所有其他状态 |

推荐在原 index 赋值所在分支同拍配对写 cache，保留原 index 的初值、分支和 NBA 优先级。不要为了减少写点另造一个弱化取消优先级的独立调度器。

## 候选必须完成的证明及协议风险

1. **选择器组合 miter**：任意24×29位存储和6×32位 filter_input，全部32个 index；包括符号边界、29→32位符号扩展、32位减法溢出/截断、非法和 X/Z 选择。比较最终 m_a 操作数，不只比较地址位。现有 LPF remainder/carry、alpha、prod 截位完全不改。
2. **完整原/新 estimator 同拍 miter**：实际两个模块，逐拍四态比较所有公开输出、diag、state/resume/index、m_start/m_a/m_b、乘除握手、LPF/余数及原有数学状态；只允许新增 cache 私有状态。cache不变量从声明初始值建立，覆盖16个真实赋值点，禁止通过 force/preload index/cache/存储制造同步。
3. **取消与恢复覆盖**：default LEVEL_TRIM_ENABLE=0 和有效/无效trim参数；正常校准、首次filter seed、连续全24槽、reseed、dt=0/超限；各繁忙状态插入 reset、link loss、reject、同拍 sample。尤其在 index非0 时 reset/invalidate 后恢复，以及槽3→4、7→8、末槽23退出。FILTER49同拍仍写旧 index 的槽，下一 FILTER_MUL 才消费新 index/cache；不能提前选择下一槽破坏 in-place cascade。
4. **原顶层协议证明**：新source55绑定下重跑原 top13 与 guard/safety/landing 同拍集成检查，保持默认caller、所有公开周期、数值、fault/ready/update节拍；上游相同输入得到同一拍输出。复用旧证据时只能复用确实未变组件，不能宣称旧 estimator hash 证明新 RTL。
5. 通过真实 compile/vvp/root 收据、源码/TB/log/tool 哈希闭环后才审 SYN。物理收益最终仍需原20ns/50MHz、原radio_rx之外无例外的真实全门验证；扇出≤100不能代替布通、slack或50MHz资格。

本目录的纯 Python 检查仅验证32个已知二进制 index 的地址/bit恒等式、抽象hold/zero/increment不变量及原源码16写点，**不是 RTL/四态/协议证明**。本次未编辑候选、未启动 vendor、UI 或硬件。两份 release 工具及原 build_candidate 保持原封存字节。

主要证据：[v22 源码](C:/Users/ScherrerL/Desktop/apple/github_publish/acg720-fpga-flight-controller/out/z_aw_fix_20261026/compact_aw_v22/canonical/source/core/ano_attitude_estimator.v:435)，[v18 真实 Path9](C:/Users/ScherrerL/Desktop/apple/github_publish/acg720-fpga-flight-controller/out/z_aw_fix_20261026/compact_aw_v18/physical_p3r0_dsploc_01/source/impl/pnr/acg720_ano_port.tr:857)，[v18 XNOR INIT9](C:/Users/ScherrerL/Desktop/apple/github_publish/acg720-fpga-flight-controller/out/z_aw_fix_20261026/compact_aw_v18/build_attempt_01/source/impl/gwsynthesis/acg720_ano_port.vg:91056)，[v22 global100 实际映射对照](C:/Users/ScherrerL/Desktop/apple/github_publish/acg720-fpga-flight-controller/out/z_aw_fix_20261026/compact_aw_v22_fan100/build_attempt_01/verification/mapped_fanout_comparison.json:1)，[实际资源对照](C:/Users/ScherrerL/Desktop/apple/github_publish/acg720-fpga-flight-controller/out/z_aw_fix_20261026/compact_aw_v22_fan100/build_attempt_01/verification/resource_comparison.json:1)，[SUG550 §5.11](<C:/Users/ScherrerL/Desktop/apple/routing_rescue_20261015/mtf01p_b0ae_ano_control/tools_notes/SUG550-2.4E_GowinSynthesis User Guide.txt:2877>)，[reg/wire作用范围](<C:/Users/ScherrerL/Desktop/apple/routing_rescue_20261015/mtf01p_b0ae_ano_control/tools_notes/SUG550-2.4E_GowinSynthesis User Guide.txt:1767>)。
