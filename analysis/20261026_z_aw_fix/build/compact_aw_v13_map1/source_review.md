# v13 同源 map1 综合对照

55份源码逐字节等于已经通过行为证明的v13，canonical build.tcl仍按源清单保持map2。只在实际执行的独立SYN Tcl中将map_option由2改为1，其余area、replicate0、50MHz/20ns、唯一原radio输入falsepath和UserCode不改。官方本地SUG1220-2.1E PDF第37页将1列为默认映射，2为不增加LUT数量的LUT5导向映射；本轮没有宣称1更省面积或更快，须查看实际资源和网表审计。

依据是既有实际完整路由报告的CLS89%/Logic77%占用与多次map2布线拥塞。默认映射可能改变LUT尺寸分布和打包取舍；该假设只授权一次SYN资源对照，不授予物理或下载资格。v13两条物理运行不被更改，不增加当前物理任务数。功能证明由同一55源和v13实际7阶段/root0及其父证明哈希复用；不复制或重新标注旧测试退出记录。新网表仍须新clock/radio/gain/18ports审计和真实正常退出。当前不启动PNR。
