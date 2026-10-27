# B0B4 core 差异独立审查

审查结论：**在本次 changed core source 中未发现需要修改当前物理构建输入的实质缺陷。最终五项有界 RTL 场景均有实际退出0的独立回执；首轮I0夹具超频触发B3/B4共同overrun的失败仍完整保留，未改写为通过。** 本审查只读 B3/B4 差异、调用边界及现有测试；没有启动新测试、综合/PNR、服务、串口或硬件操作。除本报告外未写文件，不审前飞掉高。

## 绑定对象

仓库根为 `C:/Users/ScherrerL/Desktop/apple/github_publish/acg720-fpga-flight-controller`。B3/B4 各55源，只有下列3个源文件不同；CST、SDC、top、flight state、math service及其余52源逐字节相同。codec另行比较，仅严格build常量B3→B4。

| B4路径 | SHA256 |
|---|---|
| `firmware/B0B4/source/position/mtf_xyz_hold_control.v` | `5a928e0a68db70974049a4debb0b841ca06fa00598a4ffb4cb506997cfed657c` |
| `firmware/B0B4/source/xy_pi_parameters.v` | `c7333f8d629a8eed60f0d0a1c042536ffb92eab753d23daee03bcfbdef306392` |
| `firmware/B0B4/source/build.tcl` | `ae4e19024a4869bb0665311dd56589014f1ca0aff123c9cc5c02e441200e17a4` |
| `firmware/B0B4/xy_pi_cli.py` | `b2f25c0f78343b0d7f6a5fbbaacb08a7b11c8ff857de83a88208b7da6c7ea968` |

B3 hold基线SHA256为 `b7eef6d33789523cd1e8ff81b05e75db91ab3c67bf76e03483dec356055fa1a6`。现有 `rtl_regression/inputs.json`（SHA256 `2ca37bc54f571cf2762e1efbf9f01f00af633f8dc95fd3c167283bf64781a11e`）列出同一对55源；源级结论只覆盖这些字节。

## 重点核对

- **同一选择提交 I/输出。** hold:410–428的顺序为 state22暂存原rail后的candidateI，state23更新bias并请求P，state24暂存P+新bias，state66冻结candidate/current两和及实际候选方向，state67提交。hold:126–129的选择同时供:426的I和:427的collective使用；拒绝时使用旧I对应的current sum，接受时使用candidate sum。没有先NBA写I再误读旧I求输出的错配。state22至67间旧I除reset/cancel外没有写入。
- **判据与边界。** hold:126–127采用严格 `candidateSum > 850*65536` / `<0`，比较实际clipped candidate与oldI的方向；等于rail不拒绝，反向消积不被“仍处于饱和”阻断。state53原bias生成I rail、state23新bias用于输出的时刻关系保留。
- **signed/宽度。** 新暂存均为signed33，:122–125显式扩展到signed64，旧I、bias和value也沿用signed64 aliases。自然reset轨迹中bias在0..22937600 Q16整数、I/candidate在±131072000内。即使仅按原signed31 exz存储边界保守估计，P=exz/5的绝对值≤214748364，两和范围在约−345820364..368757964内，signed33足够；没有新增截断溢出或unsigned比较。该界限针对自然初始化及合法接口运算，不把任意私有寄存器强制预置当作可达状态。
- **取消/复位/发布。** hold:294–310的优先分支清旧I及全部新暂存并回state0；state67仍重新检查taking_off，false提交I/collective为0。math cancel、blocked/math error的原取消路径及wrapper公开RC/enable/epoch masks未改。私有Z提交仍需经过原state60..25后发布；新候选不能从取消事务直接发布到下一事务。taking_off与安全输入变化时不声称逐拍旧/新等价。
- **状态/普通路径。** 原case中不存在66/67，新标签各出现一次，8位state/return_state可表示；新增两个时钟不新增共享math请求。未发生AW拒绝、边界刺激相同且安全状态稳定时，后续Z计算与输出值应保持，发布延后2个50MHz时钟；这不是任意异步输入或共享争用下的绝对周期等价承诺。
- **完整XY pair/rollback。** hold:219–225的空闲边界及work_p/work_i同拍采样保留，:342–344的XY取消回滚以及:370–385原积分/发布路径未改。新初值1000/350与bank一致，不把XY I=0解释为关闭固定Z I。
- **bank/协议。** parameters:12、:34的INIT/reset均为1000/350、generation0；:30–31回复build为B4。接收CRC、格式/范围、highwater、write_safe初验、state2实际提交重检、边界等待、同拍pair/gen+1、背压所有权与UART模块均未改。回复CRC仍扫描bytes2..21，包含B4 build，排除header与CRC尾；state2先提交、state3复位CRC、state4扫描、state5 valid，因此首GET/reset与SET回复不存在新build/CRC错位。
- **codec/build。** codec:10–14保留24字节/header/CRC/version/length/range验证并严格接受B4；GET仍零负载、SET仍两值必填、超时不重发。build.tcl:4为B4 UserCode，:5改place3、route仍0；其余选项原样。这是构建身份与物理profile变化，不能由源级审查推出布线/20ns时序通过。

