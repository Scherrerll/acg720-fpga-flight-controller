# v13 同源完整原生工程流程

55份源码逐字节等于已通过功能证明的v13。仍按原map2/replicate0/area/P3或P2/R0、50MHz/20ns、原18引脚、唯一radio_rx输入例外和B4 UserCode构建。本实验保留原RTL .gprj，在同一gw_sh进程中先run syn，再执行独立Python网表审计，审计成功才run pnr。它不以VG文件替换工程FileList。

依据：现有build_candidate.py及所有接续物理脚本均在独立SYN后创建只含VG/CST/SDC的新physical.gprj；旧自种子增量试验匹配仅2.82%。是否因导入方式丢失上下文仍是未证实的假设。本实验只改变原生工程流程，不改RTL、算法、时钟、精度或接口，也不声称一定改善资源/时序。

原build_candidate.py及其所有旧门保持原字节。新流程的审计明确用真实SYN完成、同进程审计成功、实际原RTL工程和新VG绑定来识别流程，不再把“跳过综合”当作此流程的要求；20ns、50MHz、五类余量非负、setup/hold端点0、完整路由和位流、18引脚/B4身份、vendor与runner真实退出0的验收标准保留。独立raw复核同样要求这些门。若综合审计拒绝，原生脚本必须非零退出，不能继续PNR。

单一gw_sh过程包含SYN和PNR，因此只有该完整vendor进程和Python根驱动的真实p.wait收据；不补造一个单独SYN进程退出0。SYN子阶段由实际EOF、原始报告和审计绑定记录。功能证明按相同55源复用v13及其父链，无新增仿真声明。当前只准备，未启动任何vendor或硬件操作。
