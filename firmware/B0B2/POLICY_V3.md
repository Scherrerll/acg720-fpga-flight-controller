# 已确认的超时策略 v3

本次为用户明确要求的行为修改。旧 v1/v2 的等价证明、布线结果和硬件检查不能作为当前源码的合格证据。没有进行下载、上电或飞行测试。

## 当前行为

- IMU 无新样本超过 60ms 不再触发 reader 重启、guard 资格超时或姿态年龄失效。
- 删除核心姿态年龄计数、对应门控、下游年龄输入/判断、事件年龄锁存及诊断年龄触发。旧测高几何中由姿态发布驱动的额外 60ms 发布看门狗也删除。
- 保留真实接收间隔 dt 计时。静默期间不产生样本或姿态更新；恢复后实际 dt 过长仍按数值边界拒绝并恢复初始化。没有用固定 1ms 替代真实 dt。
- 保留芯片 ID、配置、传输、数值检查和启动校准；保留独立控制请求与电机命令超时，以及积分步长上限。
- 遥控有效帧断流为 500ms，坏帧仍拒绝。
- MTF 模块在线指示为 1s；控制来源新鲜度仍为 100ms，metric 可用性仍为 200ms。来源新鲜度、计算超时及其他传感器自己的发布规则不因在线指示而放宽。

用户确认 `reference_ano/quadrotor_tm_v1_20261012/Quadrotor_TM_V1` 为 P2 参考。P2 任务传入 1ms 不等于 FPGA 可以伪造采样周期。

## 遥测明确标识已移除的年龄

帧长度和非年龄字段单位保持，旧年龄位置成为固定保留槽，不存在对应计数器或锁存。接收器将其解析为 `None` / unavailable，禁止把零解释为新鲜数据。

| 新帧 | 长度 | 逻辑记录 | 已移除内容 |
|---|---:|---|---|
| A586 | 224B | primary / a579 | 当前姿态年龄、两次门控事件年龄 |
| A587 | 32B | acceleration / a57a | 姿态年龄 |
| A588 v5 | 40B | info / a580 | 最近门控事件年龄 |
| A589 v2 | 48B | rotation / a583 | 配对姿态年龄 |
| A585 v3 | 76B | IMU summary | 首保护姿态年龄 |

总组仍为 644B。A581 v3 的在线位表示 `<1000ms`；其 metric 检查仍为 `<200ms`。A582 控制数据布局不变。新接收器继续支持历史帧和 A585 v1/v2；新头避免旧接收器把保留槽误当成 0ms 年龄。

姿态、加速度有效位表示显式资格状态；遥测到达不代表产生了新测量。界面显示年龄不可用，不重建、插值或伪造 IMU 更新。最大姿态间隔只记录真实发布之间的已完成区间，不在静默期累计未完成姿态年龄。

## 离线验证

```powershell
python -B firmware/B0B2/tests/run_policy_v3.py --iverilog C:/Users/ScherrerL/Desktop/apple/.tools/iverilog/app/bin/iverilog.exe
python -m unittest discover -s firmware/B0B2/tests -p test_protocol.py
python -m unittest discover -s firmware/B0B2/tests -p test_analyze_bench.py
python -B firmware/B0B2/tools/prepare_sik_receiver.py --output out/B0B2/policy_v3_receiver_new
```

旧 `run_policy_tests.py`、被动等价和 `verify_offline.py` 是 v1/v2 的历史验证流程，不能套用到本次有意改变行为的源码。当前物理产物必须由精确网表、原 17 引脚、19.5ns 约束及完整 STA 重新验收；逻辑删除不保证布通或达到 50MHz。

## 2026-10-25 本轮物理结果

当前保留源码已能零未布通：P4/R0、资源复制关闭，供应商返回 0，器件、17 引脚和 B0B2 身份检查通过。但最佳 Fmax 仅 39.234MHz；19.5ns 约束下 setup 有 1,194 个违例，最差余量 −5.988ns。因此没有通过完整物理验收。hold、recovery、removal 和最小脉宽均无负余量。

本轮共完成 8 组当前策略及独立 PWM 优化候选试验，4 组布通，均未达到所需时序。PWM 第二版通过组件与实际核心集成对比，但物理结果更差，未合入当前源码。第一版集成反例与取消证据保留在工作目录。

准确源码快照、精确网表、配置、完整 STA、各组结果和只读完整性检查保存在 [离线证据](evidence/policy_v3_offline_20261025/README.md)。该目录不包含位流，不能作为下载或飞行放行依据。没有下载、刷 Flash、物理串口、上电或电机操作。
