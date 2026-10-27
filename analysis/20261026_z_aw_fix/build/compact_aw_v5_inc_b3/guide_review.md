# v5增量PnR：官方指南与seed资格核查

已只读核对安装目录的两份官方英文指南：

- `SUG1220-2.1E_Gowin Software Tcl Commands User Guide.pdf`，PDF第51页/印刷44页，提供`-inc_pnr <0|auto|file>`及`set_option -inc_pnr auto`；其file说明写成*.p。文档SHA `c8ee7e8cb8486220a8639424f71debe9f4c3dff0d4c365860474c24782ded08c`。
- `SUG100-4.4.7E_Gowin Software User Guide.pdf`，PDF54–55页/印刷42–43页，区分只增量placement所用*.p与增量placement+routing所用*.pr，支持手工指定既有PR；并注明设备家族支持范围。文档SHA `b4e8891ffecdfcd8f60f060cb6025e0ab09e7e177759e3fb6570ade8c1c20d1f`。

两份指南的扩展名文字存在差异。本次按详细软件指南，显式指定复制后的*.pr，不把*.pr改名伪装成*.p。实际工具是否接受、是否完成以及新设计的STA均必须看本attempt；如拒绝，只保存该独立失败，不原地换文件或自动fallback。没有复制/分发厂商PDF。

seed原件是R `builds/idle_integral_p3r0/source/impl/pnr/acg720_ano_port.pr`，SHA **`cf1f4230147cc0393ccbe76d90d911d95b2a7c4b3f866769ace2114985ed1892`**，与冻结`firmware/B0B3/qualification.json/physical_design_sha256`完全相同；资格记录实际20ns、P3R0/map2/replicate0。新v5与B3项目Device属性逐项相同（GW5AT-LV60PG484AC1/I0）。这只确认旧seed的身份和兼容项目属性，**不把旧B3时序或功能资格转移给B4**。

新目录`out/z_aw_fix_20261026/compact_aw_v5/physical_p3r0_inc_b3_01`中，先复制seed到`donor/B0B3_selected_P3R0.pr`并复核相同SHA；实际执行Tcl的唯一新增选项`-inc_pnr`仅指向这个NEW donor绝对路径，Tcl不含R/H目录。原始R PR只由Python只读hash/copy；来源及副本before/after（包括失败分支）均记录，不能在R/H工程中直接调用工具。

逻辑输入仍仅为新v5的55项源码、精确新VG `2d670218e97041bb3d4cc7c67218f4bef12e5bf96261225b9b97203ce3b4a1c9`、新netlist-only项目的VG/CST/SDC三文件。项目恰一个UTF-8 XML声明。执行明确B4/P3R0/map2/replicate0/timing_driven1、原20ns SDC；SYN donor最终清单及clock/radio/gain/strictFF/18port各审计均原SHA绑定，不重新综合。

输入凭据在该fixture `verification/{build_input,physical_input,incremental_seed_before}.json`，实际命令/工具/runner/PID/wait在process/exit回执与原log。初始日志已实际出现Skip synthesis、新VG读取及NEW donor的Reading pr file；此刻不能因此提前声称文件完整接受、全路由或时序通过。

仍原样要求normal wait0、full route/FS、无非零unrouted、实际20ns/Fmax≥50、setup/hold端点0及全部五类slack非负、18pins/B4 FS/device.cfg、新VG/source55/seed身份未变。没有放宽CDC/时钟/功能或执行硬件操作。
