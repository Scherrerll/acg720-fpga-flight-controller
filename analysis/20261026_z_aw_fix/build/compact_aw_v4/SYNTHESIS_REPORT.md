# compact_aw_v4 SYN结果

真实full-top elaboration及一次map2 SYN均normal p.wait()=0。源hold SHA `ffddb029cb34a8d2ac8995cc43d85866e273d3d147bb650cfd5d3c66c580b642`，仅MA/MB存储及64位符号别名四处修改，其他54项同冻结v3。全部55输入前后SHA不变。

| 实际mapped top | v3 | v4 | 差值 |
|---|---:|---:|---:|
| FF | 27786 | 27766 | −20 |
| LUT | 36405 | 36213 | −192 |
| ALU | 9559 | 9544 | −15 |

controller自身−16FF/−76LUT/−15ALU；所有DSP类型及BRAM不变。不把源码减少22位当作实际FF节省数，也不以综合面积推断布线收益。

实际VG SHA `e67bcab6336757e08645756258d39dd13726b452c392d470de4c900a159aaa8f`；原clock/radio同步边界、18scalar port、P/I各16bit INIT1000/350及27766个FF全部clk50审计通过。执行UserCodeB4/map2/replicate0，原20ns SDC与唯一radio pad false-path不改。SYN本身没有STA/FS资格。

`build_attempt_01/synthesis_freeze_manifest_final.json` SHA `67611917608d8abefac5a9a79e578cf99eaad2703a4e37f8813f5d60bf61f095`绑定源55、原始log/normal-exit、执行runner副本、VG/XML与全部门禁。root拥有功能/非法取消边界回归，本SYN报告不冒充自己重跑这些测试。

root随后授权的P4R0在独立`physical_p4r0_01`、P3R0由另一位代理负责。它们须各自取得normal wait0/full route/20ns五表和Fmax≥50/18pins/B4/精确VG源绑定，不能从本报告或旧B3结果继承。本文不提前声明物理通过。
