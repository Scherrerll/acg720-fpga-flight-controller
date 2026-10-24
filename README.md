<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/branding/gm-fly-dark.svg">
    <img src="assets/branding/gm-fly.svg" alt="GM-FLY 项目标志" width="180">
  </picture>
</p>

# GM-FLY · ACG720 FPGA 四旋翼飞控开发与验证

面向嵌赛高云赛道的 ACG720 / Gowin GW5AT-60K 四旋翼飞控工程，重点展示 FPGA 并行传感器接口、定点 RTL 姿态与飞行控制、资源与时序收敛，以及可追溯的验证流程。系统接入 BMI088、MTF-01P 光流/测距和 SiK 无线遥测，配套本地网页与日志分析工具。

本仓库于 **2026-10-22** 整理为私有归档。提交从 **9月架构/选型讨论、10月初选定ACG720与接线** 开始，再按开发阶段排列。提交日期是整理当天；阶段日期来自会话与验证记录，没有伪造历史 Git 时间。早期目录是当前工作区的阶段导出，不能全部视为历史当天精确快照。

## 当前选用版本（2026-10-24 更新）

| 用途 | 版本与入口 | 已有证据 | 尚未完成 |
|---|---|---|---|
| 当前默认 Flash | [B0B0](firmware/B0B0/README.md) · [源码工程](firmware/B0B0/source_snapshot/acg720_ano_port.gprj) | 零未通、51.608 MHz；拆桨正常/失效接管与纠偏；Flash 独立校验、仅电池冷启动 | 带桨负载、空中稳定性及光流旋转分量严格资格 |
| 历史默认 / 回退 | [B0AC](history/12-b0ac/) · [精确回退文件](firmware/B0B0/release/rollback_B0AC.fs) | 保留先前验收与回退哈希 | 不代替 B0B0 当前验收 |
| 历史算法候选 | [B0AE](firmware/B0AE/README.md) | 10-22 离线回归及 50.505 MHz 结果保留 | 已由 B0B0 取代当前候选位置 |
| 当前只读接收端 | [ground/B0B0](ground/B0B0/README.md) | B0B0 分帧解码、只读接收、自动日志；提供便携导入适配 | 无电池电压、电流和 ESC 转速实测 |
| 分享网站 | [gmflylog.com](https://gmflylog.com/) · [源码](web/flight-console/README.md) | 恢复 B0B0 实时转发；保留原选定日志分享与慢网络恢复 | 需要电脑端 8765 接收和 8766 显式实时分享持续运行 |

新增工作见 [10-23～24 工作记录](docs/WORK_20261023_24.md) 与 [全部归档哈希索引](docs/WORK_ARCHIVE_20261023_24.json)。Git 提交使用真实上传时间；没有伪造昨天的提交日期。

**B0B0 仍为 `flight_ready=false`：拆桨、固化和冷启动通过不等于完成带桨飞行验收。** 此前掉动力由操作者确认为电池松动；最低油门后落地锁定按操作者确认保留。当前程序默认 Flash 已从 B0AC 更新为 B0B0，见冷启动实物记录。

## 目录

- [history](history/README.md)：00a选型、00b初始接线，接01–13阶段源码与验证摘要；[完整时间线](docs/TIMELINE.md)。
- [mechanical](mechanical/README.md)：SolidWorks总装/零件、STEP、打印件与加工件资料，保留原相对目录。
- [hardware](hardware/README.md)：材料购买文档原件《材料汇总.docx》。
- [firmware/B0B0](firmware/B0B0/README.md)：当前源快照、物理约束、网表、精确位流、回退和证明；B0AE 原始归档保留。
- [ground](ground/README.md)、`support/`：便携的 Python 只读接收网页与必要解码器。
- [web/flight-console](web/flight-console/README.md)：GM-FLY 分享前端、本地转发、EdgeOne 云函数与存储适配，以及部署和验收记录。
- [tools](docs/BUILD_AND_VERIFY.md)：导出完整性校验、可配置工具路径的离线构建和选择性 RTL 回放。
- [接线与单位](docs/HARDWARE.md)、[控制边界与待验收项](docs/STATUS.md)、[第三方来源](THIRD_PARTY_NOTICES.md)。

## 快速核查

Python 3.10+：

```sh
python tools/verify_export.py
python tools/verify_recent_export.py
python tools/build_firmware.py
python -m pip install -r ground/requirements.txt
python -B -m unittest discover -s ground/B0B0 -p "test_*.py" -v
```

上述命令不启动串口接收、不编译 Gowin、不下载硬件。实际离线构建需显式加 `--execute`，见[构建说明](docs/BUILD_AND_VERIFY.md)。

网页离线查看：

```sh
python -B ground/B0B0/launch.py --no-serial --logs ground/runtime --http-port 8765
```

然后打开 `http://127.0.0.1:8765/`。无线接收需显式指定电脑端 SiK 的实际串口：

```sh
python -B ground/B0B0/launch.py --port COM17 --baud 115200 --source SiK --logs ground/runtime --http-port 8765
```

`COM17` 只是原机器示例。正在运行的旧网站占用 8765 时，请给新实例选其他端口，不要同时抢占同一串口。

原始完整飞行日志、工具二进制、`impl/` 大型数据库、单独的用户照片、无关作业、完整厂商资料包和失败变体的大型中间产物没有上传。当前精确 B0B0 与 B0AC 回退位流作为明确例外保存在 firmware/B0B0/release，失败试验的有界源码/报告按来源保留。材料Word文档按用户要求原样保存，保留其内嵌内容。保留的验证文字可能含原机器绝对路径，仅用于来源追溯；原始完整资格检查仍有原工作区依赖，不能据此宣称在任意机器上一键重放了所有历史测试。

仓库暂不授予统一的 MIT/GPL 等许可证。第三方版权与许可各自保留；特别是匿名参考源码的公开再分发条件仍需核清，见[第三方说明](THIRD_PARTY_NOTICES.md)。
