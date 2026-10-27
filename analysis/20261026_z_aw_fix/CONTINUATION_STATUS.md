# B0B4 接续实时状态

更新时间：中国时间 2026-10-27T12:52:13.487136+08:00

本地同仓库离线工作；B0B4尚未安装。源码已按合格原始报告promote，初始原型55源保存在PROMOTION.json所列位置。原handoff_20261026为冻结快照，接续已获用户确认。

| 候选 | 方案 | 状态 | 最后阶段 | vendor / runner真实wait |
|---|---|---|---|---|
| v7 | physical_p3r0_01 | vendor_nonzero_route_failure | [90%] Routing Phase 3 completed | 1 / 1 |
| v7 | physical_p2r0_01 | vendor_nonzero_route_failure | [90%] Routing Phase 3 completed | 1 / 1 |
| v8 | physical_p3r0_01 | vendor_nonzero_route_failure | [90%] Routing Phase 3 completed | 1 / 1 |
| v8 | physical_p2r0_01 | vendor_nonzero_route_failure | [90%] Routing Phase 3 completed | 1 / 1 |
| v9 | physical_p3r0_01 | vendor_nonzero_route_failure | [90%] Routing Phase 3 completed | 1 / 1 |
| v9 | physical_p3r0_inc_v4_01 | cancelled_incremental_fallback | Running placement...... | 1 / 1 |
| v4_p2_followup | physical_p2r0_01 | vendor_nonzero_route_failure | [90%] Routing Phase 3 completed | 1 / 1 |
| v10 | physical_p3r0_01 | vendor_nonzero_route_failure | [90%] Routing Phase 3 completed | 1 / 1 |
| v10 | physical_p1r0_mf60_01 | vendor_nonzero_route_failure | [90%] Routing Phase 3 completed | 1 / 1 |
| v4_p3r1_followup | physical_p3r1_01 | vendor_nonzero_route_failure | [90%] Routing Phase 3 completed | 1 / 1 |
| v4_timing | physical_p3r0_01 | cancelled_dense_mapping_deprioritized | [60%] Routing Phase 0 completed | 1 / 1 |
| v4_p3mf60_followup | physical_p3r0_mf60_01 | completed_vendor_physical_gate_failure | PHYSICAL_COMMAND_RETURNED_EOF | 0 / 1 |
| v4_loc3_followup | physical_p3r0_inc_loc3_01 | vendor_nonzero_unclassified | [90%] Routing Phase 3 completed | 1 / 1 |
| v4_incplace_loc3_followup | physical_p3r0_incplace_loc3_01 | cancelled_incremental_fallback | Running placement...... | 1 / 1 |
| v4_p1_followup | physical_p1r0_01 | vendor_nonzero_route_failure | [90%] Routing Phase 3 completed | 1 / 1 |
| v4_partial_floorplan_followup | physical_p3r0_partial_01 | completed_vendor_physical_gate_failure | PHYSICAL_COMMAND_RETURNED_EOF | 0 / 1 |
| v4_data_routing_followup | physical_p3r0_data_route_01 | vendor_nonzero_route_failure | [90%] Routing Phase 3 completed | 1 / 1 |
| v4_data_routing_followup | physical_p2r0_data_route_01 | vendor_nonzero_route_failure | [90%] Routing Phase 3 completed | 1 / 1 |
| v11 | physical_p3r0_01 | vendor_nonzero_route_failure | [90%] Routing Phase 3 completed | 1 / 1 |
| v11 | physical_p2r0_01 | not_started | 未启动 | 尚无回执 / 尚无回执 |
| v12 | physical_p3r0_01 | vendor_nonzero_route_failure | [90%] Routing Phase 3 completed | 1 / 1 |
| v12 | physical_p2r0_01 | vendor_nonzero_route_failure | [90%] Routing Phase 3 completed | 1 / 1 |
| v13 | physical_p3r0_01 | vendor_nonzero_route_failure | [90%] Routing Phase 3 completed | 1 / 1 |
| v13 | physical_p2r0_01 | vendor_nonzero_route_failure | [90%] Routing Phase 3 completed | 1 / 1 |
| v13_map1 | physical_p3r0_01 | vendor_nonzero_route_failure | [90%] Routing Phase 3 completed | 1 / 1 |
| v13_map1 | physical_p2r0_01 | vendor_nonzero_route_failure | [90%] Routing Phase 3 completed | 1 / 1 |
| v13_native | physical_p3r0_01 | vendor_nonzero_route_failure | [90%] Routing Phase 3 completed | 1 / 1 |
| v13_native | physical_p2r0_01 | not_started | 未启动 | 尚无回执 / 尚无回执 |
| v4_native | physical_p3r0_01 | completed_vendor_physical_gate_failure | PHYSICAL_COMMAND_RETURNED_EOF | 0 / 1 |
| v4_native | physical_p2r0_01 | not_started | 未启动 | 尚无回执 / 尚无回执 |
| v4_clockbuf1_followup | physical_p3r0_clkbuf1_01 | completed_vendor_physical_gate_failure | PHYSICAL_COMMAND_RETURNED_EOF | 0 / 1 |
| v4_rep1_followup | physical_p3r0_rep1_01 | vendor_nonzero_route_failure | [90%] Routing Phase 3 completed | 1 / 1 |
| v4_fan100_native | physical_p3r0_01 | vendor_nonzero_route_failure | [90%] Routing Phase 3 completed | 1 / 1 |
| v4_fan100_native | physical_p2r0_01 | not_started | 未启动 | 尚无回执 / 尚无回执 |
| v14 | physical_p3r0_01 | vendor_nonzero_route_failure | [90%] Routing Phase 3 completed | 1 / 1 |
| v14 | physical_p2r0_01 | vendor_nonzero_route_failure | [90%] Routing Phase 3 completed | 1 / 1 |
| v4_incplace_native | physical_p3r0_01 | cancelled_orphan_after_runner_assertion | [20%] Placement Phase 1 completed | 尚无回执 / 1 |
| v4_incplace_native | physical_p2r0_01 | not_started | 未启动 | 尚无回执 / 尚无回执 |
| v15 | physical_p3r0_01 | vendor_nonzero_route_failure | [90%] Routing Phase 3 completed | 1 / 1 |
| v15 | physical_p2r0_01 | not_started | 未启动 | 尚无回执 / 尚无回执 |
| v16 | physical_p3r0_01 | vendor_nonzero_route_failure | [90%] Routing Phase 3 completed | 1 / 1 |
| v16 | physical_p2r0_01 | not_started | 未启动 | 尚无回执 / 尚无回执 |
| v17 | physical_p3r0_01 | vendor_nonzero_route_failure | [90%] Routing Phase 3 completed | 1 / 1 |
| v17 | physical_p2r0_01 | not_started | 未启动 | 尚无回执 / 尚无回执 |
| v18 | physical_p3r0_01 | not_started | 未启动 | 尚无回执 / 尚无回执 |
| v18 | physical_p2r0_01 | not_started | 未启动 | 尚无回执 / 尚无回执 |
| v18_dsp_followup | physical_p3r0_dsploc_01 | completed_vendor_physical_gate_failure | PHYSICAL_COMMAND_RETURNED_EOF | 0 / 1 |
| v19 | physical_p3r0_01 | not_started | 未启动 | 尚无回执 / 尚无回执 |
| v20 | physical_p3r0_01 | vendor_nonzero_route_failure | [90%] Routing Phase 3 completed | 1 / 1 |
| v20_dsp_followup | physical_p3r0_dsploc_01 | not_started | 未启动 | 尚无回执 / 尚无回执 |
| v22 | physical_p3r0_01 | full_gate_pass | PHYSICAL_COMMAND_RETURNED_EOF | 0 / 0 |
| v22_dsp_followup | physical_p3r0_dsploc_01 | route_failure | [90%] Routing Phase 3 completed | 1 / 1 |
| v22_fan100 | physical_p3r0_01 | not_started | 未启动 | 尚无回执 / 尚无回执 |

