from pathlib import Path
import ast,hashlib,json,shutil
O=Path(__file__).resolve().parent;p=O/'run_physical_p3r0.py';q=O/'run_physical_p3r0_launch02.py'
h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert h(p)=='de57ec3f0433fb3f80b74247be2407b612032df77f78fbafb31a7aea9651aa78' and not q.exists()
bad="assert din['synthesis_options']=={'map_option':2,'replicate_resources':0,'timing_driven':1}"
good="assert din['synthesis_options']=={'map_option':2,'replicate_resources':0}"
s=p.read_text();assert s.count(bad)==1;s=s.replace(bad,good)
assert "('timing_driven','1')" in s
ast.parse(s);q.write_text(s,encoding='utf8',newline='\n')
d=O/'launcher_attempt01';d.mkdir()
for name in ['run_physical_p3r0.py','physical_p3_runner.stdout.log','physical_p3_runner.stderr.log','physical_p3_runner_process.json','p3_runner_derivation.json']:
    shutil.copy2(O/name,d/name)
(O/'launch02_derivation.json').write_text(json.dumps({'failed_entry_sha256':h(p),'actual_launch02_entry_sha256':h(q),
 'correction':'Donor synthesis_options is exactly map2/repl0; TD1 remains an explicit physical Tcl and receipt guard. First launcher failed before profile/vendor creation.',
 'failed_launcher_evidence':{x.name:h(x) for x in d.iterdir() if x.is_file()}},indent=2)+'\n')
print(h(q))
