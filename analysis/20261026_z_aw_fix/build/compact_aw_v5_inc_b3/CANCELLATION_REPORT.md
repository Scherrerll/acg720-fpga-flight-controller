# 增量备选：工具自动回退后，按root指示取消

Gowin实际接受并解析NEW donor中的*.pr，但报告 **PA2136：matching 2.81低于阈值80，自动转普通placement+routing**。因此这是`tool_builtin_fallback`，**没有成功复用增量布局布线**，不能继承B3时序，也不把“进入placement”当增量成功。

Root判断该普通P3R0与另一条已在跑的v5常规P3重复，明确授权只取消此冗余vendor。取消前CIM核对PID50764、安装gw_sh.exe、NEW attempt绝对Tcl、父9744的本runner命令和创建时间；Tcl SHA与启动凭据相同。只执行`Stop-Process -Id 50764 -Force`，没有中止父Python或其他任务。

父Python真实`p.wait()`返回 **4294967295**。旧通用回执的`normal_wait_return=true`仅指wait函数已返回；**并非正常完成**。`cancellation_completed.json`明确`normal_completion=false`、`route_failure_claim=false`、取消理由`root_requested_duplicate_fallback_cancellation`；无TR/FS，不存在可报告的STA值。

来源R原PR和NEW copy的before/after SHA均仍为`cf1f4230147cc0393ccbe76d90d911d95b2a7c4b3f866769ace2114985ed1892`；源55、VG2d670...及SYN donor凭据均未变。没有覆盖此attempt或在此目录启动另一种策略。

冻结`cancellation_freeze_manifest.json` SHA `f7a7eb20a81f28666d1a0decdcfc2e8de7df246f028a337cf04eaaafa6e7be70`，84件150,451,208B，含复制PR。详细机器回执摘要见本目录`cancellation_result.json`（SHA `766ad674a12571874b9ec0cb444f4d437d5756fe4650a17c5ceff22b142d6c26`）。工具原始warning、终止请求、实际exit和PR before/after均保留。

Root另授权的替代是fresh `compact_aw_v5/physical_p2r0_01`，无inc_pnr、source04e75/VG2d670不变、P2R0/map2/replicate0/TD1/20ns和全部gate保持；其结果独立判断。P4任务没有被本次取消动作触碰。没有新的综合、RTL变更、Git或硬件操作。
