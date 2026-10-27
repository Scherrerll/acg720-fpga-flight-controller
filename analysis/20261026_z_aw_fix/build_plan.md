# Z anti-windup / XY默认值修正版：独立重建与交付计划

本文件先经只读勘查形成；root随后授权执行独立B0B4构建。范围仅为用户要求的Z windup修正与XY上电默认P=.1000/I=.0350；不继续处理掉高或增加倾角补偿。构建runner不改canonical源码、旧B3/R/H，不进行Git或硬件动作。**最终身份决定为UserCode与A591均B0B4，配套新ground/B0B4 strict codec；下文原B3兼容建议已被此决定替代。**

当前执行：`firmware/B0B4/build_candidate.py`从root冻结的canonical55复制到全新`out/z_aw_fix_20261026/build_attempt_01/source`，顶层Icarus真实wait0，后续依次综合和精确新VG的netlist-only P3R0。输入/工具/命令/PID/正常wait及逐阶段原始日志只记录在该attempt的`verification/`；本文件不提前断言构建、时序或功能资格通过。root若修源，该次输入应标废并另开attempt，不能悄悄替换build输入。

## 冻结基线与工具

- 唯一源基线：仓库`firmware/B0B3/source`。本次逐SHA核对`firmware/B0B3/qualification.json/source_sha256`的**55/55文件全部相同**；不能从R内当前canonical或某个未选候选补文件。
- B3选中结果：R=`C:/Users/ScherrerL/Desktop/apple/runtime_xy_pi_20261026`下`builds/idle_integral_p3r0`，**place3 / route0 / map2 / replicate0**。`source/build.tcl`默认place2/route0，与选中的物理驱动不同；直接运行它不能声称复现selected P3R0。
- 器件：`GW5AT-LV60PG484AC1/I0`，项目Device `gw5at60b-002`，顶层/输出基名`acg720_ano_port`。
- 已安装工具：`C:/Gowin/Gowin_V1.9.12.04_x64/IDE/bin/gw_sh.exe`，当前SHA256 `585c12968550a960d1021287742672ff9d6bbeaee5623f6811dfc1f907a4af41`。Icarus为`C:/Users/ScherrerL/Desktop/apple/.tools/iverilog/app/bin/{iverilog,vvp}.exe`，厂商原语`C:/Gowin/Gowin_V1.9.12.04_x64/IDE/simlib/gw5a/prim_sim.v`；不要求PATH中的C编译器。
- B3旧链身份（仅回退/差异参考，不能拿来替代新构建）：VG `4497e28d79a30da7487a40449d0f0ed19735d1859d2601f0d972f51344b9d9eb`；PR `cf1f4230147cc0393ccbe76d90d911d95b2a7c4b3f866769ace2114985ed1892`；FS `a5b893b25a5e510348c8a4ac75c914b8a14473bbfb054b4cc4040b86800f64dd`。

关键源hash：Z控制器`position/mtf_xyz_hold_control.v`=`b7eef6d33789523cd1e8ff81b05e75db91ab3c67bf76e03483dec356055fa1a6`；bank `xy_pi_parameters.v`=`c3ab65d07c7b664268192a5b0de3acfb510efdac504a7a82cfdfa89e83d1b187`；CST=`38cabf0ed2edab95e609d23a2b4a5a8a5ff70f3b1e787a2d7b1f759eaaaf69b4`；SDC=`1a9e9e0a853166a8b94194a9857df493232068bfff6fff3ea6368b339725aa87`。

## 新镜像身份与地面站兼容

root最终选新物理UserCode **B0B4**及**A591 `0000B0B4`实现标识**，同时建立`ground/B0B4`与B4 strict codec；A591版本1、24字节响应布局、成对提交和ACK/GET协议仍保持。该决定以明确版本区分Z修正版及新默认，不覆盖冻结B3及其资格声明。旧B3 ground/codec继续只认B3，不放宽或编辑它们。

旧A588/导航等遥测B0B2字段继续按B3兼容语义保留（例如顶层`acg720_ano_port.v:324`），不为显示标签修改既有遥测布局。A591本身不能证明已安装Z修复；健康读回只能确认参数能力，镜像身份另以选定FS SHA及UserCode记录。

