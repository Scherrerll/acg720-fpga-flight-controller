foreach query {{run} {run -help} {run help} {import_files} {set_option} {set_file_prop} {set_property}} {puts "QUERY $query"; catch {eval $query} result; puts $result}
exit
