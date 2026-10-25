# B0B2：IMU 输入与超时策略 v3 候选

2026-10-25 更新：V15 已零未布通、51.400MHz，原 19.5ns 下五类静态时序均通过；[已封存交付包](verified_timing_20261025/README.md)。该位流已完成 SRAM 上板和一分钟停机观察，未写 Flash；[上板记录及当前限制](hardware/v15_sram_20261025T091416_206712Z/README.md)。测距、光流尚无有效数据，未完成带动力或飞行验收。

当前源码已按用户确认范围删除 IMU/姿态的额外断流门控及姿态年龄链路，遥控有效帧超时改为 500ms、MTF 模块在线指示改为 1s。真实 dt、数值步长上限、独立控制请求/电机命令超时和控制数据 100ms / metric 200ms 新鲜度保留。完整范围、新帧标识和策略修改阶段的验证入口见 [POLICY_V3.md](POLICY_V3.md)。

本工程修复已由冻结旧版 RTL 复现的整帧拒收与恢复饥饿机制。旧日志的时间分辨率不足以证明它就是两次光流偏移的唯一原因。工程、回归测试通过、位流可安装和飞行验收是分别记录的状态；此文档不提供飞行放行结论。

v1/v2 的修改依据和历史对照见 [POLICY.md](POLICY.md) 与 [VALIDATION.md](VALIDATION.md)。不因合法运动差值拒绝完整六轴记录的修复继续保留；原有低通、重力纠正模长窗口、gyro 积分、启动校准、控制增益及落地锁保持。v3 的超时行为以新策略文档为准，历史证明不继承。

B0B0 冻结源码和回退位流保留，B0B1 被动诊断工程及失败布线证据保留。`baseline.json` 绑定 B0B0，`parent_snapshot.json` 绑定 B0B1 源码。所有构建在新目录中进行，禁止覆盖历史结果。

## 独立观测

SiK 保持 115200 baud。受年龄删除影响的帧采用 A586–A589 新头，A585 使用 v3；接收端把删除的年龄明确标为不可用，其他数据单位保持，完整组仍为 644 字节。飞行采样不依赖 USB。

当前 A585 **版本3** 保留拒收 source ID 和首保护时间，移除首保护姿态年龄并解析为 `None`。v1 完整源码和证据保留在 `evidence/source_revisions/copy99_v1/`；旧 v1/v2 协议说明属于历史格式。当前布局见 [POLICY_V3.md](POLICY_V3.md)。

本候选彻底移除新增 USB 921600 高频发送器和专用队列，不提供可选配置；监控 USB 仅复制 SiK 115200 遥测。内部诊断仅保留供低频汇总所需的状态，其余未使用字段由综合裁剪。完整高频诊断源码、测试及失败布线证据保留在 B0B1 历史工程。

## 离线流程

以下旧流程为 v1/v2 历史记录。当前 v3 请使用 [POLICY_V3.md](POLICY_V3.md) 中的入口。

从仓库根目录运行，临时产物位于忽略目录 `out/B0B2`：

```powershell
python -B firmware/B0B2/tests/run_policy_tests.py
python -B firmware/B0B2/tests/run_sik_tests.py
python -B firmware/B0B2/tests/run_temporal_contract.py
python -B -m unittest discover -s firmware/B0B2/tests -p test_analyze_bench.py
python -B firmware/B0B2/tools/build.py --output out/B0B2/NEW_BUILD --place 2 --route 2 --replicate 0
python -B firmware/B0B2/tools/verify_offline.py --build out/B0B2/NEW_BUILD
python -B firmware/B0B2/tools/install_sram.py --build out/B0B2/NEW_BUILD
```

最后一条默认只核验文件，不访问硬件。安装还需要当次人工确认及程序参数；不自动解锁、不写 Flash。构建必须通过原 17 引脚与电气约束、单一 19.5ns 时钟、完整布线、setup/hold 及其余 STA 类别，无放宽时序的例外。

如果完整构建已完成综合但布线失败，可在新目录复用这份已绑定网表进行受限物理试验：

```powershell
python -B firmware/B0B2/tools/build.py --output out/B0B2/NEW_PNR --pnr-only-from out/B0B2/FAILED_FULL --global-observer-reset --place 2 --route 2 --replicate 0
```

此流程保持逻辑源码不变，只派生 GPRJ、CST 和运行 Tcl。GPRJ 仅启用网表、CST、SDC，避免 `run pnr` 对 RTL 工程自动重新综合。复位全局网从当前网表的 boot/pose LUT 结构唯一确定，不接收调用者指定的网名。donor 输入、归档脚本、综合完成日志和复制网表均须吻合；最终还须从实际报告核对该网的全局资源分配。它不能继承 donor 的布线或时序结论。

B0B0 的胜出物理脚本使用 `place=2 / route=2 / replicate=0`；原始源码快照中的 `replicate=1` 是另一份默认设置。上例明确选用前者，但新网表仍须单独验收，不能因选项相同就认为可布通。

地面 SRAM 测试前重新确认拆桨、机架放稳、遥控低油门及 SWA/SWC 低档。静止、人工运动、拆桨动力及后续带载分别记录。若地面未复现，只记录“未复现”；不能据此写成实际振动问题或光流定点已经修复。
