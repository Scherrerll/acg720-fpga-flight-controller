# v10：Z诊断快照mask交换

依据v6 P2原始Path1（acc_time/output_az → Z可用性 → z_active → diagnostic_q[63]/RESET，−0.859ns），在v9上单独优化诊断快照。当前v9 P3/v4 P2仍独立运行，输入不改。

Z delta、collective和target分别占diagnostic_q[111:96]/[63:48]/[31:0]。z_active已在shadow_flags[4]，即diagnostic_q[84]，同一个快照、同一个hold/reset边沿捕获。原来先按z_active归零再捕获；新候选捕获原始值，在输出按同拍捕获的q[84]归零。XY已有同一做法，保持不变。无需增加寄存器或周期。

对每个快照接受边沿，`capture(a ? x : 0) == capture(a) ? capture(x) : 0`；四态条件合并也相等。reset常量Z标志和Z字段为0，hold同时冻结数据与标志，因此归纳到每个周期的720公开诊断位。两个STARTUP_ONLY_DIAGNOSTIC_RESET模式均测试。物理z_active、z_throttle_delta、z_collective、z_target_height_out等公开控制表达式逐字节不变，所有控制/融合状态机不变。

预期减少晚z_active到64个源级诊断位的前置mask扇出；实际可综合FF数不能由64直接推算。代价是把mask放到下游遥测数据路径，需要新的SYN/PNR验证，不能先宣称时序获益。

验证提取并直接执行两份源码的完整diagnostic_next/寄存器/diagnostic_body块，输入依照源码中shadow_flags与z_active的同一位契约，随机/边界/X/Z、hold、reset逐拍比较720位。再跑实际top13。控制器六个依赖及生产者/高度融合文件与v9/v8相同，按精确哈希复用已通过证明。
