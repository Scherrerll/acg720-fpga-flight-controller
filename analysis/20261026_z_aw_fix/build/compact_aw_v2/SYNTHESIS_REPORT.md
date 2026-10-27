# compact_aw_v2：完整顶层展开、综合及映射审计

本轮仅对独立v2源完成一次full-top elaboration和一次新Gowin SYN；二者实际`p.wait()=0`，映射审计通过。**相对compact_v1，全top ALU减少66、LUT增加37、FF不变。** 这些是综合资源测量，不能推出CLS、布线或20ns时序已经改善。

## 冻结源与真实执行

源目录 `out/z_aw_fix_20261026/compact_aw_v2/canonical/source` 共55文件；仅hold相对compact_v1变化，SHA256 `afc656820788d8cbf7c61d8c4e7526bec3dceb950673de9df18cb68a7d0632f3`，其余54文件逐字节相同。bank仍1000/350、generation0、A591 B4；build/SDC/CST未改。`source_freeze.json` SHA `8aae3df5b6578fb69c0566d6498dcbaaa8fd0ebf608580469eb455271afd6414`。

该源只将候选方向flag在state22按真实积分step符号捕获，taking_off=false按旧I相对0的方向捕获；删除state66两组动态比较。其数学可达范围证明另见 `../sign_step_bound.md`（SHA `cf2a9de051973862c68cd2d462678cf6436756c3a65cc4ef2c4f16f933de9c0d`），实际行为回归由主线独立负责。本报告不把证明或综合替代行为回归。

新fixture为 `out/z_aw_fix_20261026/compact_aw_v2/build_attempt_01`。执行入口 `run_synthesis.py` SHA `23fe046b259c6713536fc27862eb80a3b392808a77e842aac2085c3f91f3d658`，只读import原 `firmware/B0B4/build_candidate.py`（SHA `abb5246c203b73c111f80bc91f8db6c8220463f7d4c5cf48dbfe2167ef49db84`）。CANON、EXPECTED_CHANGES、ATTEMPT、SOURCE、VERIFY均显式绑定v2；未调用原main或PNR。

Full-top Icarus展开实际wait0。SYN vendor PID21932、helper34936，开始 `2026-10-26T04:44:12.797929Z`，结束 `04:48:48.105187Z`，`normal_wait_return=true`、`actual_p_wait=0`，原日志包含 `SYNTHESIS_COMMAND_RETURNED_EOF`。DEVNULL/CREATE_NO_WINDOW及去除显式exit的EOF驱动保留。只执行`run syn`，该SYN fixture没有PNR目录。

最终VG SHA256：`497200b2627194c9047d459402f239592fa75e16c491e39251d20c6b4238a39f`。

## 实际XML资源比较

| 资源 | compact_v1 | compact_v2 | delta |
|---|---:|---:|---:|
| 全top FF | 27786 | 27786 | 0 |
| 全top LUT | 36332 | 36369 | +37 |
| 全top ALU | 9658 | 9592 | −66 |
| controller FF | 3298 | 3298 | 0 |
| controller LUT | 4951 | 4985 | +34 |
| controller ALU | 1675 | 1609 | −66 |
| bank FF / ALU | 290 / 79 | 290 / 79 | 0 / 0 |
| bank LUT | 433 | 437 | +4 |

全top DSP各类型保持30×MULTALU27X18、7×MULT12X12、13×MULT27X36，BSRAM保持2。LUT与ALU计数直接相加为−29，仅说明这两类计数的净变化；不能据此承诺物理packing或route收益。bank源码未变而综合归属LUT变化，不能把全设计映射差异误写为bank RTL变更。

## 映射审计

- 实际图包含27786个FF、27888个clock pins；所有clock pins仅连接clk50派生的同一合法时钟或GND，非clk50/非GND项为0。
- radio_rx pad仅负载 `parameter_uart/rx_meta_s0.D` 和 `rx_meta_s1.D`；既定meta Q仅负载第二级 `rx_sync_s0.D/rx_sync_s1.D`。原false_path仍仅从radio_rx pad起，Q后路径未放宽，SDC仍唯一20.000ns clk50。
- 真实mapped顶层18个scalar ports与CST端口集合完全一致。
- bank中P/I各存在16个真实DFF，D/Q端存在，mapped INIT逐bit重建分别1000/350；没有把默认参数当常量扫除。审计中保存每个FF的类型/引脚及全primitive histogram。
- SYN结束后重新核对v2 canonical55及build55、compact_v1 canonical55、原`firmware/B0B4/source`55均与启动前一致；旧helper未改。

## 核心回执SHA256

以下均相对v2 `build_attempt_01/verification`：

| 证据 | SHA256 |
|---|---|
| `elaboration_exit.json` | `037a6feef1e1b41eacae57ad85b56005f87694c121e2e0be2dfd97cfe8940991` |
| `synthesis_exit.json` | `5130d72ef64747460af05496d537c3e309085df99a10187dd13c405e5d5ac217` |
| `synthesis_summary.json` | `cca3313e0b3ea518a55d44117a4115f5b6e0103a8edb78513572133fc28593a6` |
| `mapped_audit.json` | `c5dff8f655cbbd0bc9ed9a193bc6d92a70cf8c074bb4083eab89fec8cdd7f698` |
| `gain_port_audit.json` | `ef3b1d9015f9cf9eb9e55bc9e217d97efc520afb2b7137e057157c555ef4a432` |
| `resource_comparison.json` | `520cf910567687ea02b53e2492c7f04e9fe079916b1b3d6716a34b4d3bd6910a` |

`SYN_EVIDENCE_MANIFEST.json`绑定静态SYN证据与source55，不纳入正在运行的物理日志。主线随后单独授权该精确VG的fresh `physical_p2r0_01`，实际P2/R0、map2/repl0/20ns/B4，源build.tcl的P3仍不覆写。物理项目已成功open、skip SYN并进入placement；该新物理尝试的最终资格应读其独立回执，不能从本SYN报告推导。
