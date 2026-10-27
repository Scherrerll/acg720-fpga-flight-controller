# v4 同源综合扇出阈值100

准确复用v4全部55份源码和已绑定功能证明。源码build.tcl也不修改；仅独立执行Tcl将SYN max_fanout从200改成100，map2/area、PNR replicate_resources0/P3或P2/R0均保留。

实际最接近50MHz的v4完整布通报告为49.456MHz/setup−0.220ns，关键路径含fanout115控制网络及较大布线延迟。官方SUG1220-2.1E PDF34说明max_fanout约束输入、网络和寄存器输出扇出。本实验希望综合层的更低阈值改善这些高扇出连接；不宣称必定复制、不预先声称面积或时序改善。另一个独立v4 PNR replicate_resources1尝试仍单独保留，其选项不混入本轮。

全部RTL功能、精度、已批准抗饱和行为/默认参数、50MHz/20ns和唯一radio_rx原例外不变。实际SYN后先运行原网表/时钟/同步器/增益/18端口审计，成功才PNR；真实vendor/root退出、完整route/位流、五余量及setup/hold端点0仍全部必需。不得补造独立SYN wait0。无GUI缓存、增量seed、LOC、硬件或源码promote。
