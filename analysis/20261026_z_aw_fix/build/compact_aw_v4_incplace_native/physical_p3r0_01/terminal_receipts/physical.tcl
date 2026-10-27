open_project acg720_ano_port.gprj
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
set_option -opt_goal area
set_option -route_maxfan 23
run syn
puts SYNTHESIS_COMMAND_RETURNED_EOF
flush stdout
if {[catch {exec {C:/Users/ScherrerL/AppData/Local/Programs/Python/Python313/python.exe} -B -X utf8 {C:/Users/ScherrerL/Desktop/apple/github_publish/acg720-fpga-flight-controller/analysis/20261026_z_aw_fix/build/compact_aw_v4_incplace_native/audit_synthesis.py} 3} audit_failure]} {
  puts stderr "NATIVE_SYNTHESIS_AUDIT_REJECTED $audit_failure"
  exit 97
}
puts SYNTHESIS_AUDIT_RETURNED_EOF
flush stdout
set_option -inc_place {C:/Users/ScherrerL/Desktop/apple/github_publish/acg720-fpga-flight-controller/out/z_aw_fix_20261026/compact_aw_v4_incplace_native/physical_p3r0_01/donor/native_v4_P3R0.p}
run pnr
puts PHYSICAL_COMMAND_RETURNED_EOF
flush stdout
