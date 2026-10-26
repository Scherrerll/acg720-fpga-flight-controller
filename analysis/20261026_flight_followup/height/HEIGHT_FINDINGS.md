# 高度首次下降：独立复核与最小真实 RTL 见证

本调查只读冻结证据和已交付 B0B3 源码；本目录是唯一写入位置。没有操作 HTTP、串口、下载器、遥控或飞机，没有修改固件、旧报告或 Git。实际飞行记录来自旧 P005/I0；B0B3 的接口、Flash/冷启动验证不是新的飞行样本。

**结论：首次高度失效仍没有唯一历史首因，但已实质收窄。第二次降级最早可见于 seq375，而不是376；完整坏 Micolink 帧、多种模块资格失败以及正常回调必然拉低 ready 的说法不符合现有证据。真实 RTL 表明一个短时高度资格失败足以锁存降级，之后 ready 恢复而导航仍报告 reason2，与历史外观相同。它证明机制可达，不证明历史一定出现了所注入的值。没有确定新的产品代码缺陷，也不建议凭这些记录改变保护阈值。**

## 1. 输入身份与复算

主输入是 H 中 `workspace_snapshot/timing_closure_20261025/v15_xy_p005_i0_review_20261025/hardware/response_20261025T160009_877779Z/telemetry_clip.jsonl`，SHA256：

`73df2c5c9b36e3e6d8f8afee94b6c3e508ab8d4112982055e7ac9fb8d96a0649`

`analyze_height.py` 逐行读取该原窗口，按 `(epoch, sequence, protocol)` 保留真实子包及原行号；不插值、不跨 epoch、不要求先有 A579 才使用其他子包。输出114行 `boundary_packets.csv`、`packet_evidence.json` 和实际高度链源码差异。不会执行旧分析驱动或写回冻结输入。

与当时 P005 比较，以下8文件与交付 B0B3 **逐字节相同**：`core/height_loss_fallback.v`、`core/ano_flight_state.v`、`core/ano_attitude_estimator.v`、`core/imu_pipeline_pipelined.v`、`sensor/mtf01p_reader.v`、`sensor/mtf_shared_geometry.v`、`position/pose_time_adapter.v`、`position/mtf_shared_height_fusion.v`。`core/flight_core.v` 的新增部分是参数写安全输出；顶层和 `mtf_xyz_navigation_control.v` 的差异是参数接口接线，没有更改高度可用性算式。完整差异见 `height_chain_source_changes.diff`。B0B3 的控制器及数学调度仍有此前已审查的变化，不能据此声称全部源码相同。

## 2. 先看原子子包，第二次窗口缩到200ms

| epoch22 | 最后 false | 首个 true | FPGA uptime 窗口 | 原始 A580 行号 | 关键边界 |
|---|---|---|---|---|---|
| 第一次 | seq230 | seq231 | 46199→46399ms | 7822→7829 | 首次 true 时 taking_off/flying 仍真，主帧仍 armed/controller，ready 已恢复 |
| 第二次 | seq374 | **seq375** | 75000→75200ms | 8825→8831 | seq375 缺 A579，但 A580、A581、A582、A585 存在；A582 在8833行 |

窗口长度指两次遥测快照的 FPGA uptime 差，不能当作失效持续时间或准确触发时刻。UART 子包的主机接收时刻不同，不能拿主包时间替换缺失的主包或制造 seq375 的 RC 值。

两次边界均为：A581 sample_count +20、module_time +200ms，missing/duplicates/restarts/checksum/length/UART/timeouts 均无增长，**integration_breaks 始终1**。A582 geometry publication 计数也各 +20；MTF sample_count 减 navigation_sequence 的差维持270。

这些累计计数比单个5Hz快照的“状态正常”更有排除力：

- `mtf01p_reader.v:113–154` 中，完整提交的 ToF 状态非1、距离小于10或大于12000mm、flow状态非1、quality=0、距离低于80mm、时间/序号不连续，都会使该帧或随后一帧无法积分，增加 integration_breaks 或相应累计计数。当前200ms区间内这些计数都不变，因此不能再把“可能夹了一份这种完整坏帧”与其他候选等量并列。计数32位无重启，20份帧内也不存在回绕解释。
- geometry 只对成功计算发布 update；`navigation_sequence` 只在该 update 时增加（`mtf_xyz_navigation_control.v:328–329`）。孤立完整的 `5000 < distance <= 12000` 帧虽然可通过 reader，却会被 geometry 拒绝并少一次发布。历史 offset 在 seq227（age1ms）、232（age9ms）、374/375（age9ms）均为270。正常同步 FSM 的 compute watchdog 是10000拍=200µs，这些 anchor 超出待发布相位；因此**孤立的一份 >5m 帧作为唯一首因，不符合这组累计发布计数**。此项依赖当前同步 RTL 及同组快照契约，不是对任意硬件毛刺或复合故障的形式证明。
- 仍缺少逐帧交付时间，不能以缺帧计数0否定一次缓冲后补发的交付停顿。导航对 source_age 的门槛是100ms，reader 的 link_fresh 门槛是200ms；后者不失效，不保证前者没短时失效。

