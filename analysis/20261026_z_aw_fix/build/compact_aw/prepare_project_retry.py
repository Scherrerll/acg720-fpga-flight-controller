from pathlib import Path
import hashlib,json
O=Path(__file__).resolve().parent;R=O.parents[3]
old=O/'run_physical_p3r0.py';new=O/'run_physical_p3r0_retry02.py'
assert not new.exists()
source=old.read_text()
assert source.count("ATTEMPT=ROOT/'physical_p3r0_01'")==1
assert source.count("ET.tostring(root,encoding='utf8')")==1
fixed=source.replace("ATTEMPT=ROOT/'physical_p3r0_01'","ATTEMPT=ROOT/'physical_p3r0_02'").replace("ET.tostring(root,encoding='utf8')","ET.tostring(root,encoding='utf-8')")
anchor="    tcl=(SOURCE/'build.tcl').read_text();assert tcl.count('run all')==1 and tcl.count('open_project acg720_ano_port.gprj')==1"
assert fixed.count(anchor)==1
fixed=fixed.replace(anchor,"""    raw_project=(SOURCE/'physical.gprj').read_bytes()
    assert raw_project.count(b'<?xml')==1, 'exactly one XML declaration required'
    parsed_project=ET.fromstring(raw_project)
    assert [(f.attrib['path'],f.attrib['type']) for f in parsed_project.find('FileList')]==[
      ('impl/gwsynthesis/acg720_ano_port.vg','file.netlist'),('acg720_ano_port.cst','file.cst'),('acg720_ano_port.sdc','file.sdc')]
    write('project_serialization_check.json',{'passed':True,'xml_declarations':1,'pure_netlist_project':True,
      'project_sha256':sha(SOURCE/'physical.gprj'),'scope':'Previous fresh01 rejected before placement due duplicate XML declaration; corrected utf-8 serialization; no RTL/netlist change.'})
"""+anchor)
new.write_text(fixed,encoding='utf8',newline='\n')
h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
A=R/'out/z_aw_fix_20261026/compact_aw_v1/physical_p3r0_01'
(O/'project_retry_provenance.json').write_text(json.dumps({'original_runner_sha256':h(old),'new_runner_sha256':h(new),
 'changes':['fresh physical_p3r0_02 path','ET serialization utf8 -> utf-8 prevents automatic second XML declaration','assert single XML declaration and exact netlist/CST/SDC project'],
 'first_attempt_actual_exit':json.loads((A/'verification/physical_exit.json').read_text())['actual_p_wait'],
 'first_attempt_log_sha256':h(A/'verification/physical.log'),'first_attempt_exit_sha256':h(A/'verification/physical_exit.json'),
 'classification':'Driver-generated project rejected before PNR; not route/RTL/timing failure. First evidence unchanged.'},indent=2)+'\n')
print(h(new))