v9以曾完整布通的v4控制器配合同一份v8范围标志。五场景已完成5/5，完整批次通过=True，proof root真实wait=0，SYN runner真实wait=0；物理实现已启动=True。首轮启动器自指文件名错误在仿真前退出1，原件保留，新retry02仅修正该路径。

v7五场景、边界、top13、四客户端和综合沿用已核验结果。v8在v7上只增加与az同拍发布的原范围谓词，控制器不变；生产者444003拍、融合3194862拍和top13通过，综合vendor/runner真实0，时钟/同步器/增益/18端口审计通过。资源FF27689/LUT36075，映射组合链缩短不代表物理时序通过。

v8首次测试驱动因vvp附加finish提示而解析失败，原runner1保留；completion02复用真实已完成的exit0阶段，剩余验证及最终runner0均有原回执。详见[证明报告](build/compact_aw_v8/PROOF_REPORT.md)、[综合收据](build/compact_aw_v8/SYNTHESIS_RESULT.json)。

下载前仍须重新确认当前拆桨和低位；先SRAM地面验证，再固化和真正断电读回默认值。低空掉高不在本轮处理；仿真时间不是实机着陆等待建议。

机器状态和各尝试完整结果见[CONTINUATION_STATE.json](CONTINUATION_STATE.json)。原B3、v4～v7源55匹配归档。尚未触及串口或下载器。

