# B0B4 着陆修正、P/I默认值与布线问题移交

这是本地归档和新会话规划，**尚未创建新会话，等待用户确认规划**。本轮没有安装B0B4、访问下载器、发送串口写入或切换现有地面站。最终动态快照见本目录STATE.json和MANIFEST.json。

## 用户目标与实体状态

- 修正定点模式最低油门仍悬空、不下降的代码机制；不能建议一直最低油门等待，不能把拨SWA停桨当成正常着陆。
- 将共享水平速度启动默认值改成用户实飞认可的 **P=0.1000、I=0.0350**。这不是Z环增益；X/Y共享同一对参数。
- 保留控制功能和保护要求，持续到有可用的布线结果，之后说明改动、与原P2的关系、取舍和证据，再上传Git。
- 用户要求低空前飞掉高暂不处理。“地效”是用户判断，不是本轮已证实的因果。
- 最新要求：先归档并汇总下一步规划，用户确认后才新建会话。不要提前create/fork/send新任务。
- 此前B0B3已写Flash并验证冷启动；后来用户装桨实飞过，不能把此前“拆桨”确认当成现在的实体状态。新固件下载前必须重新核实当前拆桨、低位及下载连接。

## 当前结论

**没有通过完整50MHz物理验收的B0B4下载包，不能把任何现有B0B4 FS当成已验收固件。** 已布通的几个结果仍有setup违例。现有飞机和接收服务没有自动更新。

源码和地面站已准备好新的默认P/I。GET/SET原子提交、CRC、重放/停机保护保留；新设备响应和UserCode标识B0B4。地面站草稿、默认按钮、帮助说明均为0.1000/0.0350。手动SET仍只对当次上电有效，新固件复位回这组默认值，generation=0；未增加参数NVS/Flash保存协议。

## 已定位并修正的机制

旧Z积分能在最终输出已经到1850时继续正向累积。飞行日志有最低杆、目标下降、输出持续1850且未降级的对应现象；真实旧RTL也从复位自然复现。飞行日志没有内部I，因此不能声称唯一历史根因完全证明。

新算法暂存候选I，取得同一回调P和更新后的bias后，若最终总量越过0..850增量范围且I还同向推动饱和，就保留旧I；反向消积继续允许。同一个选中的I用于状态提交和输出。普通未饱和回调保持原算式，饱和行为有意区别于P2原实现。增加2个50MHz时钟，即40ns，PID逻辑步长仍11ms。原运行下限、着陆判据、RC/高度/倾角保护均保留。

固定传感器仿真的消积时间**不是实机着陆等待时间**，不能作为飞行操作指导。

## 候选与物理结果

| 候选 | 已完成结果 | 状态 |
| --- | --- | --- |
| v4 compact operand | P3R0完整route，49.456MHz，setup −0.220ns / 32违规端点；P4R0 7273 unroute | 不可交付；P3是目前最近50MHz的已布通参考 |
| v5 num50/value39 | P3R0 648 unroute；repl1 2670 unroute | 不可交付 |
| v5 P2R0 | 进程消失，无真实exit回执 | unknown-exit编排中断；不是已证routefail，不能补造退出码 |
| v5 inc_B3 | 匹配2.81%低于80%，工具自动回退普通PNR；随后根任务精确终止冗余计算，实际wait4294967295 | 取消/回退记录；不是增量成功或正常完成 |
| v6 numeric guard | P1R0完整route，44.286MHz，setup −2.580ns/862端点；P2R0完整route，47.942MHz，setup −0.859ns/189端点；P3R0 389 unroute | 三条均自然结束并封存，全部不可交付 |
| v7 AW storage width | 唯一一次SYN实际vendor/runner退出0；clock/radio/gain/18ports审计全过；FF27704/ALU9458/LUT36079，较v5分别−21/−3/−71 | 没有PNR，不宣称时序或可用位流 |

v6把±30000的32位范围判断改为上位符号扩展检查与16位低字比较。2态等价和真实融合逐拍对照已过，但4态X传播有明确差异；实际SYN增加13LUT/64ALU，物理结果未证实优于v4。v7从**v5**派生，不包含v6这两文件改动。

v7仅进一步收窄已证范围的Z私有存储和阶段性别名，保留Q16全部小数位、64位运算别名、原rails、状态和周期数。IZ27、bias26、候选I27、P+bias29、阶段总量30；复用槽的早期其他生命周期保持原宽度。两份独立数学/源码审查无反例。

## 源码位置：防止拿错候选

仓库绝对路径：`C:/Users/ScherrerL/Desktop/apple/github_publish/acg720-fpga-flight-controller`。

