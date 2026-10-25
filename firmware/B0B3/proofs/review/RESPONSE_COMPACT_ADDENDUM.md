# response_compact 组合审阅补充

本补充只审阅第二次通信状态精简及其交付工具绑定。原 `REVIEW.md`、`bounds.json` 保持原字节和历史哈希；没有编辑canonical RTL、工程约束或启动综合/PNR，没有操作硬件/串口。核查时三个response_compact物理尝试仍未产生最终通过凭据；此补充不声称布通、CLS减少或50MHz时序闭合。

## 精确改动与有效性边界

`verification/response_compact_promotion.json` 的55文件from/to集合相同，仅 `xy_pi_parameters.v` 改变。from集合与此前 `comm_compact_promotion.json` 的to集合完全相同；to集合与canonical55文件和 `candidates/response_compact/source` 的55文件逐个相符。控制器、核心安全门、数学服务、传感器/融合、遥控映射、顶层和约束均未被该次推广改变。

旧bank SHA256为 `bb11794b6a406a9c321e53a24d8751dc74006388063ef538bd5084f3d298886f`；新bank为 `c3ab65d07c7b664268192a5b0de3acfb510efdac504a7a82cfdfa89e83d1b187`。旧bank把响应冻结到独立192位reg，再附加CRC；新bank直接拼接bank已经冻结的opcode/status/sequence、active P/I/generation、常量头/build和reply_crc，保留原CRC开始/结束与valid时刻。

当 `response_valid=0`，新wire可以呈现正在解析/CRC计算中的状态和变化的CRC尾，**不等价于旧192位寄存器，也不承诺相同复位值**。等价契约限定为：P/I/generation/valid逐拍一致；response_valid=1时完整192位响应一致；CRC扫描正文的原范围byte2…21一致。CRC自己的byte22…23尾不进入CRC输入，头byte0…1仍不计入原协议CRC。真实TX只在valid资格下取得所有权；一旦发送，bank在最后一个UART字节完成且ready返回前不接受下一请求、不改变上述字段。

`xy_pi_parameters.v:27–31,38–40,85–96`（当前canonical，hash如上）以及 `telemetry_tx.v` 的late-ready路径支持这一所有权关系。原TX精简已取消第二份帧复制；新bank精简取消bank内重复192位寄存器。提交、更换有效P/I、generation、fresh SET序号/范围/CRC检查、write_safe二次检查、controller boundary和模式状态语义都没有改变。

复位测试证明bank在复位时同拍撤销valid和恢复默认P/I/generation；它不声称“复位打断正在发射的字节时，valid=0的所有外部wire仍相同”。当前顶层只在启动阶段释放reset，未增加复位支路或延迟。候选 `local_comm_reset` 曾在跨启动reset的合法UART帧上给出反例并停止；其ordinary-startup通过结果不能消除该反例，该候选没有推广。

## 证据及实际检查

`response_compact_review.json` 绑定本补充、旧审阅记录、两次promotion、candidate.diff、55文件映射、测试脚本/fixture/log/result、host parser及原协议fixture的SHA256。finalizer同时检查result中的指标和实际日志字节，不只接受一个 `passed=true`：

| 证据 | 已覆盖内容 | 明确未覆盖 |
|---|---|---|
| `verification/pair_results.json` | 两个真实bank RTL同输入逐拍；121个原协议用例+5个所有权/复位扩展，总126次响应；12301拍P/I/gen/valid；633次valid完整192位；2672次CRC正文 | 不是全输入形式化等价；valid=0的响应位故意不比较 |
| `verification/bank_before.v` | 只将旧bank与UART模块名添加_before以便双实例编译；归一化行尾并恢复两个模块名后，正文与已审阅comm_compact bank完全相同 | 不把一个重新编写的自定义参考模型当旧RTL |
| `verification/contract_results.json`及log | 真实434拍/bit UART、两次请求/ACK、最大2832005拍held packet、最后字节busy完成才ready、整帧稳定；692 wire bytes与历史canonical log完全相同 | 不证明真实接线、串口射频链路或飞行动态 |
| `verification/link_results.json`及log | 实际串行采样，原644遥测字节逐字节保持；GET seq100回P500/I0/gen0，SET seq101回P1500/I1000/gen1；交付host parser解码 | 不增补EEPROM/Flash参数持久化 |
| 原signed36边界和共享数学争用 | 控制器/门禁源码未变，因此原精确绑定继续适用 | 不能用通信等价替代重新绑定新网表的物理时序报告 |
| `verification/synthesis_comparison.json` | 与前一comm_compact网表的真实综合比较：全局27764FF/35999LUT，比27890/36135减少126FF/136LUT，DSP/BRAM/ALU数不变 | 综合不报告实际packed CLS；未由此证明布通/时序 |