v10仅交换Z诊断mask与同拍快照顺序：两个复位模式各720位、160001拍及top13通过=True，proof真实wait=0，SYN真实wait=0，PNR已启动=True。首轮抽取夹具缺声明的compile4/root1保留，retry02补齐显式声明并禁用隐式网络；RTL未因夹具修正而改变。

v4相同55源的timing目标综合：SYN审计通过=True，root真实wait=0，PNR已启动=True。LUT+4666/FF+81/ALU+6；旧关键逻辑锥体19→16级、最大扇出115→118，仅映射拓扑而非STA。旧v4已布通报告Logic77%/CLS89%，全局路由资源占用满，较大映射有面积取舍。

最终v4原始55源的13项顶层保护门新回执实际wait0；五场景、FRAC0/16边界与四客户端按六项完全相同依赖哈希复用v9真实通过记录。地面站53项Python及Node界面测试仅核对未变输入和原日志SHA，不重复测试，不连接硬件。见build/v4_release_proofs/RESULT.json。

v12只将自增分支比较等价改写为非零阈值下age<(AGE_LIMIT-32d1)，保留全32位年龄、原优先级及同拍撤销。九种integer阈值/200040向量、完整融合两模式/六边沿案例、top13和19阶段/root真实wait0；全部六刺激哈希冻结。SYN root实际wait=0；综合资源详见该候选SYNTHESIS_RESULT，物理资格另按原始报告和独立复核验收。

v13仅缓存MTF同拍age<200/1000谓词，原32位年龄/重复时间戳/接口与其余54文件不变。105632组抽取年龄转移、完整UART两模式各1200513拍和1140公开位、199/200与999/1000边沿/恢复、top13均通过，7阶段及root真实wait0。UART按1.152MHz加速毫秒老化，抽取转移独立于tick周期，全顶层仍50MHz；不预置完整reader内部状态。SYN root实际wait=0；该段只报告功能/综合证据，物理资格见上表和独立raw复核。

v13同源map1对照仅在独立SYN Tcl把map2改为map1，其余源码/约束/参数不变；未宣称面积或速度更好。SYN root实际wait=0；当前物理启动=True。

v13原生工程备选保留原RTL FileList，同一gw_sh先综合、执行真实网表审计，成功后才PNR。7脚本语法及Tcl结构/顺序预检通过，vendor已启动=True。原helper字节不改；流程识别改查真实SYN/hook/原工程绑定，50MHz/20ns、五余量、端点、引脚/B4身份和真实退出门均保留。完整vendor进程只有一份真实wait，不补造单独SYN退出0；详见GATE_ADAPTATION。

