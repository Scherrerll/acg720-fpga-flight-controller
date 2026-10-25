# Compact通信推广复核补记

复核当前canonical `source/telemetry_tx.v` 的SHA256为 `11fac23449b65f87a3291231f9be173046c893a994ae658e25f3e0a7827adbbb`，与已独立验证的comm_compact候选逐字节相同；未改的参数bank SHA256为 `bb11794b6a406a9c321e53a24d8751dc74006388063ef538bd5084f3d298886f`。推广回执 `verification/comm_compact_promotion.json` 仅列telemetry_tx一个变更文件。

未发现新的holding契约问题。发送期间直接读取bank的packet；bank在response_valid期间停在等待状态，不解析下一帧，不更新packet，直至ready。TX仅在state8/index23/!busy，即最后一个UART字节已经真正完成后给ready。故整帧所有权先保留在bank，最后完成才释放，不依赖被删除的192位副本。原到期遥测优先、完整遥测组不截断、单一UART及所有响应CRC/序号/生效值保持。

候选真实UART契约仿真已经覆盖最长2,832,005 clocks（56.6401ms）持包背压、两次最后字节ready、packet全程稳定和下一请求顺序；完整692字节输出与旧canonical相同。该仿真绑定的TX/bank字节哈希与本次推广后当前文件相同。主线推广后的root `verification/link_results.json`、`top_safety_results.json` 均PASS，`netlist_audit.json` 绑定compact VG `9b2cee37e4f0ed0e68c9abb2895228c455a12f50cc5e9ba2d741a36350f404dc`。相关回执和文件的当前哈希保存在 `compact_promotion_addendum.json`。

原 `review/REVIEW.md` 与 `bounds.json` 保留为推广前记录，未改写。控制器/参数bank本次没有变化，原算术和安全审阅的适用范围保持；本补记仅补充通信持包/握手变化。它不代表compact布线成功、50MHz时序闭合、硬件安装或飞行通过。
