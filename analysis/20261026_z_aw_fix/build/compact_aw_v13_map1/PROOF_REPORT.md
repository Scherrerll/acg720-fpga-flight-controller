# v13 同源默认 LUT 映射对照

55 份源码与 v13 完全相同，按其实际通过的 UART、年龄转移、top13 及父证明链复用功能证据。PROOF_BINDING.json 明确指向原证明，不复制旧退出收据充当新仿真。canonical build.tcl 仍是 source55 的 map2 基线；实际执行的 synth_only.tcl 仅将 map_option 改为1，area、replicate0、50MHz/20ns、原 radio_rx 输入例外和 B4 UserCode 均保留。

新顶层展开、综合、mapped/radio、默认 wire1000/350/18端口与全 FF clk50 审计完成。vendor 和 SYN 根驱动均正常真实退出0。精确网表 SHA256：f71a16a54abdb1f7cf13b3b943996cd7c4005d4d342de9306fb2566648a79272。

实际综合资源为 FF27756、ALU9544、LUT36225。相对 v13 map2，仅 +1LUT，FF、ALU、DSP 和 BSRAM 不变。网表模块定义中的 LUT5 从1303变为0，LUT2/3/4分布改变；这个定义直方图并非展开后的物理占用，不能与资源报告直接相加。记录见 SYNTHESIS_RESULT.json。备选依据是减少 LUT5 对组合与打包的限制可能改变拥塞，尚无物理收益声明。

对同一两个遥测端点，年龄位21及新200ms谓词的选定组合拓扑与 map2 相同；新位D和CE的所选层数也相同，详见 MAPPED_MTF_AGE_CONE_REVIEW.json。这只比较包括所有 LUT 输入弧的拓扑上界，不能推断实际延迟、拥塞或完整时序。

精确新 VG 的 P3/R0 与 P2/R0 脚本已准备。其 Tcl 明确使用 map1，并绑定真实 SYN 与同源证明位置；不会重新综合，且不会改写 source55 中的基线 build.tcl。物理试验只能在当前结果核对后、满足最多两条自有 PNR 任务时启动。是否启动及最终资格以实际进程、终态清单和独立 raw 复核为准。此报告只封存综合对照，不授予下载资格，也没有安装、冷启动或飞行声明。