v4原生流对照逐字节使用冻结v4源55（B3相对三文件），复用已绑定top13/控制器/地面站功能证明；参考旧完整布通49.456MHz仍不合格。本轮保留RTL工程先SYN审计再PNR，已启动=True；不能将参考报告或GUI状态当作新的50MHz验收。

v11仅在v9高度融合内缓存同拍age<AGE_LIMIT谓词。完整融合两模式及六组AGE=1/31/65536超时边沿、top13真实wait0；普通+边沿共4067304拍。一次新SYN和clock/radio/gain/18ports审计真实0，VG f239c61b…，相对v9实测+7FF/+789LUT/+3ALU；不以源码新增一位推算映射资源。空综合启动与Windows封装修正记录保留，正式SYN retry02成功。物理门另验。

v4两条独立选项对照：一条在同一冻结VG上仅启用PNR高扇出资源复制；另一条同源原生工程仅将实际SYN max_fanout200降为100，源码build.tcl保持原字节。max100实际审计通过=True，不补造单独SYN wait。实际网表比较见build/compact_aw_v4_fan100_native/MAPPED_FANOUT_COMPARISON.json：原fallback控制115个负载拆为58/57，实际+81FF/+83LUT，仍不能代替新STA。首次启动器缺空报告目录未创建vendor进程；补齐目录后retry02真实启动，见PRESTART_CORRECTION.json。

v4原生失败工程已由官方FloorPlanner读取，当前器件回标对话框未提供普通FF/LUT全布局导出。未执行回标、GUI构建或硬件操作。GUI自动改写的UI配置及device.cfg已先独立保存，再从已校验的查看前备份逐字节恢复；全部98文件重核一致，原失败收据仍保留。

v14从冻结v4仅给previous_pose_valid数据reg设置局部syn_maxfan10，并对fallback原active组合表达式经普通wire同值连接设置syn_maxfan50；没有新状态/时钟或周期。两文件的精确反向文本核对通过，fallback CRLF→LF单独披露；新完整顶层原13项刺激字节一致，compile/vvp/root实际0，六控制依赖及地面站43输入重核不变。SYN已启动=True、root实际wait=0；实际是否复制需新网表审计，不预先宣称生效或时序通过。五份B3相对改动及全55重建哈希已保存在implementation_history/v14_local_fanout。

用户2026-10-27新指示：继续直到成功；50MHz确实困难时允许考虑约49MHz实际降频后备。该指示不是拆桨/低位等当前实体状态确认。当前v14 P3/P2仍按完整50MHz/20ns门运行，不能把旧49.456MHz失败改称50MHz通过。

后备前置验证：厂商PLL_ADV已为GW5AT-60B生成50→49MHz的PLLA+PLL_INIT，phase0/无SSC，三份RTL及IPC原样归档；独立未修改厂商模型锁定后49000周期约1ms，compile/vvp实际0。隔离clock49_working目录仅开始tick→us转换器单元适配：默认50与旧模块139公开位/除法状态逐拍一致，49除数及余数进位12000事务/57取消/47忙时重入、409173拍真实0。完整飞控时钟、其余时基和地面站均未改；该工作源不允许全机构建或下载。见build/clock49_generate/IMPLEMENTATION_REVIEW_PENDING.json及build/clock49_time_adapter/SOURCE_BINDING.json。

v15把油门<1250比较放到数值分支之后、晚到的availability选择之前，不增加状态/周期；完整旧/新/default飞行状态在TICKS_PER_MS=1/3/7逐拍比较，2097152阈值向量、100000随机转换、自然起飞/着陆/撤销、实际fallback关系与原top13通过。首轮v15夹具compile3保留，retry02仅改保留字标识符和初始化声明；RTL未因夹具修正改变。SYN通过=True，物理另验。

v16把油门<1250比较放到数值分支之后、晚到的availability选择之前，不增加状态/周期；仅额外限制实际187负载组合数据驱动扇出50。完整旧/新/default飞行状态在TICKS_PER_MS=1/3/7逐拍比较，2097152阈值向量、100000随机转换、自然起飞/着陆/撤销、实际fallback关系与原top13通过。首轮v15夹具compile3保留，retry02仅改保留字标识符和初始化声明；RTL未因夹具修正改变。SYN通过=True，物理另验。

