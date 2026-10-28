# B0B5 V8：水面双推进与用户测试记录

本次选中版本为 `v8 / a13_a14 / P3R0`，在独立副本中加入水面双电机控制，保留冻结 B0B4 目录。2026-10-29用户在收到下列精确源码和位流路径后反馈：“好的，我测试了一下没有问题，可以的”。这是用户报告的当前接线和测试条件下运行正常，可作为后续修改的工作基线。

## 源码与位流

- [Gowin 源码工程](../../analysis/20261028_water_drive/qualified_offline_B0B5/source/acg720_ano_port.gprj)：57个源输入，工程引用为相对路径。
- [选中烧录文件 acg720_ano_port.fs](../../analysis/20261028_water_drive/qualified_offline_B0B5/DO_NOT_PROGRAM/acg720_ano_port.fs)。
- [完整原始审查包](../../analysis/20261028_water_drive/qualified_offline_B0B5/README.md)、[功能与边界](../../analysis/20261028_water_drive/qualified_offline_B0B5/DESIGN.md)、[资格报告](../../analysis/20261028_water_drive/qualified_offline_B0B5/qualification.json)、[SHA-256清单](../../analysis/20261028_water_drive/qualified_offline_B0B5/manifest.json)。

位流 SHA-256：

```text
d1e0e3a46178315d103d8db26a05806add46ded9410e2f2e6b683b84742649f5
```

`DO_NOT_PROGRAM`目录名、包内“禁止安装”文字，以及`installed=false`、`hardware_qualified=false`、`hardware_actions=false`均保留打包时的原始离线状态。该包的149个文件由清单绑定，本次上传不回写这些文件；后续用户反馈记录在本页。目录名不代表另一个位流。

## 主要功能

| 项目 | 行为 |
| --- | --- |
| 输出 | 左A13（P7-1/GPIO0_0）、右A14（P7-2/GPIO0_1），3.3V逻辑约束，50Hz PWM |
| PWM协议 | 1000μs反向、1500μs中位停止、2000μs正向；用户此前确认配套驱动器支持此协议 |
| CH6 | 高位请求水面，低位请求飞行；复位默认飞行；飞行已解锁时忽略切换 |
| CH5 | 低位停机/准备，高位确认使能 |
| CH2 / CH4 | 前后推力 / 左右差速，1500μs中位，±30μs死区；两路分别限幅到1000–2000μs |
| CH3 / CH1 | 水面要求CH3低位；切模式和准备使能时CH1/2/4回中 |
| CH7 | 保留原飞行模式选择，水面检查通道有效性 |

模式切换要求逻辑停机、CH5低位、CH3低位和CH1/2/4回中，连续至少25ms。选定水面后，保持回中，CH5低位至少0.5秒，再高位至少0.5秒才使能；实际操作各保持约0.6秒。飞行和水面使能互斥。

有效PPM中断/超时最迟约100ms撤销水面使能；坏通道、模式或CH3/CH5条件失效也清除准备状态，恢复后CH5一直高位不能自动重启。任一侧换向时两侧共同输出中位至少15个完整帧（≥300ms）。这些是逻辑及信号行为，不是机械停转证明。

如果接收机在无线失联后仍发送原来的有效PPM，FPGA不能仅凭PPM识别无线失联，实际无线失联行为取决于接收机的失效输出设置。

## 验证范围

离线审查包已通过149文件完整性绑定、精确源码57/网表/位流核对、真实50MHz完整布线和13项功能检查。Fmax为50.032MHz，setup/hold最差裕量为+0.013/+0.169ns，setup余量较小，结论绑定本次精确产物。

2026-10-29的用户反馈没有逐项列出正反转、模式切换、失联、换向等待、复位等测试结果，也没有独立镜像读回、Flash持久性、冷启动或飞行记录。因此记录为用户报告测试正常，不推断上述项目均已验收。助手本次只整理并上传仓库，没有执行硬件烧录或试转。

从仓库根目录核查原始离线包（Python 3.10+，不访问设备）：

```sh
python -B analysis/20261028_water_drive/qualified_offline_B0B5/verify_review.py analysis/20261028_water_drive/qualified_offline_B0B5
```

输出中的`HARDWARE NOT QUALIFIED`指原始离线包的核验范围，与本页后续用户反馈分别记录。完整仿真重跑需要相应仿真器及Gowin工具依赖；此命令核验已归档的输入、结果和证据。
