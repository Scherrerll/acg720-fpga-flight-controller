# B0B2：IMU 动态样本接受策略修复候选

本工程修复已由冻结旧版 RTL 复现的整帧拒收与恢复饥饿机制。旧日志的时间分辨率不足以证明它就是两次光流偏移的唯一原因。工程、回归测试通过、位流可安装和飞行验收是分别记录的状态；此文档不提供飞行放行结论。

修改依据、边界及保留保护见 [POLICY.md](POLICY.md)，对照结果和未完成项见 [VALIDATION.md](VALIDATION.md)。核心改动限于 IMU 输入策略：读数通过原有身份、配置、传输及数值检查后，不再仅因相邻运动差值丢弃完整六轴记录。原有低通、重力纠正模长窗口、gyro 积分、校准、60ms 保护、控制增益及落地锁保持。

B0B0 冻结源码和回退位流保留，B0B1 被动诊断工程及失败布线证据保留。`baseline.json` 绑定 B0B0，`parent_snapshot.json` 绑定 B0B1 源码。所有构建在新目录中进行，禁止覆盖历史结果。

## 独立观测

SiK 保持 115200 baud，原 A579–A583 报文保持兼容。新增 A585 记录关键接收、姿态发布计数、拒收子码、最大姿态空窗和首个保护原因，飞行采样不依赖 USB。

本候选彻底移除新增 USB 921600 高频发送器和专用队列，不提供可选配置；监控 USB 仅复制 SiK 115200 遥测。内部诊断仅保留供低频汇总所需的状态，其余未使用字段由综合裁剪。完整高频诊断源码、测试及失败布线证据保留在 B0B1 历史工程。

## 离线流程

从仓库根目录运行，临时产物位于忽略目录 `out/B0B2`：

```powershell
python -B firmware/B0B2/tests/run_policy_tests.py
python -B firmware/B0B2/tests/run_sik_tests.py
python -B firmware/B0B2/tests/run_temporal_contract.py
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
