create_clock -name clk50 -period 20.000 [get_ports {clk50}]
# 该异步引脚只连接同步器第一级，已按综合网表核对；仅豁免引脚到第一级的路径。
# 同步器寄存器 Q 端到后级逻辑的全部路径仍参加正常时序分析。
set_false_path -from [get_ports {radio_rx}]
