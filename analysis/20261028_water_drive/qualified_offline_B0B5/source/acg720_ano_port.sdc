create_clock -name clk50 -period 20.000 [get_ports {clk50}]
# The sole fanout of this pad is the first synchronizer stage (proved from
# the mapped netlist). All synchronizer-Q -> logic paths remain timed.
set_false_path -from [get_ports {radio_rx}]
