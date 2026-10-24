proc inventory {ns} {puts "NAMESPACE $ns"; puts [lsort [info commands ${ns}::*]]; foreach child [namespace children $ns] {inventory $child}}
inventory ::
exit
