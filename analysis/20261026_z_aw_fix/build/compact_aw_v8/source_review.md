# v8：同拍发布的加速度范围标志

依据现有 v4 P3R0 raw Path1（acc_time/output_az → height readiness → fallback → flight state，−0.220ns）和 v6 P2R0 raw Path1（同一数值检查来源 → diagnostic reset，−0.859ns），准备源端等价的范围预计算候选。v7 P3R0/P2R0 正独立运行，v8不改变其输入，也尚未启动物理计算。

pose_time_adapter 输出只在 reset/cancel 和 index==31 时改变。前者输出 az=0，范围标志为1；后者从 held_az 同拍发布数据和原表达式 `held_az>=-30000 && held_az<=30000`。其余分支两个输出都保持，包括fault/start-while-busy。因此初始化和每个时钟后均有 output_az_range_ok === (output_az>=-30000 && output_az<=30000)。不改变 update、busy、fault、acc_valid、dt或分数状态。

顶层只对这一生产者启用PRECHECKED_AZ_RANGE，导航及高度融合以标志替代两处同一数值谓词。各模块默认仍直接计算原谓词，其他调用者保留原行为。原始范围表达式逐字保留；不采用v6的符号扩展改写。取消、姿态有效、RC、倾角、源时效和输出mask均保持原边沿。

这增加一个伴随数据的FF，不增加控制延迟，不改Q16精度、算法、积分和P/I默认值。需要生产者逐拍差分（含边界、cancel、busy重入、X/Z）、真实高度融合PRE0/PRE1差分，以及顶层13项保护门验证。v7控制器及四客户端所依赖文件完全不变，原证据按文件哈希复用。物理收益仍需实际新SYN和PNR，不能由源级推断宣布通过。
