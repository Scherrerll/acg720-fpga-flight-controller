# B3→原B4综合资源差异：基线和634 LUT归属核对

**结论：旧比较确实使用冻结B3的实际selected SYN donor；全top的+744 LUT中，controller_proof占+110，其他层级合计+634，数目可完整对账。它是两次完整设计综合的映射差异，不应将+744全称为AW模块新增逻辑或据此推定布线首因。** 本次只读，未改任何源/旧回执，未运行build。

基线核验：`runtime_xy_pi_20261026/candidates/idle_gain_integral_ce/source`的55源，与repo `firmware/B0B3/source`、`qualification.json.source_sha256`、原SYN input/freeze及selected physical input的55项逐字节完全一致。其VG、repo导出`.vg.gz`解压内容、qualification和selected physical donor均为 `4497e28d79a30da7487a40449d0f0ed19735d1859d2601f0d972f51344b9d9eb`。runtime与repo proof资源XML均为 `9506d99198ee7a21293ab3e408ef0f6e3e5271fcd5119b6adb0f87bdf69cf40a`；原 `synthesis_comparison.json.files`同时绑定该VG/XML，原SYN `actual_p_wait=0`。已核对export manifest的selected55、qualification哈希和这五项proof实体哈希。freeze中的“backup_not_selected”是当时历史状态；后来的selected physical input明确donor为该候选、CST amendment=none，不能用旧状态文字否定后续选择。

对端为原B4 `out/z_aw_fix_20261026/build_attempt_01`，VG `f63ae79edcd75c9905a0e55b53c3d8d9d94c239d8e67038a73fade80ffaa958a`，XML `be44a9863456a686aa48d9918047ad3c628172d4c7fd08e09d2977463550dd49`；不是compact_v1/v2/v3。旧 `mapped_audit.json`引用的reference_resources哈希与上述B3 XML一致。两次使用同一Gowin工具SHA `585c12968550a960d1021287742672ff9d6bbeaee5623f6811dfc1f907a4af41`、map2/repl0；source差异是hold、bank defaults/build、build.tcl UserCode和place选项，故不称为控制器单模块消融实验。

两个XML均含相同60个层级节点。节点资源是**包含子节点的总数**；下表按互斥区域拆分，避免父子重复相加：

| 区域（相对acg720_ano_port） | LUT delta | 定位 |
|---|---:|---|
| native_navigation/controller_proof | +110 | 4757→4867 |
| core | +554 | 19702→20256；其中imu+362（estimator+345为其子集）、yaw_controller+60、controller+37、fallback_sticks+37、gate+16、manual_angles+8、receiver−7、fallback_control−1、core本层剩余+42 |
| native_navigation除controller_proof | +86 | height_fusion+46、velocity_fusion+20、geometry+16、divide_service+8、multiply_service+1、position−5 |
| acc_time | +4 | 136→140 |
| parameters | −6 | 441→435 |
| parameter_uart | −1 | 63→62 |
| telemetry | −3 | 3070→3067 |
| 其余直接子节点及top本层净差 | 0 | mtf LUT总数不变；未列区域净差0 |
| **全top** | **+744** | 36040→36784；外controller **554+86+4−6−1−3=634** |

另可交叉核对FF总差+140=controller+134+外部+6，ALU总差+87=controller+83+外部+4。未变化源码模块也出现映射计数差异；本次仅定位实际XML归属，未证明是哪一项输入/优化/映射因素导致这些变化。旧原始回执保留；当前解读应使用上述“同selected donor、完整设计映射差异”的范围，不把源级单改动数或LUT差直接换算为CLS、时序或具体未布通net原因。

关键交叉出处：`firmware/B0B3/qualification.json`（SHA `cc59500cde47fb8ccacf2c929c64a0dc218cf6153fdc80a83ff90b40913b3470`）；`firmware/B0B3/physical/evidence/build_input.json`（`906c60e803eabf3b73e7bad2d7e6cd527c566cdf392b174ca4a3035446787a6b`）；`firmware/B0B3/proofs/candidates/idle_gain_integral_ce/verification/synthesis_comparison.json`（`63bafea62b4cd9b187257b4b87596ab8289404b6e3c6e6e4fc74044e4123918e`）。复算方法：递归XML `name`形成路径，取每节点`T_Lut`新减旧；兄弟节点相加，父节点减直接子节点得到本层余额。
