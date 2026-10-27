# compact_aw_v5 SYN资源备选（未选择）

真实full-top elaboration及一次map2 SYN均normal p.wait()=0，全部mapped门禁通过。源hold SHA `04e75ada52551d5622af060efe38fda9aa66ff25199bfb67651f9ec5315ed873`；仅num64存储改50+64signalias/100写目标及value48改39+64signalias，其他54项同v4，源55前后不变。

| 实际mapped top | v4 | v5 | 差值 |
|---|---:|---:|---:|
| FF | 27766 | 27725 | −41 |
| LUT | 36213 | 36150 | −63 |
| ALU | 9544 | 9461 | −83 |

controller自身−41FF/−43LUT/−83ALU；所有DSP类型与BRAM不变。实际资源变化包含优化器传播，不按源码减少的位数反推每个单元的因果，也不据此声称更易布通。

实际VG SHA `2d670218e97041bb3d4cc7c67218f4bef12e5bf96261225b9b97203ce3b4a1c9`。所有27725个FF clock为clk50；radio pad/meta-Q同步级边界、18scalar ports、16bit P/I INIT1000/350均重新检查通过。保留UserCodeB4/map2/replicate0、原20ns SDC及false-path范围。

最终SYN冻结`build_attempt_01/synthesis_freeze_manifest_final.json` SHA `677dcfbdcc9fc448e3313b83cfef6f43729c521f738676d46cef2ad1a92a9b12`，78件18,156,051bytes；原始命令/工具/runner/source SHA和actual wait0均保留，详情门禁及资源hash见本目录`RESULTS.json`。root另跑v5功能回归；此SYN记录不代替其结果。

**本候选仅SYN资源备选，未运行PNR，未生成FS/STA，也未选择交付或硬件安装。** root优先已有物理候选的首个全门结果；资源更小不构成必须升级理由。没有修改v4、原B4/B3/R/H或任何旧fixture。
