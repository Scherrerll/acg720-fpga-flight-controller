# B0B4 49 MHz 后备方案：独立会话需求与交接

用户于 2026-10-27 明确要求：“降频这个你开一个新会话去做吧，你就全力做50MHZ的，记得开之前把需求说好”。本文件在创建新会话前写好。主会话 `01a17788-4242-79e0-9a84-aa5021c9aad4` 只攻真实 50 MHz；新会话独立完成真实 49 MHz 后备方案。请持续实现、验证、修复，直至交付合格的离线候选固件和可复查证据，不要只写方案或在一次失败后结束。

## 工作边界与交付

- 新会话唯一写入根目录：`C:/Users/ScherrerL/Desktop/apple/runtime_b0b4_49mhz_20261027`。先读取本目录 `HANDOFF.md` 和 `input_snapshot/MANIFEST.json`；核对全部 58 文件后复制到自己的工作源目录，输入快照保持不变。后续代码、工具、证明、构建、文档、固件包都放在此独立目录。
- 原仓库 `C:/Users/ScherrerL/Desktop/apple/github_publish/acg720-fpga-flight-controller` 以及其旧证据、out、firmware/B0B4、ground/B0B4 均为新会话只读参考。主会话可能提升正式 B4 源，勿依赖其未来可变状态，立即冻结必要参考与测试输入。不要修改共享 Git/index、提交、推送或修改主会话状态文件。
- 不打开/控制串口、烧录器、下载器、GUI，不终止任何共享/主会话进程；不发 live SET，不增加参数 NVS。硬件和正式发布由主会话统一管理，离线包完成后等待用户选择版本。硬件验收须在合格具体包之后另取当前人类确认：拆桨、CH3/CH5/CH7 低、目标下载器正确；随后 SRAM/身份/GET/新鲜 IMU、Flash 验证、真实全断电冷启动。鼓励和“继续”不能代替物理状态确认。
- 新会话最多同时占用一个 Gowin 物理实现任务，主会话保留另一槽；综合和仿真可按资源安排。进程都捕获真实 PID/父 PID/命令/启动时间/退出码，只管理自己创建的进程。原老 R 任务 PID41448、B3 地面站 PID49948/COM17 均勿碰。
- 交付：明确完整源集合与 SHA256、频率/时间基准审计、仿真及真实退出凭据、综合时钟域检查、全布线 STA 和引脚/身份检查、可重复构建说明、合格 FS/报告/离线安装说明。生成自己目录下 `PROGRESS.json`、`HANDOFF_RESULT.md` 供主会话只读查看。不要声称已烧录、已冷启动或能飞。不要自动向其他会话发送消息。
- 不读取、哈希、打印、复制或上传任何 `.env`、`.env.*`、`deployment.env` 或其他凭据；B3/B2 冻结源码、原始六份交接文件、其他无关文件保持原样。所有新构建/脚本路径明确指向独立工作目录，不直接运行会写共享 out 的旧脚本。

## 产品行为要求

这是现有 B0B4 的降频后备版本，板输入仍 50 MHz，功能数据通路实际 49 MHz。修复 Z 在最终 collective=1850 饱和时继续正向积分的问题；未饱和 P2 方程、定点精度、保护/撤销/停桨/着陆行为保持。沿用 v4 已验证反积分实现的额外两拍，不凭空添加公开控制延迟。XY 共享启动默认 P=0.1000、I=0.0350（wire1000/350），generation0；SET 仍易失，不添加持久化。低空前飞掉高不在此次范围。

不得仅把 SDC 放宽后仍用 50 MHz，不得拿旧 49.456 MHz 的 50 MHz 失败结果当作 49 MHz 成功。不得放松控制路径 false path、相位、时钟延迟或验收门槛来掩盖问题。降频必须完整核对时基，不能盲替换数字 50/50000。

## 已有输入与证据（均在原仓库相对路径下）

`input_snapshot/source58` 是从 `out/z_aw_fix_20261026/clock49_working/source` 逐文件验 SHA 复制的未完成版本：v4 的 55 文件加 3 个原厂时钟 RTL。**顶层、gprj 和真实功能时钟仍是 50 MHz，PLL 尚未接入，不能整机编译后当成 49 MHz。** 已改的叶模块仅是 pose_time_adapter 参数化、TX 分频参数化、telemetry TX 参数传递；默认 50 MHz 等价已测。`xy_pi_parameters.v` RX 已恢复原版字节，失败的半位 ceil 修改不能带入。

关键目录均为 `analysis/20261026_z_aw_fix/build/` 下：