B3地面站会**明确拒绝**A591 B4，并非只要改一处UI文案：`firmware/B0B3/xy_pi_cli.py:13`严格解码B3；`ground/B0B3/xy_pi_control.py:223`再次验证B3；`ground/B0B3/xy-pi-ui.js:29`也验证B3。因此root另行负责新B4 codec/地面站分支及HTTP/UI/transport回归；不能宽松接受任意build来绕过。本构建runner不负责修改或运行地面站。

root已将**实际bank的initial和reset两处**一致变为wire P=1000/I=350、generation=0（`xy_pi_parameters.v:12,34`）；保持volatile语义，重启恢复新默认，GET/SET范围和安全提交边界不变。root冻结hold SHA `5a928e0a68db70974049a4debb0b841ca06fa00598a4ffb4cb506997cfed657c`、bank SHA `c7333f8d629a8eed60f0d0a1c042536ffb92eab753d23daee03bcfbdef306392`、build.tcl SHA `ae4e19024a4869bb0665311dd56589014f1ca0aff123c9cc5c02e441200e17a4`；其余52项与B3 byte-identical。hold含AW state66/67额外两时钟，build.tcl已明确B4/P3R0。协议/数值测试里与旧默认绑定的预期需在新候选中明确更新，保留旧B3 fixture，不把有意默认/Z差异伪装成全输出等价。

## 最小独立工作树与执行链

建议全新工作根，例如仓库忽略输出下`out/z_aw_fix_20261026/candidate`，只从B3 source复制55项到其`source/`，排除`impl`、`.user`、日志和旧生成Tcl。在任何修改前保存baseline55哈希；候选冻结时保存全部55哈希、raw diff、允许变更列表。预期算法范围只落Z控制器和默认值bank；版本/构建驱动变更单列，不混作控制变化。R/H/B3保持只读。校准、器件、引脚、时钟及其余RTL应逐字节不变。

执行用Tcl放候选根而非`source/`，每份都留SHA，避免把生成驱动计入原55源码。源`build.tcl`若保留B3/P2默认，必须在新README和manifest直说它是历史模板，新的执行驱动才是新UserCode/P3R0配置；不要无提示照原入口跑出旧UserCode。另一可接受做法是在新source副本中明确更新build.tcl的标签/选项并将其列为第三项source差异，不能修改冻结原件。

1. **定向真实Z RTL证明与受影响回归是最终交付门禁**，绑定新source55及预期差异；root明确允许本次综合/PNR与这些回归并行。完整top Icarus elaboration用项目enabled Verilog列表、`-g2012 -s acg720_ano_port -I <source>`和上面GW5A原语。只在新verification/tmp输出。旧B3 public-cycle等价证明不能作为有意修改Z后的全行为等价；需保留未触发新饱和条件的兼容和有意触发后的正确恢复证明。
2. **一次新综合**：从copy的source/build.tcl制作`<candidate>/synth_only.tcl`，`run all`换成`run syn`、删末尾`exit`、显式设置新UserCode；保留map2/timing_driven1/replicate0/global_freq50/max_fanout200/opt_goal area/route_maxfan23，末尾`puts SYNTHESIS_COMMAND_RETURNED_EOF; flush stdout`。以source为cwd执行：

   ```text
   C:/Gowin/Gowin_V1.9.12.04_x64/IDE/bin/gw_sh.exe <absolute_candidate>/synth_only.tcl
   ```

   由Python `Popen([...], cwd=S, stdin=DEVNULL, stdout=log, stderr=STDOUT, creationflags=CREATE_NO_WINDOW)`启动并真实`p.wait()`，保存开始/结束UTC、PID、命令/工具/Tcl/source55/prerequisite哈希及实际退出码。EOF是避免旧teardown卡住的执行方式，不代替正常wait0与产物检查；日志出现完成但进程未退出不算成功。
