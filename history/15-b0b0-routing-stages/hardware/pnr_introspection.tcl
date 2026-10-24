puts "COMMANDS_BEGIN"
puts [lsort [info commands]]
puts "COMMANDS_END"
foreach name {help run read_design read_verilog read_netlist place route pnr} {
 puts "QUERY $name"
 if {[llength [info commands $name]]} {catch {help $name} result; puts $result}
}
exit
