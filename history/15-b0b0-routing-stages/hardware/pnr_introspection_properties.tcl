foreach query {{set_option -h} {set_option --help} {set_file_prop -h} {import_files -h} {add_file -h} {create_project -h} {open_project -h} {set_file_enable -h}} {puts "QUERY $query"; catch {eval $query} result; puts $result}
exit
