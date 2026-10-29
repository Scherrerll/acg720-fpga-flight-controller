<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/branding/gm-fly-dark.svg">
    <img src="assets/branding/gm-fly.svg" alt="GM-FLY 项目标志" width="180">
  </picture>
</p>

# GM-FLY：ACG720 FPGA 四旋翼飞控

这个项目是面向嵌赛高云赛道做的四旋翼飞控，主控使用 ACG720 开发板上的 Gowin GW5AT-60K。飞控通过 FPGA 接入 BMI088、MTF-01P 光流/测距模块和 SiK 数传，在 RTL 中完成姿态和飞行控制，另外写了接收网页和日志分析工具。

仓库在 2026 年 10 月 22 日开始整理。前面从 9 月的架构和选型讨论、10 月初的 ACG720 选型和接线开始，后面按开发阶段存放。Git 提交日期是实际整理上传的日期；各阶段日期来自会话和验证记录。早期目录是从当前工作区导出的阶段资料，不一定是当天的完整快照。

## 版本说明（更新于 2026-10-29）

目前最新的是 [B0B5 水面双推进版本](firmware/B0B5/README.md)，[源码工程在这里](analysis/20261028_water_drive/qualified_offline_B0B5/source/acg720_ano_port.gprj)。A13、A14 输出两路 50 Hz PWM，13 项离线检查和 20 ns 约束下的五类 STA 均通过，Fmax 为 50.032 MHz。10 月 29 日收到用户反馈，当前接线和测试条件下使用正常。具体测了哪些项目见版本记录，暂时没有独立镜像读回、Flash 持久性、冷启动和逐项保护实测证据。

原审查包是在离线阶段打包的，里面保留了“禁止安装”、`installed=false` 和 `hardware_qualified=false` 等当时的状态；后来的测试反馈单独写在 B0B5 记录里。水面测试结果不能用于证明回中刹停、持续悬停或完整飞行功能已经通过验收。[原始审查包](analysis/20261028_water_drive/qualified_offline_B0B5/README.md)中保留了对应源码、位流和离线证据。

其他版本和相关入口：

| 版本 | 已完成的工作 | 需要注意 |
|---|---|---|
| [B0B4 高度抗积分饱和](firmware/B0B4/README.md) | 保留原飞行版本的源码、位流和安装、验证记录 | 本次水面测试不扩展原飞行版本的验收范围 |
| [B0B3 在线 P/I](firmware/B0B3/README.md) · [源码工程](firmware/B0B3/source/acg720_ano_port.gprj) | 完成布线；20 ns 五类 STA 通过，Fmax 50.257 MHz；有停机原子参数、CLI 和回归记录 | 当时尚未安装，实机参数通信和飞行动态未验收 |
| P005/I0（B0B2）· [当次回执](validation/20261025_p005_i0/README.md) | 10 月 25 日完成独立 Flash 校验和冷启动，默认 P=0.05、I=0 | 旧 19.5 ns setup 未通过，当时的 20 ns 结果是分析性结论；回中刹停和悬停未验收 |
| [B0B2 原 V15](firmware/B0B2/README.md) | 保留原 V15 的 51.400 MHz、19.5 ns 通过结果和当次上板、Flash 记录 | 与后续 P005/I0、B0B3 分开记录，不继承飞行资格 |
| [B0B0](firmware/B0B0/README.md)、[B0AC](history/12-b0ac/) | 保留原拆桨、Flash 和冷启动证据 | 不能据此判断当前机载镜像或新版本验收情况 |
| [B0AE](firmware/B0AE/README.md) | 保留 10 月 22 日离线回归和 50.505 MHz 结果 | 后来由 B0B0 取代候选位置 |
| [ground/B0B0](ground/B0B0/README.md) | B0B0 分帧解码、只读接收和自动日志，提供便携导入适配 | 没有电池电压、电流和 ESC 转速实测 |
| [分享网站](https://gmflylog.com/) · [源码](web/flight-console/README.md) | 恢复 B0B0 实时转发，保留选定日志分享与慢网络恢复 | 实时分享需要电脑端的 8765 接收和 8766 显式实时分享持续运行 |

更早的工作可查看 [10 月 25～26 日记录](docs/WORK_20261025_26.md)、[归档索引](docs/WORK_ARCHIVE_20261025_26.json)和 [10 月 23～24 日记录](docs/WORK_20261023_24.md)。

## 仓库目录

- [history](history/README.md)：选型、初始接线及 01–13 阶段的源码和验证摘要，时间顺序见[时间线](docs/TIMELINE.md)。
- [mechanical](mechanical/README.md)：SolidWorks 总装和零件、STEP、打印件及加工件，保留原相对目录。
- [hardware](hardware/README.md)：材料购买文档原件《材料汇总.docx》。
- [firmware/B0B5](firmware/B0B5/README.md)：水面双推进的源码、位流入口和测试反馈；[B0B4](firmware/B0B4/README.md)及更早版本也在 firmware 中。
- [ground](ground/README.md)、`support/`：Python 只读接收网页和所需解码器。
- [web/flight-console](web/flight-console/README.md)：分享前端、本地转发、EdgeOne 云函数与存储适配，以及部署和验收记录。
- [构建与核查工具](docs/BUILD_AND_VERIFY.md)：导出完整性校验、离线构建和选择性 RTL 回放。
- 其他资料：[接线与单位](docs/HARDWARE.md)、[控制边界与待验收项](docs/STATUS.md)、[第三方来源](THIRD_PARTY_NOTICES.md)。

## 如何核查

需要 Python 3.10 或更新版本，在仓库根目录运行：

```sh
python -B tools/verify_progress_20261025_26.py
python -B firmware/B0B3/verify_export.py
python -B analysis/20261028_water_drive/qualified_offline_B0B5/verify_review.py analysis/20261028_water_drive/qualified_offline_B0B5
python -m pip install -r ground/requirements.txt
python -B -m unittest discover -s ground/B0B0 -p "test_*.py" -v
```

这些命令不会启动串口接收、编译 Gowin 工程或下载到硬件。部分历史导出工具和旧阶段完整包依赖没有上传的大型原始证据，具体范围请看各阶段说明。B0B3 的构建和验证入口见其 README，旧版说明见[构建说明](docs/BUILD_AND_VERIFY.md)。

如果只想离线查看接收网页，可以运行：

```sh
python -B ground/B0B0/launch.py --no-serial --logs ground/runtime --http-port 8765
```

然后打开 `http://127.0.0.1:8765/`。使用 SiK 无线接收时，需要指定电脑上实际的串口，例如：

```sh
python -B ground/B0B0/launch.py --port COM17 --baud 115200 --source SiK --logs ground/runtime --http-port 8765
```

这里的 `COM17` 只是原电脑上的例子，使用时请按自己的设备修改。如果旧网站已经占用了 8765，请给新实例换一个端口；同一个串口也不要被两个程序同时占用。
