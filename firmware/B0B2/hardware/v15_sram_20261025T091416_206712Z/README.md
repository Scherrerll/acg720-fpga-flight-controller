# V15 B0B2 SRAM 上板记录

2026-10-25 17:14（北京时间），已将通过原 19.5ns 时序约束、零未布通、51.400MHz 的 V15 位流下载至 SRAM。下载前取得当次拆桨、机架放稳、油门最低、SWA/SWC 低档确认，并核验实时停机状态。

- 下载器：唯一 Gowin USB Cable，序列号 6，位置 289；器件 ID `0x0001481B`。
- 实际操作仅为读取身份、SRAM 下载、再次读取身份（0、2、0）。UserCode 从 B0B0 变为 B0B2，下载日志明确为 SRAM Program / Finished。
- 位流 SHA256：`3b9920acc1abecf6e0ef50465f5bc408d9b74af2ac6d046cb151137a375b4306`。源码、网表、物理报告及功能证明与已封存交付包绑定。
- 下载后取得新鲜 B0B2 身份与停机遥测。接收端支持 A588 v5、A585 v3 等当前协议，已删除的姿态年龄显示为不可用。

随后进行了 60.03 秒、61 个快照的只读静止观察：所有样本均未解锁、控制器关闭，四路命令和报告 PWM 始终为 1000μs；IMU 校准完成、姿态有效。accepted_count 增加 60,094，rejected_count、controller_fault_count、控制中断和撤销计数均无增加。

通信窗口内收到 296 个主帧，主帧序号显示丢失 4 帧，丢弃字节增加 171，CRC 错误计数无增加。这只能描述已记录窗口，尚未定位链路丢失原因。测距、光流和高度当前均未报告有效数据，不构成这些功能已完成实物验收的证据。

没有写 Flash，没有发送解锁或电机控制命令，没有进行带动力或飞行测试。PWM 数值来自遥测，未使用仪器独立测量波形。

主要证据：

- [安装报告](report.json)、[SRAM 下载原始日志](program_sram.txt)、[下载后器件身份](identity_after.txt)。
- [一分钟观察结果](stationary_60s/summary.json)、[原始快照](stationary_60s/snapshots.jsonl)。
- 兼容接收端位于仓库 `out/B0B2/ground_v15`，继续使用 COM17 / SiK / 115200、HTTP 8765，只读记录至 `C:/Users/ScherrerL/Desktop/apple/flight_logs/20261025T090759Z_8624c3f6`。旧 8767 接收服务曾动态切换到 COM17 并占用端口，确认停机后已正常关闭，日志保留。