此前第一次TX精简减少199FF/617LUT；本次bank精简额外减少126FF/136LUT。两次是不同网表间的比较，不能把各自未通过的路由报告拼成一次通过，也不能从综合数量推断未来布线成功。

## finalizer的最小fail-closed例外

只允许 `bounds.json` 中 `xy_pi_parameters.v` 的旧hash由本组合证据补充；核心门/控制器等其他不符仍拒绝。例外校验：旧hash→comm_compact原bank、promotion完整链、55文件唯一bank差异、canonical/candidate新源相符、旧bank双实例fixture正文身份、126协议/所有权结果、全部pair/contract evidence文件哈希、link脚本/fixture/log/结果hash、host parser和协议fixturehash、实际692字节流一致。

finalizer的现有telemetry例外保留。新清单同时保留comm_compact与response_compact两个proof子树，避免只打包最终综合donor而遗漏第一阶段契约证据；排除vvp/cache及二进制物理工件。local_comm_reset只保留源码与停止反例证据，没有该候选的综合/PNR位流。其他物理尝试仅保存有限回执、physical.tcl、物理工程、CST/SDC；只有存在process_exit回执时才保存其log/rpt，防止把仍追加的日志纳入冻结清单；不重复复制失败尝试的VG/PR/FS。

## 物理交付工具的边界/待最终核对

1. 现有netlist-only PNR由 `physical_retry.py` 创建仅VG/CST/SDC的physical.gprj，并断言前后VG hash不变；最终必须从选中的同一fixture取得process_exit=0、完整route/bitstream消息、无未布通、20ns真实STA和18引脚匹配。普通RTL工程的run pnr可能重新综合，不能替代这一网表身份。
2. 旧活动build_input的mode字段从donor继承“syn only/PNR prohibited”，不代表该fixture未运行PNR；须结合physical_options、physical_project_sha256、physical.tcl、process.json和原始Gowin日志判定。主线随后更新了未来receipt的显式physical-only mode，历史receipt不回写。
3. finalizer把netlist、PR、FS、TR均要求mtime晚于PNR启动前2秒。当前physical_retry用普通copy导入VG，恰好满足；若以后改为copy2/保留donor时间，此检查会误拒绝合法旧网表。正确的网表身份依据是donor SHA256，物理输出的新鲜度仍须独立保证。此补充没有放松当前检查。
4. 已新增轻量 `verify_timing_review` 门槛：fixture解析后必须为选中fixture、period必须20ns、Fmax至少50MHz且有限、setup/hold违例端点均0、setup/hold/recovery/removal/minimum-pulse-width五类slack均有限且非负；parser_sha256必须等于当前inspect_timing.py，TR/PR/FS/SDC/VG的五个原始evidence hash必须全部与当前文件相符。缺少报告/字段、旧parser或换fixture均拒绝。必须对最终fixture重新运行 `inspect_timing.py --require-pass`；此补充没有实际新TR，门槛只作合成元数据正/负测试，未将任何未完成报告认定通过。
5. finalizer要求TR中的绝对网表路径与当前fixture一致，以及PNR日志完成原文、报告引脚表格式匹配；失败时应检查真实vendor格式/路径，不应删掉这些身份或完成性门槛来通过。

本补充修改只涉及finalizer、当前审阅说明与本补充文件。WORK_STATE、build_attempts、构建与时序验收由主线负责，未由本支线改写。
