# Numeric guard factoring (v6, 2026-10-26)

结论：可做同周期二态等价优化。v4 P3 raw TR Path1 为20层、49.456MHz、setup -0.220ns；VG证实 s111→s91→s72→s44→s18→s7 是 `converted_az` 的±30000比较，输出 `nav_xy_ready_10` 也供 height fusion numeric tail。v5仍用相同32位比较，未见既有等价分解。

负责点（v5行号）：`position/mtf_shared_height_fusion.v:88,96` 当前az；`:1232` state84 held_rawaz；`mtf_xyz_navigation_control.v:169,171,172` sample/ax/ay/az，共7处。held_rawaz已有16位存储和32位符号扩展，改其布尔guard不改存储或提交。

候选函数：`(x[31:16]=={16{x[15]}}) && $signed(x[15:0])>=-16'sd30000 && $signed(x[15:0])<=16'sd30000`。证明：原谓词为真则x落在S16范围，必是低16位符号扩展；新谓词为真则x等于该S16值且在原界内，双向成立。不得删upper检查：`32'h00010000`低字0却非法；`32'h0000ffff`低字-1却是65535。与CLK/AGE/CAL参数无关。

风险：不是四态等价；例如upper明确不匹配、低字含X时原比较X而候选0。只主张二态硬件等价，禁止宣称X传播不变。综合可能重建原比较，收益须实测。

验证：低16位穷举65536，配符号扩展及坏upper；定向±30000、±30001、±32768、32767、INT32极值和上述别名；top/height fusion原故障立即撤销与提交边界回归；完整SYN及clock/gain/18ports审计。只隔离v6两文件，其余53同v5；不改阈值、周期、状态、数学、接口，不启动PNR。
