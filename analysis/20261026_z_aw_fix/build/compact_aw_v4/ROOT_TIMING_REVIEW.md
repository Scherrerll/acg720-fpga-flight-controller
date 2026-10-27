# v4 P3R0：完整布线后的真实时序失败

根任务直接读取 `out/z_aw_fix_20261026/compact_aw_v4/physical_p3r0_01/` 原始TR、log、exit及物理audit；不是把“工具返回0”解释成时序通过。

原工具于UTC06:34:00.989正常wait0、EOF已返回，完整route和位流生成成功；新VG、55源、B4 UserCode及18引脚检查通过。但原TR实际20ns/50MHz约束下Fmax=49.456MHz，setup最差−0.220ns，32个setup端点违规，TNS=−2.878ns。因此**此FS不可作为合格下载版本**。

其他四类最差slack：hold +0.122ns、recovery +11.288ns、removal +3.092ns、minimum pulse width +7.387ns；hold违规端点0。不能用这些正余量抵消setup失败。

原报告前25条setup路径中可见的主要锥体：

- Path1：`acc_time/output_az_3_s0/Q` → `core/flight_state/flying_ms_3_s0/D`，−0.220ns；数据延迟19.726ns、clock skew0.437ns。详细节点经过nav numeric ready、height fusion/vertical ready、fallback active、selected_throttle及flight-state组合选择。跨区tNET包括1.461/2.271/2.640ns，fallback节点还见45/115扇出；这是一条真实的跨模块健康/高度选择组合路径，不能当作异步路径豁免。
- Path3：`mtf/metric/vy_x100_28_s0/Q` → `staged_telemetry/extension_q_814_s0/D`，−0.177ns。
- Path8/9：`previous_pose_valid_s0/Q` → `native_navigation/multiply_service/held_a_38_s0/D`及bit42，−0.140ns；另有同源pending enable路径。

报告只列前25条代表路径，上述分类不声称逐一枚举全部32违规端点。也不能仅凭这一报告，把此前所有“未布通网络”的原因归结为某一个锥体。

继续使用经过等价及数值范围验证的资源压缩候选和独立物理策略，并重新检查真实TR。保留原20ns、五表非负、Fmax≥50MHz、全部路由及安全接线要求；本轮没有通过增加false path、multicycle或延迟紧急mask来抹去负余量。原FS、失败audit及全部原始文件保持不改，历史冻结指纹由p3r0_final绑定。
