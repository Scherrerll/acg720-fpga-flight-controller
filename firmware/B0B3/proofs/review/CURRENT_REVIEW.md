# 当前审阅适用范围

`REVIEW.md` / `bounds.json` 是 signed36 修复后的冻结审阅记录，保留其当时的文件哈希，不改写历史。核心安全门和真实XY控制器仍与该记录逐字节一致，36001 yaw边界计算及共享数学争用证明继续适用。参数bank及TX的两次通信精简分别按独立组合证据补充审阅，不把旧源码哈希改成新哈希。

其中关于TX“在idle复制整帧响应”的段落已被最终通信精简替换。当前 `telemetry_tx.v` SHA256 为 `11fac23449b65f87a3291231f9be173046c893a994ae658e25f3e0a7827adbbb`。主线检查了 `candidates/comm_compact/candidate.diff`：唯一功能结构调整为省去第二份192位响应复制，直接读取bank的稳定帧，并将ready延后至最后字节UART完成。仲裁优先级、单一UART及原遥测字节不变。

bank在response_valid且未ready期间不解析下一请求、不改response；发送器仅在最终字节busy撤销后ready，因此整帧数据有明确唯一所有者。实际UART/背压测试断言此契约，两次请求/响应顺序正确，全部692字节（644遥测与48响应）与推广前完全一致。主线随后复跑顶层13项安全门和实际串行输出测试，均通过。证据与当前源码通过 `verification/comm_compact_promotion.json` 及候选contract_results的逐文件哈希关联。

第二次精简将参数bank的完整192位响应寄存器改成冻结状态字段与CRC的wire拼接。当前 `xy_pi_parameters.v` SHA256为 `c3ab65d07c7b664268192a5b0de3acfb510efdac504a7a82cfdfa89e83d1b187`，旧审阅hash为 `bb11794b6a406a9c321e53a24d8751dc74006388063ef538bd5084f3d298886f`。两真实bank对121个原用例及5个复位/所有权用例逐拍比较P/I/generation/valid，共12301拍一致；valid期间633次完整192位响应及CRC阶段2672次正文一致。valid=0时响应不再保证与旧寄存器相同。实际UART/late-ready完整692字节仍一致，详见 [RESPONSE_COMPACT_ADDENDUM.md](RESPONSE_COMPACT_ADDENDUM.md) 及 `response_compact_review.json` 的逐文件绑定。

候选报告中的“尚未推广/未PNR”是生成时刻记录；推广事实以各独立promotion回执为准。综合节省不等同于CLS、布通或时序通过。物理结果只能由最终厂商完整布线和20ns STA报告确认。