1. `clock49_generate/vendor_generated_reference/{clock49.v,clock49_mod.v,pll_init.v,clock49.ipc}`、`REFERENCE_IP_MANIFEST.json`：Gowin 官方 clock_plladv 为 GW5AT-LV60PG484AC1/I0 B 生成，PLLA FCLKIN=50，IDIV=2、MDIV=49、ODIV0=25、FBDIV=1，49 MHz 整数比，零相移、无 SSC，PLL_INIT 的 mdclk=50 MHz。原厂生成真实退出 0，未手调参数。
2. `clock49_generate/simulation/RESULT.json`：原厂 PLL/INIT 未修改模型自然输入，未 force/预载/绕过初始化；LOCK 稳定，49000 周期历时999992ns（模型量化约8ppm），compile/vvp 实际0。仅为 IP 单测。
3. `clock49_time_adapter/{SOURCE_BINDING.json,proofs/RESULT.json}`：原版/参数化默认50MHz 公共139位和内部除法状态逐拍等价；49 除数独立64位算术参考，12000事务、57取消、47忙重入、409173周期，实际0。
4. `clock49_pwm/proofs/RESULT.json`：真实 motor_pwm 50/49 参数，物理时宽1000/1200/1500/1850/2000us、400Hz/2500us帧，8路、停桨/重启边界，实际0。**核心 wiring 仍乘50、安全比较50000，必须改为49/49000并整机复验。**
5. `clock49_uart/proofs_retry03/RESULT.json`、`RX_EVEN_DIVISOR_REVIEW.json`、`RETRY03_DERIVATION.json`：TX425、RX426，RX 原始 FSM 不变，全部256字节 TX 默认50逐拍等价/49环回、独立115200主机256好帧+16坏停止位+假起始位，保留严格计数及3bit短空闲，真实 compile/vvp0。TX波特约115294(+0.082%)，RX采样约115023(-0.153%)。建议 RX 最近偶数公式 `2*floor((CLOCK_HZ+BAUD)/(2*BAUD))`，50时434、49时426。TX最近整数49时425。
6. UART `proofs/` TX425/RX425 曾因坏停止位后假起始失败；`proofs_retry02/` 半位 ceil 也失败，`failed_halfbit_candidate.v` 已保留且回退。**不能恢复失败改动、延长空闲或删断言来宣称成功。** 原版RX+426才是当前通过的方案。MTF/range 等其他 RX 仍须审查。
7. `clock49_generate/IMPLEMENTATION_REVIEW_PENDING.json`、`TIMEBASE_INVENTORY_PENDING.json` 是未完成审查笔记/92个字面命中，不是完整维度审计或确定替换表。
8. v4 既有功能依据 `v4_release_proofs/RESULT.json`，v9 六依赖/反积分五组/FRAC/争用证明可按精确源依赖审查复用；原地面43输入未变凭据只适用于50MHz，49改动后须新测。原顶层13场景见 `v4_release_proofs/run_top13.py`，测试不能删保护断言。

## 必须完成的实现与证明

接入上述原厂 PLL、MOD、INIT，功能模块使用同一个真实49MHz数据时钟，初始化专用50MHz是明确允许的独立域。检查 LOCK/复位同步、失锁与启动期物理输出抑制，防止短脉冲/提前出桨；必要的 CDC 例外只能精确落到首级复位同步边界并有证明，不能屏蔽原功能路径。

逐项建立“单位/旧值/新值/理由/验证”的时间基准清单：RC/PWM和原始安全ticks、UART分频/25ms超时(1.225M)、SPI/IMU启动和采样周期、ms计数/年龄/看门狗、估计器 alpha、rate/control tick dt/导数分母、pose ticks转us/余数进位、height fusion存储位宽/age参数、各模块 `CLK_HZ==50M` 断言、B4地面原始ticks到us/ms换算。微秒域常量如50000us不能改成49000us。必要最小SPI保护延时可保留稍长并记录，实际约0.98MHz SPI也须确认安全。实现只做达成同物理行为所需修改。

新项目显式列全实际源（当前58，若加头文件可更多）并冻结哈希。重新跑49MHz集成行为/时基/保护/复位/反积分/默认值/CRC协议测试，默认50参数应维持原行为的模块用对照证明。原仿真固定传感器时间不构成飞行着陆等待建议。

综合审计必须认识 input50MHz/20ns 与功能49MHz/20.408163ns 的真实关系，检查功能 FF 的唯一49MHz根与专用原厂初始化50MHz FF白名单、PLLA配置、B4身份、XY默认、radio_rx首同步、18引脚（RX B16/TX B15）。原50MHz-only审计/55文件断言不能直接用于新时钟结构，也不能简单删掉。

真实完整物理实现必须：vendor与父 runner 的实际 p.wait均0、完整EOF、全布线、生成FS、input/init50MHz与功能49MHz各自达标、五类setup/hold/recovery/removal/MPW slack非负、setup和hold违规端点0、18针全部一致、FS/cfg/UserCode=0x0000B0B4。从原始报告独立复核并绑定源/VG/工具/参数/退出凭据。保留失败，不拼凑旧成功。离线包能从冻结输入复建，验证后再通知用户结果。

## 工具与主会话状态参考

- Gowin `C:/Gowin/Gowin_V1.9.12.04_x64/IDE/bin/gw_sh.exe` SHA256 `585c12968550a960d1021287742672ff9d6bbeaee5623f6811dfc1f907a4af41`。
- Python `C:/Users/ScherrerL/AppData/Local/Programs/Python/Python313/python.exe`，使用 `-B -X utf8`，文本显式 encoding=utf8。
- Iverilog `C:/Users/ScherrerL/Desktop/apple/.tools/iverilog/app/bin`。
- 原厂文档本地 `C:/Gowin/Gowin_V1.9.12.04_x64/IDE/doc/EN/`，UG306-1.0.9E Arora V Clock User Guide 的 PLLA/GW5AT60 与 PLL_INIT 条目。只读原厂手册及官方源，不解密 `.p/.pr`。
- 主会话50MHz最好完整布线 v4 为49.456MHz/setup−0.220ns/32setup端点/0hold，故尚未合格；v14扇出提示 P3失败480unrouted，P2失败778unrouted，均实际vendor/root1。主会话继续寻找真实50MHz方案；这些均不是49交付。
- 原共享 `firmware/B0B4/build_candidate.py`、旧读网表/增益审计器和原始交接不可改。可以在独立目录复制并明确派生新的49版本和门槛，不能把原50专用证明改成49成功。
