# 当前验收状态（2026-10-25）

当前 SiK 模块 SHA256 为 `aff3e5a2fc19f045faf01885f23cbe245753c048686982c9d19a97bcc57bc160`，telemetry SHA256为`3aadbf30852adeb70cb40011d1b57d859c1bf7b4aec1b31625c260580b4b557c`。当前A585版本2保留76字节/64字节payload，拒收source ID及首保护精确时间两槽不可用；其余448位与capture tick有实际tap逐拍投影对照。正式变更由`v2_integration.json`绑定，之前完整copy99/v1源、脚本、文档及证据保留在`source_revisions/copy99_v1/`。51个其它源文件逐字节不变，未修改控制增益或目标上限。

截至本记录，当前源码没有通过物理验收的位流，未进行新版本 SRAM 安装，未写 Flash。IMU A/B 对照核心输入未变、v2实际tap投影、被动观测审计、真实UART644字节/CRC及旧568字节黄金对照通过。新接收器协议18项、bench分析器24项、隔离接收器24项、安装器70项回归通过；这些均为离线验证，不能写成实物或飞行验收。

正式综合`out/B0B2/build_v2_syn_p2r2_rep0/`已vendor0通过，真实VG为`7e0a3dcea65355fcd4233edebf9ac3f37727a0647df3366dea6054b57710cd74`，27460 FF/35735 LUT/9237 ALU；影子VG哈希不同，两者不能混称同一网表。正式派生物理工程`out/B0B2/build_v2_global_p2r2_rep0/`正在布线，保留原17引脚及19.5ns约束，尚无结果。

早期初始 SiK 模块的布线结果为：默认完整工程剩余292条；强制复位全局网后，p2/r2/rep1剩余266条，p3/r2/rep1剩余340条，p2/r2/rep0剩余210条。均没有可安装位流或 STA 通过结果。该源码修订的哈希、模块和已完成测试/审查保留在 `source_revisions/pre_copy99/`，原始失败报告保留在 `failed_default_route/`、`failed_global_routes/`。

旧 B0B0 胜出物理参数为 p2/r2/rep0，与逻辑源码快照默认的rep1不同。当前构建默认及文档已对齐rep0；当前新网表仍需独立验收。旧精确网表的单轮重放只作为物理基准，不产生 B0B2 验收资格。

历史copy99/v1网表`cba41971c26a66ffc5f36d8bf4f1ebbbc41974d31e2cdf2307e480da75ed49ea`的p2/r2/rep0剩余176条，单改route=1后剩余4689条。两项均vendor退出码1、没有STA通过或可安装位流，小型可移植证据保留在`failed_copy99_routes/`。不继续使用更差的route1作为当前候选。

光流目标25°与观测有效15°的后续问题已在实际RTL中复现，尚未改动。轴向、旋转影响、动态融合及目标范围一致性仍需按计划继续验证。
