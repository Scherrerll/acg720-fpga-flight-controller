# 构建入口：请以 source 目录为当前工作目录运行，工程中的源文件均使用相对路径。
open_project acg720_ano_port.gprj
set_option -top_module acg720_ano_port
set_option -output_base_name acg720_ano_port
# 本版构建标识为 B0B5；此标识不是精确位流哈希，不能单凭它区分同标识的不同构建。
set_option -user_code 0000B0B5
# 以下保留最终选中版本的布局、布线和资源映射设置，注释版没有调整物理配方。
set_option -place_option 3
set_option -route_option 0
set_option -timing_driven 1
set_option -replicate_resources 0
set_option -map_option 2
# 目标工作频率为 50MHz；实际时钟周期仍由工程 SDC 的 20ns 约束定义。
set_option -global_freq 50
set_option -max_fanout 200
set_option -opt_goal area
set_option -route_maxfan 23
# 执行综合与完整物理实现；本脚本不调用下载器，也不操作开发板。
run all
exit
