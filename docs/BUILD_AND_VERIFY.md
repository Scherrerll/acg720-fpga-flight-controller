# 构建与核查

## 导出完整性

```sh
python tools/verify_export.py
```

核验 B0AE 导出文件 SHA-256、早/晚历史及便携地面站清单哈希、机械模型/材料原件的归档哈希与大小、17 个 GPRJ 引用、B0AE qualification 源码哈希、原始参考函数哈希、选用离线证明及关键 TCL 选项。不会执行原机器的完整资格链，也不打开或重建CAD装配。

`.gitattributes` 禁止 Git 换行转换，以保持混合 CRLF/LF 历史文件的原始字节。编辑受证据约束的源码后，旧 qualification 不再代表新源码；不能只刷新哈希就声称重新通过验证。

## 只读地面站

Python 3.10+、pyserial 3.5。见 [ground/README.md](../ground/README.md)。离线单元测试不打开串口、不监听网站端口：

```sh
python -B -m unittest discover -s ground -p "test_*.py" -v
```

## 选择性 RTL 回放

安装 Icarus Verilog，使 `iverilog` 和 `vvp` 在 PATH，或显式指定路径：

```sh
python tools/sim_smoke.py --iverilog "C:/tools/iverilog/bin/iverilog.exe" --vvp "C:/tools/iverilog/bin/vvp.exe"
```

从本仓库的选用 RTL 编译 9 项带自检查的测试台，包括控制竞态、准备/起飞状态、几何资格、导航、整数除法、PWM 波形和掩码重定时；读取历史测试台的输入哈希，不靠打印历史 PASS 文本。测试输出仅写 `out/`。这不是完整 C/oracle 等价验证重跑，原历史脚本和证据保存在 `firmware/B0AE/provenance/`。

## Gowin 离线构建

原版使用 Gowin V1.9.12.04 x64。先只校验导出而不启动编译：

```sh
python tools/build_firmware.py
```

真正执行综合/布线：

```sh
python tools/build_firmware.py --gw-sh "C:/Gowin/Gowin_V1.9.12.04_x64/IDE/bin/gw_sh.exe" --execute
```

也可设置 `GW_SH`。程序先核验冻结输入，复制到 `out/b0ae_<UTC>/`，运行原样 `build.tcl`，检查实际综合/PNR 选项、完成标志、未通网络、50 MHz 时序、setup/hold 违例、精确引脚与 UserCode，并写新报告/哈希。不执行 SRAM/Flash 下载。重新构建的位流若与历史位流不同，会分别记录，不自动冒用历史验收。

GPRJ 是源码入口，严格选用参数以 TCL 为准。不能只打开 GUI 使用默认选项，就声称复现选用构建。

旧阶段的构建说明见各自 README。部分历史脚本含原机器路径/回退位流依赖，仅作为追溯资料，仓库没有完整拷贝这些依赖。上传整理没有重跑 Gowin 全量布线，也没有更改原工程。
