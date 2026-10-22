# B0AE：选用离线候选

`fixture/acg720_ano_port.gprj` 及 `fixture/build.tcl` 来自选用目录 `mask_retimed_f200_rep0_map2_r2`，均按原始字节导出。`source_export.json` 记录每个副本的原路径与 SHA-256；没有对已证明的 RTL 做便携化改写。

- 目标：GW5AT-LV60PG484AC1/I0，50 MHz。
- 历史工具：Gowin V1.9.12.04，mapper 2、place 3、route 2、max fanout 200、物理资源复制关闭。
- 原布线结果：50.505 MHz、0 未布通、setup/hold TNS=0、17 个精确 I/O，UserCode `0xB0AE`。
- 历史位流 SHA-256：`7cef4a47a17d2a03709d0b7f5bdb7c1b46c030a33c72876db65aba2e0b953a80`。位流本体未放入源码仓库。
- 未做该版本的 SRAM/Flash 下载；最近已验证默认 Flash 为 B0AC。

`reference/` 是比较所需的有限原始 C 函数及模型，保留来源版权；不是完整原厂固件包。`tests/` 保存生成的测试台、向量、输出和证明 JSON，均与历史文件一致。部分记录保留旧机器或先前等价变体路径，来源字节校验不等于当前路径下重新执行过全部测试。

`provenance/` 原样保留选用指针、qualification、build manifest、时序与资源报告、源差异和原检查脚本。`original_scripts/` 是历史实现记录：它们依赖原 B0AD 回退位流、其他审查目录、原工具路径，**不是便携执行入口**。里面的旧“板上版本”文字属于文件产生时的状态，不覆盖主 README 的最近状态。

在新机器上使用仓库根目录的 `tools/verify_export.py`、`tools/sim_smoke.py` 和 `tools/build_firmware.py`。这些包装器保留原 RTL 和构建 TCL，输出写入被忽略的 `out/`。选择性 RTL 回放不替代完整的原 C/oracle/全部回归链，也不替代实物验收。
