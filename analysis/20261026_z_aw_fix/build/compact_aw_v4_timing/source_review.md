# v4 相同源码的timing目标综合对照

此前全部候选的SYN使用opt_goal area。原v4 P3R0曾完整route且距离50MHz仅−0.220ns；以同一55份源码、同一map2/repl0/global50和原20ns SDC，单独尝试官方支持的opt_goal timing，检查映射是否为时序目标作出不同取舍。

不改RTL、默认值、算法、精度、状态周期或保护；没有重新执行相同SYN。canonical/source/build.tcl保留原area字节，实际synth_only.tcl显式覆盖成timing并记录哈希，build_input标明真实目标，不混淆源码与执行配置。原v4综合与证据不覆盖。

本机官方SUG1220-2.1E PDF第29/30页（文内22/23页）定义auto/area/timing。首先必须审查实际VG/资源及全部clock/radio/gain/18ports门；若实际有效网表与area相同，跳过重复物理试验。若不同，再在空闲计算名额内选择一项有依据的物理实现，50MHz及五类时序门不变。

真实控制器及共享数学六个依赖与v9已完成的五场景、边界和四客户端完全相同，按哈希复用。不以SYN配置或面积变化宣称时序通过。
