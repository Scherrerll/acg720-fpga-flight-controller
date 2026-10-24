# 开发阶段与来源

按证据中的时间和功能演进排序。表内日期为北京时间（Asia/Shanghai）；Git 提交使用实际归档时间。早期源码可能已经含后续修订，因此不冒充当日精确快照。所有历史通过状态只覆盖当时记录的条件。

| 顺序 | 日期 | 阶段 | 来源/结果 |
|---|---|---|---|
| 00a | 09-18～10-01 | 架构取舍与硬件选型 | [00a-selection](../history/00a-selection/)，由候选架构到明确选ACG720；规划不冒充实现 |
| 00b | 10-01～04 | 初始接线、接收机与PPM决策 | [00b-initial-wiring](../history/00b-initial-wiring/)，旧IMU/管脚建议后有修正 |
| 01 | 最迟 10-09 | 板卡 LED、PPM | [01-bringup](../history/01-bringup/)，Smoke 本身无明确日期 |
| 02 | 10-10～11 | ICM IMU、姿态保护 | [02-imu-attitude](../history/02-imu-attitude/)，含后续异常/恢复记录 |
| 03 | 10-11 | 虚拟控制、拆桨电机 | [03-control-motor](../history/03-control-motor/) |
| 04 | 10-12～13 | 综合监控与FPGA控制算法工程化 | [04-monitor-ano](../history/04-monitor-ano/) |
| 05 | 10-14～16 | BMI088 迁移/B088 停机回退 | [05-bmi088](../history/05-bmi088/)，不混称 B089 |
| 06 | 10-16 | B089 厘米测距、自稳台架 | [06-b089](../history/06-b089/)，55.171 MHz |
| 07 | 10-17 | B09E ATK/PixArt 诊断 | [07-b09e](../history/07-b09e/)，51.313 MHz，SRAM 诊断，比例/转动未验收 |
| 08 | 10-18 | B0A0 SiK 数传候选 | [08-b0a0](../history/08-b0a0/)，51.436 MHz |
| 09 | 10-18 | B0A6 无线日志与冷启动 | [09-b0a6](../history/09-b0a6/)，59.799 MHz；允许标记缺口的辅助地面日志 |
| 10 | 10-18 | MTF 独立 Micolink 工具 | [10-mtf-eval](../history/10-mtf-eval/)，自测不等于实物验收 |
| 11 | 10-19 | B0AB 完整控制 | [11-b0ab](../history/11-b0ab/)，选 publication_yaw_study，50.001 MHz |
| 12 | 10-19～20 | B0AC FSM/硬件默认版 | [12-b0ac](../history/12-b0ac/)，50.191 MHz，10-20 已有 Flash/冷启动记录 |
| 13 | 10-20～21 | B0AD 本地取消/接管候选 | [13-b0ad](../history/13-b0ad/)，50.067 MHz，历史 SRAM 验证，Flash 保留 B0AC |
| 14 | 10-22 03:36 | B0AE 按参考源码对齐控制流程 | [最新候选](../firmware/B0AE/)，50.505 MHz，仅离线通过 |
| 15 | 10-22 | GitHub 整理与便携接收端 | [ground](../ground/)，未操作原机监控或硬件 |
| 16 | 10-22 | 机械与材料资料归档 | [SolidWorks/加工模型](../mechanical/README.md)、[材料购买文档原件](../hardware/README.md)；这是归档日期，不倒推模型设计或采购日期 |
| 17 | 10-22 | GM-FLY 分享网站与国内访问迁移 | [前端/转发/EdgeOne 后端](../web/flight-console/README.md)，正式域名 HTTPS、国内无 VPN 实时数值、选定日志上传/读取/CSV 及 12000 样本完整性验证；未更改 FPGA |
| 18 | 10-23 | B0AF 测距失效接管与 B0B0 综合/布线排查 | [B0AF](../history/14-b0af-height-loss/)、[B0B0 阶段](../history/15-b0b0-routing-stages/)；保留证明和失败，不将失败试验视为当前默认 |
| 19 | 10-23～24 | 分享网站慢网络恢复、实时旁路恢复 | 前端延迟读数/退避测试，10-24 重启 8766 后公网收到当前 B0B0；新增显式分享启动器 |
| 20 | 10-24 | B0B0 物理收敛与拆桨实物验收 | [当前默认](../firmware/B0B0/README.md)：51.608 MHz、零未通，增量证明、接管/纠偏、Flash 与仅电池冷启动；未完成飞行验收 |

这是一条展示顺序，不代表所有阶段都直接继承上一阶段。例如 B0A0/B0A6 准备记录均声明以 B089 为基线，并非继承 B09E 的全部实验修改。

选型/接线摘要来源见各阶段的 `evidence_sources.json`，导出哈希见 `history/origins_manifest.json`；早期源码来源见 `history/early_manifest.json`；后期见 `history/late_manifest.json`；B0AE 见 `firmware/B0AE/source_export.json`。各阶段 README 写明实际选用入口。B089/B09E 原 `build.tcl` 中残留 B088 标识，历史实际入口为各自 `trial.tcl`，因此两份原脚本都保留并说明。

失败的毫米测距/资源压力、旧光流诊断和 B0AE 布线试验不被包装成正式可飞版本。历史位流及庞大原始日志保留在原工作区，未纳入 Git。
