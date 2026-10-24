set_device -name GW5AT-60B GW5AT-LV60PG484AC1/I0
add_file bad.v
set_option -top_module bad
set_option -output_base_name bad
run syn
exit
