from pathlib import Path
import importlib.util
root=Path(__file__).resolve().parent
s=(root/'fixture/core/flight_core.v').read_text(encoding='utf8')
for name,decl in [('rate_fresh','wire rate_fresh;'),('selected_throttle','wire [15:0] selected_throttle;'),('motor_prepared','wire motor_prepared,taking_off,flying,land_lock;')]:
 assert s.index(decl)+decl.index(name)==s.index(name), name
for name in ['taking_off','flying','land_lock','preparation_mask']:
 decl='wire motor_prepared,taking_off,flying,land_lock;' if name!='preparation_mask' else 'wire [3:0] preparation_mask;'
 # Ignore comments and output name taking_off_out: exact token first occurrence.
 import re
 code=re.sub(r'//[^\n]*','',s)
 occurrences=list(re.finditer(r'\b'+name+r'\b',code))
 assert occurrences and code.index(decl)+decl.index(name)==occurrences[0].start(),name
spec=importlib.util.spec_from_file_location('builder',root/'fixture/build_project.py')
b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
proof=root/'hardware/forward_net_reproduction'
try:b.reject_connectivity_warnings(proof/'bad')
except ValueError:pass
else:raise AssertionError('Bad actual Gowin synthesis was accepted')
b.reject_connectivity_warnings(proof/'good')
print('Predeclaration and actual Gowin bad/good diagnostic gate PASS')
