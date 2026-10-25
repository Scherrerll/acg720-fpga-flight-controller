# B0B1：光流失稳的被动诊断工程

此版本用于定位 2026-10-25 两次光流试飞的最初失效原因。新增诊断不改变控制算法、IMU 判据、60ms 保护、起飞流程或落地锁。它不是已经修复或完成飞行验收的固件。

原 B0B0 源码、默认 Flash 和回退位流保留。B0B1 位流必须重新综合布线、绑定输入与测试结果并单独验收；离线通过后才进行人工确认的拆桨 SRAM 测试，不写 Flash。

当前两次全顶层构建均未通过：分别剩余 930 和 575 条未布线网络，没有可安装位流或时序验收结论。输入与失败结果摘要见 `evidence/failed_routing.json`。B0B1 保留为被动诊断及失败证据；输入策略修复在独立 `../B0B2` 中继续，不能把两者结论混用。

## 诊断链路

- USB 监控 M15：921600 baud、8N1，新 A584/v1 高频诊断。50MHz / 54 的实际波特率为 925925.93，偏差 +0.47%。
- SiK B15：原 115200 A579～A583 协议，固件身份明确为 B0B1。原接收器严格限制身份，需要先用 `tools/prepare_sik_receiver.py` 生成独立兼容副本，不能把 B0B1 冒充 B0B0。
- 每个原始记录和姿态发布保留来源、采样时间、接受资格与时间差；首个异常冻结原因及拒收三元组。队列满时明确计数，不回压或暂停传感器。完整格式见 [DIAGNOSTIC_PROTOCOL.md](DIAGNOSTIC_PROTOCOL.md)。
- USB 数据记录到新目录的 `raw.bin`、`decoded.jsonl`、`summary.json`。原始记录只在 reader_valid/config_ok 时代表新物理观测；接受计数增加不代表姿态必然有效。

## 编译与离线验证

在仓库根目录运行；所有编译产物写入被忽略的 `out/B0B1`。需要 Gowin V1.9.12.04 和 Icarus，工具均不访问硬件。

```powershell
python -B firmware/B0B1/tests/run_tap_tests.py
python -B firmware/B0B1/tests/uart_test.py
python -B -m unittest discover -s firmware/B0B1/tests -p test_protocol.py
python -B firmware/B0B1/tools/build.py --output out/B0B1/build_p2r2_rep1
```

构建目录不得复用。`inputs.json` 绑定实际输入，`console.log` 保存工具输出，`result.json` 单独记录布线、时序、引脚和位流身份。实际时钟仍为 50MHz；约束为单一 19.5ns 时钟，不添加 false-path/multicycle，也不复用 B0B0 网表内部的强制全局网名。

## 与早先自稳版本的差异

原默认 B0AC 到 B0B0 确有控制流程变更：按 ANO 参考对齐起飞状态机、自动起飞辅助、高度环及光流速度 PI，并在自动起飞阶段令角速度环积分增益为零。不能把两版当成完全相同的飞行控制。

逐字节比较显示，两版 `imu_temporal_check_pipelined.v` 和 `imu_checked_guard_pipelined.v` 完全相同；姿态估计器的差异为增加同步发布的 45° 倾角资格标志，未改变估计数值方程。B0B0 固化之后的网页优化也未改变机上固件。早先自稳表现和本次光流失稳之间的因果关系仍需诊断，不能仅凭模式名称或版本时间判定。

## 下一步实物验证

先确认拆桨、机架放稳、油门最低、SWA/SWC 低档及两根板上 USB 的实际状态，再临时下载经过验收的 SRAM 位流。程序不会自动解锁或转动电机。静止、人工小角度运动和拆桨动力采样分别留档，不用静止结果替代动力结果。

如果拆桨不复现，结论保持“未复现”。用户当前没有专用带载台架，虽愿意配合后续试飞，仍需根据已得到的诊断和地面验收结果确定下一次采样方式。本诊断版本不提供飞行就绪结论。
