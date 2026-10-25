# 响应字段快照压缩：第二个独立备用候选

状态：源级契约复核、真实RTL逐周期对照、真实UART与背压测试、真实综合均PASS。**未推广canonical、未启动PNR、没有位流/CLS打包/50MHz时序通过结论。**

此目录复制当前canonical的55份source（含已推广late-ready TX和observer物理约束），只改 `xy_pi_parameters.v`。参数范围、CRC算法、请求/版本/长度/序号、重发高水位、SET校验/原子提交、active P/I/generation、状态和保护均保持。前后完整源哈希在 `change.json`，可审阅差异为 `candidate.diff`；准备、测试、综合结束都核验canonical55文件未变。

## 为什么可以移除第二份字段寄存器

原bank在state3把已有字段复制到192位response，在state5再复制reply_crc。候选将response声明为组合wire，以同样字段/顺序拼接，保留原state3/4/5及valid的逐周期时序。

| 字段来源 | 可写位置 | state3到valid/ready期间为何稳定 |
|---|---|---|
| frame/opcode/sequence | reset，state0且!response_valid时接收 | state3/4/5不接收，valid期间state0明确拒绝解析 |
| status | reset，state1/2 | state3之后无赋值，直到当前响应释放后下一帧 |
| active P/I/generation | reset，state2提交 | 当前事务离开state2后不能再提交，valid期间不接收新事务 |
| reply_crc | reset，state3初始化，state4推进 | state5及valid等待期间不变 |

CRC输入仍只遍历bytes2..21，恰好是版本到build ID，不含两字节帧头或末尾CRC。虽然组合response的CRC尾在state4随reply_crc变化，选中的输入字节从未覆盖该尾，故不会把CRC再喂回自身。state5仍在相同边沿置valid，旧版此时复制的CRC与候选wire上的reply_crc相同。

reset会同时恢复两版active P=500、I=0、generation=0并撤销valid。旧response在reset/invalid时为0，候选invalid时仍显示字段拼接；**valid=0时的192位值不属于接口契约**，没有把它当作逐位相等的要求。真实late-ready TX仅在valid后取得所有权，并在最后一个UART字节确实完成后才ready；reset期间不产生新有效响应。本候选没有增加新的发送端提前消费条件。

## 真实RTL对照

`verify_pair.py` 使用主线实际 `verification/protocol_tb.v` 的全部121协议向量，同时驱动原版bank与候选bank，非Python复刻模型。每周期严格case比较P/I/generation/response_valid，valid时逐位比较完整192位响应；还比较每个CRC阶段bytes2..21输入体，并检查index始终2..21。

通过结果：

- **12,301个时钟**的P/I/gen/valid完全相同。
- **633个valid周期**的完整192位响应完全相同。
- **2,672个CRC体周期**一致。
- **126份检查响应**由shipping电脑端解码器校验，包含原121用例和5个补充检查。

原121用例覆盖GET、SET、CRC损坏/逐bit翻转、版本/长度/保留字节/opcode、范围、重复/陈旧序号、锁定、提交竞态、超时、背压和复位默认值。补充场景专门针对新ownership边界：CRC中复位、valid背压中复位、pending commit复位、提前完整GET不能改held SET响应、释放后fresh GET。

`verification/pair_results.json` 绑定原向量夹具、原版真实bank改名副本、候选源码、对照夹具和日志SHA。响应在invalid时的don't-care差异是显式设计边界，未掩盖任何valid响应不同。

## 真实UART与late-ready

`verify_link.py` 仅适配主线脚本的路径/输出，使用同一冻结telemetry baseline和shipping `xy_pi_cli.py`。`verify_contract.py` 使用候选新bank与未改late-ready TX：

- 644字节旧遥测完全保持。
- GET/SET与generation/实际P/I正确。
- 692字节完整输出与当前canonical逐字节一致。
- packet在valid期间稳定；两次ready均仅出现于最后字节UART busy已经撤销时。
- 最长持包2,832,005 clocks（56.6401ms），覆盖遥测背压和整个响应发送；之后下一请求被接受。

所有结果均在本候选 `verification/`，未访问串口或硬件。可复现：`python -B candidates/response_compact/run_checks.py`。

## 真实综合

`run_synthesis.py` 仅调用厂商 `run syn`，Gowin1.9.12.04退出0；没有run all/run pnr。参考是已推广comm_compact的9b网表及其真实综合XML，RTL仅bank一个文件不同。

| 综合XML资源 | 当前canonical compact | 本备用 | 变化 |
|---|---:|---:|---:|
| 顶层 Registers | 27,890 | 27,764 | −126 |
| 顶层 LUT | 36,135 | 35,999 | −136 |
| 顶层 ALU | 9,565 | 9,565 | 0 |
| 参数bank Registers | 414 | 290 | −124 |
| 参数bank LUT | 456 | 435 | −21 |
| 参数bank ALU | 79 | 79 | 0 |
| DSP/BSRAM组成 | 相同 | 相同 | 0 |

顶层其余差异包含映射/共享变化，不能把全部136个LUT都解释成删除字段快照的直接硬件数量。综合不报告实际packed CLS，故不能声称CLS节省或未布通数改善。新组合路径也必须有自己的完整PNR和真实20ns STA，不以综合或协议通过代替时序闭合。

关键SHA256：

- 新bank：`c3ab65d07c7b664268192a5b0de3acfb510efdac504a7a82cfdfa89e83d1b187`。
- 本候选真实VG：`7d815709a3699e3805efadf4a287e388329d5a75ca2f63ef40ea05bbf349b3e9`。
- 参考compact VG：`9b2cee37e4f0ed0e68c9abb2895228c455a12f50cc5e9ba2d741a36350f404dc`。

机器结果在 `verification/synthesis_comparison.json` 和 `bank_resource_comparison.json`，工件清单在 `candidate_artifact_hashes.json`。在主线明确选择前，本目录只作为备用，不替换canonical。
