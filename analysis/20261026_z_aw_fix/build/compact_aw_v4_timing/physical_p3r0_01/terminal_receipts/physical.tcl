open_project physical.gprj
set_option -top_module acg720_ano_port
set_option -output_base_name acg720_ano_port
set_option -user_code 0000B0B4
set_option -place_option 3
set_option -route_option 0
set_option -timing_driven 1
set_option -replicate_resources 0
set_option -map_option 2
set_option -global_freq 50
set_option -max_fanout 200
set_option -opt_goal timing
set_option -route_maxfan 23
run pnr
puts PHYSICAL_COMMAND_RETURNED_EOF
flush stdout