**firmware/B0B4/source 目前仍是初版候选5a928e…，尚未promote成最终版本。** 不要因为目录叫B0B4就拿它直接构建或烧录。

- v4 hold：ffddb029cb34a8d2ac8995cc43d85866e273d3d147bb650cfd5d3c66c580b642。
- v5/v6 hold：04e75ada52551d5622af060efe38fda9aa66ff25199bfb67651f9ec5315ed873。
- v7 hold：2109595a24c6f15a553ea8a0958b8313c3f19d56b4371c827cd428976489daad。
- v7 canonical：`out/z_aw_fix_20261026/compact_aw_v7/canonical/source`，55文件，其他54与v5相同。
- v7精确VG：dc20d15cec4471df8679960fb05660349caaa19dfaee40604b419ca6450cf0e0。
- v7SYN：`out/z_aw_fix_20261026/compact_aw_v7/build_attempt_01/`。
- v7封存：`analysis/20261026_z_aw_fix/build/compact_aw_v7/RESULTS.json`、`SYNTHESIS_REPORT.md`和source_freeze.json。
- 本归档另保存v7 hold原始字节；完整source55哈希在STATE.json。out被Git忽略，不能只上传指向out的说明而丢掉最终可交付件。

## 行为验证与证据入口

- 原型及v5五场景：真实新旧RTL自然上/下饱和、恢复、400次未饱和等价、取消重入、XY I=0不关闭Z I，最终各actual0；原失败夹具和修正重跑记录保留。
- v5宽度边界：两个速度单位各816534拍，全部222控制/归一化/参数边界bits及实际运算一致，4个单拍坏az取消；num/value别名逐拍相等且在50/39位范围。
- 实际top13、四客户端非零XY/Z积分、121个协议用例、53项地面站测试均有记录。
- v6：1410720组实际谓词测试；真实height-fusion PRE0/PRE1共3194862拍，公开/请求/运算结果逐拍一致，坏az当拍撤销和发布veto；见numeric_guard_fusion/completion03/results.json。
- v7：aw_storage_boundary两单位均actual0，新增I/bias及合法阶段的27/26/29/30位范围与等价断言；top13和四客户端actual0。归档收尾时五场景批次也已completed=5、真实exit0，输入55源码前后保持不变。本轮自有计算已全部收尾，没有待启动的PNR。
- 所有源码/工具/原始日志、失败分类和manifest的导航见已有build/ATTEMPTS.md、raw_terminal_receipts/frozen_11_terminal_20261026、followup_closed、各候选终态目录。不要改写封存旧记录。

## 接续边界

1. 首先核对STATE.json与实际文件/进程；已有完成结果直接读取，不重复启动同一计算。没有新chat批准前不启动PNR。
2. 保留冻结B0B3、runtime_xy_pi_20261026（R）、handoff_xy_pi_runtime_20261026（H）和旧证据。不要运行旧驱动去覆盖它们。
3. 41448是旧R/map1_p2r2的独立gw_sh，非本轮任务，不要终止。新任务只核自己PID/创建时间/命令路径。
4. 现有B3接收服务最后已知PID49948，COM17/115200、8765；本轮未改。接续前重新核实；不要启动第二个串口所有者。公共bridge同样未改，禁止归档或打印.env凭证。
5. 所有长构建使用独立Hidden后台supervisor，分别保存vendor和runner真实wait。编排中断没有exit就写unknown，不伪造正常返回。
6. 物理验收必须：完整route+位流、正常vendor0/EOF、新VG/source55、原20ns/50MHz、五类slack非负、setup/hold违规端点0、18pins正确、FS/cfg B0B4。不能沿用旧时序，也不能降低频率/增加假falsepath抹去失败。
7. 首个全门通过后，独立读取raw TR再选中；其他运行任务先真实结束或精确取消并留据，再promote最终canonical，避免使仍在运行的source55冻结检查失效。
8. 新版实体下载前重新确认当前拆桨/低位；先SRAM地面读回，再按用户长期使用意图固化和真正断电重启验证。飞行效果单列验收，不把仿真PASS说成已解决所有实飞问题。

## Git状态

本轮最新已推远端为ddd887da55b7b0841a100a61deebbfe61cebe76e。新firmware/B0B4、ground/B0B4、analysis/20261026_z_aw_fix尚未提交；不要git clean/reset或新worktree丢掉这些工作。无关未跟踪firmware/B0B2/evidence/copy99_proof/proof.zip保持排除。

确认后新会话应使用本机apple项目、local环境、同一目录；项目ID见STATE.json。最终源码/位流/证据配套并只读验证后再commit/push，不把未达标候选发布成正式升级包。
