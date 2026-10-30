# B0AE：离线候选版本

这个版本选用 `mask_retimed_f200_rep0_map2_r2` 目录中的工程。`fixture/acg720_ano_port.gprj` 和 `fixture/build.tcl` 按原始字节导出，没有对已完成证明的 RTL 做便携化修改。每个导出文件的原路径和 SHA-256 见 `source_export.json`。

- 目标：GW5AT-LV60PG484AC1/I0，50 MHz。
- 历史工具：Gowin V1.9.12.04，mapper 2、place 3、route 2、max fanout 200、物理资源复制关闭。
- 原布线结果：50.505 MHz、0 未布通、setup/hold TNS=0、17 个精确 I/O，UserCode `0xB0AE`。
- 历史位流 SHA-256：`7cef4a47a17d2a03709d0b7f5bdb7c1b46c030a33c72876db65aba2e0b953a80`。位流本体未放入源码仓库。
- 未做该版本的 SRAM/Flash 下载；最近已验证默认 Flash 为 B0AC。

`reference/` 保存比较所需的部分原始 C 函数和模型，并保留来源版权；它不是完整的原厂固件包。`tests/` 保存生成的测试台、向量、输出和证明 JSON，内容与历史文件一致。部分记录中有旧机器或先前等价变体的路径，来源字节校验通过不代表已在当前路径下重新运行全部测试。

`provenance/` 保留选用指针、qualification、build manifest、时序和资源报告、源码差异及原检查脚本。`original_scripts/` 中的历史脚本依赖原 B0AD 回退位流、其他审查目录和原工具路径，**不能作为便携执行入口**。其中有关“板上版本”的文字描述的是文件产生时的状态，最近状态请看主 README。

在新机器上，从仓库根目录使用 `tools/verify_export.py`、`tools/sim_smoke.py` 和 `tools/build_firmware.py`。这些包装器保留原 RTL 和构建 TCL，输出写入被忽略的 `out/` 目录。选择性 RTL 回放不能替代完整的原 C/oracle 和全部回归链重跑，也不能替代实物验收。