3. **审核新VG而非复用B3 VG**：保存`.vg`及`_syn_rsc.xml`，记录整体/控制器/参数bank FF/LUT/ALU/DSP/BRAM差异、全FF clk50、radio_rx仅先到同步器且同步器Q到逻辑继续受时序、端口/方向/18脚及CE/SR变化。新逻辑有新增比较/状态风险，资源不能由旧结果推断。
4. **对该新VG独立P3R0物理实现**：复制新source55和同一新VG到未使用的物理fixture，`physical.gprj` FileList只包含该`.vg`（`file.netlist`）、CST、SDC；否则RTL project的`run pnr`可能自动重综合、破坏精确VG绑定。用已选profile制作`physical.tcl`：

   ```tcl
   open_project physical.gprj
   set_option -top_module acg720_ano_port
   set_option -output_base_name acg720_ano_port
   set_option -user_code 0000B0B4
   set_option -place_option 3
   set_option -route_option 0
   set_option -timing_driven 1
   set_option -replicate_resources 0
   set_option -map_option 2
   set_option -global_freq 50
   set_option -max_fanout 200
   set_option -opt_goal area
   set_option -route_maxfan 23
   run pnr
   puts PHYSICAL_COMMAND_RETURNED_EOF
   flush stdout
   ```

   同样DEVNULL/NO_WINDOW/真实wait。物理前后都验证VG SHA等于新综合VG，来源不是B3旧网表。首试P3R0是沿用成功配置，不保证新逻辑仍可布通/满足时序；不预先安排额外候选或重试。

可借鉴但**不能直接原位调用**：R的`build.py`（顶层elaboration+EOF执行）、`candidates/idle_gain_integral_ce/run_synthesis.py`（单次综合门禁）、`verification/executed_physical_retry_idle_integral.py`/`physical_retry.py`（netlist-only物理驱动）。它们含R相对路径、固定B3 UserCode、旧候选/manifest/VG hardcode或会写R；须在新工作根重新适配/审查，不移除来源和正常退出门禁，不把改路径变成复用旧资格。

## 20ns与交付验收门禁

冻结SDC只有`create_clock -name clk50 -period 20.000 [get_ports {clk50}]`与从radio_rx pad起的false path；其余保持受时序。CST保留原18脚及`CLOCK_LOC "observer_reset" BUFG = CE|SR|LOGIC;`，不新增物理豁免。B3旧Fmax50.257MHz、setup仅+0.102ns，不能因改动小就继承；也不能用19.5ns旧结果加0.5ns代替真实20ns。

新放行必须同时具备：实际正常wait0；日志完整route/bitstream完成；无非零unrouted；同一fixture的原始TR明确clk50=20.000ns、Fmax≥50MHz、setup/hold violated endpoints均0；setup、hold、recovery、removal、minimum pulse五类raw表最差slack均≥0。独立核18个端口/引脚/方向（B15 TX、B16 RX）、device.cfg UserCode、FS头/UserCode、source/SDC/CST/VG/PR/FS身份，不以“有FS文件”或“全局频率设50”替代。

R的`inspect_timing.py`提供raw五表解析，可在新工作根适配。它自身`timing_passed`不含独立Fmax≥50与完整路由判断，需像旧finalizer一样补齐，不只看该布尔值。`finalize_release.py`和B3 `verify_export.py`固定旧source链/UserCode/50.257/具体SHA；不能直接拿它们给新候选盖章，也不能修改冻结版本。

新交付最少保留：baseline55/candidate55及raw diff、执行工具/runner/Tcl哈希、功能证明及明确有意变化、综合资源/XML/新VG、netlist-only project/选项、真实process/wait日志、完整原始TR/pin/rpt、PR/device.cfg/新FS和SHA sidecar、单独qualification及只读验证器。若压缩VG/PR，按B3出口保留原始size/SHA和deterministic gzip信息。只读manifest排除自身，或用单独sidecar，避免自引用哈希。

B3 FS及P005/V15回退保持原名原SHA。新文件应命名如`B0B4_z_aw_xy1000_350_P3R0.fs`并记录精确来源，不覆盖`B0B3_selected_P3R0.fs`。旧硬件下载/Flash脚本固定B3 image/hash/操作白名单，不适用于新FS；本计划不授权或执行下载、SRAM/Flash写入、服务重启、串口或飞行验收。

### 本次只读依据

只读阶段已读B3 README/PROTOCOL/qualification、source构建/约束/身份字段、physical provenance/project/device.cfg及R的上述runner、`builds/idle_integral_p3r0/verification/{build_input,process,process_exit}.json`与gowin.log。旧实际进程2026-10-25T22:45:34Z启动、23:07:52Z正常exit0；日志明确Skip synthesis→full placement/routing/timing→bitstream完成并有EOF返回sentinel。未运行这些旧脚本。随后仅按root新授权运行新B4 `build_candidate.py`，实际状态以后者attempt回执为准，不能与旧成功记录混同。