## 3. 它发生在主动下降阶段，但低油门不是高度失效条件

第一次 CH3 在 seq227 已降至1374，随后1223、1141；seq231为1089。第二次在372为1322、373为1120、374为1000；seq375主帧缺失，不填补它的CH3。两段可见测距均在向低处收敛；不是一段已证明“持续中杆悬停、未经下降指令即失去高度”的记录。

但正常下降本身也不能解释 `height_available=0`：

- `core/ano_flight_state.v:14–44` 的低油门只在落地判据满足一段时间后清 taking_off/设置 land_lock；并不直接使测高输入失效。
- `height_loss_fallback.v:24` 的 enter 条件是 `armed && taking_off && seen && !height_available`，没有 CH3 低位条件。
- 第一次首个降级时 taking_off、flying、armed、controller 均仍真，gate event_sequence 未增长。更晚 seq241 的 gate0x32/无原始 sensor mask 是另一个事件，不能倒填为首次高度原因。第二次更晚 seq379 的 CH5低和 gate0x34 也晚于 seq375。

第二次 seq374 有可见 `world_az_up_mmps2=16348`；第一次 seq232 为15201。这使下降/接触阶段的加速度瞬态值得优先诊断，但这些可见数值均未超过30000，第一次较大的正向样本还晚于首个降级快照。**不能把隐藏的 ±3g 越界、触地或传感器冲击写成已观测事实。**

## 4. 真实高度可用性链与已有诊断盲区

顶层 `acg720_ano_port.v:76–79,300–310` 实际送入 core 的是：

```text
core_vertical_available = nav_core_height_state_tail
                        && mtf_range_ok && mtf_age_ms < 100
                        && accel_valid && converted_acc_valid && time_adapter_fault == 0
                        && body_tilt4500_ok && body_yaw_range_ok
```

`mtf_xyz_navigation_control.v:137–156` 的 state tail 内含高度 qualified_ready、geometry 的状态/数值 tail、height fusion 的状态/数值 tail、启动/origin资格。geometry 距离上限5000mm；height fusion 还要求当前 `az_up_mmps2` 在±30000、发布年龄小于100ms、seeded/seen、cleanup=0及fault=0（`mtf_shared_height_fusion.v:87–107`）。

触发后，`height_loss_fallback.v:60–78` 把 last_good 油门作为回退锚点并锁存；`flight_core.v:372` 因 latched fallback 撤销 navigation_enabled。`mtf_xyz_navigation_control.v:314,325` 的 reason2 优先表示 enabled=0，是降级后的下游状态，不是源传感器首因。门禁通过 `vertical_available || fallback_takeover_ready` 保持已解锁控制，所以首次高度降级不必产生 gate revoke 事件；现有 A585 first-protection 也没有专门捕获它。

正常 publication 并不主动拉低有效性：pose_time_adapter 的 start/busy 分支保留 output_acc_valid；geometry 发布期间保留 seen；height fusion 的 seen/qualified_ready 在正常更新中继续保持。所审源码未发现“每次回调必短低”的机制。

geometry 数学/overlap fault 与 height fusion 的 queue/math fault 均有保持行为，要等 source invalid/origin/reset 才恢复。故“输入始终健康、仅一次孤立内部 fault、随后自动恢复 ready”不是这份 FSM 的完整机制。历史若真有内部 fault，还需要额外解释它随后如何得到恢复条件。现有计数也不支持旧 B0B0 那种持续 IMU 拒收；这不等于排除了所有未采到的加速度或交付瞬态。

## 5. 三种真实 RTL 构造测试，全部通过

