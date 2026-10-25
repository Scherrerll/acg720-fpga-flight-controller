# 交付结果：光流 XY P/I 运行时调参

离线实现、针对性测试、完整布线和厂商真实20ns STA已完成；新镜像尚未安装、未写Flash，实机调参通信与飞行动态均未验收。默认P=0.05/I=0，两轴共用，停机原子生效，仅本次上电有效。

## 本次新工件与时序

最终冻结工程：`builds/idle_integral_p3r0/source`，不是失败或中止的诊断尝试。器件GW5AT-LV60PG484AC1/I0，UserCode B0B3。厂商报告直接使用20.000ns约束，不采用旧19.5ns结果加0.5ns换算。物理重试复用本次真实综合产生的同一网表；源码CST完整保存选中物理约束，observer的所选分配见下文复现命令，未改控制逻辑或豁免关键路径。

选中物理选项为 **place=3 / route=0 / map_option=2 / replicate_resources=0**，来自该fixture的 `verification/build_input.json`（历史回执缺省map_option按2、replicate_resources按0解释），同时记入 `qualification.json` 的physical_options。源码build.tcl的综合映射选项为2，与最终物理命令选项分别记录；canonical `build.tcl` 的 `--all` 默认P2/R0并不代表本次选中物理选项。

| 检查 | 新结果 |
|---|---|
| 完整布线 | 完成，无未布通报告；18/18引脚与CST一致 |
| Fmax | 50.257 MHz |
| Setup | +0.102 ns，违例端点0 |
| Hold | +0.145 ns，违例端点0 |
| Recovery | +11.895 ns |
| Removal | +3.312 ns |
| 最小脉宽 | +7.387 ns |

原始网表、`.pr`、`.fs`、`.tr`、`.rpt.txt`、引脚报告及完整厂商日志都在最终fixture。所有映射时钟引脚均核对为clk50；新增radio_rx异步例外只覆盖第一级同步器D，后续路径仍计时。既有异步串口/PPM与外部SPI接口的原边界不因本次内部时钟闭合而获得新的外部时序/飞行资格，见网表审计和原报告约束表。

| SHA256绑定 | 值 |
|---|---|
| 新网表 | `4497e28d79a30da7487a40449d0f0ed19735d1859d2601f0d972f51344b9d9eb` |
| 新物理设计.pr | `cf1f4230147cc0393ccbe76d90d911d95b2a7c4b3f866769ace2114985ed1892` |
| 新位流.fs | `a5b893b25a5e510348c8a4ac75c914b8a14473bbfb054b4cc4040b86800f64dd` |

源码55文件、最终网表/约束/配置/物理结果、测试、工具、审阅和飞行分析通过 `delivery_manifest.json` 绑定。`verify_delivery.py` 只读校验清单；`qualification.json`记录验收边界。相对冻结P005/I0，45文件逐字节未变，9个既有文件改变，新增1个参数模块；完整差异见 `source_changes.diff`。

## 按选中物理选项离线复现

在交付工程的独立副本中，从下列综合步骤开始，每一步exit0后再运行下一步；验证及audit工具会刷新该副本的verification凭据。两个目标fixture都必须是未使用的新目录，已有目录应换新后缀，不覆盖canonical source或已有验收fixture。先产生自己的新网表，再以精确网表工程运行本次选中的place/route。选中CST的observer_reset为已审阅BUFG；`--observer-global`只核对并保留该现有指令。

```powershell
python -B build.py --synth --fixture builds/rebuild_syn_001
python -B physical_retry.py --donor builds/rebuild_syn_001 --fixture builds/rebuild_pr_001 --place 3 --route 0 --observer-global
python -B inspect_timing.py builds/rebuild_pr_001 --require-pass
python -B audit_netlist.py builds/rebuild_pr_001
```

复现需读取新fixture自己的完整厂商布线与20ns STA结果；以上参数记录不保证新运行的位流逐字节等同于本次交付，也不替代新报告验收。

## 接口与验证

接收B16/P7-20，发射B15/P7-19，115200 8N1、3.3V TTL。停机且有效遥控CH5未处于解锁高位时写入；在取消状态的空闲边界同时更新P/I/generation，提交时再查安全条件。ACK之后独立GET核对。P/I均进入真实控制算术，I沿用原误差、dt、限幅和模式语义；P+I+FF扩大为36位以覆盖合法大增益而不在限幅前环绕。详见 `PROTOCOL.md` 与 `README.md`。