v17把油门<1250比较放到数值分支之后、晚到的availability选择之前，不增加状态/周期；额外限制active组合驱动扇出50和previous_pose_valid数据reg扇出10。完整旧/新/default飞行状态在TICKS_PER_MS=1/3/7逐拍比较，2097152阈值向量、100000随机转换、自然起飞/着陆/撤销、实际fallback关系与原top13通过。首轮v15夹具compile3保留，retry02仅改保留字标识符和初始化声明；RTL未因夹具修正改变。SYN通过=True，物理另验。

v18在v17基础上缓存与原数据同拍发布的input velocity range谓词，真实新增一个私有状态位，原公开周期不变。组件证明、完整飞行状态比较及原top13均有实际成功回执；控制器及地面站相同依赖按哈希复用。SYN通过=True；组合级数减少不能代替物理验收。

v19在v17基础上缓存与原数据同拍发布的AZ range谓词，真实新增一个私有状态位，原公开周期不变。组件证明、完整飞行状态比较及原top13均有实际成功回执；控制器及地面站相同依赖按哈希复用。SYN通过=True；组合级数减少不能代替物理验收。

v20：Combined same-publication AZ and input-velocity predicates；完整源55已核对，功能证据通过=True，SYN真实runner wait=0，物理资格须单独测量。新完整候选不能冒充任一父版本的完整55文件证明。

v21：Exact v18 with extension-only same-edge snapshot moved to vendor SP；完整源55已核对，功能证据通过=True，SYN真实runner wait=1，物理资格须单独测量。新完整候选不能冒充任一父版本的完整55文件证明。

v22：Exact v20 arithmetic with one local logic-multiplier synthesis hint and same-value wire；完整源55已核对，功能证据通过=True，SYN真实runner wait=0，物理资格须单独测量。新完整候选不能冒充任一父版本的完整55文件证明。

v18 DSP/BSRAM物理对照复用完全相同的v18源55、功能证明和综合VG。官方FloorPlanner从隔离原生工程导出的52条位置约束中，仅保留与该VG实例及类型匹配的44 DSP和2 BSRAM；完整原CST前缀逐字节保留，combined CST另存并被physical.gprj实际选用。cst_warn_to_error=1；50MHz/20ns及原完整物理门不变。

v20_dsp_followup：薄层仅增加匹配实际VG的官方位置约束，测得数量={'official_export_rows': 52, 'kept': 41, 'excluded': 11, 'DSP': 39, 'BSRAM': 2}；源55、功能和SYN证明均来自standard v20，不能冒充新的同源功能测试。原CST完整前缀和50MHz门保持。

v22_dsp_followup：薄层仅增加匹配实际VG的官方位置约束，测得数量={'official_export_rows': 52, 'kept': 33, 'excluded': 19, 'DSP': 31, 'BSRAM': 2}；源55、功能和SYN证明均来自standard v22，不能冒充新的同源功能测试。原CST完整前缀和50MHz门保持。

v22_fan100复用完整相同的standard v22源55与功能证明，仅执行用综合max_fanout从200改为100；source/build.tcl仍保持原件。实际SYN/vendor、audit、runner均0，译码节点最大负载174降到100，FF和LUT各增加83。该测量不代表布线或50MHz时序通过。

用户最新要求已执行：49MHz交由独立会话01a17a00-9d49-7860-ba99-03fe403f6b62，开会话前已写完整需求并逐文件核对复制58份输入到runtime_b0b4_49mhz_20261027。本会话只攻真实50MHz；独立会话不得写共享仓库或接触硬件，主会话统一烧录/发布。上述49单测段落只是交接时冻结状态，后续49实现进度以独立目录为准。

真实50MHz完整物理门及独立raw复核已通过：standard v22 / physical_p3r0_01，50.075MHz，setup +0.030ns，setup/hold端点0/0。其它备选不再推进；下载及冷启动状态独立记录，不能由离线通过推断。
