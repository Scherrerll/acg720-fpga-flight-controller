<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/branding/gm-fly-dark.svg">
    <img src="assets/branding/gm-fly.svg" alt="GM-FLY 项目标志" width="180">
  </picture>
</p>

# GM-FLY · ACG720 FPGA 四旋翼飞控开发与验证

面向嵌赛高云赛道的 ACG720 / Gowin GW5AT-60K 四旋翼飞控工程，重点展示 FPGA 并行传感器接口、定点 RTL 姿态与飞行控制、资源与时序收敛，以及可追溯的验证流程。系统接入 BMI088、MTF-01P 光流/测距和 SiK 无线遥测，配套本地网页与日志分析工具。

本仓库于 **2026-10-22** 整理为私有归档。提交从 **9月架构/选型讨论、10月初选定ACG720与接线** 开始，再按开发阶段排列。提交日期是整理当天；阶段日期来自会话与验证记录，没有伪造历史 Git 时间。早期目录是当前工作区的阶段导出，不能全部视为历史当天精确快照。

## 当前选用版本

| 用途 | 版本与入口 | 已有证据 | 尚未完成 |
|---|---|---|---|
| 最近已验证的默认 Flash | [B0AC 历史工程](history/12-b0ac/) | 拆桨模式/运行、Flash 独立校验、仅电池冷启动 | 带桨闭环飞行与掉动力原因确认 |
| 最新算法候选 | [B0AE GPRJ](firmware/B0AE/fixture/acg720_ano_port.gprj) | 离线算法回归、布线 0 未通、50.505 MHz、setup/hold 0 违例 | SRAM 上板及实物验收；未写默认 Flash |
| 只读地面站 | [ground](ground/README.md) | 解码、保存、CSV/ZIP 下载与分析的离线测试 | 本次便携副本未替换正在运行的监控服务 |
| 只读分享网站 | [gmflylog.com](https://gmflylog.com/) · [源码](web/flight-console/README.md) | 国内无 VPN 实时访问、日志上传/读取/CSV、大日志完整性验证 | 实时数据依赖电脑端接收与转发服务；旧云日志需重新选择分享 |

**B0AE 是离线通过的候选，不能据此称为已完成飞行验收。** 默认 Flash 已验证为 B0AC，10-22 最后一次遥测刷新也报告 B0AC（来源见 B0AE `provenance/latest_work_state_at_export.txt`）；更早证明里的 B0AD 是历史 SRAM 观察。本次整理上传没有下载 FPGA、写 Flash 或改变电台参数。

B0AE 的选用来源为 `routing_rescue_20261015/mtf01p_b0ae_ano_control/variants/mask_retimed_f200_rep0_map2_r2`。原目录其他失败/未选用的布线变体没有作为正式工程导出。

## 目录

- [history](history/README.md)：00a选型、00b初始接线，接01–13阶段源码与验证摘要；[完整时间线](docs/TIMELINE.md)。
- [mechanical](mechanical/README.md)：SolidWorks总装/零件、STEP、打印件与加工件资料，保留原相对目录。
- [hardware](hardware/README.md)：材料购买文档原件《材料汇总.docx》。
- [firmware/B0AE](firmware/B0AE/README.md)：选用 RTL、约束、原始参考函数、测试向量和原始证明记录。
- [ground](ground/README.md)、`support/`：便携的 Python 只读接收网页与必要解码器。
- [web/flight-console](web/flight-console/README.md)：GM-FLY 分享前端、本地转发、EdgeOne 云函数与存储适配，以及部署和验收记录。
- [tools](docs/BUILD_AND_VERIFY.md)：导出完整性校验、可配置工具路径的离线构建和选择性 RTL 回放。
- [接线与单位](docs/HARDWARE.md)、[控制边界与待验收项](docs/STATUS.md)、[第三方来源](THIRD_PARTY_NOTICES.md)。

## 快速核查

Python 3.10+：

```sh
python tools/verify_export.py
python tools/build_firmware.py
python -m pip install -r ground/requirements.txt
python -B -m unittest discover -s ground -p "test_*.py" -v
```

上述命令不启动串口接收、不编译 Gowin、不下载硬件。实际离线构建需显式加 `--execute`，见[构建说明](docs/BUILD_AND_VERIFY.md)。

网页离线查看：

```sh
python -B ground/launch.py --no-serial --logs ground/runtime --http-port 8765
```

然后打开 `http://127.0.0.1:8765/`。无线接收需显式指定电脑端 SiK 的实际串口：

```sh
python -B ground/launch.py --port COM17 --baud 115200 --source SiK --logs ground/runtime --http-port 8765
```

`COM17` 只是原机器示例。正在运行的旧网站占用 8765 时，请给新实例选其他端口，不要同时抢占同一串口。

原始飞行日志、工具二进制、位流、`impl/`、单独的用户照片、无关作业、完整厂商资料包和失败变体没有上传。材料Word文档按用户要求原样保存，保留其内嵌内容。保留的验证文字可能含原机器绝对路径，仅用于来源追溯；原始完整资格检查仍有原工作区依赖，不能据此宣称在任意机器上一键重放了所有历史测试。

仓库暂不授予统一的 MIT/GPL 等许可证。第三方版权与许可各自保留；特别是匿名参考源码的公开再分发条件仍需核清，见[第三方说明](THIRD_PARTY_NOTICES.md)。
