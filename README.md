<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/branding/gm-fly-dark.svg">
    <img src="assets/branding/gm-fly.svg" alt="GM-FLY 项目标志" width="180">
  </picture>
</p>

# GM-FLY · ACG720 FPGA 四旋翼飞控开发与验证

面向嵌赛高云赛道的 ACG720 / Gowin GW5AT-60K 四旋翼飞控工程，重点展示 FPGA 并行传感器接口、定点 RTL 姿态与飞行控制、资源与时序收敛，以及可追溯的验证流程。系统接入 BMI088、MTF-01P 光流/测距和 SiK 无线遥测，配套本地网页与日志分析工具。

本仓库于 **2026-10-22** 整理为私有归档。提交从 **9月架构/选型讨论、10月初选定ACG720与接线** 开始，再按开发阶段排列。提交日期是整理当天；阶段日期来自会话与验证记录，没有伪造历史 Git 时间。早期目录是当前工作区的阶段导出，不能全部视为历史当天精确快照。

## 版本入口（2026-10-29 更新）

| 用途 | 版本与入口 | 已有证据 | 尚未完成 |
|---|---|---|---|
| 本次水面推进版本 | [B0B5 V8：使用与测试记录](firmware/B0B5/README.md) · [源码工程](analysis/20261028_water_drive/qualified_offline_B0B5/source/acg720_ano_port.gprj) | A13/A14双路50Hz PWM；13项离线检查、真实20ns五类STA通过，Fmax50.032MHz；10-29用户反馈测试正常 | 未提供独立镜像读回、Flash持久性、冷启动及逐项保护实测证据；不继承飞行验收 |
| 原飞行版本 | [B0B4 高度抗积分饱和](firmware/B0B4/README.md) | 原源码、位流及既有安装/验证记录保留 | 本次水面测试不扩展原飞行资格 |
| 历史离线候选 | [B0B3 在线 P/I](firmware/B0B3/README.md) · [源码工程](firmware/B0B3/source/acg720_ano_port.gprj) | 完整布线；真实20ns五类STA通过，Fmax50.257MHz；停机原子参数、CLI及回归 | 当时尚未安装；实机参数通信及飞行动态未验收 |
| 历史 Flash 记录 | P005/I0（B0B2）· [当次回执](validation/20261025_p005_i0/README.md) | 10-25独立Flash校验、冷启动；默认P=.05/I=0 | 旧19.5ns setup未通过，当时20ns是分析性结论；回中刹停/悬停未验收 |
| 历史原 V15 | [B0B2](firmware/B0B2/README.md) | 原V15 51.400MHz、19.5ns通过及当次上板/Flash记录保留 | 已与后续P005/I0及B0B3分开记录，不继承飞行资格 |
| 历史默认 / 回退 | [B0B0](firmware/B0B0/README.md)、[B0AC](history/12-b0ac/) | 原拆桨、Flash及冷启动证据保留 | 不代表当前记录的机载镜像或新版本验收 |
| 历史算法候选 | [B0AE](firmware/B0AE/README.md) | 10-22 离线回归及 50.505 MHz 结果保留 | 已由 B0B0 取代当前候选位置 |
| 当前只读接收端 | [ground/B0B0](ground/B0B0/README.md) | B0B0 分帧解码、只读接收、自动日志；提供便携导入适配 | 无电池电压、电流和 ESC 转速实测 |
| 分享网站 | [gmflylog.com](https://gmflylog.com/) · [源码](web/flight-console/README.md) | 恢复 B0B0 实时转发；保留原选定日志分享与慢网络恢复 | 需要电脑端 8765 接收和 8766 显式实时分享持续运行 |

最新水面推进版本及10-29用户测试反馈见 [B0B5](firmware/B0B5/README.md)，精确源码、位流和离线证据见[原始审查包](analysis/20261028_water_drive/qualified_offline_B0B5/README.md)。此前工作见 [10-25～26 工作记录](docs/WORK_20261025_26.md) 与 [归档索引](docs/WORK_ARCHIVE_20261025_26.json)；前一阶段见 [10-23～24 工作记录](docs/WORK_20261023_24.md)。Git 提交使用真实上传时间，不回填历史日期。

**B0B5 已收到用户测试正常的反馈，具体范围见版本记录。** 原审查包中的“禁止安装”、`installed=false`和`hardware_qualified=false`描述打包时的离线状态，按原字节保留；后续用户反馈单独记录，不改写原证据。水面测试不证明回中刹停、持续悬停或完整飞行资格。

## 目录

- [history](history/README.md)：00a选型、00b初始接线，接01–13阶段源码与验证摘要；[完整时间线](docs/TIMELINE.md)。
- [mechanical](mechanical/README.md)：SolidWorks总装/零件、STEP、打印件与加工件资料，保留原相对目录。
- [hardware](hardware/README.md)：材料购买文档原件《材料汇总.docx》。
- [firmware/B0B5](firmware/B0B5/README.md)：水面双推进的源码/位流入口、功能说明和用户测试反馈；[B0B4](firmware/B0B4/README.md)及更早版本保留。
- [ground](ground/README.md)、`support/`：便携的 Python 只读接收网页与必要解码器。
- [web/flight-console](web/flight-console/README.md)：GM-FLY 分享前端、本地转发、EdgeOne 云函数与存储适配，以及部署和验收记录。
- [tools](docs/BUILD_AND_VERIFY.md)：导出完整性校验、可配置工具路径的离线构建和选择性 RTL 回放。
- [接线与单位](docs/HARDWARE.md)、[控制边界与待验收项](docs/STATUS.md)、[第三方来源](THIRD_PARTY_NOTICES.md)。

## 快速核查

Python 3.10+：

```sh
python -B tools/verify_progress_20261025_26.py
python -B firmware/B0B3/verify_export.py
python -B analysis/20261028_water_drive/qualified_offline_B0B5/verify_review.py analysis/20261028_water_drive/qualified_offline_B0B5
python -m pip install -r ground/requirements.txt
python -B -m unittest discover -s ground/B0B0 -p "test_*.py" -v
```

上述核验不启动串口接收、不编译 Gowin、不下载硬件。历史导出工具和旧阶段完整包可能依赖未上传的大型原始证据，适用范围见本次清单及各阶段说明。B0B3构建/验证入口见其README；旧构建说明保留在[构建说明](docs/BUILD_AND_VERIFY.md)。

网页离线查看：

```sh
python -B ground/B0B0/launch.py --no-serial --logs ground/runtime --http-port 8765
```

然后打开 `http://127.0.0.1:8765/`。无线接收需显式指定电脑端 SiK 的实际串口：

```sh
python -B ground/B0B0/launch.py --port COM17 --baud 115200 --source SiK --logs ground/runtime --http-port 8765
```

`COM17` 只是原机器示例。正在运行的旧网站占用 8765 时，请给新实例选其他端口，不要同时抢占同一串口。

原始完整飞行日志、录像、工具二进制、`impl/` 大型数据库、单独的用户照片、无关作业、完整厂商资料包和失败变体的大型中间产物没有上传。选中B0B5、B0B3及两份回退位流、原V15选中位流按明确例外保存；有界源码/报告和省略文件的哈希按来源保留。材料Word文档保持原样。验证文字可能含原机器路径，用于私有归档追溯；未声称任意机器可直接重跑全部历史资格检查。

仓库暂不授予统一的 MIT/GPL 等许可证。第三方版权与许可各自保留；特别是匿名参考源码的公开再分发条件仍需核清，见[第三方说明](THIRD_PARTY_NOTICES.md)。
