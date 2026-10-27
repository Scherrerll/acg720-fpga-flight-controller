# B0B4 attempt02 P2R0 物理尝试：失败并保留

独立attempt02正常取得实际 `p.wait()=1`，原始日志报告 `DesRoute failed`、`PR0004: total721unrouted nets`；未生成TR或FS，**没有物理/时序资格通过结论**。没有重新综合、修改canonical55、ground、旧proof或操作硬件/Git，也未启动后续profile。

## 精确输入与执行

- 构建目录：`out/z_aw_fix_20261026/build_attempt_02`；analysis仅写本`build/p2r0`目录。
- donor：attempt01已审计VG `f63ae79edcd75c9905a0e55b53c3d8d9d94c239d8e67038a73fade80ffaa958a`，14746310bytes。fresh02复制canonical55并额外复制此精确VG；没有复制旧PNR产物。
- source55与donor、canonical完全相同，hold SHA `5a928e0a68db70974049a4debb0b841ca06fa00598a4ffb4cb506997cfed657c`。原source/build.tcl仍逐字节保留，独立physical.tcl选择 **place2/route0/map2/replicate0/UserCode0000B0B4**；SDC仍20.000ns。
- physical.gprj只列VG、CST、SDC。实际日志明确 `Skip synthesis, because there is only one netlist file`。
- 新helper `firmware/B0B4/retry_physical.py` SHA `2bb616de1bdd860222434f89702acdfe56726bcfb80f583efac169fb23c282f1`。只读导入原 `build_candidate.py`（SHA `abb5246c203b73c111f80bc91f8db6c8220463f7d4c5cf48dbfe2167ef49db84`），显式将其ATTEMPT/SOURCE/VERIFY绑定02，原run_phase/physical_audit门完整复用，无门槛放宽。
- helper PID15404，vendor PID7440，原native creation `2026-10-26T12:03:13.659553+08:00`，parent15404，CIM命令为02精确physical.tcl。DEVNULL/CREATE_NO_WINDOW及EOF driver保留。
- 实际开始 `2026-10-26T04:03:13.658492Z`，vendor返回 `2026-10-26T04:37:46.566395Z`，`normal_wait_return=true`、`actual_p_wait=1`。故没有进入仅在exit0之后执行的physical_audit，也没有生成假PASS receipt。

## 原始报告事实

| 项目 | attempt02实际报告 |
|---|---:|
| 未布通网络 | 721 |
| Logic | 46478/59904，78% |
| LUT / ALU | 36631 / 9847 |
| Register | 27905/60780，46%（logicFF27901+IOFF4） |
| CLS | 26302/29952，88% |
| PRIMARY / LW | 各8/8，100% |
| TR / FS | 均不存在 |

原报告命名的PRIMARY含 `clk50_d`、`mtf_sample`、`core/n5926_7`、两个estimator信号、velocity_fusion信号、两个controller_proof信号；LW含 `observer_reset`、`rst_n_ff`、staged_telemetry、diagnostic及若干内部信号。完整命名/区域原文保存在 `resource_and_global_excerpt.txt`。这些分配/利用率和721计数不能单独识别失败的具体net、资源类型或唯一根因。

完成后再次读取并确认：canonical55、02源55、01源55及donor四项proof/VG哈希全部未变；helper与原runner也未变。输入/退出/报告绑定在本目录 `RESULT.json`，全部源55哈希及轻量证据哈希均列入其中。

## 冻结证据SHA256

| 相对attempt02路径（除注明外） | SHA256 |
|---|---|
| `physical.tcl` | `9873825636c469ca74dc6d12c84f6ef930a8318b4b736408f4f168a5c1832947` |
| `verification/physical_input.json` | `aba920c909060338a447bc43177920917f06318f2e029c0f4d381a8b5b2bfdfd` |
| `verification/physical_exit.json` | `24c8878b9a753bfb6d1676f188098b15636259c2e54cd858e4939a0ad25ca625` |
| `verification/physical.log` | `b42bd989d6d96bdcd745ca3b77e9b1f6de115aa02b576e7c96c43d4850440f15` |
| `source/impl/pnr/acg720_ano_port.rpt.txt` | `09611a274d381f9ad7c0246c239a068b3370ad6e9eed3958f576e6db0fbd7204` |
| 本analysis目录 `RESULT.json` | `b7dba4c73c8dab2c1fb4cdeff603f833fffdcf4471838ab8b3b4a721219b1b86` |
| 本analysis目录 `resource_and_global_excerpt.txt` | `7317865964b2413b7e83de83b527ac13944d1821a9b761d02f7431367e20d7d1` |

此尝试保留为真实失败历史；不能因比另一次未布通数量少而称其已可下载、通过时序或可飞。