## 已读取的证明及首轮失败复核

截至 `2026-10-26T03:42:04Z`，现有 `rtl_regression/results.json` completed=5、passed=false：

| 已有case | 实际结果 |
|---|---|
| natural_upper_and_low_stick | exit0；2237次实际提交检查；新/旧每次Z发布相差2clocks |
| unsaturated_equivalence | exit0；400次发布值/目标/bias/I相同，正I100次、负I150次，延迟2clocks |
| natural_lower_and_positive_recovery | exit0；650次提交，lower rejects406、accepted up52 |
| cancel_and_takingoff | exit0；八个撤销/重入边界及taking_off=false，74次提交检查 |
| xy_i0_independence | **exit1**；`aw_tb.v:67 unexpected arithmetic/stick/controller fault`，Time200171000，未产生PASS断言 |

第五项失败已即时通知主线。原测试负责人另建 `xy_i0_attempt02`，原cadence只增强诊断，实际exit1复现新/旧同时 `blocked/xy_blocked=1/1`、`reason=128/128`、`height_due/position_due=1/1`、`state=100/100`。这证明原2500clocks的height、5000clocks的XY到达节奏已触发两版原有overrun保护，不能把该失败直接记为B4控制器回归。

随后同目录的独立CASE5仅将callback cadence2500→20000clocks，逻辑dt、端口刺激序列及所有原断言保持；本审查逐行diff确认只有该周期常量与先前诊断文字的变化。该执行实际exit0：150次Z提交、75次XY发布，XY角度精确匹配旧RTL、XY I=0而Z I非0，每次Z发布仍延后2clocks。原 `results.json` 继续保留首失败；新增 `final_results.json` 汇总原case1–4及独立成功case5，不覆盖原日志。

另读现有 `parameter_tests/contention/results.json`：真实四客户端、非零XY I的共享math争用PASS，12XY/20Z回调；max XY request→publish17792clocks（355.84μs），max Z12554clocks（251.08μs）。这是RTL服务/调度证据，不是物理时序表。

已有 `parameter_tests/protocol_results.json`为121寄存器用例+actual UART PASS，`top_safety_results.json`为13项PASS；首个真实RTL GET输出为 `a591010118000000000103e8015e000000000000b0b472b4`，即1000/350/gen0/B4。该证据是RTL仿真，不是机载实收。

证据SHA256：

- `rtl_regression/aw_tb.v`：`f43ca284dec68382a376a179173dff6819d510752c1474579f285aaf85febe56`
- `rtl_regression/natural_upper_and_low_stick/simulation.log`：`0b6fb9133ceefa7cd8e32fc893ede9e230aff133c560d43783193effeb05d281`
- `rtl_regression/unsaturated_equivalence/simulation.log`：`dbdca538e9f703e4112cf7c972abedd78a860cb855551b4b490fef06bf1784e1`
- 首次失败 `rtl_regression/xy_i0_independence/simulation.log`：`a3e87b9431e732dfd07e7d38eab129dc73f980894cdd800e455473245133d623`
- 原cadence双版overrun诊断 `rtl_regression/xy_i0_attempt02/diagnose_original_cadence/simulation.log`：`405284309edb2501c496b23296cd1ad2f289fc4cd75e1eb687ed848d4447d4b3`
- 成功I0独立执行 `rtl_regression/xy_i0_attempt02/corrected_xy_i0/simulation.log`：`83ae5498ef0fe0fdb7fca286499adc08a77b4e40772931765137a85a8704ccac`
- `rtl_regression/xy_i0_attempt02/inputs.json`：`a139d8414f57e9a779acb793a59be54b40cd20d4b0f2f1490192158c1ff07f77`
- `rtl_regression/xy_i0_attempt02/results.json`：`52c1ef0ce5f5b593a14834511558e23cd7d49e2081462868428659c833ffca3e`
- `rtl_regression/final_results.json`：`e356c86092dc3337bc0218fef912ebc863cc8cbad1d7c9575097c8c215dc13ff`
- `rtl_regression/source_stability.json`：`213035dd64acb0bb0249f34b2d6accf49237b37a57410f50969503d5b8dd7f7b`；本审查也重新读取B3/B4各55源并核对当前哈希仍与首轮inputs一致。
- `parameter_tests/protocol_tb.log`：`a36ce405f1de2c24cf6a5a97e934256a72e5a97cb916c46c5fd8e9fed2b5f0bd`
- `parameter_tests/protocol_results.json`：`00817b6d1bc15ae4a48751a5840b94ef33e48d010df9ba4a5ec9546701ac9420`
- `parameter_tests/top_safety_results.json`：`9e45bd8fde2bd0092c9da36925f9a3c6ffaa71cc79d9713fae8b66924ede4274`

审查未提出cleanup或逻辑修改。最终上述五项场景通过范围、真实物理/时序资格、安装及实机着陆效果均保持各自验收边界；没有由有限RTL场景推导任意反馈下立即下降或实际着陆成功。