- 121项实际参数RTL响应校验，覆盖逐bit CRC破坏、重发、范围、短包/超时、锁定、提交竞态与背压；真实434拍/bit UART和电脑端分片/粘包解析通过。
- 实际控制器默认输出与P005/I0基线一致；P=.15/I=.10与原V15输出/积分一致；非零I、双向饱和、零误差、失效、模式退出/重入和停机清零通过。最大P=1与±10000mm/s边界输出符号/限幅通过。工作对在回调中途输入改变时保持一致；孤立夹具最长XY回调5082拍=101.64us。加速到达节奏保留原dt，此证据不是飞机动态辨识。
- 真实UART→参数bank→唯一TX→串行采样→交付电脑解析器通过；644字节完整旧遥测与冻结基线逐字节一致。
- 最终TX读取bank冻结状态字段与CRC组成的192位响应wire；省去TX第二份响应复制后，bank也省去重复整帧寄存器。ready仅在第24字节UART真正完成后置位，response_valid期间整帧稳定。121个原协议用例及5个所有权/复位扩展用例与原bank逐拍比较，P/I/generation/valid共12301拍一致，valid时633次完整192位响应一致，CRC阶段2672次正文一致；valid=0时的响应位不承诺相同。692字节遥测/响应与推广前版本完全一致。两次独立真实综合分别减少199FF/617LUT、126FF/136LUT，CLS、布通和时序只以最终物理报告为准；推广记录与原审阅记录分开保留，见review/RESPONSE_COMPACT_ADDENDUM.md。
- 历史bank分支曾采用独立的一拍INIT0启动复位，并保留UART、核心/导航/保护和TX原复位时刻；其首边沿归纳、完整双顶层1215644拍/168串行字节/7次末字节ACK、无force的740ns GET100及后续CST重复负LOCAL删除均逐段保留。single-positive做了新综合，54个非CST文件不变时的测试复用明确未称重跑。见review/LOCAL_BANK_RESET_RELEASE_ADDENDUM.md和review/BANK_SINGLE_CONSTRAINT_RELEASE_ADDENDUM.md。
- 另行保留的未选同相通信复位实验把UART和bank接到独立INIT0、syn_preserve-only的boot>=254寄存器；真实单释放启动轨迹与原global逐拍同相，核心/导航/保护/TX原复位不变。新鲜完整双顶层1215644拍和168串行字节、无force740ns GET100、8相位557706拍生产UART/bank扫描通过；普通流只等同force两边core依赖，safe/boundary保持真实。126直接bank用例仅按未变源码复用。两个正常EOF综合stage的原始p.wait均为0；330个通信SR负载、3283个原广域负载、27765个FF均50MHz、两LUT对256个boot值的组合真值均独立核对。中断attempt只作历史，不充作成功回执。见review/EXACT_PHASE_COMM_RESET_RELEASE_ADDENDUM.md及独立审阅。


- 当前明确选择idle_gain_integral_ce：在冻结gain sampler基础上仅搬迁54个savedI快照FF的使能，liveI/reset/算术不变。两份真实参考的450位公共输出比较1002843拍并检查两次非零部分积分回滚；三套原断言回归通过。正常EOF sentinel和p.wait0绑定4497冻结VG，映射snapshot129/idle86CE（总146），128状态仅idle使能；额外1FF为position原state3相同D/CLK/RESET/CE/INIT的综合副本。私有idle/reset快照差异明确保留；此段不替代最终完整布线和真实20ns五类STA。见review/IDLE_GAIN_INTEGRAL_CE_RELEASE_ADDENDUM.md。
- body_only_request仅保留为RESOURCE_STOP诊断：bank减少16FF/5LUT，但整机仅减少10FF且增加620LUT/5ALU；已停止，未进行PNR、未推广，不属于任何源码接受分支。其冻结证明和资源报告仅供检查，见review/BODY_ONLY_REQUEST_RESOURCE_STOP.md。
- bounded_bank_counters功能和资源证明通过但未选：bank减少12FF/33LUT、整机减少13FF/28LUT，冻结证明仅作诊断保留，未获物理资格、未推广，不属于源码接受分支。任何人工取消的物理尝试仅保留实际取消审计和退出码，不作厂商正常失败或成功；见review/COUNTER_UNSELECTED_DIAGNOSTIC.md。
- 实际顶层/核心13项门禁与连线测试通过，包括真实解锁FF与潜在提交同拍的拒绝；电脑端4项测试通过，不自动重发SET。
- 源码独立复查核对所有36001个合法yaw的整数三角边界，未发现已修正位宽/解锁竞态之外的新缺陷。这是公式/源码审查，不冒充RTL或实机验收。
- 真实四客户端持续争用下，P=.125/I=.25的12次XY与20次高度输出/积分和独占服务逐次一致，无数学故障。最坏XY请求至发布355.84us，高度251.08us；输入到达加速10倍而dt仍1/11/20ms。详见 `review/CONTENTION_RESULT.md`。

早期诊断尝试分别遇到SDC对象名称不匹配、工具环境切换后的进程中止，以及缺少基线实际CST复位全局指令的一次995未布通失败。bank正/负两条LOCAL约束还曾被厂商CT1000按重复约束拒绝，两次均在placement前exit1；这些失败及后续单正约束修订逐段保留。无最终报告或未布通的尝试均未作为通过凭据。最终工程是新的完整布线。

## 飞行/P2调查

完整报告见 `analysis_flights/FINDINGS.md`，含C文件/行号→冻结RTL→epoch/sequence对应表与复算数据。P2 376文件哈希相符，5882个原生帧独立复算无字段/单位不符。当前46/46活动帧实际采用导航目标；同镜像表面对照证实环境影响观测；原V15转动相关伪速度是动态摆动的强候选，未排除真实平移/时序/环路匹配。两次当前退出均伴高度降级锁存，首次瞬态失效源仍未知。可以排除可见范围内旧B0B0按合法变化拒收机制重演，不能据5Hz数据排除所有IMU/高度/内环问题。参数可调不等于回中刹停和持续悬停通过。

## 实机待办与回退

本次无硬件/串口操作，现有接收器不变。需当次核对B15/B16、电平/共地、拆桨停机状态，并明确批准所选新位流的SRAM测试；未取得本次安装确认前不下载，更不自动写Flash。优先验证默认查询、停机SET+GET、解锁/预解锁写拒绝、重启默认值，再决定是否另行Flash安装。旧遥控映射/姿态方向不重新整套验收。

回退镜像及哈希在 `rollback/`；只做SRAM且Flash未变时，完全断电可恢复现有Flash。Flash回退须按当次维护流程校验镜像、写入并独立verify、冷启动确认；具体步骤在README。新参数不做掉电保存。
