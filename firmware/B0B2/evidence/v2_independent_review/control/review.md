本次独立只读复核未发现 v2 改动新增控制反馈，也未发现现有保留位投影或线包证据的绑定缺口。结论范围是源码差分、被动观测连接、已有有界仿真证据及字节/CRC/哈希重算。未重新启动仿真、vendor 或硬件操作。

复核基准为 `firmware/B0B2/evidence/source_revisions/copy99_v1`。独立重算该归档全部 93 个文件的 SHA，核实归档源文件集为完整 53 项，并核对其 index 与 `evidence/v2_integration.json` 中的绑定。当前 53 项和 integration、projection、SiK wire 三份收据中的源映射完全一致；恰好两项改变，其余 51 项逐字节一致。复核开始与结束的当前源哈希相同。

| 文件 | copy99_v1 SHA256 | 当前 v2 SHA256 |
| --- | --- | --- |
| `source/sik_imu_diagnostic.v` | `7783baba34cc7cdc014d17f38e9e0d5f52210e1d8b02bde49a5f308d8ee3160e` | `aff3e5a2fc19f045faf01885f23cbe245753c048686982c9d19a97bcc57bc160` |
| `source/telemetry_tx.v` | `2ae5bd7edf24418c9707add77711789a4f6cbeb339bef6259e9f41c29785796b` | `3aadbf30852adeb70cb40011d1b57d859c1bf7b4aec1b31625c260580b4b557c` |

SiK 的实际差分删除了两个 32 位本地历史寄存器及其 next/reset/update 逻辑，将原对应输出槽改为零，并保留其余接口、事件判定、窗口、hold、计数和发布条件。两个不可用槽为 `latest_rejected_source_id`（summary `[319:288]`，payload 字节 24–27）和 `first_protection_time_ms_low32`（`[95:64]`，字节 52–55）。因此 v2 丢失“最新被拒样本的 ID”及“首个真实保护事件的精确毫秒时间”能力；当前捕获 tick/uptime 不能代替旧事件时间。最新拒收的 reader/detail/raw flags、首个保护 code/mask/imu/attitude/pose_age、consumed ID/dt 等继续保留。地面解析将两个槽解释为 null/capability false，不能将零解释为真实 ID 或事件时间。

`telemetry_tx.v:44` 在换行归一后只有一处字面量变化：A585 version 1→2，type 仍为 1，长度仍为 76 字节（64 字节 payload）。独立计算验证除这一字面量外全文相同。CRC 算法、序列捕获和发送状态机未变（`telemetry_tx.v:20–24,60–66,183–227`）；版本和 payload 的变化会按既有算法改变 CRC 值，不能把 v2 A585 称为旧 A585 全包等价。

被动性依据是实际输出去向和调度关系。`sik_imu_diagnostic.v:15` 仅输出 summary_body/tick；顶层 `acg720_ano_port.v:296–305` 将其送给 telemetry，再送串口镜像。两个被删寄存器没有控制消费者。telemetry 唯一非串行数据输出 snapshot_hold 的表达式、状态转移、frame_complete/index 边界均不变；这些分支不依赖 payload/CRC 值，UART busy 也由 start/固定 bit/baud 计数控制（`core/spi_uart_modules.v:74` 起）。故本次 v2 差分不会通过 snapshot_hold 改变控制输入或观测快照时点。其余 51 项（含 top、flight_core、tap、reader、guard、estimator、navigation 和约束）字节相同，为这一增量判断提供直接边界。这里不是对整个 B0B2 相对 B0B0 的重新等价证明。

`evidence/v2_projection_proof/index.json` 的全部 26 文件大小和 SHA、24 个 origin 路径、integration 的 3 个原型收据绑定均已独立核对。归档 reference 确为 copy99_v1 的 SiK；`reference_renamed.v` 在换行归一后仅改变模块声明名。actual tap、候选、TB、runner、工具二进制、两个命令退出码/日志、原始 VVP 产物及脚本哈希均与 projection 收据相符；当前 source53 与该次测试收据一致。

投影 TB `sik_copy_contract_tb.v:16–39` 让真实 `imu_diagnostic_tap` 驱动新旧 SiK；`43–52` 在每个 negedge（posedge NBA 之后）比较 448 个保留 summary 位和 32 位 capture tick，并断言两个槽为零、tap 在 valid 之外保持 raw/pose body。已有运行的 120,000 周期结果通过：raw/pose 同拍 14,358 次，拒收 29,979 次，hold 内更新 38,664 次，hold 上/下沿 28,697/28,696 次，无 pose 最长 7,001 周期，reset 11 周期；taking_off 新窗 121 次、hold 中新窗 62 次、新窗与事件同拍 11 次。窗口清旧 fault 的 NBA 规避逻辑未变（SiK `new_window/active_diagnostic_fault`），上述同拍覆盖核实了保留投影的边界行为。

该投影采用合成事件刺激，tap 的 `POSE_AGE_TRIGGER` 缩短为 1,000 ticks，link/attitude 等状态由 fixture 驱动；它没有实例化整条真实 estimator/guard，也不是 60ms 保护或实飞失效实验。它证明这些已覆盖时序上的 448 位+tick 逐拍一致，不证明全 512 位、不证明所有可能输入的形式等价。未重跑这组既有仿真。

线包复核独立从归档 hex 解析 644 字节，并逐包重算 A579/A57A 的 XOR 及 A580/A581/A582/A583/A585 的 CRC16-CCITT-FALSE；所有校验均正确，七包 sequence 相同。A585 header/version/type 为 A585/2/1，两个不可用槽各四字节全零。前 568 字节与同一 fixture 下冻结 B0B0 telemetry 模块产生的黄金数据逐字节相等；该冻结模块 SHA 同时匹配 B0B2 baseline 和 wire 收据。wire TB 按真实 434-clock UART 位周期采样；fixture 将 PERIOD 缩短，不能将该批数据解释为现场采样。既有 18 个协议/接收器测试日志包含 v1/v2、非法零槽、CRC 损坏重同步、source/reset freshness 清除且全部通过；相关当前 runner/TB/ground 文件哈希已重新核对。这里只读核证，没有重新执行这些测试。

formal/shadow 资源 XML 完全相同，formal synthesis 收据的 logical source53 也匹配当前。但两份 VG 的 SHA 明确不同，现有 binding 明确 `full_netlist_equivalence_proved=false`。本复核不将资源相同推导为综合网表等价，不评判当前 PNR、安装资格或飞行条件。

`audit.py` 是本次只读可重跑核验入口（仅打印 JSON，不运行仿真/vendor/设备），`audit_result.json` 记录实际重算结果及完整前后源映射，`source_delta.diff` 保留两文件差分，`index.json` 绑定本目录产物。未修改正式源码、helper、协议文档或已有 review JSON。
