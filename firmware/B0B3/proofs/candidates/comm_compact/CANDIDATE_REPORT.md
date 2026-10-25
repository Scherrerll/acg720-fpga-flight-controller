# 通信响应暂存压缩：独立备用候选

状态：源码/通信验证/真实综合通过；**未被主线选择，未推广canonical，未运行PNR，没有位流或时序通过结论。**

本目录复制了canonical当前55份source文件（包含 `observer_reset` 全局物理CST），仅改 `source/telemetry_tx.v`；控制器、参数bank、CRC、序号高水位、保护、参数范围、管脚与时序约束均逐字节不变。完整前后文件SHA在 `change.json`，改动在 `candidate.diff`。准备、测试、综合均对canonical55文件重新做了完整清单比较，原root副本保持不变。

## 源级契约与变化

原实现把bank已有的192位响应再次复制进 `parameter_shift`，在发送起点即给bank ready，然后逐字节移位。候选取消这份第二副本，直接按 `parameter_index` 从bank的 `parameter_packet` 取字节；`parameter_ready` 仅在 state8、index23、UART busy已撤销时产生一个周期。该条件发生于最后一个字节实际发完之后。

未修改的 `xy_pi_parameters` 在response_valid期间不解析后续请求、不改响应包，直到ready后才释放响应寄存器。因此其原有寄存器足以承担整帧所有权。CRC在valid置位前算完，随后packet不会在发送途中变化。遥测组已经开始后不能被参数帧截断；原有到期遥测优先仲裁及单一UART保持。

协议原本只允许一个在途请求，主机收到完整响应后才发下一请求；候选遵守此契约。它不保留原第二副本所偶然提供的提前并行接收能力，超前多请求仍属于协议允许丢弃的输入。正常GET/SET/回读功能与主线一致。

## 真实UART验证

`verify_link.py` 是主线脚本副本，只调整目录/输出路径绑定，使用同一 `test_baseline` 和同一shipping `xy_pi_cli.py`。它通过真实UART RX→未改bank→候选TX→串行波形采样，证明：

- 完整644字节原遥测与冻结基线完全相同。
- GET和SET响应由同一电脑端解析器解码，实际值与generation正确。
- 候选692字节完整输出（644遥测+两份24字节响应）与canonical实测RTL仿真输出逐字节一致。

`verify_contract.py` 另加源级所有权相关的真实RTL断言：packet在valid期间稳定；bank保持等待且没有解析另一帧；ready绝不早于最终字节UART完成；两次ready都在state8/index23/!busy，随后第二请求被接受。第一份packet被保持2,832,005个50MHz周期（56.6401ms），覆盖前一整组遥测背压和自身发送时间。`contract_results.json` 绑定脚本、夹具、编译日志、串行日志、候选TX和未改bank哈希。

运行：`python -B candidates/comm_compact/run_checks.py`。输出仅在本候选 `verification/`。两项均PASS；没有访问串口、硬件或原接收器。

## 真实综合与资源

`run_synthesis.py` 只运行厂商 `run syn`，未使用run all/run pnr。Gowin 1.9.12.04返回0，实际网表与XML保存在 `source/impl/gwsynthesis/`，进程回执和输入清单位于 `verification/synthesis_*.json`。比较参考为主线 `builds/release_width36` 的同版本工具/选项综合结果；两份RTL语义输入仅telemetry_tx不同，CST的observer物理行不改变RTL功能。

| 综合XML资源 | 主线36位实现 | 备用候选 | 差值 |
|---|---:|---:|---:|
| 顶层 Registers | 28,089 | 27,890 | −199 |
| 顶层 LUT | 36,752 | 36,135 | −617 |
| 顶层 ALU | 9,569 | 9,565 | −4 |
| telemetry Registers | 432 | 238 | −194 |
| telemetry LUT | 3,146 | 3,061 | −85 |
| telemetry ALU | 46 | 46 | 0 |
| DSP/BSRAM组成 | 相同 | 相同 | 0 |

删除192位重复暂存是明确结构变化；整顶层差值还包含综合映射/共享变化，不把全部617个LUT都称为这192位寄存器的直接逻辑。综合未提供已打包CLS：只能说明寄存器和逻辑需求降低，**不能凭上述差值声称实际CLS减少多少或995未布通问题已解决**。选择本候选后仍必须进行它自己的完整布线和真实20ns STA。

关键SHA256：

- 候选 `telemetry_tx.v`：`11fac23449b65f87a3291231f9be173046c893a994ae658e25f3e0a7827adbbb`。
- 候选综合网表：`9b2cee37e4f0ed0e68c9abb2895228c455a12f50cc5e9ba2d741a36350f404dc`。
- 对比主线综合网表：`1f99ef20515771a7f57b921fe55690ac6173376f4e1f7db1e26b4ab89999de6d`。

`verification/synthesis_comparison.json` 含完整机器可读数值与网表/XML哈希。候选未获得主线推广授权，没有替换任何canonical文件，源码以外的已有构建、主线verification和旧报告均未改动。