权威回执为 **`rtl_attempt_03/rtl_results.json`**，不是根目录的早期失败回执。`height_path_tb.v` 实例化冻结的完整 mtf_xyz_navigation_control、真实四客户端 nav_math_service、metric observer、pose_time_adapter 及 height_loss_fallback。50MHz、1ms pose到达、10ms MTF到达、实际1000µs/10ms算法dt；每场景4,000,000拍=80ms，共12,000,000拍。没有 force 私有状态或最终安全输出。前40ms CH3=1500，后40ms为1000。

假定 core 已健康、armed/taking_off；这不是 arming/PWM、实测线字节、飞行器动力学或历史高频输入重放。MTF source_age 固定0，因此不验证交付停顿候选。

| 场景 | 实际构造输入 | 实际结果 |
|---|---|---|
| 0 正常回调/低杆 | 全部源有效，距离250，az0 | 首次ready12.05666ms；之后0次高度撤销、0次adapter有效性撤销，40ms低杆不锁存fallback，Z reason0 |
| 1 加速度资格失败 | 只把一份1ms pose tuple的az改为30001，valid仍真 | 50.00064ms高度ready下降；62.04774ms恢复，下降12.04710ms；80ms末fallback仍锁存、Z reason2 |
| 2 reader许可、geometry拒绝 | 一份10ms MTF tuple距离5001，ToF/flow状态1、quality100 | 51ms高度ready下降；72.05666ms恢复，下降21.05666ms；80ms末fallback仍锁存、Z reason2 |

三场景均真实完成 Z 活动并建立 last-good 油门；adapter fault/drop均0；metric integration_breaks都保持1。逐拍检查复原的 core 高度 cofactor 与 public height_ready 相等。场景2说明仅盯 reader 的 integration_breaks 不够，但历史 geometry 发布计数对这类孤立坏帧又提供了额外限制。

场景0是有限的正常调用排除；场景1/2是**机制见证**，不是历史首因认定，也不表示应删除该保护。初次编译因本机默认TMP不可用失败；第二次漏了源码 include 路径，calibration.vh未找到而停止解析。两份失败日志保留，第三次仅修正独立驱动的TMP和include配置，产品源码未改；不得把它们称作产品缺陷或有效仿真失败。

## 6. 最小缺失证据及可实现的首次原因锁存

不能从现有5Hz快照唯一决定最先下降的是100ms freshness、加速度数值门、内部状态/发布年龄还是其他cofactor。最小缺口不是更多相邻正常快照，而是**实际 fallback 锁存那个边沿的原始原因位**。

建议后续独立诊断候选（本次不实现、不烧录）：

1. 在 `height_loss_fallback` 的真正锁存边沿产生只供诊断使用的 enter pulse：`rst_n && healthy && armed && !latched && taking_off && seen && !height_available`。不能等A580采样、不能用 reason2反推，也不能取保护清理之后的值。
2. 顶层同边沿锁存 cause mask：range_valid、age<100、native_acc_valid的3个组成项、height_origin_ok、tilt45、yaw range，以及 nav 的 geometry/fusion/qualified 三个tail。nav另导出原始分项位：geometry距离范围/fault/overlap/seen/发布年龄；fusion当前az范围/cleanup/seeded/seen/发布年龄/fault/new_acc_fault/new_height_fault。保留重叠原因，不用单一优先级覆盖。
3. 同时保存 event_tick、事件计数、distance_mm、source_age_ms、原始az_up_mmps2、acc_dt_us、geometry reason和height-fusion reason/state。至少要有距离上限位、az上限位、age上限位、内部fault位，才能把本次剩余候选分开；数值保留32位，避免异常值在诊断前被窄化或夹紧。
4. 一个 last-event 记录即可跨源恢复和停机保留，只有下一次真实entry才覆盖并递增计数；不要在disarm或ready恢复时抹掉。把记录接入单一UART的独立版本化诊断包（例如新A58A），随普通组序号/CRC发布。不要挤占或改释A591参数ACK，也不要覆盖现有IMU first-protection记录。接收器明确识别新版本；未知版本继续拒绝。
5. 这些寄存器不反馈保护或控制。新增包长、触发扇出、物理资源与时序必须单独审查/仿真/布线；当前链路已有未定位丢响应，不能仅凭波特率预算宣称无线带宽已验收。也不建议去掉ready的即时门、延长失效阈值或用false path回避问题。

当前可以结束在这个精确缺口：**高度降级链本身已确认；正常调用和低油门未复现虚假撤销；短暂源资格失败足以解释现象，但历史最初失效的那几位未被记录。** 本次没有确定一个可据此修改已烧录产品的唯一软件根因。
