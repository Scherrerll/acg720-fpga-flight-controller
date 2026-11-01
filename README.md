<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/branding/gm-fly-dark.svg">
    <img src="assets/branding/gm-fly.svg" alt="GM-FLY 项目标志" width="180">
  </picture>
</p>

# 基于FPGA的水空两栖无人平台

本作品以高云小梅哥 ACG720 FPGA 开发板为核心，设计水空两栖无人平台。系统融合 IMU、激光测距、光流等传感器，在 FPGA 硬件逻辑中完成传感器数据采集、姿态解算、运动控制及多路电机 PWM 驱动，实现空中姿态稳定、定点悬停和水面航行，并支持水空工作模式切换。同时搭载数传电台，系统通过无线数传链路将运行数据发送至地面站，支持状态实时显示、数据记录与日志回放，辅助空中飞行和水面航行的调试与分析。作品发挥 FPGA 并行处理和时序可控的特点，突出其在跨介质无人平台实时感知与运动控制中的主体作用。

仓库在 2026 年 10 月 22 日开始整理。前面从 9 月的架构和选型讨论、10 月初的 ACG720 选型和接线开始，后面按开发阶段存放。Git 提交日期是实际整理上传的日期；各阶段日期来自会话和验证记录。

## 版本说明（更新于 2026-10-31）

目前最新的是 [B0B5 水面双推进版本](firmware/B0B5/README.md)，[源码工程在这里](analysis/20261028_water_drive/qualified_offline_B0B5/source/acg720_ano_port.gprj)。A13、A14 输出两路 50 Hz PWM，13 项离线检查和 20 ns 约束下的五类 STA 均通过，Fmax 为 50.032 MHz。当前接线和测试条件下使用正常。

其他版本和相关入口：

| 版本 | 已完成的工作 |
|---|---|
| [B0B4 高度抗积分饱和](firmware/B0B4/README.md) | 保留原飞行版本的源码、位流和安装、验证记录 |
| [B0B3 在线 P/I](firmware/B0B3/README.md) · [源码工程](firmware/B0B3/source/acg720_ano_port.gprj) | 完成布线；20 ns 五类 STA 通过，Fmax 50.257 MHz；有停机原子参数、CLI 和回归记录 |
| P005/I0（B0B2）· [当次回执](validation/20261025_p005_i0/README.md) | 10 月 25 日完成独立 Flash 校验和冷启动，默认 P=0.05、I=0 |
| [B0B2 原 V15](firmware/B0B2/README.md) | 保留原 V15 的 51.400 MHz、19.5 ns 通过结果和当次上板、Flash 记录 |
| [B0B0](firmware/B0B0/README.md)、[B0AC](history/12-b0ac/) | 保留原拆桨、Flash 和冷启动证据 |
| [B0AE](firmware/B0AE/README.md) | 保留 10 月 22 日离线回归和 50.505 MHz 结果 |
| [ground/B0B4 地面站](ground/B0B4/README.md) | 新增 GM-FLY 风格实时、日志和 P/I 页面，可显式选择 B0B4 或 B0B5 参数协议 |
| [ground/B0B0](ground/B0B0/README.md) | B0B0 分帧解码、只读接收和自动日志，提供便携导入适配 |
| [分享网站](https://gmflylog.com/) · [源码](web/flight-console/README.md) | 恢复 B0B0 实时转发，保留选定日志分享与慢网络恢复 |

更早的工作可查看 [10 月 25～26 日记录](docs/WORK_20261025_26.md)、[归档索引](docs/WORK_ARCHIVE_20261025_26.json)和 [10 月 23～24 日记录](docs/WORK_20261023_24.md)。

## 仓库目录

- [history](history/README.md)：选型、初始接线及 01–13 阶段的源码和验证摘要，时间顺序见[时间线](docs/TIMELINE.md)。
- [机械最终版总装](mechanical/final-assembly-20261031/README.md)：2026-10-31 用户确认的「飞船五颜六色版」，含原始 ZIP、1 个总装和 28 个零件；[机械历史资料](mechanical/README.md)保留早期 CAD、STEP、打印件及加工件。
- [hardware](hardware/README.md)：材料购买文档原件《材料汇总.docx》。
- [firmware/B0B5](firmware/B0B5/README.md)：水面双推进的源码、位流入口和测试反馈；[B0B4](firmware/B0B4/README.md)及更早版本也在 firmware 中。
- [ground](ground/README.md)、`support/`：Python 接收网页和所需解码器；B0B4 地面站支持在明确启用后进行受控的 P/I 查询和设置。
- [web/flight-console](web/flight-console/README.md)：分享前端、本地转发、EdgeOne 云函数与存储适配，以及部署和验收记录。
- [构建与核查工具](docs/BUILD_AND_VERIFY.md)：导出完整性校验、离线构建和选择性 RTL 回放。
- 其他资料：[接线与单位](docs/HARDWARE.md)、[控制边界与待验收项](docs/STATUS.md)。

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
