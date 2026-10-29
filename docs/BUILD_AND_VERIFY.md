# 构建与核查

## 导出完整性

在仓库根目录运行：

```sh
python tools/verify_export.py
```

该命令核对 B0AE 导出文件、早期和晚期历史资料、便携地面站、机械模型与材料原件的归档哈希；同时检查文件大小、17 个 GPRJ 的引用、B0AE qualification 源码、原始参考函数、选用离线证明和关键 TCL 选项。它不会重跑原机器上的完整资格验证，也不会打开或重建 CAD 装配。

`.gitattributes` 禁止 Git 转换换行，以保留历史文件混用的 CRLF/LF 原始字节。如果修改了受证据约束的源码，旧 qualification 就不能再代表修改后的源码；仅更新哈希不能证明验证重新通过。

## 只读地面站

需要 Python 3.10+ 和 pyserial 3.5，使用方法见 [ground/README.md](../ground/README.md)。以下离线单元测试不会打开串口或监听网站端口：

```sh
python -B -m unittest discover -s ground -p "test_*.py" -v
```

## 分享网站

需要 Node.js 20.18+ 和 Python 3.10+。在 `web/flight-console/` 目录下运行：

```sh
npm ci
npm test
npm run build
cd local
python -B -m unittest test_bridge.py
```

测试使用内存或本地 mock，不连接串口，也不发布真实遥测。归档时 20 项 Node 测试和 16 项 Python 测试通过；实际部署与公网验收记录见 [deployment.json](../web/flight-console/deployment.json)。网站源码不在上面旧工程导出清单的哈希核验范围内，部署凭证、发布令牌和私人飞行日志不入库。

## 选择性 RTL 回放

安装 Icarus Verilog，并将 `iverilog` 和 `vvp` 加入 PATH，或显式指定路径：

```sh
python tools/sim_smoke.py --iverilog "C:/tools/iverilog/bin/iverilog.exe" --vvp "C:/tools/iverilog/bin/vvp.exe"
```

该命令使用仓库中选定的 RTL 编译 9 项带自检查的测试台，覆盖控制竞态、准备和起飞状态、几何资格、导航、整数除法、PWM 波形及掩码重定时。程序会读取历史测试台的输入哈希，不依赖打印历史 PASS 文本；测试输出只写入 `out/`。这不是完整 C/oracle 等价验证的重跑，原历史脚本和证据保存在 `firmware/B0AE/provenance/`。

## Gowin 离线构建

原版使用 Gowin V1.9.12.04 x64。先核查导出文件，此命令不会启动编译：

```sh
python tools/build_firmware.py
```

执行综合和布线时，指定实际工具路径：

```sh
python tools/build_firmware.py --gw-sh "C:/Gowin/Gowin_V1.9.12.04_x64/IDE/bin/gw_sh.exe" --execute
```

也可以设置 `GW_SH`。程序会先核查冻结输入，复制到 `out/b0ae_<UTC>/`，运行原样的 `build.tcl`，再检查实际综合和 PNR 选项、完成标志、未通网络、50 MHz 时序、setup/hold 违例、精确引脚及 UserCode，并写入新的报告和哈希。该过程不执行 SRAM/Flash 下载。如果重新构建的位流与历史位流不同，会分别记录，不自动沿用历史验收结果。

GPRJ 是源码入口，严格选用的参数以 TCL 为准。仅在 GUI 中使用默认选项打开工程，不能认定为复现了选用构建。

旧阶段的构建方法见各自 README。部分历史脚本依赖原机器路径或回退位流，仓库没有完整复制这些依赖，因此仅作为追溯资料。整理上传时没有重跑 Gowin 全量布线，也没有更改原工程。

## 10 月 23～24 日追加归档

`python tools/verify_recent_export.py` 用于验证 979 项有界导出、JSONL gzip 解压后的哈希、51 个 B0B0 源输入、精确网表和位流，以及 GPRJ 引用。命令不访问硬件，也不依赖原机器路径，但没有重跑完整原始资格链。B0B0 接收端测试需要从 `ground/B0B0` 单独执行，避免与历史接收器的同名模块混淆。

两份选中位流是 `.gitignore` 中的明确例外；其他位流、凭证、完整原始日志和大型 `impl` 数据库的忽略规则没有放宽。
