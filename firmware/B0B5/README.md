# B0B5 V8：水面双推进与测试记录

本次选用 `v8 / a13_a14 / P3R0`，在独立副本中加入水面双电机控制，原 B0B4 目录保持冻结。2026 年 10 月 29 日，用户收到下面列出的源码和位流路径后反馈：“好的，我测试了一下没有问题，可以的”。这说明在当时的接线和测试条件下运行正常，可以作为后续修改的工作基线。

## 源码与位流

- [Gowin 源码工程](../../analysis/20261028_water_drive/qualified_offline_B0B5/source/acg720_ano_port.gprj)：包含 57 个源输入，工程使用相对路径引用。
- [选中烧录文件 acg720_ano_port.fs](../../analysis/20261028_water_drive/qualified_offline_B0B5/DO_NOT_PROGRAM/acg720_ano_port.fs)。
- [完整原始审查包](../../analysis/20261028_water_drive/qualified_offline_B0B5/README.md)、[功能与边界](../../analysis/20261028_water_drive/qualified_offline_B0B5/DESIGN.md)、[资格报告](../../analysis/20261028_water_drive/qualified_offline_B0B5/qualification.json)、[SHA-256 清单](../../analysis/20261028_water_drive/qualified_offline_B0B5/manifest.json)。

位流 SHA-256：

```text
d1e0e3a46178315d103d8db26a05806add46ded9410e2f2e6b683b84742649f5
```

审查包中的 `DO_NOT_PROGRAM` 目录名、“禁止安装”文字，以及 `installed=false`、`hardware_qualified=false`、`hardware_actions=false` 保留的是打包时的离线状态。包内 149 个文件由清单绑定，上传时没有回写；后续用户反馈记录在本页。这个目录名不代表另一个位流。

## 主要功能

| 项目 | 功能 |
| --- | --- |
| 输出 | 左侧 A13（P7-1/GPIO0_0），右侧 A14（P7-2/GPIO0_1）；3.3 V 逻辑约束，50 Hz PWM |
| PWM 协议 | 1000 μs 反向，1500 μs 中位停止，2000 μs 正向；用户此前确认配套驱动器支持此协议 |
| CH6 | 高位请求水面模式，低位请求飞行模式；复位后默认为飞行模式，飞行已解锁时忽略切换请求 |
| CH5 | 低位停机或准备，高位确认使能 |
| CH2 / CH4 | 分别控制前后推力和左右差速；中位为 1500 μs，死区为 ±30 μs，两路分别限幅至 1000–2000 μs |
| CH3 / CH1 | 水面模式要求 CH3 低位；切换模式和准备使能时，CH1/2/4 需要回中 |
| CH7 | 保留原飞行模式选择，水面模式下检查通道有效性 |

切换模式时，需要保持逻辑停机、CH5 和 CH3 低位、CH1/2/4 回中，持续至少 25 ms。选定水面模式后，保持回中，CH5 先在低位保持至少 0.5 秒，再在高位保持至少 0.5 秒，才能使能；实际操作时每个位置保持约 0.6 秒。飞行和水面使能互斥。

有效 PPM 中断或超时后，水面使能最迟约 100 ms 撤销；通道异常、模式条件或 CH3/CH5 条件失效时，也会清除准备状态。恢复后，如果 CH5 一直处于高位，系统不会自动重启。任一侧换向时，两侧共同输出中位至少 15 个完整帧（≥300 ms）。上述结果描述的是逻辑和信号行为，不能证明机械部分已经停转。

需要注意：如果接收机在无线失联后仍发送原来的有效 PPM，FPGA 无法仅凭 PPM 判断无线连接是否中断。实际失联行为取决于接收机的失效输出设置。

## 验证范围

离线审查包已通过 149 个文件的完整性绑定、57 个源码输入与网表和位流的核对、真实 50 MHz 完整布线，以及 13 项功能检查。Fmax 为 50.032 MHz，setup/hold 最差裕量分别为 +0.013/+0.169 ns。setup 余量较小，上述结果只对应本次归档的具体产物。

2026 年 10 月 29 日的用户反馈没有逐项列出正反转、模式切换、失联、换向等待、复位等测试结果，也没有独立镜像读回、Flash 持久性、冷启动或飞行记录。因此这里仅记录用户反馈测试正常，不将上述项目推定为已验收。此次仓库整理和上传没有执行硬件烧录或试转。

在仓库根目录运行以下命令，可以核查原始离线包。需要 Python 3.10 或更新版本，命令不会访问设备：

```sh
python -B analysis/20261028_water_drive/qualified_offline_B0B5/verify_review.py analysis/20261028_water_drive/qualified_offline_B0B5
```

输出中的 `HARDWARE NOT QUALIFIED` 说明原始离线包的核验范围，与本页记录的后续用户反馈分别保留。完整重跑仿真还需要相应仿真器和 Gowin 工具；上述命令核查的是已归档的输入、结果和证据。
