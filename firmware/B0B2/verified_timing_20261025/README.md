# B0B2 布线与时序通过版本

2026-10-25，Gowin V1.9.12.04，GW5AT-LV60PG484AC1/I0。

- 未布通网络：0。
- 原时钟约束：19.500ns；实际 Fmax：51.400MHz。
- Setup / Hold 违例：0 / 0，TNS 均为 0。
- 最差裕量：Setup +0.045ns、Hold +0.196ns、Recovery +13.711ns、Removal +2.317ns、最小脉宽 +7.137ns。
- 原 17 个引脚、电气约束、B0B2 标识保持，未增加时序例外。

`source/` 是与已通过综合网表绑定的完整 RTL 快照，已同步至上级 `source/`。原源码保存在 `source_before/`。优化包含控制门分解、原寄存器快照、同拍遥测分组缓存，以及把原姿态、加速度、距离有效性和 100ms 年龄门恢复到飞控入口；数值检查、失效策略、协议和释放拍由归档证明约束。

`project/acg720_ano_port.gprj` 是本次通过的综合网表物理工程；`project/build.tcl` 固定 P2/R0、资源复制关闭及原 19.5ns 约束。`bitstream/` 保存本次实际生成的位流，`reports/complete_audit.json` 保存完整审查。`manifest.json` 和 `evidence/index.json` 将源码、网表、位流、报告及 313 项历史证明材料绑定；历史材料按哈希存放于 `evidence/blobs/`。

在 B0B2 目录执行：

```powershell
python tools/build_verified.py
python tools/build_verified.py --prepare-only
python tools/build_verified.py --run
```

第一条检查所有交付输入；第二条生成全新的物理复现目录；第三条从已绑定网表重新布线并审查完整时序。脚本拒绝使用此网表认证修改后的 RTL。此入口复现本次物理结果，不重新综合编辑后的源码。历史 `source/build.tcl` 与 `tools/build.py` 为保持原证明依赖而保留，本次复现使用上述入口。

这些材料确认当前配置的离线 RTL/协议检查及静态时序结果。没有访问硬件、串口或 Flash，也不代表安装、旋转方向或实飞验收完成。
