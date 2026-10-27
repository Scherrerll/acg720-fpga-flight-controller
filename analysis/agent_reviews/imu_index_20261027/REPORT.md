# IMU index Path9：只读定位与最小方向

实际 v18 DSP 路由的 [Path9](C:/Users/ScherrerL/Desktop/apple/github_publish/acg720-fpga-flight-controller/out/z_aw_fix_20261026/compact_aw_v18/physical_p3r0_dsploc_01/source/impl/pnr/acg720_ano_port.tr:857) 为 `index_1_s7/Q → m_a_21_s0/D`，20ns 下 setup −0.563ns，data delay 20.505ns；其中 route 14.149ns、cell 6.025ns、C2Q 0.331ns，clock skew 0。五条最长数据 route 合计 11.360ns；问题主要在选择网络的布局布线，不能仅凭 carry 长度归因。

| 实际 VG | index bit1 副本 fanout | 低2位 XNOR 解码器 fanout |
|---|---|---|
| v18 DSP 当前 VG | 129 / **127** | **174 / 174** |
| exact v4 max_fanout100 native VG | 59 / **51** / 100 / 50 | 48 / 100 / 100 / 100 |

首解码 `n8507_s5` 是 LUT2，INIT=`4'h9`，输入为 index[0]/index[1] 的复制网络。其后 `n8558_*` 读取 24×29-bit LPF 存储，经共享减法 carry 再穿过多状态复用的 `m_a` 选择树。独立按实际 LUT INIT/MUX 解释 `n8558_76`，23个非零合法 index×20组随机数组的460次检查全部对应 `lpf[index-1][8]`；这是定位诊断，不是等价证明。

对应 [源码](C:/Users/ScherrerL/Desktop/apple/github_publish/acg720-fpga-flight-controller/out/z_aw_fix_20261026/compact_aw_v20/canonical/source/core/ano_attitude_estimator.v:433) 在 FILTER_MUL 计算 `filter_input[index>>2]-lpf[index]` 或 `lpf[index-1]-lpf[index]`。B3、原B4、v4、v18、v20 的 estimator 均为同一 SHA `72c7e1fe…dea3ea0a`；当前 compact_aw 分支没有改过这个 RTL。更早的资源调查已提出 LPF RAM/lazy-seed 重构，但明确未实现，且要证明全24槽同拍 seed、reset/reseed 和调度，超出本轮最小方向。

已有复制实证，但没有复制后可布通的结论：本轮 exact v4 global100 SYN 为 **+81FF/+83LUT**，ALU/DSP/BRAM不变；实际 [physical.log:381](C:/Users/ScherrerL/Desktop/apple/github_publish/acg720-fpga-flight-controller/out/z_aw_fix_20261026/compact_aw_v4_fan100_native/physical_p3r0_01/verification/physical.log:381) 报 **707 unrouted nets**，vendor/root 都1。早期 B0AB 的类似试验也复制过该 decoder（+81FF/+88LUT），但未PNR、未采用。v20/v22 已增加 guards/local hints，不能把这些不同全芯片结果直接转成当前收益。

可考虑的两个独立、小范围方向：

1. **先做局部 decoder 扇出实验。** 对 LPF 读选择的数据 index/明确组合选择网络施加局部 `syn_maxfan`，必要时将读 mux 的共同选择项显式命名再约束。只有新 VG 显示关键 INIT9 decoder 确实复制、原174负载分散，才算命中；仅 index FF 增加副本不算成功。保持原存储、32位有符号减法、状态和握手不变。global100可作单选项对照，但已有707 unrouted的反证，不能优先假定它能改善布通。

2. **若局部 hint 未命中，再考虑与 index 同拍维护的私有 one-hot 读选择缓存。** 一个32位选择缓存覆盖全部5位 index；所有 `index<=0` 同拍置bit0，所有 increment 同拍旋转，其余同拍保持。用它选出 current/previous 两个原29位有符号扩展值，再做原共享32位减法；不展开24套减法器、不加状态或等待周期、不改量化/余数。源码共有10处归零、6处递增，且 reset/invalidate 本身不写 index，因此缓存也必须在这些分支持有，不能擅自全局复位到bit0。需证明 `selector == (32'b1 << index)` 每拍成立、同拍写回后的下一槽读取一致，并比较原/新完整 estimator 状态及发布周期。该方向只有潜在收益；仍需实际 SYN 面积/扇出和严格20ns物理结果。

本次仅读取源码、真实VG/TR和已有历史，写入本目录。未创建候选、未运行综合/PNR/仿真、未访问硬件。两份 release 生产脚本仍保持上一封存哈希。机器可读输入哈希与映射数据见 [EVIDENCE.json](C:/Users/ScherrerL/Desktop/apple/github_publish/acg720-fpga-flight-controller/analysis/agent_reviews/imu_index_20261027/EVIDENCE.json)。
